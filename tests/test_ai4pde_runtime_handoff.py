from metaharness.core.boot import HarnessRuntime, bundled_discovery
from metaharness.core.models import GraphSnapshot, SessionEventType
from metaharness.provenance import RelationKind
from metaharness_ext.ai4pde.components.evidence_manager import EvidenceManagerComponent
from metaharness_ext.ai4pde.components.physics_validator import PhysicsValidatorComponent
from metaharness_ext.ai4pde.components.reference_solver import ReferenceSolverComponent
from metaharness_ext.ai4pde.contracts import PDEPlan
from metaharness_ext.ai4pde.executors import run_pinn_strong
from metaharness_ext.ai4pde.runtime_handoff import AI4PDEGovernanceAdapter
from metaharness_ext.ai4pde.types import SolverFamily


def _bundle():
    plan = PDEPlan(
        plan_id="plan-1",
        task_id="task-1",
        selected_method=SolverFamily.PINN_STRONG,
    )
    artifact = run_pinn_strong(plan)
    reference = ReferenceSolverComponent().run_reference(plan)
    validation = PhysicsValidatorComponent().validate_run(
        artifact,
        graph_version_id=3,
        reference_result=reference,
    )
    bundle = EvidenceManagerComponent().assemble_evidence(
        artifact,
        validation,
        reference_result=reference,
        graph_family="ai4pde-test",
    )
    return artifact, validation, bundle


def test_ai4pde_governance_adapter_emits_session_audit_and_provenance_evidence(examples_dir):
    artifact, validation, bundle = _bundle()
    runtime = HarnessRuntime(
        bundled_discovery(examples_dir / "manifests" / "ai4pde"),
        session_id="ai4pde-session",
    )

    refs = AI4PDEGovernanceAdapter(session_id="ai4pde-session").emit_runtime_evidence(
        bundle,
        validation=validation,
        session_store=runtime.session_store,
        audit_log=runtime.audit_log,
        provenance_graph=runtime.provenance_graph,
    )

    events = runtime.session_store.get_events("ai4pde-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert events[1].payload == {
        "decision": "accept",
        "violations": [],
        "solver_family": "pinn_strong",
        "graph_family": "ai4pde-test",
    }
    assert len(runtime.audit_log.by_kind("session.candidate_validated")) == 1
    assert len(runtime.audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert len(runtime.audit_log.by_kind("ai4pde.governance_handoff")) == 1
    assert all(ref.startswith("audit-record:") for ref in refs["audit_refs"])
    assert "provenance://ai4pde/validation/task-1" in refs["provenance_refs"]

    provenance = runtime.provenance_graph.to_dict()
    assert f"graph-candidate:{artifact.run_id}" in provenance["entities"]
    assert "graph-version:3" in provenance["entities"]
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == f"graph-candidate:{artifact.run_id}"
        for relation in provenance["relations"]
    )


def test_ai4pde_governance_adapter_handoff_ingests_candidate_without_double_emission(examples_dir):
    artifact, validation, bundle = _bundle()
    runtime = HarnessRuntime(
        bundled_discovery(examples_dir / "manifests" / "ai4pde"),
        session_id="ai4pde-session",
    )

    record = AI4PDEGovernanceAdapter(session_id="ai4pde-session").handoff_candidate_record(
        runtime,
        bundle,
        validation=validation,
        snapshot=GraphSnapshot(graph_version=3),
    )

    assert record.candidate_id == artifact.run_id
    assert len(runtime.version_manager.candidates) == 1
    assert len(runtime.audit_log.by_kind("ai4pde.governance_handoff")) == 1
    assert len(runtime.audit_log.by_kind("session.candidate_validated")) == 1
    assert len(runtime.audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert not runtime.audit_log.by_kind("session.candidate_created")
