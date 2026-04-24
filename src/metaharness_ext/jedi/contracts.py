from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, field_validator, model_validator

from metaharness.safety.gates import GateResult
from metaharness_ext.jedi.types import (
    JediApplicationFamily,
    JediCostType,
    JediExecutionMode,
    JediLauncher,
    JediRunStatus,
    JediValidationStatus,
)


class JediExecutableSpec(BaseModel):
    binary_name: str = "qg4DVar.x"
    launcher: JediLauncher = "direct"
    execution_mode: JediExecutionMode = "validate_only"
    timeout_seconds: int | None = None
    process_count: int | None = None
    launcher_args: list[str] = Field(default_factory=list)

    @field_validator("binary_name")
    @classmethod
    def validate_binary_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or " " in stripped:
            raise ValueError("binary_name must be a non-empty executable name or path")
        basename = Path(stripped).name
        if not basename.endswith(".x"):
            raise ValueError("binary_name must reference an executable ending in .x")
        stem = basename[:-2]
        if not stem or not stem[0].isalpha():
            raise ValueError("binary_name must start with a letter")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if any(char not in allowed for char in stem):
            raise ValueError("binary_name contains unsupported characters")
        if stem.lower() == stem and "_" in stem and any(char.isdigit() for char in stem):
            raise ValueError("binary_name looks like a CTest test name, not an executable")
        return stripped

    @field_validator("launcher_args")
    @classmethod
    def validate_launcher_args(cls, value: list[str]) -> list[str]:
        for arg in value:
            if not arg or not arg.strip():
                raise ValueError("launcher_args must not contain empty strings")
        return [arg.strip() for arg in value]


class JediVariationalSpec(BaseModel):
    task_id: str
    application_family: Literal["variational"] = "variational"
    executable: JediExecutableSpec
    cost_type: JediCostType = "4D-Var"
    window_begin: str = "2020-01-01T00:00:00Z"
    window_length: str = "PT6H"
    geometry: dict[str, Any] = Field(default_factory=lambda: {"resolution": "toy"})
    background_path: str | None = None
    background: dict[str, Any] = Field(default_factory=dict)
    background_error_path: str | None = None
    background_error: dict[str, Any] = Field(default_factory=dict)
    observation_paths: list[str] = Field(default_factory=list)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    variational: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    final: dict[str, Any] = Field(default_factory=dict)
    test: dict[str, Any] = Field(default_factory=dict)
    required_paths: list[str] = Field(default_factory=list)
    reference_paths: list[str] = Field(default_factory=list)
    expected_diagnostics: list[str] = Field(default_factory=list)
    scientific_check: Literal["runtime_only", "rms_improves"] = "runtime_only"
    working_directory: str | None = None


class JediLocalEnsembleDASpec(BaseModel):
    task_id: str
    application_family: Literal["local_ensemble_da"] = "local_ensemble_da"
    executable: JediExecutableSpec
    window_begin: str = "2020-01-01T00:00:00Z"
    window_length: str = "PT6H"
    geometry: dict[str, Any] = Field(default_factory=lambda: {"resolution": "toy"})
    ensemble_paths: list[str] = Field(default_factory=list)
    observation_paths: list[str] = Field(default_factory=list)
    background_path: str | None = None
    background: dict[str, Any] = Field(default_factory=dict)
    driver: dict[str, Any] = Field(default_factory=dict)
    ensemble: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    final: dict[str, Any] = Field(default_factory=dict)
    test: dict[str, Any] = Field(default_factory=dict)
    required_paths: list[str] = Field(default_factory=list)
    reference_paths: list[str] = Field(default_factory=list)
    expected_diagnostics: list[str] = Field(default_factory=list)
    scientific_check: Literal["runtime_only", "ensemble_outputs_present"] = "runtime_only"
    working_directory: str | None = None

    @model_validator(mode="after")
    def validate_ensemble_paths(self) -> "JediLocalEnsembleDASpec":
        if not self.ensemble_paths:
            raise ValueError("local_ensemble_da requires at least one ensemble path")
        if any(not path.strip() for path in self.ensemble_paths):
            raise ValueError("ensemble_paths must not contain empty strings")
        return self


class JediHofXSpec(BaseModel):
    task_id: str
    application_family: Literal["hofx"] = "hofx"
    executable: JediExecutableSpec
    geometry: dict[str, Any] = Field(default_factory=lambda: {"resolution": "toy"})
    state_path: str | None = None
    observation_paths: list[str] = Field(default_factory=list)
    hofx: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    test: dict[str, Any] = Field(default_factory=dict)
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None


class JediForecastSpec(BaseModel):
    task_id: str
    application_family: Literal["forecast"] = "forecast"
    executable: JediExecutableSpec
    geometry: dict[str, Any] = Field(default_factory=lambda: {"resolution": "toy"})
    initial_condition_path: str | None = None
    model: dict[str, Any] = Field(default_factory=dict)
    forecast: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    test: dict[str, Any] = Field(default_factory=dict)
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None


JediExperimentSpec = Annotated[
    JediVariationalSpec | JediLocalEnsembleDASpec | JediHofXSpec | JediForecastSpec,
    Field(discriminator="application_family"),
]
JEDI_EXPERIMENT_SPEC_ADAPTER = TypeAdapter(JediExperimentSpec)


class JediEnvironmentReport(BaseModel):
    binary_available: bool
    launcher_available: bool
    shared_libraries_resolved: bool
    required_paths_present: bool
    workspace_testinput_present: bool = True
    data_paths_present: bool = True
    data_prerequisites_ready: bool = True
    binary_path: str | None = None
    launcher_path: str | None = None
    workspace_root: str | None = None
    missing_required_paths: list[str] = Field(default_factory=list)
    missing_data_paths: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    ready_prerequisites: list[str] = Field(default_factory=list)
    prerequisite_evidence: dict[str, list[str]] = Field(default_factory=dict)
    environment_prerequisites: list[str] = Field(default_factory=list)
    smoke_candidate: JediApplicationFamily | None = None
    smoke_ready: bool = False
    messages: list[str] = Field(default_factory=list)


class JediRunPlan(BaseModel):
    task_id: str
    run_id: str
    application_family: JediApplicationFamily
    execution_mode: JediExecutionMode
    command: list[str] = Field(default_factory=list)
    working_directory: str
    config_path: str
    schema_path: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)
    expected_diagnostics: list[str] = Field(default_factory=list)
    expected_references: list[str] = Field(default_factory=list)
    required_runtime_paths: list[str] = Field(default_factory=list)
    scientific_check: Literal["runtime_only", "rms_improves", "ensemble_outputs_present"] = (
        "runtime_only"
    )
    config_text: str
    executable: JediExecutableSpec


class JediRunArtifact(BaseModel):
    task_id: str
    run_id: str
    application_family: JediApplicationFamily
    execution_mode: JediExecutionMode
    command: list[str] = Field(default_factory=list)
    return_code: int | None = None
    config_path: str | None = None
    schema_path: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    prepared_inputs: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    reference_files: list[str] = Field(default_factory=list)
    working_directory: str
    status: JediRunStatus = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)


class JediSmokePolicyReport(BaseModel):
    ready: bool
    recommended_family: str | None
    recommended_binary: str | None
    reason: str


class JediDiagnosticSummary(BaseModel):
    ioda_groups_found: list[str] = Field(default_factory=list)
    ioda_groups_missing: list[str] = Field(default_factory=list)
    files_scanned: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    minimizer_iterations: int | None = None
    outer_iterations: int | None = None
    inner_iterations: int | None = None
    initial_cost_function: float | None = None
    final_cost_function: float | None = None
    initial_gradient_norm: float | None = None
    final_gradient_norm: float | None = None
    gradient_norm_reduction: float | None = None
    posterior_output_detected: bool = False
    observer_output_detected: bool = False


class JediValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool
    status: JediValidationStatus
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
    blocking_reasons: list[str] = Field(default_factory=list)
    policy_decision: Literal["allow", "defer", "reject"] | None = None
    prerequisite_evidence: dict[str, list[str]] = Field(default_factory=dict)
    provenance_refs: list[str] = Field(default_factory=list)
    checkpoint_refs: list[str] = Field(default_factory=list)


class JediEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning"] = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class JediEvidenceBundle(BaseModel):
    task_id: str
    run_id: str
    application_family: JediApplicationFamily
    execution_mode: JediExecutionMode
    run: JediRunArtifact
    validation: JediValidationReport | None = None
    summary: JediDiagnosticSummary | None = None
    evidence_files: list[str] = Field(default_factory=list)
    warnings: list[JediEvidenceWarning] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JediPolicyReport(BaseModel):
    passed: bool
    decision: Literal["allow", "defer", "reject"]
    reason: str
    warnings: list[JediEvidenceWarning] = Field(default_factory=list)
    gates: list[GateResult] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class JediMutationAxis(BaseModel):
    kind: Literal[
        "variational_minimizer",
        "variational_iterations",
        "validate_only_mode",
        "ensemble_inflation",
        "ensemble_localization_radius",
    ]
    values: list[str | int | float] = Field(default_factory=list)
    label: str | None = None

    @model_validator(mode="after")
    def validate_values(self) -> "JediMutationAxis":
        if not self.values:
            raise ValueError("axis.values must not be empty")
        return self


class JediStudySpec(BaseModel):
    study_id: str
    task_id: str
    base_task: JediVariationalSpec | JediLocalEnsembleDASpec
    axis: JediMutationAxis
    metric_key: str
    goal: Literal["minimize", "maximize"] = "minimize"


class JediStudyTrial(BaseModel):
    trial_id: str
    task_id: str
    axis_kind: str
    axis_value: str | int | float
    mutated_parameters: dict[str, int | float | str] = Field(default_factory=dict)
    run: JediRunArtifact
    diagnostics: JediDiagnosticSummary
    validation: JediValidationReport
    evidence_bundle: JediEvidenceBundle | None = None
    policy_report: JediPolicyReport | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class JediStudyReport(BaseModel):
    study_id: str
    task_id: str
    axis_kind: str
    metric_key: str
    trials: list[JediStudyTrial] = Field(default_factory=list)
    recommended_value: str | int | float | None = None
    recommended_trial_id: str | None = None
    recommended_reason: str | None = None
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
