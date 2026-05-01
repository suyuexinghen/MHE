from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field

from metaharness.sdk.research import DecisionOutcome, EvidenceBundle, Hypothesis


class ReviewDimensions(BaseModel):
    credibility: float = Field(ge=0.0, le=1.0)
    novelty: float = Field(ge=0.0, le=1.0)
    correctness: float = Field(ge=0.0, le=1.0)
    reproducibility: float = Field(ge=0.0, le=1.0)
    significance: float = Field(ge=0.0, le=1.0)


class EvidenceReview(BaseModel):
    review_id: str
    reviewer_id: str
    evidence_bundle_id: str
    hypothesis_id: str
    dimensions: ReviewDimensions
    recommendation: DecisionOutcome
    reasoning: str


@runtime_checkable
class ReviewerProtocol(Protocol):
    """Reviews one evidence bundle against one hypothesis."""

    reviewer_id: str

    def review(self, hypothesis: Hypothesis, evidence: EvidenceBundle) -> EvidenceReview: ...
