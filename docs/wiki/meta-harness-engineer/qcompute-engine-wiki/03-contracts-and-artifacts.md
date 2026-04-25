# 03. Contracts 与产物

## 3.1 为什么 contracts 是一等设计对象

量子计算涉及多种后端（不同芯片架构、模拟器 vs 真机）、
多种电路表示（OpenQASM 2.0 / 3.0、Qiskit QuantumCircuit、pyQuafu circuit）、
多种噪声模型和错误缓解策略。没有严格的类型约束，
扩展很快就会变成"字符串拼凑 + dict 透传"的脆弱管道。

Contracts 的核心目标：
1. **后端无关**：同一套 Spec 类型可以描述针对模拟器和真机的实验
2. **噪声可表达**：规范表达 noise model、calibration data、fidelity thresholds
3. **promotion-readable**：所有 report 类型携带 MHE 治理层需要的 `blocks_promotion`、evidence refs

## 3.2 类型层次

```
BaseModel
  ├─ Spec 类型（用户输入）
  │   ├─ QComputeExperimentSpec
  │   ├─ QComputeBackendSpec
  │   ├─ QComputeCircuitSpec
  │   └─ QComputeNoiseSpec
  │
  ├─ Plan 类型（编译产出）
  │   └─ QComputeRunPlan
  │
  ├─ Report 类型（阶段输出）
  │   ├─ QComputeEnvironmentReport
  │   └─ QComputeValidationReport
  │
  ├─ Artifact 类型（执行产物）
  │   └─ QComputeRunArtifact
  │
  ├─ Bundle 类型（证据元组）
  │   └─ QComputeEvidenceBundle
  │
  ├─ Study 类型（突变/扫描）
  │   ├─ QComputeStudySpec
  │   ├─ QComputeStudyTrial
  │   └─ QComputeStudyReport
  │
  └─ 治理元数据类型
      ├─ QComputeCandidateIdentity
      ├─ QComputePromotionMetadata
      └─ QComputeExecutionPolicy
```

## 3.3 QComputeExecutionMode

```python
from typing import Literal

QComputeExecutionMode = Literal[
    "simulate",   # 纯模拟器执行
    "run",        # 真机执行
    "hybrid",     # 经典-量子混合
]
```

## 3.3b MHE 治理元数据

QCompute 的所有核心 contract 类型共享一组 MHE 治理元数据字段，
使每个产物都能参与 graph promotion、checkpoint、provenance 与审计流。
该模式与 `nektar` 扩展的治理元数据约定对齐。

```python
class QComputeCandidateIdentity(BaseModel):
    """Candidate/graph version identity for promotion tracking."""
    candidate_id: str | None = None
    proposed_graph_version: int | None = None
    graph_version_id: int | None = None
    actor: str | None = None

class QComputePromotionMetadata(BaseModel):
    """Promotion outcome and tracking metadata."""
    outcome: Literal["pending", "approved", "rejected", "unknown"] = "pending"
    affected_components: list[str] = Field(default_factory=list)
    created_at: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)

class QComputeExecutionPolicy(BaseModel):
    """Execution constraints: sandbox, API token, quota, retry."""
    sandbox_profile: str | None = None
    requires_api_token: bool = False
    api_token_env: str | None = None
    daily_quota: int | None = None
    max_retry: int = 3
    details: dict[str, Any] = Field(default_factory=dict)
```

以下各 contract 类型中的 `graph_metadata`、`candidate_identity`、`promotion_metadata`、
`checkpoint_refs`、`provenance_refs`、`trace_refs`、`execution_policy`、`scored_evidence`
字段均引用上述类型，不再逐一展开。

## 3.4 QComputeExperimentSpec —— 实验规格

顶层用户输入，表达一次量子实验的完整意图。

```python
class QComputeExperimentSpec(BaseModel):
    task_id: str
    mode: QComputeExecutionMode
    backend: QComputeBackendSpec
    circuit: QComputeCircuitSpec
    noise: QComputeNoiseSpec | None = None
    shots: int = 1024
    error_mitigation: list[str] = Field(default_factory=list)
    fidelity_threshold: float | None = None
    energy_target: float | None = None         # VQE 目标能量（可选）
    max_iterations: int = 1                     # VQE 迭代轮数

    # Hamiltonian & chemistry context (for VQE/QPE experiments)
    hamiltonian_file: str | None = None              # Path to FCIDUMP or HDF5 file
    hamiltonian_format: Literal["fcidump", "hdf5", "pauli_dict", "qiskit_op"] = "fcidump"
    fermion_mapping: Literal["jordan_wigner", "bravyi_kitaev", "parity"] = "jordan_wigner"
    active_space: tuple[int, int] | None = None      # (n_active_electrons, n_active_orbitals)
    reference_energy: float | None = None            # Classical reference energy (e.g. DFT result)

    metadata: dict[str, Any] = Field(default_factory=dict)

    # MHE governance metadata
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    promotion_metadata: QComputePromotionMetadata = Field(default_factory=QComputePromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: QComputeExecutionPolicy = Field(default_factory=QComputeExecutionPolicy)
```

### 3.4.1 字段语义

| 字段 | 语义 | 验证规则 |
|------|------|---------|
| `task_id` | 全局唯一任务标识 | 必填 |
| `mode` | 执行模式 | `simulate` / `run` / `hybrid` |
| `backend` | 目标后端规格 | 必填；见 3.5 |
| `circuit` | 电路规格 | 必填；见 3.6 |
| `noise` | 噪声配置 | simulate 模式下可选（不加则无噪声） |
| `shots` | 测量次数 | 模拟器默认 1024；真机最小 1000 |
| `error_mitigation` | 错误缓解策略列表 | 选自 `["rem", "zne", "pauli_twirling"]` |
| `fidelity_threshold` | 最低可接受保真度 | 不满足则 `blocks_promotion=True` |
| `energy_target` | VQE 期望能量 | 用于收敛判断 |
| `max_iterations` | 最大优化迭代数 | VQE 场景 >1 |

## 3.5 QComputeBackendSpec —— 后端规格

```python
class QComputeBackendSpec(BaseModel):
    platform: Literal["quafu", "qiskit_aer", "ibm_quantum"]
    chip_id: str | None = None              # Quafu 芯片 ID，如 "Baihua"
    simulator: bool = True                  # True=模拟器, False=真机
    qubit_count: int | None = None          # 需要的量子比特数
    coupling_map: list[tuple[int, int]] | None = None  # 硬件拓扑（预留）
    api_token_env: str | None = None        # API token 环境变量名
    daily_quota: int | None = None          # 每日配额上限
```

### 3.5.1 平台适配器

| `platform` | 模拟器支持 | 真机支持 | SDK |
|-----------|-----------|---------|-----|
| `quafu` | ✅ (Quafu 内置模拟器) | ✅ (百花/其他芯片) | pyQuafu + MCP |
| `qiskit_aer` | ✅ (AerSimulator) | ❌ | qiskit-aer |
| `ibm_quantum` | ✅ (Aer) | ✅ (IBM Q 设备) | qiskit-ibm-runtime (预留) |

## 3.6 QComputeCircuitSpec —— 电路规格

```python
class QComputeCircuitSpec(BaseModel):
    ansatz: str                              # "vqe", "qaoa", "qpe", "custom"
    num_qubits: int
    depth: int | None = None                 # None = 自动确定
    gate_set: list[str] = Field(default_factory=lambda: ["rx", "ry", "rz", "cx"])
    openqasm: str | None = None              # 直接提供 OpenQASM 2.0
    qiskit_circuit_b64: str | None = None    # 序列化的 Qiskit QuantumCircuit
    parameters: dict[str, float] = Field(default_factory=dict)  # 电路参数（ansatz 角度等）
    entanglement: Literal["linear", "full", "circular"] = "full"
    repetitions: int = 1                     # ansatz 重复层数
    transpiler_level: int = 1                        # 0=trivial, 1=basic, 2=enhanced, 3=maximum
    sabre_layout_trials: int = 20                    # SabreLayout random initial layouts
    sabre_swap_trials: int = 20                      # Swap-selection trials per layout
```

### 3.6.1 ansatz 类型

| ansatz | 说明 | 典型参数 |
|--------|------|---------|
| `vqe` | Variational Quantum Eigensolver | `parameters` 含旋转角度 |
| `qaoa` | Quantum Approximate Optimization Algorithm | `parameters` 含 γ, β |
| `qpe` | Quantum Phase Estimation | 辅助比特数 |
| `custom` | 自定义电路（通过 `openqasm` 或 `qiskit_circuit_b64` 提供） | 任意 |

## 3.7 QComputeNoiseSpec —— 噪声规格

```python
class QComputeNoiseSpec(BaseModel):
    model: Literal["none", "depolarizing", "thermal_relaxation", "real"]
    depolarizing_prob: float | None = None        # depolarizing 模型的单门错误率
    t1_us: float | None = None                    # 热弛豫 T1 (μs)
    t2_us: float | None = None                    # 热弛豫 T2 (μs)
    readout_error: float | None = None             # 读出错误概率
    gate_error_map: dict[str, float] | None = None # 门级错误率 {"cx": 0.01, "u3": 0.001}
    calibration_ref: str | None = None            # 引用环境报告中的校准数据
```

## 3.8 QComputeRunPlan —— 编译产出

```python
class QComputeRunPlan(BaseModel):
    plan_id: str
    experiment_ref: str                          # 关联的 task_id
    circuit_openqasm: str                        # 编译后的 OpenQASM 2.0
    target_backend: QComputeBackendSpec
    compilation_strategy: Literal["baseline", "sabre", "agentic"]
    compilation_metadata: dict[str, Any] = Field(default_factory=dict)
    estimated_depth: int | None = None
    estimated_swap_count: int = 0
    estimated_fidelity: float | None = None      # 编译时预估保真度
    execution_params: QComputeExecutionParams

    # MHE governance metadata
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    promotion_metadata: QComputePromotionMetadata = Field(default_factory=QComputePromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    execution_policy: QComputeExecutionPolicy = Field(default_factory=QComputeExecutionPolicy)
```

### 3.8.1 QComputeExecutionParams

```python
class QComputeExecutionParams(BaseModel):
    shots: int = 1024
    measurement_basis: str = "Z"
    error_mitigation: list[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_on_failure: int = 0
```

## 3.9 QComputeRunArtifact —— 执行产物

```python
class QComputeRunArtifact(BaseModel):
    artifact_id: str
    plan_ref: str
    backend_actual: str                           # 实际执行后端（可能与请求不同）
    status: Literal["created", "queued", "running", "completed", "failed", "timeout", "cancelled"]
    counts: dict[str, int] | None = None           # 测量计数 {"00": 512, "11": 512}
    statevector: list[complex] | None = None       # 仅模拟器
    probabilities: dict[str, float] | None = None
    execution_time_ms: float | None = None
    queue_time_ms: float | None = None
    raw_output_path: str | None = None            # 原始输出文件路径
    error_message: str | None = None
    calibration_snapshot: dict[str, Any] | None = None  # 执行时的校准快照
    shots_requested: int | None = None               # Originally requested shots
    shots_completed: int | None = None               # Actually completed shots
    retry_count: int = 0                             # Number of retries
    terminal_error_type: str | None = None           # "retriable" | "non_retriable" | None

    # MHE governance metadata
    graph_metadata: dict[str, Any] = Field(default_factory=dict)
    candidate_identity: QComputeCandidateIdentity = Field(default_factory=QComputeCandidateIdentity)
    promotion_metadata: QComputePromotionMetadata = Field(default_factory=QComputePromotionMetadata)
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
    execution_policy: QComputeExecutionPolicy = Field(default_factory=QComputeExecutionPolicy)
```

## 3.10 QComputeEnvironmentReport

```python
class QComputeEnvironmentReport(BaseModel):
    task_id: str
    backend: QComputeBackendSpec
    available: bool
    status: str                                                # "online", "maintenance", "unreachable"
    qubit_count_available: int | None = None
    queue_depth: int | None = None                             # 当前排队任务数
    estimated_wait_seconds: int | None = None
    calibration_fresh: bool = True
    calibration_data: QComputeCalibrationData | None = None
    prerequisite_errors: list[str] = Field(default_factory=list)
    blocks_promotion: bool = False
```

### 3.10.1 QComputeCalibrationData

```python
class QComputeCalibrationData(BaseModel):
    timestamp: datetime
    t1_us_avg: float | None = None
    t2_us_avg: float | None = None
    single_qubit_gate_fidelity_avg: float | None = None  # 单比特门平均保真度
    two_qubit_gate_fidelity_avg: float | None = None     # 双比特门（CX）平均保真度
    readout_fidelity_avg: float | None = None
    qubit_connectivity: list[tuple[int, int]] | None = None
```

### 3.10.2 CalibrationSnapshot

```python
class CalibrationSnapshot(BaseModel):
    """Full per-qubit calibration snapshot — complements aggregated CalibrationData."""
    calibration_id: str
    chip_id: str
    captured_at: datetime
    t1_us: dict[int, float]                          # qubit index → T1 (μs)
    t2_us: dict[int, float]                          # qubit index → T2 (μs)
    single_gate_fidelity: dict[int, dict[str, float]] # qubit → {gate_name: fidelity}
    two_qubit_gate_fidelity: dict[tuple[int,int], float]  # (q1,q2) → CX fidelity
    readout_error_0to1: dict[int, float]             # qubit → P(1|0)
    readout_error_1to0: dict[int, float]             # qubit → P(0|1)
    coupling_map: list[tuple[int, int]]
```

## 3.11 QComputeValidationReport —— 验证产出

```python
class QComputeValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool
    status: QComputeValidationStatus
    metrics: QComputeValidationMetrics
    issues: list[ValidationIssue] = Field(default_factory=list)
    promotion_ready: bool = False
    evidence_refs: list[str] = Field(default_factory=list)

    # MHE governance metadata
    checkpoint_refs: list[str] = Field(default_factory=list)
    provenance_refs: list[str] = Field(default_factory=list)
    trace_refs: list[str] = Field(default_factory=list)
    scored_evidence: ScoredEvidence | None = None
```

### 3.11.1 QComputeValidationMetrics

```python
class QComputeValidationMetrics(BaseModel):
    fidelity: float | None = None               # 态保真度或能量相对误差
    energy: float | None = None                 # VQE 计算能量
    energy_error: float | None = None           # |E_computed - E_target|
    convergence_iterations: int | None = None   # 收敛所需迭代数
    chi_squared: float | None = None            # 测量分布拟合优度
    circuit_depth_executed: int | None = None
    swap_count_executed: int | None = None
    noise_impact_score: float | None = None     # 噪声对结果的影响评分 (0-1)
    gate_error_accumulation: float | None = None
    readout_confidence: float | None = None

    # QUASAR-inspired hierarchical evaluation (gated: level N only evaluated if N-1 passes)
    syntax_valid: bool | None = None                 # OpenQASM syntax check passed
    distributional_jsd: float | None = None          # Jensen-Shannon divergence vs reference
    semantic_expectation_error: float | None = None  # |〈H〉_gen - 〈H〉_ref|
    optimization_efficiency: float | None = None     # Composite: (depth)^-1 × (SWAP)^-1
```

## 3.12 QComputeEvidenceBundle

```python
class QComputeEvidenceBundle(BaseModel):
    bundle_id: str
    experiment_ref: str
    environment_report: QComputeEnvironmentReport
    run_artifact: QComputeRunArtifact
    validation_report: QComputeValidationReport
    provenance_inputs: list[str] = Field(default_factory=list)  # 上游 artifact refs
    scored_evidence: ScoredEvidence | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

## 3.13 Study 类型

### 3.13.1 QComputeStudySpec

```python
class QComputeStudySpec(BaseModel):
    study_id: str
    experiment_template: QComputeExperimentSpec       # 模板（参数可被突变）
    axes: list[QComputeStudyAxis]                     # 突变轴定义
    strategy: Literal["grid", "random", "bayesian", "agentic"]
    max_trials: int = 100
    parallel_workers: int = 1
    objective: str                                    # "fidelity", "energy", "circuit_depth", "swap_count"
```

### 3.13.2 QComputeStudyAxis

```python
class QComputeStudyAxis(BaseModel):
    parameter_path: str                               # 模板中的参数路径，如 "circuit.repetitions"
    values: list[Any] | None = None                   # grid search 值列表
    range: tuple[float, float] | None = None          # random search 范围
    step: float | None = None                         # grid search 步长
```

### 3.13.3 QComputeStudyTrial / QComputeStudyReport

```python
class QComputeStudyTrial(BaseModel):
    trial_id: str
    parameter_snapshot: dict[str, Any]
    evidence_bundle: QComputeEvidenceBundle
    trajectory_score: float | None = None            # Whole-trajectory score (not per-step)

class QComputeStudyReport(BaseModel):
    study_id: str
    trials: list[QComputeStudyTrial]
    best_trial_id: str | None = None
    pareto_front: list[str] = Field(default_factory=list)  # Pareto 最优 trial IDs
    convergence_analysis: dict[str, Any] = Field(default_factory=dict)
```

## 3.14 首版 contract 边界

首版 contracts 不应过度建模，也不应过度自由。具体来说：

错误缓解策略的实现路径上，优先集成 [Mitiq](https://mitiq.readthedocs.io/)
而非自行实现 REM、ZNE 和 Pauli Twirling。
Mitiq 作为成熟的量子错误缓解框架，提供了
`mitiq.rem`、`mitiq.zne`、`mitiq.pec` 等即用技术栈，
且与 Qiskit、Cirq、pyQuil 等多后端兼容。
首版 QCompute 的 `QComputeExecutorComponent` 将在执行层
通过 Mitiq 的 `Executor` 包装器调用这些技术，
避免重复造轮子并降低维护成本。

- **包含**：当前常用后端（Quafu + Qiskit Aer）、VQE/QAOA/QPE 三种 ansatz、
  基础错误缓解策略（通过 Mitiq 集成）、核心验证指标
- **不包含**：脉冲级控制、量子纠错码设计、自定义门校准、多芯片分布式量子计算
- **预留扩展点**：`QComputeBackendSpec.platform` 新增平台、
  `QComputeCircuitSpec.ansatz` 新增 ansatz 类型、
  `QComputeValidationMetrics` 新增指标字段

这些 contract 的用途也不只停留在 local execution；它们还需要为 runtime-level promotion gating
提供稳定、可审计、可引用的上游输入：

- report 侧至少应预留稳定的 candidate / graph version / session-event / audit / provenance handoff 面，
  避免文档继续把 `QComputeValidationReport` 理解成一次性终端输出
- `QComputeEvidenceBundle.provenance_inputs` 是 provenance link 的载体，
  当前即可被 `WAS_DERIVED_FROM` 关系引用
- 未来可对齐 `ScoredEvidence`、session/audit/provenance refs 与 `BrainProvider` seam

## 3.15 HI-VQE Handover Contract（远期扩展）

HI-VQE (Handover-Iterative VQE) 是北京量子院提出的经典-量子"信息交接"范式。
与传统 VQE 中量子端独立求解能量不同，HI-VQE 的核心创新在于：

- 量子端通过采样识别对波函数贡献最大的 Slater 行列式
- 将这些信息"交接"给经典端进行子空间对角化
- 经典端完成精确对角化后，将结果反馈回量子端指导下一轮采样

这种设计显著降低了对量子电路深度的要求，使得在 NISQ 硬件上达到化学精度成为可能。

### HI-VQE 的 contract 影响

若 QCompute 未来支持 HI-VQE，contracts 层需要增加：

```python
class HI_VQEHandover(BaseModel):
    iteration: int
    selected_determinants: list[str]               # Slater determinant bitstrings
    determinant_coefficients: list[complex] | None = None
    subspace_energy: float | None = None           # Classical diagonalization result
    convergence_metric: float | None = None
    handover_timestamp: datetime
```

当前首版不实现 HI-VQE，但 `QComputeExperimentSpec.hamiltonian_file` 和 `active_space`
字段的设计已预留了与 HI-VQE 范式的兼容性——它们支持经典端（ABACUS）和量子端（QCompute）
之间以 FCIDUMP 文件为基础、以活性空间规格为边界的稳定数据交接面。
