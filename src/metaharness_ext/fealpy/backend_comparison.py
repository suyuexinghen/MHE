from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from metaharness.benchmark_drivers.io import case_dir, write_json
from metaharness.benchmark_drivers.models import BenchmarkCaseSpec
from metaharness_ext.fealpy.benchmark_cases import get_fealpy_cases
from metaharness_ext.fealpy.compiler import FealpyCompilerComponent
from metaharness_ext.fealpy.contracts import FealpyMeshSpec, FealpyProblemSpec
from metaharness_ext.fealpy.environment import FealpyEnvironmentProbeComponent
from metaharness_ext.fealpy.executor import FealpyExecutorComponent
from metaharness_ext.fealpy.validator import FealpyValidatorComponent


class BackendMetrics(BaseModel):
    backend: str
    wall_time: float | None = None
    l2_error: float | None = None
    h1_error: float | None = None
    dof: int | None = None
    status: str = "unknown"
    error_message: str | None = None


class FealpyBackendComparisonResult(BaseModel):
    case_id: str
    backends: list[BackendMetrics] = Field(default_factory=list)
    comparison_matrix: dict[str, dict[str, Any]] = Field(default_factory=dict)


class FealpyBackendComparisonRunner:
    """Runs a single PDE case across numpy/pytorch/jax backends and produces
    a comparison matrix."""

    def __init__(self, *, runs_root: Path, allow_real_tools: bool = False) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools

    def compare_backends(
        self,
        case: BenchmarkCaseSpec,
        *,
        backends: list[str] | None = None,
    ) -> FealpyBackendComparisonResult:
        if backends is None:
            backends = ["numpy", "pytorch", "jax"]

        result = FealpyBackendComparisonResult(case_id=case.case_id)

        for backend in backends:
            metrics = self._run_single_backend(case, backend)
            result.backends.append(metrics)
            result.comparison_matrix[backend] = {
                "wall_time": metrics.wall_time,
                "l2_error": metrics.l2_error,
                "h1_error": metrics.h1_error,
                "dof": metrics.dof,
                "status": metrics.status,
            }

        return result

    def _run_single_backend(self, case: BenchmarkCaseSpec, backend: str) -> BackendMetrics:
        if not self.allow_real_tools:
            return self._dry_run_metrics(backend)

        problem = case.problem_definition
        spec = FealpyProblemSpec(
            task_id=case.case_id,
            pde_family=problem.get("pde_family", "poisson"),
            example_key=problem.get("example_key", 1),
            backend=backend,  # type: ignore[arg-type]
            mesh=FealpyMeshSpec(
                meshtype=problem.get("meshtype", "tri"),
                nx=problem.get("nx", 8),
                ny=problem.get("ny", 8),
                nz=problem.get("nz"),
            ),
            fe_degree=problem.get("fe_degree", 1),
            timeout_seconds=problem.get("timeout_seconds", 300),
        )

        env = FealpyEnvironmentProbeComponent().probe(spec)
        if not env.available or backend not in env.available_backends:
            return BackendMetrics(
                backend=backend,
                status="skipped",
                error_message=f"Backend '{backend}' is not available",
            )

        try:
            plan = FealpyCompilerComponent().compile(spec, environment=env)
            artifact = FealpyExecutorComponent().execute_plan(plan, environment=env)
            _validation = FealpyValidatorComponent().validate(artifact, plan)

            return BackendMetrics(
                backend=backend,
                wall_time=artifact.wall_time_seconds,
                l2_error=artifact.l2_error,
                h1_error=artifact.h1_error,
                dof=artifact.dof_count,
                status=artifact.status,
            )
        except Exception as exc:
            return BackendMetrics(
                backend=backend,
                status="failed",
                error_message=str(exc),
            )

    def _dry_run_metrics(self, backend: str) -> BackendMetrics:
        return BackendMetrics(
            backend=backend,
            wall_time=0.1,
            l2_error=0.001,
            h1_error=0.01,
            dof=81,
            status="completed",
        )

    def compare_all_cases(
        self,
        *,
        case_ids: list[str] | None = None,
        backends: list[str] | None = None,
    ) -> dict[str, FealpyBackendComparisonResult]:
        cases = get_fealpy_cases(case_ids)
        results: dict[str, FealpyBackendComparisonResult] = {}
        for case in cases:
            result = self.compare_backends(case, backends=backends)
            results[case.case_id] = result
            output_dir = case_dir(self.runs_root, "fealpy-pde", "comparison", case.case_id)
            write_json(output_dir / "backend_comparison.json", result.model_dump(mode="json"))
        return results
