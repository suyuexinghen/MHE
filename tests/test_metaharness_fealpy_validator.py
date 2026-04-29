from __future__ import annotations

from metaharness_ext.fealpy.contracts import (
    FealpyRunArtifact,
    FealpyRunPlan,
)
from metaharness_ext.fealpy.types import FealpyValidationStatus
from metaharness_ext.fealpy.validator import FealpyValidatorComponent


def _artifact(**overrides) -> FealpyRunArtifact:
    defaults = {
        "artifact_id": "artifact-run-1",
        "run_id": "run-1",
        "task_id": "val-test",
        "plan_ref": "fealpy-val-test-abc",
        "status": "completed",
        "l2_error": 1e-8,
        "h1_error": 1e-6,
        "dof_count": 81,
        "summary_metrics": {"l2_error": 1e-8, "h1_error": 1e-6, "dof": 81},
        "evidence_refs": ["fealpy://run/val-test/run-1"],
    }
    defaults.update(overrides)
    return FealpyRunArtifact(**defaults)


def _plan() -> FealpyRunPlan:
    from metaharness_ext.fealpy.contracts import FealpyProblemSpec

    spec = FealpyProblemSpec(task_id="val-test", pde_family="poisson")
    return FealpyRunPlan(
        plan_id="fealpy-val-test-abc",
        task_id="val-test",
        run_id="run-1",
        spec=spec,
        workspace_dir="/tmp/.runs/fealpy/val-test/run-1",
        script_source="print('hello')",
    )


def test_validator_status_unavailable() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(status="unavailable", l2_error=None, h1_error=None)
    report = validator.validate(artifact, _plan())

    assert report.passed is False
    assert report.status == FealpyValidationStatus.ENVIRONMENT_INVALID
    assert any(i.code == "FEALPY_ENV_UNAVAILABLE" for i in report.issues)
    assert report.blocks_promotion is True


def test_validator_status_timeout() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(
        status="timeout", l2_error=None, h1_error=None, error_message="timed out after 30s"
    )
    report = validator.validate(artifact, _plan())

    assert report.passed is False
    assert report.status == FealpyValidationStatus.RUNTIME_FAILED
    assert any(i.code == "FEALPY_TIMEOUT" for i in report.issues)


def test_validator_status_failed() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(
        status="failed", l2_error=None, h1_error=None, error_message="Non-zero exit"
    )
    report = validator.validate(artifact, _plan())

    assert report.passed is False
    assert report.status == FealpyValidationStatus.RUNTIME_FAILED
    assert any(i.code == "FEALPY_RUNTIME_FAILED" for i in report.issues)


def test_validator_output_missing() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(status="completed", l2_error=None, h1_error=None)
    report = validator.validate(artifact, _plan())

    assert report.passed is False
    assert report.status == FealpyValidationStatus.OUTPUT_MISSING
    assert any(i.code == "FEALPY_OUTPUT_MISSING" for i in report.issues)


def test_validator_l2_exceeds_tolerance() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(l2_error=0.01, h1_error=1e-6)
    report = validator.validate(artifact, _plan())

    assert report.passed is False
    assert report.status == FealpyValidationStatus.NUMERIC_VALIDATION_FAILED
    assert report.l2_passed is False
    assert report.h1_passed is True
    assert any(i.code == "FEALPY_L2_TOLERANCE" for i in report.issues)


def test_validator_h1_exceeds_tolerance() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(l2_error=1e-8, h1_error=0.01)
    report = validator.validate(artifact, _plan())

    assert report.passed is False
    assert report.status == FealpyValidationStatus.NUMERIC_VALIDATION_FAILED
    assert report.l2_passed is True
    assert report.h1_passed is False
    assert any(i.code == "FEALPY_H1_TOLERANCE" for i in report.issues)


def test_validator_both_pass() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(l2_error=1e-8, h1_error=1e-6)
    report = validator.validate(artifact, _plan())

    assert report.passed is True
    assert report.status == FealpyValidationStatus.EXECUTED
    assert report.l2_passed is True
    assert report.h1_passed is True
    assert report.blocks_promotion is False


def test_validator_custom_tolerances() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(l2_error=0.01, h1_error=0.05)
    report = validator.validate(artifact, _plan(), l2_tolerance=0.1, h1_tolerance=0.1)

    assert report.passed is True
    assert report.l2_tolerance == 0.1
    assert report.h1_tolerance == 0.1


def test_validator_null_plan() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(l2_error=1e-8, h1_error=1e-6)
    report = validator.validate(artifact, plan=None)

    assert report.passed is True
    assert report.plan_ref == artifact.plan_ref


def test_validator_summary_metrics_copied() -> None:
    validator = FealpyValidatorComponent()
    artifact = _artifact(l2_error=1e-8, h1_error=1e-6)
    report = validator.validate(artifact, _plan())

    assert "l2_error" in report.summary_metrics
    assert report.summary_metrics["l2_error"] == 1e-8
