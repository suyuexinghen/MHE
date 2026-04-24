from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from metaharness.core.graph_versions import CandidateRecord
from metaharness.core.models import ScoredEvidence, ValidationIssue, ValidationReport
from metaharness.safety.gates import GateResult

DeepMDApplicationFamily = Literal["deepmd_train", "dpgen_run", "dpgen_simplify", "dpgen_autotest"]
DeepMDStudyHandoffPolicy = Literal["none", "all", "recommended"]
DeepMDExecutionMode = Literal[
    "train",
    "freeze",
    "test",
    "compress",
    "model_devi",
    "neighbor_stat",
    "dpgen_run",
    "dpgen_simplify",
    "dpgen_autotest",
]
DeepMDRunStatus = Literal["planned", "completed", "failed", "unavailable"]
DPGenStageName = Literal["00.train", "01.model_devi", "02.fp"]
DPGenBatchType = Literal["shell", "slurm", "pbs", "lsf"]
DPGenContextType = Literal["local", "ssh"]


class DeepMDExecutableSpec(BaseModel):
    binary_name: str = "dp"
    launcher: Literal["direct"] = "direct"
    execution_mode: DeepMDExecutionMode
    timeout_seconds: int | None = None


class DeepMDDatasetSpec(BaseModel):
    dataset_id: str | None = None
    source_format: Literal["deepmd_npy"] = "deepmd_npy"
    train_systems: list[str] = Field(default_factory=list)
    validation_systems: list[str] = Field(default_factory=list)
    type_map: list[str] = Field(default_factory=list)
    labels_present: list[str] = Field(default_factory=list)
    periodic: bool = True

    @model_validator(mode="after")
    def validate_systems(self) -> "DeepMDDatasetSpec":
        if not self.type_map:
            raise ValueError("type_map must not be empty")
        return self


class DeepMDDescriptorSpec(BaseModel):
    descriptor_type: Literal["se_e2_a"]
    rcut: float
    rcut_smth: float
    sel: list[int] = Field(default_factory=list)
    neuron: list[int] = Field(default_factory=list)
    seed: int | None = None

    @model_validator(mode="after")
    def validate_descriptor(self) -> "DeepMDDescriptorSpec":
        if self.rcut <= 0:
            raise ValueError("rcut must be positive")
        if self.rcut_smth <= 0 or self.rcut_smth > self.rcut:
            raise ValueError("rcut_smth must be positive and <= rcut")
        if not self.sel:
            raise ValueError("sel must not be empty")
        return self


class DeepMDFittingNetSpec(BaseModel):
    neuron: list[int] = Field(default_factory=list)
    resnet_dt: bool = False
    seed: int | None = None

    @model_validator(mode="after")
    def validate_neuron(self) -> "DeepMDFittingNetSpec":
        if not self.neuron:
            raise ValueError("neuron must not be empty")
        return self


class DeepMDModeInputSpec(BaseModel):
    model_path: str | None = None
    output_model_path: str | None = None
    system_path: str | None = None
    system_paths: list[str] = Field(default_factory=list)
    sample_count: int | None = None


class DeepMDTrainSpec(BaseModel):
    task_id: str
    application_family: DeepMDApplicationFamily = "deepmd_train"
    executable: DeepMDExecutableSpec
    dataset: DeepMDDatasetSpec
    type_map: list[str] = Field(default_factory=list)
    descriptor: DeepMDDescriptorSpec
    fitting_net: DeepMDFittingNetSpec
    training: dict[str, Any] = Field(default_factory=dict)
    learning_rate: dict[str, Any] = Field(default_factory=dict)
    loss: dict[str, Any] = Field(default_factory=dict)
    working_directory: str | None = None
    mode_inputs: DeepMDModeInputSpec = Field(default_factory=DeepMDModeInputSpec)

    @model_validator(mode="after")
    def validate_type_map(self) -> "DeepMDTrainSpec":
        if self.type_map and self.type_map != self.dataset.type_map:
            raise ValueError("spec type_map must match dataset type_map when provided")
        if not self.type_map:
            self.type_map = list(self.dataset.type_map)

        mode = self.executable.execution_mode
        system_paths = [
            *self.mode_inputs.system_paths,
            *([self.mode_inputs.system_path] if self.mode_inputs.system_path else []),
        ]
        if mode == "train" and not self.dataset.train_systems:
            raise ValueError("train mode requires dataset.train_systems")
        if mode == "compress":
            if not self.mode_inputs.model_path:
                raise ValueError("compress mode requires mode_inputs.model_path")
            if self.mode_inputs.output_model_path is None:
                self.mode_inputs.output_model_path = "compressed_model.pb"
        elif mode == "test":
            if not self.mode_inputs.model_path:
                self.mode_inputs.model_path = "frozen_model.pb"
            if (
                not system_paths
                and not self.dataset.train_systems
                and not self.dataset.validation_systems
            ):
                raise ValueError("test mode requires at least one dataset path")
        elif mode == "model_devi":
            if not self.mode_inputs.model_path:
                raise ValueError("model_devi mode requires mode_inputs.model_path")
            if not system_paths:
                raise ValueError("model_devi mode requires at least one system path")
        elif mode == "neighbor_stat":
            if not system_paths:
                raise ValueError("neighbor_stat mode requires at least one system path")
        return self


class DPGenMachineSpec(BaseModel):
    batch_type: DPGenBatchType = "shell"
    context_type: DPGenContextType = "local"
    local_root: str = "."
    remote_root: str | None = None
    python_path: str | None = None
    command: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @field_validator("local_root", mode="before")
    @classmethod
    def validate_required_strings(cls, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError("machine fields must be strings")
        stripped = value.strip()
        if not stripped:
            raise ValueError("machine fields must not be empty")
        return stripped

    @field_validator("remote_root", "python_path", "command", mode="before")
    @classmethod
    def normalize_optional_strings(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("optional machine fields must be strings")
        stripped = value.strip()
        return stripped or None

    @field_validator("extra")
    @classmethod
    def validate_extra(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("machine.extra must be a dictionary")
        return value

    @model_validator(mode="after")
    def validate_roots(self) -> "DPGenMachineSpec":
        if self.context_type == "local" and self.remote_root is not None:
            raise ValueError("remote_root is only allowed when context_type is not 'local'")
        if self.batch_type == "shell" and self.command is not None:
            raise ValueError("command is only allowed when batch_type is not 'shell'")
        return self


class DPGenRunSpec(BaseModel):
    task_id: str
    application_family: DeepMDApplicationFamily = "dpgen_run"
    executable: DeepMDExecutableSpec = Field(
        default_factory=lambda: DeepMDExecutableSpec(
            binary_name="dpgen", execution_mode="dpgen_run"
        )
    )
    param: dict[str, Any] = Field(default_factory=dict)
    machine: DPGenMachineSpec = Field(default_factory=DPGenMachineSpec)
    working_directory: str | None = None
    workspace_files: list[str] = Field(default_factory=list)
    workspace_inline_files: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dpgen_run(self) -> "DPGenRunSpec":
        if self.executable.execution_mode != "dpgen_run":
            raise ValueError("DPGenRunSpec requires executable.execution_mode='dpgen_run'")
        if not self.param:
            raise ValueError("param must not be empty")
        return self


class DPGenSimplifySpec(BaseModel):
    task_id: str
    application_family: DeepMDApplicationFamily = "dpgen_simplify"
    executable: DeepMDExecutableSpec = Field(
        default_factory=lambda: DeepMDExecutableSpec(
            binary_name="dpgen", execution_mode="dpgen_simplify"
        )
    )
    param: dict[str, Any] = Field(default_factory=dict)
    machine: DPGenMachineSpec = Field(default_factory=DPGenMachineSpec)
    training_init_model: list[str] = Field(default_factory=list)
    trainable_mask: list[bool] = Field(default_factory=list)
    relabeling: dict[str, Any] = Field(default_factory=dict)
    working_directory: str | None = None
    workspace_files: list[str] = Field(default_factory=list)
    workspace_inline_files: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dpgen_simplify(self) -> "DPGenSimplifySpec":
        if self.executable.execution_mode != "dpgen_simplify":
            raise ValueError(
                "DPGenSimplifySpec requires executable.execution_mode='dpgen_simplify'"
            )
        if not self.param:
            raise ValueError("param must not be empty")
        return self


class DPGenAutotestSpec(BaseModel):
    task_id: str
    application_family: DeepMDApplicationFamily = "dpgen_autotest"
    executable: DeepMDExecutableSpec = Field(
        default_factory=lambda: DeepMDExecutableSpec(
            binary_name="dpgen", execution_mode="dpgen_autotest"
        )
    )
    param: dict[str, Any] = Field(default_factory=dict)
    machine: DPGenMachineSpec = Field(default_factory=DPGenMachineSpec)
    properties: list[str] = Field(default_factory=list)
    working_directory: str | None = None
    workspace_files: list[str] = Field(default_factory=list)
    workspace_inline_files: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dpgen_autotest(self) -> "DPGenAutotestSpec":
        if self.executable.execution_mode != "dpgen_autotest":
            raise ValueError(
                "DPGenAutotestSpec requires executable.execution_mode='dpgen_autotest'"
            )
        if not self.param:
            raise ValueError("param must not be empty")
        return self


DeepMDExperimentSpec = DeepMDTrainSpec | DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec


class DeepMDEnvironmentReport(BaseModel):
    application_family: DeepMDApplicationFamily
    execution_mode: DeepMDExecutionMode
    dp_available: bool
    dpgen_available: bool = False
    python_available: bool
    required_paths_present: bool
    workspace_ready: bool = True
    machine_root_ready: bool = True
    remote_root_configured: bool = True
    scheduler_command_configured: bool = True
    machine_spec_valid: bool = True
    dp_probe_supported: bool = False
    dp_probe_succeeded: bool = False
    dp_probe_output: str | None = None
    dpgen_probe_supported: bool = False
    dpgen_probe_succeeded: bool = False
    dpgen_probe_output: str | None = None
    missing_required_paths: list[str] = Field(default_factory=list)
    environment_prerequisites: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    fallback_reason: str | None = None


class DPGenCompiledDocument(BaseModel):
    filename: Literal["param.json", "machine.json"]
    payload: dict[str, Any] = Field(default_factory=dict)


class DeepMDRunPlan(BaseModel):
    task_id: str
    run_id: str
    application_family: DeepMDApplicationFamily = "deepmd_train"
    execution_mode: DeepMDExecutionMode
    command: list[str] = Field(default_factory=list)
    working_directory: str
    input_json_path: str | None = None
    param_json_path: str | None = None
    machine_json_path: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    expected_diagnostics: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)
    dataset_paths: list[str] = Field(default_factory=list)
    input_json: dict[str, Any] = Field(default_factory=dict)
    param_json: dict[str, Any] = Field(default_factory=dict)
    machine_json: dict[str, Any] = Field(default_factory=dict)
    workspace_sources: list[str] = Field(default_factory=list)
    workspace_inline_files: dict[str, str] = Field(default_factory=dict)
    executable: DeepMDExecutableSpec
    mode_inputs: DeepMDModeInputSpec = Field(default_factory=DeepMDModeInputSpec)
    properties: list[str] = Field(default_factory=list)


class DPGenIterationSummary(BaseModel):
    iteration_id: str
    path: str
    train_path: str | None = None
    model_devi_path: str | None = None
    fp_path: str | None = None
    candidate_count: int = 0
    accurate_count: int = 0
    failed_count: int = 0


class DPGenIterationCollection(BaseModel):
    record_path: str | None = None
    iterations: list[DPGenIterationSummary] = Field(default_factory=list)
    candidate_count: int = 0
    accurate_count: int = 0
    failed_count: int = 0
    messages: list[str] = Field(default_factory=list)


class DeepMDDiagnosticSummary(BaseModel):
    learning_curve_path: str | None = None
    train_log_path: str | None = None
    last_step: int | None = None
    rmse_e_trn: float | None = None
    rmse_f_trn: float | None = None
    rmse_e_val: float | None = None
    rmse_f_val: float | None = None
    lcurve_metrics: dict[str, float] = Field(default_factory=dict)
    test_metrics: dict[str, float] = Field(default_factory=dict)
    compressed_model_path: str | None = None
    model_devi_metrics: dict[str, float] = Field(default_factory=dict)
    neighbor_stat_metrics: dict[str, float] = Field(default_factory=dict)
    log_clues: dict[str, str] = Field(default_factory=dict)
    dpgen_collection: DPGenIterationCollection | None = None
    autotest_properties: dict[str, dict[str, float]] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)


class DeepMDRunArtifact(BaseModel):
    task_id: str
    run_id: str
    application_family: DeepMDApplicationFamily = "deepmd_train"
    execution_mode: DeepMDExecutionMode
    command: list[str] = Field(default_factory=list)
    return_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    working_directory: str
    workspace_files: list[str] = Field(default_factory=list)
    checkpoint_files: list[str] = Field(default_factory=list)
    model_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    summary: DeepMDDiagnosticSummary = Field(default_factory=DeepMDDiagnosticSummary)
    status: DeepMDRunStatus = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)


class DeepMDValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool
    status: Literal[
        "environment_invalid",
        "workspace_failed",
        "scheduler_invalid",
        "remote_invalid",
        "machine_invalid",
        "trained",
        "frozen",
        "tested",
        "compressed",
        "model_devi_computed",
        "neighbor_stat_computed",
        "baseline_success",
        "simplify_success",
        "converged",
        "autotest_validated",
        "run_failed",
        "runtime_failed",
        "validation_failed",
    ]
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str | bool] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)
    blocks_promotion: bool = False
    governance_state: Literal["ready", "defer", "blocked"] = "defer"
    scored_evidence: ScoredEvidence | None = None


class DeepMDEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning"] = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class DeepMDEvidenceBundle(BaseModel):
    task_id: str
    run_id: str
    application_family: DeepMDApplicationFamily
    execution_mode: DeepMDExecutionMode
    run: DeepMDRunArtifact
    validation: DeepMDValidationReport | None = None
    summary: DeepMDDiagnosticSummary
    evidence_files: list[str] = Field(default_factory=list)
    warnings: list[DeepMDEvidenceWarning] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DeepMDPolicyReport(BaseModel):
    passed: bool
    decision: Literal["allow", "defer", "reject"]
    reason: str
    warnings: list[DeepMDEvidenceWarning] = Field(default_factory=list)
    gates: list[GateResult] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class DeepMDBaselineReport(BaseModel):
    task: DeepMDExperimentSpec
    environment: DeepMDEnvironmentReport
    plan: DeepMDRunPlan
    run: DeepMDRunArtifact
    validation: DeepMDValidationReport
    evidence_bundle: DeepMDEvidenceBundle
    policy_report: DeepMDPolicyReport
    core_validation_report: ValidationReport
    candidate_record: CandidateRecord


class DeepMDMutationAxis(BaseModel):
    kind: Literal[
        "numb_steps",
        "rcut",
        "rcut_smth",
        "sel",
        "model_devi_f_trust_lo",
        "model_devi_f_trust_hi",
        "relabeling.pick_number",
        "autotest.type",
    ]
    values: list[int | float | str] = Field(default_factory=list)
    label: str | None = None

    @model_validator(mode="after")
    def validate_values(self) -> "DeepMDMutationAxis":
        if not self.values:
            raise ValueError("axis.values must not be empty")
        return self


DeepMDStudyBaseTask = DeepMDTrainSpec | DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec


class DeepMDStudySpec(BaseModel):
    study_id: str
    task_id: str
    base_task: DeepMDStudyBaseTask
    axis: DeepMDMutationAxis
    metric_key: str
    goal: Literal["minimize", "maximize"] = "minimize"
    handoff_policy: DeepMDStudyHandoffPolicy = "none"


class DeepMDStudyTrial(BaseModel):
    trial_id: str
    task_id: str
    axis_kind: str
    axis_value: int | float | str
    mutated_parameters: dict[str, int | float | str] = Field(default_factory=dict)
    run: DeepMDRunArtifact
    validation: DeepMDValidationReport
    evidence_bundle: DeepMDEvidenceBundle | None = None
    policy_report: DeepMDPolicyReport | None = None
    core_validation_report: ValidationReport | None = None
    candidate_record: CandidateRecord | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)


class DeepMDStudyReport(BaseModel):
    study_id: str
    task_id: str
    axis_kind: str
    metric_key: str
    trials: list[DeepMDStudyTrial] = Field(default_factory=list)
    recommended_value: int | float | str | None = None
    recommended_trial_id: str | None = None
    recommended_reason: str | None = None
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)
