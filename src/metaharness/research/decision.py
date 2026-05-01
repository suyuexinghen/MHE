from __future__ import annotations

from metaharness.sdk.research import Decision, DecisionOutcome, EvidenceBundle, Hypothesis


def decision_from_evidence(evidence: EvidenceBundle, hypothesis: Hypothesis) -> Decision:
    """Create the MVP metric-threshold decision for one evidence bundle."""

    supported = hypothesis.hypothesis_id in evidence.supports
    outcome = DecisionOutcome.ADVANCE if supported else DecisionOutcome.REFINE
    if supported:
        reasoning = "evidence supports the hypothesis metric threshold"
    elif hypothesis.hypothesis_id in evidence.refutes:
        reasoning = "evidence refutes the hypothesis metric threshold"
    else:
        reasoning = "evidence is inconclusive for the hypothesis"
    return Decision(
        decision_id=f"dec-{evidence.bundle_id}-{hypothesis.hypothesis_id}",
        hypothesis_id=hypothesis.hypothesis_id,
        evidence_bundle_id=evidence.bundle_id,
        decision=outcome,
        reasoning=reasoning,
    )
