from __future__ import annotations

from metaharness_ext.deepmd.contracts import (
    DeepMDEvidenceBundle,
    DeepMDEvidenceWarning,
    DeepMDRunArtifact,
    DeepMDValidationReport,
)


def build_evidence_bundle(
    run: DeepMDRunArtifact,
    validation: DeepMDValidationReport | None = None,
) -> DeepMDEvidenceBundle:
    evidence_files = list(
        dict.fromkeys(
            [
                *(validation.evidence_files if validation is not None else []),
                *run.workspace_files,
                *run.checkpoint_files,
                *run.model_files,
                *run.diagnostic_files,
            ]
        )
    )
    warnings: list[DeepMDEvidenceWarning] = []
    if not run.stdout_path:
        warnings.append(
            DeepMDEvidenceWarning(
                code="stdout_missing",
                message="Run artifact does not include a stdout log path.",
                evidence={"run_id": run.run_id},
            )
        )
    if not run.stderr_path:
        warnings.append(
            DeepMDEvidenceWarning(
                code="stderr_missing",
                message="Run artifact does not include a stderr log path.",
                evidence={"run_id": run.run_id},
            )
        )
    if (
        run.execution_mode in {"dpgen_run", "dpgen_simplify"}
        and run.summary.dpgen_collection is None
    ):
        warnings.append(
            DeepMDEvidenceWarning(
                code="dpgen_iteration_evidence_missing",
                message="DP-GEN run is missing iteration evidence collection.",
                evidence={"run_id": run.run_id, "execution_mode": run.execution_mode},
            )
        )
    if run.execution_mode == "dpgen_autotest" and not run.summary.autotest_properties:
        warnings.append(
            DeepMDEvidenceWarning(
                code="autotest_properties_missing",
                message="Autotest run did not produce structured property results.",
                evidence={"run_id": run.run_id},
            )
        )

    return DeepMDEvidenceBundle(
        task_id=run.task_id,
        run_id=run.run_id,
        application_family=run.application_family,
        execution_mode=run.execution_mode,
        run=run,
        validation=validation,
        summary=run.summary,
        evidence_files=evidence_files,
        warnings=warnings,
        metadata={
            "status": run.status,
            "return_code": run.return_code,
            "validation_status": validation.status if validation is not None else None,
        },
    )
