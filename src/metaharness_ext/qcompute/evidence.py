from __future__ import annotations

import hashlib
import uuid

from metaharness.core.execution_modes import ExecutionMode, InstantiationRecord
from metaharness_ext.qcompute.contracts import (
    QComputeBackendSpec,
    QComputeEnvironmentReport,
    QComputeEvidenceBundle,
    QComputeEvidenceWarning,
    QComputeRunArtifact,
    QComputeValidationReport,
)


def qcompute_core_execution_mode(
    native_execution_mode: object | None,
    backend: QComputeBackendSpec,
    run: QComputeRunArtifact | None = None,
    external_evidence_refs: list[str] | None = None,
) -> ExecutionMode:
    native_mode = str(native_execution_mode or "").strip().lower()
    external_refs = list(external_evidence_refs or [])
    if native_mode == "simulate" or backend.simulator:
        return ExecutionMode.SIMULATION
    if native_mode == "hybrid":
        return ExecutionMode.STAGED
    if native_mode == "run" and run is not None and run.status == "completed":
        if external_refs:
            return ExecutionMode.EXTERNAL_VERIFIED
        return ExecutionMode.INSTANTIATED
    return ExecutionMode.UNKNOWN


def qcompute_external_evidence_refs(
    run: QComputeRunArtifact,
    validation: QComputeValidationReport,
    environment: QComputeEnvironmentReport,
) -> list[str]:
    if environment.backend.simulator or run.status != "completed":
        return []
    refs = [*run.external_evidence_refs]
    if run.raw_output_path is not None:
        receipt_payload = {
            "backend": run.backend_actual,
            "artifact_id": run.artifact_id,
            "plan_ref": run.plan_ref,
            "shots_requested": run.shots_requested,
            "shots_completed": run.shots_completed,
            "raw_output_path": run.raw_output_path,
            "validation_status": validation.status.value,
        }
        receipt_hash = hashlib.sha256(
            repr(sorted(receipt_payload.items())).encode("utf-8")
        ).hexdigest()[:16]
        refs.append(f"qcompute://provider-receipt/{run.backend_actual}/{receipt_hash}")
    return list(dict.fromkeys(refs))


def build_instantiation_record(
    bundle: QComputeEvidenceBundle,
    *,
    candidate_id: str | None = None,
    graph_version: int | None = None,
) -> InstantiationRecord:
    run = bundle.run_artifact
    validation = bundle.validation_report
    external_refs = list(bundle.external_evidence_refs)
    native_mode = run.native_execution_mode or bundle.metadata.get("native_execution_mode")
    execution_mode = qcompute_core_execution_mode(
        native_mode,
        bundle.environment_report.backend,
        run,
        external_refs,
    )
    return InstantiationRecord(
        execution_mode=execution_mode,
        native_execution_mode=str(native_mode) if native_mode is not None else None,
        claim_ref=f"qcompute://experiment/{bundle.experiment_ref}",
        action_ref=run.artifact_id,
        run_artifact_ref=run.artifact_id,
        validation_ref=validation.task_id,
        evidence_refs=list(dict.fromkeys([*bundle.provenance_refs, *validation.evidence_refs])),
        external_evidence_refs=external_refs,
        candidate_id=candidate_id,
        graph_version=graph_version,
        attributes={
            "extension_family": "qcompute",
            "backend": run.backend_actual,
            "backend_simulator": bundle.environment_report.backend.simulator,
            "artifact_status": run.status,
        },
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

    external_evidence_refs = qcompute_external_evidence_refs(run, validation, environment)
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
                *external_evidence_refs,
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
        external_evidence_refs=external_evidence_refs,
        metadata={
            "backend": run.backend_actual,
            "artifact_status": run.status,
            "validation_status": validation.status.value,
            "promotion_ready": validation.promotion_ready,
            "environment_status": environment.status,
            "native_execution_mode": run.native_execution_mode,
            "core_execution_mode": qcompute_core_execution_mode(
                run.native_execution_mode,
                environment.backend,
                run,
                external_evidence_refs,
            ).value,
            "candidate_id": run.candidate_identity.candidate_id,
            "graph_version_id": run.candidate_identity.graph_version_id,
            "proposed_graph_version": run.candidate_identity.proposed_graph_version,
        },
    )
