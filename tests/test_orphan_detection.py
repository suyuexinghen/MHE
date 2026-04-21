"""Orphan-component detection tests."""

from __future__ import annotations

from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml_text
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.core.validators import detect_orphans, validate_graph
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _registry(manifest_dir: Path, names: list[str]) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in names:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_unreferenced_component_with_inputs_is_orphan(manifest_dir: Path) -> None:
    xml = """<Harness version='0.1.0' graphVersion='1' schemaVersion='1.1'>
      <Components>
        <Component id='gateway.primary' type='Gateway' impl='metaharness.components.gateway' version='0.1.0'/>
        <Component id='runtime.primary' type='Runtime' impl='metaharness.components.runtime' version='0.1.0'/>
        <Component id='memory.primary' type='Memory' impl='metaharness.components.memory' version='0.1.0'/>
      </Components>
      <Connections>
        <Connection id='c1' from='gateway.primary.task' to='runtime.primary.task' payload='TaskRequest' mode='sync' policy='required'/>
      </Connections>
    </Harness>"""
    snapshot = parse_graph_xml_text(xml)

    registry = _registry(manifest_dir, ["gateway", "runtime", "memory"])
    engine = ConnectionEngine(registry, GraphVersionStore())
    _, report = engine.stage(PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges))
    codes = {(i.code, i.subject) for i in report.issues}
    assert ("orphan_component", "memory.primary") in codes


def test_components_without_inputs_are_not_orphans(manifest_dir: Path, graphs_dir: Path) -> None:
    snapshot = parse_graph_xml_text((graphs_dir / "default-topology.xml").read_text())
    registry = _registry(
        manifest_dir,
        [
            "gateway",
            "runtime",
            "planner",
            "executor",
            "evaluation",
            "memory",
            "toolhub",
            "policy",
            "observability",
        ],
    )
    report = validate_graph(snapshot, registry)
    assert report.valid, report.issues


def test_detect_orphans_helper(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir, ["policy", "observability", "runtime"])
    # Runtime has inputs but no edges target it.
    snapshot = parse_graph_xml_text(
        """<Harness version='0.1.0' graphVersion='1' schemaVersion='1.1'>
          <Components>
            <Component id='runtime.primary' type='Runtime' impl='metaharness.components.runtime' version='0.1.0'/>
            <Component id='policy.primary' type='Policy' impl='metaharness.components.policy' version='0.1.0' protected='true'/>
          </Components>
          <Connections/>
        </Harness>"""
    )
    orphans = detect_orphans(snapshot, registry)
    assert orphans == ["runtime.primary"]
