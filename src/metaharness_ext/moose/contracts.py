from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from metaharness.core.models import ValidationIssue
from metaharness_ext.moose.types import (
    MooseInputMode,
    MooseOutputKind,
    MooseRunArtifactStatus,
    MooseValidationStatus,
)


class MooseExecutableSpec(BaseModel):
    binary_name: str = "moose-opt"
    timeout_seconds: int = 300
    env: dict[str, str] = Field(default_factory=dict)
    minimum_version: str | None = None
    source_root: str | None = None

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


class MooseWorkspaceSpec(BaseModel):
    working_directory: str | None = None
    output_directory: str = "outputs"
    cleanup: bool = False


class MooseInputSpec(BaseModel):
    mode: MooseInputMode = "inline"
    inline_source: str | None = None
    input_path: str | None = None
    input_filename: str = "input.i"
    extra_args: list[str] = Field(default_factory=list)
    mesh_only: bool = False
    mesh_output_path: str | None = None

    @field_validator("input_filename")
    @classmethod
    def validate_input_filename(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or any(part in stripped for part in ("/", "\\", "..")):
            raise ValueError("input_filename must be a simple file name")
        if not stripped.endswith(".i"):
            raise ValueError("MOOSE input files must use the .i suffix")
        return stripped

    @model_validator(mode="after")
    def validate_source(self) -> "MooseInputSpec":
        if self.mode == "inline" and not self.inline_source:
            raise ValueError("inline mode requires inline_source")
        if self.mode == "file" and not self.input_path:
            raise ValueError("file mode requires input_path")
        return self


class MooseOutputSpec(BaseModel):
    name: str
    kind: MooseOutputKind = "other"
    file_name: str | None = None
    required: bool = True
    description: str | None = None

    @computed_field
    @property
    def resolved_file_name(self) -> str:
        return self.file_name or self.name


class MooseProblemSpec(BaseModel):
    task_id: str
    input: MooseInputSpec
    executable: MooseExecutableSpec = Field(default_factory=MooseExecutableSpec)
    workspace: MooseWorkspaceSpec | None = None
    expected_outputs: list[MooseOutputSpec] = Field(default_factory=list)
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


class MooseEnvironmentReport(BaseModel):
    task_id: str
    available: bool = False
    status: str = "unknown"
    binary_path: str | None = None
    version: str | None = None
    minimum_version: str | None = None
    source_root: str | None = None
    source_tree_detected: bool = False
    workspace_writable: bool = False
    missing_prerequisites: list[str] = Field(default_factory=list)
    prerequisite_errors: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False


class MooseRunPlan(BaseModel):
    plan_id: str
    task_id: str
    run_id: str
    spec: MooseProblemSpec
    workspace_dir: str
    input_filename: str
    input_source: str
    command: list[str]
    expected_outputs: list[MooseOutputSpec] = Field(default_factory=list)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def experiment_ref(self) -> str:
        return self.task_id


class MooseWarning(BaseModel):
    message: str
    severity: str = "suspicious"
    source: str | None = None


class MooseRunArtifact(BaseModel):
    artifact_id: str
    run_id: str
    task_id: str
    plan_ref: str
    status: MooseRunArtifactStatus
    return_code: int | None = None
    terminal_error_type: str | None = None
    error_message: str | None = None
    command: list[str] = Field(default_factory=list)
    working_directory: str
    input_files: list[str] = Field(default_factory=list)
    output_files: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    stdout_path: str | None = None
    stderr_path: str | None = None
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[MooseWarning] = Field(default_factory=list)


class MooseValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool = False
    status: MooseValidationStatus = MooseValidationStatus.RUNTIME_FAILED
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    missing_evidence: list[str] = Field(default_factory=list)
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


class MooseEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class MooseEvidenceBundle(BaseModel):
    bundle_id: str
    task_id: str
    run_id: str | None = None
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    environment: MooseEnvironmentReport | None = None
    plan: MooseRunPlan | None = None
    artifact: MooseRunArtifact | None = None
    validation: MooseValidationReport | None = None
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[MooseEvidenceWarning] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MoosePolicyReport(BaseModel):
    passed: bool
    decision: str
    reason: str
    warnings: list[MooseEvidenceWarning] = Field(default_factory=list)
    gates: list[Any] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class MooseStudyAxis(BaseModel):
    parameter_path: str
    values: list[Any] | None = None
    range: tuple[float, float] | None = None
    step: float | None = None

    @field_validator("parameter_path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("parameter_path must not be empty")
        return stripped


class MooseStudySpec(BaseModel):
    study_id: str
    task_template: MooseProblemSpec
    axes: list[MooseStudyAxis] = Field(default_factory=list)
    objective: str = "output_count"
    goal: str = "maximize"
    max_trials: int | None = None


class MooseStudyTrial(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    plan_ref: str | None = None
    artifact_ref: str | None = None
    validation_ref: str | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class MooseStudyReport(BaseModel):
    study_id: str
    task_id: str | None = None
    trials: list[MooseStudyTrial] = Field(default_factory=list)
    best_trial_id: str | None = None
    recommended_parameters: dict[str, Any] | None = None
    summary_metrics: dict[str, float | int | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
