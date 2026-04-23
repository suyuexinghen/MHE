from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

DeepMDApplicationFamily = Literal["deepmd_train", "dpgen_run"]
DeepMDExecutionMode = Literal[
    "train",
    "freeze",
    "test",
    "compress",
    "model_devi",
    "neighbor_stat",
    "dpgen_run",
]
DeepMDRunStatus = Literal["planned", "completed", "failed", "unavailable"]
DPGenStageName = Literal["00.train", "01.model_devi", "02.fp"]


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
            if not system_paths and not self.dataset.train_systems and not self.dataset.validation_systems:
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
    batch_type: str = "shell"
    context_type: str = "local"
    local_root: str = "."
    remote_root: str | None = None
    python_path: str | None = None
    command: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_roots(self) -> "DPGenMachineSpec":
        if not self.local_root:
            raise ValueError("local_root must not be empty")
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


class DeepMDEnvironmentReport(BaseModel):
    dp_available: bool
    python_available: bool
    required_paths_present: bool
    messages: list[str] = Field(default_factory=list)


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
    expected_logs: list[str] = Field(default_factory=list)
    dataset_paths: list[str] = Field(default_factory=list)
    input_json: dict[str, Any] = Field(default_factory=dict)
    param_json: dict[str, Any] = Field(default_factory=dict)
    machine_json: dict[str, Any] = Field(default_factory=dict)
    workspace_sources: list[str] = Field(default_factory=list)
    workspace_inline_files: dict[str, str] = Field(default_factory=dict)
    executable: DeepMDExecutableSpec
    mode_inputs: DeepMDModeInputSpec = Field(default_factory=DeepMDModeInputSpec)


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
        "trained",
        "frozen",
        "tested",
        "compressed",
        "model_devi_computed",
        "neighbor_stat_computed",
        "baseline_success",
        "run_failed",
        "runtime_failed",
        "validation_failed",
    ]
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
