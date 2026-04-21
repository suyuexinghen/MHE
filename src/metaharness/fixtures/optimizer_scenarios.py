"""Evaluation scenarios for the optimizer loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class OptimizerScenario:
    """Scenario description for an optimizer evaluation run."""

    scenario_id: str
    description: str
    actions: list[Any] = field(default_factory=list)
    rewards: dict[Any, float] = field(default_factory=dict)
    budget: int = 32
    expected_best: Any | None = None


def all_optimizer_scenarios() -> list[OptimizerScenario]:
    """Canonical set of optimizer scenarios bundled with the tree."""

    return [
        OptimizerScenario(
            scenario_id="OPT-single-peak",
            description="Bayesian optimizer must find the single high-reward arm.",
            actions=["lo", "mid", "hi"],
            rewards={"lo": 0.1, "mid": 0.3, "hi": 0.9},
            expected_best="hi",
        ),
        OptimizerScenario(
            scenario_id="OPT-flat",
            description="All arms produce identical reward - any arm is acceptable.",
            actions=["a", "b", "c"],
            rewards={"a": 0.5, "b": 0.5, "c": 0.5},
            expected_best=None,
        ),
        OptimizerScenario(
            scenario_id="OPT-tight-budget",
            description="Budget is tight; optimizer must still surface the peak.",
            actions=["a", "b", "c", "d"],
            rewards={"a": 0.1, "b": 0.2, "c": 0.3, "d": 0.99},
            budget=8,
            expected_best="d",
        ),
    ]
