from __future__ import annotations

from collections.abc import Iterable
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
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_VALIDATE
from metaharness_ext.deepmd.contracts import (
    DeepMDEvidenceBundle,
    DeepMDRunArtifact,
    DeepMDValidationReport,
)
from metaharness_ext.deepmd.evidence import build_evidence_bundle
from metaharness_ext.deepmd.slots import DEEPMD_VALIDATOR_SLOT


def _has_named_artifact(paths: Iterable[str], suffix: str) -> bool:
    return any(path.endswith(suffix) for path in paths)


class DeepMDValidatorComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_VALIDATOR_SLOT)
        api.declare_input("run", "DeepMDRunArtifact")
        api.declare_output("validation", "DeepMDValidationReport", mode="sync")
        api.provide_capability(CAP_DEEPMD_VALIDATE)

    def validate_run(self, artifact: DeepMDRunArtifact) -> DeepMDValidationReport:
        messages: list[str] = []
        issues: list[ValidationIssue] = []
        metrics: dict[str, float | str | bool] = {}
        fallback_reason = artifact.result_summary.get("fallback_reason")
        evidence_files = [
            path
            for path in [
                artifact.stdout_path,
                artifact.stderr_path,
                *artifact.workspace_files,
                *artifact.checkpoint_files,
                *artifact.model_files,
                *artifact.diagnostic_files,
            ]
            if path is not None
        ]
        evidence_refs = self._build_evidence_refs(artifact, evidence_files)

        if artifact.status == "unavailable" and fallback_reason:
            messages.append(f"DeepMD run unavailable: {fallback_reason}.")
            issues.append(
                ValidationIssue(
                    code=f"deepmd_{fallback_reason}",
                    message=f"DeepMD run unavailable: {fallback_reason}.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            status = "environment_invalid"
            if fallback_reason == "missing_remote_root":
                status = "remote_invalid"
            elif fallback_reason == "missing_scheduler_command":
                status = "scheduler_invalid"
            elif fallback_reason in {"missing_machine_root", "missing_python_runtime"}:
                status = "machine_invalid"
            return self._build_report(
                artifact,
                passed=False,
                status=status,
                messages=messages,
                summary_metrics=metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        if fallback_reason == "workspace_prepare_failed":
            messages.append("Workspace preparation failed.")
            issues.append(
                ValidationIssue(
                    code="deepmd_workspace_prepare_failed",
                    message="Workspace preparation failed.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                passed=False,
                status="workspace_failed",
                messages=messages,
                summary_metrics=metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        if artifact.return_code not in {0, None} or artifact.status == "failed":
            if artifact.return_code is not None:
                messages.append(f"DeepMD command exited with code {artifact.return_code}.")
            elif fallback_reason:
                messages.append(f"DeepMD command failed: {fallback_reason}.")
            else:
                messages.append("DeepMD command failed.")
            status = (
                "run_failed"
                if artifact.execution_mode in {"dpgen_run", "dpgen_simplify"}
                else "runtime_failed"
            )
            issues.append(
                ValidationIssue(
                    code=f"deepmd_{status}",
                    message=messages[-1],
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.READINESS,
                    blocks_promotion=True,
                )
            )
            return self._build_report(
                artifact,
                passed=False,
                status=status,
                messages=messages,
                summary_metrics=metrics,
                evidence_files=evidence_files,
                evidence_refs=evidence_refs,
                issues=issues,
            )

        passed = False
        status = "validation_failed"
        if artifact.execution_mode == "train":
            passed = bool(artifact.checkpoint_files or artifact.summary.learning_curve_path)
            status = "trained" if passed else "validation_failed"
            if passed:
                messages.append("Training produced checkpoints or a learning curve.")
        elif artifact.execution_mode == "freeze":
            passed = any(path.endswith(".pb") for path in artifact.model_files)
            status = "frozen" if passed else "validation_failed"
            if passed:
                messages.append("Freeze produced a frozen model artifact.")
        elif artifact.execution_mode == "test":
            passed = bool(artifact.summary.test_metrics)
            status = "tested" if passed else "validation_failed"
            if passed:
                messages.append("Test produced parseable RMSE metrics.")
                metrics.update(artifact.summary.test_metrics)
        elif artifact.execution_mode == "compress":
            compressed_model_path = artifact.summary.compressed_model_path
            passed = _has_named_artifact(artifact.model_files, "compressed_model.pb") or (
                compressed_model_path is not None and compressed_model_path.endswith(".pb")
            )
            status = "compressed" if passed else "validation_failed"
            if passed:
                messages.append("Compress produced a compressed model artifact.")
                if compressed_model_path is not None:
                    metrics["compressed_model_path"] = compressed_model_path
        elif artifact.execution_mode == "model_devi":
            passed = bool(artifact.summary.model_devi_metrics)
            status = "model_devi_computed" if passed else "validation_failed"
            if passed:
                messages.append("Model deviation diagnostics were produced.")
                metrics.update(artifact.summary.model_devi_metrics)
        elif artifact.execution_mode == "neighbor_stat":
            passed = bool(artifact.summary.neighbor_stat_metrics)
            status = "neighbor_stat_computed" if passed else "validation_failed"
            if passed:
                messages.append("Neighbor statistics diagnostics were produced.")
                metrics.update(artifact.summary.neighbor_stat_metrics)
        elif artifact.execution_mode in {"dpgen_run", "dpgen_simplify"}:
            collection = artifact.summary.dpgen_collection
            passed = bool(
                collection
                and collection.record_path
                and collection.iterations
                and all(
                    iteration.train_path and iteration.model_devi_path and iteration.fp_path
                    for iteration in collection.iterations
                )
            )
            if artifact.execution_mode == "dpgen_simplify" and passed:
                converged = any("converged" in message.lower() for message in collection.messages)
                status = "converged" if converged else "simplify_success"
                messages.append("DP-GEN simplify completed with iteration evidence.")
            else:
                status = "baseline_success" if passed else "validation_failed"
                if passed:
                    messages.append("DP-GEN baseline completed with iteration evidence.")
            if passed and collection is not None:
                metrics.update(
                    {
                        "candidate_count": float(collection.candidate_count),
                        "accurate_count": float(collection.accurate_count),
                        "failed_count": float(collection.failed_count),
                    }
                )
                if any("relabel" in message.lower() for message in collection.messages):
                    metrics["relabeling_detected"] = "true"
        elif artifact.execution_mode == "dpgen_autotest":
            passed = bool(artifact.summary.autotest_properties)
            status = "autotest_validated" if passed else "validation_failed"
            if passed:
                messages.append("Autotest produced structured property results.")
                for prop_name, prop_metrics in artifact.summary.autotest_properties.items():
                    for key, value in prop_metrics.items():
                        metrics[f"{prop_name}_{key}"] = value

        if artifact.summary.last_step is not None:
            metrics["last_step"] = float(artifact.summary.last_step)
        if artifact.summary.rmse_e_trn is not None:
            metrics["rmse_e_trn"] = artifact.summary.rmse_e_trn
        if artifact.summary.rmse_f_trn is not None:
            metrics["rmse_f_trn"] = artifact.summary.rmse_f_trn
        if artifact.summary.rmse_e_val is not None:
            metrics["rmse_e_val"] = artifact.summary.rmse_e_val
        if artifact.summary.rmse_f_val is not None:
            metrics["rmse_f_val"] = artifact.summary.rmse_f_val

        if not passed:
            messages.append(f"DeepMD {artifact.execution_mode} run completed but evidence insufficient.")
            issues.append(
                ValidationIssue(
                    code="deepmd_missing_evidence",
                    message=f"DeepMD {artifact.execution_mode} evidence insufficient.",
                    subject=artifact.task_id,
                    category=ValidationIssueCategory.PROMOTION_BLOCKER,
                    blocks_promotion=True,
                )
            )

        return self._build_report(
            artifact,
            passed=passed,
            status=status,
            messages=messages,
            summary_metrics=metrics,
            evidence_files=evidence_files,
            evidence_refs=evidence_refs,
            issues=issues,
        )

    def _build_report(
        self,
        artifact: DeepMDRunArtifact,
        *,
        passed: bool,
        status: str,
        messages: list[str],
        summary_metrics: dict[str, float | str | bool],
        evidence_files: list[str],
        evidence_refs: list[str],
        issues: list[ValidationIssue],
    ) -> DeepMDValidationReport:
        combined_metrics = {
            **summary_metrics,
            "return_code": artifact.return_code if artifact.return_code is not None else "none",
            "has_evidence_files": bool(evidence_files),
            "blocks_promotion": any(issue.blocks_promotion for issue in issues),
            "application_family": artifact.application_family,
            "execution_mode": artifact.execution_mode,
            "status": status,
        }
        scored_evidence = ScoredEvidence(
            score=1.0 if passed else 0.0,
            metrics={
                key: float(value)
                for key, value in combined_metrics.items()
                if isinstance(value, int | float)
            },
            safety_score=1.0 if passed else 0.0,
            budget=BudgetState(used=1, exhausted=not passed),
            convergence=ConvergenceState(
                converged=passed,
                criteria_met=[status] if passed else [],
                reason="validator accepted run" if passed else "validator blocked promotion",
            ),
            evidence_refs=evidence_refs,
            reasons=list(messages),
            attributes={
                "status": status,
                "application_family": artifact.application_family,
                "execution_mode": artifact.execution_mode,
                "governance_state": "ready" if passed else "blocked",
            },
        )
        return DeepMDValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=passed,
            status=status,
            messages=messages,
            summary_metrics=combined_metrics,
            evidence_files=evidence_files,
            evidence_refs=evidence_refs,
            issues=issues,
            blocks_promotion=any(issue.blocks_promotion for issue in issues),
            governance_state="ready" if passed else "blocked",
            scored_evidence=scored_evidence,
        )

    def _build_evidence_refs(self, artifact: DeepMDRunArtifact, evidence_files: list[str]) -> list[str]:
        refs = [
            f"deepmd://run/{artifact.task_id}/{artifact.run_id}",
            f"deepmd://run/{artifact.task_id}/{artifact.run_id}/mode/{artifact.execution_mode}",
            f"deepmd://run/{artifact.task_id}/{artifact.run_id}/family/{artifact.application_family}",
        ]
        refs.extend(f"deepmd://file/{Path(path).name}" for path in evidence_files)
        return list(dict.fromkeys(refs))

    def build_evidence_bundle(
        self,
        artifact: DeepMDRunArtifact,
        validation: DeepMDValidationReport | None = None,
    ) -> DeepMDEvidenceBundle:
        return build_evidence_bundle(artifact, validation)
