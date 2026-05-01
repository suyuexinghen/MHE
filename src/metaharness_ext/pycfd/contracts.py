from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator

from metaharness.core.models import ValidationIssue
from metaharness_ext.pycfd.types import (
    PyCFDCaseType,
    PyCFDFlowType,
    PyCFDFluxType,
    PyCFDLimiterType,
    PyCFDMeshType,
    PyCFDRunArtifactStatus,
    PyCFDSolverType,
    PyCFDValidationStatus,
)


class PyCFDMeshSpec(BaseModel):
    mesh_type: PyCFDMeshType = "quad"
    nx: int = 42
    ny: int = 21
    xb: float = -20.0
    xe: float = 20.0
    yb: float = -10.0
    ye: float = 10.0

    @field_validator("nx", "ny")
    @classmethod
    def validate_divisions(cls, value: int) -> int:
        if value < 2:
            raise ValueError("mesh divisions must be >= 2")
        return value


class PyCFDFlowSpec(BaseModel):
    M_inf: float = 0.3
    aoa: float = 0.0
    gamma: float = 1.4
    rho_inf: float = 1.0
    p_inf: float | None = None

    @field_validator("M_inf")
    @classmethod
    def validate_mach(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("M_inf must be positive")
        return value

    @field_validator("gamma")
    @classmethod
    def validate_gamma(cls, value: float) -> float:
        if value <= 1.0:
            raise ValueError("gamma must be > 1.0")
        return value


class PyCFDSolverSpec(BaseModel):
    CFL: float = 0.9
    second_order: bool = True
    use_limiter: bool = False
    limiter: PyCFDLimiterType = "none"
    inviscid_flux: PyCFDFluxType = "roe"
    eig_limiting_factor: float = 0.0
    max_steps: int = 100000

    @field_validator("CFL")
    @classmethod
    def validate_cfl(cls, value: float) -> float:
        if value <= 0 or value > 2.0:
            raise ValueError("CFL must be in (0, 2.0]")
        return value


class PyCFDProblemSpec(BaseModel):
    task_id: str
    case_type: PyCFDCaseType = "vortex"
    mesh: PyCFDMeshSpec = Field(default_factory=PyCFDMeshSpec)
    flow: PyCFDFlowSpec = Field(default_factory=PyCFDFlowSpec)
    solver: PyCFDSolverSpec = Field(default_factory=PyCFDSolverSpec)
    t_final: float = 1.0
    dt: float = 0.01
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

    @field_validator("t_final")
    @classmethod
    def validate_t_final(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("t_final must be positive")
        return value

    @field_validator("dt")
    @classmethod
    def validate_dt(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("dt must be positive")
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value

    @computed_field
    @property
    def flowtype(self) -> PyCFDFlowType:
        _map: dict[str, PyCFDFlowType] = {
            "vortex": "vortex",
            "airfoil": "freestream",
            "cylinder": "freestream",
            "mms": "mms",
            "shock_diffraction": "shock-diffraction",
        }
        return _map.get(self.case_type, "freestream")

    @computed_field
    @property
    def solver_type(self) -> PyCFDSolverType:
        _map: dict[str, PyCFDSolverType] = {
            "vortex": "explicit_unsteady_solver",
            "airfoil": "explicit_steady_solver",
            "cylinder": "explicit_steady_solver",
            "mms": "mms_solver",
            "shock_diffraction": "explicit_unsteady_solver_efficient_shockdiffraction",
        }
        return _map.get(self.case_type, "explicit_unsteady_solver")


class PyCFDEnvironmentReport(BaseModel):
    task_id: str
    available: bool = False
    status: str = "unknown"
    pycfd_src_path: str | None = None
    python_version: str | None = None
    numpy_version: str | None = None
    available_case_types: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False


class PyCFDRunPlan(BaseModel):
    plan_id: str
    task_id: str
    run_id: str
    spec: PyCFDProblemSpec
    workspace_dir: str
    script_source: str
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def experiment_ref(self) -> str:
        return self.task_id


class PyCFDRunArtifact(BaseModel):
    artifact_id: str
    run_id: str
    task_id: str
    plan_ref: str
    case_type: PyCFDCaseType = "vortex"
    status: PyCFDRunArtifactStatus = "unavailable"
    return_code: int | None = None
    error_message: str | None = None
    residual_l1: float | None = None
    residual_l2: float | None = None
    wall_time_seconds: float | None = None
    iterations: int | None = None
    ncells: int | None = None
    nnodes: int | None = None
    nfaces: int | None = None
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PyCFDValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool = False
    status: PyCFDValidationStatus = PyCFDValidationStatus.RUNTIME_FAILED
    messages: list[str] = Field(default_factory=list)
    residual_tolerance: float = 1e-5
    residual_l1_passed: bool = False
    residual_l2_passed: bool = False
    summary_metrics: dict[str, object] = Field(default_factory=dict)
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


class PyCFDEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class PyCFDEvidenceBundle(BaseModel):
    bundle_id: str
    task_id: str
    run_id: str | None = None
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    environment: PyCFDEnvironmentReport | None = None
    plan: PyCFDRunPlan | None = None
    artifact: PyCFDRunArtifact | None = None
    validation: PyCFDValidationReport | None = None
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[PyCFDEvidenceWarning] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PyCFDPolicyReport(BaseModel):
    passed: bool
    decision: str  # allow / defer / reject
    reason: str
    warnings: list[PyCFDEvidenceWarning] = Field(default_factory=list)
    gates: list[Any] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class PyCFDStudyAxis(BaseModel):
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


class PyCFDStudySpec(BaseModel):
    study_id: str
    task_template: PyCFDProblemSpec
    axes: list[PyCFDStudyAxis] = Field(default_factory=list)
    objective: str = "residual_l2"
    goal: str = "minimize"
    max_trials: int | None = None
    convergence_rule: str | None = None
    target_tolerance: float | None = None

    @computed_field
    @property
    def resolved_task_id(self) -> str:
        return self.task_template.task_id


class PyCFDStudyTrial(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class PyCFDStudyReport(BaseModel):
    study_id: str
    task_id: str | None = None
    trials: list[PyCFDStudyTrial] = Field(default_factory=list)
    best_trial_id: str | None = None
    recommended_parameters: dict[str, Any] | None = None
    convergence_analysis: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
