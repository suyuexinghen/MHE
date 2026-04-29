import pytest

from metaharness_ext.fealpy.contracts import (
    FealpyMeshSpec,
    FealpyProblemSpec,
    FealpySolverSpec,
    FealpyValidationReport,
)
from metaharness_ext.fealpy.types import FealpyValidationStatus


def _spec() -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id="fealpy-poisson-1",
        pde_family="poisson",
        example_key=1,
        backend="numpy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=8, ny=8),
        fe_degree=1,
        solver=FealpySolverSpec(method="direct"),
    )


def test_fealpy_problem_spec_creation() -> None:
    spec = _spec()
    assert spec.task_id == "fealpy-poisson-1"
    assert spec.pde_family == "poisson"
    assert spec.example_key == 1
    assert spec.backend == "numpy"
    assert spec.mesh.nx == 8
    assert spec.fe_degree == 1


def test_fealpy_problem_spec_reject_unsafe_task_id() -> None:
    with pytest.raises(ValueError, match="task_id"):
        FealpyProblemSpec(task_id="../escape")


def test_fealpy_problem_spec_reject_invalid_degree() -> None:
    with pytest.raises(ValueError, match="fe_degree"):
        FealpyProblemSpec(task_id="bad-degree", fe_degree=0)


def test_fealpy_problem_spec_reject_negative_timeout() -> None:
    with pytest.raises(ValueError, match="timeout_seconds"):
        FealpyProblemSpec(task_id="bad-timeout", timeout_seconds=0)


def test_fealpy_problem_spec_reject_invalid_nx() -> None:
    with pytest.raises(ValueError, match="nx"):
        FealpyMeshSpec(nx=1)


def test_fealpy_solver_spec_reject_invalid_maxiter() -> None:
    with pytest.raises(ValueError, match="max_iterations"):
        FealpySolverSpec(max_iterations=0)


def test_fealpy_validation_report_blocks_promotion() -> None:
    from metaharness.core.models import ValidationIssue

    report = FealpyValidationReport(
        task_id="test",
        plan_ref="plan-1",
        artifact_ref="artifact-1",
        passed=False,
        issues=[
            ValidationIssue(
                code="FEALPY_L2_TOLERANCE",
                message="L2 error exceeds tolerance",
                subject="l2_error",
                blocks_promotion=True,
            )
        ],
    )
    assert report.blocks_promotion is True
    assert report.run_id == "artifact-1"


def test_fealpy_validation_report_no_issue_passes() -> None:
    report = FealpyValidationReport(
        task_id="test",
        plan_ref="plan-1",
        artifact_ref="artifact-1",
        passed=True,
        status=FealpyValidationStatus.EXECUTED,
        l2_passed=True,
        h1_passed=True,
    )
    assert report.passed is True
    assert report.blocks_promotion is False


def test_fealpy_problem_spec_defaults() -> None:
    spec = FealpyProblemSpec(task_id="minimal")
    assert spec.pde_family == "poisson"
    assert spec.example_key == 1
    assert spec.backend == "numpy"
    assert spec.mesh.meshtype == "tri"
    assert spec.mesh.nx == 8
    assert spec.fe_degree == 1
    assert spec.fe_space_type == "Lagrange"
    assert spec.adaptive_refinement == 0


def test_fealpy_study_spec_defaults() -> None:
    from metaharness_ext.fealpy.contracts import FealpyStudySpec

    spec = FealpyStudySpec(
        study_id="test-defaults",
        task_template=FealpyProblemSpec(task_id="minimal"),
    )
    assert spec.convergence_rule is None
    assert spec.target_tolerance is None
    assert spec.goal == "minimize"
    assert spec.objective == "l2_error"
