"""Mutation proposal and governance-mediated commit flow."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from metaharness.core.models import PendingConnectionSet, ValidationReport

if TYPE_CHECKING:  # pragma: no cover - typing only
    from metaharness.core.connection_engine import ConnectionEngine


class MutationProposal(BaseModel):
    """A candidate mutation to a graph emitted by optimizer or operator."""

    proposal_id: str
    description: str
    pending: PendingConnectionSet
    proposer_id: str = "optimizer"
    domain_payload: dict[str, Any] | None = None


class MutationDecision(BaseModel):
    """Governance decision against a mutation proposal or graph promotion."""

    proposal_id: str
    decision: str  # "allow" | "defer" | "reject"
    reason: str = ""
    report: ValidationReport | None = None


class MutationRecord(BaseModel):
    """Audit record for a proposal lifecycle."""

    proposal: MutationProposal
    decision: MutationDecision
    graph_version: int | None = None


GovernanceReviewer = Callable[[MutationProposal, ValidationReport], MutationDecision]


def default_reviewer(proposal: MutationProposal, report: ValidationReport) -> MutationDecision:
    """Default reviewer: accept iff the validation report is valid."""

    if report.valid:
        return MutationDecision(proposal_id=proposal.proposal_id, decision="allow", report=report)
    reasons = "; ".join(issue.code for issue in report.issues) or "validation_failed"
    return MutationDecision(
        proposal_id=proposal.proposal_id, decision="reject", reason=reasons, report=report
    )


class MutationSubmitter(BaseModel):
    """Submitter mediating optimizer proposals through governance to commit."""

    model_config = {"arbitrary_types_allowed": True}

    engine: object
    reviewer: GovernanceReviewer = Field(default=default_reviewer)
    history: list[MutationRecord] = Field(default_factory=list)

    def submit(self, proposal: MutationProposal) -> MutationRecord:
        """Validate, review, and atomically commit or reject a proposal."""

        engine: ConnectionEngine = self.engine  # type: ignore[assignment]
        candidate, report = engine.stage(proposal.pending)
        decision = self.reviewer(proposal, report)
        graph_version: int | None = None
        if decision.decision == "allow":
            graph_version = engine.commit(proposal.proposal_id, candidate, report)
        else:
            engine.discard_candidate(proposal.proposal_id, candidate, report)
        record = MutationRecord(proposal=proposal, decision=decision, graph_version=graph_version)
        self.history.append(record)
        return record
