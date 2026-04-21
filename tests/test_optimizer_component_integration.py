"""Tests for OptimizerComponent's integration with self-growth modules."""

from __future__ import annotations

from metaharness.components.optimizer import OptimizerComponent
from metaharness.optimizer.triggers import (
    Trigger,
    TriggerKind,
    TriggerThreshold,
)


def test_optimizer_component_uses_trigger_system() -> None:
    optimizer = OptimizerComponent()
    optimizer.triggers.register(
        Trigger(
            trigger_id="latency-high",
            kind=TriggerKind.METRIC,
            metric_name="latency",
            threshold=TriggerThreshold(min_value=100.0),
        )
    )
    events = optimizer.tick({"metrics": {"latency": 120.0}, "now": 0.0})
    assert len(events) == 1
    assert optimizer.last_triggers == events


def test_optimizer_component_records_fitness_and_convergence() -> None:
    optimizer = OptimizerComponent()
    optimizer.convergence.fitness_window = 3
    optimizer.convergence.fitness_epsilon = 1e-6
    optimizer.dead_end.window = 3
    for _ in range(3):
        optimizer.record_fitness(1.0)
    result = optimizer.check_convergence(budget_used=0, safety_score=0.0)
    assert result.converged
    assert optimizer.last_convergence is result
    # Dead-end detector tracked the same path.
    assert optimizer.dead_end.is_dead_end("default")


def test_optimizer_component_negative_reward_updates() -> None:
    optimizer = OptimizerComponent()
    optimizer.negative_reward.threshold = 0.0
    optimizer.record_fitness(-1.0)
    assert optimizer.negative_reward.penalty_for("default") > 0
