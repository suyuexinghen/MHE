from __future__ import annotations

from uuid import uuid4

from metaharness_ext.moose.contracts import (
    MooseEnvironmentReport,
    MooseEvidenceBundle,
    MooseRunArtifact,
    MooseRunPlan,
    MooseValidationReport,
)


def build_evidence_bundle(
    *,
    task_id: str,
    environment: MooseEnvironmentReport | None = None,
    plan: MooseRunPlan | None = None,
    artifact: MooseRunArtifact | None = None,
    validation: MooseValidationReport | None = None,
) -> MooseEvidenceBundle:
    return MooseEvidenceBundle(
        bundle_id=f"moose-bundle-{uuid4().hex[:12]}",
        task_id=task_id,
        run_id=artifact.run_id
        if artifact is not None
        else (validation.run_id if validation else None),
        plan_ref=plan.plan_id if plan is not None else None,
        artifact_ref=artifact.artifact_id if artifact is not None else None,
        validation_ref=validation.artifact_ref if validation is not None else None,
        environment=environment,
        plan=plan,
        artifact=artifact,
        validation=validation,
        evidence_files=[
            *(artifact.output_files if artifact is not None else []),
            *(artifact.log_files if artifact is not None else []),
        ],
        evidence_refs=[
            *(environment.evidence_refs if environment is not None else []),
            *(plan.evidence_refs if plan is not None else []),
            *(artifact.evidence_refs if artifact is not None else []),
            *(validation.evidence_refs if validation is not None else []),
        ],
        metadata={},
    )
