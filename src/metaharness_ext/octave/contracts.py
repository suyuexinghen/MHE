from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from metaharness.core.models import ScoredEvidence, ValidationIssue
from metaharness.safety.gates import GateResult
from metaharness_ext.octave.types import (
    OctaveExperimentFamily,
    OctaveGovernanceState,
    OctaveInputKind,
    OctaveOutputKind,
    OctaveRunArtifactStatus,
    OctaveScriptMode,
    OctaveStudyStrategy,
    OctaveValidationStatus,
    OctaveWarningSeverity,
)


class OctaveExecutableSpec(BaseModel):
    binary_name: str = "octave-cli"
    timeout_seconds: int = 300
    env: dict[str, str] = Field(default_factory=dict)
    minimum_version: str | None = None

    @field_validator("binary_name")
    @classmethod
    def validate_binary_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(part in stripped for part in ("\x00", "\n", "\r")):
            raise ValueError("binary_name must be a non-empty executable name or path")
        return stripped

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value


class OctaveWorkspaceSpec(BaseModel):
    working_directory: str | None = None
    output_directory: str = "outputs"
    cleanup: bool = False
    allow_network: bool = False
    allowed_read_paths: list[str] = Field(default_factory=list)
    allowed_write_paths: list[str] = Field(default_factory=list)


class OctaveScriptSpec(BaseModel):
    mode: OctaveScriptMode = "inline"
    inline_source: str | None = None
    script_path: str | None = None
    function_name: str | None = None
    function_args: list[str] = Field(default_factory=list)
    add_paths: list[str] = Field(default_factory=list)
    method_hints: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_source(self) -> "OctaveScriptSpec":
        if self.mode == "inline" and not self.inline_source:
            raise ValueError("inline mode requires inline_source")
        if self.mode == "file" and not self.script_path:
            raise ValueError("file mode requires script_path")
        if self.mode == "function" and not self.function_name:
            raise ValueError("function mode requires function_name")
        return self


class OctavePackageSpec(BaseModel):
    name: str
    version: str | None = None
    required: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(part in stripped for part in ("/", "\\", "..")):
            raise ValueError("package name must be a simple identifier")
        return stripped


class OctaveInputAssetSpec(BaseModel):
    source_path: str
    target_name: str | None = None
    kind: OctaveInputKind = "data"
    variable_name: str | None = None
    load_method: str | None = None
    unit: str | None = None
    uncertainty: float | None = None
    sha256: str | None = None


class OctaveToleranceSpec(BaseModel):
    expected_value: float | list[float] | None = None
    atol: float = 1e-8
    rtol: float = 1e-6
    allow_nan: bool = False
    allow_inf: bool = False

    @field_validator("atol", "rtol")
    @classmethod
    def validate_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("tolerances must be non-negative")
        return value


class OctaveInvariantSpec(BaseModel):
    expression: str
    description: str
    tolerance: float = 1e-10


class OctaveOutputSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    kind: OctaveOutputKind = "variable"
    variable_name: str | None = None
    file_name: str | None = None
    required: bool = True
    shape: list[int] | None = None
    dtype: str | None = None
    tolerance: OctaveToleranceSpec | None = None
    output_schema: dict[str, Any] = Field(default_factory=dict, alias="schema")
    unit: str | None = None
    uncertainty: float | None = None
    invariants: list[OctaveInvariantSpec] = Field(default_factory=list)

    @computed_field
    @property
    def metric_key(self) -> str:
        return self.variable_name or self.name

    @model_validator(mode="after")
    def validate_reference(self) -> "OctaveOutputSpec":
        if self.kind == "variable" and not (self.variable_name or self.name):
            raise ValueError("variable outputs require variable_name or name")
        if self.kind != "variable" and not self.file_name:
            raise ValueError("file outputs require file_name")
        return self


class OctaveExperimentSpec(BaseModel):
    task_id: str
    family: OctaveExperimentFamily = "script_run"
    executable: OctaveExecutableSpec = Field(default_factory=OctaveExecutableSpec)
    script: OctaveScriptSpec
    workspace: OctaveWorkspaceSpec | None = None
    packages: list[OctavePackageSpec] = Field(default_factory=list)
    inputs: list[OctaveInputAssetSpec] = Field(default_factory=list)
    expected_outputs: list[OctaveOutputSpec] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(part in stripped for part in ("/", "\\", "..")):
            raise ValueError("task_id must be a simple identifier")
        return stripped

    @model_validator(mode="after")
    def validate_outputs(self) -> "OctaveExperimentSpec":
        if not self.expected_outputs:
            raise ValueError("Octave tasks must declare expected_outputs")
        return self


class OctaveExecutionParams(BaseModel):
    argv: list[str] = Field(default_factory=list)
    workspace_dir: str
    timeout_seconds: int = 300
    output_directory: str = "outputs"
    status_file: str = "mhe_status.txt"
    environment: dict[str, str] = Field(default_factory=dict)


class OctaveRunPlan(BaseModel):
    plan_id: str
    task_id: str
    run_id: str
    executable: OctaveExecutableSpec
    wrapper_name: str = "mhe_wrapper.m"
    wrapper_source: str
    workspace_dir: str
    input_assets: list[OctaveInputAssetSpec] = Field(default_factory=list)
    expected_outputs: list[OctaveOutputSpec] = Field(default_factory=list)
    packages: list[OctavePackageSpec] = Field(default_factory=list)
    execution_params: OctaveExecutionParams
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def experiment_ref(self) -> str:
        return self.task_id

    @computed_field
    @property
    def target_backend(self) -> str:
        return self.executable.binary_name


class OctavePackageFact(BaseModel):
    name: str
    version: str | None = None
    available: bool = False
    required: bool = True


class OctaveEnvironmentReport(BaseModel):
    task_id: str
    available: bool = False
    status: str = "unknown"
    binary_path: str | None = None
    version: str | None = None
    minimum_version: str | None = None
    workspace_writable: bool = False
    packages: list[OctavePackageFact] = Field(default_factory=list)
    blas_lapack: dict[str, Any] = Field(default_factory=dict)
    graphics_backend: str | None = None
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    missing_packages: list[str] = Field(default_factory=list)
    prerequisite_errors: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False


class OctaveWarning(BaseModel):
    message: str
    severity: OctaveWarningSeverity = "suspicious"
    source: str | None = None


class OctaveRunArtifact(BaseModel):
    artifact_id: str
    run_id: str
    task_id: str
    plan_ref: str
    status: OctaveRunArtifactStatus
    return_code: int | None = None
    terminal_error_type: str | None = None
    command: list[str] = Field(default_factory=list)
    working_directory: str
    wrapper_files: list[str] = Field(default_factory=list)
    input_files: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
    figure_files: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    stdout_path: str | None = None
    stderr_path: str | None = None
    status_path: str | None = None
    raw_output_path: str | None = None
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    parsed_outputs: dict[str, Any] = Field(default_factory=dict)
    output_metadata: dict[str, dict[str, Any]] = Field(default_factory=dict)
    warnings: list[OctaveWarning] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    error_message: str | None = None

    def numeric_value(self, key: str) -> float | None:
        value = self.summary_metrics.get(key, self.parsed_outputs.get(key))
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None


class OctaveValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool = False
    status: OctaveValidationStatus = OctaveValidationStatus.RUNTIME_FAILED
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | int | str | bool] = Field(default_factory=dict)
    issues: list[ValidationIssue] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    numeric_metrics: dict[str, float | int | bool] = Field(default_factory=dict)
    package_facts: dict[str, str | None] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    governance_state: OctaveGovernanceState = "defer"

    @computed_field
    @property
    def run_id(self) -> str:
        return self.artifact_ref

    @computed_field
    @property
    def blocks_promotion(self) -> bool:
        return any(issue.blocks_promotion for issue in self.issues)


class OctaveEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning"] = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class OctaveEvidenceBundle(BaseModel):
    bundle_id: str
    task_id: str
    run_id: str | None = None
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    environment: OctaveEnvironmentReport | None = None
    plan: OctaveRunPlan | None = None
    artifact: OctaveRunArtifact | None = None
    validation: OctaveValidationReport | None = None
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[OctaveEvidenceWarning] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    governance_state: OctaveGovernanceState = "defer"
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OctavePolicyReport(BaseModel):
    passed: bool
    decision: Literal["allow", "defer", "reject"]
    governance_state: OctaveGovernanceState
    reason: str
    warnings: list[OctaveEvidenceWarning] = Field(default_factory=list)
    gates: list[GateResult] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class OctaveStudyAxis(BaseModel):
    name: str | None = None
    parameter_path: str | None = None
    values: list[Any] = Field(default_factory=list)
    range: tuple[float, float] | None = None
    step: float | None = None

    @computed_field
    @property
    def path(self) -> str:
        return self.parameter_path or self.name or ""

    @model_validator(mode="after")
    def validate_axis(self) -> "OctaveStudyAxis":
        if not self.path:
            raise ValueError("OctaveStudyAxis requires name or parameter_path")
        if not self.values and self.range is None:
            raise ValueError("OctaveStudyAxis requires values or range")
        if self.step is not None and self.step <= 0:
            raise ValueError("OctaveStudyAxis step must be positive")
        return self


class OctaveStudySpec(BaseModel):
    study_id: str
    task_id: str | None = None
    task_template: OctaveExperimentSpec
    strategy: OctaveStudyStrategy = "grid"
    axes: list[OctaveStudyAxis] = Field(default_factory=list)
    objective: str = "validation_score"
    objective_metric: str | None = None
    goal: Literal["minimize", "maximize"] = "minimize"
    max_trials: int | None = None

    @computed_field
    @property
    def base_task(self) -> OctaveExperimentSpec:
        return self.task_template

    @computed_field
    @property
    def resolved_task_id(self) -> str:
        return self.task_id or self.task_template.task_id

    @computed_field
    @property
    def resolved_objective_metric(self) -> str:
        return self.objective_metric or self.objective


class OctaveStudyTrial(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    parameter_snapshot: dict[str, Any] = Field(default_factory=dict)
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    score: float | None = None
    metric_value: float | None = None
    status: OctaveValidationStatus | None = None
    passed: bool = False
    evidence_bundle: OctaveEvidenceBundle | None = None
    policy_report: OctavePolicyReport | None = None
    messages: list[str] = Field(default_factory=list)


class OctaveStudyReport(BaseModel):
    study_id: str
    task_id: str | None = None
    trials: list[OctaveStudyTrial] = Field(default_factory=list)
    best_trial_id: str | None = None
    recommended_parameters: dict[str, Any] | None = None
    convergence_analysis: dict[str, Any] = Field(default_factory=dict)
    convergence_evidence_refs: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
