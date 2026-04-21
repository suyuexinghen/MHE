"""Phase C: constrained synthesis.

Synthesises new component / connection proposals from templates and a
hard constraint set. Unlike Phase B (which explores the immediate
neighborhood) Phase C composes multi-step plans while respecting
user-supplied invariants such as "policy.primary must always remain
protected" or "observability.primary cannot be removed".
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from metaharness.core.models import PendingConnectionSet

Constraint = Callable[[PendingConnectionSet], bool]
Plan = list[dict[str, Any]]


@dataclass(slots=True)
class SynthesisResult:
    """Outcome of a constrained-synthesis run."""

    proposal: PendingConnectionSet
    plan: Plan
    score: float
    violations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ConstrainedSynthesis:
    """Greedy plan search with hard constraints.

    ``planner`` produces a sequence of mutations (each a dict the caller
    understands); ``applier`` turns the plan into a concrete pending
    set; ``constraints`` veto any plan that violates an invariant.
    Callers typically compose this with a fitness evaluator to rank
    surviving plans.
    """

    planner: Callable[[PendingConnectionSet], list[Plan]]
    applier: Callable[[PendingConnectionSet, Plan], PendingConnectionSet]
    constraints: list[Constraint] = field(default_factory=list)
    scorer: Callable[[PendingConnectionSet], float] | None = None
    history: list[SynthesisResult] = field(default_factory=list)

    def add_constraint(self, constraint: Constraint) -> None:
        self.constraints.append(constraint)

    def run(self, baseline: PendingConnectionSet) -> list[SynthesisResult]:
        results: list[SynthesisResult] = []
        plans = self.planner(baseline)
        for plan in plans:
            candidate = self.applier(baseline, plan)
            violations = [
                f"constraint_{i}"
                for i, constraint in enumerate(self.constraints)
                if not constraint(candidate)
            ]
            score = 0.0 if self.scorer is None else self.scorer(candidate)
            result = SynthesisResult(
                proposal=candidate, plan=plan, score=score, violations=violations
            )
            if not violations:
                self.history.append(result)
                results.append(result)
        results.sort(key=lambda r: r.score, reverse=True)
        return results
