from metaharness.core.models import SessionEventType
from metaharness.observability.events import InMemorySessionStore, make_session_event
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness_ext.jedi.contracts import (
    JediEvidenceBundle,
    JediPolicyReport,
    JediRunArtifact,
    JediValidationReport,
)
from metaharness_ext.jedi.governance import JediGovernanceAdapter


def _bundle(*, decision: str = "allow", graph_version_id: int | None = 3) -> tuple[JediEvidenceBundle, JediPolicyReport]:
    run = JediRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="real_run",
        command=["/usr/bin/qg4DVar.x", "config.yaml"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        output_files=["/tmp/analysis.out"],
        diagnostic_files=["/tmp/departures.json"],
        reference_files=["provenance://jedi/reference/task-1"],
        working_directory="/tmp/run-1",
        status="completed",
    )
    validation = JediValidationReport(
        task_id="task-1",
        run_id="run-1",
        passed=decision == "allow",
        status="executed" if decision == "allow" else "validation_failed",
        candidate_id="candidate-1",
        graph_version_id=graph_version_id,
        session_id="jedi-session",
        session_events=[
            make_session_event(
                "jedi-session",
                SessionEventType.CANDIDATE_VALIDATED,
                graph_version=graph_version_id,
                candidate_id="candidate-1",
                payload={"source": "validator"},
            )
        ],
        blocking_reasons=[] if decision == "allow" else ["missing diagnostics"],
        provenance_refs=["provenance://jedi/validation/task-1"],
    )
    bundle = JediEvidenceBundle(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="real_run",
        run=run,
        validation=validation,
        candidate_id="candidate-1",
        graph_version_id=graph_version_id,
        session_id="jedi-session",
    )
    policy = JediPolicyReport(
        passed=decision == "allow",
        decision=decision,
        reason="ready" if decision == "allow" else "defer for review",
    )
    return bundle, policy


def test_jedi_governance_adapter_builds_candidate_record() -> None:
    bundle, policy = _bundle()

    record = JediGovernanceAdapter().build_candidate_record(bundle, policy)

    assert record.candidate_id == "candidate-1"
    assert record.promoted is True
    assert record.snapshot.graph_version == 3
    assert record.report.valid is True
    assert record.report.issues == []


def test_jedi_governance_adapter_maps_blockers_into_core_validation_report() -> None:
    bundle, policy = _bundle(decision="defer")

    report = JediGovernanceAdapter().build_core_validation_report(bundle.validation, policy)

    assert report.valid is False
    assert report.issues[0].code == "jedi_policy_blocker"
    assert report.issues[0].blocks_promotion is True


def test_jedi_governance_adapter_emits_session_audit_and_provenance_evidence() -> None:
    bundle, policy = _bundle()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance_graph = ProvGraph()

    refs = JediGovernanceAdapter().emit_runtime_evidence(
        bundle,
        policy,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )

    events = session_store.get_events("jedi-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert len(audit_log.by_kind("session.candidate_validated")) == 1
    assert len(audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert len(audit_log.by_kind("jedi.governance_handoff")) == 1
    assert all(ref.startswith("audit-record:") for ref in refs["audit_refs"])
    assert "provenance://jedi/validation/task-1" in refs["provenance_refs"]

    provenance = provenance_graph.to_dict()
    assert "graph-candidate:candidate-1" in provenance["entities"]
    assert "graph-version:3" in provenance["entities"]
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == "graph-candidate:candidate-1"
        for relation in provenance["relations"]
    )
