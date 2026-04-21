from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from metaharness_ext.ai4pde.types import NextAction, ProblemType, RiskLevel, SolverFamily


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
