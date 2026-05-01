from __future__ import annotations

from metaharness.core.models import ValidationIssue
from metaharness_ext.pycfd.contracts import PyCFDRunArtifact, PyCFDValidationReport
from metaharness_ext.pycfd.types import PyCFDValidationStatus


class PyCFDValidatorComponent:
    """Validates PyCFD run artifacts against residual-based tolerances.

    Protected slot — cannot be replaced via graph mutation.
    """

    protected: bool = True

    def __init__(self, residual_tolerance: float = 1e-5):
        self._residual_tolerance = residual_tolerance

    def validate(self, artifact: PyCFDRunArtifact, plan_ref: str = "") -> PyCFDValidationReport:
        task_id = artifact.task_id

        # Environment unavailable
        if artifact.status == "unavailable":
            return PyCFDValidationReport(
                task_id=task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=PyCFDValidationStatus.ENVIRONMENT_UNAVAILABLE,
                messages=["PyCFD environment is unavailable — cannot validate."],
                residual_tolerance=self._residual_tolerance,
                issues=[
                    ValidationIssue(
                        code="pycfd_environment_unavailable",
                        message="PyCFD environment is unavailable.",
                        subject=task_id,
                        blocks_promotion=True,
                    )
                ],
            )

        # Timeout
        if artifact.status == "timeout":
            return PyCFDValidationReport(
                task_id=task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=PyCFDValidationStatus.RUNTIME_FAILED,
                messages=[f"Execution timed out: {artifact.error_message}"],
                residual_tolerance=self._residual_tolerance,
                issues=[
                    ValidationIssue(
                        code="pycfd_timeout",
                        message=f"Execution timed out: {artifact.error_message}",
                        subject=task_id,
                        blocks_promotion=True,
                    )
                ],
            )

        # Runtime failure
        if artifact.status == "failed":
            return PyCFDValidationReport(
                task_id=task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=PyCFDValidationStatus.RUNTIME_FAILED,
                messages=[f"Execution failed: {artifact.error_message}"],
                residual_tolerance=self._residual_tolerance,
                issues=[
                    ValidationIssue(
                        code="pycfd_runtime_failure",
                        message=f"Execution failed: {artifact.error_message}",
                        subject=task_id,
                        blocks_promotion=True,
                    )
                ],
            )

        # Check residual norms
        issues: list[ValidationIssue] = []
        messages: list[str] = []
        rl1_ok = True
        rl2_ok = True

        if artifact.residual_l1 is not None:
            if artifact.residual_l1 > self._residual_tolerance:
                rl1_ok = False
                msg = f"L1 residual {artifact.residual_l1:.2e} exceeds tolerance {self._residual_tolerance:.2e}"
                messages.append(msg)
                issues.append(
                    ValidationIssue(
                        code="pycfd_residual_l1_exceeded",
                        message=msg,
                        subject=task_id,
                        blocks_promotion=True,
                    )
                )
        else:
            rl1_ok = False

        if artifact.residual_l2 is not None:
            if artifact.residual_l2 > self._residual_tolerance:
                rl2_ok = False
                msg = f"L2 residual {artifact.residual_l2:.2e} exceeds tolerance {self._residual_tolerance:.2e}"
                messages.append(msg)
                issues.append(
                    ValidationIssue(
                        code="pycfd_residual_l2_exceeded",
                        message=msg,
                        subject=task_id,
                        blocks_promotion=True,
                    )
                )
        else:
            rl2_ok = False

        passed = rl1_ok and rl2_ok and artifact.status == "completed"

        status = (
            PyCFDValidationStatus.EXECUTED if passed else PyCFDValidationStatus.RESIDUAL_EXCEEDED
        )

        return PyCFDValidationReport(
            task_id=task_id,
            plan_ref=plan_ref,
            artifact_ref=artifact.artifact_id,
            passed=passed,
            status=status,
            messages=messages,
            residual_tolerance=self._residual_tolerance,
            residual_l1_passed=rl1_ok,
            residual_l2_passed=rl2_ok,
            summary_metrics={
                k: v
                for k, v in {
                    "residual_l1": artifact.residual_l1,
                    "residual_l2": artifact.residual_l2,
                    "wall_time_seconds": artifact.wall_time_seconds,
                    "iterations": artifact.iterations,
                    "ncells": artifact.ncells,
                }.items()
                if v is not None
            },
            issues=issues,
        )
