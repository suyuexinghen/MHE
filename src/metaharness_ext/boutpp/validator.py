from __future__ import annotations

from metaharness.core.models import ValidationIssue
from metaharness_ext.boutpp.contracts import (
    BoutPPPostprocessReport,
    BoutPPRunArtifact,
    BoutPPValidationReport,
    BoutPPValidationSpec,
)
from metaharness_ext.boutpp.types import BoutPPValidationStatus


class BoutPPValidatorComponent:
    protected: bool = True

    def validate(
        self,
        artifact: BoutPPRunArtifact,
        plan_ref: str = "",
        postprocess: BoutPPPostprocessReport | None = None,
        validation_spec: BoutPPValidationSpec | None = None,
    ) -> BoutPPValidationReport:
        if artifact.status == "unavailable":
            return BoutPPValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                postprocess_ref=postprocess.report_id if postprocess else None,
                passed=False,
                status=BoutPPValidationStatus.ENVIRONMENT_UNAVAILABLE,
                messages=[artifact.error_message or "BOUT++ environment unavailable"],
                issues=[
                    ValidationIssue(
                        code="boutpp_environment_unavailable",
                        message=artifact.error_message or "BOUT++ environment unavailable",
                        subject=artifact.task_id,
                        blocks_promotion=True,
                    )
                ],
            )
        if artifact.status in {"timeout", "failed"}:
            return BoutPPValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                postprocess_ref=postprocess.report_id if postprocess else None,
                passed=False,
                status=BoutPPValidationStatus.RUNTIME_FAILED,
                messages=[artifact.error_message or f"run status {artifact.status}"],
                issues=[
                    ValidationIssue(
                        code="boutpp_runtime_failure",
                        message=artifact.error_message or f"run status {artifact.status}",
                        subject=artifact.task_id,
                        blocks_promotion=True,
                    )
                ],
            )
        if artifact.missing_artifacts:
            return BoutPPValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan_ref,
                artifact_ref=artifact.artifact_id,
                postprocess_ref=postprocess.report_id if postprocess else None,
                passed=False,
                status=BoutPPValidationStatus.ARTIFACT_MISSING,
                messages=[f"Missing artifacts: {', '.join(artifact.missing_artifacts)}"],
                issues=[
                    ValidationIssue(
                        code="boutpp_artifact_missing",
                        message=f"Missing artifacts: {', '.join(artifact.missing_artifacts)}",
                        subject=artifact.task_id,
                        blocks_promotion=True,
                    )
                ],
            )
        messages: list[str] = []
        issues: list[ValidationIssue] = []
        summary_metrics = dict(artifact.summary_metrics)
        if postprocess is not None:
            summary_metrics.update(postprocess.summary_metrics)
        if validation_spec is not None:
            if validation_spec.required_variables and postprocess is not None:
                missing_vars = [
                    name for name in validation_spec.required_variables if name not in postprocess.variable_names
                ]
                if missing_vars:
                    message = f"Missing variables: {', '.join(missing_vars)}"
                    issues.append(
                        ValidationIssue(
                            code="boutpp_variable_missing",
                            message=message,
                            subject=artifact.task_id,
                            blocks_promotion=True,
                        )
                    )
                    return BoutPPValidationReport(
                        task_id=artifact.task_id,
                        plan_ref=plan_ref,
                        artifact_ref=artifact.artifact_id,
                        postprocess_ref=postprocess.report_id,
                        passed=False,
                        status=BoutPPValidationStatus.VARIABLE_MISSING,
                        messages=[message],
                        summary_metrics=summary_metrics,
                        issues=issues,
                    )
            for key, threshold in validation_spec.metric_thresholds.items():
                value = summary_metrics.get(key)
                if value is not None and isinstance(value, (int, float)) and value > threshold:
                    message = f"Metric {key}={value} exceeds threshold {threshold}"
                    messages.append(message)
                    issues.append(
                        ValidationIssue(
                            code=f"boutpp_metric_{key}_exceeded",
                            message=message,
                            subject=artifact.task_id,
                            blocks_promotion=True,
                        )
                    )
            if issues:
                return BoutPPValidationReport(
                    task_id=artifact.task_id,
                    plan_ref=plan_ref,
                    artifact_ref=artifact.artifact_id,
                    postprocess_ref=postprocess.report_id if postprocess else None,
                    passed=False,
                    status=BoutPPValidationStatus.METRIC_THRESHOLD_EXCEEDED,
                    messages=messages,
                    summary_metrics=summary_metrics,
                    issues=issues,
                )
        return BoutPPValidationReport(
            task_id=artifact.task_id,
            plan_ref=plan_ref,
            artifact_ref=artifact.artifact_id,
            postprocess_ref=postprocess.report_id if postprocess else None,
            passed=artifact.status == "completed" and artifact.return_code in {None, 0},
            status=BoutPPValidationStatus.EXECUTED,
            messages=messages,
            summary_metrics=summary_metrics,
            issues=issues,
        )
