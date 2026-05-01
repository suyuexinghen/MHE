from __future__ import annotations

from metaharness_ext.pycfd.contracts import PyCFDRunArtifact
from metaharness_ext.pycfd.types import PyCFDValidationStatus
from metaharness_ext.pycfd.validator import PyCFDValidatorComponent


def _artifact(**kwargs) -> PyCFDRunArtifact:
    defaults = {
        "artifact_id": "a1",
        "run_id": "r1",
        "task_id": "t1",
        "plan_ref": "p1",
        "status": "completed",
    }
    defaults.update(kwargs)
    return PyCFDRunArtifact(**defaults)


class TestPyCFDValidator:
    def test_passed_when_residuals_within_tolerance(self):
        v = PyCFDValidatorComponent(residual_tolerance=1e-5)
        a = _artifact(residual_l1=1e-6, residual_l2=1e-7)
        report = v.validate(a, plan_ref="p1")
        assert report.passed
        assert report.status == PyCFDValidationStatus.EXECUTED

    def test_fails_l1_exceeded(self):
        v = PyCFDValidatorComponent(residual_tolerance=1e-5)
        a = _artifact(residual_l1=1e-2, residual_l2=1e-7)
        report = v.validate(a, plan_ref="p1")
        assert not report.passed
        assert not report.residual_l1_passed
        assert report.residual_l2_passed
        assert report.status == PyCFDValidationStatus.RESIDUAL_EXCEEDED

    def test_fails_l2_exceeded(self):
        v = PyCFDValidatorComponent(residual_tolerance=1e-5)
        a = _artifact(residual_l1=1e-6, residual_l2=1e-2)
        report = v.validate(a, plan_ref="p1")
        assert not report.passed
        assert report.residual_l1_passed
        assert not report.residual_l2_passed

    def test_unavailable_environment(self):
        v = PyCFDValidatorComponent()
        a = _artifact(status="unavailable")
        report = v.validate(a)
        assert not report.passed
        assert report.status == PyCFDValidationStatus.ENVIRONMENT_UNAVAILABLE

    def test_timeout(self):
        v = PyCFDValidatorComponent()
        a = _artifact(status="timeout", error_message="Timed out")
        report = v.validate(a)
        assert not report.passed
        assert report.status == PyCFDValidationStatus.RUNTIME_FAILED

    def test_runtime_failure(self):
        v = PyCFDValidatorComponent()
        a = _artifact(status="failed", error_message="Something broke")
        report = v.validate(a)
        assert not report.passed
        assert report.status == PyCFDValidationStatus.RUNTIME_FAILED

    def test_custom_tolerance(self):
        v = PyCFDValidatorComponent(residual_tolerance=1e-3)
        a = _artifact(residual_l1=1e-4, residual_l2=1e-4)
        report = v.validate(a, plan_ref="p1")
        assert report.passed
        assert report.residual_tolerance == 1e-3

    def test_missing_residuals_fails(self):
        v = PyCFDValidatorComponent()
        a = _artifact(residual_l1=None, residual_l2=None)
        report = v.validate(a, plan_ref="p1")
        assert not report.passed
