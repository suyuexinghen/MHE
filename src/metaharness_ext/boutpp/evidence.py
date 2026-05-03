from __future__ import annotations

import uuid

from metaharness_ext.boutpp.contracts import (
    BoutPPEnvironmentReport,
    BoutPPEvidenceBundle,
    BoutPPEvidenceWarning,
    BoutPPPostprocessReport,
    BoutPPRunArtifact,
    BoutPPRunPlan,
    BoutPPValidationReport,
)


def build_evidence_bundle(
    task_id: str,
    environment: BoutPPEnvironmentReport | None = None,
    plan: BoutPPRunPlan | None = None,
    artifact: BoutPPRunArtifact | None = None,
    postprocess: BoutPPPostprocessReport | None = None,
    validation: BoutPPValidationReport | None = None,
    evidence_files: list[str] | None = None,
    provenance: dict | None = None,
    metadata: dict | None = None,
) -> BoutPPEvidenceBundle:
    bundle_id = f"boutpp-evidence-{uuid.uuid4().hex[:12]}"
    warnings: list[BoutPPEvidenceWarning] = []
    refs: list[str] = []
    if environment is not None:
        refs.append(f"boutpp://environment/{environment.task_id}")
    if plan is not None:
        refs.append(f"boutpp://plan/{plan.plan_id}")
    if artifact is not None:
        refs.append(f"boutpp://artifact/{artifact.artifact_id}")
    if postprocess is not None:
        refs.append(f"boutpp://postprocess/{postprocess.report_id}")
    if validation is not None:
        refs.append(f"boutpp://validation/{validation.artifact_ref}")
    refs = list(dict.fromkeys(refs))
    if environment is None or not environment.available:
        warnings.append(
            BoutPPEvidenceWarning(
                code="boutpp_environment_not_ready",
                message="BOUT++ environment is not available.",
            )
        )
    if validation is None:
        warnings.append(
            BoutPPEvidenceWarning(
                code="boutpp_validation_missing",
                message="Validation report is missing.",
            )
        )
    return BoutPPEvidenceBundle(
        bundle_id=bundle_id,
        task_id=task_id,
        run_id=validation.run_id if validation is not None else None,
        plan_ref=plan.plan_id if plan is not None else None,
        artifact_ref=artifact.artifact_id if artifact is not None else None,
        postprocess_ref=postprocess.report_id if postprocess is not None else None,
        validation_ref=validation.artifact_ref if validation is not None else None,
        environment=environment,
        plan=plan,
        artifact=artifact,
        postprocess=postprocess,
        validation=validation,
        evidence_files=evidence_files or [],
        evidence_refs=refs,
        warnings=warnings,
        provenance=provenance or {},
        metadata=metadata or {},
    )
