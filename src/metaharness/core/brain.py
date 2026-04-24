"""Brain provider abstraction for planning and evaluation seams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from metaharness.components.optimizer import (
        EvaluatorFn,
        Observation,
        OptimizerComponent,
        ProposalEvaluation,
        ProposerFn,
    )
    from metaharness.core.mutation import MutationProposal


class BrainProvider(Protocol):
    """Typed planning/evaluation provider for optimizer decisions."""

    def propose(
        self,
        optimizer: OptimizerComponent,
        observations: list[Observation],
    ) -> list[MutationProposal]:
        """Return candidate proposals for the current observation set."""

    def evaluate(
        self,
        optimizer: OptimizerComponent,
        proposal: MutationProposal,
        observations: list[Observation],
    ) -> ProposalEvaluation:
        """Score a proposal against the current observation set."""


@dataclass(slots=True)
class FunctionalBrainProvider:
    """Adapter that wraps proposer/evaluator callables as a brain provider."""

    proposer: ProposerFn
    evaluator: EvaluatorFn

    def propose(
        self,
        optimizer: OptimizerComponent,
        observations: list[Observation],
    ) -> list[MutationProposal]:
        return list(self.proposer(optimizer, observations))

    def evaluate(
        self,
        optimizer: OptimizerComponent,
        proposal: MutationProposal,
        observations: list[Observation],
    ) -> ProposalEvaluation:
        return self.evaluator(optimizer, proposal, observations)
