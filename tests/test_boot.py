"""Full discovery -> boot orchestration tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime
from metaharness.core.brain import BrainProvider
from metaharness.core.event_bus import (
    AFTER_COMMIT_GRAPH,
    BEFORE_COMMIT_GRAPH,
    CANDIDATE_DEFERRED,
    CANDIDATE_REJECTED,
)
from metaharness.core.graph_versions import CandidateRecord, ExternalCandidateReviewState
from metaharness.core.models import (
    GraphSnapshot,
    PendingConnectionSet,
    SessionEventType,
    ValidationIssue,
    ValidationReport,
)
from metaharness.hotreload import HotSwapOrchestrator
from metaharness.identity import InMemoryIdentityBoundary
from metaharness.observability.events import (
    FileSessionStore,
    InMemorySessionStore,
    make_session_event,
)
from metaharness.provenance import RelationKind
from metaharness.safety import SandboxTier
from metaharness.sdk import ResourceQuota
from metaharness.sdk.discovery import ComponentDiscovery
from metaharness.sdk.lifecycle import ComponentPhase
from metaharness.sdk.runtime import ComponentRuntime, RuntimeServices


def test_boot_registers_discovered_components(manifest_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    report = runtime.boot()

    assert "runtime.primary" in [cid for cid in report.booted_ids]
    # All discovered manifests should be registered.
    assert len(report.booted_ids) >= 8
    assert "runtime.primary" in runtime.registry.components


def test_boot_commits_default_topology(manifest_dir: Path, graphs_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    version = runtime.commit_graph(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
        candidate_id="default",
    )
    assert version == 1
    assert runtime.version_manager.active_version == 1
    index = runtime.build_port_index()
    assert index.lookup("policy.primary.decision") is not None
    table = runtime.build_route_table()
    assert table is not None
    assert any(r.connection_id == "c1" for r in table.all_routes())


def test_boot_filters_disabled_components(manifest_dir: Path) -> None:
    runtime = HarnessRuntime(
        ComponentDiscovery(bundled=manifest_dir),
        enabled_overrides={"memory": {"enabled": False}},
    )
    report = runtime.boot()
    assert "memory.primary" not in runtime.registry.components
    assert "memory" in report.skipped_ids


def test_commit_graph_publishes_before_and_after_events(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    events: list[tuple[str, object]] = []

    runtime.event_bus.subscribe(
        BEFORE_COMMIT_GRAPH, lambda event: events.append((event.name, event.payload))
    )
    runtime.event_bus.subscribe(
        AFTER_COMMIT_GRAPH, lambda event: events.append((event.name, event.payload))
    )

    version = runtime.commit_graph(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
        candidate_id="default",
    )

    assert version == 1
    assert [name for name, _ in events] == [BEFORE_COMMIT_GRAPH, AFTER_COMMIT_GRAPH]
    before_ctx = events[0][1]
    after_ctx = events[1][1]
    assert before_ctx is after_ctx
    assert before_ctx.candidate_id == "default"
    assert before_ctx.proposed_graph_version == 1
    assert before_ctx.rollback_target is None
    assert before_ctx.validation_report.valid is True


def test_commit_graph_rejects_on_blocks_promotion_and_records_failure(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    rejected: list[object] = []
    events: list[str] = []

    runtime.event_bus.subscribe(BEFORE_COMMIT_GRAPH, lambda event: events.append(event.name))
    runtime.event_bus.subscribe(AFTER_COMMIT_GRAPH, lambda event: events.append(event.name))
    runtime.event_bus.subscribe(
        CANDIDATE_REJECTED,
        lambda event: (events.append(event.name), rejected.append(event.payload)),
    )

    original_stage = runtime.engine.stage

    def stage_with_nonblocking_invalid(pending: PendingConnectionSet):
        candidate, report = original_stage(pending)
        report.valid = False
        report.issues.append(
            ValidationIssue(
                code="nonblocking_warning",
                message="Warning that does not block promotion",
                subject="policy.primary",
                blocks_promotion=False,
            )
        )
        report.issues.append(
            ValidationIssue(
                code="explicit_gate",
                message="Issue blocks promotion explicitly",
                subject="runtime.primary",
                blocks_promotion=True,
            )
        )
        return candidate, report

    runtime.engine.stage = stage_with_nonblocking_invalid

    with pytest.raises(ValueError, match="failed promotion gate"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="blocked",
        )

    assert events == [CANDIDATE_REJECTED]
    assert len(rejected) == 1
    ctx = rejected[0]
    assert ctx.candidate_id == "blocked"
    assert ctx.proposed_graph_version == 1
    assert ctx.validation_report.valid is False
    assert any(issue.code == "explicit_gate" for issue in ctx.validation_report.issues)
    assert runtime.version_manager.active_version is None
    assert runtime.lifecycle.phase("runtime.primary") == ComponentPhase.FAILED
    assert runtime.lifecycle.phase("policy.primary") == ComponentPhase.FAILED
    candidate_record = runtime.version_manager.candidates[-1]
    assert candidate_record.candidate_id == "blocked"
    assert candidate_record.promoted is False


def test_commit_graph_allows_invalid_report_without_blocking_issues(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    events: list[str] = []

    runtime.event_bus.subscribe(BEFORE_COMMIT_GRAPH, lambda event: events.append(event.name))
    runtime.event_bus.subscribe(AFTER_COMMIT_GRAPH, lambda event: events.append(event.name))
    runtime.event_bus.subscribe(CANDIDATE_REJECTED, lambda event: events.append(event.name))

    original_stage = runtime.engine.stage

    def stage_with_nonblocking_invalid(pending: PendingConnectionSet):
        candidate, report = original_stage(pending)
        report.valid = False
        report.issues.append(
            ValidationIssue(
                code="advisory_only",
                message="Advisory issue that should not block promotion",
                subject="runtime.primary",
                blocks_promotion=False,
            )
        )
        return candidate, report

    runtime.engine.stage = stage_with_nonblocking_invalid

    version = runtime.commit_graph(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
        candidate_id="advisory",
    )

    assert version == 1
    assert runtime.version_manager.active_version == 1
    assert events == [BEFORE_COMMIT_GRAPH, AFTER_COMMIT_GRAPH]
    candidate_record = runtime.version_manager.candidates[-1]
    assert candidate_record.candidate_id == "advisory"
    assert candidate_record.promoted is True


def test_session_event_type_includes_execution_lifecycle_values() -> None:
    assert SessionEventType.CANDIDATE_DEFERRED.value == "candidate_deferred"
    assert SessionEventType.ENVIRONMENT_PROBED.value == "environment_probed"
    assert SessionEventType.TASK_SUBMITTED.value == "task_submitted"
    assert SessionEventType.TASK_COMPLETED.value == "task_completed"
    assert SessionEventType.TASK_FAILED.value == "task_failed"
    assert SessionEventType.TASK_RETRIED.value == "task_retried"


def test_wake_recovers_file_backed_session_events(tmp_path: Path) -> None:
    session_store = FileSessionStore(tmp_path / "sessions.jsonl")
    session_id = "wake-session"
    session_store.append(
        make_session_event(
            session_id,
            SessionEventType.CANDIDATE_CREATED,
            candidate_id="candidate-before-wake",
            graph_version=1,
        )
    )
    session_store.append(
        make_session_event(
            session_id,
            SessionEventType.GRAPH_COMMITTED,
            candidate_id="candidate-before-wake",
            graph_version=1,
            payload={"committed_graph_version": 1, "rollback_target": None},
        )
    )

    runtime = HarnessRuntime.wake(
        session_id,
        ComponentDiscovery(bundled=tmp_path / "manifests"),
        session_store=FileSessionStore(tmp_path / "sessions.jsonl"),
    )

    assert [event.event_type for event in runtime.recovered_session.events] == [
        SessionEventType.CANDIDATE_CREATED,
        SessionEventType.GRAPH_COMMITTED,
    ]
    assert runtime.recovered_session.latest_event is not None
    assert runtime.recovered_session.latest_event.event_type == SessionEventType.GRAPH_COMMITTED
    assert runtime.recovered_session.active_graph_version == 1
    assert runtime.recovered_session.rollback_graph_version is None
    assert runtime.recovered_session.candidate_ids == ["candidate-before-wake"]
    committed_events = runtime.session_events(event_type=SessionEventType.GRAPH_COMMITTED)
    assert committed_events[0].graph_version == 1


def test_woken_runtime_continues_appending_and_querying_events(tmp_path: Path) -> None:
    session_path = tmp_path / "sessions.jsonl"
    session_id = "wake-append-session"
    session_store = FileSessionStore(session_path)
    session_store.append(
        make_session_event(
            session_id,
            SessionEventType.CHECKPOINT_SAVED,
            payload={"snapshot_id": "checkpoint-1"},
        )
    )

    runtime = HarnessRuntime.wake(
        session_id,
        ComponentDiscovery(bundled=tmp_path / "manifests"),
        session_store=FileSessionStore(session_path),
    )
    runtime.session_store.append(
        make_session_event(
            session_id,
            SessionEventType.TASK_SUBMITTED,
            payload={"task_id": "task-after-wake"},
        )
    )

    refreshed = runtime.refresh_recovered_session()

    assert refreshed.checkpoint_index == 0
    assert [event.event_type for event in runtime.session_events()] == [
        SessionEventType.CHECKPOINT_SAVED,
        SessionEventType.TASK_SUBMITTED,
    ]
    assert runtime.session_events(after_index=0)[0].payload["task_id"] == "task-after-wake"
    assert FileSessionStore(session_path).get_events(session_id)[-1].event_type == (
        SessionEventType.TASK_SUBMITTED
    )


def test_commit_graph_records_session_events_and_graph_links(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    session_store = InMemorySessionStore()
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), session_store=session_store)
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")

    version = runtime.commit_graph(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
        candidate_id="evidence-commit",
    )

    assert version == 1
    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_CREATED,
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
        SessionEventType.GRAPH_COMMITTED,
    ]
    assert all(event.candidate_id == "evidence-commit" for event in events)
    assert all(event.graph_version == 1 for event in events)
    assert events[-1].payload["committed_graph_version"] == 1

    provenance = runtime.provenance_graph.to_dict()
    assert "graph-candidate:evidence-commit" in provenance["entities"]
    assert "graph-version:1" in provenance["entities"]
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == "graph-candidate:evidence-commit"
        for relation in provenance["relations"]
    )
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == "graph-version:1"
        for relation in provenance["relations"]
    )
    assert len(runtime.audit_log.by_kind("session.graph_committed")) == 1


def test_commit_graph_rejection_records_session_evidence_with_candidate_linkage(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    session_store = InMemorySessionStore()
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), session_store=session_store)
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")

    original_stage = runtime.engine.stage

    def stage_with_blocking_issue(pending: PendingConnectionSet):
        candidate, report = original_stage(pending)
        report.valid = False
        report.issues.append(
            ValidationIssue(
                code="explicit_gate",
                message="Issue blocks promotion explicitly",
                subject="runtime.primary",
                blocks_promotion=True,
            )
        )
        return candidate, report

    runtime.engine.stage = stage_with_blocking_issue

    with pytest.raises(ValueError, match="failed promotion gate"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="evidence-reject",
        )

    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_CREATED,
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
        SessionEventType.CANDIDATE_REJECTED,
    ]
    rejected = events[-1]
    assert rejected.candidate_id == "evidence-reject"
    assert rejected.graph_version == 1
    assert rejected.payload["reason"] == "explicit_gate:runtime.primary"
    assert rejected.payload["blocking_issues"][0]["code"] == "explicit_gate"

    provenance = runtime.provenance_graph.to_dict()
    assert "graph-candidate:evidence-reject" in provenance["entities"]
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == "graph-candidate:evidence-reject"
        for relation in provenance["relations"]
    )
    assert len(runtime.audit_log.by_kind("session.candidate_rejected")) == 1


def test_commit_graph_rejects_when_policy_vetoes(manifest_dir: Path, graphs_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    policy = runtime.components["policy.primary"]
    original_review = policy.evaluate_promotion

    def reject_review(promotion):
        decision = original_review(promotion)
        return decision.model_copy(update={"decision": "reject", "reason": "policy_veto"})

    policy.evaluate_promotion = reject_review

    with pytest.raises(ValueError, match="policy_veto"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="policy-reject",
        )

    assert runtime.version_manager.active_version is None
    candidate_record = runtime.version_manager.candidates[-1]
    assert candidate_record.candidate_id == "policy-reject"
    assert candidate_record.promoted is False


def test_commit_graph_defers_when_policy_requests_manual_review(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    session_store = InMemorySessionStore()
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), session_store=session_store)
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    policy = runtime.components["policy.primary"]
    original_review = policy.evaluate_promotion
    bus_events: list[str] = []
    runtime.event_bus.subscribe(CANDIDATE_DEFERRED, lambda event: bus_events.append(event.name))
    runtime.event_bus.subscribe(CANDIDATE_REJECTED, lambda event: bus_events.append(event.name))

    def defer_review(promotion):
        decision = original_review(promotion)
        return decision.model_copy(update={"decision": "defer", "reason": "manual_review"})

    policy.evaluate_promotion = defer_review

    with pytest.raises(ValueError, match="manual_review"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="policy-defer",
        )

    assert bus_events == [CANDIDATE_DEFERRED]
    events = session_store.get_events(runtime.session_id)
    assert events[-1].event_type == SessionEventType.CANDIDATE_DEFERRED
    assert events[-1].payload["reason"] == "manual_review"
    candidate_record = runtime.version_manager.candidates[-1]
    assert candidate_record.candidate_id == "policy-defer"
    assert candidate_record.promoted is False
    assert candidate_record.deferred is True
    assert runtime.deferred_candidates() == [candidate_record]
    assert runtime.version_manager.active_version is None


def test_review_deferred_candidate_can_promote_after_policy_allows(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    session_store = InMemorySessionStore()
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), session_store=session_store)
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    policy = runtime.components["policy.primary"]
    original_review = policy.evaluate_promotion

    def defer_review(promotion):
        decision = original_review(promotion)
        return decision.model_copy(update={"decision": "defer", "reason": "manual_review"})

    policy.evaluate_promotion = defer_review

    with pytest.raises(ValueError, match="manual_review"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="policy-defer-allow",
        )

    policy.evaluate_promotion = original_review
    reviewed = runtime.review_deferred_candidate("policy-defer-allow")

    assert reviewed.promoted is True
    assert reviewed.deferred is False
    assert runtime.deferred_candidates() == []
    assert runtime.version_manager.active_version == 1
    assert runtime.build_route_table() is not None
    events = session_store.get_events(runtime.session_id)
    assert events[-2].event_type == SessionEventType.SAFETY_GATE_EVALUATED
    assert events[-1].event_type == SessionEventType.GRAPH_COMMITTED


def test_review_deferred_candidate_can_reject_after_policy_vetoes(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    session_store = InMemorySessionStore()
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), session_store=session_store)
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    policy = runtime.components["policy.primary"]
    original_review = policy.evaluate_promotion
    bus_events: list[str] = []
    runtime.event_bus.subscribe(CANDIDATE_REJECTED, lambda event: bus_events.append(event.name))

    def defer_review(promotion):
        decision = original_review(promotion)
        return decision.model_copy(update={"decision": "defer", "reason": "manual_review"})

    def reject_review(promotion):
        decision = original_review(promotion)
        return decision.model_copy(update={"decision": "reject", "reason": "manual_reject"})

    policy.evaluate_promotion = defer_review

    with pytest.raises(ValueError, match="manual_review"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="policy-defer-reject",
        )

    policy.evaluate_promotion = reject_review
    reviewed = runtime.review_deferred_candidate("policy-defer-reject")

    assert reviewed.promoted is False
    assert reviewed.deferred is False
    assert runtime.deferred_candidates() == []
    assert runtime.version_manager.active_version is None
    assert bus_events == [CANDIDATE_REJECTED]
    events = session_store.get_events(runtime.session_id)
    assert events[-1].event_type == SessionEventType.CANDIDATE_REJECTED
    assert events[-1].payload["reason"] == "manual_reject"


def test_review_external_candidate_marks_adopted_state() -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=Path(".")))
    candidate = CandidateRecord(
        candidate_id="external-adopted",
        snapshot=GraphSnapshot(graph_version=0),
        report=ValidationReport(valid=True),
        promoted=True,
    )

    reviewed = runtime.review_external_candidate(candidate)

    assert candidate.external_review is None
    assert reviewed.external_review is not None
    assert reviewed.external_review.state == ExternalCandidateReviewState.ADOPTED
    assert reviewed.external_review.reason is None
    assert reviewed.promoted is True


def test_review_external_candidate_marks_rejected_state_from_blocking_issues() -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=Path(".")))
    candidate = CandidateRecord(
        candidate_id="external-rejected",
        snapshot=GraphSnapshot(graph_version=0),
        report=ValidationReport(
            valid=False,
            issues=[
                ValidationIssue(
                    code="deepmd_gate_run_status",
                    message="run failed",
                    subject="deepmd-task",
                    blocks_promotion=True,
                )
            ],
        ),
        promoted=False,
    )

    reviewed = runtime.review_external_candidate(candidate)

    assert reviewed.external_review is not None
    assert reviewed.external_review.state == ExternalCandidateReviewState.REJECTED
    assert reviewed.external_review.reason == "deepmd_gate_run_status:deepmd-task"
    assert reviewed.external_review.reviewer == "extension_governance"


def test_commit_graph_rejects_protected_boundary_rewire_with_evidence(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    session_store = InMemorySessionStore()
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), session_store=session_store)
    runtime.boot()

    active_snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    runtime.commit_graph(
        PendingConnectionSet(nodes=active_snapshot.nodes, edges=active_snapshot.edges),
        candidate_id="active-default",
    )

    candidate_nodes = list(active_snapshot.nodes)
    candidate_edges = [
        *active_snapshot.edges,
        active_snapshot.edges[0].model_copy(
            update={
                "connection_id": "policy-feed",
                "target": "policy.primary.decision",
            }
        ),
    ]

    with pytest.raises(ValueError, match="protected_boundary_violation:policy.primary"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=candidate_nodes, edges=candidate_edges),
            candidate_id="protected-rewire",
        )

    candidate_record = runtime.version_manager.candidates[-1]
    assert candidate_record.candidate_id == "protected-rewire"
    assert candidate_record.promoted is False
    assert any(
        issue.code == "protected_boundary_violation" for issue in candidate_record.report.issues
    )

    events = session_store.get_events(runtime.session_id)
    rejected = events[-1]
    assert rejected.event_type == SessionEventType.CANDIDATE_REJECTED
    assert rejected.payload["reason"] == "protected_boundary_violation:policy.primary"
    assert rejected.payload["blocking_issues"][0]["code"] == "protected_boundary_violation"


def test_boot_injects_default_identity_boundary(manifest_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()

    gateway = runtime.components["gateway.primary"]
    policy = runtime.components["policy.primary"]

    payload = gateway.issue_task(
        "fetch dataset",
        subject_id="service:gateway",
        credentials={"api_key": "top-secret"},
    )
    record = policy.record(
        "allow",
        payload["subject"],
        attestation_id=payload["attestation"]["attestation_id"],
    )

    assert gateway._runtime.identity_boundary is not None
    assert policy._runtime.identity_boundary is not None
    assert payload["subject"] == "service:gateway"
    assert record["credential_bound"] == "true"


def test_boot_preserves_explicit_identity_boundary(manifest_dir: Path) -> None:
    boundary = InMemoryIdentityBoundary()
    runtime = HarnessRuntime(
        ComponentDiscovery(bundled=manifest_dir),
        runtime_factory=lambda manifest: ComponentRuntime(identity_boundary=boundary),
    )
    runtime.boot()

    gateway = runtime.components["gateway.primary"]
    policy = runtime.components["policy.primary"]

    assert gateway._runtime.identity_boundary is boundary
    assert policy._runtime.identity_boundary is boundary


def test_boot_injects_runtime_services(manifest_dir: Path) -> None:
    quota = ResourceQuota(resource_type="gpu", remaining=1)
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir), resource_quota=quota)
    runtime.boot()

    gateway_runtime = runtime.components["gateway.primary"]._runtime

    assert gateway_runtime.services is not None
    assert gateway_runtime.services.event_bus is runtime.event_bus
    assert gateway_runtime.services.session_store is runtime.session_store
    assert gateway_runtime.services.artifact_store is runtime.artifact_store
    assert gateway_runtime.services.audit_log is runtime.audit_log
    assert gateway_runtime.services.provenance_graph is runtime.provenance_graph
    assert gateway_runtime.services.identity_boundary is runtime._default_identity_boundary
    assert gateway_runtime.services.mutation_submitter is runtime.submitter
    assert gateway_runtime.services.resource_quota is quota
    assert gateway_runtime.resolved_resource_quota() is quota


def test_component_runtime_resolvers_prefer_services_over_legacy_fields() -> None:
    legacy_boundary = object()
    service_boundary = object()
    services = RuntimeServices(
        event_bus=object(),
        session_store=object(),
        artifact_store=object(),
        audit_log=object(),
        provenance_graph=object(),
        identity_boundary=service_boundary,
        graph_reader=object(),
        mutation_submitter=object(),
        resource_quota=ResourceQuota(resource_type="cpu", remaining=4),
    )
    runtime = ComponentRuntime(
        services=services,
        event_bus=object(),
        session_store=object(),
        artifact_store=object(),
        audit_log=object(),
        provenance_graph=object(),
        identity_boundary=legacy_boundary,
        graph_reader=object(),
        mutation_submitter=object(),
        resource_quota=ResourceQuota(resource_type="gpu", remaining=1),
    )

    assert runtime.resolved_event_bus() is services.event_bus
    assert runtime.resolved_session_store() is services.session_store
    assert runtime.resolved_artifact_store() is services.artifact_store
    assert runtime.resolved_audit_log() is services.audit_log
    assert runtime.resolved_provenance_graph() is services.provenance_graph
    assert runtime.resolved_identity_boundary() is service_boundary
    assert runtime.resolved_graph_reader() is services.graph_reader
    assert runtime.resolved_mutation_submitter() is services.mutation_submitter
    assert runtime.resolved_resource_quota() is services.resource_quota


def test_component_runtime_resolvers_fall_back_to_legacy_fields() -> None:
    runtime = ComponentRuntime(
        event_bus=object(),
        session_store=object(),
        artifact_store=object(),
        audit_log=object(),
        provenance_graph=object(),
        identity_boundary=object(),
        graph_reader=object(),
        mutation_submitter=object(),
        resource_quota=ResourceQuota(resource_type="gpu", remaining=1),
    )

    assert runtime.resolved_event_bus() is runtime.event_bus
    assert runtime.resolved_session_store() is runtime.session_store
    assert runtime.resolved_artifact_store() is runtime.artifact_store
    assert runtime.resolved_audit_log() is runtime.audit_log
    assert runtime.resolved_provenance_graph() is runtime.provenance_graph
    assert runtime.resolved_identity_boundary() is runtime.identity_boundary
    assert runtime.resolved_graph_reader() is runtime.graph_reader
    assert runtime.resolved_mutation_submitter() is runtime.mutation_submitter
    assert runtime.resolved_resource_quota() is runtime.resource_quota


def test_component_runtime_prefers_brain_provider_and_falls_back_to_llm() -> None:
    direct = _RuntimeBrainProvider()
    fallback = _RuntimeBrainProvider()

    runtime = ComponentRuntime(brain_provider=direct, llm=fallback)
    assert runtime.resolved_brain_provider() is direct

    fallback_only = ComponentRuntime(llm=fallback)
    assert fallback_only.resolved_brain_provider() is fallback

    empty = ComponentRuntime()
    assert empty.resolved_brain_provider() is None


class _TierLimitedSandboxClient:
    def __init__(self, supported: set[SandboxTier]) -> None:
        self.supported = supported

    def supports_tier(self, tier: SandboxTier) -> bool:
        return tier in self.supported


class _RuntimeBrainProvider(BrainProvider):
    def propose(self, optimizer, observations):  # type: ignore[no-untyped-def]
        return []

    def evaluate(self, optimizer, proposal, observations):  # type: ignore[no-untyped-def]
        return None


def test_commit_graph_rejects_unavailable_declared_sandbox_tier(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    runtime = HarnessRuntime(
        ComponentDiscovery(bundled=manifest_dir),
        runtime_factory=lambda manifest: ComponentRuntime(
            identity_boundary=InMemoryIdentityBoundary(),
            sandbox_client=_TierLimitedSandboxClient({SandboxTier.V8_WASM}),
        ),
    )
    runtime.boot()

    registered = runtime.registry.components["executor.primary"]
    registered.manifest.policy.sandbox.tier = "firecracker"
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")

    with pytest.raises(ValueError, match="sandbox policy requires tier 'firecracker'"):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="sandbox-reject",
        )


def test_commit_graph_rejects_identity_bound_unprotected_component(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()

    registered = runtime.registry.components["gateway.primary"]
    registered.manifest.policy.credentials.requires_subject = True
    registered.manifest.safety.protected = False
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")

    with pytest.raises(
        ValueError, match="requires identity-bound credentials but is not protected"
    ):
        runtime.commit_graph(
            PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
            candidate_id="credential-reject",
        )


def test_boot_registers_declared_migration_adapters_into_runtime_registry(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    component_module = tmp_path / "boot_migration_component.py"
    component_module.write_text(
        """
from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class BootMigrationComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(\"boot-migrator.primary\")
        api.register_migration_adapter(
            from_version=1,
            to_version=2,
            adapter=lambda old, delta: {**old, \"migrated\": True, **(delta or {})},
        )
""".strip()
    )
    manifest = {
        "name": "boot-migrator",
        "version": "0.1.0",
        "kind": "core",
        "entry": "boot_migration_component:BootMigrationComponent",
        "contracts": {
            "inputs": [],
            "outputs": [],
            "events": [],
            "provides": [],
            "requires": [],
            "slots": [{"slot": "boot-migrator.primary", "binding": "primary", "required": True}],
        },
        "safety": {"protected": False, "mutability": "mutable", "hot_swap": True},
        "state_schema_version": 1,
    }
    (manifest_dir / "boot-migrator.json").write_text(json.dumps(manifest))

    sys.path.insert(0, str(tmp_path))
    try:
        runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
        runtime.boot()

        component = runtime.components["boot-migrator.primary"]
        assert component._runtime.migration_adapters is runtime.migration_adapters

        resolved = runtime.migration_adapters.resolve(
            source_type="boot-migrator.primary",
            source_version=1,
            target_type="boot-migrator.primary",
            target_version=2,
        )
        assert resolved is not None

        orchestrator = HotSwapOrchestrator(migration_adapters=runtime.migration_adapters)
        report = orchestrator.swap_sync(
            component_id="boot-migrator.primary",
            outgoing=_TestStatefulComponent(initial={"count": 1}),
            incoming=_TestStatefulComponent(),
            delta={"delta": 2},
            state_schema_version=1,
            target_state_schema_version=2,
        )

        assert report.success is True
        assert report.migrated_state == {"count": 1, "migrated": True, "delta": 2}
    finally:
        sys.path.remove(str(tmp_path))


def test_boot_reports_manifest_validation_issues(tmp_path: Path, manifest_dir: Path) -> None:
    # Copy one manifest but replace its entry with a broken class to force
    # an import failure at instantiation. Static validation uses
    # harness_version / bins / env only; we instead exercise the happy path
    # with unreachable bins requirement.

    broken_dir = tmp_path / "manifests"
    broken_dir.mkdir()
    src = manifest_dir / "memory.json"
    manifest = json.loads(src.read_text())
    manifest["bins"] = ["definitely-not-a-real-binary-xyz"]
    (broken_dir / "memory.json").write_text(json.dumps(manifest))

    runtime = HarnessRuntime(ComponentDiscovery(bundled=broken_dir))
    report = runtime.boot()
    assert "memory" in report.validation_issues
    assert "memory.primary" not in runtime.registry.components


class _TestStatefulComponent:
    def __init__(self, *, initial: dict[str, object] | None = None) -> None:
        self.state = dict(initial or {})

    async def suspend(self) -> None:
        return None

    async def deactivate(self) -> None:
        return None

    async def activate(self, runtime: ComponentRuntime | None) -> None:
        self._runtime = runtime

    async def export_state(self) -> dict[str, object]:
        return dict(self.state)

    async def import_state(self, state: dict[str, object]) -> None:
        self.state = dict(state)

    async def resume(self, new_state: dict[str, object] | None = None) -> None:
        if new_state is not None:
            self.state = dict(new_state)

    async def transform_state(
        self, old_state: dict[str, object], delta: dict[str, object] | None = None
    ) -> dict[str, object]:
        return {**old_state, **(delta or {})}
