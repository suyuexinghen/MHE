from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from metaharness.core.models import ScoredEvidence, ValidationIssue
from metaharness.safety.gates import GateResult
from metaharness_ext.qcompute.types import QComputeExecutionMode, QComputeValidationStatus

QComputeRunArtifactStatus = Literal[
    "created",
    "queued",
    "running",
    "completed",
    "failed",
    "timeout",
    "cancelled",
]
QComputeStudyStrategy = Literal["grid", "random", "bayesian", "agentic"]
QComputeObjective = Literal["fidelity", "energy", "circuit_depth", "swap_count"]
QComputePlatform = Literal["quafu", "qiskit_aer", "ibm_quantum"]
QComputeAnsatz = Literal["vqe", "qaoa", "qpe", "custom"]
QComputeEntanglement = Literal["linear", "full", "circular"]
QComputeHamiltonianFormat = Literal["fcidump", "hdf5", "pauli_dict", "qiskit_op"]
QComputeFermionMapping = Literal["jordan_wigner", "bravyi_kitaev", "parity"]
QComputeNoiseModel = Literal["none", "depolarizing", "thermal_relaxation", "real"]
QComputeCompilationStrategy = Literal["baseline", "sabre", "agentic"]


class QComputeCandidateIdentity(BaseModel):
    candidate_id: str | None = None
    proposed_graph_version: int | None = None
    graph_version_id: int | None = None
    actor: str | None = None
    template_id: str | None = None
    backend_platform: QComputePlatform | None = None


class QComputePromotionMetadata(BaseModel):
    outcome: Literal["pending", "approved", "rejected", "unknown"] = "pending"
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    affected_components: list[str] = Field(default_factory=list)
    created_at: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class QComputeExecutionPolicy(BaseModel):
    sandbox_profile: str | None = None
    requires_api_token: bool = False
    api_token_env: str | None = None
    daily_quota: int | None = None
    max_retry: int = 3
    details: dict[str, Any] = Field(default_factory=dict)


class QComputeBackendSpec(BaseModel):
    platform: QComputePlatform
    chip_id: str | None = None
    simulator: bool = True
    qubit_count: int | None = None
    coupling_map: list[tuple[int, int]] | None = None
    api_token_env: str | None = None
    daily_quota: int | None = None


class QComputeCircuitSpec(BaseModel):
    ansatz: QComputeAnsatz
    num_qubits: int
    depth: int | None = None
    gate_set: list[str] = Field(default_factory=lambda: ["rx", "ry", "rz", "cx"])
    openqasm: str | None = None
    qiskit_circuit_b64: str | None = None
    parameters: dict[str, float] = Field(default_factory=dict)
    entanglement: QComputeEntanglement = "full"
    repetitions: int = 1
    transpiler_level: int = 1
    sabre_layout_trials: int = 20
    sabre_swap_trials: int = 20

    @field_validator("num_qubits")
    @classmethod
    def validate_num_qubits(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("num_qubits must be positive")
        return value

    @field_validator("repetitions", "sabre_layout_trials", "sabre_swap_trials")
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value

    @field_validator("transpiler_level")
    @classmethod
    def validate_transpiler_level(cls, value: int) -> int:
        if value not in {0, 1, 2, 3}:
            raise ValueError("transpiler_level must be between 0 and 3")
        return value

    @model_validator(mode="after")
    def validate_circuit_source(self) -> "QComputeCircuitSpec":
        if self.ansatz == "custom" and not self.openqasm and not self.qiskit_circuit_b64:
            raise ValueError("custom ansatz requires openqasm or qiskit_circuit_b64")
        return self


class QComputeNoiseSpec(BaseModel):
    model: QComputeNoiseModel
    depolarizing_prob: float | None = None
    t1_us: float | None = None
    t2_us: float | None = None
    readout_error: float | None = None
    gate_error_map: dict[str, float] | None = None
    calibration_ref: str | None = None


class QComputeExperimentSpec(BaseModel):
    task_id: str
    mode: QComputeExecutionMode
    backend: QComputeBackendSpec
    circuit: QComputeCircuitSpec
    noise: QComputeNoiseSpec | None = None
    shots: int = 1024
    error_mitigation: list[str] = Field(default_factory=list)
    fidelity_threshold: float | None = None
    energy_target: float | None = None
    max_iterations: int = 1
    hamiltonian_file: str | None = None
    hamiltonian_format: QComputeHamiltonianFormat = "fcidump"
    fermion_mapping: QComputeFermionMapping = "jordan_wigner"
    active_space: tuple[int, int] | None = None
    reference_energy: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    promotion_metadata: QComputePromotionMetadata = Field(default_factory=QComputePromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: QComputeExecutionPolicy = Field(default_factory=QComputeExecutionPolicy)

    @field_validator("shots", "max_iterations")
    @classmethod
    def validate_positive_counts(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("value must be positive")
        return value


class QComputeExecutionParams(BaseModel):
    shots: int = 1024
    measurement_basis: str = "Z"
    error_mitigation: list[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_on_failure: int = 0


class QComputeRunPlan(BaseModel):
    plan_id: str
    experiment_ref: str
    circuit_openqasm: str
    target_backend: QComputeBackendSpec
    compilation_strategy: QComputeCompilationStrategy
    compilation_metadata: dict[str, Any] = Field(default_factory=dict)
    estimated_depth: int | None = None
    estimated_swap_count: int | None = None
    estimated_fidelity: float | None = None
    execution_params: QComputeExecutionParams
    noise: QComputeNoiseSpec | None = None
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    promotion_metadata: QComputePromotionMetadata = Field(default_factory=QComputePromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: QComputeExecutionPolicy = Field(default_factory=QComputeExecutionPolicy)


class QComputeCalibrationData(BaseModel):
    timestamp: datetime
    t1_us_avg: float | None = None
    t2_us_avg: float | None = None
    single_qubit_gate_fidelity_avg: float | None = None
    two_qubit_gate_fidelity_avg: float | None = None
    readout_fidelity_avg: float | None = None
    qubit_connectivity: list[tuple[int, int]] | None = None


class CalibrationSnapshot(BaseModel):
    calibration_id: str
    chip_id: str
    captured_at: datetime
    t1_us: dict[int, float]
    t2_us: dict[int, float]
    single_gate_fidelity: dict[int, dict[str, float]]
    two_qubit_gate_fidelity: dict[tuple[int, int], float]
    readout_error_0to1: dict[int, float]
    readout_error_1to0: dict[int, float]
    coupling_map: list[tuple[int, int]]


class QComputeEnvironmentReport(BaseModel):
    task_id: str
    backend: QComputeBackendSpec
    available: bool
    status: str
    qubit_count_available: int | None = None
    queue_depth: int | None = None
    estimated_wait_seconds: int | None = None
    calibration_fresh: bool = True
    calibration_data: QComputeCalibrationData | None = None
    prerequisite_errors: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False


class QComputeValidationMetrics(BaseModel):
    fidelity: float | None = None
    energy: float | None = None
    energy_error: float | None = None
    convergence_iterations: int | None = None
    chi_squared: float | None = None
    circuit_depth_executed: int | None = None
    swap_count_executed: int | None = None
    noise_impact_score: float | None = None
    gate_error_accumulation: float | None = None
    readout_confidence: float | None = None
    syntax_valid: bool | None = None
    distributional_jsd: float | None = None
    semantic_expectation_error: float | None = None
    optimization_efficiency: float | None = None


class QComputeValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool = False
    status: QComputeValidationStatus = QComputeValidationStatus.EXECUTION_FAILED
    metrics: QComputeValidationMetrics = Field(default_factory=QComputeValidationMetrics)
    issues: list[ValidationIssue] = Field(default_factory=list)
    promotion_ready: bool = False
    evidence_refs: list[str] = Field(default_factory=list)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None


class QComputeRunArtifact(BaseModel):
    artifact_id: str
    plan_ref: str
    backend_actual: str
    status: QComputeRunArtifactStatus
    counts: dict[str, int] | None = None
    statevector: list[complex] | None = None
    probabilities: dict[str, float] | None = None
    execution_time_ms: float | None = None
    queue_time_ms: float | None = None
    raw_output_path: str | None = None
    error_message: str | None = None
    calibration_snapshot: dict[str, Any] | None = None
    shots_requested: int | None = None
    shots_completed: int | None = None
    retry_count: int = 0
    terminal_error_type: str | None = None
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    promotion_metadata: QComputePromotionMetadata = Field(default_factory=QComputePromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    execution_policy: QComputeExecutionPolicy = Field(default_factory=QComputeExecutionPolicy)


class QComputeEvidenceWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning"] = "warning"
    evidence: dict[str, Any] = Field(default_factory=dict)


class QComputeEvidenceBundle(BaseModel):
    bundle_id: str
    experiment_ref: str
    environment_report: QComputeEnvironmentReport
    run_artifact: QComputeRunArtifact
    validation_report: QComputeValidationReport
    provenance_inputs: list[str] = Field(default_factory=list)
    warnings: list[QComputeEvidenceWarning] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QComputePolicyReport(BaseModel):
    passed: bool
    decision: Literal["allow", "defer", "reject"]
    reason: str
    warnings: list[QComputeEvidenceWarning] = Field(default_factory=list)
    gates: list[GateResult] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class QComputeStudyAxis(BaseModel):
    parameter_path: str
    values: list[Any] | None = None
    range: tuple[float, float] | None = None
    step: float | None = None

    @model_validator(mode="after")
    def validate_axis_shape(self) -> "QComputeStudyAxis":
        if self.values is None and self.range is None:
            raise ValueError("study axis requires values or range")
        return self


class QComputeStudySpec(BaseModel):
    study_id: str
    experiment_template: QComputeExperimentSpec
    axes: list[QComputeStudyAxis]
    strategy: QComputeStudyStrategy
    max_trials: int = 100
    parallel_workers: int = 1
    objective: QComputeObjective


class QComputeStudyTrial(BaseModel):
    trial_id: str
    parameter_snapshot: dict[str, Any]
    evidence_bundle: QComputeEvidenceBundle
    trajectory_score: float | None = None


class QComputeStudyReport(BaseModel):
    study_id: str
    trials: list[QComputeStudyTrial]
    best_trial_id: str | None = None
    pareto_front: list[str] = Field(default_factory=list)
    convergence_analysis: dict[str, Any] = Field(default_factory=dict)
