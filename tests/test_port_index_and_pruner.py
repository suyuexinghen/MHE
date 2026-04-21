"""PortIndex, RouteTable, and ContractPruner tests."""

from __future__ import annotations

from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.contract_pruner import ContractPruner
from metaharness.core.port_index import PortIndex, RouteTable
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in ["gateway", "runtime", "executor", "evaluation", "planner", "memory"]:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_port_index_lookup_by_fqid(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    index = PortIndex.from_registry(registry)
    ref = index.lookup("runtime.primary.task")
    assert ref is not None
    assert ref.direction == "input"
    assert ref.payload_type == "TaskRequest"


def test_port_index_enumerates_inputs_and_outputs(manifest_dir: Path) -> None:
    index = PortIndex.from_registry(_registry(manifest_dir))
    assert {p.fqid for p in index.outputs_of("gateway.primary")} == {"gateway.primary.task"}
    inputs = {p.fqid for p in index.inputs_of("runtime.primary")}
    assert "runtime.primary.task" in inputs


def test_route_table_build(manifest_dir: Path, graphs_dir: Path) -> None:
    registry = _registry(manifest_dir)
    index = PortIndex.from_registry(registry)
    snapshot = parse_graph_xml(graphs_dir / "minimal-expanded.xml")
    table = RouteTable.build(snapshot, index)

    routes = table.routes_from("gateway.primary.task")
    assert [r.target.fqid for r in routes] == ["runtime.primary.task"]
    assert table.find("c4") is not None
    assert len(table.all_routes()) == len(snapshot.edges)


def test_contract_pruner_filters_by_payload(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    pruner = ContractPruner(registry)

    targets = pruner.legal_targets("gateway.primary.task")
    # gateway emits TaskRequest; compatible inputs are runtime.task,
    # planner.task, and executor.task. memory/evaluation accept TaskResult.
    fqids = {ref.fqid for ref in targets}
    assert "runtime.primary.task" in fqids
    assert "planner.primary.task" in fqids
    assert "executor.primary.task" in fqids
    assert "memory.primary.task_result" not in fqids


def test_contract_pruner_denied_pairs(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir)
    pruner = ContractPruner(
        registry,
        denied_pairs=[("gateway.primary.task", "planner.primary.task")],
    )
    fqids = {ref.fqid for ref in pruner.legal_targets("gateway.primary.task")}
    assert "planner.primary.task" not in fqids
    assert "runtime.primary.task" in fqids
