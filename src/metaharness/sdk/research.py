from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ResearchQuestionStatus(StrEnum):
    OPEN = "open"
    ACTIVE = "active"
    ANSWERED = "answered"
    STALE = "stale"


class ValidationStrategy(StrEnum):
    GROUND_TRUTH = "GROUND_TRUTH"


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"


class EvidenceStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DecisionOutcome(StrEnum):
    ADVANCE = "ADVANCE"
    REFINE = "REFINE"


class ResearchBudget(BaseModel):
    """P1 budget gate for experiment-count-limited loops."""

    max_experiments: int | None = Field(default=None, ge=0)
    experiments_used: int = Field(default=0, ge=0)
    max_wall_clock_seconds: float | None = Field(default=None, ge=0)
    max_llm_cost: float | None = Field(default=None, ge=0)

    @property
    def exhausted(self) -> bool:
        return self.max_experiments is not None and self.experiments_used >= self.max_experiments

    def consume_experiment(self) -> "ResearchBudget":
        return self.model_copy(update={"experiments_used": self.experiments_used + 1})


class ResearchQuestion(BaseModel):
    """Minimal research question for benchmark-backed MVP loops."""

    question_id: str
    statement: str
    formal_spec: dict[str, Any] = Field(default_factory=dict)
    status: ResearchQuestionStatus = ResearchQuestionStatus.OPEN
    created_from: str | None = None
    validation_strategy: ValidationStrategy = ValidationStrategy.GROUND_TRUTH


class Hypothesis(BaseModel):
    """Testable claim tied to one research question."""

    hypothesis_id: str
    question_id: str
    statement: str
    prediction: dict[str, dict[str, Any]] = Field(default_factory=dict)
    status: HypothesisStatus = HypothesisStatus.PROPOSED


class ExperimentPlan(BaseModel):
    """MVP experiment binding between a hypothesis and a benchmark case."""

    plan_id: str
    hypothesis_id: str
    run_plan_ref: str | None = None
    suite: str
    case_id: str
    lane: str | None = None
    controls: dict[str, Any] = Field(default_factory=dict)
    variables: dict[str, Any] = Field(default_factory=dict)
    expected_outcome: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    """Evidence extracted from a benchmark artifact."""

    bundle_id: str
    experiment_plan_id: str
    artifact_refs: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    status: EvidenceStatus
    failure_category: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_method: str
    validation_strategy: ValidationStrategy = ValidationStrategy.GROUND_TRUTH
    domain_tags: dict[str, Any] = Field(default_factory=dict)
    supports: list[str] = Field(default_factory=list)
    refutes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def execution_failures_do_not_judge_hypotheses(self) -> "EvidenceBundle":
        if self.status != EvidenceStatus.PASSED and (self.supports or self.refutes):
            raise ValueError("non-passing evidence cannot support or refute hypotheses")
        return self


class Decision(BaseModel):
    """MVP decision produced from one hypothesis and one evidence bundle."""

    decision_id: str
    hypothesis_id: str
    evidence_bundle_id: str
    decision: DecisionOutcome
    requires_approval: Literal[False] = False
    reasoning: str


class ResearchConclusion(BaseModel):
    """Minimal conclusion artifact for the MVP research loop."""

    question_id: str
    decision_ids: list[str] = Field(default_factory=list)
    supported_hypotheses: list[str] = Field(default_factory=list)
    refuted_hypotheses: list[str] = Field(default_factory=list)
    status: ResearchQuestionStatus
