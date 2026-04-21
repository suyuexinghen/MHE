"""Lightweight Bayesian optimization over a discrete action set.

We implement a pragmatic UCB-style strategy: track the mean and
variance of each action's score from past trials and pick the action
maximising ``mean + beta * sqrt(variance / count)``. This does not
require adding scipy/scikit-learn; it gives correct exploration /
exploitation trade-off for modest discrete spaces as described by the
roadmap.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field


@dataclass(slots=True)
class _ArmStats:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0  # Welford running variance accumulator.

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

    def variance(self) -> float:
        if self.count < 2:
            return 1.0
        return self.m2 / (self.count - 1)


@dataclass(slots=True)
class BayesianOptimizer:
    """UCB-style surrogate-free Bayesian optimizer.

    Actions are identified by any hashable key. ``tell`` feeds an
    observed score; ``ask`` returns the next action to try, balancing
    mean score against uncertainty.
    """

    beta: float = 1.414
    unseen_priority: float = 1.0
    stats: dict[Hashable, _ArmStats] = field(default_factory=dict)

    def register(self, action: Hashable) -> None:
        self.stats.setdefault(action, _ArmStats())

    def tell(self, action: Hashable, score: float) -> None:
        stats = self.stats.setdefault(action, _ArmStats())
        stats.update(score)

    def ask(self, actions: list[Hashable] | None = None) -> Hashable | None:
        candidates = list(actions) if actions is not None else list(self.stats.keys())
        if not candidates:
            return None

        best_action: Hashable | None = None
        best_score = float("-inf")
        for action in candidates:
            stats = self.stats.setdefault(action, _ArmStats())
            if stats.count == 0:
                score = self.unseen_priority
            else:
                uncertainty = math.sqrt(stats.variance() / stats.count)
                score = stats.mean + self.beta * uncertainty
            if score > best_score:
                best_action = action
                best_score = score
        return best_action

    def optimize(
        self,
        actions: list[Hashable],
        objective: Callable[[Hashable], float],
        *,
        budget: int = 32,
    ) -> tuple[Hashable, float]:
        best: tuple[Hashable, float] | None = None
        for _ in range(budget):
            action = self.ask(actions)
            if action is None:
                break
            score = objective(action)
            self.tell(action, score)
            if best is None or score > best[1]:
                best = (action, score)
        if best is None:
            raise RuntimeError("no actions evaluated")
        return best

    def best_mean(self) -> tuple[Hashable, float] | None:
        ranked: list[tuple[Hashable, float]] = [
            (action, stats.mean) for action, stats in self.stats.items() if stats.count > 0
        ]
        if not ranked:
            return None
        ranked.sort(key=lambda pair: pair[1], reverse=True)
        return ranked[0]


@dataclass(slots=True)
class _ExperimentRecord:
    """Public history view returned from :meth:`BayesianOptimizer.summary`."""

    action: Hashable
    count: int
    mean: float
    variance: float
    confidence: float


def summarize(optimizer: BayesianOptimizer) -> list[_ExperimentRecord]:
    """Summarise every arm's stats for diagnostics."""

    out: list[_ExperimentRecord] = []
    for action, stats in optimizer.stats.items():
        variance = stats.variance()
        confidence = optimizer.beta * math.sqrt(variance / max(stats.count, 1))
        out.append(
            _ExperimentRecord(
                action=action,
                count=stats.count,
                mean=stats.mean,
                variance=variance,
                confidence=confidence,
            )
        )
    out.sort(key=lambda r: r.mean, reverse=True)
    return out


__all__ = ["BayesianOptimizer", "summarize"]
