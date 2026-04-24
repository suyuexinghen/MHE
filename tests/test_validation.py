from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import ComponentNode, ConnectionEdge, PendingConnectionSet
from metaharness.sdk.contracts import RouteMode
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _build_registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in [
        "gateway",
        "runtime",
        "executor",
        "evaluation",
        "planner",
        "policy",
        "observability",
        "memory",
    ]:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_valid_graph_produces_clean_report(manifest_dir: Path, graphs_dir: Path) -> None:
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")

    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("candidate-1", candidate, report)

    assert report.valid is True
    assert version == 1
    assert engine.emit("gateway.primary.task", {"task": "demo"}) == []


def test_invalid_candidate_does_not_mutate_active_graph(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    registry = _build_registry(manifest_dir)
    store = GraphVersionStore()
    engine = ConnectionEngine(registry, store)

    valid_snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=valid_snapshot.nodes, edges=valid_snapshot.edges)
    )
    engine.commit("candidate-valid", candidate, report)

    invalid_snapshot = parse_graph_xml(graphs_dir / "minimal-invalid-contract.xml")
    invalid_candidate, invalid_report = engine.stage(
        PendingConnectionSet(nodes=invalid_snapshot.nodes, edges=invalid_snapshot.edges)
    )
    version = engine.commit("candidate-invalid", invalid_candidate, invalid_report)

    assert invalid_report.valid is False
    assert store.state.active_graph_version == 1
    assert version == 1


def test_cycle_graph_is_rejected(manifest_dir: Path, graphs_dir: Path) -> None:
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "minimal-cycle.xml")

    _, report = engine.stage(PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges))

    assert report.valid is False
    assert any(issue.code == "cycle_detected" for issue in report.issues)


def test_protected_slot_override_is_rejected(manifest_dir: Path, graphs_dir: Path) -> None:
    registry = _build_registry(manifest_dir)
    manifest = load_manifest(manifest_dir / "policy.json")
    _, api = declare_component("policy.secondary", manifest)
    registry.register("policy.secondary", manifest, api.snapshot())

    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "minimal-protected-slot-override.xml")

    _, report = engine.stage(PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges))

    assert report.valid is False
    assert any(issue.code == "protected_slot_override" for issue in report.issues)


def test_protected_component_rewire_is_rejected(manifest_dir: Path) -> None:
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())

    active_nodes = [
        ComponentNode(
            component_id="gateway.primary",
            component_type="Gateway",
            implementation="metaharness.components.gateway",
            version="0.1.0",
        ),
        ComponentNode(
            component_id="policy.primary",
            component_type="Policy",
            implementation="metaharness.components.policy",
            version="0.1.0",
            protected=True,
        ),
    ]
    active_candidate, active_report = engine.stage(
        PendingConnectionSet(nodes=active_nodes, edges=[])
    )
    engine.commit("active", active_candidate, active_report)

    rewired_edges = [
        ConnectionEdge(
            connection_id="policy-feed",
            source="gateway.primary.task",
            target="policy.primary.decision",
            payload="TaskRequest",
            mode=RouteMode.SYNC,
        ),
    ]

    _, report = engine.stage(PendingConnectionSet(nodes=active_nodes, edges=rewired_edges))

    assert report.valid is False
    assert any(issue.code == "protected_boundary_violation" for issue in report.issues)


def test_protected_component_removal_is_rejected(manifest_dir: Path) -> None:
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())

    active_nodes = [
        ComponentNode(
            component_id="gateway.primary",
            component_type="Gateway",
            implementation="metaharness.components.gateway",
            version="0.1.0",
        ),
        ComponentNode(
            component_id="policy.primary",
            component_type="Policy",
            implementation="metaharness.components.policy",
            version="0.1.0",
            protected=True,
        ),
    ]
    active_candidate, active_report = engine.stage(
        PendingConnectionSet(nodes=active_nodes, edges=[])
    )
    engine.commit("active-protected", active_candidate, active_report)

    candidate_nodes = [
        ComponentNode(
            component_id="gateway.primary",
            component_type="Gateway",
            implementation="metaharness.components.gateway",
            version="0.1.0",
        )
    ]

    _, report = engine.stage(PendingConnectionSet(nodes=candidate_nodes, edges=[]))

    assert report.valid is False
    assert any(issue.code == "protected_component_removed" for issue in report.issues)
