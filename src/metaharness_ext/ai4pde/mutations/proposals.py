from __future__ import annotations

from metaharness.core.models import MutationType, PendingConnectionSet, PendingMutation
from metaharness.core.mutation import MutationProposal
from metaharness_ext.ai4pde.mutations.triggers import MutationSignal


def build_proposal(
    *,
    proposal_id: str,
    description: str,
    mutation_type: MutationType,
    target: str,
    justification: str,
) -> MutationProposal:
    pending = PendingConnectionSet(
        mutations=[
            PendingMutation(
                mutation_id=proposal_id,
                description=description,
                type=mutation_type,
                target=target,
                justification=justification,
            )
        ]
    )
    return MutationProposal(
        proposal_id=proposal_id,
        description=description,
        pending=pending,
        proposer_id="ai4pde-mutation-builder",
    )


def build_proposals_from_signals(signals: list[MutationSignal]) -> list[MutationProposal]:
    proposals: list[MutationProposal] = []
    for index, signal in enumerate(signals, start=1):
        if signal.signal == "cost_too_high":
            proposals.append(
                build_proposal(
                    proposal_id=f"ai4pde-cost-{index}",
                    description="Tune solver parameters to reduce compute cost",
                    mutation_type=MutationType.PARAM,
                    target="solver_executor.primary",
                    justification=signal.reason,
                )
            )
        elif signal.signal == "baseline_divergence_widening":
            proposals.append(
                build_proposal(
                    proposal_id=f"ai4pde-template-{index}",
                    description="Substitute a more conservative template",
                    mutation_type=MutationType.TEMPLATE,
                    target="method_router.primary",
                    justification=signal.reason,
                )
            )
        elif signal.signal == "benchmark_plateau":
            proposals.append(
                build_proposal(
                    proposal_id=f"ai4pde-graph-{index}",
                    description="Propose graph rewiring for plateau mitigation",
                    mutation_type=MutationType.CONNECTION,
                    target="physics_validator.primary",
                    justification=signal.reason,
                )
            )
        else:
            proposals.append(
                build_proposal(
                    proposal_id=f"ai4pde-param-{index}",
                    description="Adjust parameters or validator profile",
                    mutation_type=MutationType.PARAM,
                    target="solver_executor.primary",
                    justification=signal.reason,
                )
            )
    return proposals
