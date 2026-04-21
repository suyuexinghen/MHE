"""Tests for the GIN encoder and the four-layer action space funnel."""

from __future__ import annotations

from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.optimizer.action_space import (
    ActionSpaceFunnel,
    CandidateAction,
)
from metaharness.optimizer.encoder import GINEncoder


def test_gin_encoder_is_deterministic(graphs_dir: Path) -> None:
    snapshot = parse_graph_xml(graphs_dir / "minimal-expanded.xml")
    encoder = GINEncoder(dim=8, layers=2)
    a = encoder.encode(snapshot)
    b = encoder.encode(snapshot)
    assert a.graph_vector == b.graph_vector
    assert set(a.nodes) == {n.component_id for n in snapshot.nodes}
    for vec in a.nodes.values():
        assert len(vec.vector) == 8


def test_gin_encoder_distinguishes_topologies(graphs_dir: Path) -> None:
    snap_a = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    snap_b = parse_graph_xml(graphs_dir / "minimal-expanded.xml")
    encoder = GINEncoder(dim=8, layers=2)
    vec_a = encoder.encode(snap_a).graph_vector
    vec_b = encoder.encode(snap_b).graph_vector
    assert vec_a != vec_b


def test_action_funnel_applies_all_layers_in_order() -> None:
    funnel = ActionSpaceFunnel()
    funnel.add_generator(
        lambda ctx: [
            CandidateAction(action_id="a", kind="x", payload=1),
            CandidateAction(action_id="b", kind="x", payload=2),
            CandidateAction(action_id="c", kind="x", payload=3),
        ]
    )
    funnel.add_structural_filter(lambda c, _: c.payload != 1)  # drops "a"
    funnel.add_contract_filter(lambda c, _: c.payload != 3)  # drops "c"
    funnel.add_budget_filter(lambda c, _: True)
    funnel.scorer = lambda c, _: float(c.payload)

    result = funnel.run(context={})
    assert [c.action_id for c in result] == ["b"]
    assert result[0].score == 2.0


def test_action_funnel_sorts_by_score() -> None:
    funnel = ActionSpaceFunnel()
    funnel.add_generator(
        lambda ctx: [
            CandidateAction(action_id="lo", kind="x", payload=1),
            CandidateAction(action_id="hi", kind="x", payload=10),
            CandidateAction(action_id="mid", kind="x", payload=5),
        ]
    )
    funnel.scorer = lambda c, _: float(c.payload)
    result = funnel.run(context={})
    assert [c.action_id for c in result] == ["hi", "mid", "lo"]
