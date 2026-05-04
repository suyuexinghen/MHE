from __future__ import annotations

from uuid import uuid4

from metaharness.core.execution_modes import ExecutionMode, InstantiationRecord
from metaharness_ext.moose.contracts import (
    MooseEnvironmentReport,
    MooseEvidenceBundle,
    MooseRunArtifact,
    MooseRunPlan,
    MooseValidationReport,
)


def build_instantiation_record(
    *,
    plan: MooseRunPlan | None = None,
    artifact: MooseRunArtifact | None = None,
    validation: MooseValidationReport | None = None,
) -> InstantiationRecord | None:
    if plan is None and artifact is None:
        return None

    graph_version = None
    candidate_id = None
    if plan is not None:
        candidate_id = plan.graph_metadata.get("candidate_id")
        raw_graph_version = plan.graph_metadata.get("graph_version")
        if isinstance(raw_graph_version, int):
            graph_version = raw_graph_version

    if artifact is None:
        return InstantiationRecord(
            execution_mode=ExecutionMode.DRY_RUN,
            native_execution_mode="input_deck_generation",
            claim_ref=plan.plan_id if plan is not None else None,
            action_ref=plan.plan_id if plan is not None else None,
            evidence_refs=list(plan.evidence_refs) if plan is not None else [],
            candidate_id=candidate_id,
            graph_version=graph_version,
            attributes={"extension": "moose"},
        )

    execution_mode = ExecutionMode.UNKNOWN
    native_execution_mode = "execution_unavailable"
    if artifact.status in {"completed", "failed", "timeout"}:
        execution_mode = ExecutionMode.INSTANTIATED
        native_execution_mode = "executable_run"

    return InstantiationRecord(
        execution_mode=execution_mode,
        native_execution_mode=native_execution_mode,
        claim_ref=artifact.plan_ref,
        action_ref=" ".join(artifact.command) if artifact.command else None,
        run_artifact_ref=artifact.artifact_id,
        validation_ref=validation.artifact_ref if validation is not None else None,
        evidence_refs=list(artifact.evidence_refs),
        external_evidence_refs=[],
        candidate_id=candidate_id,
        graph_version=graph_version,
        attributes={"extension": "moose", "status": artifact.status},
    )


def build_evidence_bundle(
    *,
    task_id: str,
    environment: MooseEnvironmentReport | None = None,
    plan: MooseRunPlan | None = None,
    artifact: MooseRunArtifact | None = None,
    validation: MooseValidationReport | None = None,
) -> MooseEvidenceBundle:
    instantiation_record = build_instantiation_record(
        plan=plan,
        artifact=artifact,
        validation=validation,
    )
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
        instantiation_records=[instantiation_record] if instantiation_record is not None else [],
        metadata={},
    )
