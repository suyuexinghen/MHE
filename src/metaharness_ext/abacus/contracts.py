from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from metaharness.core.models import ScoredEvidence, ValidationIssue

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


def _dedupe_paths(paths: list[str]) -> list[str]:
    return list(dict.fromkeys(path for path in paths if path))


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


class AbacusControlFiles(BaseModel):
    input_name: str = "INPUT"
    input_content: str = ""
    structure_name: str = "STRU"
    structure_content: str = ""
    kpoints_name: str | None = None
    kpoints_content: str | None = None


class AbacusMaterializedControlFiles(BaseModel):
    input_file: str | None = None
    structure_file: str | None = None
    kpoints_file: str | None = None

    def as_list(self) -> list[str]:
        return [path for path in [self.input_file, self.structure_file, self.kpoints_file] if path]


class AbacusRuntimeAssets(BaseModel):
    explicit_required_paths: list[str] = Field(default_factory=list)
    pseudo_files: list[str] = Field(default_factory=list)
    orbital_files: list[str] = Field(default_factory=list)
    restart_inputs: list[str] = Field(default_factory=list)
    charge_density_path: str | None = None
    pot_file: str | None = None

    def all_paths(self) -> list[str]:
        return _dedupe_paths(
            [
                *self.explicit_required_paths,
                *self.pseudo_files,
                *self.orbital_files,
                *self.restart_inputs,
                *([self.charge_density_path] if self.charge_density_path else []),
                *([self.pot_file] if self.pot_file else []),
            ]
        )


class AbacusWorkspaceLayout(BaseModel):
    working_directory: str
    output_root: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None


class AbacusOutputExpectations(BaseModel):
    expected_outputs: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)


class AbacusLifecycleState(BaseModel):
    environment_probed: bool = False
    compiled: bool = False
    workspace_materialized: bool = False
    executed: bool = False
    evidence_discovered: bool = False


class AbacusArtifactGroups(BaseModel):
    output_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    structure_files: list[str] = Field(default_factory=list)


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
        if self.basis_type == "lcao":
            raise ValueError("basis_type=lcao is not supported for MD")
        if self.esolver_type == "dp" and not self.pot_file:
            raise ValueError("esolver_type=dp requires pot_file")
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
    deeppmd_probe_supported: bool = False
    deeppmd_probe_succeeded: bool = False
    deeppmd_support_detected: bool | None = None
    gpu_support_detected: bool | None = None
    required_paths_present: bool = False
    required_path_groups: AbacusRuntimeAssets = Field(default_factory=AbacusRuntimeAssets)
    missing_path_groups: AbacusRuntimeAssets = Field(default_factory=AbacusRuntimeAssets)
    missing_required_paths: list[str] = Field(default_factory=list)
    environment_prerequisites: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class AbacusRunPlan(BaseModel):
    task_id: str
    run_id: str
    application_family: AbacusApplicationFamily = "scf"
    command: list[str] = Field(default_factory=list)
    working_directory: str
    input_content: str = ""
    structure_content: str = ""
    kpoints_content: str | None = None
    control_files: AbacusControlFiles | None = None
    runtime_assets: AbacusRuntimeAssets | None = None
    workspace_layout: AbacusWorkspaceLayout | None = None
    output_expectations: AbacusOutputExpectations | None = None
    lifecycle_state: AbacusLifecycleState = Field(default_factory=AbacusLifecycleState)
    suffix: str = "ABACUS"
    esolver_type: AbacusESolverType = "ksdft"
    pot_file: str | None = None
    environment_prerequisites: list[str] = Field(default_factory=list)
    environment_evidence_refs: list[str] = Field(default_factory=list)
    output_root: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)
    required_runtime_paths: list[str] = Field(default_factory=list)
    executable: AbacusExecutableSpec = Field(default_factory=AbacusExecutableSpec)

    @model_validator(mode="after")
    def align_nested_fields(self) -> "AbacusRunPlan":
        if self.control_files is None:
            self.control_files = AbacusControlFiles(
                input_content=self.input_content,
                structure_content=self.structure_content,
                kpoints_name="KPT" if self.kpoints_content is not None else None,
                kpoints_content=self.kpoints_content,
            )
        if self.runtime_assets is None:
            self.runtime_assets = AbacusRuntimeAssets(
                explicit_required_paths=list(self.required_runtime_paths),
                pot_file=self.pot_file,
            )
        if self.workspace_layout is None:
            self.workspace_layout = AbacusWorkspaceLayout(
                working_directory=self.working_directory,
                output_root=self.output_root,
            )
        if self.output_expectations is None:
            self.output_expectations = AbacusOutputExpectations(
                expected_outputs=list(self.expected_outputs),
                expected_logs=list(self.expected_logs),
            )
        self.input_content = self.control_files.input_content
        self.structure_content = self.control_files.structure_content
        self.kpoints_content = self.control_files.kpoints_content
        self.working_directory = self.workspace_layout.working_directory
        self.output_root = self.workspace_layout.output_root
        self.expected_outputs = list(self.output_expectations.expected_outputs)
        self.expected_logs = list(self.output_expectations.expected_logs)
        self.required_runtime_paths = self.runtime_assets.all_paths()
        self.pot_file = self.runtime_assets.pot_file
        return self


class AbacusRunArtifact(BaseModel):
    task_id: str
    run_id: str
    application_family: AbacusApplicationFamily = "scf"
    command: list[str] = Field(default_factory=list)
    return_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    prepared_inputs: list[str] = Field(default_factory=list)
    control_file_paths: AbacusMaterializedControlFiles | None = None
    workspace_layout: AbacusWorkspaceLayout | None = None
    artifact_groups: AbacusArtifactGroups | None = None
    lifecycle_state: AbacusLifecycleState = Field(default_factory=AbacusLifecycleState)
    output_root: str | None = None
    output_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    structure_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    working_directory: str
    status: Literal["planned", "completed", "failed", "unavailable"] = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def align_nested_fields(self) -> "AbacusRunArtifact":
        if self.control_file_paths is None:
            input_file = next(
                (
                    path
                    for path in self.prepared_inputs
                    if path.endswith("/INPUT") or path.endswith("INPUT")
                ),
                None,
            )
            structure_file = next(
                (
                    path
                    for path in self.prepared_inputs
                    if path.endswith("/STRU") or path.endswith("STRU")
                ),
                None,
            )
            kpoints_file = next(
                (
                    path
                    for path in self.prepared_inputs
                    if path.endswith("/KPT") or path.endswith("KPT")
                ),
                None,
            )
            self.control_file_paths = AbacusMaterializedControlFiles(
                input_file=input_file,
                structure_file=structure_file,
                kpoints_file=kpoints_file,
            )
        if self.workspace_layout is None:
            self.workspace_layout = AbacusWorkspaceLayout(
                working_directory=self.working_directory,
                output_root=self.output_root,
                stdout_path=self.stdout_path,
                stderr_path=self.stderr_path,
            )
        if self.artifact_groups is None:
            self.artifact_groups = AbacusArtifactGroups(
                output_files=list(self.output_files),
                diagnostic_files=list(self.diagnostic_files),
                structure_files=list(self.structure_files),
            )
        self.prepared_inputs = self.control_file_paths.as_list()
        self.working_directory = self.workspace_layout.working_directory
        self.output_root = self.workspace_layout.output_root
        self.stdout_path = self.workspace_layout.stdout_path
        self.stderr_path = self.workspace_layout.stderr_path
        self.output_files = list(self.artifact_groups.output_files)
        self.diagnostic_files = list(self.artifact_groups.diagnostic_files)
        self.structure_files = list(self.artifact_groups.structure_files)
        return self


class AbacusValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool = False
    status: AbacusValidationStatus = "validation_failed"
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str | bool] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)
    blocks_promotion: bool = False
    governance_state: Literal["defer", "blocked"] = "defer"
    scored_evidence: ScoredEvidence | None = None
