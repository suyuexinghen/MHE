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
from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import FealpyMeshSpec, FealpyProblemSpec
from metaharness_ext.fealpy.environment import FealpyEnvironmentProbeComponent
from metaharness_ext.fealpy.evidence import build_evidence_bundle
from metaharness_ext.fealpy.executor import FealpyExecutorComponent
from metaharness_ext.fealpy.validator import FealpyValidatorComponent

_ALLOWED_SPEC_FIELDS = set(FealpyProblemSpec.model_fields)
_ALLOWED_MESH_FIELDS = set(FealpyMeshSpec.model_fields)


class FealpyBenchmarkRunner:
    """Three-lane benchmark runner for FEALPy PDE cases."""

    def __init__(
        self,
        *,
        runs_root: Path,
        allow_real_tools: bool = False,
        brain_provider: ClaudeCLIBrainProvider | FakeClaudeCLIBrainProvider | None = None,
        adaptive_agent: bool = False,
        max_repair_attempts: int = 1,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
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
        if not self._fealpy_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="skipped",
                skip_reason="fealpy not available",
            )
        return self._run_extension_pipeline_lane(case=case, lane="extension", output_dir=output_dir)

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        prompt = self._fealpy_direct_prompt(case)
        claude_result: ClaudeCLIResult | None = None
        for retry in range(self.max_repair_attempts + 1):
            claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
            if not claude_result.error:
                break
        assert claude_result is not None
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
                error_message=f"(after {self.max_repair_attempts + 1} attempts) {claude_result.error}",
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
        if not self._fealpy_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
                skip_reason="fealpy not available",
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        return self._run_direct_script_lane(
            case=case,
            output_dir=output_dir,
            script_source=str(preflight["solve_py"]),
            evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
            attempt_log=attempt_log,
            preflight=preflight,
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        prompt = self._fealpy_agent_prompt(case)
        # Retry Claude call on transient errors (e.g. max-turns exceeded)
        claude_result: ClaudeCLIResult | None = None
        for retry in range(self.max_repair_attempts + 1):
            claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
            if not claude_result.error:
                break
        assert claude_result is not None  # unreachable — loop always runs at least once
        attempt_log = self._claude_attempt_log(claude_result.error, "agent")
        preflight = self._write_proposal_preflight(output_dir, case, "agent", claude_result)
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                attempt_log=attempt_log,
                evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
                error_message=f"(after {self.max_repair_attempts + 1} attempts) {claude_result.error}",
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if preflight["preflight_status"] != "passed":
            if self.max_repair_attempts > 0:
                repaired = self._propose_agent_preflight_repair(
                    case, output_dir, claude_result, preflight
                )
                if repaired is not None and repaired.get("preflight_status") == "passed":
                    preflight = repaired
                else:
                    return self._preflight_failure_summary(
                        case, "agent", claude_result, attempt_log, preflight
                    )
            else:
                return self._preflight_failure_summary(
                    case, "agent", claude_result, attempt_log, preflight
                )
        if not self.allow_real_tools:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="passed",
                metrics=expected_reference_metrics(case),
                evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
                attempt_log=attempt_log,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if not self._fealpy_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=[*self._claude_evidence_files(claude_result), preflight["path"]],
                skip_reason="fealpy not available",
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        evidence_files = [*self._claude_evidence_files(claude_result), preflight["path"]]
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

    def _validator_tolerances(self, case: BenchmarkCaseSpec) -> tuple[float, float]:
        l2_ref = case.metric_references.get("l2_error")
        h1_ref = case.metric_references.get("h1_error")
        l2_tol = float(l2_ref.tolerance) if l2_ref is not None and l2_ref.tolerance > 0 else 1e-3
        h1_tol = float(h1_ref.tolerance) if h1_ref is not None and h1_ref.tolerance > 0 else 0.5
        return l2_tol, h1_tol

    def _fealpy_available(self) -> bool:
        spec = FealpyProblemSpec(task_id="bench-probe")
        return FealpyEnvironmentProbeComponent().probe(spec).available

    @staticmethod
    def _coerce(v: Any, default: Any) -> Any:
        """Return *default* when *v* is ``None``, otherwise *v*.

        Claude proposals often set optional fields to explicit ``null``,
        which survives ``dict.get(key, default)`` and causes a Pydantic
        type error.  This helper turns ``None`` → *default* while
        preserving falsy-but-valid values (0, False, empty string).
        """
        return default if v is None else v

    def _build_spec(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        payload: dict[str, Any] | None = None,
    ) -> FealpyProblemSpec:
        problem = dict(case.problem_definition)
        if payload:
            problem.update(payload)
        mesh_payload = problem.get("mesh") if isinstance(problem.get("mesh"), dict) else {}
        return FealpyProblemSpec(
            task_id=str(problem.get("task_id", case.case_id)),
            pde_family=problem.get("pde_family", "poisson"),
            example_key=problem.get("example_key", 1),
            backend=problem.get("backend", "numpy"),
            mesh=FealpyMeshSpec(
                meshtype=mesh_payload.get("meshtype", problem.get("meshtype", "tri")),
                nx=mesh_payload.get("nx", problem.get("nx", 8)),
                ny=mesh_payload.get("ny", problem.get("ny", 8)),
                nz=mesh_payload.get("nz", problem.get("nz")),
                h=mesh_payload.get("h", problem.get("h")),
            ),
            fe_degree=self._coerce(problem.get("fe_degree"), 1),
            fe_space_type=self._coerce(problem.get("fe_space_type"), "Lagrange"),
            solver=self._coerce(problem.get("solver"), {}),
            adaptive_refinement=self._coerce(problem.get("adaptive_refinement"), 0),
            dt=max(float(self._coerce(problem.get("dt"), 0.01)), 0.01),
            num_time_steps=self._coerce(problem.get("num_time_steps"), 100),
            time_integrator=self._coerce(problem.get("time_integrator"), "implicit_euler"),
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
        spec: FealpyProblemSpec | None = None,
        evidence_files: list[str] | None = None,
        attempt_log: AttemptLog | None = None,
        proposal_contract_status: str | None = None,
        preflight_status: str | None = None,
        failure_category: str | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        try:
            spec = spec or self._build_spec(case, output_dir)
            env = FealpyEnvironmentProbeComponent().probe(spec)
            plan = FealpyCompilerComponent().compile(spec, environment=env)
            artifact = FealpyExecutorComponent().execute_plan(plan, environment=env)
            l2_tol, h1_tol = self._validator_tolerances(case)
            validation = FealpyValidatorComponent().validate(
                artifact, plan, l2_tolerance=l2_tol, h1_tolerance=h1_tol
            )
            evidence = build_evidence_bundle(artifact, validation, plan=plan, environment=env)
            metrics: dict[str, Any] = {
                **artifact.summary_metrics,
                **validation.summary_metrics,
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
                error_message="fealpy direct script timed out",
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
        for line in stdout.strip().splitlines():
            try:
                data = json.loads(line)
                if isinstance(data, dict) and any(key.endswith("error") for key in data):
                    return data
            except json.JSONDecodeError:
                continue
        return {}

    def _fealpy_direct_prompt(self, case: BenchmarkCaseSpec) -> str:
        problem = case.problem_definition
        backend = problem.get("backend", "numpy")
        meshtype = problem.get("meshtype", "tri")
        # Map meshtype to the correct fealpy mesh class name (verified in compiler.py)
        mesh_class = {
            "tri": "TriangleMesh",
            "quad": "QuadrangleMesh",
            "tet": "TetrahedronMesh",
            "hex": "HexahedronMesh",
            "uniform": "UniformMesh2d",
        }.get(meshtype, "TriangleMesh")
        return (
            "Output a JSON object with a solve_py field containing a complete Python script. "
            "The script must use fealpy with the verified API surface below. "
            f"Case: {case.case_id}, PDE={problem.get('pde_family', 'poisson')}, "
            f"mesh={meshtype} {problem.get('nx', 16)}x{problem.get('ny', 16)}, "
            f"degree={problem.get('fe_degree', 1)}, backend={backend}. "
            f"Use these EXACT import patterns (verified against installed fealpy): "
            f"from fealpy.backend import backend_manager as bm; "
            f"bm.set_backend('{backend}'); "
            f"from fealpy.fem import BilinearForm, LinearForm, DirichletBC; "
            f"from fealpy.fem import ScalarDiffusionIntegrator, ScalarSourceIntegrator; "
            f"from fealpy.functionspace import LagrangeFESpace; "
            f"from fealpy.mesh import {mesh_class}; "
            f"from fealpy.model import PDEModelManager; "
            f"from fealpy.solver import spsolve. "
            f"CRITICAL: use bm.set_backend() not set_backend() — the latter does NOT exist. "
            f"Flow: pde = PDEModelManager('poisson').get_example({problem.get('example_key', 1)}); "
            f"mesh = {mesh_class}.from_box([0,1,0,1], nx={problem.get('nx', 16)}, ny={problem.get('ny', 16)}); "
            f"space = LagrangeFESpace(mesh, p={problem.get('fe_degree', 1)}); "
            f"bform = BilinearForm(space); bform.add_integrator(ScalarDiffusionIntegrator()); "
            f"lform = LinearForm(space); lform.add_integrator(ScalarSourceIntegrator(pde.source)); "
            f"A = bform.assembly(); F = lform.assembly(); "
            f"A, F = DirichletBC(space, gd=pde.solution).apply(A, F); "
            f"uh = spsolve(A, F, solver='scipy'); "
            f"l2 = mesh.error(pde.solution, space.function(uh)); "
            f"h1 = mesh.error(pde.gradient, uh_func.grad_value); "
            f"Print json.dumps({{status:'completed', l2_error:float(l2), h1_error:float(h1), "
            f"dof:int(space.number_of_global_dofs()), wall_time:float(wall)}}). "
            f"Wrap in main() with try/except printing {{status:'failed',error:str(exc)}}. "
            'Return: {"solve_py": "<script>"}'
        )

    def _fealpy_agent_prompt(self, case: BenchmarkCaseSpec) -> str:
        problem = case.problem_definition
        return (
            "Output a JSON object with a fealpy_spec or spec_patch. "
            f"Case: {case.case_id}, PDE={problem.get('pde_family', 'poisson')}. "
            "Valid fields: task_id, pde_family (str), example_key (int), backend (numpy/pytorch/jax), "
            "mesh (nest: meshtype (tri/quad/uniform), nx (int>=2), ny (int|null), nz (int|null), h (float|null)), "
            "fe_degree (int), fe_space_type (Lagrange/FirstNedelec/RaviartThomas/HuZhang), "
            "solver (nest: method (mumps/scipy/cupy), max_iterations, atol, rtol), "
            "adaptive_refinement (int), dt (float), num_time_steps (int), "
            "time_integrator (str), timeout_seconds (int). "
            "CRITICAL: every field in fealpy_spec must have a concrete value — "
            "NEVER use null for dt, num_time_steps, time_integrator, solver, fe_degree, "
            "fe_space_type, adaptive_refinement, timeout_seconds. "
            "For a steady-state Poisson problem use: dt=0.01, num_time_steps=100, "
            "time_integrator='implicit_euler'. "
            f"Current: {json.dumps(problem, sort_keys=True)}. "
            'Return: {"fealpy_spec": {...}} or {"spec_patch": {...}}'
        )

    def _fealpy_repair_prompt(
        self, case: BenchmarkCaseSpec, spec: FealpyProblemSpec, summary: LaneSummary
    ) -> str:
        return (
            "Return only a JSON object, with no markdown and no tool calls. "
            f"The previous FEALPy spec for case {case.case_id} produced a failed validation. "
            "Propose a minimal spec_patch to fix the issue. "
            f"Failed metrics: {json.dumps(summary.metrics)}. "
            f"Missing metrics: {json.dumps(summary.missing_metrics)}. "
            f"Error: {summary.error_message or 'none'}. "
            f"Current spec mesh: nx={spec.mesh.nx}, ny={spec.mesh.ny}. "
            "The JSON object must include spec_patch with only changed fields."
        )

    def _propose_agent_repair(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        spec: FealpyProblemSpec,
        summary: LaneSummary,
    ) -> FealpyProblemSpec | None:
        prompt = self._fealpy_repair_prompt(case, spec, summary)
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        if claude_result.error:
            return None
        proposal = self._unwrap_claude_proposal(dict(claude_result.proposal))
        repair_payload = proposal.get("spec_patch") or proposal.get("fealpy_spec")
        if not isinstance(repair_payload, dict):
            return None
        merged = {**case.problem_definition, **repair_payload}
        unknown = sorted(set(merged) - _ALLOWED_SPEC_FIELDS - {"meshtype", "nx", "ny", "nz", "h"})
        if unknown:
            return None
        try:
            return self._build_spec(case, output_dir, merged)
        except ValidationError:
            return None

    def _preflight_repair_prompt(self, case: BenchmarkCaseSpec, preflight: dict[str, Any]) -> str:
        messages = preflight.get("messages", [])
        return (
            "Return only a JSON object with a fealpy_spec or spec_patch, no markdown. "
            f"The previous proposal for case {case.case_id} failed validation: "
            f"{'; '.join(messages)}. "
            "Fix the spec so every required field has a concrete value — "
            "NEVER use null for dt, num_time_steps, time_integrator, solver, "
            "fe_degree, fe_space_type, adaptive_refinement, timeout_seconds. "
            f"Current problem: {json.dumps(case.problem_definition, sort_keys=True)}. "
            'Return: {"fealpy_spec": {...}} or {"spec_patch": {...}}'
        )

    def _propose_agent_preflight_repair(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        claude_result: ClaudeCLIResult,
        preflight: dict[str, Any],
    ) -> dict[str, Any] | None:
        prompt = self._preflight_repair_prompt(case, preflight)
        repair_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        if repair_result.error:
            return None
        return self._write_proposal_preflight(output_dir, case, "agent", repair_result)

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
            if isinstance(spec_result, FealpyProblemSpec):
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
            key: value.model_dump(mode="json") if isinstance(value, FealpyProblemSpec) else value
            for key, value in payload.items()
            if key not in {"solve_py", "spec"}
        }
        preflight_path = write_json(output_dir / "proposal_preflight.json", path_payload)
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

    def _extract_agent_spec(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        proposal: dict[str, Any],
    ) -> FealpyProblemSpec | str:
        proposal = self._unwrap_claude_proposal(proposal)
        if isinstance(proposal.get("fealpy_spec"), dict):
            payload = dict(proposal["fealpy_spec"])
        elif isinstance(proposal.get("spec_patch"), dict):
            payload = {**case.problem_definition, **proposal["spec_patch"]}
        else:
            return "proposal must include fealpy_spec or spec_patch"
        unknown = sorted(set(payload) - _ALLOWED_SPEC_FIELDS - {"meshtype", "nx", "ny", "nz", "h"})
        if unknown:
            return f"unknown FealpyProblemSpec fields: {', '.join(unknown)}"
        mesh = payload.get("mesh")
        if isinstance(mesh, dict):
            unknown_mesh = sorted(set(mesh) - _ALLOWED_MESH_FIELDS)
            if unknown_mesh:
                return f"unknown FealpyMeshSpec fields: {', '.join(unknown_mesh)}"
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
    ) -> LaneSummary:
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status="failed",
            evidence_files=[*self._claude_evidence_files(result), preflight["path"]],
            attempt_log=attempt_log,
            error_message="; ".join(str(message) for message in preflight.get("messages", [])),
            proposal_contract_status=preflight["proposal_contract_status"],
            preflight_status=preflight["preflight_status"],
            failure_category=preflight["failure_category"],
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
