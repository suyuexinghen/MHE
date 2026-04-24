from metaharness.core.models import SessionEventType
from metaharness.observability.events import InMemorySessionStore, make_session_event
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness_ext.jedi.contracts import (
    JediDiagnosticSummary,
    JediEvidenceBundle,
    JediPolicyReport,
    JediRunArtifact,
    JediValidationReport,
)
from metaharness_ext.jedi.governance import JediGovernanceAdapter


def _bundle(
    *,
    decision: str = "allow",
    graph_version_id: int | None = 3,
    summary: JediDiagnosticSummary | None = None,
) -> tuple[JediEvidenceBundle, JediPolicyReport]:
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
        summary=summary,
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
    bundle, policy = _bundle(
        summary=JediDiagnosticSummary(
            files_scanned=["/tmp/departures.json", "/tmp/stdout.log"],
            ioda_groups_found=["MetaData", "ObsValue", "HofX"],
            ioda_groups_missing=["ObsError"],
            minimizer_iterations=4,
            outer_iterations=2,
            inner_iterations=5,
            initial_cost_function=12.5,
            final_cost_function=3.125,
            initial_gradient_norm=8.0,
            final_gradient_norm=0.5,
            gradient_norm_reduction=0.0625,
            observer_output_detected=True,
            posterior_output_detected=False,
        )
    )
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
    safety_gate_event = next(
        event for event in events if event.event_type == SessionEventType.SAFETY_GATE_EVALUATED
    )
    assert safety_gate_event.payload["diagnostic_files_scanned"] == 2
    assert safety_gate_event.payload["ioda_groups_found"] == ["MetaData", "ObsValue", "HofX"]
    assert safety_gate_event.payload["ioda_groups_missing"] == ["ObsError"]
    assert safety_gate_event.payload["minimizer_iterations"] == 4
    assert safety_gate_event.payload["outer_iterations"] == 2
    assert safety_gate_event.payload["inner_iterations"] == 5
    assert safety_gate_event.payload["initial_cost_function"] == 12.5
    assert safety_gate_event.payload["final_cost_function"] == 3.125
    assert safety_gate_event.payload["initial_gradient_norm"] == 8.0
    assert safety_gate_event.payload["final_gradient_norm"] == 0.5
    assert safety_gate_event.payload["gradient_norm_reduction"] == 0.0625
    assert safety_gate_event.payload["observer_output_detected"] is True
    assert safety_gate_event.payload["posterior_output_detected"] is False

    assert len(audit_log.by_kind("session.candidate_validated")) == 1
    assert len(audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert len(audit_log.by_kind("jedi.governance_handoff")) == 1
    handoff_record = audit_log.by_kind("jedi.governance_handoff")[0]
    assert handoff_record.payload["diagnostic_files_scanned"] == 2
    assert handoff_record.payload["ioda_groups_found"] == ["MetaData", "ObsValue", "HofX"]
    assert handoff_record.payload["ioda_groups_missing"] == ["ObsError"]
    assert handoff_record.payload["minimizer_iterations"] == 4
    assert handoff_record.payload["outer_iterations"] == 2
    assert handoff_record.payload["inner_iterations"] == 5
    assert handoff_record.payload["initial_cost_function"] == 12.5
    assert handoff_record.payload["final_cost_function"] == 3.125
    assert handoff_record.payload["initial_gradient_norm"] == 8.0
    assert handoff_record.payload["final_gradient_norm"] == 0.5
    assert handoff_record.payload["gradient_norm_reduction"] == 0.0625
    assert handoff_record.payload["observer_output_detected"] is True
    assert handoff_record.payload["posterior_output_detected"] is False
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


def test_jedi_governance_adapter_emits_decision_only_payload_without_summary() -> None:
    bundle, policy = _bundle(summary=None)
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
    safety_gate_event = next(
        event for event in events if event.event_type == SessionEventType.SAFETY_GATE_EVALUATED
    )
    assert safety_gate_event.payload == {
        "decision": "allow",
        "reason": "ready",
        "gate_count": 0,
    }

    handoff_record = audit_log.by_kind("jedi.governance_handoff")[0]
    assert handoff_record.payload == {
        "task_id": "task-1",
        "run_id": "run-1",
        "candidate_id": "candidate-1",
        "graph_version": 3,
        "policy_decision": "allow",
    }
    assert all(ref.startswith("audit-record:") for ref in refs["audit_refs"])
    assert "provenance://jedi/validation/task-1" in refs["provenance_refs"]
