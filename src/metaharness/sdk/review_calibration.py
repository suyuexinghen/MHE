from __future__ import annotations

from pydantic import BaseModel, Field

from metaharness.sdk.research import DecisionOutcome, EvidenceBundle, Hypothesis
from metaharness.sdk.review import ReviewerProtocol


class ReviewerCalibrationCase(BaseModel):
    case_id: str
    hypothesis: Hypothesis
    evidence: EvidenceBundle
    expected_recommendation: DecisionOutcome


class ReviewerCalibrationResult(BaseModel):
    reviewer_id: str
    calibration_set_id: str
    accuracy: float = Field(ge=0.0, le=1.0)
    passed: bool
    flagged_for_human_review: bool
    failed_case_ids: list[str] = Field(default_factory=list)


def calibrate_reviewer(
    reviewer: ReviewerProtocol,
    cases: list[ReviewerCalibrationCase],
    *,
    calibration_set_id: str,
    accuracy_threshold: float = 1.0,
    human_review_margin: float = 0.1,
) -> ReviewerCalibrationResult:
    failed_case_ids: list[str] = []
    for case in cases:
        review = reviewer.review(case.hypothesis, case.evidence)
        if review.recommendation != case.expected_recommendation:
            failed_case_ids.append(case.case_id)
    accuracy = 1.0 if not cases else (len(cases) - len(failed_case_ids)) / len(cases)
    passed = accuracy >= accuracy_threshold
    flagged = passed and accuracy < min(1.0, accuracy_threshold + human_review_margin)
    return ReviewerCalibrationResult(
        reviewer_id=reviewer.reviewer_id,
        calibration_set_id=calibration_set_id,
        accuracy=accuracy,
        passed=passed,
        flagged_for_human_review=flagged,
        failed_case_ids=failed_case_ids,
    )
