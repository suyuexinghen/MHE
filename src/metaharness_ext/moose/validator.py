from __future__ import annotations

from pathlib import Path

from metaharness.core.models import ValidationIssue
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.moose.capabilities import CAP_MOOSE_VALIDATE_REPORT
from metaharness_ext.moose.contracts import (
    MooseOutputSpec,
    MooseRunArtifact,
    MooseRunPlan,
    MooseValidationReport,
)
from metaharness_ext.moose.slots import MOOSE_VALIDATOR_SLOT
from metaharness_ext.moose.types import MooseValidationStatus


class MooseValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(MOOSE_VALIDATOR_SLOT)
        api.declare_input("run", "MooseRunArtifact")
        api.declare_input("plan", "MooseRunPlan", required=False)
        api.declare_output("validation", "MooseValidationReport", mode="sync")
        api.provide_capability(CAP_MOOSE_VALIDATE_REPORT)

    def validate_run(
        self,
        artifact: MooseRunArtifact,
        plan: MooseRunPlan | None = None,
    ) -> MooseValidationReport:
        messages: list[str] = []
        issues: list[ValidationIssue] = []
        missing_evidence: list[str] = []
        summary_metrics = dict(artifact.summary_metrics)
        evidence_refs = self._build_evidence_refs(artifact)

        if artifact.status == "unavailable":
            messages.append("MOOSE run is unavailable.")
            issues.append(
                self._issue("moose_run_unavailable", messages[-1], artifact.task_id, True)
            )
            return self._finalize(
                artifact,
                passed=False,
                status=MooseValidationStatus.ENVIRONMENT_INVALID,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                summary_metrics=summary_metrics,
                evidence_refs=evidence_refs,
            )

        if artifact.status == "timeout" or artifact.terminal_error_type == "timeout":
            messages.append("MOOSE command timed out.")
            issues.append(self._issue("moose_timeout", messages[-1], artifact.task_id, True))
            return self._finalize(
                artifact,
                passed=False,
                status=MooseValidationStatus.RUNTIME_FAILED,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                summary_metrics=summary_metrics,
                evidence_refs=evidence_refs,
            )

        if artifact.return_code is None:
            messages.append("MOOSE command did not report an exit code.")
            issues.append(
                self._issue("moose_missing_exit_code", messages[-1], artifact.task_id, True)
            )
            return self._finalize(
                artifact,
                passed=False,
                status=MooseValidationStatus.RUNTIME_FAILED,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                summary_metrics=summary_metrics,
                evidence_refs=evidence_refs,
            )

        if artifact.return_code != 0 or artifact.status == "failed":
            messages.append(f"MOOSE command exited with code {artifact.return_code}.")
            issues.append(self._issue("moose_runtime_failed", messages[-1], artifact.task_id, True))
            return self._finalize(
                artifact,
                passed=False,
                status=MooseValidationStatus.RUNTIME_FAILED,
                messages=messages,
                issues=issues,
                missing_evidence=missing_evidence,
                summary_metrics=summary_metrics,
                evidence_refs=evidence_refs,
            )

        for warning in artifact.warnings:
            if warning.severity == "blocking":
                issues.append(
                    self._issue("moose_blocking_warning", warning.message, artifact.task_id, True)
                )

        expected_outputs = plan.expected_outputs if plan is not None else []
        for output in expected_outputs:
            resolved = self._resolve_output_path(artifact, output)
            if resolved is None:
                missing_evidence.append(output.resolved_file_name)
                issues.append(
                    self._issue(
                        "moose_output_missing",
                        f"Missing MOOSE output evidence: {output.resolved_file_name}.",
                        artifact.task_id,
                        output.required,
                    )
                )

        if expected_outputs and any(issue.blocks_promotion for issue in issues):
            status = MooseValidationStatus.OUTPUT_MISSING
            passed = False
        else:
            status = MooseValidationStatus.EXECUTED
            passed = not any(issue.blocks_promotion for issue in issues)

        messages.append(
            "MOOSE run completed with sufficient evidence."
            if passed
            else "MOOSE run completed but validation found issues."
        )
        return self._finalize(
            artifact,
            passed=passed,
            status=status,
            messages=messages,
            issues=issues,
            missing_evidence=missing_evidence,
            summary_metrics=summary_metrics,
            evidence_refs=evidence_refs,
        )

    def _resolve_output_path(
        self, artifact: MooseRunArtifact, output: MooseOutputSpec
    ) -> str | None:
        resolved_name = output.resolved_file_name
        candidates = [Path(path) for path in artifact.output_files]
        candidates.extend(Path(path) for path in artifact.log_files)
        for path in candidates:
            if path.name == resolved_name and path.exists():
                return str(path)
        if output.kind == "exodus":
            exodus_name = resolved_name if resolved_name.endswith(".e") else f"{resolved_name}.e"
            for path in candidates:
                if path.name == exodus_name and path.exists():
                    return str(path)
        return None

    def _issue(
        self, code: str, message: str, subject: str, blocks_promotion: bool
    ) -> ValidationIssue:
        return ValidationIssue(
            code=code,
            message=message,
            subject=subject,
            blocks_promotion=blocks_promotion,
        )

    def _build_evidence_refs(self, artifact: MooseRunArtifact) -> list[str]:
        return list(
            dict.fromkeys([*artifact.evidence_refs, f"moose://artifact/{artifact.artifact_id}"])
        )

    def _finalize(
        self,
        artifact: MooseRunArtifact,
        *,
        passed: bool,
        status: MooseValidationStatus,
        messages: list[str],
        issues: list[ValidationIssue],
        missing_evidence: list[str],
        summary_metrics: dict[str, object],
        evidence_refs: list[str],
    ) -> MooseValidationReport:
        return MooseValidationReport(
            task_id=artifact.task_id,
            plan_ref=artifact.plan_ref,
            artifact_ref=artifact.artifact_id,
            passed=passed,
            status=status,
            messages=messages,
            summary_metrics=summary_metrics,
            missing_evidence=missing_evidence,
            issues=issues,
            evidence_refs=evidence_refs,
        )
