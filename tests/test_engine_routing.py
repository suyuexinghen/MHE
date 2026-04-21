"""Routing and mode-specific behavior of the ConnectionEngine."""

from __future__ import annotations

import asyncio

from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import ComponentNode, ConnectionEdge, GraphSnapshot
from metaharness.sdk.contracts import ConnectionPolicy, RouteMode
from metaharness.sdk.registry import ComponentRegistry


def _snapshot(edges: list[ConnectionEdge]) -> GraphSnapshot:
    ids = set()
    nodes: list[ComponentNode] = []
    for e in edges:
        for side in (e.source, e.target):
            comp = side.rsplit(".", 1)[0]
            if comp not in ids:
                ids.add(comp)
                nodes.append(
                    ComponentNode(
                        component_id=comp,
                        component_type="Test",
                        implementation="test",
                        version="0.0.0",
                    )
                )
    return GraphSnapshot(graph_version=1, nodes=nodes, edges=edges)


def _engine_with(edges: list[ConnectionEdge]) -> ConnectionEngine:
    engine = ConnectionEngine(ComponentRegistry(), GraphVersionStore())
    engine.load_graph(_snapshot(edges))
    return engine


def test_emit_dispatches_to_registered_handler() -> None:
    engine = _engine_with(
        [
            ConnectionEdge(
                connection_id="c1",
                source="a.out",
                target="b.in",
                payload="X",
                mode=RouteMode.SYNC,
            )
        ]
    )
    seen: list[int] = []
    engine.register_handler("b.in", lambda p: seen.append(p) or p * 2)

    results = engine.emit("a.out", 4)
    assert seen == [4]
    assert results == [8]


def test_emit_ignores_unregistered_handlers() -> None:
    engine = _engine_with(
        [
            ConnectionEdge(
                connection_id="c1",
                source="a.out",
                target="b.in",
                payload="X",
                mode=RouteMode.SYNC,
            )
        ]
    )
    assert engine.emit("a.out", 1) == []


def test_shadow_route_does_not_contribute_results_and_swallows_errors() -> None:
    edges = [
        ConnectionEdge(
            connection_id="c1",
            source="a.out",
            target="primary.in",
            payload="X",
            mode=RouteMode.SYNC,
        ),
        ConnectionEdge(
            connection_id="c2",
            source="a.out",
            target="shadow.in",
            payload="X",
            mode=RouteMode.SHADOW,
            policy=ConnectionPolicy.SHADOW,
        ),
    ]
    engine = _engine_with(edges)

    def raise_error(_: int) -> int:
        raise RuntimeError("boom")

    engine.register_handler("primary.in", lambda p: p + 1)
    engine.register_handler("shadow.in", raise_error)

    results = engine.emit("a.out", 1)
    assert results == [2]


def test_event_route_collects_all_handler_results() -> None:
    edges = [
        ConnectionEdge(
            connection_id="c1",
            source="a.out",
            target="sub1.in",
            payload="Ev",
            mode=RouteMode.EVENT,
        ),
        ConnectionEdge(
            connection_id="c2",
            source="a.out",
            target="sub2.in",
            payload="Ev",
            mode=RouteMode.EVENT,
        ),
    ]
    engine = _engine_with(edges)
    engine.register_handler("sub1.in", lambda p: f"s1:{p}")
    engine.register_handler("sub2.in", lambda p: f"s2:{p}")
    assert engine.emit("a.out", "ping") == ["s1:ping", "s2:ping"]


def test_emit_async_awaits_coroutine_handlers() -> None:
    edges = [
        ConnectionEdge(
            connection_id="c1",
            source="a.out",
            target="b.in",
            payload="X",
            mode=RouteMode.ASYNC,
        )
    ]
    engine = _engine_with(edges)

    async def handler(payload: int) -> int:
        await asyncio.sleep(0)
        return payload + 100

    engine.register_handler("b.in", handler)
    results = asyncio.run(engine.emit_async("a.out", 1))
    assert results == [101]


def test_rollback_reloads_previous_route_table() -> None:
    store = GraphVersionStore()
    engine = ConnectionEngine(ComponentRegistry(), store)
    first = _snapshot(
        [
            ConnectionEdge(
                connection_id="c1",
                source="a.out",
                target="b.in",
                payload="X",
                mode=RouteMode.SYNC,
            )
        ]
    )
    second = GraphSnapshot(
        graph_version=2,
        nodes=first.nodes,
        edges=[
            ConnectionEdge(
                connection_id="c2",
                source="a.out",
                target="c.in",
                payload="X",
                mode=RouteMode.SYNC,
            )
        ],
    )
    store.commit(first)
    engine.load_graph(first)
    store.commit(second)
    engine.load_graph(second)

    assert [b.target for b in engine.bindings_for("a.out")] == ["c.in"]
    engine.rollback()
    assert [b.target for b in engine.bindings_for("a.out")] == ["b.in"]
