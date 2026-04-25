"""Hot-reload orchestration tests."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from metaharness.core.models import SessionEventType
from metaharness.hotreload import (
    CheckpointManager,
    HotSwapOrchestrator,
    MigrationAdapterRegistry,
    ObservationWindowEvaluator,
    SagaRollback,
    SagaStep,
    forbidden_event_probe,
    max_metric_probe,
)
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class _StatefulComponent(HarnessComponent):
    def __init__(self, *, initial: dict[str, Any] | None = None) -> None:
        self.state: dict[str, Any] = dict(initial or {})
        self.suspended = 0
        self.resumed = 0
        self.deactivated = 0
        self.activated = 0
        self.transform_calls = 0
        self._runtime: ComponentRuntime | None = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("runtime.primary")

    async def activate(self, runtime: ComponentRuntime | None) -> None:
        self.activated += 1
        self._runtime = runtime

    async def deactivate(self) -> None:
        self.deactivated += 1

    async def export_state(self) -> dict[str, Any]:
        return dict(self.state)

    async def import_state(self, state: Mapping[str, Any]) -> None:
        self.state = dict(state)

    async def suspend(self) -> None:
        self.suspended += 1

    async def resume(self, new_state: Mapping[str, Any] | None = None) -> None:
        self.resumed += 1
        if new_state is not None:
            self.state = dict(new_state)

    async def transform_state(
        self, old_state: Mapping[str, Any], delta: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        self.transform_calls += 1
        return await super().transform_state(old_state, delta)


class _ProtectedStatefulComponent(_StatefulComponent):
    protected = True


def test_checkpoint_capture_and_restore() -> None:
    comp = _StatefulComponent(initial={"a": 1})
    manager = CheckpointManager(retention=2)
    ckpt = asyncio.run(manager.capture(comp, component_id="x"))
    assert ckpt.state == {"a": 1}
    assert manager.latest("x") is ckpt

    comp.state = {"a": 99}
    asyncio.run(manager.restore(comp, ckpt))
    assert comp.state == {"a": 1}


def test_checkpoint_retention_bounds_history() -> None:
    comp = _StatefulComponent(initial={"v": 0})
    manager = CheckpointManager(retention=2)

    async def populate() -> None:
        for i in range(5):
            comp.state = {"v": i}
            await manager.capture(comp, component_id="x")

    asyncio.run(populate())
    history = manager.history("x")
    assert len(history) == 2
    assert history[-1].state == {"v": 4}


def test_checkpoint_capture_records_lineage_and_session_evidence() -> None:
    comp = _StatefulComponent(initial={"v": 1})
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance = ProvGraph()
    manager = CheckpointManager(retention=4)
    manager.bind_evidence_runtime(
        session_id="hotreload-session",
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance,
    )

    first = asyncio.run(
        manager.capture(
            comp, component_id="runtime.primary", graph_version=3, candidate_id="swap-a"
        )
    )
    comp.state = {"v": 2}
    second = asyncio.run(
        manager.capture(
            comp, component_id="runtime.primary", graph_version=4, candidate_id="swap-b"
        )
    )

    assert second.parent_checkpoint_id == first.checkpoint_id
    events = session_store.get_events("hotreload-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CHECKPOINT_SAVED,
        SessionEventType.CHECKPOINT_SAVED,
    ]
    assert events[-1].payload["parent_checkpoint_id"] == first.checkpoint_id
    assert len(second.evidence_refs) == 2
    assert len(audit_log.by_kind("session.checkpoint_saved")) == 2
    data = provenance.to_dict()
    assert f"checkpoint:{second.checkpoint_id}" in data["entities"]
    assert any(
        relation["subject"] == f"checkpoint:{second.checkpoint_id}"
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == f"checkpoint:{first.checkpoint_id}"
        for relation in data["relations"]
    )


def test_hot_swap_preserves_state_through_migration() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    orchestrator = HotSwapOrchestrator()
    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        delta={"added": True},
    )
    assert report.success is True
    assert incoming.state.get("counter") == 7
    assert incoming.state.get("added") is True
    assert outgoing.suspended == 1
    assert outgoing.deactivated == 1
    assert incoming.resumed == 1


def test_hot_swap_uses_registered_exact_adapter() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    registry = MigrationAdapterRegistry()
    registry.register_component_adapter(
        component_id="runtime.primary",
        from_version=1,
        to_version=2,
        adapter=lambda old, delta: {**old, "counter": old["counter"] + 10, **(delta or {})},
    )
    orchestrator = HotSwapOrchestrator(migration_adapters=registry)

    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        delta={"added": True},
        state_schema_version=1,
        target_state_schema_version=2,
    )

    assert report.success is True
    assert incoming.state == {"counter": 17, "added": True}
    assert incoming.transform_calls == 0


def test_hot_swap_defaults_to_runtime_migration_registry() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    runtime_registry = MigrationAdapterRegistry()
    runtime_registry.register_component_adapter(
        component_id="runtime.primary",
        from_version=1,
        to_version=2,
        adapter=lambda old, delta: {**old, "counter": old["counter"] + 20, **(delta or {})},
    )
    runtime = ComponentRuntime(migration_adapters=runtime_registry)
    asyncio.run(outgoing.activate(runtime))
    asyncio.run(incoming.activate(runtime))

    report = HotSwapOrchestrator().swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        delta={"added": True},
        state_schema_version=1,
        target_state_schema_version=2,
    )

    assert report.success is True
    assert incoming.state == {"counter": 27, "added": True}
    assert incoming.transform_calls == 0


def test_hot_swap_uses_wildcard_adapter_when_exact_missing() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    registry = MigrationAdapterRegistry()
    registry.register(
        source_type="*",
        source_version=1,
        target_type="*",
        target_version=None,
        adapter=lambda old, delta: {**old, "wildcard": True, **(delta or {})},
    )
    orchestrator = HotSwapOrchestrator(migration_adapters=registry)

    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        delta={"added": True},
        state_schema_version=1,
        target_state_schema_version=99,
    )

    assert report.success is True
    assert incoming.state == {"counter": 7, "wildcard": True, "added": True}
    assert incoming.transform_calls == 0


def test_hot_swap_falls_back_to_transform_state_without_adapter() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    orchestrator = HotSwapOrchestrator()

    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        delta={"added": True},
        state_schema_version=1,
        target_state_schema_version=2,
    )

    assert report.success is True
    assert incoming.state == {"counter": 7, "added": True}
    assert incoming.transform_calls == 1


def test_hot_swap_saga_rolls_back_on_migration_failure() -> None:
    class BadIncoming(_StatefulComponent):
        async def transform_state(
            self, old_state: Mapping[str, Any], delta: Mapping[str, Any] | None = None
        ) -> dict[str, Any]:
            raise RuntimeError("migration failed")

    outgoing = _StatefulComponent(initial={"v": 1})
    incoming = BadIncoming()
    orchestrator = HotSwapOrchestrator()
    report = orchestrator.swap_sync(
        component_id="runtime.primary", outgoing=outgoing, incoming=incoming
    )
    assert report.success is False
    assert "migration failed" in (report.error or "")
    # Compensation should have resumed the outgoing component.
    assert outgoing.resumed == 1


def test_observation_window_evaluator_rejects_metric_and_event_failures() -> None:
    evaluator = ObservationWindowEvaluator(
        probes=[
            ("latency", max_metric_probe("latency_p95_ms", 200.0)),
            ("events", forbidden_event_probe({"panic", "crash_loop"})),
        ]
    )

    metric_failure = evaluator.evaluate(metrics={"latency_p95_ms": 250.0}, events=[])
    assert metric_failure.passed is False
    assert metric_failure.rejected_by == "latency"
    assert metric_failure.evidence["value"] == 250.0

    event_failure = evaluator.evaluate(
        metrics={"latency_p95_ms": 100.0}, events=[{"name": "panic"}]
    )
    assert event_failure.passed is False
    assert event_failure.rejected_by == "events"
    assert event_failure.evidence["seen"] == ["panic"]


def test_hot_swap_observation_window_allows_healthy_swap() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    evaluator = ObservationWindowEvaluator(
        probes=[("latency", max_metric_probe("latency_p95_ms", 200.0))]
    )
    orchestrator = HotSwapOrchestrator(observation_evaluator=evaluator)

    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        observation_metrics={"latency_p95_ms": 120.0},
    )

    assert report.success is True
    assert report.observation is not None
    assert report.observation.passed is True
    assert incoming.state["counter"] == 7


def test_hot_swap_requires_explicit_approval_for_protected_component() -> None:
    outgoing = _ProtectedStatefulComponent(initial={"counter": 7})
    incoming = _ProtectedStatefulComponent()

    report = HotSwapOrchestrator().swap_sync(
        component_id="policy.primary",
        outgoing=outgoing,
        incoming=incoming,
    )

    assert report.success is False
    assert report.error == "protected component requires explicit hot-swap approval"
    assert report.affected_protected_components == ["policy.primary"]
    assert outgoing.suspended == 0


def test_hot_swap_rejected_protected_swap_records_governance_evidence() -> None:
    outgoing = _ProtectedStatefulComponent(initial={"counter": 7})
    incoming = _ProtectedStatefulComponent()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance = ProvGraph()

    report = HotSwapOrchestrator(
        session_id="hotreload-session",
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance,
    ).swap_sync(
        component_id="policy.primary",
        outgoing=outgoing,
        incoming=incoming,
        candidate_id="swap-protected-reject",
        graph_version=12,
        rollback_target=11,
    )

    assert report.success is False
    events = session_store.get_events("hotreload-session")
    assert [event.event_type for event in events] == [SessionEventType.HOT_SWAP_ROLLED_BACK]
    assert events[-1].payload["rollback_target"] == 11
    assert events[-1].payload["error"] == "protected component requires explicit hot-swap approval"
    assert len(audit_log.by_kind("session.hot_swap_rolled_back")) == 1
    assert any(ref.startswith("session-event:") for ref in report.evidence_refs)


def test_hot_swap_records_governed_completion_evidence() -> None:
    outgoing = _ProtectedStatefulComponent(initial={"counter": 7})
    incoming = _ProtectedStatefulComponent()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance = ProvGraph()
    orchestrator = HotSwapOrchestrator(
        session_id="hotreload-session",
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance,
    )

    report = orchestrator.swap_sync(
        component_id="policy.primary",
        outgoing=outgoing,
        incoming=incoming,
        candidate_id="swap-protected",
        graph_version=9,
        rollback_target=8,
        allow_protected=True,
    )

    assert report.success is True
    events = session_store.get_events("hotreload-session")
    assert [event.event_type for event in events] == [
        SessionEventType.HOT_SWAP_INITIATED,
        SessionEventType.CHECKPOINT_SAVED,
        SessionEventType.HOT_SWAP_COMPLETED,
    ]
    assert events[-1].payload["affected_protected_components"] == ["policy.primary"]
    assert events[-1].payload["rollback_target"] == 8
    assert any(ref.startswith("session-event:") for ref in report.evidence_refs)
    assert len(audit_log.by_kind("session.hot_swap_completed")) == 1
    data = provenance.to_dict()
    assert "hot-swap:policy.primary" in data["entities"]
    checkpoint_entity = f"checkpoint:{report.checkpoint.checkpoint_id}"
    session_event_entities = [
        entity_id
        for entity_id, entity in data["entities"].items()
        if entity["kind"] == "session_event"
    ]
    assert any(
        relation["subject"] in session_event_entities
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == checkpoint_entity
        for relation in data["relations"]
    )


def test_hot_swap_rejected_protected_swap_preserves_outgoing_state() -> None:
    outgoing = _ProtectedStatefulComponent(initial={"counter": 7})
    incoming = _ProtectedStatefulComponent(initial={"counter": 0})

    report = HotSwapOrchestrator().swap_sync(
        component_id="policy.primary",
        outgoing=outgoing,
        incoming=incoming,
    )

    assert report.success is False
    assert outgoing.state == {"counter": 7}
    assert incoming.state == {"counter": 0}
    assert outgoing.deactivated == 0
    assert incoming.resumed == 0


def test_hot_swap_observation_window_rolls_back_failed_swap() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    evaluator = ObservationWindowEvaluator(
        probes=[("latency", max_metric_probe("latency_p95_ms", 200.0))]
    )
    orchestrator = HotSwapOrchestrator(observation_evaluator=evaluator)

    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        observation_metrics={"latency_p95_ms": 250.0},
    )

    assert report.success is False
    assert report.observation is not None
    assert report.observation.passed is False
    assert report.observation.rejected_by == "latency"
    assert "exceeded threshold" in (report.error or "")
    assert outgoing.resumed == 1
    assert incoming.deactivated == 1


def test_hot_swap_records_rollback_evidence_on_failed_observation() -> None:
    outgoing = _StatefulComponent(initial={"counter": 7})
    incoming = _StatefulComponent()
    evaluator = ObservationWindowEvaluator(
        probes=[("latency", max_metric_probe("latency_p95_ms", 200.0))]
    )
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance = ProvGraph()
    orchestrator = HotSwapOrchestrator(
        observation_evaluator=evaluator,
        session_id="hotreload-session",
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance,
    )

    report = orchestrator.swap_sync(
        component_id="runtime.primary",
        outgoing=outgoing,
        incoming=incoming,
        candidate_id="swap-rollback",
        graph_version=11,
        rollback_target=10,
        observation_metrics={"latency_p95_ms": 250.0},
    )

    assert report.success is False
    events = session_store.get_events("hotreload-session")
    assert [event.event_type for event in events] == [
        SessionEventType.HOT_SWAP_INITIATED,
        SessionEventType.CHECKPOINT_SAVED,
        SessionEventType.HOT_SWAP_ROLLED_BACK,
    ]
    assert events[-1].payload["rollback_target"] == 10
    assert events[-1].payload["checkpoint_id"] == report.checkpoint.checkpoint_id
    assert len(audit_log.by_kind("session.hot_swap_rolled_back")) == 1
    data = provenance.to_dict()
    assert any(
        relation["subject"].startswith("session-event:")
        and relation["kind"] == RelationKind.WAS_DERIVED_FROM.value
        and relation["object"] == f"checkpoint:{report.checkpoint.checkpoint_id}"
        for relation in data["relations"]
    )


def test_saga_rollback_compensates_on_failure() -> None:
    log: list[str] = []

    async def ok1() -> None:
        log.append("do1")

    async def ok2() -> None:
        log.append("do2")

    async def fail() -> None:
        raise RuntimeError("boom")

    async def undo1() -> None:
        log.append("undo1")

    async def undo2() -> None:
        log.append("undo2")

    saga = SagaRollback(
        [
            SagaStep(name="s1", forward=ok1, compensate=undo1),
            SagaStep(name="s2", forward=ok2, compensate=undo2),
            SagaStep(name="s3", forward=fail),
        ]
    )
    ok, results = asyncio.run(saga.run())
    assert ok is False
    # Compensations run in reverse order of successful forwards.
    assert log == ["do1", "do2", "undo2", "undo1"]
    assert [r.compensated for r in results if r.success] == [True, True]
