from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from metaharness.core.models import ValidationIssue
from metaharness_ext.boutpp.types import (
    BoutPPLauncherMode,
    BoutPPPolicyDecision,
    BoutPPPostprocessStatus,
    BoutPPRestartMode,
    BoutPPRunStatus,
    BoutPPStudyGoal,
    BoutPPValidationStatus,
)

BoutPPOptionValue = bool | int | float | str


class BoutPPMpiSpec(BaseModel):
    launcher_mode: BoutPPLauncherMode = "mpi"
    launcher: str = "mpiexec"
    processes: int = 1
    extra_args: list[str] = Field(default_factory=list)

    @field_validator("processes")
    @classmethod
    def validate_processes(cls, value: int) -> int:
        if value < 1:
            raise ValueError("processes must be >= 1")
        return value

    @model_validator(mode="after")
    def validate_launcher(self) -> "BoutPPMpiSpec":
        if self.launcher_mode == "mpi" and not self.launcher.strip():
            raise ValueError("MPI launcher is required when launcher_mode='mpi'")
        return self


class BoutPPRestartSpec(BaseModel):
    mode: BoutPPRestartMode = "fresh"

    @computed_field
    @property
    def argv_tokens(self) -> list[str]:
        if self.mode == "restart":
            return ["restart"]
        if self.mode == "restart_append":
            return ["restart", "append"]
        return []


class BoutPPOutputSpec(BaseModel):
    data_dir: str = "data"
    settings_file: str = "BOUT.settings"
    log_glob: str = "BOUT.log.*"
    dump_glob: str = "BOUT.dmp.*"
    restart_glob: str = "BOUT.restart.*"
    require_settings: bool = True
    require_logs: bool = True
    require_dumps: bool = False
    require_restarts: bool = False

    @field_validator("data_dir", "settings_file", "log_glob", "dump_glob", "restart_glob")
    @classmethod
    def validate_simple_path(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or ".." in stripped or stripped.startswith("/"):
            raise ValueError("path fields must be non-empty relative paths")
        return stripped


class BoutPPValidationSpec(BaseModel):
    required_variables: list[str] = Field(default_factory=list)
    metric_thresholds: dict[str, float] = Field(default_factory=dict)
    require_successful_return_code: bool = True


class BoutPPProblemSpec(BaseModel):
    task_id: str
    case_name: str = "conduction"
    executable: str = "conduction"
    source_case_dir: str | None = None
    grid_file: str | None = None
    top_level_options: dict[str, BoutPPOptionValue] = Field(default_factory=dict)
    options: dict[str, dict[str, BoutPPOptionValue]] = Field(default_factory=dict)
    cli_overrides: list[str] = Field(default_factory=list)
    mpi: BoutPPMpiSpec = Field(default_factory=BoutPPMpiSpec)
    restart: BoutPPRestartSpec = Field(default_factory=BoutPPRestartSpec)
    output: BoutPPOutputSpec = Field(default_factory=BoutPPOutputSpec)
    validation: BoutPPValidationSpec = Field(default_factory=BoutPPValidationSpec)
    timeout_seconds: int = 300
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("task_id")
    @classmethod
    def validate_task_id(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or "/" in stripped or "\\" in stripped or ".." in stripped:
            raise ValueError("task_id must be a simple identifier")
        return stripped

    @field_validator("case_name", "executable")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @field_validator("timeout_seconds")
    @classmethod
    def validate_timeout(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("timeout_seconds must be positive")
        return value

    @field_validator("cli_overrides")
    @classmethod
    def validate_cli_overrides(cls, value: list[str]) -> list[str]:
        for item in value:
            if not item.strip() or " =" in item or "= " in item:
                raise ValueError("BOUT++ CLI overrides must be non-empty and use key=value")
        return value


class BoutPPEnvironmentReport(BaseModel):
    task_id: str
    available: bool = False
    status: str = "unknown"
    boutpp_root: str | None = None
    boutpp_build_root: str | None = None
    executable_path: str | None = None
    mpi_launcher: str | None = None
    cmake_path: str | None = None
    nc_config_path: str | None = None
    bout_config_path: str | None = None
    python_version: str | None = None
    optional_python_readers: dict[str, bool] = Field(default_factory=dict)
    missing_prerequisites: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False


class BoutPPRunPlan(BaseModel):
    plan_id: str
    task_id: str
    run_id: str
    spec: BoutPPProblemSpec
    workspace_dir: str
    data_dir: str
    bout_inp_content: str
    command: list[str]
    expected_settings_path: str
    expected_log_glob: str
    expected_dump_glob: str
    expected_restart_glob: str
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    promotion_metadata: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def experiment_ref(self) -> str:
        return self.task_id


class BoutPPRunArtifact(BaseModel):
    artifact_id: str
    run_id: str
    task_id: str
    plan_ref: str
    status: BoutPPRunStatus = "unavailable"
    return_code: int | None = None
    error_message: str | None = None
    stdout_excerpt: str | None = None
    stderr_excerpt: str | None = None
    workspace_dir: str | None = None
    data_dir: str | None = None
    settings_file: str | None = None
    log_files: list[str] = Field(default_factory=list)
    dump_files: list[str] = Field(default_factory=list)
    restart_files: list[str] = Field(default_factory=list)
    missing_artifacts: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class BoutPPPostprocessReport(BaseModel):
    report_id: str
    task_id: str
    artifact_ref: str
    status: BoutPPPostprocessStatus = "unavailable"
    log_files: list[str] = Field(default_factory=list)
    settings_file: str | None = None
    dump_files: list[str] = Field(default_factory=list)
    restart_files: list[str] = Field(default_factory=list)
    variable_names: list[str] = Field(default_factory=list)
    settings_summary: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error_message: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)


class BoutPPValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    postprocess_ref: str | None = None
    passed: bool = False
    status: BoutPPValidationStatus = BoutPPValidationStatus.RUNTIME_FAILED
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, Any] = Field(default_factory=dict)
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


class BoutPPEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: str = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class BoutPPEvidenceBundle(BaseModel):
    bundle_id: str
    task_id: str
    run_id: str | None = None
    plan_ref: str | None = None
    artifact_ref: str | None = None
    postprocess_ref: str | None = None
    validation_ref: str | None = None
    environment: BoutPPEnvironmentReport | None = None
    plan: BoutPPRunPlan | None = None
    artifact: BoutPPRunArtifact | None = None
    postprocess: BoutPPPostprocessReport | None = None
    validation: BoutPPValidationReport | None = None
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    warnings: list[BoutPPEvidenceWarning] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BoutPPPolicyReport(BaseModel):
    passed: bool
    decision: BoutPPPolicyDecision
    reason: str
    warnings: list[BoutPPEvidenceWarning] = Field(default_factory=list)
    gates: list[dict[str, Any]] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class BoutPPStudyAxis(BaseModel):
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


class BoutPPStudySpec(BaseModel):
    study_id: str
    task_template: BoutPPProblemSpec
    axes: list[BoutPPStudyAxis] = Field(default_factory=list)
    objective: str = "runtime_seconds"
    goal: BoutPPStudyGoal = "minimize"
    max_trials: int | None = None

    @computed_field
    @property
    def resolved_task_id(self) -> str:
        return self.task_template.task_id


class BoutPPStudyTrial(BaseModel):
    trial_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    plan_ref: str | None = None
    artifact_ref: str | None = None
    postprocess_ref: str | None = None
    validation_ref: str | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class BoutPPStudyReport(BaseModel):
    study_id: str
    task_id: str | None = None
    trials: list[BoutPPStudyTrial] = Field(default_factory=list)
    best_trial_id: str | None = None
    recommended_parameters: dict[str, Any] | None = None
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
