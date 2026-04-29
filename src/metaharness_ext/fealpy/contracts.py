from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator

from metaharness.core.models import ValidationIssue
from metaharness_ext.fealpy.types import (
    FealpyBackend,
    FealpyMeshType,
    FealpyPdeFamily,
    FealpyRunArtifactStatus,
    FealpySolverMethod,
    FealpyValidationStatus,
)


class FealpyMeshSpec(BaseModel):
    meshtype: FealpyMeshType = "tri"
    nx: int = 8
    ny: int | None = 8
    nz: int | None = None
    h: float | None = None

    @field_validator("nx")
    @classmethod
    def validate_nx(cls, value: int) -> int:
        if value < 2:
            raise ValueError("nx must be >= 2")
        return value

    @field_validator("ny", "nz")
    @classmethod
    def validate_optional_divisions(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("mesh divisions must be >= 1")
        return value


class FealpySolverSpec(BaseModel):
    method: FealpySolverMethod = "direct"
    max_iterations: int = 5000
    atol: float = 1e-14
    rtol: float = 1e-14

    @field_validator("max_iterations")
    @classmethod
    def validate_maxit(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_iterations must be >= 1")
        return value


class FealpyProblemSpec(BaseModel):
    task_id: str
    pde_family: FealpyPdeFamily = "poisson"
    example_key: int = 1
    backend: FealpyBackend = "numpy"
    mesh: FealpyMeshSpec = Field(default_factory=FealpyMeshSpec)
    fe_degree: int = 1
    solver: FealpySolverSpec = Field(default_factory=FealpySolverSpec)
    adaptive_refinement: int = 0
    timeout_seconds: int = 300
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(c in stripped for c in ("/", "\\", "..")):
            raise ValueError("task_id must be a simple identifier")
        return stripped

    @field_validator("fe_degree")
    @classmethod
    def validate_degree(cls, value: int) -> int:
        if value < 1:
            raise ValueError("fe_degree must be >= 1")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value

    @field_validator("adaptive_refinement")
    @classmethod
    def validate_refinement(cls, value: int) -> int:
        if value < 0:
            raise ValueError("adaptive_refinement must be >= 0")
        return value


class FealpyEnvironmentReport(BaseModel):
    task_id: str
    available: bool = False
    status: str = "unknown"
    fealpy_version: str | None = None
    python_version: str | None = None
    available_backends: list[str] = Field(default_factory=list)
    available_pde_families: list[str] = Field(default_factory=list)
    backend_status: dict[str, bool] = Field(default_factory=dict)
    missing_prerequisites: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False


class FealpyRunPlan(BaseModel):
    plan_id: str
    task_id: str
    run_id: str
    spec: FealpyProblemSpec
    workspace_dir: str
    script_source: str
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def experiment_ref(self) -> str:
        return self.task_id


class FealpyRunArtifact(BaseModel):
    artifact_id: str
    run_id: str
    task_id: str
    plan_ref: str
    status: FealpyRunArtifactStatus
    return_code: int | None = None
    error_message: str | None = None
    l2_error: float | None = None
    h1_error: float | None = None
    linf_error: float | None = None
    dof_count: int | None = None
    solver_iterations: int | None = None
    wall_time_seconds: float | None = None
    mesh_info: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FealpyValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool = False
    status: FealpyValidationStatus = FealpyValidationStatus.RUNTIME_FAILED
    messages: list[str] = Field(default_factory=list)
    l2_tolerance: float = 1e-6
    h1_tolerance: float = 1e-4
    l2_passed: bool = False
    h1_passed: bool = False
    linf_passed: bool | None = None
    summary_metrics: dict[str, float | int | str | bool] = Field(default_factory=dict)
    issues: list[ValidationIssue] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def run_id(self) -> str:
        return self.artifact_ref

    @computed_field
    @property
    def blocks_promotion(self) -> bool:
        return any(issue.blocks_promotion for issue in self.issues)


# ── Evidence ───────────────────────────────────────────────────────────


class FealpyEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class FealpyEvidenceBundle(BaseModel):
    bundle_id: str
    task_id: str
    run_id: str | None = None
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    environment: FealpyEnvironmentReport | None = None
    plan: FealpyRunPlan | None = None
    artifact: FealpyRunArtifact | None = None
    validation: FealpyValidationReport | None = None
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[FealpyEvidenceWarning] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Policy ─────────────────────────────────────────────────────────────


class FealpyPolicyReport(BaseModel):
    passed: bool
    decision: str  # allow / defer / reject
    reason: str
    warnings: list[FealpyEvidenceWarning] = Field(default_factory=list)
    gates: list[Any] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


# ── Study ──────────────────────────────────────────────────────────────


class FealpyStudyAxis(BaseModel):
    parameter_path: str
    values: list[Any] | None = None
    range: tuple[float, float] | None = None
    step: float | None = None

    @field_validator("parameter_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("parameter_path must not be empty")
        return value.strip()


class FealpyStudySpec(BaseModel):
    study_id: str
    task_template: FealpyProblemSpec
    axes: list[FealpyStudyAxis] = Field(default_factory=list)
    objective: str = "l2_error"
    goal: str = "minimize"  # minimize / maximize
    max_trials: int | None = None

    @computed_field
    @property
    def resolved_task_id(self) -> str:
        return self.task_template.task_id


class FealpyStudyTrial(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class FealpyStudyReport(BaseModel):
    study_id: str
    task_id: str | None = None
    trials: list[FealpyStudyTrial] = Field(default_factory=list)
    best_trial_id: str | None = None
    recommended_parameters: dict[str, Any] | None = None
    convergence_analysis: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
