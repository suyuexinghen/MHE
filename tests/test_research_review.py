from __future__ import annotations

from dataclasses import dataclass

from metaharness.research.reviewers import MetricThresholdReviewer
from metaharness.research.store import ResearchStore
from metaharness.sdk.research import DecisionOutcome, EvidenceBundle, EvidenceStatus, Hypothesis
from metaharness.sdk.review import EvidenceReview, ReviewDimensions, ReviewerProtocol
from metaharness.sdk.review_calibration import ReviewerCalibrationCase, calibrate_reviewer


def _hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="P1 Lagrange elements produce L2 error below 0.01.",
        prediction={"l2_error": {"relation": "lt", "value": 0.01}},
    )


def _evidence(*, supports: bool) -> EvidenceBundle:
    hypothesis_id = "h-fealpy-poisson-p1-16x16"
    return EvidenceBundle(
        bundle_id="ev-supported" if supports else "ev-refuted",
        experiment_plan_id="plan-fealpy-poisson-extension",
        metrics={"l2_error": 0.002 if supports else 0.02},
        status=EvidenceStatus.PASSED,
        confidence=1.0,
        confidence_method="deterministic_metric_threshold",
        supports=[hypothesis_id] if supports else [],
        refutes=[] if supports else [hypothesis_id],
    )


def test_metric_threshold_reviewer_advances_supported_evidence() -> None:
    review = MetricThresholdReviewer().review(_hypothesis(), _evidence(supports=True))

    assert review.recommendation == DecisionOutcome.ADVANCE
    assert review.dimensions.credibility == 1.0
    assert review.dimensions.correctness == 1.0
    assert review.dimensions.reproducibility == 1.0


def test_metric_threshold_reviewer_refines_refuted_evidence() -> None:
    review = MetricThresholdReviewer().review(_hypothesis(), _evidence(supports=False))

    assert review.recommendation == DecisionOutcome.REFINE
    assert review.dimensions.credibility == 1.0
    assert review.dimensions.significance == 0.5


def test_reviewer_calibration_passes_expected_cases() -> None:
    hypothesis = _hypothesis()
    reviewer = MetricThresholdReviewer()
    cases = [
        ReviewerCalibrationCase(
            case_id="known-good",
            hypothesis=hypothesis,
            evidence=_evidence(supports=True),
            expected_recommendation=DecisionOutcome.ADVANCE,
        ),
        ReviewerCalibrationCase(
            case_id="known-bad",
            hypothesis=hypothesis,
            evidence=_evidence(supports=False),
            expected_recommendation=DecisionOutcome.REFINE,
        ),
    ]

    result = calibrate_reviewer(reviewer, cases, calibration_set_id="fealpy-smoke")

    assert result.reviewer_id == reviewer.reviewer_id
    assert result.accuracy == 1.0
    assert result.passed is True
    assert result.flagged_for_human_review is False
    assert result.failed_case_ids == []


def test_reviewer_calibration_blocks_incorrect_reviewer() -> None:
    @dataclass(frozen=True)
    class BadReviewer(ReviewerProtocol):
        reviewer_id: str = "bad-reviewer"

        def review(self, hypothesis: Hypothesis, evidence: EvidenceBundle) -> EvidenceReview:
            return EvidenceReview(
                review_id="bad-review",
                reviewer_id=self.reviewer_id,
                evidence_bundle_id=evidence.bundle_id,
                hypothesis_id=hypothesis.hypothesis_id,
                dimensions=ReviewDimensions(
                    credibility=0.0,
                    novelty=0.0,
                    correctness=0.0,
                    reproducibility=0.0,
                    significance=0.0,
                ),
                recommendation=DecisionOutcome.ADVANCE,
                reasoning="always advance",
            )

    hypothesis = _hypothesis()
    case = ReviewerCalibrationCase(
        case_id="known-bad",
        hypothesis=hypothesis,
        evidence=_evidence(supports=False),
        expected_recommendation=DecisionOutcome.REFINE,
    )

    result = calibrate_reviewer(BadReviewer(), [case], calibration_set_id="fealpy-smoke")

    assert result.passed is False
    assert result.failed_case_ids == ["known-bad"]


def test_research_store_records_reviews(tmp_path) -> None:
    evidence = _evidence(supports=True)
    review = MetricThresholdReviewer().review(_hypothesis(), evidence)
    store = ResearchStore(tmp_path)

    store.record_review(review)

    assert store.reviews_for(evidence.bundle_id) == [review]
