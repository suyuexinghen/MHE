from __future__ import annotations

import asyncio
from typing import Any

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.drain import DrainCoordinator, DrainPolicy, DrainState
from metaharness.core.event_bus import EventBus
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import ConnectionEdge, GraphSnapshot, PendingConnectionSet
from metaharness.sdk.contracts import RouteMode
from metaharness.sdk.discovery import ComponentDiscovery
from metaharness.sdk.registry import ComponentRegistry


def test_connection_engine_buffers_and_replays_routes_during_drain() -> None:
    engine = ConnectionEngine(ComponentRegistry(), GraphVersionStore())
    received: list[str] = []
    _load_test_route(engine)
    engine.register_handler("target.in", lambda payload: received.append(payload))

    engine.begin_drain("epoch-1", max_buffered=4)
    assert engine.emit("source.out", "during-drain") == []
    assert received == []

    engine.end_drain(replay=True)

    assert received == ["during-drain"]


def test_event_bus_buffers_and_replays_events_during_drain() -> None:
    bus = EventBus()
    received: list[tuple[str, dict[str, str]]] = []
    bus.subscribe("graph.event", lambda event: received.append((event.payload, event.headers)))

    bus.begin_drain("epoch-1", max_buffered=4)
    assert bus.publish("graph.event", "during-drain") == []
    assert received == []

    bus.end_drain(replay=True)

    assert received == [
        ("during-drain", {"drain_epoch": "epoch-1", "replayed_from_drain_epoch": "epoch-1"})
    ]


def test_drain_coordinator_suspends_resumes_and_replays_buffers() -> None:
    engine = ConnectionEngine(ComponentRegistry(), GraphVersionStore())
    bus = EventBus()
    component = _DrainAwareComponent()
    coordinator = DrainCoordinator(
        engine=engine,
        event_bus=bus,
        components={"runtime.primary": component},
        policy=DrainPolicy(max_buffered_routes=4, max_buffered_events=4),
    )
    routed: list[str] = []
    events: list[str] = []
    _load_test_route(engine)
    engine.register_handler("target.in", lambda payload: routed.append(payload))
    bus.subscribe("graph.event", lambda event: events.append(event.payload))

    epoch = coordinator.begin(
        candidate_id="candidate-1",
        graph_version=1,
        affected_components=["runtime.primary"],
    )
    engine.emit("source.out", "route-buffer")
    bus.publish("graph.event", "event-buffer")
    report = coordinator.complete(epoch)

    assert report.success is True
    assert report.epoch.state == DrainState.COMPLETED
    assert component.suspended == 1
    assert component.resumed == 1
    assert routed == ["route-buffer"]
    assert events == ["event-buffer"]
    assert report.epoch.buffered_routes == 1
    assert report.epoch.buffered_events == 1


def test_commit_graph_uses_drain_epoch(manifest_dir, graphs_dir) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")

    version = runtime.commit_graph(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
        candidate_id="default",
    )

    assert version == 1
    assert runtime.drain_coordinator.reports[-1].success is True
    assert runtime.drain_coordinator.reports[-1].epoch.candidate_id == "default"
    assert runtime.drain_coordinator.reports[-1].epoch.state == DrainState.COMPLETED


def test_commit_graph_resumes_after_cutover_failure(manifest_dir, graphs_dir) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    original_commit = runtime.engine.commit

    def fail_commit(*args, **kwargs):
        raise RuntimeError("cutover failed")

    runtime.engine.commit = fail_commit

    try:
        try:
            runtime.commit_graph(
                PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
                candidate_id="failed-cutover",
            )
        except RuntimeError as exc:
            assert str(exc) == "cutover failed"
        else:
            raise AssertionError("expected cutover failure")
    finally:
        runtime.engine.commit = original_commit

    assert runtime.drain_coordinator.current_epoch is None
    assert runtime.engine.drain_active is False
    assert runtime.event_bus.drain_active is False
    assert runtime.drain_coordinator.reports[-1].success is False


def test_commit_graph_preserves_committed_lifecycle_on_later_drain(
    manifest_dir, graphs_dir
) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    pending = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)

    runtime.commit_graph(pending, candidate_id="default-1")
    runtime.commit_graph(pending, candidate_id="default-2")

    assert runtime.lifecycle.phase("gateway.primary").value == "committed"
    assert (
        runtime.drain_coordinator.reports[-1].epoch.previous_phases["gateway.primary"].value
        == "committed"
    )


def _load_test_route(engine: ConnectionEngine) -> None:
    engine.load_graph(
        GraphSnapshot(
            graph_version=1,
            edges=[
                ConnectionEdge(
                    connection_id="route-1",
                    source="source.out",
                    target="target.in",
                    payload="str",
                    mode=RouteMode.SYNC,
                )
            ],
        )
    )


class _DrainAwareComponent:
    def __init__(self) -> None:
        self.suspended = 0
        self.resumed = 0

    async def suspend(self) -> None:
        self.suspended += 1
        await asyncio.sleep(0)

    async def resume(self, new_state: Any | None = None) -> None:
        self.resumed += 1
        await asyncio.sleep(0)
