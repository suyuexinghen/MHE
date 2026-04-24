from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from metaharness.core.models import ScoredEvidence
from metaharness_ext.nektar.types import (
    NektarAdrEqType,
    NektarBoundaryConditionType,
    NektarGeometryMode,
    NektarIncnsEqType,
    NektarIncnsSolverType,
    NektarProjection,
    NektarSolverFamily,
)

NektarRunStatus = Literal["planned", "completed", "failed", "unavailable"]
NektarPromotionOutcome = Literal["pending", "approved", "rejected", "unknown"]


class NektarCandidateIdentity(BaseModel):
    candidate_id: str | None = None
    proposed_graph_version: int | None = None
    graph_version_id: int | None = None
    actor: str | None = None
    template_id: str | None = None
    solver_family: NektarSolverFamily | None = None


class NektarPromotionMetadata(BaseModel):
    outcome: NektarPromotionOutcome = "pending"
    candidate_identity: NektarCandidateIdentity = Field(default_factory=NektarCandidateIdentity)
    affected_components: list[str] = Field(default_factory=list)
    created_at: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class NektarExecutionPolicy(BaseModel):
    sandbox_profile: str | None = None
    policy_tags: list[str] = Field(default_factory=list)
    required_binaries: list[str] = Field(default_factory=list)
    binary_constraints: dict[str, Any] = Field(default_factory=dict)
    requires_network: bool = False
    requires_workspace_write: bool = True
    details: dict[str, Any] = Field(default_factory=dict)


class NektarBoundaryCondition(BaseModel):
    region: str
    field: str
    condition_type: NektarBoundaryConditionType
    value: str | None = None
    user_defined_type: str | None = None
    prim_coeff: str | None = None

    @model_validator(mode="after")
    def validate_robin_prim_coeff(self) -> "NektarBoundaryCondition":
        if self.condition_type == NektarBoundaryConditionType.ROBIN and not self.prim_coeff:
            raise ValueError("Robin BC requires prim_coeff (PRIMCOEFF in Nektar++ XML)")
        return self


class NektarGeometrySection(BaseModel):
    dimension: int = 2
    space_dimension: int | None = None
    vertices: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    faces: list[dict[str, Any]] = Field(default_factory=list)
    elements: list[dict[str, Any]] = Field(default_factory=list)
    curved: list[dict[str, Any]] = Field(default_factory=list)
    composites: list[dict[str, Any]] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dimension_constraints(self) -> "NektarGeometrySection":
        if self.dimension not in {1, 2, 3}:
            raise ValueError("Geometry dimension must be 1, 2, or 3")
        if self.space_dimension is not None and self.space_dimension < self.dimension:
            raise ValueError("space_dimension must be greater than or equal to dimension")
        has_explicit_geometry = any(
            [
                self.vertices,
                self.edges,
                self.faces,
                self.elements,
                self.curved,
                self.composites,
                self.domain,
            ]
        )
        if self.dimension >= 2 and has_explicit_geometry and not self.edges:
            raise ValueError("Geometry with dimension >= 2 requires edges")
        if self.dimension == 3 and has_explicit_geometry and not self.faces:
            raise ValueError("Geometry with dimension 3 requires faces")
        return self


class NektarProblemSpec(BaseModel):
    task_id: str
    title: str
    solver_family: NektarSolverFamily
    dimension: int
    space_dimension: int | None = None
    equation_type: NektarAdrEqType | NektarIncnsEqType | None = None
    variables: list[str] = Field(default_factory=list)
    domain: dict[str, Any] = Field(default_factory=dict)
    materials: dict[str, float | str] = Field(default_factory=dict)
    parameters: dict[str, float | str] = Field(default_factory=dict)
    initial_conditions: list[dict[str, Any]] = Field(default_factory=list)
    boundary_conditions: list[NektarBoundaryCondition] = Field(default_factory=list)
    forcing: list[dict[str, Any]] = Field(default_factory=list)
    reference: dict[str, Any] | None = None
    postprocess_plan: list[dict[str, Any]] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: NektarCandidateIdentity = Field(default_factory=NektarCandidateIdentity)
    promotion_metadata: NektarPromotionMetadata = Field(default_factory=NektarPromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: NektarExecutionPolicy = Field(default_factory=NektarExecutionPolicy)

    @model_validator(mode="after")
    def validate_equation_type(self) -> "NektarProblemSpec":
        if self.equation_type is None:
            return self
        if self.solver_family == NektarSolverFamily.ADR and not isinstance(
            self.equation_type, NektarAdrEqType
        ):
            raise ValueError("ADR problems require a NektarAdrEqType equation_type")
        if self.solver_family == NektarSolverFamily.INCNS and not isinstance(
            self.equation_type, NektarIncnsEqType
        ):
            raise ValueError("IncNS problems require a NektarIncnsEqType equation_type")
        return self


class NektarMeshSpec(BaseModel):
    source_mode: Literal["existing_xml", "nekg", "gmsh", "generated"]
    source_path: str | None = None
    geometry_mode: NektarGeometryMode = NektarGeometryMode.DIM_2D
    geometry: NektarGeometrySection = Field(default_factory=NektarGeometrySection)
    periodic_pairs: list[dict[str, Any]] = Field(default_factory=list)
    mesh_processes: list[dict[str, Any]] = Field(default_factory=list)


class NektarExpansionSpec(BaseModel):
    field: str
    composite_ids: list[str] = Field(default_factory=list)
    basis_type: str
    num_modes: int | dict[str, int]
    points_type: str | None = None
    homogeneous_length: float | None = None


class NektarSessionPlan(BaseModel):
    plan_id: str
    task_id: str
    solver_family: NektarSolverFamily
    solver_binary: str
    equation_type: NektarAdrEqType | NektarIncnsEqType
    projection: NektarProjection = NektarProjection.CONTINUOUS
    solver_type: NektarIncnsSolverType | None = None
    mesh: NektarMeshSpec
    variables: list[str] = Field(default_factory=list)
    expansions: list[NektarExpansionSpec] = Field(default_factory=list)
    solver_info: dict[str, str] = Field(default_factory=dict)
    parameters: dict[str, float | str] = Field(default_factory=dict)
    time_integration: dict[str, Any] = Field(default_factory=dict)
    boundary_regions: list[dict[str, Any]] = Field(default_factory=list)
    boundary_conditions: list[NektarBoundaryCondition] = Field(default_factory=list)
    functions: list[dict[str, Any]] = Field(default_factory=list)
    forcing: list[dict[str, Any]] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    validation_targets: list[str] = Field(default_factory=list)
    render_geometry_inline: bool = False
    session_file_name: str = "session.xml"
    postprocess_plan: list[dict[str, Any]] = Field(default_factory=list)
    global_system_solution_info: dict[str, Any] = Field(default_factory=dict)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: NektarCandidateIdentity = Field(default_factory=NektarCandidateIdentity)
    promotion_metadata: NektarPromotionMetadata = Field(default_factory=NektarPromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: NektarExecutionPolicy = Field(default_factory=NektarExecutionPolicy)

    @model_validator(mode="after")
    def validate_equation_type(self) -> "NektarSessionPlan":
        if self.solver_family == NektarSolverFamily.ADR and not isinstance(
            self.equation_type, NektarAdrEqType
        ):
            raise ValueError("ADR plans require a NektarAdrEqType equation_type")
        if self.solver_family == NektarSolverFamily.INCNS and not isinstance(
            self.equation_type, NektarIncnsEqType
        ):
            raise ValueError("IncNS plans require a NektarIncnsEqType equation_type")
        return self


class FilterOutputSummary(BaseModel):
    files: list[str] = Field(default_factory=list)
    checkpoint_files: list[str] = Field(default_factory=list)
    history_point_files: list[str] = Field(default_factory=list)
    fieldconvert_intermediates: list[str] = Field(default_factory=list)
    error_norms: dict[str, float | str] = Field(default_factory=dict)
    metrics: dict[str, float | str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SolverLogAnalysis(BaseModel):
    path: str
    exists: bool
    warning_count: int = 0
    error_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_steps: int | None = None
    final_time: float | None = None
    cpu_time: float | None = None
    wall_time: float | None = None
    l2_error_keys: list[str] = Field(default_factory=list)
    linf_error_keys: list[str] = Field(default_factory=list)
    has_timeout_marker: bool = False
    incns_metrics: dict[str, float] = Field(default_factory=dict)


class FilterOutputAnalysis(BaseModel):
    files: list[str] = Field(default_factory=list)
    existing_files: list[str] = Field(default_factory=list)
    missing_files: list[str] = Field(default_factory=list)
    formats: dict[str, str] = Field(default_factory=dict)
    file_sizes: dict[str, int] = Field(default_factory=dict)
    has_vtu: bool = False
    has_dat: bool = False
    has_fld: bool = False
    nonempty_count: int = 0


class ErrorSummary(BaseModel):
    l2_keys: list[str] = Field(default_factory=list)
    linf_keys: list[str] = Field(default_factory=list)
    max_l2: float | None = None
    max_linf: float | None = None
    primary_variable: str | None = None
    primary_l2: float | None = None
    status: Literal[
        "no_reference_error",
        "reference_error_present",
        "reference_error_within_tolerance",
        "reference_error_exceeds_tolerance",
    ] = "no_reference_error"
    messages: list[str] = Field(default_factory=list)


class NektarMutationAxis(BaseModel):
    kind: Literal["num_modes"]
    values: list[int] = Field(default_factory=list)
    label: str | None = None


class ConvergenceStudySpec(BaseModel):
    study_id: str
    task_id: str
    base_problem: NektarProblemSpec
    axis: NektarMutationAxis
    metric_key: str = "l2_error_u"
    convergence_rule: Literal["absolute", "relative_drop", "plateau"] = "absolute"
    target_tolerance: float | None = None
    relative_drop_ratio: float = 0.5
    plateau_tolerance: float = 0.1
    min_points: int = 3
    stop_on_first_pass: bool = False
    postprocess_plan_override: list[dict[str, str]] | None = None


class NektarRunArtifact(BaseModel):
    run_id: str
    task_id: str
    solver_family: NektarSolverFamily
    solver_binary: str
    session_files: list[str] = Field(default_factory=list)
    mesh_files: list[str] = Field(default_factory=list)
    field_files: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    derived_files: list[str] = Field(default_factory=list)
    filter_output: FilterOutputSummary = Field(default_factory=FilterOutputSummary)
    result_summary: dict[str, Any] = Field(default_factory=dict)
    postprocess_plan: list[dict[str, Any]] = Field(default_factory=list)
    status: NektarRunStatus = "planned"
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: NektarCandidateIdentity = Field(default_factory=NektarCandidateIdentity)
    promotion_metadata: NektarPromotionMetadata = Field(default_factory=NektarPromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    execution_policy: NektarExecutionPolicy = Field(default_factory=NektarExecutionPolicy)


class NektarValidationReport(BaseModel):
    task_id: str
    passed: bool
    solver_exited_cleanly: bool | None = None
    field_files_exist: bool | None = None
    error_vs_reference: bool | None = None
    messages: list[str] = Field(default_factory=list)
    metrics: dict[str, float | str] = Field(default_factory=dict)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None


class ConvergenceTrialReport(BaseModel):
    trial_id: str
    task_id: str
    axis_kind: str
    axis_value: int
    mutated_parameters: dict[str, float | str] = Field(default_factory=dict)
    plan_id: str
    run: NektarRunArtifact
    validation: NektarValidationReport
    solver_log_analysis: SolverLogAnalysis
    filter_output_analysis: FilterOutputAnalysis
    error_summary: ErrorSummary
    metric_value: float | None = None
    status: NektarRunStatus = "planned"
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class ConvergenceStudyReport(BaseModel):
    study_id: str
    task_id: str
    axis_kind: str
    metric_key: str
    trials: list[ConvergenceTrialReport] = Field(default_factory=list)
    recommended_value: int | None = None
    recommended_trial_id: str | None = None
    converged: bool = False
    observed_order: float | None = None
    recommended_reason: str | None = None
    error_sequence: list[float] = Field(default_factory=list)
    drop_ratios: list[float] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
