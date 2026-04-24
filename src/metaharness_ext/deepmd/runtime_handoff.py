from __future__ import annotations

from metaharness.core.boot import HarnessRuntime
from metaharness.core.graph_versions import CandidateRecord
from metaharness_ext.deepmd.contracts import DeepMDEvidenceBundle, DeepMDPolicyReport
from metaharness_ext.deepmd.governance import DeepMDGovernanceAdapter


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
    bundle: DeepMDEvidenceBundle,
    policy: DeepMDPolicyReport,
) -> CandidateRecord:
    if runtime is None:
        return candidate_record
    DeepMDGovernanceAdapter(session_id=runtime.session_id).emit_runtime_evidence(
        bundle,
        policy,
        session_store=runtime.session_store,
        audit_log=runtime.audit_log,
        provenance_graph=runtime.provenance_graph,
    )
    return runtime.ingest_candidate_record(candidate_record, emit_runtime_evidence=False)
