from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

AbacusApplicationFamily = Literal["scf", "nscf", "relax", "md"]
AbacusBasisType = Literal["pw", "lcao"]
AbacusLauncher = Literal["direct", "mpirun", "mpiexec", "srun"]
AbacusESolverType = Literal["ksdft", "dp"]
AbacusValidationStatus = Literal[
    "environment_invalid",
    "input_invalid",
    "runtime_failed",
    "validation_failed",
    "executed",
]


class AbacusExecutableSpec(BaseModel):
    binary_name: str = "abacus"
    launcher: AbacusLauncher = "direct"
    timeout_seconds: int | None = None
    process_count: int | None = None
    launcher_args: list[str] = Field(default_factory=list)

    @field_validator("binary_name")
    @classmethod
    def validate_binary_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped or " " in stripped:
            raise ValueError("binary_name must be a non-empty executable name or path")
        return stripped

    @field_validator("launcher_args")
    @classmethod
    def validate_launcher_args(cls, value: list[str]) -> list[str]:
        for arg in value:
            if not arg or not arg.strip():
                raise ValueError("launcher_args must not contain empty strings")
        return [arg.strip() for arg in value]


class AbacusStructureSpec(BaseModel):
    content: str = ""
    format: Literal["stru"] = "stru"


class AbacusKPointSpec(BaseModel):
    content: str = ""
    format: Literal["kpt"] = "kpt"


class AbacusScfSpec(BaseModel):
    task_id: str
    application_family: Literal["scf"] = "scf"
    executable: AbacusExecutableSpec = Field(default_factory=AbacusExecutableSpec)
    structure: AbacusStructureSpec = Field(default_factory=AbacusStructureSpec)
    kpoints: AbacusKPointSpec | None = None
    basis_type: AbacusBasisType = "pw"
    esolver_type: AbacusESolverType = "ksdft"
    calculation: Literal["scf"] = "scf"
    suffix: str = "ABACUS"
    params: dict[str, Any] = Field(default_factory=dict)
    pseudo_files: list[str] = Field(default_factory=list)
    orbital_files: list[str] = Field(default_factory=list)
    pot_file: str | None = None
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None

    @model_validator(mode="after")
    def validate_combination(self) -> "AbacusScfSpec":
        if self.basis_type not in {"pw", "lcao"}:
            raise ValueError(f"unsupported basis_type: {self.basis_type}")
        if self.esolver_type not in {"ksdft", "dp"}:
            raise ValueError(f"unsupported esolver_type: {self.esolver_type}")
        if self.esolver_type == "dp":
            raise ValueError("esolver_type=dp is not supported in Phase 0 (SCF baseline)")
        if self.basis_type == "lcao" and not self.orbital_files:
            raise ValueError("basis_type=lcao requires orbital_files")
        return self


class AbacusNscfSpec(BaseModel):
    task_id: str
    application_family: Literal["nscf"] = "nscf"
    executable: AbacusExecutableSpec = Field(default_factory=AbacusExecutableSpec)
    structure: AbacusStructureSpec = Field(default_factory=AbacusStructureSpec)
    kpoints: AbacusKPointSpec
    basis_type: AbacusBasisType = "pw"
    esolver_type: AbacusESolverType = "ksdft"
    calculation: Literal["nscf"] = "nscf"
    suffix: str = "ABACUS"
    params: dict[str, Any] = Field(default_factory=dict)
    pseudo_files: list[str] = Field(default_factory=list)
    orbital_files: list[str] = Field(default_factory=list)
    pot_file: str | None = None
    charge_density_path: str | None = None
    restart_file_path: str | None = None
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None

    @model_validator(mode="after")
    def validate_combination(self) -> "AbacusNscfSpec":
        if self.basis_type not in {"pw", "lcao"}:
            raise ValueError(f"unsupported basis_type: {self.basis_type}")
        if self.esolver_type not in {"ksdft", "dp"}:
            raise ValueError(f"unsupported esolver_type: {self.esolver_type}")
        if self.esolver_type == "dp":
            raise ValueError("esolver_type=dp is not supported in Phase 1 (NSCF baseline)")
        if self.basis_type == "lcao" and not self.orbital_files:
            raise ValueError("basis_type=lcao requires orbital_files")
        if self.charge_density_path is None and self.restart_file_path is None:
            raise ValueError("nscf requires charge_density_path or restart_file_path")
        return self


class AbacusRelaxSpec(BaseModel):
    task_id: str
    application_family: Literal["relax"] = "relax"
    executable: AbacusExecutableSpec = Field(default_factory=AbacusExecutableSpec)
    structure: AbacusStructureSpec = Field(default_factory=AbacusStructureSpec)
    kpoints: AbacusKPointSpec | None = None
    basis_type: AbacusBasisType = "pw"
    esolver_type: AbacusESolverType = "ksdft"
    calculation: Literal["relax"] = "relax"
    suffix: str = "ABACUS"
    params: dict[str, Any] = Field(default_factory=dict)
    pseudo_files: list[str] = Field(default_factory=list)
    orbital_files: list[str] = Field(default_factory=list)
    pot_file: str | None = None
    relax_controls: dict[str, Any] = Field(default_factory=dict)
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None

    @model_validator(mode="after")
    def validate_combination(self) -> "AbacusRelaxSpec":
        if self.basis_type not in {"pw", "lcao"}:
            raise ValueError(f"unsupported basis_type: {self.basis_type}")
        if self.esolver_type not in {"ksdft", "dp"}:
            raise ValueError(f"unsupported esolver_type: {self.esolver_type}")
        if self.esolver_type == "dp":
            raise ValueError("esolver_type=dp is not supported in Phase 1 (relax baseline)")
        if self.basis_type == "lcao" and not self.orbital_files:
            raise ValueError("basis_type=lcao requires orbital_files")
        return self


class AbacusMdSpec(BaseModel):
    task_id: str
    application_family: Literal["md"] = "md"
    executable: AbacusExecutableSpec = Field(default_factory=AbacusExecutableSpec)
    structure: AbacusStructureSpec = Field(default_factory=AbacusStructureSpec)
    kpoints: AbacusKPointSpec | None = None
    basis_type: AbacusBasisType = "pw"
    esolver_type: AbacusESolverType = "ksdft"
    calculation: Literal["md"] = "md"
    suffix: str = "ABACUS"
    params: dict[str, Any] = Field(default_factory=dict)
    pseudo_files: list[str] = Field(default_factory=list)
    orbital_files: list[str] = Field(default_factory=list)
    pot_file: str | None = None
    required_paths: list[str] = Field(default_factory=list)
    working_directory: str | None = None

    @model_validator(mode="after")
    def validate_combination(self) -> "AbacusMdSpec":
        if self.basis_type not in {"pw", "lcao"}:
            raise ValueError(f"unsupported basis_type: {self.basis_type}")
        if self.esolver_type not in {"ksdft", "dp"}:
            raise ValueError(f"unsupported esolver_type: {self.esolver_type}")
        if self.esolver_type == "dp":
            raise ValueError("esolver_type=dp is not supported in Phase 2 (MD baseline)")
        if self.basis_type == "lcao":
            raise ValueError("basis_type=lcao is not supported in Phase 2 (MD baseline)")
        return self


AbacusExperimentSpec = AbacusScfSpec | AbacusNscfSpec | AbacusRelaxSpec | AbacusMdSpec


class AbacusEnvironmentReport(BaseModel):
    abacus_available: bool = False
    abacus_path: str | None = None
    version_probe_supported: bool = False
    version_probe_succeeded: bool = False
    version_output: str | None = None
    info_probe_supported: bool = False
    info_probe_succeeded: bool = False
    info_output: str | None = None
    check_input_probe_supported: bool = False
    check_input_probe_succeeded: bool = False
    check_input_output: str | None = None
    requested_launcher: str | None = None
    launcher_available: bool = False
    launcher_path: str | None = None
    deeppmd_support_detected: bool = False
    gpu_support_detected: bool = False
    required_paths_present: bool = False
    messages: list[str] = Field(default_factory=list)


class AbacusRunPlan(BaseModel):
    task_id: str
    run_id: str
    application_family: AbacusApplicationFamily = "scf"
    command: list[str] = Field(default_factory=list)
    working_directory: str
    input_content: str = ""
    structure_content: str = ""
    kpoints_content: str | None = None
    suffix: str = "ABACUS"
    output_root: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)
    required_runtime_paths: list[str] = Field(default_factory=list)
    executable: AbacusExecutableSpec = Field(default_factory=AbacusExecutableSpec)


class AbacusRunArtifact(BaseModel):
    task_id: str
    run_id: str
    application_family: AbacusApplicationFamily = "scf"
    command: list[str] = Field(default_factory=list)
    return_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    prepared_inputs: list[str] = Field(default_factory=list)
    output_root: str | None = None
    output_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    structure_files: list[str] = Field(default_factory=list)
    working_directory: str
    status: Literal["planned", "completed", "failed", "unavailable"] = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)


class AbacusValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool = False
    status: AbacusValidationStatus = "validation_failed"
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
