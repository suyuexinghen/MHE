from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.io import case_dir, write_json, write_text
from metaharness.benchmark_drivers.models import (
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


class FealpyBenchmarkRunner:
    """Three-lane benchmark runner for fealpy PDE cases.

    Follows the same pattern as OctaveBenchmarkRunner:
    - extension lane: compiler → executor → validator → evidence pipeline
    - direct lane: script execution via subprocess
    - agent lane: LLM proposal → extension pipeline
    """

    def __init__(
        self,
        *,
        runs_root: Path,
        allow_real_tools: bool = False,
        adaptive_agent: bool = False,
        max_repair_attempts: int = 1,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.adaptive_agent = adaptive_agent
        self.max_repair_attempts = max(0, max_repair_attempts)

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
        return self._run_extension_pipeline_lane(case=case, output_dir=output_dir)

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        if not self.allow_real_tools:
            metrics = expected_reference_metrics(case)
            evidence_files = self._write_direct_evidence(output_dir, case)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="passed",
                metrics=metrics,
                evidence_files=evidence_files,
            )
        if not self._fealpy_available():
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="skipped",
                skip_reason="fealpy not available",
            )
        return self._run_direct_script_lane(case=case, output_dir=output_dir)

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        if not self.allow_real_tools:
            metrics = expected_reference_metrics(case)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="passed",
                metrics=metrics,
            )
        return self._run_extension_pipeline_lane(case=case, output_dir=output_dir)

    # ── internal ──────────────────────────────────────────────────────────

    def _fealpy_available(self) -> bool:
        spec = FealpyProblemSpec(task_id="bench-probe")
        return FealpyEnvironmentProbeComponent().probe(spec).available

    def _build_spec(self, case: BenchmarkCaseSpec, output_dir: Path) -> FealpyProblemSpec:
        problem = case.problem_definition
        return FealpyProblemSpec(
            task_id=case.case_id,
            pde_family=problem.get("pde_family", "poisson"),
            example_key=problem.get("example_key", 1),
            backend=problem.get("backend", "numpy"),
            mesh=FealpyMeshSpec(
                meshtype=problem.get("meshtype", "tri"),
                nx=problem.get("nx", 8),
                ny=problem.get("ny", 8),
            ),
            fe_degree=problem.get("fe_degree", 1),
            timeout_seconds=problem.get("timeout_seconds", 300),
            workspace_dir=str(output_dir / "workspace"),
        )

    def _run_extension_pipeline_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        evidence_files: list[str] | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        try:
            spec = self._build_spec(case, output_dir)
            env = FealpyEnvironmentProbeComponent().probe(spec)
            plan = FealpyCompilerComponent().compile(spec, environment=env)
            artifact = FealpyExecutorComponent().execute_plan(plan, environment=env)
            validation = FealpyValidatorComponent().validate(artifact, plan)
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
                lane="extension",
                status="passed" if validation.passed else "failed",
                metrics=metrics,
                evidence_files=[
                    *(evidence_files or []),
                    *evidence.evidence_refs,
                    str(output_dir / "validation.json"),
                    str(output_dir / "evidence.json"),
                ],
                started_at=started_at,
            )
        except Exception as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="failed",
                evidence_files=evidence_files,
                error_message=str(exc),
                started_at=started_at,
            )

    def _run_direct_script_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        output_dir: Path,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        script_path = output_dir / "solve.py"
        spec = self._build_spec(case, output_dir)
        compiler = FealpyCompilerComponent()
        plan = compiler.compile(spec)
        write_text(script_path, plan.script_source)

        stdout_path = output_dir / "stdout.txt"
        stderr_path = output_dir / "stderr.txt"
        evidence_files = [str(script_path), str(stdout_path), str(stderr_path)]

        try:
            result = subprocess.run(
                ["python", str(script_path)],
                cwd=output_dir,
                text=True,
                capture_output=True,
                check=False,
                timeout=spec.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                evidence_files=evidence_files,
                error_message="fealpy script timed out",
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
            evidence_files=evidence_files,
            started_at=started_at,
        )

    def _parse_metrics_from_stdout(self, stdout: str) -> dict[str, Any]:
        import json

        for line in stdout.strip().splitlines():
            try:
                data = json.loads(line)
                if isinstance(data, dict) and "l2_error" in data:
                    return data
            except json.JSONDecodeError:
                continue
        return {}

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
