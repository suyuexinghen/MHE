from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from metaharness.core.models import ScoredEvidence, SessionEvent
from metaharness_ext.ai4pde.types import (
    NextAction,
    ProblemType,
    PromotionOutcome,
    RiskLevel,
    SafetyOutcome,
    SolverFamily,
)


class BudgetRecord(BaseModel):
    token_budget: int = 0
    gpu_hours: float = 0.0
    cpu_hours: float = 0.0
    walltime_hours: float = 0.0
    hpc_quota: float = 0.0
    candidate_eval_budget: int = 0


class PDETaskRequest(BaseModel):
    task_id: str
    goal: str
    problem_type: ProblemType
    physics_spec: dict[str, Any] = Field(default_factory=dict)
    geometry_spec: dict[str, Any] = Field(default_factory=dict)
    data_spec: dict[str, Any] = Field(default_factory=dict)
    deliverables: list[str] = Field(default_factory=list)
    budget: BudgetRecord = Field(default_factory=BudgetRecord)
    risk_level: RiskLevel = RiskLevel.GREEN


class PDEPlan(BaseModel):
    plan_id: str
    task_id: str
    selected_method: SolverFamily
    template_id: str | None = None
    graph_family: str = "ai4pde-minimal"
    slot_bindings: dict[str, str] = Field(default_factory=dict)
    parameter_overrides: dict[str, Any] = Field(default_factory=dict)
    required_validators: list[str] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)


class PDERunArtifact(BaseModel):
    run_id: str
    task_id: str
    solver_family: SolverFamily
    artifact_refs: list[str] = Field(default_factory=list)
    checkpoint_refs: list[str] = Field(default_factory=list)
    telemetry_refs: list[str] = Field(default_factory=list)
    status: str = "executed"
    result_summary: dict[str, Any] = Field(default_factory=dict)


class ReferenceResult(BaseModel):
    reference_id: str
    task_id: str
    solver_family: SolverFamily = SolverFamily.CLASSICAL_HYBRID
    artifact_refs: list[str] = Field(default_factory=list)
    benchmark_snapshot_refs: list[str] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class CandidateIdentity(BaseModel):
    candidate_id: str | None = None
    proposed_graph_version: int | None = None
    graph_version_id: int | None = None
    actor: str | None = None
    template_id: str | None = None
    solver_family: SolverFamily | None = None


class PromotionMetadata(BaseModel):
    outcome: PromotionOutcome = PromotionOutcome.PENDING
    candidate_identity: CandidateIdentity = Field(default_factory=CandidateIdentity)
    affected_protected_components: list[str] = Field(default_factory=list)
    created_at: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ProtectionOutcome(BaseModel):
    protected_components: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    allowed: bool | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class SafetyEvaluation(BaseModel):
    outcome: SafetyOutcome = SafetyOutcome.UNKNOWN
    rejected_by: str | None = None
    rejected_reason: str | None = None
    guard_vetoed: bool = False
    protection: ProtectionOutcome = Field(default_factory=ProtectionOutcome)
    details: dict[str, Any] = Field(default_factory=dict)


class RollbackContext(BaseModel):
    rollback_target: int | None = None
    rollback_recommended: bool = False
    rollback_reason: str | None = None
    applied: bool = False
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationBundle(BaseModel):
    validation_id: str
    task_id: str
    graph_version_id: int
    residual_metrics: dict[str, float] = Field(default_factory=dict)
    bc_ic_metrics: dict[str, float] = Field(default_factory=dict)
    conservation_metrics: dict[str, float] = Field(default_factory=dict)
    reference_comparison: dict[str, Any] = Field(default_factory=dict)
    telemetry_refs: list[str] = Field(default_factory=list)
    lifecycle_refs: list[str] = Field(default_factory=list)
    budget_state: dict[str, Any] = Field(default_factory=dict)
    violations: list[str] = Field(default_factory=list)
    next_action: NextAction = NextAction.ACCEPT
    summary: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: PromotionMetadata = Field(default_factory=PromotionMetadata)
    candidate_identity: CandidateIdentity = Field(default_factory=CandidateIdentity)
    safety_evaluation: SafetyEvaluation = Field(default_factory=SafetyEvaluation)
    rollback_context: RollbackContext = Field(default_factory=RollbackContext)
    scored_evidence: ScoredEvidence | None = None
    session_events: list[SessionEvent] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class ScientificEvidenceBundle(BaseModel):
    bundle_id: str
    task_id: str
    graph_version_id: int
    template_id: str | None = None
    solver_config: dict[str, Any] = Field(default_factory=dict)
    validation_summary: dict[str, Any] = Field(default_factory=dict)
    artifact_hashes: list[str] = Field(default_factory=list)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    reference_comparison_refs: list[str] = Field(default_factory=list)
    benchmark_snapshot_refs: list[str] = Field(default_factory=list)
    baseline_metadata: dict[str, Any] = Field(default_factory=dict)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: PromotionMetadata = Field(default_factory=PromotionMetadata)
    candidate_identity: CandidateIdentity = Field(default_factory=CandidateIdentity)
    safety_evaluation: SafetyEvaluation = Field(default_factory=SafetyEvaluation)
    rollback_context: RollbackContext = Field(default_factory=RollbackContext)
    scored_evidence: ScoredEvidence | None = None
    session_events: list[SessionEvent] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
