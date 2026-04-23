from __future__ import annotations

from collections.abc import Iterable

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_VALIDATE
from metaharness_ext.deepmd.contracts import DeepMDRunArtifact, DeepMDValidationReport
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
        metrics: dict[str, float | str] = {}
        fallback_reason = artifact.result_summary.get("fallback_reason")
        evidence_files = [
            *artifact.workspace_files,
            *artifact.checkpoint_files,
            *artifact.model_files,
            *artifact.diagnostic_files,
        ]

        if artifact.status == "unavailable" and fallback_reason:
            messages.append(f"DeepMD run unavailable: {fallback_reason}.")
            return DeepMDValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="environment_invalid",
                messages=messages,
                summary_metrics=metrics,
                evidence_files=evidence_files,
            )

        if fallback_reason == "workspace_prepare_failed":
            messages.append("Workspace preparation failed.")
            return DeepMDValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status="workspace_failed",
                messages=messages,
                summary_metrics=metrics,
                evidence_files=evidence_files,
            )

        if artifact.return_code not in {0, None} or artifact.status == "failed":
            if artifact.return_code is not None:
                messages.append(f"DeepMD command exited with code {artifact.return_code}.")
            elif fallback_reason:
                messages.append(f"DeepMD command failed: {fallback_reason}.")
            else:
                messages.append("DeepMD command failed.")
            status = "run_failed" if artifact.execution_mode == "dpgen_run" else "runtime_failed"
            return DeepMDValidationReport(
                task_id=artifact.task_id,
                run_id=artifact.run_id,
                passed=False,
                status=status,
                messages=messages,
                summary_metrics=metrics,
                evidence_files=evidence_files,
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
        elif artifact.execution_mode == "dpgen_run":
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
            status = "baseline_success" if passed else "validation_failed"
            if passed and collection is not None:
                messages.append("DP-GEN baseline completed with iteration evidence.")
                metrics.update(
                    {
                        "candidate_count": float(collection.candidate_count),
                        "accurate_count": float(collection.accurate_count),
                        "failed_count": float(collection.failed_count),
                    }
                )

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

        return DeepMDValidationReport(
            task_id=artifact.task_id,
            run_id=artifact.run_id,
            passed=passed,
            status=status,
            messages=messages,
            summary_metrics=metrics,
            evidence_files=evidence_files,
        )
