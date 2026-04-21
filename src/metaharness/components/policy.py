"""Minimal policy component."""

from __future__ import annotations

from metaharness.core.models import ValidationReport
from metaharness.core.mutation import MutationDecision, MutationProposal
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class PolicyComponent(HarnessComponent):
    """Records simple policy decisions for candidate commits and proposals."""

    protected = True

    def __init__(self) -> None:
        self.decisions: list[dict[str, str]] = []
        self.proposal_reviews: list[MutationDecision] = []

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("policy.primary")
        api.declare_event("decision", "PolicyDecision")

    def record(
        self,
        decision: str,
        subject: str,
        *,
        attestation_id: str | None = None,
    ) -> dict[str, str]:
        payload = {"decision": decision, "subject": subject}
        boundary = getattr(getattr(self, "_runtime", None), "identity_boundary", None)
        if attestation_id is not None:
            payload["attestation_id"] = attestation_id
            credential_bound = boundary is not None and boundary.credentials_for(attestation_id) is not None
            payload["credential_bound"] = "true" if credential_bound else "false"
        self.decisions.append(payload)
        return payload

    def review_proposal(
        self, proposal: MutationProposal, report: ValidationReport
    ) -> MutationDecision:
        """Governance hook: allow/reject a proposal based on its report."""

        if report.valid:
            decision = MutationDecision(
                proposal_id=proposal.proposal_id, decision="allow", report=report
            )
        else:
            reasons = "; ".join(issue.code for issue in report.issues) or "validation_failed"
            decision = MutationDecision(
                proposal_id=proposal.proposal_id,
                decision="reject",
                reason=reasons,
                report=report,
            )
        self.proposal_reviews.append(decision)
        self.record(decision.decision, proposal.proposal_id)
        return decision
