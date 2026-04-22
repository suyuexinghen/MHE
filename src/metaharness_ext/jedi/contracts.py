from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, field_validator, model_validator

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
    ensemble: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    final: dict[str, Any] = Field(default_factory=dict)
    test: dict[str, Any] = Field(default_factory=dict)
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None

    @model_validator(mode="after")
    def validate_ensemble_paths(self) -> "JediLocalEnsembleDASpec":
        if not self.ensemble_paths:
            raise ValueError("local_ensemble_da requires at least one ensemble path")
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
    binary_path: str | None = None
    launcher_path: str | None = None
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
    working_directory: str
    status: JediRunStatus = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)


class JediValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool
    status: JediValidationStatus
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
