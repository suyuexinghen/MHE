# QCompute Extension — User Manual

> MHE quantum computing extension: circuit execution, VQE simulation, parameter study, and governance-ready evidence collection.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Installation & Dependencies](#2-installation--dependencies)
3. [Quick Start](#3-quick-start)
4. [Experiment Specification](#4-experiment-specification)
5. [Backend Adapters](#5-backend-adapters)
6. [Five-Stage Pipeline](#6-five-stage-pipeline)
7. [Noise Simulation & Error Mitigation](#7-noise-simulation--error-mitigation)
8. [Policy & Governance](#8-policy--governance)
9. [Parameter Study](#9-parameter-study)
10. [VQE / Molecular Simulation](#10-vqe--molecular-simulation)
11. [Tested Support Matrix](#11-tested-support-matrix)
12. [Core Integration](#12-core-integration)
13. [Error Handling](#13-error-handling)
14. [API Reference](#14-api-reference)

---

## 1. Overview

QCompute (`metaharness_ext.qcompute`) is a quantum computing extension for the Meta-Harness Engine (MHE). It provides:

- **Circuit execution** on simulators (Qiskit Aer, PennyLane) and real hardware (Quafu/Baihua)
- **VQE molecular simulation** via FCIDUMP integration and fermion-to-qubit mapping
- **Error mitigation** — self-implemented ZNE (zero-noise extrapolation) and REM (readout error mitigation)
- **Parameter study** — grid, random, and agentic strategies for parameter space exploration
- **Governance pipeline** — policy evaluation, evidence recording, artifact persistence, and candidate promotion

### Architecture

```
ExperimentSpec
    │
    ▼
┌──────────────────────────────────────────────┐
│              Gateway (五阶段管线)                │
│                                              │
│  1. Environment Probe                        │
│     └─ 检测后端可用性、依赖、配额               │
│  2. Config Compiler                          │
│     └─ 编译 OpenQASM、选择编译策略              │
│  3. Executor                                 │
│     └─ 执行量子线路，可选误差缓解               │
│  4. Validator                                │
│     └─ 验证结果完整性、保真度、噪声              │
│  5. Evidence Builder                         │
│     └─ 构建 QComputeEvidenceBundle            │
│                                              │
│  + Policy Evaluation (安全门)                  │
│  + Governance Adapter (审计/溯源)              │
│  + Artifact Store (快照持久化)                  │
└──────────────────────────────────────────────┘
    │
    ▼
QComputeBaselineResult / QComputeStudyReport
```

---

## 2. Installation & Dependencies

### Core Dependencies

```bash
# Required
pip install qiskit qiskit-aer

# Optional — PennyLane backend
pip install pennylane

# Optional — Quafu real hardware
pip install quarkstudio
```

### API Token (Quafu 真机)

在 `.env` 中配置：

```bash
export Qcompute_Token="your_token_here"
```

Token 从 [量子计算云平台](https://quafu.baqis.ac.cn/) 获取。

---

## 3. Quick Start

### 3.1 最简示例：Bell 态

```python
import asyncio
from pathlib import Path
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute import (
    QComputeGatewayComponent,
    QComputeExperimentSpec,
    QComputeBackendSpec,
    QComputeCircuitSpec,
)

# 1. 构造实验规格
spec = QComputeExperimentSpec(
    task_id="bell-state-demo",
    mode="simulate",
    backend=QComputeBackendSpec(
        platform="qiskit_aer",
        simulator=True,
        qubit_count=2,
    ),
    circuit=QComputeCircuitSpec(
        ansatz="custom",
        num_qubits=2,
        openqasm='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; creg c[2]; h q[0]; cx q[0],q[1]; measure q[0]->c[0]; measure q[1]->c[1];',
    ),
    shots=1024,
)

# 2. 激活网关并执行
gateway = QComputeGatewayComponent()
asyncio.run(gateway.activate(ComponentRuntime(storage_path=Path("./runs"))))

result = gateway.run_baseline(spec)

# 3. 读取结果
bundle = result
print("Artifact:", bundle.run_artifact.status)
print("Counts:", bundle.run_artifact.counts)
print("Validation:", bundle.validation_report.status)
```

### 3.2 含策略与治理的完整管线

```python
result = gateway.run_baseline_full(spec)

print("Environment:", result.environment.available)
print("Policy decision:", result.policy.decision)  # "allow" | "defer" | "reject"
print("Core validation:", result.core_validation.valid)
```

### 3.3 可直接运行的示例脚本

仓库提供了与本手册场景对应的可运行脚本：

- `examples/qcompute/bell.py` — Bell 态基线与 Artifact Store 持久化
- `examples/qcompute/noise_mitigation.py` — 噪声模拟 + ZNE/REM 误差缓解
- `examples/qcompute/study.py` — Grid / Random / Agentic Study 示例
- `examples/qcompute/vqe.py` — 基于 FCIDUMP 的 H2 VQE 演示

默认情况下这些脚本只使用模拟器；只有在显式设置 `QCOMPUTE_ENABLE_HARDWARE=1` 且配置 `Qcompute_Token` 时，`examples/qcompute/bell.py` 才会切换到 Quafu 真机路径。

### 3.4 示例运行后的反思清单

运行示例或 Quafu 真机检查后，建议把终端输出和 `Raw output` / `Artifact snapshots` 文件一起交给 AI 或人工复盘，并按以下问题判断下一步：

- `Backend` / `Mode` 是否符合预期？如果真机检查仍显示 `qiskit_aer` 或 `simulate`，优先确认 `QCOMPUTE_ENABLE_HARDWARE=1`、`Qcompute_Token`、`QCOMPUTE_QUAFU_CHIP` 与配额设置。
- `Run status`、`Validation`、`Policy decision` 是否同时通过？如果策略为 `defer` / `reject` 或验证失败，先查看环境探测错误、配额快照、保真度阈值与噪声配置。
- `Counts` 是否符合场景预期？Bell 态应主要集中在 `00` / `11`；噪声缓解示例应对比 mitigation details，确认 ZNE/REM 是否真正启用并改善分布。
- Study 示例的 `Best trial payload` 是否只推荐了可复现实验参数？若 agentic strategy 产生非整数 `shots` 或不可验证参数，应记录为 Study 参数类型/约束缺口。
- VQE 示例的 `Energy error` 是否在可接受范围内？若误差偏大，下一步优先检查 ansatz、active space、mapping、迭代次数与参考能量。
- Quafu 真机路径若被 gated、排队、维护或校准信息缺失，应把它归类为能力门控而非模拟器失败，并在改进计划中标注所需 token、芯片状态、校准采集或重试策略。

这些检查项可直接映射到改进 backlog：API 诚信（暴露但缺失的策略）、结果质量（真实 fidelity / energy error）、硬件可靠性（校准、重试、配额）和 Study 可用性（参数类型、并行 trial）。

---

## 4. Experiment Specification

`QComputeExperimentSpec` 是所有实验的入口配置：

```python
spec = QComputeExperimentSpec(
    task_id="my-experiment",        # 唯一标识

    # 执行模式
    mode="simulate",                # "simulate" | "run" | "hybrid"

    # 后端配置
    backend=QComputeBackendSpec(
        platform="qiskit_aer",      # "qiskit_aer" | "pennylane_aer" | "quafu"
        simulator=True,
        qubit_count=4,
        chip_id="Baihua",           # 仅 quafu
        api_token_env="Qcompute_Token",
        daily_quota=100,            # 每日配额
    ),

    # 线路配置
    circuit=QComputeCircuitSpec(
        ansatz="custom",            # "vqe" | "qaoa" | "qpe" | "custom"
        num_qubits=2,
        openqasm='OPENQASM 2.0; ...',
        # 或使用 qiskit_circuit_b64 传入序列化的 Qiskit 线路
        parameters={"theta": 0.5},  # 可参数化
        entanglement="full",        # "linear" | "full" | "circular"
        transpiler_level=1,         # 0-3, Qiskit transpiler 优化级别
    ),

    # 噪声配置 (可选)
    noise=QComputeNoiseSpec(
        model="depolarizing",       # "none" | "depolarizing" | "thermal_relaxation" | "real"
        depolarizing_prob=0.01,
        t1_us=100.0,
        t2_us=80.0,
        readout_error=0.02,
        gate_error_map={"cx": 0.01, "x": 0.001},
    ),

    # 执行参数
    shots=1024,
    error_mitigation=["zne", "rem"], # ZNE + 读出误差缓解
    fidelity_threshold=0.9,          # 保真度阈值

    # VQE 参数 (可选)
    hamiltonian_file="h2.fcidump",
    hamiltonian_format="fcidump",
    fermion_mapping="jordan_wigner", # "jordan_wigner" | "bravyi_kitaev" | "parity"
    active_space=(2, 2),             # (n_electrons, n_orbitals)
    reference_energy=-1.137,         # 参考能量（用于能量误差计算）
    max_iterations=100,

    # 执行策略
    execution_policy=QComputeExecutionPolicy(
        requires_api_token=False,
        api_token_env="Qcompute_Token",
        daily_quota=100,
        max_retry=3,
    ),
)
```

### 关键字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `mode` | `"simulate"` \| `"run"` \| `"hybrid"` | `simulate` = 模拟器; `run` = 真机; `hybrid` = 混合 |
| `circuit.ansatz` | `"vqe"` \| `"qaoa"` \| `"qpe"` \| `"custom"` | `custom` 需提供 `openqasm` 或 `qiskit_circuit_b64` |
| `circuit.parameters` | `dict[str, float]` | 可参数化线路的当前参数值 |
| `shots` | `int` | 测量次数，默认 1024 |
| `fidelity_threshold` | `float \| None` | 低于此阈值时验证失败 |
| `error_mitigation` | `list[str]` | `"zne"`, `"rem"` 或两者 |

---

## 5. Backend Adapters

### 5.1 Qiskit Aer (模拟器)

```python
backend = QComputeBackendSpec(
    platform="qiskit_aer",
    simulator=True,
    qubit_count=4,
)
```

- 纯模拟，无 API 限制
- 支持噪声模型
- 默认后端

### 5.2 PennyLane Aer (模拟器)

```python
backend = QComputeBackendSpec(
    platform="pennylane_aer",
    simulator=True,
    qubit_count=4,
)
```

- 通过 PennyLane `default.qubit` 设备执行
- 支持原生 PennyLane 误差缓解 transforms (ZNE via `fold_global`)
- 需安装 `pennylane`

### 5.3 Quafu / Baihua (真机)

```python
backend = QComputeBackendSpec(
    platform="quafu",
    simulator=False,
    qubit_count=41,
    chip_id="Baihua",
    api_token_env="Qcompute_Token",
    daily_quota=50,
)
```

- 通过 quarkstudio SDK (`from quark import Task`) 接入量子计算云平台
- 支持 Baihua 芯片 (41 比特)
- 自动检测芯片状态（在线/维护/离线）
- 支持异步执行：`submit()` → `poll()` → `await_result()`
- 配额感知：环境探测会构建 `ResourceQuota`

### 5.4 Mock (测试)

```python
from metaharness_ext.qcompute.backends import MockQuantumBackend

mock = MockQuantumBackend()
result = mock.run(circuit=my_circuit, shots=1024)
```

---

## 6. Five-Stage Pipeline

Gateway 的 `run_baseline()` 执行五阶段管线：

### Stage 1: Environment Probe

```python
from metaharness_ext.qcompute import QComputeEnvironmentProbeComponent

probe = QComputeEnvironmentProbeComponent()
env_report = probe.probe(spec)

print(env_report.available)              # True/False
print(env_report.status)                 # "online" / "dependency_missing" / ...
print(env_report.qubit_count_available)  # 可用比特数
print(env_report.quota_snapshot)         # ResourceQuota | None
```

检查项：
- 平台依赖是否安装
- API Token 是否配置
- 芯片是否在线 (Quafu)
- 线路比特数是否超过后端容量
- 校准数据是否新鲜

### Stage 2: Config Compiler

```python
from metaharness_ext.qcompute import QComputeConfigCompilerComponent

compiler = QComputeConfigCompilerComponent()
plan = compiler.build_plan(spec, environment_report=env_report)

print(plan.plan_id)                  # 编译计划 ID
print(plan.circuit_openqasm)         # 编译后的 OpenQASM
print(plan.compilation_strategy)     # "baseline" | "sabre" | "agentic"
print(plan.estimated_depth)          # 预估线路深度
```

### Stage 3: Executor

```python
from metaharness_ext.qcompute import QComputeExecutorComponent

executor = QComputeExecutorComponent()
executor._runtime = runtime  # 需要 storage_path
artifact = executor.execute_plan(plan, environment_report=env_report)

print(artifact.status)             # "completed" | "failed"
print(artifact.counts)             # {"00": 487, "11": 452, ...}
print(artifact.execution_time_ms)  # 执行时间
print(artifact.raw_output_path)    # 结果文件路径
```

### Stage 4: Validator

```python
from metaharness_ext.qcompute import QComputeValidatorComponent

validator = QComputeValidatorComponent()
validation = validator.validate_run(artifact, plan, env_report)

print(validation.passed)             # True/False
print(validation.status)             # QComputeValidationStatus 枚举
print(validation.metrics.fidelity)   # 保真度
print(validation.promotion_ready)    # 是否可晋升
```

### Stage 5: Evidence Bundle

```python
bundle = validator.build_evidence_bundle(artifact, validation, env_report)

print(bundle.bundle_id)
print(bundle.run_artifact.counts)
print(bundle.validation_report.metrics)
print(bundle.provenance_refs)  # 溯源引用
```

---

## 7. Noise Simulation & Error Mitigation

### 噪声模型

```python
noise = QComputeNoiseSpec(
    model="depolarizing",     # 退极化噪声
    depolarizing_prob=0.01,
    readout_error=0.02,
)
```

可选模型：
- `"none"` — 无噪声 (默认)
- `"depolarizing"` — 退极化噪声
- `"thermal_relaxation"` — 热弛豫噪声 (需配置 t1_us, t2_us)
- `"real"` — 真实噪声 (需校准数据，当前不可用)

### ZNE (Zero-Noise Extrapolation)

```python
spec = QComputeExperimentSpec(
    ...,
    error_mitigation=["zne"],
)
```

实现原理：
- 在缩放因子 1, 3, 5 下分别执行线路（通过 unitary folding 放大噪声）
- 使用 Richardson 外推法估计零噪声期望值
- 仅依赖 `numpy`，不依赖 `mitiq`

### REM (Readout Error Mitigation)

```python
spec = QComputeExperimentSpec(
    ...,
    error_mitigation=["rem"],
)
```

实现原理：
- 构建读出混淆矩阵
- 矩阵求逆校正计数分布
- 需配置 `noise.readout_error`

### 组合使用

```python
spec = QComputeExperimentSpec(
    ...,
    error_mitigation=["zne", "rem"],
)
```

PennyLane 后端会自动使用 PennyLane 原生 transforms (`fold_global`)。

---

## 8. Policy & Governance

### 8.1 Policy Evaluation

```python
from metaharness_ext.qcompute import QComputeEvidencePolicy

policy = QComputeEvidencePolicy()
report = policy.evaluate(bundle)

print(report.decision)  # "allow" | "defer" | "reject"
print(report.reason)    # 决策原因
print(report.gates)     # 安全门评估列表
```

安全门链：

| 门 | 触发条件 | 决策 |
|----|----------|------|
| `environment_readiness` | 环境不可用 | REJECT |
| `validation_status` | 执行失败类状态 | REJECT |
| `validation_status` | 结果不完整/保真度不足/噪声过高 | DEFER |
| `raw_output_anchor` | 缺少原始输出路径 | DEFER |
| `promotion_readiness` | 验证未标记晋升就绪 | DEFER |
| `qcompute_evidence_ready` | 全部通过 | ALLOW |

决策逻辑：
- 任一门 REJECT → 整体 `reject`
- 无 REJECT 但有 DEFER → 整体 `defer`
- 全部通过 → 整体 `allow`

### 8.2 Governance Adapter

```python
from metaharness_ext.qcompute import QComputeGovernanceAdapter
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph

governance = QComputeGovernanceAdapter(session_id="my-session")

# 构建 Core 验证报告
core_report = governance.build_core_validation_report(
    bundle.validation_report, policy_report
)

# 发出运行时证据
refs = governance.emit_runtime_evidence(
    bundle, policy_report,
    session_store=InMemorySessionStore(),
    audit_log=AuditLog(),
    provenance_graph=ProvGraph(),
)

# 含 Artifact Store 的增强记录
from metaharness.provenance import ArtifactSnapshotStore

refs = governance.record_with_artifact_store(
    bundle, policy_report,
    session_store=session_store,
    audit_log=audit_log,
    provenance_graph=provenance_graph,
    artifact_store=ArtifactSnapshotStore(),
)
```

### 8.3 Candidate Record

```python
candidate = governance.build_candidate_record(bundle, policy_report)
print(candidate.candidate_id)
print(candidate.promoted)  # True if policy=allow and validation passed
```

---

## 9. Parameter Study

### 9.1 Grid Search

```python
from metaharness_ext.qcompute import (
    QComputeStudyComponent,
    QComputeStudySpec,
    QComputeStudyAxis,
)

study_spec = QComputeStudySpec(
    study_id="bell-theta-sweep",
    experiment_template=base_spec,
    axes=[
        QComputeStudyAxis(
            parameter_path="circuit.parameters.theta",
            range=(0.0, 6.28),
            step=0.5,
        ),
        QComputeStudyAxis(
            parameter_path="shots",
            values=[256, 512, 1024],
        ),
    ],
    strategy="grid",
    max_trials=100,
    objective="fidelity",
)

study = QComputeStudyComponent()
report = study.run_study(study_spec)

print("Best trial:", report.best_trial_id)
print("Trials:", len(report.trials))
print("Pareto front:", report.pareto_front)
```

### 9.2 Random Search

```python
study_spec = QComputeStudySpec(
    ...,
    strategy="random",
    max_trials=50,
)
```

### 9.3 Agentic Strategy

```python
study_spec = QComputeStudySpec(
    ...,
    strategy="agentic",
    max_trials=30,
)
```

Agentic 策略使用 `FunctionalBrainProvider` 进行迭代优化：
1. 初始随机探索
2. 以最佳参数为基线，添加高斯噪声生成候选
3. 每轮提出 3 个候选，迭代至 `max_trials`

### 9.4 Domain Payload Bridge

将 Study 结果桥接到 MHE 优化器：

```python
from metaharness_ext.qcompute.study import trial_to_domain_payload

best_trial = next(t for t in report.trials if t.trial_id == report.best_trial_id)
payload = trial_to_domain_payload(best_trial)

# payload = {
#     "trial_id": "...",
#     "parameters": {"theta": 1.57, ...},
#     "trajectory_score": 0.95,
#     "validation_status": "validated",
#     "fidelity": 0.95,
#     "energy_error": 0.01,
#     "circuit_depth": 5,
#     "backend": "qiskit_aer",
# }
```

---

## 10. VQE / Molecular Simulation

### 10.1 FCIDUMP 解析

```python
from metaharness_ext.qcompute.fcidump import parse_fcidump
from metaharness_ext.qcompute.contracts import FCIDumpData

fcidata = parse_fcidump("h2.fcidump")

print(fcidata.norb)   # 轨道数
print(fcidata.nelec)  # 电子数
print(fcidata.one_electron_integrals)   # {(i,j): value}
print(fcidata.two_electron_integrals)   # {(i,j,k,l): value}
```

### 10.2 Fermion-to-Qubit Mapping

```python
from metaharness_ext.qcompute.fermion_mapper import (
    map_fermionic_to_qubit,
    build_active_space,
)
from metaharness_ext.qcompute.contracts import QComputeActiveSpace

# 构建活性空间
active_space = build_active_space(fcidata, n_electrons=2, n_orbitals=2)

# Jordan-Wigner 映射
hamiltonian = map_fermionic_to_qubit(fcidata, active_space, method="jordan_wigner")

print(hamiltonian.num_qubits)
for term in hamiltonian.terms:
    print(f"  {term.coefficient:+.6f} * {term.pauli_string}")
```

支持的映射方法：
- `"jordan_wigner"` — Jordan-Wigner 变换
- `"bravyi_kitaev"` — Bravyi-Kitaev 变换

### 10.3 VQE 实验示例

```python
spec = QComputeExperimentSpec(
    task_id="h2-vqe",
    mode="simulate",
    backend=QComputeBackendSpec(platform="qiskit_aer", simulator=True, qubit_count=2),
    circuit=QComputeCircuitSpec(
        ansatz="vqe",
        num_qubits=2,
        parameters={"theta": 0.0},
    ),
    hamiltonian_file="h2.fcidump",
    hamiltonian_format="fcidump",
    fermion_mapping="jordan_wigner",
    active_space=(2, 2),
    reference_energy=-1.13727,
    max_iterations=100,
    shots=4096,
)
```

---

## 11. Tested Support Matrix

当前支持面的测试状态见 `docs/wiki/meta-harness-engineer/qcompute-tested-support-matrix.md`。

该矩阵明确标注了 Qiskit、PennyLane、Quafu、ZNE、REM、Study、Governance、ArtifactStore 与 VQE 的 `tested` / `experimental` / `gated` 状态，并给出对应测试锚点。

---

## 12. Core Integration

QCompute 实现了 MHE 增强核心的主要接口：

### Protocol 一致性

| QCompute 类型 | Core Protocol |
|---------------|---------------|
| `QComputeRunPlan` | `RunPlanProtocol` |
| `QComputeRunArtifact` | `RunArtifactProtocol` |
| `QComputeEnvironmentReport` | `EnvironmentReportProtocol` |
| `QComputeValidationReport` | `ValidationOutcomeProtocol` |
| `QComputeEvidenceBundle` | `EvidenceBundleProtocol` |
| `QuafuBackendAdapter` | `AsyncExecutorProtocol` |

### ExecutionEvidenceRecorder

通过 `governance.record_with_artifact_store()` 集成，遵循 DeepMD `runtime_handoff.py` 模式：

```python
from metaharness.provenance import ArtifactSnapshotStore

result = gateway.run_baseline_full(
    spec,
    artifact_store=ArtifactSnapshotStore(),  # 持久化快照
)
```

### ResourceQuota

当 `execution_policy.daily_quota` 设置时，环境探测自动构建 `ResourceQuota` 并存入 `env_report.quota_snapshot`。

### domain_payload Bridge

`trial_to_domain_payload()` 将 Study 试验结果转为 `MutationProposal.domain_payload` 兼容格式。

---

## 13. Error Handling

### 常见错误状态

| 状态 | 含义 | 处理 |
|------|------|------|
| `dependency_missing` | 缺少依赖包 | 安装对应包 |
| `missing_api_token` | API Token 未配置 | 设置环境变量 |
| `unsupported_platform` | 不支持的平台 | 使用支持的平台 |
| `insufficient_qubits` | 线路比特数超过后端容量 | 减少比特数或换用更大量子芯片 |
| `chip_maintenance` | 芯片维护中 | 等待或切换芯片 |
| `calibration_stale` | 校准数据过期 (>24h) | 等待新校准 |
| `environment_unavailable` | 环境探测失败 | 检查 prerequisite_errors |

### Validation Status 枚举

```python
class QComputeValidationStatus(str, Enum):
    ENVIRONMENT_INVALID = "environment_invalid"
    BACKEND_UNAVAILABLE = "backend_unavailable"
    EXECUTION_FAILED = "execution_failed"
    RESULT_INCOMPLETE = "result_incomplete"
    BELOW_FIDELITY_THRESHOLD = "below_fidelity"
    NOISE_CORRUPTED = "noise_corrupted"
    VALIDATED = "validated"
    CONVERGED = "converged"
```

### Run Artifact Status

```python
QComputeRunArtifactStatus = Literal[
    "created", "queued", "running", "completed",
    "failed", "timeout", "cancelled",
]
```

---

## 14. API Reference

### 主要组件

| 组件 | 职责 |
|------|------|
| `QComputeGatewayComponent` | 五阶段管线入口 |
| `QComputeEnvironmentProbeComponent` | 后端可用性探测 |
| `QComputeConfigCompilerComponent` | 编译 OpenQASM |
| `QComputeExecutorComponent` | 执行量子线路 |
| `QComputeValidatorComponent` | 结果验证 |
| `QComputeStudyComponent` | 参数空间探索 |
| `QComputeGovernanceAdapter` | 治理/审计/溯源 |
| `QComputeEvidencePolicy` | 安全门评估 |

### 主要数据模型

| 模型 | 说明 |
|------|------|
| `QComputeExperimentSpec` | 实验规格 (入口) |
| `QComputeRunPlan` | 编译后执行计划 |
| `QComputeRunArtifact` | 执行结果 |
| `QComputeValidationReport` | 验证报告 |
| `QComputeEvidenceBundle` | 证据包 (完整输出) |
| `QComputePolicyReport` | 策略决策报告 |
| `QComputeBaselineResult` | 完整管线输出 |
| `QComputeStudySpec` | Study 规格 |
| `QComputeStudyReport` | Study 结果 |
| `QComputeStudyTrial` | 单次试验 |
| `FCIDumpData` | FCIDUMP 分子积分数据 |
| `QubitHamiltonian` | 量子比特哈密顿量 |

### 后端适配器

| 适配器 | 平台 | 说明 |
|--------|------|------|
| `QiskitAerBackend` | `qiskit_aer` | Qiskit Aer 模拟器 |
| `PennyLaneBackend` | `pennylane_aer` | PennyLane 模拟器 |
| `QuafuBackendAdapter` | `quafu` | 量子计算云平台真机 |
| `MockQuantumBackend` | 测试 | Mock 后端 |

### 工具函数

| 函数 | 说明 |
|------|------|
| `parse_fcidump(path)` | 解析 FCIDUMP 文件 |
| `map_fermionic_to_qubit(fcidata, ...)` | 费米子→量子比特映射 |
| `build_active_space(fcidata, ...)` | 构建活性空间 |
| `mitigate_result(backend, circuit, ...)` | Qiskit 端误差缓解 |
| `mitigate_with_pennylane_transforms(...)` | PennyLane 端误差缓解 |
| `trial_to_domain_payload(trial)` | Study → 优化器桥接 |
| `build_evidence_bundle(...)` | 构建证据包 |
