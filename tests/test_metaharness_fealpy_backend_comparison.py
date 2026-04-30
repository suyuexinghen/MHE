from __future__ import annotations

import pytest

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec
from metaharness_ext.fealpy.backend_comparison import (
    BackendMetrics,
    FealpyBackendComparisonResult,
    FealpyBackendComparisonRunner,
)


class TestBackendMetrics:
    def test_default_status_unknown(self):
        m = BackendMetrics(backend="numpy")
        assert m.status == "unknown"
        assert m.wall_time is None

    def test_explicit_fields(self):
        m = BackendMetrics(
            backend="pytorch",
            wall_time=1.23,
            l2_error=0.001,
            h1_error=0.01,
            dof=100,
            status="completed",
        )
        assert m.backend == "pytorch"
        assert m.wall_time == 1.23
        assert m.l2_error == 0.001
        assert m.h1_error == 0.01
        assert m.dof == 100
        assert m.status == "completed"

    def test_failed_backend_with_error(self):
        m = BackendMetrics(backend="jax", status="failed", error_message="No GPU available")
        assert m.status == "failed"
        assert m.error_message == "No GPU available"


class TestFealpyBackendComparisonResult:
    def test_empty_result(self):
        result = FealpyBackendComparisonResult(case_id="test-case")
        assert result.case_id == "test-case"
        assert result.backends == []
        assert result.comparison_matrix == {}

    def test_with_backends(self):
        result = FealpyBackendComparisonResult(
            case_id="test-case",
            backends=[
                BackendMetrics(backend="numpy", wall_time=0.5),
                BackendMetrics(backend="pytorch", wall_time=0.3),
            ],
        )
        assert len(result.backends) == 2

    def test_model_dump_json(self):
        result = FealpyBackendComparisonResult(
            case_id="test-case",
            backends=[BackendMetrics(backend="numpy", wall_time=0.5)],
        )
        dumped = result.model_dump(mode="json")
        assert dumped["case_id"] == "test-case"
        assert dumped["backends"][0]["backend"] == "numpy"


class TestFealpyBackendComparisonRunner:
    @pytest.fixture
    def tmp_runs_root(self, tmp_path):
        return tmp_path / "runs"

    @pytest.fixture
    def runner(self, tmp_runs_root):
        return FealpyBackendComparisonRunner(runs_root=tmp_runs_root, allow_real_tools=False)

    @pytest.fixture
    def poisson_case(self):
        return BenchmarkCaseSpec(
            case_id="poisson-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Poisson, numpy",
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            problem_definition={
                "pde_family": "poisson",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "tri",
                "nx": 16,
                "ny": 16,
                "fe_degree": 1,
            },
        )

    def test_dry_run_returns_all_backends(self, runner, poisson_case):
        result = runner.compare_backends(poisson_case, backends=["numpy", "pytorch", "jax"])
        assert len(result.backends) == 3
        backend_names = [b.backend for b in result.backends]
        assert backend_names == ["numpy", "pytorch", "jax"]

    def test_dry_run_metrics_are_completed(self, runner, poisson_case):
        result = runner.compare_backends(poisson_case, backends=["numpy", "pytorch", "jax"])
        for backend_metrics in result.backends:
            assert backend_metrics.status == "completed"
            assert backend_metrics.wall_time == 0.1
            assert backend_metrics.l2_error == 0.001
            assert backend_metrics.h1_error == 0.01
            assert backend_metrics.dof == 81

    def test_dry_run_populates_comparison_matrix(self, runner, poisson_case):
        result = runner.compare_backends(poisson_case, backends=["numpy", "jax"])
        assert "numpy" in result.comparison_matrix
        assert "jax" in result.comparison_matrix
        assert result.comparison_matrix["numpy"]["wall_time"] == 0.1
        assert result.comparison_matrix["jax"]["l2_error"] == 0.001

    def test_different_backend_different_plan_id(self, runner, poisson_case):
        result = runner.compare_backends(poisson_case, backends=["numpy", "pytorch"])
        assert result.backends[0].backend != result.backends[1].backend

    def test_custom_backend_list(self, runner, poisson_case):
        result = runner.compare_backends(poisson_case, backends=["numpy"])
        assert len(result.backends) == 1
        assert result.backends[0].backend == "numpy"

    def test_result_case_id_matches_input(self, runner, poisson_case):
        result = runner.compare_backends(poisson_case, backends=["numpy"])
        assert result.case_id == poisson_case.case_id

    def test_dry_run_different_cases_produce_different_results(self, runner):
        case_a = BenchmarkCaseSpec(
            case_id="poisson-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="Poisson",
            source_reference={},
            expected_metrics=["l2_error"],
            problem_definition={"pde_family": "poisson", "backend": "numpy"},
        )
        case_b = BenchmarkCaseSpec(
            case_id="stokes-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="Stokes",
            source_reference={},
            expected_metrics=["l2_error"],
            problem_definition={"pde_family": "stokes", "backend": "numpy"},
        )
        result_a = runner.compare_backends(case_a, backends=["numpy"])
        result_b = runner.compare_backends(case_b, backends=["numpy"])
        assert result_a.case_id != result_b.case_id

    def test_compare_all_cases_dry_run(self, runner):
        results = runner.compare_all_cases(case_ids=["poisson-2d-numpy", "poisson-2d-pytorch"])
        assert len(results) == 2
        assert "poisson-2d-numpy" in results
        assert "poisson-2d-pytorch" in results
        for result in results.values():
            assert len(result.backends) == 3  # default backends
            assert result.case_id in results

    def test_compare_all_cases_respects_backends(self, runner):
        results = runner.compare_all_cases(case_ids=["poisson-2d-numpy"], backends=["numpy", "jax"])
        assert len(results["poisson-2d-numpy"].backends) == 2
