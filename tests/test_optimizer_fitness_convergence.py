"""Tests for fitness, convergence, dead-end, and non-Markovian guard."""

from __future__ import annotations

from metaharness.optimizer.convergence import (
    ConvergenceCriterion,
    DeadEndDetector,
    NonMarkovianGuard,
    TripleConvergence,
)
from metaharness.optimizer.fitness import (
    FitnessEvaluator,
    NegativeRewardLoop,
    RewardComponents,
    composite_fitness,
)


def test_composite_fitness_weighted_sum() -> None:
    components = RewardComponents(success=1.0, efficiency=0.5, safety=1.0, penalties=0.2)
    assert composite_fitness(
        components, weights={"success": 1.0, "safety": 0.5, "penalty": 1.0}
    ) == (1.0 + 0.5 - 0.2)


def test_fitness_evaluator_registers_and_dispatches() -> None:
    evaluator = FitnessEvaluator()

    def score_proposal(proposal: dict[str, float]) -> RewardComponents:
        return RewardComponents(success=proposal["score"])

    evaluator.register("proposal", score_proposal)
    components, fitness = evaluator.score("proposal", {"score": 0.8})
    assert components.success == 0.8
    assert fitness > 0
    assert evaluator.last_score_of("proposal") == fitness


def test_negative_reward_loop_accumulates_and_decays() -> None:
    loop = NegativeRewardLoop(decay=0.5, threshold=0.0)
    loop.observe("runtime", -1.0)
    loop.observe("runtime", -0.5)
    assert loop.penalty_for("runtime") > 0
    # Positive observations still decay prior penalty.
    loop.observe("runtime", 1.0)
    assert loop.penalty_for("runtime") < 1.5


def test_triple_convergence_fires_on_plateau() -> None:
    criteria = TripleConvergence(
        fitness_window=3, fitness_epsilon=1e-6, budget_limit=999, safety_floor=2.0
    )
    result = criteria.evaluate(
        fitness_history=[1.0, 1.0, 1.0],
        budget_used=0,
        safety_score=0.0,
    )
    assert result.converged
    assert ConvergenceCriterion.FITNESS_PLATEAU in result.criteria_met


def test_triple_convergence_fires_on_budget_or_safety() -> None:
    criteria = TripleConvergence(
        fitness_window=10, fitness_epsilon=1e-6, budget_limit=3, safety_floor=0.99
    )
    result = criteria.evaluate(
        fitness_history=[0.0],
        budget_used=3,
        safety_score=0.0,
    )
    assert ConvergenceCriterion.BUDGET_EXHAUSTED in result.criteria_met

    result = criteria.evaluate(
        fitness_history=[0.0],
        budget_used=0,
        safety_score=0.99,
    )
    assert ConvergenceCriterion.SAFETY_FLOOR_MET in result.criteria_met


def test_triple_convergence_require_all_is_conservative() -> None:
    criteria = TripleConvergence(
        fitness_window=2,
        fitness_epsilon=1e-6,
        budget_limit=3,
        safety_floor=0.99,
        require_all=True,
    )
    all_three = criteria.evaluate(
        fitness_history=[0.1, 0.1, 0.1],
        budget_used=10,
        safety_score=1.0,
    )
    assert all_three.converged


def test_dead_end_detector_tracks_per_path() -> None:
    detector = DeadEndDetector(window=3, improvement_epsilon=0.001)
    for score in [0.5, 0.5001, 0.4999]:
        detector.record("path-a", score)
    assert detector.is_dead_end("path-a")
    detector.record("path-b", 0.1)
    assert not detector.is_dead_end("path-b")


def test_non_markovian_guard_bounds_window() -> None:
    guard = NonMarkovianGuard(history_window=3)
    for i in range(5):
        guard.record({"step": i})
    assert len(guard.window()) == 3
    assert guard.required_lookback == 3
