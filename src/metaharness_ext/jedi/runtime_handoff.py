from __future__ import annotations

from metaharness.core.boot import HarnessRuntime
from metaharness.core.execution import ExecutionEvidenceRecorder
from metaharness.core.graph_versions import CandidateRecord
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.contracts import JediEvidenceBundle, JediPolicyReport
from metaharness_ext.jedi.governance import JediGovernanceAdapter


def handoff_candidate_record(
    runtime: HarnessRuntime | None, candidate_record: CandidateRecord
) -> CandidateRecord:
    if runtime is None:
        return candidate_record
    return runtime.ingest_candidate_record(candidate_record)


def handoff_governed_candidate(
    runtime: HarnessRuntime | None,
    candidate_record: CandidateRecord,
    *,
    bundle: JediEvidenceBundle,
    policy: JediPolicyReport,
    component_runtime: ComponentRuntime | None = None,
) -> CandidateRecord:
    if runtime is None:
        return candidate_record

    resolved_runtime = component_runtime
    if resolved_runtime is None:
        runtime_component = runtime.components.get("runtime.primary")
        resolved_runtime = getattr(runtime_component, "_runtime", None)
    if resolved_runtime is None or resolved_runtime.resolved_artifact_store() is None:
        resolved_runtime = next(
            (
                candidate_runtime
                for candidate_runtime in (
                    getattr(component, "_runtime", None)
                    for component in runtime.components.values()
                )
                if candidate_runtime is not None
                and candidate_runtime.resolved_artifact_store() is not None
            ),
            None,
        )
    session_store = (
        resolved_runtime.resolved_session_store()
        if resolved_runtime is not None
        else runtime.session_store
    )
    artifact_store = (
        resolved_runtime.resolved_artifact_store()
        if resolved_runtime is not None
        else runtime.artifact_store
    )
    audit_log = (
        resolved_runtime.resolved_audit_log() if resolved_runtime is not None else runtime.audit_log
    )
    provenance_graph = (
        resolved_runtime.resolved_provenance_graph()
        if resolved_runtime is not None
        else runtime.provenance_graph
    )

    adapter = JediGovernanceAdapter(session_id=runtime.session_id)
    refs = adapter.emit_runtime_evidence(
        bundle,
        policy,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )
    ExecutionEvidenceRecorder(
        session_store=session_store,
        artifact_store=artifact_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
        actor="jedi_runtime_handoff",
    ).record(
        session_id=runtime.session_id,
        run_artifact=bundle.run,
        validation_outcome=adapter._require_validation(bundle),
        evidence_bundle=bundle,
        candidate_id=candidate_record.candidate_id,
        graph_version=candidate_record.snapshot.graph_version,
        policy_decision=policy.decision,
        safety_payload={
            "reason": policy.reason,
            "gate_count": len(policy.gates),
            **adapter._diagnostics_payload(bundle),
        },
    )
    validation = adapter._require_validation(bundle)
    validation.provenance_refs = list(
        dict.fromkeys([*validation.provenance_refs, *refs["provenance_refs"]])
    )
    bundle.audit_refs = list(dict.fromkeys([*bundle.audit_refs, *refs["audit_refs"]]))
    bundle.metadata = {
        **bundle.metadata,
        "runtime_provenance_refs": list(
            dict.fromkeys(
                [*bundle.metadata.get("runtime_provenance_refs", []), *refs["provenance_refs"]]
            )
        ),
    }
    return runtime.ingest_candidate_record(candidate_record, emit_runtime_evidence=False)
