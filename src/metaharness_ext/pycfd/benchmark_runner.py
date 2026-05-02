from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    ClaudeCLIResult,
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
from metaharness.benchmark_drivers.runner_common import (
    dry_run_summary,
    expected_reference_metrics,
    write_lane_outputs,
)
from metaharness_ext.pycfd.compiler import PyCFDCompilerComponent
from metaharness_ext.pycfd.contracts import PyCFDMeshSpec, PyCFDProblemSpec
from metaharness_ext.pycfd.environment import PyCFDEnvironmentProbeComponent
from metaharness_ext.pycfd.evidence import build_evidence_bundle
from metaharness_ext.pycfd.executor import PyCFDExecutorComponent
from metaharness_ext.pycfd.validator import PyCFDValidatorComponent

_ALLOWED_SPEC_FIELDS = set(PyCFDProblemSpec.model_fields)
_ALLOWED_MESH_FIELDS = set(PyCFDMeshSpec.model_fields)


class PyCFDBenchmarkRunner:
    """Three-lane benchmark runner for PyCFD 2D Euler cases."""

    def __init__(
        self,
        *,
        runs_root: Path,
        allow_real_tools: bool = False,
        pycfd_src_path: str | None = None,
        brain_provider: ClaudeCLIBrainProvider | FakeClaudeCLIBrainProvider | None = None,
        adaptive_agent: bool = False,
        max_repair_attempts: int = 1,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.pycfd_src_path = pycfd_src_path
        self.brain_provider = brain_provider or FakeClaudeCLIBrainProvider()
        self.adaptive_agent = adaptive_agent
        self.max_repair_attempts = max(0, max_repair_attempts)
        if adaptive_agent and max_repair_attempts <= 1:
            self.max_repair_attempts = 3

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
                evidence_factory=lambda path: self._write_extension_evidence(path, case),
            )
        if not self._pycfd_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="skipped",
                skip_reason="PyCFD environment not available",
            )
        return self._run_extension_pipeline_lane(case=case, lane="extension", output_dir=output_dir)

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        prompt = self._pycfd_direct_prompt(case)
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        attempt_log = self._claude_attempt_log(claude_result.error, "direct")
        preflight = self._write_proposal_preflight(output_dir, case, "direct", claude_result)
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
                error_message=claude_result.error,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if preflight["preflight_status"] != "passed":
            return self._preflight_failure_summary(
                case, "direct", claude_result, attempt_log, preflight
            )
        if not self.allow_real_tools:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="passed",
                metrics=expected_reference_metrics(case),
                evidence_files=[
                    *self._claude_evidence_files(claude_result),
                    preflight["path"],
                    *self._write_direct_evidence(output_dir, case),
                ],
                attempt_log=attempt_log,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if not self._pycfd_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
                skip_reason="PyCFD environment not available",
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        script_source = preflight.get("solve_py")
        if script_source is None:
            spec = self._build_spec(case, output_dir)
            plan = PyCFDCompilerComponent(pycfd_src_path=self.pycfd_src_path).compile(
                spec, run_id=f"bench-{case.case_id}", workspace_dir=str(output_dir)
            )
            script_source = plan.script_source
            preflight["solve_py"] = script_source
        return self._run_direct_script_lane(
            case=case,
            output_dir=output_dir,
            script_source=str(script_source),
            evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
            attempt_log=attempt_log,
            preflight=preflight,
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        initial_proposal_dir = output_dir / "proposal_attempt_1"
        prompt = self._pycfd_agent_prompt(case)
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=initial_proposal_dir)
        attempt_log = self._claude_attempt_log(claude_result.error, "agent")
        preflight_evidence_files = self._claude_evidence_files(claude_result)
        preflight_repair_outcome = None
        preflight = self._write_proposal_preflight(
            output_dir, case, "agent", claude_result, attempt_id=1
        )
        preflight_evidence_files.append(preflight["path"])
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=preflight_evidence_files,
                error_message=claude_result.error,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if preflight["preflight_status"] != "passed":
            if self.max_repair_attempts > 0:
                repair = self._propose_agent_preflight_repair(case, output_dir, preflight)
                if repair is not None:
                    repaired, repair_result = repair
                    preflight_evidence_files.extend(self._claude_evidence_files(repair_result))
                    preflight_evidence_files.append(repaired["path"])
                    repair_passed = repaired.get("preflight_status") == "passed"
                    attempt_log.add(
                        AttemptRecord(
                            attempt_id=attempt_log.attempt_count + 1,
                            lane="agent",
                            status="passed" if repair_passed else "failed",
                            repair=True,
                            llm_call=True,
                            message="preflight repair passed"
                            if repair_passed
                            else "; ".join(str(m) for m in repaired.get("messages", [])),
                        )
                    )
                    if repair_passed:
                        preflight = repaired
                        preflight_repair_outcome = "preflight_repaired"
                    else:
                        preflight_repair_outcome = "preflight_unrepaired_failure"
                        return self._preflight_failure_summary(
                            case,
                            "agent",
                            claude_result,
                            attempt_log,
                            repaired,
                            evidence_files=preflight_evidence_files,
                            repair_outcome=preflight_repair_outcome,
                        )
                else:
                    attempt_log.add(
                        AttemptRecord(
                            attempt_id=attempt_log.attempt_count + 1,
                            lane="agent",
                            status="failed",
                            repair=True,
                            llm_call=True,
                            message="preflight repair did not return a usable proposal",
                        )
                    )
                    preflight_repair_outcome = "preflight_unrepaired_failure"
                    return self._preflight_failure_summary(
                        case,
                        "agent",
                        claude_result,
                        attempt_log,
                        preflight,
                        evidence_files=preflight_evidence_files,
                        repair_outcome=preflight_repair_outcome,
                    )
            else:
                return self._preflight_failure_summary(
                    case,
                    "agent",
                    claude_result,
                    attempt_log,
                    preflight,
                    evidence_files=preflight_evidence_files,
                )
        if not self.allow_real_tools:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="passed",
                metrics=expected_reference_metrics(case),
                evidence_files=preflight_evidence_files,
                attempt_log=attempt_log,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
                repair_outcome=preflight_repair_outcome,
            )
        if not self._pycfd_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=preflight_evidence_files,
                skip_reason="PyCFD environment not available",
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
                repair_outcome=preflight_repair_outcome,
            )
        evidence_files = preflight_evidence_files
        spec = preflight["spec"]
        records: list[AttemptRecord] = []
        for attempt_idx in range(self.max_repair_attempts + 1):
            is_repair = attempt_idx > 0
            records.append(
                AttemptRecord(
                    attempt_id=attempt_idx + 1,
                    lane="agent",
                    status="passed",
                    repair=is_repair,
                    llm_call=False,
                )
            )
            summary = self._run_extension_pipeline_lane(
                case=case,
                lane="agent",
                output_dir=output_dir,
                spec=spec,
                evidence_files=evidence_files,
                attempt_log=AttemptLog(attempts=list(records)),
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
            records[-1].status = "passed" if summary.passed else "failed"
            if summary.passed or attempt_idx >= self.max_repair_attempts:
                summary.attempt_count = len(records)
                summary.repair_count = sum(1 for r in records if r.repair)
                summary.llm_calls = sum(1 for r in records if r.llm_call)
                if is_repair:
                    summary.repair_outcome = (
                        "repaired_success" if summary.passed else "unrepaired_failure"
                    )
                return summary
            repair_result = self._propose_agent_repair(case, output_dir, spec, summary)
            if repair_result is None:
                summary.attempt_count = len(records)
                summary.repair_count = sum(1 for r in records if r.repair)
                summary.llm_calls = sum(1 for r in records if r.llm_call)
                summary.repair_outcome = "unrepaired_failure"
                return summary
            spec = repair_result
            records[-1].llm_call = True

    def _pycfd_available(self) -> bool:
        probe = PyCFDEnvironmentProbeComponent(pycfd_src_path=self.pycfd_src_path)
        return probe.probe(task_id="bench-probe").available

    @staticmethod
    def _coerce(v: Any, default: Any) -> Any:
        return default if v is None else v

    def _build_spec(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        payload: dict[str, Any] | None = None,
    ) -> PyCFDProblemSpec:
        problem = dict(case.problem_definition)
        if payload:
            problem.update(payload)
        mesh_payload = problem.get("mesh") if isinstance(problem.get("mesh"), dict) else {}
        return PyCFDProblemSpec(
            task_id=str(problem.get("task_id", case.case_id)),
            case_type=problem.get("case_type", "vortex"),
            mesh=PyCFDMeshSpec(
                mesh_type=mesh_payload.get("mesh_type", problem.get("mesh_type", "quad")),
                nx=mesh_payload.get("nx", problem.get("nx", 42)),
                ny=mesh_payload.get("ny", problem.get("ny", 21)),
                xb=mesh_payload.get("xb", problem.get("xb", -20.0)),
                xe=mesh_payload.get("xe", problem.get("xe", 20.0)),
                yb=mesh_payload.get("yb", problem.get("yb", -10.0)),
                ye=mesh_payload.get("ye", problem.get("ye", 10.0)),
            ),
            flow=self._coerce(problem.get("flow"), {}),
            solver=self._coerce(problem.get("solver"), {}),
            t_final=self._coerce(problem.get("t_final"), 1.0),
            dt=self._coerce(problem.get("dt"), 0.01),
            timeout_seconds=self._coerce(problem.get("timeout_seconds"), 300),
            promotion_metadata=self._coerce(problem.get("promotion_metadata"), {}),
            graph_metadata={
                **self._coerce(problem.get("graph_metadata"), {}),
                "benchmark_workspace": str(output_dir / "workspace"),
            },
            evidence_refs=self._coerce(problem.get("evidence_refs"), []),
        )

    def _run_extension_pipeline_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        output_dir: Path,
        spec: PyCFDProblemSpec | None = None,
        evidence_files: list[str] | None = None,
        attempt_log: AttemptLog | None = None,
        proposal_contract_status: str | None = None,
        preflight_status: str | None = None,
        failure_category: str | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        try:
            spec = spec or self._build_spec(case, output_dir)
            env = PyCFDEnvironmentProbeComponent(pycfd_src_path=self.pycfd_src_path).probe(
                task_id=spec.task_id
            )
            plan = PyCFDCompilerComponent(pycfd_src_path=self.pycfd_src_path).compile(
                spec, run_id=f"bench-{case.case_id}", workspace_dir=str(output_dir)
            )
            artifact = PyCFDExecutorComponent().execute(plan)
            validation = PyCFDValidatorComponent().validate(artifact, plan_ref=plan.plan_id)
            evidence = build_evidence_bundle(
                task_id=spec.task_id,
                environment=env,
                plan=plan,
                artifact=artifact,
                validation=validation,
            )
            metrics: dict[str, Any] = {
                **artifact.summary_metrics,
                **{k: v for k, v in validation.summary_metrics.items()},
            }
            write_json(output_dir / "validation.json", validation)
            write_json(output_dir / "evidence.json", evidence)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="passed" if validation.passed else "failed",
                metrics=metrics,
                evidence_files=[
                    *(evidence_files or []),
                    *evidence.evidence_refs,
                    str(output_dir / "validation.json"),
                    str(output_dir / "evidence.json"),
                ],
                attempt_log=attempt_log,
                proposal_contract_status=proposal_contract_status,
                preflight_status=preflight_status,
                failure_category=failure_category,
                started_at=started_at,
            )
        except Exception as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                evidence_files=evidence_files,
                attempt_log=attempt_log,
                error_message=str(exc),
                proposal_contract_status=proposal_contract_status,
                preflight_status=preflight_status,
                failure_category=failure_category,
                started_at=started_at,
            )

    def _run_direct_script_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        script_source: str,
        evidence_files: list[str],
        attempt_log: AttemptLog,
        preflight: dict[str, Any],
    ) -> LaneSummary:
        started_at = time.perf_counter()
        script_path = output_dir.resolve() / "solve.py"
        write_text(script_path, script_source)

        stdout_path = output_dir / "stdout.txt"
        stderr_path = output_dir / "stderr.txt"
        run_evidence = [*evidence_files, str(script_path), str(stdout_path), str(stderr_path)]
        try:
            result = subprocess.run(
                ["python", str(script_path)],
                cwd=str(output_dir.resolve()),
                text=True,
                capture_output=True,
                check=False,
                timeout=int(case.problem_definition.get("timeout_seconds", 300)),
            )
        except subprocess.TimeoutExpired:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                evidence_files=run_evidence,
                attempt_log=attempt_log,
                error_message="PyCFD direct script timed out",
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category="solver_failure",
                started_at=started_at,
            )
        write_text(stdout_path, result.stdout)
        write_text(stderr_path, result.stderr)

        metrics = self._parse_metrics_from_stdout(result.stdout)
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status="passed" if result.returncode == 0 else "failed",
            metrics=metrics,
            evidence_files=run_evidence,
            attempt_log=attempt_log,
            error_message=result.stderr.strip() or None if result.returncode else None,
            proposal_contract_status=preflight["proposal_contract_status"],
            preflight_status=preflight["preflight_status"],
            failure_category=preflight["failure_category"]
            if result.returncode == 0
            else "solver_failure",
            started_at=started_at,
        )

    def _parse_metrics_from_stdout(self, stdout: str) -> dict[str, Any]:
        lines = stdout.strip().splitlines()
        for line in reversed(lines):
            try:
                data = json.loads(line)
                if isinstance(data, dict) and "status" in data:
                    return data
            except json.JSONDecodeError:
                continue
        return {}

    def _pycfd_direct_prompt(self, case: BenchmarkCaseSpec) -> str:
        problem = case.problem_definition
        return (
            "Output a JSON object with a solve_py field containing a complete Python script. "
            "The script must use PyCFD with the verified API surface below. "
            f"Case: {case.case_id}, case_type={problem.get('case_type', 'vortex')}, "
            f"mesh={problem.get('nx', 42)}x{problem.get('ny', 21)}, "
            f"t_final={problem.get('t_final', 1.0)}, dt={problem.get('dt', 0.01)}. "
            "Use these EXACT import patterns: "
            "import json, sys, os; "
            "sys.path.insert(0, os.environ.get('PYCFD_SRC_PATH', '.')); "
            "from Solvers import run_pycfd_case; "
            "config = {...}; "  # placeholder, fill with actual case config
            "result = run_pycfd_case(config); "
            "print(json.dumps(result)). "
            "CRITICAL: the script MUST print a single JSON line with status, residual_l1, "
            "residual_l2, wall_time_seconds, iterations, ncells, nnodes, nfaces. "
            "Wrap in try/except printing {status:'failed', error:str(exc)}. "
            'Return: {"solve_py": "<script>"}'
        )

    def _pycfd_agent_prompt(self, case: BenchmarkCaseSpec) -> str:
        problem = case.problem_definition
        return (
            "Output a JSON object with a pycfd_spec or spec_patch. "
            f"Case: {case.case_id}, case_type={problem.get('case_type', 'vortex')}. "
            "Valid fields: task_id, case_type (vortex/airfoil/cylinder/mms/shock_diffraction), "
            "mesh (nest: mesh_type (quad), nx (int>=2), ny (int>=2), xb, xe, yb, ye), "
            "flow (nest: M_inf (float>0), aoa, gamma (>1.0), rho_inf, p_inf), "
            "solver (nest: CFL (float 0-2), second_order (bool), use_limiter (bool), "
            "limiter, inviscid_flux (roe/hllc/van-leer), max_steps), "
            "t_final (float>0), dt (float>0), timeout_seconds (int>0). "
            "CRITICAL: every field must have a concrete value — NEVER use null. "
            f"Current: {json.dumps(problem, sort_keys=True, default=str)}. "
            'Return: {"pycfd_spec": {...}} or {"spec_patch": {...}}'
        )

    def _pycfd_repair_prompt(
        self, case: BenchmarkCaseSpec, spec: PyCFDProblemSpec, summary: LaneSummary
    ) -> str:
        return (
            "Return only a JSON object, with no markdown and no tool calls. "
            f"The previous PyCFD spec for case {case.case_id} produced a failed validation. "
            "Propose a minimal spec_patch to fix the issue. "
            f"Failed metrics: {json.dumps(summary.metrics)}. "
            f"Missing metrics: {json.dumps(summary.missing_metrics)}. "
            f"Error: {summary.error_message or 'none'}. "
            f"Current spec mesh: nx={spec.mesh.nx}, ny={spec.mesh.ny}. "
            "The JSON object must include spec_patch with only changed fields."
        )

    def _preflight_repair_prompt(self, case: BenchmarkCaseSpec, preflight: dict[str, Any]) -> str:
        messages = preflight.get("messages", [])
        return (
            "Return only a JSON object with a pycfd_spec or spec_patch, no markdown. "
            f"The previous proposal for case {case.case_id} failed validation: "
            f"{'; '.join(messages)}. "
            "Fix the spec so every required field has a concrete value. "
            f"Current problem: {json.dumps(case.problem_definition, sort_keys=True, default=str)}. "
            'Return: {"pycfd_spec": {...}} or {"spec_patch": {...}}'
        )

    def _propose_agent_repair(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        spec: PyCFDProblemSpec,
        summary: LaneSummary,
    ) -> PyCFDProblemSpec | None:
        prompt = self._pycfd_repair_prompt(case, spec, summary)
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        if claude_result.error:
            return None
        proposal = self._unwrap_claude_proposal(dict(claude_result.proposal))
        repair_payload = proposal.get("spec_patch") or proposal.get("pycfd_spec")
        if not isinstance(repair_payload, dict) or self._find_null_paths(repair_payload):
            return None
        merged = self._merge_problem_payload(
            spec.model_dump(mode="json", exclude_computed_fields=True), repair_payload
        )
        unknown = sorted(
            set(merged)
            - _ALLOWED_SPEC_FIELDS
            - {
                "mesh_type",
                "nx",
                "ny",
                "xb",
                "xe",
                "yb",
                "ye",
                "M_inf",
                "aoa",
                "gamma",
                "rho_inf",
                "p_inf",
                "CFL",
                "second_order",
                "use_limiter",
                "limiter",
                "inviscid_flux",
                "max_steps",
            }
        )
        if unknown:
            return None
        try:
            return self._build_spec(case, output_dir, merged)
        except ValidationError:
            return None

    def _propose_agent_preflight_repair(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        preflight: dict[str, Any],
    ) -> tuple[dict[str, Any], ClaudeCLIResult] | None:
        prompt = self._preflight_repair_prompt(case, preflight)
        attempt_id = 2
        repair_dir = output_dir / f"proposal_attempt_{attempt_id}"
        repair_result = self.brain_provider.propose(prompt=prompt, output_dir=repair_dir)
        if repair_result.error:
            return None
        repaired = self._write_proposal_preflight(
            output_dir, case, "agent", repair_result, attempt_id=attempt_id
        )
        return repaired, repair_result

    def _claude_attempt_log(self, error: str | None, lane: BenchmarkLane) -> AttemptLog:
        status = "failed" if error else "passed"
        return AttemptLog(
            attempts=[
                AttemptRecord(
                    attempt_id=1,
                    lane=lane,
                    status=status,
                    llm_call=True,
                    message=error,
                )
            ]
        )

    def _claude_evidence_files(self, result: ClaudeCLIResult) -> list[str]:
        return [
            result.invocation.prompt_path,
            result.invocation.stdout_path,
            result.invocation.stderr_path,
            result.invocation.result_path or "",
            result.invocation.proposal_path or "",
        ]

    def _is_fake_claude_result(self, result: ClaudeCLIResult) -> bool:
        return bool(result.invocation.command) and result.invocation.command[0] == "fake-claude"

    def _write_proposal_preflight(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        result: ClaudeCLIResult,
        *,
        attempt_id: int = 1,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "case_id": case.case_id,
            "lane": lane,
            "proposal_contract_status": "invalid",
            "preflight_status": "failed",
            "failure_category": "proposal_failure",
            "messages": [],
        }
        if result.error:
            payload["messages"].append(result.error)
        elif self._is_fake_claude_result(result) and not result.proposal:
            payload.update(
                {
                    "proposal_contract_status": "not_checked",
                    "preflight_status": "passed",
                    "failure_category": None,
                }
            )
        elif not isinstance(result.proposal, dict) or not result.proposal:
            payload["messages"].append("proposal must be a non-empty JSON object")
        elif lane == "direct":
            solve_py = self._extract_direct_script(result.proposal)
            if solve_py is None:
                payload["messages"].append("proposal must include solve_py")
            else:
                payload.update(
                    {
                        "proposal_contract_status": "valid",
                        "preflight_status": "passed",
                        "failure_category": None,
                        "solve_py": solve_py,
                    }
                )
        elif lane == "agent":
            spec_result = self._extract_agent_spec(case, output_dir, result.proposal)
            if isinstance(spec_result, PyCFDProblemSpec):
                payload.update(
                    {
                        "proposal_contract_status": "valid",
                        "preflight_status": "passed",
                        "failure_category": None,
                        "spec": spec_result,
                    }
                )
            else:
                payload["messages"].append(spec_result)
        path_payload = {
            key: value.model_dump(mode="json") if isinstance(value, PyCFDProblemSpec) else value
            for key, value in payload.items()
            if key not in {"solve_py", "spec"}
        }
        preflight_path = write_json(
            output_dir / f"proposal_preflight_attempt_{attempt_id}.json", path_payload
        )
        payload["path"] = str(preflight_path)
        return payload

    def _unwrap_claude_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        result_text = proposal.get("result")
        if isinstance(result_text, str):
            inner = self._extract_json_from_markdown(result_text)
            if inner is not None:
                return inner
        return proposal

    @staticmethod
    def _extract_json_from_markdown(text: str) -> dict[str, Any] | None:
        import re

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

    def _extract_direct_script(self, proposal: dict[str, Any]) -> str | None:
        proposal = self._unwrap_claude_proposal(proposal)
        candidate = proposal.get("solve_py") or proposal.get("solve.py")
        nested = proposal.get("proposal")
        if candidate is None and isinstance(nested, dict):
            candidate = nested.get("solve_py") or nested.get("solve.py")
        if isinstance(candidate, str) and candidate.strip():
            return candidate
        return None

    @staticmethod
    def _find_null_paths(payload: Any, prefix: str = "") -> list[str]:
        if isinstance(payload, dict):
            paths: list[str] = []
            for key, value in payload.items():
                child_prefix = f"{prefix}.{key}" if prefix else str(key)
                paths.extend(PyCFDBenchmarkRunner._find_null_paths(value, child_prefix))
            return paths
        if isinstance(payload, list):
            paths = []
            for index, value in enumerate(payload):
                child_prefix = f"{prefix}[{index}]"
                paths.extend(PyCFDBenchmarkRunner._find_null_paths(value, child_prefix))
            return paths
        return [prefix] if payload is None and prefix else []

    @staticmethod
    def _merge_problem_payload(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = PyCFDBenchmarkRunner._merge_problem_payload(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _extract_agent_spec(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        proposal: dict[str, Any],
    ) -> PyCFDProblemSpec | str:
        proposal = self._unwrap_claude_proposal(proposal)
        if isinstance(proposal.get("pycfd_spec"), dict):
            payload = dict(proposal["pycfd_spec"])
        elif isinstance(proposal.get("spec_patch"), dict):
            payload = self._merge_problem_payload(case.problem_definition, proposal["spec_patch"])
        else:
            return "proposal must include pycfd_spec or spec_patch"
        null_paths = self._find_null_paths(payload)
        if null_paths:
            return f"proposal contains null values: {', '.join(null_paths)}"
        unknown = sorted(
            set(payload)
            - _ALLOWED_SPEC_FIELDS
            - {
                "mesh_type",
                "nx",
                "ny",
                "xb",
                "xe",
                "yb",
                "ye",
                "M_inf",
                "aoa",
                "gamma",
                "rho_inf",
                "p_inf",
                "CFL",
                "second_order",
                "use_limiter",
                "limiter",
                "inviscid_flux",
                "max_steps",
            }
        )
        if unknown:
            return f"unknown PyCFDProblemSpec fields: {', '.join(unknown)}"
        mesh = payload.get("mesh")
        if isinstance(mesh, dict):
            unknown_mesh = sorted(set(mesh) - _ALLOWED_MESH_FIELDS)
            if unknown_mesh:
                return f"unknown PyCFDMeshSpec fields: {', '.join(unknown_mesh)}"
        try:
            return self._build_spec(case, output_dir, payload)
        except ValidationError as exc:
            return str(exc)

    def _preflight_failure_summary(
        self,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        result: ClaudeCLIResult,
        attempt_log: AttemptLog,
        preflight: dict[str, Any],
        *,
        evidence_files: list[str] | None = None,
        repair_outcome: str | None = None,
    ) -> LaneSummary:
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status="failed",
            evidence_files=evidence_files or [*self._claude_evidence_files(result), preflight["path"]],
            attempt_log=attempt_log,
            error_message="; ".join(str(message) for message in preflight.get("messages", [])),
            proposal_contract_status=preflight["proposal_contract_status"],
            preflight_status=preflight["preflight_status"],
            failure_category=preflight["failure_category"],
            repair_outcome=repair_outcome,
        )

    def _write_extension_evidence(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        validation_path = write_json(
            output_dir / "validation.json", {"passed": True, "dry_run": True}
        )
        evidence_path = write_json(
            output_dir / "evidence.json", {"case_id": case.case_id, "dry_run": True}
        )
        solver_path = write_text(output_dir / "generated_solver.py", "# dry-run solver\n")
        return [str(validation_path), str(evidence_path), str(solver_path)]

    def _write_direct_evidence(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        script_path = write_text(output_dir / "solve.py", "# dry-run direct solve\n")
        stdout_path = write_text(output_dir / "stdout.txt", "")
        stderr_path = write_text(output_dir / "stderr.txt", "")
        return [str(script_path), str(stdout_path), str(stderr_path)]
