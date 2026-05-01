from __future__ import annotations

import uuid

from metaharness_ext.pycfd.contracts import (
    PyCFDEnvironmentReport,
    PyCFDEvidenceBundle,
    PyCFDEvidenceWarning,
    PyCFDRunArtifact,
    PyCFDRunPlan,
    PyCFDValidationReport,
)


def build_evidence_bundle(
    task_id: str,
    environment: PyCFDEnvironmentReport | None = None,
    plan: PyCFDRunPlan | None = None,
    artifact: PyCFDRunArtifact | None = None,
    validation: PyCFDValidationReport | None = None,
    evidence_files: list[str] | None = None,
    provenance: dict | None = None,
    metadata: dict | None = None,
) -> PyCFDEvidenceBundle:
    bundle_id = f"pycfd-evidence-{uuid.uuid4().hex[:12]}"
    warnings: list[PyCFDEvidenceWarning] = []

    plan_ref = plan.plan_id if plan else None
    artifact_ref = artifact.artifact_id if artifact else None
    validation_ref = None
    run_id = None

    if validation:
        validation_ref = f"pycfd://validations/{validation.artifact_ref}"
        run_id = validation.run_id

    # Gather evidence refs
    refs: list[str] = []
    if environment:
        refs.append(f"pycfd://environments/{environment.task_id}")
    if plan:
        refs.append(f"pycfd://plans/{plan.plan_id}")
    if artifact:
        refs.append(f"pycfd://artifacts/{artifact.artifact_id}")
    if validation:
        refs.append(validation_ref or "")

    # Deduplicate
    refs = list(dict.fromkeys(r for r in refs if r))

    # Generate warnings for missing stages
    if validation is None:
        warnings.append(
            PyCFDEvidenceWarning(
                code="pycfd_validation_missing",
                message="Validation report is missing — evidence is incomplete.",
                severity="warning",
            )
        )
    if environment is None or not environment.available:
        warnings.append(
            PyCFDEvidenceWarning(
                code="pycfd_environment_not_ready",
                message="PyCFD environment is not available.",
                severity="warning",
            )
        )

    return PyCFDEvidenceBundle(
        bundle_id=bundle_id,
        task_id=task_id,
        run_id=run_id,
        plan_ref=plan_ref,
        artifact_ref=artifact_ref,
        validation_ref=validation_ref,
        environment=environment,
        plan=plan,
        artifact=artifact,
        validation=validation,
        evidence_files=evidence_files or [],
        evidence_refs=refs,
        warnings=warnings,
        provenance=provenance or {},
        metadata=metadata or {},
    )
