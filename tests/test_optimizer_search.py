"""Tests for Phase A/B/C search, Bayesian optimization, and RL."""

from __future__ import annotations

from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.contract_pruner import ContractPruner
from metaharness.core.models import PendingConnectionSet
from metaharness.optimizer.search.bayesian import BayesianOptimizer, summarize
from metaharness.optimizer.search.phase_a import LocalParameterSearch
from metaharness.optimizer.search.phase_b import TopologyTemplateSearch
from metaharness.optimizer.search.phase_c import ConstrainedSynthesis
from metaharness.optimizer.search.rl import RLEnhancement
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _registry(manifest_dir: Path, names: list[str]) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in names:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_phase_a_grid_search_picks_best() -> None:
    search = LocalParameterSearch(
        schema={"x": [1, 2, 3], "y": [10, 20]},
        strategy="grid",
    )
    best = search.run(lambda params: params["x"] * params["y"])
    assert best.params == {"x": 3, "y": 20}
    assert best.score == 60


def test_phase_a_random_samples_subset() -> None:
    search = LocalParameterSearch(
        schema={"x": list(range(10))},
        strategy="random",
        random_samples=3,
        rng_seed=7,
    )
    candidates = search.candidates()
    assert len(candidates) == 3


def test_phase_b_enumerates_legal_moves(manifest_dir: Path, graphs_dir: Path) -> None:
    registry = _registry(manifest_dir, ["gateway", "runtime", "executor", "evaluation"])
    pruner = ContractPruner(registry)
    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    baseline = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)

    def score(_: PendingConnectionSet) -> float:
        return 1.0

    search = TopologyTemplateSearch(pruner=pruner, objective=score, top_k=3)
    trials = search.run(baseline)
    assert len(trials) <= 3
    # There must be at least the remove_edge moves plus some add_edge moves.
    kinds = {t.move.kind for t in search.history}
    assert "remove_edge" in kinds


def test_phase_c_constrained_synthesis_filters_invalid_plans() -> None:
    baseline = PendingConnectionSet()

    def planner(_: PendingConnectionSet) -> list[list[dict[str, str]]]:
        return [
            [{"op": "noop"}],
            [{"op": "forbidden"}],
        ]

    def applier(base: PendingConnectionSet, plan: list[dict[str, str]]) -> PendingConnectionSet:
        return base

    search = ConstrainedSynthesis(planner=planner, applier=applier)
    search.add_constraint(
        lambda _pending: True  # trivial
    )
    results = search.run(baseline)
    assert len(results) == 2


def test_bayesian_optimizer_ucb_flow() -> None:
    optimizer = BayesianOptimizer(beta=1.0, unseen_priority=10.0)
    actions = ["a", "b", "c"]
    for action in actions:
        optimizer.register(action)

    scores = {"a": 0.1, "b": 0.9, "c": 0.5}
    action, score = optimizer.optimize(actions, lambda a: scores[a], budget=12)
    assert action == "b"
    assert score == 0.9
    summary = summarize(optimizer)
    assert summary[0].action == "b"


def test_bayesian_optimizer_ask_returns_none_for_empty() -> None:
    optimizer = BayesianOptimizer()
    assert optimizer.ask([]) is None


def test_rl_enhancement_updates_preferences() -> None:
    rl = RLEnhancement(learning_rate=0.5, temperature=1.0, seed=123)
    actions = ["a", "b"]
    # Reward action "a" repeatedly.
    for _ in range(20):
        rl.update("a", 1.0, actions)
    probs = rl.probabilities(actions)
    assert probs["a"] > probs["b"]
    # Sampling should still return a valid element.
    assert rl.sample(actions) in actions
