from __future__ import annotations

import math
from pathlib import Path

from metaharness.core.models import (
    BudgetState,
    ConvergenceState,
    ScoredEvidence,
    ValidationIssue,
    ValidationIssueCategory,
)
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.octave.capabilities import CAP_OCTAVE_VALIDATE_REPORT
from metaharness_ext.octave.contracts import (
    OctaveOutputSpec,
    OctaveRunArtifact,
    OctaveRunPlan,
    OctaveValidationReport,
)
from metaharness_ext.octave.slots import OCTAVE_VALIDATOR_SLOT
from metaharness_ext.octave.types import OctaveValidationStatus


class OctaveValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OCTAVE_VALIDATOR_SLOT)
        api.declare_input("run", "OctaveRunArtifact")
        api.declare_input("plan", "OctaveRunPlan", required=False)
        api.declare_output("validation", "OctaveValidationReport", mode="sync")
        api.provide_capability(CAP_OCTAVE_VALIDATE_REPORT)

    def validate_run(
        self,
        artifact: OctaveRunArtifact,
        plan: OctaveRunPlan | None = None,
    ) -> OctaveValidationReport:
        messages: list[str] = []
        issues: list[ValidationIssue] = []
        missing_evidence: list[str] = []
        numeric_metrics: dict[str, float | str | bool] = {}
        evidence_files = self._build_evidence_files(artifact)
        evidence_refs = self._build_evidence_refs(artifact, evidence_files)

        if artifact.status == "unavailable":
            messages.append("Octave run is unavailable.")
            issues.append(
                self._issue("octave_run_unavailable", messages[-1], artifact.task_id, True)
            )
            return self._finalize_report(
                artifact,
                passed=False,
                status=OctaveValidationStatus.ENVIRONMENT_INVALID,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                numeric_metrics=numeric_metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
            )

        if artifact.status == "timeout" or artifact.terminal_error_type == "timeout":
            messages.append("Octave command timed out.")
            issues.append(
                self._issue("octave_command_timeout", messages[-1], artifact.task_id, True)
            )
            return self._finalize_report(
                artifact,
                passed=False,
                status=OctaveValidationStatus.RUNTIME_FAILED,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                numeric_metrics=numeric_metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
            )

        if artifact.return_code is None:
            messages.append("Octave command did not report an exit code.")
            issues.append(
                self._issue("octave_missing_exit_code", messages[-1], artifact.task_id, True)
            )
            return self._finalize_report(
                artifact,
                passed=False,
                status=OctaveValidationStatus.RUNTIME_FAILED,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                numeric_metrics=numeric_metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
            )

        if artifact.return_code != 0 or artifact.status == "failed":
            messages.append(f"Octave command exited with code {artifact.return_code}.")
            issues.append(
                self._issue("octave_runtime_failed", messages[-1], artifact.task_id, True)
            )
            return self._finalize_report(
                artifact,
                passed=False,
                status=OctaveValidationStatus.RUNTIME_FAILED,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                numeric_metrics=numeric_metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
            )

        for warning in artifact.warnings:
            if warning.severity == "blocking":
                issues.append(
                    self._issue("octave_blocking_warning", warning.message, artifact.task_id, True)
                )
            elif warning.severity == "suspicious":
                issues.append(
                    self._issue(
                        "octave_suspicious_warning", warning.message, artifact.task_id, False
                    )
                )

        expected_outputs = plan.expected_outputs if plan is not None else []
        for output in expected_outputs:
            output_missing = self._validate_output_presence(artifact, output)
            if output_missing is not None:
                missing_evidence.append(output_missing)
                issues.append(
                    self._issue(
                        "octave_output_missing",
                        f"Missing Octave output evidence: {output_missing}.",
                        artifact.task_id,
                        output.required,
                    )
                )
                continue
            output_issues = self._validate_numeric_output(artifact, output, numeric_metrics)
            issues.extend(output_issues)

        if not expected_outputs and not artifact.output_files and not artifact.parsed_outputs:
            missing_evidence.append("declared output evidence")
            issues.append(
                self._issue(
                    "octave_evidence_missing",
                    "Octave run completed without declared output evidence.",
                    artifact.task_id,
                    True,
                )
            )

        status = self._status_from_issues(issues, missing_evidence)
        passed = status is OctaveValidationStatus.EXECUTED
        messages.append(
            "Octave run completed with sufficient evidence."
            if passed
            else "Octave run completed but validation found issues."
        )
        return self._finalize_report(
            artifact,
            passed=passed,
            status=status,
            messages=messages,
            issues=issues,
            missing_evidence=missing_evidence,
            numeric_metrics=numeric_metrics,
            evidence_files=evidence_files,
            evidence_refs=evidence_refs,
        )

    def _validate_output_presence(
        self, artifact: OctaveRunArtifact, output: OctaveOutputSpec
    ) -> str | None:
        if output.kind == "variable":
            if (
                output.metric_key in artifact.parsed_outputs
                or output.metric_key in artifact.summary_metrics
            ):
                return None
            return f"variable:{output.metric_key}"
        if output.file_name is None:
            return f"file:{output.name}"
        output_paths = [
            Path(path).name for path in [*artifact.output_files, *artifact.figure_files]
        ]
        if output.file_name in output_paths:
            return None
        return output.file_name

    def _validate_numeric_output(
        self,
        artifact: OctaveRunArtifact,
        output: OctaveOutputSpec,
        numeric_metrics: dict[str, float | str | bool],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        value = artifact.numeric_value(output.metric_key)
        if value is None:
            return issues
        metric_prefix = output.metric_key
        numeric_metrics[f"{metric_prefix}.actual"] = value
        tolerance_spec = output.tolerance
        allow_nan = tolerance_spec.allow_nan if tolerance_spec is not None else False
        allow_inf = tolerance_spec.allow_inf if tolerance_spec is not None else False
        expected_value = tolerance_spec.expected_value if tolerance_spec is not None else None
        if math.isnan(value) and not allow_nan:
            issues.append(
                self._issue(
                    "octave_numeric_nan",
                    f"Octave output {output.metric_key} is NaN.",
                    f"{artifact.task_id}:{output.metric_key}",
                    True,
                )
            )
        if math.isinf(value) and not allow_inf:
            issues.append(
                self._issue(
                    "octave_numeric_inf",
                    f"Octave output {output.metric_key} is infinite.",
                    f"{artifact.task_id}:{output.metric_key}",
                    True,
                )
            )
        if isinstance(expected_value, int | float):
            tolerance = tolerance_spec.atol + tolerance_spec.rtol * abs(expected_value)
            error = abs(value - expected_value)
            numeric_metrics[f"{metric_prefix}.expected"] = expected_value
            numeric_metrics[f"{metric_prefix}.abs_error"] = error
            numeric_metrics[f"{metric_prefix}.tolerance"] = tolerance
            numeric_metrics[f"{metric_prefix}.within_tolerance"] = error <= tolerance
            if error > tolerance:
                issues.append(
                    self._issue(
                        "octave_numeric_tolerance_failed",
                        f"Octave output {output.metric_key} failed tolerance check.",
                        f"{artifact.task_id}:{output.metric_key}",
                        True,
                    )
                )
        metadata = artifact.output_metadata.get(output.metric_key, {})
        if output.shape is not None and metadata.get("shape") not in (None, output.shape):
            issues.append(
                self._issue(
                    "octave_output_shape_mismatch",
                    f"Octave output {output.metric_key} shape does not match expected shape.",
                    f"{artifact.task_id}:{output.metric_key}",
                    True,
                )
            )
        if output.dtype is not None and metadata.get("dtype") not in (None, output.dtype):
            issues.append(
                self._issue(
                    "octave_output_dtype_mismatch",
                    f"Octave output {output.metric_key} dtype does not match expected dtype.",
                    f"{artifact.task_id}:{output.metric_key}",
                    True,
                )
            )
        return issues

    def _status_from_issues(
        self, issues: list[ValidationIssue], missing_evidence: list[str]
    ) -> OctaveValidationStatus:
        if missing_evidence:
            return OctaveValidationStatus.OUTPUT_MISSING
        if any(issue.code.startswith("octave_numeric") for issue in issues):
            return OctaveValidationStatus.NUMERIC_VALIDATION_FAILED
        if any(issue.blocks_promotion for issue in issues):
            return OctaveValidationStatus.RUNTIME_FAILED
        return OctaveValidationStatus.EXECUTED

    def _build_evidence_files(self, artifact: OctaveRunArtifact) -> list[str]:
        return list(
            dict.fromkeys(
                [
                    *artifact.wrapper_files,
                    *artifact.input_files,
                    *artifact.output_files,
                    *artifact.figure_files,
                    *artifact.log_files,
                    *([artifact.stdout_path] if artifact.stdout_path else []),
                    *([artifact.stderr_path] if artifact.stderr_path else []),
                    *([artifact.status_path] if artifact.status_path else []),
                ]
            )
        )

    def _build_evidence_refs(
        self, artifact: OctaveRunArtifact, evidence_files: list[str]
    ) -> list[str]:
        refs = [
            f"octave://run/{artifact.task_id}/{artifact.run_id}",
            f"octave://artifact/{artifact.artifact_id}",
            *artifact.evidence_refs,
            *(f"octave://file/{Path(path).name}" for path in evidence_files),
        ]
        return list(dict.fromkeys(refs))

    def _issue(
        self, code: str, message: str, subject: str, blocks_promotion: bool
    ) -> ValidationIssue:
        return ValidationIssue(
            code=code,
            message=message,
            subject=subject,
            category=(
                ValidationIssueCategory.PROMOTION_BLOCKER
                if blocks_promotion
                else ValidationIssueCategory.READINESS
            ),
            blocks_promotion=blocks_promotion,
        )

    def _finalize_report(
        self,
        artifact: OctaveRunArtifact,
        *,
        passed: bool,
        status: OctaveValidationStatus,
        messages: list[str],
        issues: list[ValidationIssue],
        missing_evidence: list[str],
        numeric_metrics: dict[str, float | str | bool],
        evidence_files: list[str],
        evidence_refs: list[str],
    ) -> OctaveValidationReport:
        blocks_promotion = any(issue.blocks_promotion for issue in issues)
        governance_state = "blocked" if blocks_promotion else "ready" if passed else "defer"
        summary_metrics: dict[str, float | str | bool] = {
            "return_code": artifact.return_code if artifact.return_code is not None else "none",
            "has_output_files": bool(artifact.output_files),
            "has_parsed_outputs": bool(artifact.parsed_outputs),
            "warning_count": float(len(artifact.warnings)),
            "blocks_promotion": blocks_promotion,
            "status": status,
        }
        scored_evidence = ScoredEvidence(
            score=1.0 if passed else 0.0,
            metrics={
                key: float(value)
                for key, value in {**summary_metrics, **numeric_metrics}.items()
                if isinstance(value, int | float) and not isinstance(value, bool)
            },
            safety_score=1.0 if not blocks_promotion else 0.0,
            budget=BudgetState(used=1, exhausted=blocks_promotion),
            convergence=ConvergenceState(
                converged=passed,
                criteria_met=["octave_validation_passed"] if passed else [],
                reason="validator accepted run" if passed else "validator found issues",
            ),
            evidence_refs=evidence_refs,
            reasons=list(messages),
            attributes={
                "status": status.value,
                "governance_state": governance_state,
                "artifact_id": artifact.artifact_id,
            },
        )
        report = OctaveValidationReport(
            task_id=artifact.task_id,
            plan_ref=artifact.plan_ref,
            artifact_ref=artifact.run_id,
            passed=passed,
            status=status,
            messages=messages,
            summary_metrics=summary_metrics,
            issues=issues,
            governance_state=governance_state,
            missing_evidence=missing_evidence,
            numeric_metrics=numeric_metrics,
            evidence_files=evidence_files,
            evidence_refs=evidence_refs,
            scored_evidence=scored_evidence,
        )
        self._record_validation_snapshot(report)
        return report

    def _record_validation_snapshot(self, report: OctaveValidationReport) -> None:
        runtime = getattr(self, "_runtime", None)
        artifact_store = runtime.resolved_artifact_store() if runtime is not None else None
        if artifact_store is None:
            return
        artifact_store.save("validation_outcome", report.task_id, report.model_dump(mode="json"))
