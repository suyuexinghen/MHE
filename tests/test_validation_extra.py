"""Additional semantic validator coverage."""

from __future__ import annotations

from pathlib import Path

from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import ComponentNode, ConnectionEdge, PendingConnectionSet
from metaharness.sdk.contracts import RouteMode
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in ["gateway", "runtime", "executor", "evaluation"]:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def _node(cid: str) -> ComponentNode:
    return ComponentNode(component_id=cid, component_type="T", implementation="i", version="1")


def test_duplicate_connection_id_is_reported(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    edges = [
        ConnectionEdge(
            connection_id="dup",
            source="gateway.primary.task",
            target="runtime.primary.task",
            payload="TaskRequest",
            mode=RouteMode.SYNC,
        ),
        ConnectionEdge(
            connection_id="dup",
            source="runtime.primary.result",
            target="executor.primary.task",
            payload="TaskRequest",
            mode=RouteMode.SYNC,
        ),
    ]
    _, report = engine.stage(
        PendingConnectionSet(
            nodes=[
                _node("gateway.primary"),
                _node("runtime.primary"),
                _node("executor.primary"),
            ],
            edges=edges,
        )
    )
    assert report.valid is False
    assert any(issue.code == "duplicate_connection" for issue in report.issues)


def test_unknown_component_and_port_reported(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    edge = ConnectionEdge(
        connection_id="c1",
        source="ghost.primary.out",
        target="runtime.primary.unknown",
        payload="TaskRequest",
        mode=RouteMode.SYNC,
    )
    _, report = engine.stage(PendingConnectionSet(nodes=[_node("runtime.primary")], edges=[edge]))
    codes = {issue.code for issue in report.issues}
    assert "unknown_source_component" in codes
    assert "unknown_input_port" in codes


def test_missing_required_input(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    _, report = engine.stage(
        PendingConnectionSet(nodes=[_node("gateway.primary"), _node("runtime.primary")], edges=[])
    )
    codes = {issue.code for issue in report.issues}
    assert "missing_required_input" in codes


def test_payload_mismatch(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    edge = ConnectionEdge(
        connection_id="c1",
        source="gateway.primary.task",
        target="runtime.primary.task",
        payload="WrongPayload",
        mode=RouteMode.SYNC,
    )
    _, report = engine.stage(
        PendingConnectionSet(
            nodes=[_node("gateway.primary"), _node("runtime.primary")], edges=[edge]
        )
    )
    assert any(issue.code == "payload_mismatch" for issue in report.issues)
