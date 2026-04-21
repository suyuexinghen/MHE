"""Tests for the optimizer -> governance -> commit mutation flow."""

from __future__ import annotations

from pathlib import Path

from metaharness.components.optimizer import OptimizerComponent
from metaharness.components.policy import PolicyComponent
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.core.mutation import MutationSubmitter
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _registry_for(manifest_dir: Path, names: list[str]) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in names:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_valid_proposal_commits_through_governance(manifest_dir: Path, graphs_dir: Path) -> None:
    names = ["gateway", "runtime", "executor", "evaluation"]
    registry = _registry_for(manifest_dir, names)
    engine = ConnectionEngine(registry, GraphVersionStore())
    policy = PolicyComponent()
    submitter = MutationSubmitter(engine=engine, reviewer=policy.review_proposal)
    optimizer = OptimizerComponent()

    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    pending = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)

    proposal = optimizer.propose("install happy path", pending=pending)
    record = submitter.submit(proposal)

    assert record.decision.decision == "allow"
    assert record.graph_version == 1
    assert policy.proposal_reviews[-1].decision == "allow"


def test_invalid_proposal_rejected_without_commit(manifest_dir: Path, graphs_dir: Path) -> None:
    names = ["gateway", "runtime"]
    registry = _registry_for(manifest_dir, names)
    engine = ConnectionEngine(registry, GraphVersionStore())
    policy = PolicyComponent()
    submitter = MutationSubmitter(engine=engine, reviewer=policy.review_proposal)
    optimizer = OptimizerComponent()

    snapshot = parse_graph_xml(graphs_dir / "minimal-invalid-contract.xml")
    pending = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    proposal = optimizer.propose("install invalid graph", pending=pending)
    record = submitter.submit(proposal)

    assert record.decision.decision == "reject"
    assert record.graph_version is None
    assert engine._version_store.state.active_graph_version is None  # type: ignore[attr-defined]
    assert any(c.promoted is False for c in engine._version_store.candidates)  # type: ignore[attr-defined]
