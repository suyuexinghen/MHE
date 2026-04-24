"""Triple convergence criteria, dead-end detection, non-Markovian guard."""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

from metaharness.core.models import BudgetState, ConvergenceState, ScoredEvidence


class ConvergenceCriterion(str, Enum):
    """Three convergence criteria mandated by the roadmap."""

    FITNESS_PLATEAU = "fitness_plateau"
    BUDGET_EXHAUSTED = "budget_exhausted"
    SAFETY_FLOOR_MET = "safety_floor_met"


@dataclass(slots=True)
class ConvergenceResult:
    """Outcome of a convergence evaluation."""

    converged: bool
    criteria_met: list[ConvergenceCriterion] = field(default_factory=list)
    reason: str = ""

    def to_state(self) -> ConvergenceState:
        """Convert the dataclass result into the shared core state model."""

        return ConvergenceState(
            converged=self.converged,
            criteria_met=[criterion.value for criterion in self.criteria_met],
            reason=self.reason,
        )


@dataclass(slots=True)
class TripleConvergence:
    """Evaluates all three convergence criteria together.

    The search is declared converged when *any* criterion is satisfied.
    Callers that want stricter behaviour (require all three) can pass
    ``require_all=True``.
    """

    fitness_window: int = 5
    fitness_epsilon: float = 1e-3
    budget_limit: int = 1000
    safety_floor: float = 0.95
    require_all: bool = False

    def evaluate(
        self,
        *,
        fitness_history: Sequence[float],
        budget_used: int,
        safety_score: float,
    ) -> ConvergenceResult:
        met: list[ConvergenceCriterion] = []

        if len(fitness_history) >= self.fitness_window:
            tail = list(fitness_history[-self.fitness_window :])
            if statistics.pstdev(tail) <= self.fitness_epsilon:
                met.append(ConvergenceCriterion.FITNESS_PLATEAU)

        if budget_used >= self.budget_limit:
            met.append(ConvergenceCriterion.BUDGET_EXHAUSTED)

        if safety_score >= self.safety_floor:
            met.append(ConvergenceCriterion.SAFETY_FLOOR_MET)

        if self.require_all:
            converged = len(met) == 3
        else:
            converged = bool(met)

        reason = ", ".join(c.value for c in met) or "no criterion satisfied"
        return ConvergenceResult(converged=converged, criteria_met=met, reason=reason)


def convergence_to_scored_evidence(
    result: ConvergenceResult,
    *,
    fitness_history: Sequence[float],
    budget_used: int,
    budget_limit: int | None,
    safety_score: float,
    evidence_refs: list[str] | None = None,
) -> ScoredEvidence:
    """Project convergence state into the shared scored evidence protocol."""

    remaining = None if budget_limit is None else max(budget_limit - budget_used, 0)
    budget = BudgetState(
        used=budget_used,
        limit=budget_limit,
        remaining=remaining,
        exhausted=budget_limit is not None and budget_used >= budget_limit,
    )
    last_fitness = fitness_history[-1] if fitness_history else 0.0
    metrics = {"fitness": last_fitness, "safety": safety_score, "budget_used": float(budget_used)}
    if fitness_history:
        metrics["fitness_history_length"] = float(len(fitness_history))
    return ScoredEvidence(
        score=last_fitness,
        metrics=metrics,
        safety_score=safety_score,
        budget=budget,
        convergence=result.to_state(),
        evidence_refs=list(evidence_refs or ()),
    )


@dataclass(slots=True)
class DeadEndDetector:
    """Detects search paths that have stopped producing improvements.

    A path is marked dead when fitness has not improved by at least
    ``improvement_epsilon`` across ``window`` consecutive evaluations.
    The detector keeps per-path history so multiple search branches can
    be tracked in parallel.
    """

    window: int = 8
    improvement_epsilon: float = 1e-3
    _history: dict[str, list[float]] = field(default_factory=dict)

    def record(self, path_id: str, score: float) -> None:
        self._history.setdefault(path_id, []).append(score)

    def is_dead_end(self, path_id: str) -> bool:
        history = self._history.get(path_id, [])
        if len(history) < self.window:
            return False
        tail = history[-self.window :]
        return (max(tail) - min(tail)) < self.improvement_epsilon

    def reset(self, path_id: str | None = None) -> None:
        if path_id is None:
            self._history.clear()
        else:
            self._history.pop(path_id, None)


@dataclass(slots=True)
class NonMarkovianGuard:
    """Tracks enough history to remind callers the state is non-Markovian.

    The roadmap notes that candidate graph evolution is not Markovian:
    the best next move depends on multiple past decisions. This guard
    exposes a recent window of state snapshots and a flag telling the
    caller how many steps of history they're expected to feed into
    decisions.
    """

    history_window: int = 16
    _snapshots: list[object] = field(default_factory=list)

    def record(self, state_snapshot: object) -> None:
        self._snapshots.append(state_snapshot)
        if len(self._snapshots) > self.history_window:
            excess = len(self._snapshots) - self.history_window
            del self._snapshots[:excess]

    def window(self) -> list[object]:
        return list(self._snapshots)

    @property
    def required_lookback(self) -> int:
        return min(self.history_window, len(self._snapshots))
