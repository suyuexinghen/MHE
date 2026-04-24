from __future__ import annotations

from metaharness_ext.deepmd.contracts import (
    DeepMDEnvironmentReport,
    DeepMDEvidenceBundle,
    DeepMDEvidenceWarning,
    DeepMDRunArtifact,
    DeepMDValidationReport,
)


def build_evidence_bundle(
    run: DeepMDRunArtifact,
    validation: DeepMDValidationReport | None = None,
    environment: DeepMDEnvironmentReport | None = None,
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
    scored_evidence = validation.scored_evidence if validation is not None else None
    provenance_refs = list(
        dict.fromkeys(
            [
                *(
                    [f"deepmd://validation/{run.task_id}/{run.run_id}"]
                    if validation is not None
                    else []
                ),
                *(validation.evidence_refs if validation is not None else []),
                *([] if scored_evidence is None else scored_evidence.evidence_refs),
                *(environment.evidence_refs if environment is not None else []),
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
    if environment is not None:
        for prerequisite in environment.missing_prerequisites:
            warnings.append(
                DeepMDEvidenceWarning(
                    code="environment_prerequisite_missing",
                    message=f"Environment prerequisite missing: {prerequisite}.",
                    evidence={"run_id": run.run_id, "prerequisite": prerequisite},
                )
            )
        for path in environment.missing_required_paths:
            warnings.append(
                DeepMDEvidenceWarning(
                    code="environment_required_path_missing",
                    message=f"Environment required path missing: {path}.",
                    evidence={"run_id": run.run_id, "path": path},
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
        provenance_refs=provenance_refs,
        scored_evidence=scored_evidence,
        provenance={
            "task_id": run.task_id,
            "run_id": run.run_id,
            "application_family": run.application_family,
            "execution_mode": run.execution_mode,
            "validation_status": validation.status if validation is not None else None,
        },
        metadata={
            "status": run.status,
            "return_code": run.return_code,
            "validation_status": validation.status if validation is not None else None,
            "environment": {
                "fallback_reason": environment.fallback_reason if environment is not None else None,
                "missing_prerequisites": (
                    list(environment.missing_prerequisites) if environment is not None else []
                ),
                "missing_required_paths": (
                    list(environment.missing_required_paths) if environment is not None else []
                ),
                "machine_spec_valid": (
                    environment.machine_spec_valid if environment is not None else None
                ),
                "remote_root_configured": (
                    environment.remote_root_configured if environment is not None else None
                ),
                "scheduler_command_configured": (
                    environment.scheduler_command_configured if environment is not None else None
                ),
                "messages": list(environment.messages) if environment is not None else [],
            },
        },
    )
