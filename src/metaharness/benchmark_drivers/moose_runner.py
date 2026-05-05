from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    FakeClaudeCLIBrainProvider,
)
from metaharness.benchmark_drivers.io import case_dir, write_json
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    BenchmarkLane,
    LaneSummary,
)
from metaharness.benchmark_drivers.runner_common import dry_run_summary, write_lane_outputs
from metaharness_ext.moose.contracts import (
    MooseExecutableSpec,
    MooseInputSpec,
    MooseOutputSpec,
    MooseProblemSpec,
    MooseWorkspaceSpec,
)
from metaharness_ext.moose.environment import MooseEnvironmentProbeComponent
from metaharness_ext.moose.evidence import build_evidence_bundle
from metaharness_ext.moose.executor import MooseExecutorComponent
from metaharness_ext.moose.input_compiler import MooseInputCompilerComponent
from metaharness_ext.moose.policy import MooseEvidencePolicy
from metaharness_ext.moose.validator import MooseValidatorComponent


class MooseBenchmarkRunner:
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
        if not self.allow_real_tools:
            return dry_run_summary(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                evidence_factory=lambda path: self._write_extension_dry_run_evidence(path, case),
            )
        return self._run_extension_pipeline(case, output_dir)

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        claude_result = self.brain_provider.propose(
            prompt=self._proposal_prompt(case, "direct"), output_dir=output_dir
        )
        attempt_log = self._attempt_log(claude_result.error, "direct")
        evidence_files = self._claude_evidence_files(claude_result)
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=claude_result.error,
                failure_category="llm_proposal_failed",
            )
        contract = self._validate_proposal(case, claude_result.proposal)
        preflight_path = self._write_proposal_contract(output_dir, case, "direct", contract)
        evidence_files.append(str(preflight_path))
        if contract["status"] != "valid":
            if case.metadata.get("allow_direct_fallback"):
                contract = self._fallback_contract(case, contract, source="fallback_compiler")
                preflight_path = self._write_proposal_contract(output_dir, case, "direct", contract)
                evidence_files.append(str(preflight_path))
            else:
                return write_lane_outputs(
                    runs_root=self.runs_root,
                    case=case,
                    lane="direct",
                    status="failed",
                    attempt_log=attempt_log,
                    evidence_files=evidence_files,
                    error_message="MOOSE proposal contract validation failed",
                    proposal_contract_status=contract["status"],
                    preflight_status="failed",
                    failure_category="proposal_contract_failed",
                )
        if self.allow_real_tools:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                skip_reason="direct real MOOSE CLI lane is not implemented in this first benchmark slice",
                proposal_contract_status=contract["status"],
                preflight_status="passed",
                repair_outcome=contract.get("repair_outcome"),
            )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status="passed",
            metrics=self._dry_metrics(case),
            evidence_files=[
                *evidence_files,
                *self._write_direct_dry_run_evidence(output_dir, case, contract),
            ],
            attempt_log=attempt_log,
            proposal_contract_status=contract["status"],
            preflight_status="passed",
            repair_outcome=contract.get("repair_outcome"),
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        claude_result = self.brain_provider.propose(
            prompt=self._proposal_prompt(case, "agent"), output_dir=output_dir
        )
        attempt_log = self._attempt_log(claude_result.error, "agent")
        evidence_files = self._claude_evidence_files(claude_result)
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=claude_result.error,
                failure_category="llm_proposal_failed",
            )
        contract = self._validate_proposal(case, claude_result.proposal)
        if contract["status"] != "valid":
            contract = self._fallback_contract(
                case, contract, source="agent_repair_from_case_defaults"
            )
            attempt_log.add(
                AttemptRecord(
                    attempt_id=attempt_log.attempt_count + 1,
                    lane="agent",
                    status="passed",
                    repair=True,
                    message="repaired MOOSE HIT proposal from case defaults",
                )
            )
        preflight_path = self._write_proposal_contract(output_dir, case, "agent", contract)
        evidence_files.append(str(preflight_path))
        if self.allow_real_tools:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                skip_reason="agent real MOOSE CLI lane is not implemented in this first benchmark slice",
                proposal_contract_status=contract["status"],
                preflight_status="passed",
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
                *self._write_agent_dry_run_evidence(output_dir, case, contract),
            ],
            attempt_log=attempt_log,
            proposal_contract_status=contract["status"],
            preflight_status="passed",
            repair_outcome=contract.get("repair_outcome"),
        )

    def _run_extension_pipeline(self, case: BenchmarkCaseSpec, output_dir: Path) -> LaneSummary:
        started_at = time.perf_counter()
        binary = self._real_binary(case)
        if binary is None:
            evidence = self._write_real_tool_gate(output_dir, case)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="skipped",
                evidence_files=[str(evidence)],
                skip_reason="MOOSE real binary not found; set MHE_MOOSE_BINARY or build test/moose_test-opt",
                preflight_status="blocked",
                started_at=started_at,
            )
        spec = self._problem_spec(case, output_dir, binary=binary)
        environment = MooseEnvironmentProbeComponent().probe(spec)
        if not environment.available:
            env_path = write_json(output_dir / "moose_environment_report.json", environment)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="skipped",
                evidence_files=[str(env_path)],
                skip_reason=f"MOOSE environment unavailable: {environment.status}",
                preflight_status="blocked",
                started_at=started_at,
            )
        plan = MooseInputCompilerComponent().compile(
            spec,
            environment=environment,
            run_id=f"{case.case_id}-real",
            workspace_dir=str(output_dir / "workspace"),
        )
        artifact = MooseExecutorComponent().execute_plan(plan, environment)
        validation = MooseValidatorComponent().validate_run(artifact, plan)
        bundle = build_evidence_bundle(
            task_id=case.case_id,
            environment=environment,
            plan=plan,
            artifact=artifact,
            validation=validation,
        )
        policy = MooseEvidencePolicy().evaluate(bundle)
        evidence_files = [
            str(write_json(output_dir / "moose_problem_spec.json", spec)),
            str(write_json(output_dir / "moose_environment_report.json", environment)),
            str(write_json(output_dir / "moose_run_plan.json", plan)),
            str(write_json(output_dir / "moose_run_artifact.json", artifact)),
            str(write_json(output_dir / "moose_validation_report.json", validation)),
            str(write_json(output_dir / "moose_evidence_bundle.json", bundle)),
            str(write_json(output_dir / "moose_policy_report.json", policy)),
        ]
        status = "passed" if validation.passed and policy.decision == "allow" else "failed"
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="extension",
            status=status,
            metrics={
                "spec_valid": 1.0,
                "plan_valid": 1.0,
                "output_count": float(artifact.summary_metrics.get("output_count", 0)),
                "elapsed_seconds": 0.0,
            },
            evidence_files=evidence_files,
            error_message=None if status == "passed" else validation.messages[-1],
            preflight_status="passed",
            started_at=started_at,
        )

    def _write_extension_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec
    ) -> list[str]:
        spec = self._problem_spec(case, output_dir, binary=self._default_binary(case))
        plan = MooseInputCompilerComponent().compile(
            spec,
            run_id=f"{case.case_id}-dry-run",
            workspace_dir=str(output_dir / "workspace"),
        )
        bundle = build_evidence_bundle(task_id=case.case_id, plan=plan)
        return [
            str(write_json(output_dir / "moose_problem_spec.json", spec)),
            str(write_json(output_dir / "moose_run_plan.json", plan)),
            str(write_json(output_dir / "moose_evidence_bundle.json", bundle)),
            str(
                write_json(
                    output_dir / "claim_boundary.json",
                    {
                        "real_tools": False,
                        "claim": "dry-run workflow evidence only",
                        "non_claims": [
                            "no real MOOSE execution",
                            "no numerical accuracy claim",
                            "no runtime superiority claim",
                        ],
                    },
                )
            ),
        ]

    def _problem_spec(
        self, case: BenchmarkCaseSpec, output_dir: Path, *, binary: str
    ) -> MooseProblemSpec:
        problem = case.problem_definition
        return MooseProblemSpec(
            task_id=case.case_id,
            executable=MooseExecutableSpec(
                binary_name=binary,
                timeout_seconds=120,
                env=self._moose_env(),
                source_root=str(case.source_reference.get("source_root"))
                if isinstance(case.source_reference, dict)
                else None,
            ),
            workspace=MooseWorkspaceSpec(
                working_directory=str(output_dir / "workspace"),
                output_directory="outputs",
            ),
            input=MooseInputSpec(
                mode="inline",
                inline_source=str(problem["input_source"]),
                input_filename=str(problem.get("input_filename", "input.i")),
            ),
            expected_outputs=[
                MooseOutputSpec(
                    name="exodus",
                    kind="exodus",
                    file_name=str(problem.get("expected_output", "input_out.e")),
                )
            ],
            graph_metadata={"benchmark_suite": case.suite, "case_id": case.case_id},
        )

    def _proposal_prompt(self, case: BenchmarkCaseSpec, lane: BenchmarkLane) -> str:
        return (
            f"Return a JSON MOOSE proposal for benchmark case {case.case_id} in lane {lane}. "
            "Required fields: input_source, expected_outputs. The input_source must be a HIT .i deck. "
            "Do not claim numerical superiority."
        )

    def _validate_proposal(
        self, case: BenchmarkCaseSpec, proposal: dict[str, Any]
    ) -> dict[str, Any]:
        missing = []
        input_source = proposal.get("input_source")
        if not isinstance(input_source, str) or "[Mesh]" not in input_source:
            missing.append("input_source")
        expected_outputs = proposal.get("expected_outputs")
        if not isinstance(expected_outputs, list) or not expected_outputs:
            missing.append("expected_outputs")
        return {
            "case_id": case.case_id,
            "contract": case.metadata.get("proposal_contract", "moose_hit_input_v1"),
            "status": "valid" if not missing else "invalid",
            "missing_fields": missing,
            "proposal_keys": sorted(proposal),
        }

    def _fallback_contract(
        self, case: BenchmarkCaseSpec, contract: dict[str, Any], *, source: str
    ) -> dict[str, Any]:
        return {
            **contract,
            "status": "valid",
            "original_status": contract["status"],
            "missing_fields": [],
            "repair_outcome": "repaired_from_case_defaults"
            if source.startswith("agent")
            else "fallback_from_case_defaults",
            "proposal_source": source,
            "repaired_fields": contract.get("missing_fields", []),
        }

    def _write_proposal_contract(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        contract: dict[str, Any],
    ) -> Path:
        return write_json(
            output_dir / "moose_proposal_contract.json",
            {
                **contract,
                "lane": lane,
                "claim_boundary": case.metadata.get("claim_boundary"),
            },
        )

    def _write_direct_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec, contract: dict[str, Any]
    ) -> list[str]:
        return [
            str(
                write_json(
                    output_dir / "direct_workflow_evidence.json",
                    {
                        "case_id": case.case_id,
                        "lane": "direct",
                        "execution_status": "dry_run_only",
                        "proposal_contract_status": contract["status"],
                        "proposal_source": contract.get("proposal_source", "claude_proposal"),
                        "non_claims": ["no real MOOSE execution", "no solver-quality claim"],
                    },
                )
            )
        ]

    def _write_agent_dry_run_evidence(
        self, output_dir: Path, case: BenchmarkCaseSpec, contract: dict[str, Any]
    ) -> list[str]:
        return [
            str(
                write_json(
                    output_dir / "agent_workflow_evidence.json",
                    {
                        "case_id": case.case_id,
                        "lane": "agent",
                        "execution_status": "dry_run_only",
                        "proposal_contract_status": contract["status"],
                        "repair_outcome": contract.get("repair_outcome"),
                        "non_claims": ["no real MOOSE execution", "no solver-quality claim"],
                    },
                )
            )
        ]

    def _write_real_tool_gate(self, output_dir: Path, case: BenchmarkCaseSpec) -> Path:
        return write_json(
            output_dir / "capability_status.json",
            {
                "case_id": case.case_id,
                "status": "skipped",
                "promotion_ready": False,
                "missing_capabilities": ["moose_test_app_binary"],
                "solver_binary": self._default_binary(case),
                "solver_family": "moose_test_app",
                "plan_status": "binary_missing_or_not_executable",
            },
        )

    def _dry_metrics(self, case: BenchmarkCaseSpec) -> dict[str, float]:
        metrics = {
            "spec_valid": 1.0,
            "plan_valid": 1.0,
            "output_count": 1.0,
        }
        if "elapsed_seconds" in case.expected_metrics:
            metrics["elapsed_seconds"] = 0.0
        return metrics

    def _real_binary(self, case: BenchmarkCaseSpec) -> str | None:
        binary = os.environ.get("MHE_MOOSE_BINARY") or self._default_binary(case)
        path = Path(binary).expanduser()
        if path.exists() and os.access(path, os.X_OK):
            return str(path)
        return None

    def _default_binary(self, case: BenchmarkCaseSpec) -> str:
        if isinstance(case.source_reference, dict) and case.source_reference.get("binary"):
            return str(case.source_reference["binary"])
        return str(case.metadata.get("real_tool_default_binary", "moose-opt"))

    def _moose_env(self) -> dict[str, str]:
        env = {
            key: value
            for key, value in {
                "PETSC_DIR": os.environ.get("PETSC_DIR", "/usr/lib64/petscdir"),
                "LIBMESH_DIR": os.environ.get(
                    "LIBMESH_DIR",
                    "/home/linden/code/work/Solvers/FEM/moose/libmesh/installed",
                ),
                "WASP_DIR": os.environ.get(
                    "WASP_DIR", "/home/linden/code/work/Solvers/FEM/moose/wasp_conda_install"
                ),
                "PKG_CONFIG_PATH": os.environ.get("PKG_CONFIG_PATH", "/usr/lib64/pkgconfig"),
            }.items()
            if value
        }
        return env

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

    def _claude_evidence_files(self, claude_result: Any) -> list[str]:
        return [
            claude_result.invocation.prompt_path,
            claude_result.invocation.stdout_path,
            claude_result.invocation.stderr_path,
            claude_result.invocation.result_path or "",
            claude_result.invocation.proposal_path or "",
        ]
