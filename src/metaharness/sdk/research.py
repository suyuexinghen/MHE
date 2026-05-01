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
    SUPERSEDED = "superseded"


class EvidenceStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EvidenceQuality(StrEnum):
    HIGH = "high"
    INCONCLUSIVE = "inconclusive"
    EXECUTION_FAILURE = "execution_failure"


class ReproducibilityTier(StrEnum):
    DETERMINISTIC = "deterministic"
    SINGLE_RUN = "single_run"
    UNVERIFIED = "unverified"


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
    parent_hypothesis_id: str | None = None
    estimated_information_gain: float = Field(default=0.0, ge=0.0)
    estimated_cost: float = Field(default=1.0, gt=0.0)

    @property
    def cost_benefit_ratio(self) -> float:
        return self.estimated_information_gain / self.estimated_cost


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


class DossierClaim(BaseModel):
    """Traceable statement in a research dossier."""

    claim_id: str
    statement: str
    hypothesis_ids: list[str] = Field(default_factory=list)
    evidence_bundle_ids: list[str] = Field(default_factory=list)
    baseline_refs: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_quality: EvidenceQuality
    reproducibility_tier: ReproducibilityTier

    @model_validator(mode="after")
    def claim_must_be_traceable(self) -> "DossierClaim":
        if not self.evidence_bundle_ids and not self.baseline_refs:
            raise ValueError("dossier claims must cite evidence bundles or SOTA baselines")
        return self


class NegativeResultCluster(BaseModel):
    """Grouped dead-end evidence for avoiding repeated failed research paths."""

    cluster_id: str
    domain_tags: dict[str, Any] = Field(default_factory=dict)
    metric_schema: str | None = None
    failure_category: str | None = None
    evidence_bundle_ids: list[str] = Field(default_factory=list)
    refuted_hypothesis_ids: list[str] = Field(default_factory=list)
    repeated_dead_end: bool = False


class ResearchDossier(BaseModel):
    """Minimal traceable dossier for a completed MVP research loop."""

    dossier_id: str
    question_id: str
    claims: list[DossierClaim] = Field(default_factory=list)
    negative_result_clusters: list[NegativeResultCluster] = Field(default_factory=list)
    conclusion: ResearchConclusion
