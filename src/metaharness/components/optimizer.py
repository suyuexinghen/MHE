"""Optimizer skeleton with strict proposal-only authority."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from metaharness.core.brain import BrainProvider, FunctionalBrainProvider
from metaharness.core.models import PendingConnectionSet, ScoredEvidence
from metaharness.core.mutation import MutationProposal, MutationRecord, MutationSubmitter
from metaharness.optimizer.convergence import (
    ConvergenceResult,
    DeadEndDetector,
    TripleConvergence,
    convergence_to_scored_evidence,
)
from metaharness.optimizer.fitness import (
    FitnessEvaluator,
    NegativeRewardLoop,
    RewardComponents,
    reward_components_to_scored_evidence,
)
from metaharness.optimizer.triggers import LayeredTriggerSystem, TriggerEvent


@dataclass(slots=True)
class Observation:
    """An observation the optimizer consumes before proposing mutations."""

    source: str
    value: Any
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class ProposalEvaluation:
    """Result of evaluating a proposal against observations."""

    proposal_id: str
    score: float
    reasons: list[str] = field(default_factory=list)
    evidence: ScoredEvidence | None = None


ProposerFn = Callable[["OptimizerComponent", list[Observation]], list[MutationProposal]]
EvaluatorFn = Callable[
    ["OptimizerComponent", MutationProposal, list[Observation]], ProposalEvaluation
]
DomainPayloadFn = Callable[["OptimizerComponent", list[Observation]], dict[str, Any] | None]


def _default_proposer(_: OptimizerComponent, __: list[Observation]) -> list[MutationProposal]:
    return []


def _default_evaluator(
    _: OptimizerComponent, proposal: MutationProposal, __: list[Observation]
) -> ProposalEvaluation:
    # Treat any non-empty pending set as baseline candidate.
    score = 1.0 if proposal.pending.edges or proposal.pending.nodes else 0.0
    reasons = [] if score > 0 else ["empty_pending_set"]
    components = RewardComponents(success=score, penalties=0.0 if score > 0 else 1.0)
    evidence = reward_components_to_scored_evidence(
        components,
        evidence_refs=[proposal.proposal_id],
    ).model_copy(update={"score": score, "reasons": reasons})
    return ProposalEvaluation(
        proposal_id=proposal.proposal_id,
        score=score,
        reasons=reasons,
        evidence=evidence,
    )


class OptimizerComponent:
    """Proposal-only optimizer with an ``observe/propose/evaluate/commit`` cycle.

    The optimizer has **no** access to the ConnectionEngine, the registry, or
    the version store. ``commit()`` is a thin delegate to a
    :class:`MutationSubmitter` which goes through the governance reviewer.

    Plug-in strategies supply a typed brain provider (or legacy proposer /
    evaluator callables); the defaults keep unit tests deterministic while
    enforcing the invariant that an optimizer can only propose, never write.
    """

    def __init__(
        self,
        *,
        proposer: ProposerFn | None = None,
        evaluator: EvaluatorFn | None = None,
        brain_provider: BrainProvider | None = None,
        triggers: LayeredTriggerSystem | None = None,
        fitness: FitnessEvaluator | None = None,
        convergence: TripleConvergence | None = None,
        dead_end: DeadEndDetector | None = None,
        negative_reward: NegativeRewardLoop | None = None,
        domain_payload_provider: DomainPayloadFn | None = None,
    ) -> None:
        self._counter = 0
        self._observations: list[Observation] = []
        self.brain_provider = brain_provider or FunctionalBrainProvider(
            proposer=proposer or _default_proposer,
            evaluator=evaluator or _default_evaluator,
        )
        self.triggers = triggers or LayeredTriggerSystem()
        self.fitness = fitness or FitnessEvaluator()
        self.convergence = convergence or TripleConvergence()
        self.dead_end = dead_end or DeadEndDetector()
        self.negative_reward = negative_reward or NegativeRewardLoop()
        self.fitness_history: list[float] = []
        self.last_triggers: list[TriggerEvent] = []
        self.last_convergence: ConvergenceResult | None = None
        self._domain_payload_provider = domain_payload_provider

    # ------------------------------------------------------------------ observe

    def observe(self, observation: Observation) -> None:
        """Record an observation that later proposals may reference."""

        self._observations.append(observation)

    def clear_observations(self) -> None:
        self._observations.clear()

    @property
    def observations(self) -> list[Observation]:
        return list(self._observations)

    # ------------------------------------------------------------------ propose

    def propose(
        self,
        description: str,
        pending: PendingConnectionSet | None = None,
        *,
        proposer_id: str = "optimizer",
        domain_payload: dict[str, Any] | None = None,
    ) -> MutationProposal:
        """Emit a single mutation proposal."""

        self._counter += 1
        proposal_id = f"p-{self._counter:04d}"
        if domain_payload is None and self._domain_payload_provider is not None:
            domain_payload = self._domain_payload_provider(self, list(self._observations))
        return MutationProposal(
            proposal_id=proposal_id,
            description=description,
            pending=pending or PendingConnectionSet(),
            proposer_id=proposer_id,
            domain_payload=domain_payload,
        )

    def propose_batch(self) -> list[MutationProposal]:
        """Ask the configured brain provider for proposals based on observations."""

        return self.brain_provider.propose(self, list(self._observations))

    # ------------------------------------------------------------------ evaluate

    def evaluate(self, proposal: MutationProposal) -> ProposalEvaluation:
        """Score a proposal using the configured brain provider."""

        evaluation = self.brain_provider.evaluate(self, proposal, list(self._observations))
        if proposal.domain_payload is None or evaluation.evidence is None:
            return evaluation
        evidence = evaluation.evidence.model_copy(
            update={
                "attributes": {
                    **evaluation.evidence.attributes,
                    "domain_payload": proposal.domain_payload,
                }
            }
        )
        return ProposalEvaluation(
            proposal_id=evaluation.proposal_id,
            score=evaluation.score,
            reasons=evaluation.reasons,
            evidence=evidence,
        )

    # ------------------------------------------------------------------ commit

    def commit(self, proposal: MutationProposal, submitter: MutationSubmitter) -> MutationRecord:
        """Submit a proposal through governance.

        The optimizer never calls the engine or registry directly; the only
        way a proposal reaches the active graph is via ``submitter.submit``.
        """

        return submitter.submit(proposal)

    # -------------------------------------------------------- self-growth API

    def tick(
        self,
        context: dict[str, Any] | None = None,
    ) -> list[TriggerEvent]:
        """Evaluate registered triggers and return fired events.

        Callers typically invoke ``tick`` on a clock or in response to
        bus events. Fired events gate subsequent ``propose_batch`` calls.
        """

        events = self.triggers.evaluate(context)
        self.last_triggers = events
        return events

    def record_fitness(self, score: float, *, path_id: str = "default") -> None:
        """Record a fitness reading so convergence / dead-end updates."""

        self.fitness_history.append(score)
        self.dead_end.record(path_id, score)
        self.negative_reward.observe(path_id, score)

    def check_convergence(self, *, budget_used: int, safety_score: float) -> ConvergenceResult:
        """Evaluate the triple convergence criteria with current history."""

        result = self.convergence.evaluate(
            fitness_history=self.fitness_history,
            budget_used=budget_used,
            safety_score=safety_score,
        )
        self.last_convergence = result
        return result

    def convergence_evidence(self, *, budget_used: int, safety_score: float) -> ScoredEvidence:
        """Return convergence state in the shared scored evidence shape."""

        result = self.check_convergence(budget_used=budget_used, safety_score=safety_score)
        return convergence_to_scored_evidence(
            result,
            fitness_history=self.fitness_history,
            budget_used=budget_used,
            budget_limit=self.convergence.budget_limit,
            safety_score=safety_score,
        )
