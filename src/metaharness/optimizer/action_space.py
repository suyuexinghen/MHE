"""Four-layer action space funnel.

The roadmap defines a four-layer pipeline that shrinks the raw space
of possible mutations down to a small ranked list of legal, contract-
compatible, budget-feasible candidates. This module provides the
funnel as composable layers so the optimizer can plug in custom filters
at any layer without forking the whole machinery.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionLayer(str, Enum):
    """The four funnel layers."""

    GENERATE = "generate"  # layer 1: produce raw candidates
    FILTER = "filter"  # layer 2: remove structurally illegal ones
    CONTRACT = "contract"  # layer 3: contract-compatibility pruning
    BUDGET = "budget"  # layer 4: cost / risk / budget constraints


@dataclass(slots=True)
class CandidateAction:
    """Opaque action wrapper carried through the funnel."""

    action_id: str
    kind: str
    payload: Any
    score: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)


Generator = Callable[[Any], list[CandidateAction]]
Filterer = Callable[[CandidateAction, Any], bool]
Scorer = Callable[[CandidateAction, Any], float]


@dataclass(slots=True)
class ActionSpaceFunnel:
    """Runs the four-layer funnel in order.

    The funnel is constructor-configurable so callers can compose
    generators and filters at run time. ``generate`` produces raw
    candidates; ``structural_filter`` removes malformed ones;
    ``contract_filter`` applies contract-driven pruning (typically
    wrapping the :class:`ContractPruner`); ``budget_filter`` and
    ``scorer`` carry the final cost / ranking pass.
    """

    generators: list[Generator] = field(default_factory=list)
    structural_filters: list[Filterer] = field(default_factory=list)
    contract_filters: list[Filterer] = field(default_factory=list)
    budget_filters: list[Filterer] = field(default_factory=list)
    scorer: Scorer | None = None

    # ------------------------------------------------------------ pipeline

    def add_generator(self, generator: Generator) -> None:
        self.generators.append(generator)

    def add_structural_filter(self, filterer: Filterer) -> None:
        self.structural_filters.append(filterer)

    def add_contract_filter(self, filterer: Filterer) -> None:
        self.contract_filters.append(filterer)

    def add_budget_filter(self, filterer: Filterer) -> None:
        self.budget_filters.append(filterer)

    # ------------------------------------------------------------ execution

    def run(self, context: Any) -> list[CandidateAction]:
        candidates: list[CandidateAction] = []
        for generator in self.generators:
            candidates.extend(generator(context))

        candidates = self._apply_filters(candidates, self.structural_filters, context)
        candidates = self._apply_filters(candidates, self.contract_filters, context)
        candidates = self._apply_filters(candidates, self.budget_filters, context)

        if self.scorer is not None:
            for candidate in candidates:
                candidate.score = self.scorer(candidate, context)
            candidates.sort(key=lambda c: c.score, reverse=True)

        return candidates

    @staticmethod
    def _apply_filters(
        candidates: Iterable[CandidateAction],
        filters: list[Filterer],
        context: Any,
    ) -> list[CandidateAction]:
        out = list(candidates)
        for filterer in filters:
            out = [c for c in out if filterer(c, context)]
        return out
