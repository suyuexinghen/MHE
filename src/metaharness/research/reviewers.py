from __future__ import annotations

from dataclasses import dataclass

from metaharness.sdk.research import DecisionOutcome, EvidenceBundle, EvidenceStatus, Hypothesis
from metaharness.sdk.review import EvidenceReview, ReviewDimensions, ReviewerProtocol


@dataclass(frozen=True)
class MetricThresholdReviewer(ReviewerProtocol):
    """Deterministic MVP reviewer based on evidence support/refute lists."""

    reviewer_id: str = "metric-threshold-reviewer"

    def review(self, hypothesis: Hypothesis, evidence: EvidenceBundle) -> EvidenceReview:
        supported = hypothesis.hypothesis_id in evidence.supports
        refuted = hypothesis.hypothesis_id in evidence.refutes
        recommendation = DecisionOutcome.ADVANCE if supported else DecisionOutcome.REFINE
        dimensions = _dimensions_for(evidence, supported=supported, refuted=refuted)
        if supported:
            reasoning = "evidence supports the hypothesis metric threshold"
        elif refuted:
            reasoning = "evidence refutes the hypothesis metric threshold"
        else:
            reasoning = "evidence is inconclusive for the hypothesis"
        return EvidenceReview(
            review_id=f"review-{evidence.bundle_id}-{hypothesis.hypothesis_id}",
            reviewer_id=self.reviewer_id,
            evidence_bundle_id=evidence.bundle_id,
            hypothesis_id=hypothesis.hypothesis_id,
            dimensions=dimensions,
            recommendation=recommendation,
            reasoning=reasoning,
        )


def _dimensions_for(
    evidence: EvidenceBundle, *, supported: bool, refuted: bool
) -> ReviewDimensions:
    credible = evidence.confidence if evidence.status == EvidenceStatus.PASSED else 0.0
    correctness = credible if supported or refuted else 0.0
    reproducibility = (
        1.0 if evidence.confidence_method == "deterministic_metric_threshold" else credible
    )
    significance = 1.0 if supported else 0.5 if refuted else 0.0
    return ReviewDimensions(
        credibility=credible,
        novelty=0.0,
        correctness=correctness,
        reproducibility=reproducibility,
        significance=significance,
    )
