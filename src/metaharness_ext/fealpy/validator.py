from __future__ import annotations

from metaharness.core.models import ValidationIssue
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.fealpy.capabilities import CAP_FEALPY_VALIDATE_REPORT
from metaharness_ext.fealpy.contracts import (
    FealpyRunArtifact,
    FealpyRunPlan,
    FealpyValidationReport,
)
from metaharness_ext.fealpy.slots import FEALPY_VALIDATOR_SLOT
from metaharness_ext.fealpy.types import FealpyValidationStatus


class FealpyValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(FEALPY_VALIDATOR_SLOT)
        api.declare_input("plan", "FealpyRunPlan", required=False)
        api.declare_input("artifact", "FealpyRunArtifact")
        api.declare_output("validation_report", "FealpyValidationReport", mode="sync")
        api.provide_capability(CAP_FEALPY_VALIDATE_REPORT)

    def validate(
        self,
        artifact: FealpyRunArtifact,
        plan: FealpyRunPlan | None = None,
        l2_tolerance: float = 1e-6,
        h1_tolerance: float = 1e-4,
    ) -> FealpyValidationReport:
        plan_ref = plan.plan_id if plan is not None else artifact.plan_ref
        issues: list[ValidationIssue] = []
        messages: list[str] = []

        if artifact.status == "unavailable":
            return FealpyValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=FealpyValidationStatus.ENVIRONMENT_INVALID,
                messages=["Executor reported environment unavailable"],
                l2_tolerance=l2_tolerance,
                h1_tolerance=h1_tolerance,
                issues=[
                    ValidationIssue(
                        code="FEALPY_ENV_UNAVAILABLE",
                        message="Environment unavailable",
                        blocks_promotion=True,
                    )
                ],
                evidence_refs=artifact.evidence_refs,
            )

        if artifact.status == "timeout":
            return FealpyValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=FealpyValidationStatus.RUNTIME_FAILED,
                messages=["Execution timed out"],
                l2_tolerance=l2_tolerance,
                h1_tolerance=h1_tolerance,
                issues=[
                    ValidationIssue(
                        code="FEALPY_TIMEOUT",
                        message=artifact.error_message or "Timeout",
                        blocks_promotion=True,
                    )
                ],
                evidence_refs=artifact.evidence_refs,
            )

        if artifact.status == "failed":
            return FealpyValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=FealpyValidationStatus.RUNTIME_FAILED,
                messages=[artifact.error_message or "Execution failed"],
                l2_tolerance=l2_tolerance,
                h1_tolerance=h1_tolerance,
                issues=[
                    ValidationIssue(
                        code="FEALPY_RUNTIME_FAILED",
                        message=artifact.error_message or "Execution failed",
                        blocks_promotion=True,
                    )
                ],
                evidence_refs=artifact.evidence_refs,
            )

        if artifact.l2_error is None and artifact.h1_error is None:
            return FealpyValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                passed=False,
                status=FealpyValidationStatus.OUTPUT_MISSING,
                messages=["No error metrics in output"],
                l2_tolerance=l2_tolerance,
                h1_tolerance=h1_tolerance,
                issues=[
                    ValidationIssue(
                        code="FEALPY_OUTPUT_MISSING",
                        message="No L2 or H1 error in artifact",
                        blocks_promotion=True,
                    )
                ],
                evidence_refs=artifact.evidence_refs,
            )

        l2_passed = artifact.l2_error is not None and artifact.l2_error < l2_tolerance
        h1_passed = artifact.h1_error is not None and artifact.h1_error < h1_tolerance

        if not l2_passed:
            msg = (
                f"L2 error {artifact.l2_error:.2e} exceeds tolerance {l2_tolerance:.2e}"
                if artifact.l2_error is not None
                else "L2 error is None"
            )
            messages.append(msg)
            issues.append(
                ValidationIssue(
                    code="FEALPY_L2_TOLERANCE",
                    message=msg,
                    blocks_promotion=True,
                )
            )

        if not h1_passed:
            msg = (
                f"H1 error {artifact.h1_error:.2e} exceeds tolerance {h1_tolerance:.2e}"
                if artifact.h1_error is not None
                else "H1 error is None"
            )
            messages.append(msg)
            issues.append(
                ValidationIssue(
                    code="FEALPY_H1_TOLERANCE",
                    message=msg,
                    blocks_promotion=True,
                )
            )

        all_passed = l2_passed and h1_passed

        return FealpyValidationReport(
            task_id=artifact.task_id,
            plan_ref=plan_ref,
            artifact_ref=artifact.artifact_id,
            passed=all_passed,
            status=FealpyValidationStatus.EXECUTED
            if all_passed
            else FealpyValidationStatus.NUMERIC_VALIDATION_FAILED,
            messages=messages,
            l2_tolerance=l2_tolerance,
            h1_tolerance=h1_tolerance,
            l2_passed=l2_passed,
            h1_passed=h1_passed,
            summary_metrics=dict(artifact.summary_metrics),
            issues=issues,
            evidence_refs=artifact.evidence_refs,
        )
