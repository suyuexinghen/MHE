"""Level 3 policy veto gate.

Wraps a :class:`GovernanceReviewer` (typically supplied by the Policy
component) and lifts its decision into the safety-pipeline vocabulary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from metaharness.core.models import GraphSnapshot, PendingConnectionSet, ValidationReport
from metaharness.core.validators import validate_graph
from metaharness.safety.gates import GateDecision, GateResult

if TYPE_CHECKING:  # pragma: no cover
    from metaharness.core.mutation import GovernanceReviewer, MutationProposal
    from metaharness.sdk.registry import ComponentRegistry


class PolicyVetoGate:
    """Level 3 safety gate backed by a governance reviewer.

    The reviewer is always given a fresh validation report computed
    against the supplied registry so its decisions remain independent of
    upstream gates.
    """

    name: str = "level_3_policy_veto"

    def __init__(self, reviewer: GovernanceReviewer, registry: ComponentRegistry) -> None:
        self._reviewer = reviewer
        self._registry = registry

    def evaluate(
        self, proposal: MutationProposal, context: dict[str, Any] | None = None
    ) -> GateResult:
        pending = proposal.pending
        assert isinstance(pending, PendingConnectionSet)
        snapshot = GraphSnapshot(graph_version=0, nodes=pending.nodes, edges=pending.edges)
        report: ValidationReport = validate_graph(snapshot, self._registry)
        decision = self._reviewer(proposal, report)
        if decision.decision == "allow":
            return GateResult(
                gate=self.name,
                decision=GateDecision.ALLOW,
                evidence={"decision_id": decision.proposal_id},
            )
        if decision.decision == "defer":
            return GateResult(
                gate=self.name,
                decision=GateDecision.DEFER,
                reason=decision.reason or "policy_deferred",
                evidence={"decision_id": decision.proposal_id},
            )
        return GateResult(
            gate=self.name,
            decision=GateDecision.REJECT,
            reason=decision.reason or "policy_veto",
            evidence={"decision_id": decision.proposal_id},
        )
