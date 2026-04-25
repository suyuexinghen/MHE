from __future__ import annotations

import uuid

from metaharness_ext.qcompute.contracts import (
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeEvidenceWarning,
    QComputeRunArtifact,
    QComputeValidationReport,
)


def build_evidence_bundle(
    run: QComputeRunArtifact,
    validation: QComputeValidationReport,
    environment: QComputeEnvironmentReport,
) -> QComputeEvidenceBundle:
    warnings: list[QComputeEvidenceWarning] = []
    if run.raw_output_path is None:
        warnings.append(
            QComputeEvidenceWarning(
                code="raw_output_missing",
                message="Run artifact does not include a raw output path.",
                evidence={"artifact_id": run.artifact_id},
            )
        )
    if environment.prerequisite_errors:
        warnings.append(
            QComputeEvidenceWarning(
                code="environment_prerequisites_present",
                message="Environment report includes prerequisite findings.",
                evidence={
                    "task_id": environment.task_id,
                    "status": environment.status,
                    "prerequisite_errors": list(environment.prerequisite_errors),
                },
            )
        )
    if not validation.promotion_ready:
        warnings.append(
            QComputeEvidenceWarning(
                code="promotion_not_ready",
                message="Validation report is not ready for promotion.",
                evidence={"task_id": validation.task_id, "status": validation.status.value},
            )
        )

    provenance_refs = list(
        dict.fromkeys(
            [
                *run.provenance_refs,
                *validation.provenance_refs,
                *validation.evidence_refs,
                *(
                    []
                    if validation.scored_evidence is None
                    else validation.scored_evidence.evidence_refs
                ),
                f"qcompute://environment/{environment.task_id}/{environment.status}",
            ]
        )
    )
    return QComputeEvidenceBundle(
        bundle_id=f"{run.artifact_id}-bundle-{uuid.uuid4().hex[:8]}",
        experiment_ref=environment.task_id,
        environment_report=environment,
        run_artifact=run,
        validation_report=validation,
        provenance_inputs=provenance_refs,
        warnings=warnings,
        scored_evidence=validation.scored_evidence or run.scored_evidence,
        provenance_refs=provenance_refs,
        metadata={
            "backend": run.backend_actual,
            "artifact_status": run.status,
            "validation_status": validation.status.value,
            "promotion_ready": validation.promotion_ready,
            "environment_status": environment.status,
            "candidate_id": run.candidate_identity.candidate_id,
            "graph_version_id": run.candidate_identity.graph_version_id,
            "proposed_graph_version": run.candidate_identity.proposed_graph_version,
        },
    )
