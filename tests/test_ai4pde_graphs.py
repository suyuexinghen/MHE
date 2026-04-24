from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry

AI4PDE_COMPONENTS = [
    "pde_gateway",
    "problem_formulator",
    "method_router",
    "solver_executor",
    "reference_solver",
    "physics_validator",
    "evidence_manager",
    "experiment_memory",
    "risk_policy",
    "observability_hub",
    "knowledge_adapter",
]


def _build_registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in AI4PDE_COMPONENTS:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_ai4pde_graph_is_semantically_valid(examples_dir: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "ai4pde"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "ai4pde-minimal.xml")

    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("ai4pde-minimal", candidate, report)

    assert report.valid is True
    assert version == 1


def test_ai4pde_baseline_graph_is_semantically_valid(examples_dir: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "ai4pde"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "ai4pde-baseline.xml")

    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("ai4pde-baseline", candidate, report)

    assert report.valid is True
    assert version == 1


def test_ai4pde_expanded_graph_is_semantically_valid(examples_dir: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "ai4pde"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "ai4pde-expanded.xml")

    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("ai4pde-expanded", candidate, report)

    assert report.valid is True
    assert version == 1
