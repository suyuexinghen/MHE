"""Reward / fitness functions and the negative-reward feedback loop."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from metaharness.core.models import ScoredEvidence


@dataclass(slots=True)
class RewardComponents:
    """Decomposed reward signals consumed by :func:`composite_fitness`.

    The roadmap calls out multi-signal reward aggregation: a candidate's
    score is the weighted sum of task-level success, cost/latency
    efficiency, safety compliance, and a novelty bonus. Each component
    is kept separate so observers can see *why* a score is high/low.
    """

    success: float = 0.0
    efficiency: float = 0.0
    safety: float = 0.0
    novelty: float = 0.0
    penalties: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)


def composite_fitness(
    components: RewardComponents,
    *,
    weights: dict[str, float] | None = None,
) -> float:
    """Combine ``RewardComponents`` into a single scalar fitness."""

    w = weights or {
        "success": 1.0,
        "efficiency": 0.5,
        "safety": 1.0,
        "novelty": 0.2,
        "penalty": 1.0,
    }
    return (
        w.get("success", 1.0) * components.success
        + w.get("efficiency", 0.0) * components.efficiency
        + w.get("safety", 0.0) * components.safety
        + w.get("novelty", 0.0) * components.novelty
        - w.get("penalty", 1.0) * components.penalties
    )


def reward_components_to_scored_evidence(
    components: RewardComponents,
    *,
    weights: dict[str, float] | None = None,
    evidence_refs: list[str] | None = None,
) -> ScoredEvidence:
    """Convert decomposed reward signals into the shared scored protocol."""

    fitness = composite_fitness(components, weights=weights)
    return ScoredEvidence(
        score=fitness,
        metrics={
            "success": components.success,
            "efficiency": components.efficiency,
            "safety": components.safety,
            "novelty": components.novelty,
            "penalties": components.penalties,
        },
        safety_score=components.safety,
        evidence_refs=list(evidence_refs or ()),
        attributes=dict(components.attributes),
    )


Evaluator = Callable[[Any], RewardComponents]


class FitnessEvaluator:
    """Stateful fitness evaluator.

    Callers register a mapping from ``kind`` -> evaluator function and
    then dispatch proposals or candidate graphs by kind. Results are
    accumulated so downstream components (negative-reward loop, dead-end
    detector) can inspect trends.
    """

    def __init__(self) -> None:
        self._evaluators: dict[str, Evaluator] = {}
        self.history: list[tuple[str, RewardComponents, float]] = []

    def register(self, kind: str, evaluator: Evaluator) -> None:
        self._evaluators[kind] = evaluator

    def has(self, kind: str) -> bool:
        return kind in self._evaluators

    def score(
        self,
        kind: str,
        subject: Any,
        *,
        weights: dict[str, float] | None = None,
    ) -> tuple[RewardComponents, float]:
        if kind not in self._evaluators:
            raise KeyError(f"no evaluator registered for {kind!r}")
        components = self._evaluators[kind](subject)
        fitness = composite_fitness(components, weights=weights)
        self.history.append((kind, components, fitness))
        return components, fitness

    def score_evidence(
        self,
        kind: str,
        subject: Any,
        *,
        weights: dict[str, float] | None = None,
        evidence_refs: list[str] | None = None,
    ) -> ScoredEvidence:
        """Return the shared scored evidence shape while reusing fitness logic."""

        components, _ = self.score(kind, subject, weights=weights)
        return reward_components_to_scored_evidence(
            components,
            weights=weights,
            evidence_refs=evidence_refs,
        )

    def last_score_of(self, kind: str) -> float | None:
        for k, _, score in reversed(self.history):
            if k == kind:
                return score
        return None


@dataclass(slots=True)
class NegativeRewardLoop:
    """Tracks repeated low scores and escalates penalties.

    Every call to :meth:`observe` updates the running penalty scaled by
    how often the same subject (keyed by id) has recently produced a
    negative signal. Downstream fitness can subtract this penalty to
    discourage retries of known-bad paths.
    """

    decay: float = 0.8
    threshold: float = 0.0
    penalties: dict[str, float] = field(default_factory=dict)

    def observe(self, subject_id: str, score: float) -> float:
        current = self.penalties.get(subject_id, 0.0) * self.decay
        if score < self.threshold:
            current += abs(self.threshold - score)
        self.penalties[subject_id] = current
        return current

    def penalty_for(self, subject_id: str) -> float:
        return self.penalties.get(subject_id, 0.0)

    def reset(self, subject_id: str | None = None) -> None:
        if subject_id is None:
            self.penalties.clear()
        else:
            self.penalties.pop(subject_id, None)
