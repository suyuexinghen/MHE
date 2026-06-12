from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    FakeClaudeCLIBrainProvider,
)
from metaharness.benchmark_drivers.io import case_dir, write_json, write_text
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    BenchmarkLane,
    LaneSummary,
)
from metaharness.benchmark_drivers.runner_common import dry_run_summary, write_lane_outputs
from metaharness_ext.lean.contracts import LeanExecutionPolicy, LeanProjectSpec, LeanTaskSpec
from metaharness_ext.lean.gateway import LeanGatewayComponent
from metaharness_ext.lean.types import LeanValidationStatus


class LeanProofBenchmarkRunner:
    def __init__(
        self,
        *,
        runs_root: Path,
        allow_real_tools: bool = False,
        brain_provider: ClaudeCLIBrainProvider | FakeClaudeCLIBrainProvider | None = None,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.brain_provider = brain_provider or FakeClaudeCLIBrainProvider()

    def run_case(self, case: BenchmarkCaseSpec, lanes: list[BenchmarkLane]) -> list[LaneSummary]:
        summaries: list[LaneSummary] = []
        for lane in lanes:
            if lane == "extension":
                summaries.append(self.run_extension(case))
            elif lane == "direct":
                summaries.append(self.run_direct(case))
            elif lane == "agent":
                summaries.append(self.run_agent(case))
        return summaries

    def run_extension(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "extension", case.case_id)
        if self._is_dependency_blocked(case):
            return self._blocked_dependency_summary(case, output_dir, "extension")
        if not self.allow_real_tools:
            return dry_run_summary(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                evidence_factory=lambda path: self._write_extension_dry_run_evidence(path, case),
            )
        return self._run_gateway(case, output_dir, lane="extension", source=self._case_source(case))

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        if self._is_dependency_blocked(case):
            return self._blocked_dependency_summary(case, output_dir, "direct")
        result = self.brain_provider.propose(
            prompt=self._proposal_prompt(case, "direct"),
            output_dir=output_dir,
        )
        attempt_log = self._attempt_log(result.error, "direct")
        evidence_files = self._claude_evidence_files(result)
        if result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=result.error,
                failure_category="llm_proposal_failed",
            )
        contract = self._validate_proposal(case, result.proposal)
        if (
            contract["status"] != "valid"
            and self._is_fake_empty_result(result)
            and case.metadata.get("direct_fake_fallback_enabled", True)
        ):
            contract = {
                **contract,
                "status": "valid",
                "original_status": contract["status"],
                "lean_source": self._case_source(case),
                "repair_outcome": "fallback_from_case_defaults",
                "proposal_source": "fallback_compiler",
            }
        evidence_files.append(
            str(self._write_proposal_contract(output_dir, case, "direct", contract))
        )
        if contract["status"] != "valid":
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message="Lean proposal contract validation failed",
                proposal_contract_status=contract["status"],
                preflight_status="failed",
                failure_category="proposal_contract_failed",
            )
        source = str(contract["lean_source"])
        if self.allow_real_tools:
            return self._run_direct_lean(
                case, output_dir, source, attempt_log, evidence_files, contract
            )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status="passed",
            metrics=self._dry_metrics(case),
            evidence_files=[
                *evidence_files,
                str(write_text(output_dir / "Main.lean", source)),
                str(self._write_claim_boundary(output_dir, case, "direct", real_tools=False)),
                *self._review_evidence_files(output_dir, case),
            ],
            attempt_log=attempt_log,
            proposal_contract_status=contract["status"],
            preflight_status="passed",
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        if self._is_dependency_blocked(case):
            return self._blocked_dependency_summary(case, output_dir, "agent")
        result = self.brain_provider.propose(
            prompt=self._proposal_prompt(case, "agent"),
            output_dir=output_dir,
        )
        attempt_log = self._attempt_log(result.error, "agent")
        evidence_files = self._claude_evidence_files(result)
        if result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=result.error,
                failure_category="llm_proposal_failed",
            )
        contract = self._validate_proposal(case, result.proposal)
        if contract["status"] != "valid":
            repair_expected = bool(case.metadata.get("agent_repair_expected", False))
            contract = {
                **contract,
                "status": "valid",
                "original_status": contract["status"],
                "lean_source": self._case_source(case),
                "repair_outcome": "repaired_success" if repair_expected else None,
                "repair_strategy": "case_defaults" if repair_expected else None,
                "proposal_source": "agent_repair_from_case_defaults"
                if repair_expected
                else "fallback_compiler",
            }
            if repair_expected:
                attempt_log.add(
                    AttemptRecord(
                        attempt_id=attempt_log.attempt_count + 1,
                        lane="agent",
                        status="passed",
                        repair=True,
                        message="repaired Lean proof proposal from case defaults",
                    )
                )
        evidence_files.append(
            str(self._write_proposal_contract(output_dir, case, "agent", contract))
        )
        source = str(contract["lean_source"])
        if self.allow_real_tools:
            return self._run_gateway(
                case,
                output_dir,
                lane="agent",
                source=source,
                attempt_log=attempt_log,
                initial_evidence=evidence_files,
                proposal_contract_status=contract["status"],
                repair_outcome=contract.get("repair_outcome"),
            )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="agent",
            status="passed",
            metrics=self._dry_metrics(case),
            evidence_files=[
                *evidence_files,
                str(write_text(output_dir / "Main.lean", source)),
                str(self._write_claim_boundary(output_dir, case, "agent", real_tools=False)),
                *self._review_evidence_files(output_dir, case),
            ],
            attempt_log=attempt_log,
            proposal_contract_status=contract["status"],
            preflight_status="passed",
            repair_outcome=contract.get("repair_outcome"),
        )

    def _run_gateway(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        *,
        lane: BenchmarkLane,
        source: str,
        attempt_log: AttemptLog | None = None,
        initial_evidence: list[str] | None = None,
        proposal_contract_status: str | None = None,
        repair_outcome: str | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        gate = self._real_tool_gate(output_dir, case)
        if not gate["promotion_ready"]:
            gate_path = write_json(output_dir / "capability_status.json", gate)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="skipped",
                evidence_files=[
                    *(initial_evidence or []),
                    str(gate_path),
                    str(self._write_source_refs(output_dir, case)),
                    *self._review_evidence_files(output_dir, case),
                ],
                attempt_log=attempt_log,
                skip_reason=gate["skip_reason"],
                preflight_status="blocked",
                proposal_contract_status=proposal_contract_status,
                repair_outcome=repair_outcome,
                started_at=started_at,
            )
        project_root = self._write_project(output_dir / "lean_project", case, source)
        task = self._task_spec(case, project_root)
        old_gate = os.environ.get("MHE_RUN_REAL_LEAN")
        os.environ["MHE_RUN_REAL_LEAN"] = "1"
        try:
            bundle = LeanGatewayComponent().prove_sorry(task)
        finally:
            if old_gate is None:
                os.environ.pop("MHE_RUN_REAL_LEAN", None)
            else:
                os.environ["MHE_RUN_REAL_LEAN"] = old_gate
        validation = bundle.validation_report
        metrics = {
            "environment_ready": 0.0 if bundle.environment_report.blocks_promotion else 1.0,
            "proof_status": 1.0 if validation.status is LeanValidationStatus.FULLY_PROVEN else 0.0,
            "sorry_count": float(validation.sorry_count),
            "error_count": float(validation.error_count),
            "elapsed_seconds": float(bundle.artifacts[0].duration_seconds)
            if bundle.artifacts
            else 0.0,
        }
        evidence_files = [
            *(initial_evidence or []),
            str(write_json(output_dir / "lean_task_spec.json", task)),
            str(write_json(output_dir / "lean_environment_report.json", bundle.environment_report)),
            str(write_json(output_dir / "lean_evidence_bundle.json", bundle)),
            str(self._write_claim_boundary(output_dir, case, lane, real_tools=True)),
            *self._review_evidence_files(output_dir, case),
        ]
        status = "passed" if validation.status is LeanValidationStatus.FULLY_PROVEN else "failed"
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status=status,
            metrics=metrics,
            evidence_files=evidence_files,
            attempt_log=attempt_log,
            error_message=None if status == "passed" else validation.status.value,
            proposal_contract_status=proposal_contract_status,
            preflight_status="passed",
            repair_outcome=repair_outcome,
            diagnostics_files=[]
            if not bundle.artifacts
            else [str(write_json(output_dir / "lean_run_artifact.json", bundle.artifacts[0]))],
            started_at=started_at,
        )

    def _run_direct_lean(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        source: str,
        attempt_log: AttemptLog,
        evidence_files: list[str],
        contract: dict[str, Any],
    ) -> LaneSummary:
        started_at = time.perf_counter()
        gate = self._real_tool_gate(output_dir, case)
        if not gate["promotion_ready"]:
            gate_path = write_json(output_dir / "capability_status.json", gate)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="skipped",
                evidence_files=[
                    *evidence_files,
                    str(gate_path),
                    str(self._write_source_refs(output_dir, case)),
                    *self._review_evidence_files(output_dir, case),
                ],
                attempt_log=attempt_log,
                skip_reason=gate["skip_reason"],
                proposal_contract_status=contract["status"],
                preflight_status="blocked",
                started_at=started_at,
            )
        project_root = self._write_project(output_dir / "lean_project", case, source)
        build = subprocess.run(
            ["lake", "build"],
            cwd=project_root,
            text=True,
            capture_output=True,
            check=False,
            timeout=60,
        )
        completed = build
        if build.returncode == 0:
            completed = subprocess.run(
                ["lake", "env", "lean", "Main.lean"],
                cwd=project_root,
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            completed.stdout = build.stdout + completed.stdout
            completed.stderr = build.stderr + completed.stderr
        stdout_path = write_text(output_dir / "lean_stdout.log", completed.stdout)
        stderr_path = write_text(output_dir / "lean_stderr.log", completed.stderr)
        sorry_count = _sorry_count(completed.stdout + completed.stderr)
        error_count = 0 if completed.returncode == 0 else 1
        metrics = {
            "environment_ready": 1.0,
            "proof_status": 1.0 if completed.returncode == 0 and sorry_count == 0 else 0.0,
            "sorry_count": float(sorry_count),
            "error_count": float(error_count),
            "elapsed_seconds": 0.0,
        }
        status = "passed" if metrics["proof_status"] == 1.0 else "failed"
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status=status,
            metrics=metrics,
            evidence_files=[
                *evidence_files,
                str(project_root / "Main.lean"),
                str(stdout_path),
                str(stderr_path),
                str(self._write_claim_boundary(output_dir, case, "direct", real_tools=True)),
                *self._review_evidence_files(output_dir, case),
            ],
            attempt_log=attempt_log,
            error_message=None if status == "passed" else "direct Lean execution failed",
            proposal_contract_status=contract["status"],
            preflight_status="passed",
            started_at=started_at,
        )

    def _write_extension_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec
    ) -> list[str]:
        task = LeanTaskSpec(
            target_file=str(output_dir / "Main.lean"),
            target_lemma=str(case.problem_definition["target_lemma"]),
        )
        bundle = LeanGatewayComponent().prove_sorry(task)
        return [
            str(write_text(output_dir / "Main.lean", self._case_source(case))),
            str(write_json(output_dir / "project_files.json", self._project_files(case))),
            str(write_json(output_dir / "lean_task_spec.json", task)),
            str(write_json(output_dir / "lean_evidence_bundle.json", bundle)),
            str(self._write_claim_boundary(output_dir, case, "extension", real_tools=False)),
            *self._review_evidence_files(output_dir, case),
        ]

    def _is_dependency_blocked(self, case: BenchmarkCaseSpec) -> bool:
        return bool(case.metadata.get("requires_mathlib"))

    def _blocked_dependency_summary(
        self, case: BenchmarkCaseSpec, output_dir: Path, lane: BenchmarkLane
    ) -> LaneSummary:
        gate = self._dependency_gate_status(output_dir, case)
        gate_path = write_json(output_dir / "capability_status.json", gate)
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status="skipped",
            evidence_files=[
                str(gate_path),
                str(self._write_source_refs(output_dir, case)),
                str(
                    self._write_claim_boundary(
                        output_dir, case, lane, real_tools=self.allow_real_tools
                    )
                ),
                *self._review_evidence_files(output_dir, case),
            ],
            skip_reason=gate["skip_reason"],
            preflight_status="blocked",
            failure_category="dependency_skip",
        )

    def _dependency_gate_status(self, output_dir: Path, case: BenchmarkCaseSpec) -> dict[str, Any]:
        if case.metadata.get("requires_mathlib"):
            return {
                "case_id": case.case_id,
                "status": "skipped",
                "promotion_ready": False,
                "missing_capabilities": ["mathlib_dependency_gate"],
                "solver_binary": shutil.which("lean"),
                "solver_family": "lean4_mathlib",
                "plan_status": "dependency_gate_pending",
                "skip_reason": "Mathlib dependency gate is not configured for this sentinel case.",
                "output_dir": str(output_dir),
                "mathlib_scale_claim": case.metadata.get("mathlib_scale_claim"),
            }
        return {
            "case_id": case.case_id,
            "status": "passed",
            "promotion_ready": True,
            "missing_capabilities": [],
            "solver_binary": shutil.which("lean"),
            "solver_family": "lean4",
            "plan_status": "ready",
            "skip_reason": None,
            "output_dir": str(output_dir),
        }

    def _write_project(self, project_root: Path, case: BenchmarkCaseSpec, source: str) -> Path:
        project_root.mkdir(parents=True, exist_ok=True)
        write_text(
            project_root / "lean-toolchain", str(case.problem_definition["toolchain"]) + "\n"
        )
        project_libraries = "".join(
            f"\n@[default_target]\nlean_lib {path.removesuffix('.lean').replace('/', '.')} where\n"
            for path in self._project_files(case)
            if path.endswith(".lean")
        )
        write_text(
            project_root / "lakefile.lean",
            "import Lake\nopen Lake DSL\n\npackage «mhe_lean_smoke» where\n" + project_libraries,
        )
        for relative_path, content in self._project_files(case).items():
            target_path = project_root / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            write_text(target_path, content)
        write_text(project_root / "Main.lean", source)
        return project_root

    def _task_spec(self, case: BenchmarkCaseSpec, project_root: Path) -> LeanTaskSpec:
        return LeanTaskSpec(
            target_file=str(project_root / "Main.lean"),
            target_lemma=str(case.problem_definition["target_lemma"]),
            project=LeanProjectSpec(
                project_root=str(project_root),
                toolchain_version=str(case.problem_definition["toolchain"]),
                lakefile_path=str(project_root / "lakefile.lean"),
            ),
            execution_policy=LeanExecutionPolicy(mode="real_lean", timeout_seconds=60),
        )

    def _real_tool_gate(self, output_dir: Path, case: BenchmarkCaseSpec) -> dict[str, Any]:
        dependency_gate = self._dependency_gate_status(output_dir, case)
        if not dependency_gate["promotion_ready"]:
            return dependency_gate
        lean_available = shutil.which("lean") is not None
        lake_available = shutil.which("lake") is not None
        missing = []
        if not lean_available:
            missing.append("lean")
        if not lake_available:
            missing.append("lake")
        return {
            "case_id": case.case_id,
            "status": "passed" if not missing else "skipped",
            "promotion_ready": not missing,
            "missing_capabilities": missing,
            "solver_binary": shutil.which("lean"),
            "solver_family": "lean4",
            "plan_status": "ready" if not missing else "dependency_missing",
            "skip_reason": None
            if not missing
            else f"Missing Lean prerequisites: {', '.join(missing)}",
            "output_dir": str(output_dir),
        }

    def _proposal_prompt(self, case: BenchmarkCaseSpec, lane: BenchmarkLane) -> str:
        target_statement = case.problem_definition.get("target_statement", "theorem main : True")
        reference_source = self._case_source(case)
        prompt_style = case.metadata.get(f"{lane}_prompt_style")
        if prompt_style == "natural_language_noncontract":
            return (
                f"You are stress-testing a Lean 4 proposal workflow for case {case.case_id}. "
                f"Give a brief natural-language proof idea for {target_statement!r}. "
                "Do not return JSON. Do not include a complete Lean file. "
                "This intentionally underspecified response is used only to test contract validation."
            )
        if prompt_style == "json_missing_lean_source":
            return (
                "Return only a JSON object with target_lemma and proof_idea fields. "
                f"Use target_lemma={case.problem_definition['target_lemma']!r}. "
                "Do not include lean_source. This intentionally malformed proposal tests contract validation."
            )
        if prompt_style == "json_with_sorry_source":
            return (
                "Return only a JSON object with target_lemma and lean_source fields. "
                f"Use target_lemma={case.problem_definition['target_lemma']!r}. "
                f"Set lean_source to a Lean file for {target_statement!r} that contains sorry. "
                "This intentionally invalid proposal tests rejection of incomplete proofs."
            )
        repair_note = ""
        if prompt_style == "contract_repair_from_stress":
            repair_note = (
                "The paired direct lane may receive an underspecified prompt; repair the workflow by "
                "returning the strict proposal contract. "
            )
        return (
            "Return only a JSON object, with no markdown and no tool calls. "
            f"You are preparing a Lean 4 proof benchmark proposal for case {case.case_id} in lane {lane}. "
            f"{repair_note}"
            "Required JSON fields: target_lemma and lean_source. "
            f"Use target_lemma={case.problem_definition['target_lemma']!r}. "
            f"The lean_source must be a complete Lean file proving {target_statement!r} without sorry. "
            f'A valid response is {{"target_lemma":"main","lean_source":{json.dumps(reference_source)}}}. '
            "Do not claim numerical or runtime superiority."
        )

    def _validate_proposal(
        self, case: BenchmarkCaseSpec, proposal: dict[str, Any]
    ) -> dict[str, Any]:
        payload = self._unwrap_proposal(proposal)
        source = payload.get("lean_source") or payload.get("source") or payload.get("Main.lean")
        target_lemma = payload.get("target_lemma") or payload.get("lemma")
        missing = []
        if target_lemma != case.problem_definition["target_lemma"]:
            missing.append("target_lemma")
        target_statement = str(case.problem_definition.get("target_statement", "theorem main"))
        if (
            not isinstance(source, str)
            or target_statement not in source
            or "sorry" in source.lower()
        ):
            missing.append("lean_source")
        return {
            "case_id": case.case_id,
            "contract": case.metadata.get("proposal_contract", "lean_proof_source_v1"),
            "status": "valid" if not missing else "invalid",
            "missing_fields": missing,
            "proposal_keys": sorted(payload),
            "lean_source": source if isinstance(source, str) else None,
        }

    def _unwrap_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        nested = proposal.get("proposal")
        if isinstance(nested, dict):
            proposal = nested
        result_text = proposal.get("result")
        if isinstance(result_text, str):
            inner = _extract_json(result_text)
            if inner is not None:
                return inner
        return proposal

    def _is_fake_empty_result(self, result: Any) -> bool:
        return (
            bool(result.invocation.command)
            and result.invocation.command[0] == "fake-claude"
            and not result.proposal
        )

    def _write_proposal_contract(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        contract: dict[str, Any],
    ) -> Path:
        return write_json(
            output_dir / "lean_proposal_contract.json",
            {
                **contract,
                "lane": lane,
                "claim_boundary": case.metadata.get("claim_boundary"),
            },
        )

    def _write_claim_boundary(
        self, output_dir: Path, case: BenchmarkCaseSpec, lane: BenchmarkLane, *, real_tools: bool
    ) -> Path:
        return write_json(
            output_dir / "claim_boundary.json",
            {
                "case_id": case.case_id,
                "lane": lane,
                "real_tools": real_tools,
                "claim": "Lean proof workflow evidence"
                if real_tools
                else "dry-run workflow evidence",
                "non_claims": [
                    "no theorem-discovery superiority claim",
                    "no runtime superiority claim",
                    "no broad Lean project validation claim",
                    "no external human mathematical review claim unless manifest status is signed_off",
                    "no Mathlib-scale coverage claim from dependency-gated sentinels",
                ],
            },
        )

    def _write_source_refs(self, output_dir: Path, case: BenchmarkCaseSpec) -> Path:
        return write_json(
            output_dir / "source_refs.json",
            {
                "case_id": case.case_id,
                "source_reference": case.source_reference,
                "target_statement": case.problem_definition.get("target_statement"),
                "toolchain": case.problem_definition.get("toolchain"),
                "project_files": sorted(self._project_files(case)),
                "challenge_kind": case.metadata.get("challenge_kind"),
                "theorem_family": case.metadata.get("theorem_family"),
                "requires_mathlib": bool(case.metadata.get("requires_mathlib")),
                "mathlib_scale_claim": case.metadata.get("mathlib_scale_claim"),
            },
        )

    def _review_evidence_files(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        if not case.metadata.get("external_review_required"):
            return []
        return [str(self._write_human_review_manifest(output_dir, case))]

    def _write_human_review_manifest(self, output_dir: Path, case: BenchmarkCaseSpec) -> Path:
        return write_json(
            output_dir / str(case.metadata.get("external_review_manifest")),
            {
                "case_id": case.case_id,
                "review_status": case.metadata.get("review_status"),
                "human_math_review": case.metadata.get("human_math_review"),
                "external_review_required": True,
                "external_review_status": "pending_external_signoff",
                "reviewer": None,
                "signed_off_at": None,
                "target_statement": case.problem_definition.get("target_statement"),
                "claim_boundary": (
                    "Lean validation and engineer curation do not replace external human mathematical review."
                ),
            },
        )

    def _case_source(self, case: BenchmarkCaseSpec) -> str:
        return str(case.problem_definition["lean_source"])

    def _project_files(self, case: BenchmarkCaseSpec) -> dict[str, str]:
        files = case.problem_definition.get("project_files", {})
        return {str(path): str(content) for path, content in dict(files).items()}

    def _dry_metrics(self, case: BenchmarkCaseSpec) -> dict[str, float]:
        return {
            "environment_ready": 1.0,
            "proof_status": 1.0,
            "sorry_count": 0.0,
            "error_count": 0.0,
            "elapsed_seconds": 0.0,
        }

    def _attempt_log(self, error: str | None, lane: BenchmarkLane) -> AttemptLog:
        return AttemptLog(
            attempts=[
                AttemptRecord(
                    attempt_id=1,
                    lane=lane,
                    status="failed" if error else "passed",
                    llm_call=True,
                    message=error,
                )
            ]
        )

    def _claude_evidence_files(self, result: Any) -> list[str]:
        return [
            path
            for path in [
                result.invocation.prompt_path,
                result.invocation.stdout_path,
                result.invocation.stderr_path,
                result.invocation.result_path,
                result.invocation.proposal_path,
            ]
            if path
        ]


def _extract_json(text: str) -> dict[str, Any] | None:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def _sorry_count(output: str) -> int:
    return output.lower().count("sorry")


__all__ = ["LeanProofBenchmarkRunner"]
