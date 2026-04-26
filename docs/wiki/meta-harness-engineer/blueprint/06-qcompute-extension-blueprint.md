# 06. QCompute Extension Blueprint

> 状态：全部 Phase 0–5 + Gateway + Quafu 已实现 | 远期扩展待规划 | 以 `qcompute-engine-wiki` (01–08) 设计文档为准的实现蓝图

## 6.1 目标

`metaharness_ext.qcompute` 的目标，是把量子计算（NISQ 设备）以 **后端无关、噪声感知、证据驱动、Agent 可编排** 的方式接入 MHE，使其成为与 ABACUS（DFT）、DeepMD（分子动力学）、JEDI（数据同化）并列的科学计算 Worker。

QCompute 不是通用量子计算框架，也不是量子编译器。它不自行实现：
- 量子电路编译（委托 Qiskit Transpiler / QSteed）
- 错误缓解算法（委托自实现 ZNE/REM）
- 量子硬件校准（读取 Quafu 平台数据）
- Agent 推理与决策（委托 MHE BrainProvider）

它的核心价值是：将量子计算特有的 **后端多样性、时变噪声、配额约束、概率性测量结果** 映射到 MHE 的 typed contract / governance / evidence 体系中。

设计文档基线：

- `MHE/docs/wiki/meta-harness-engineer/qcompute-engine-wiki/` (01–08)
- `MHE/src/metaharness/core/models.py` (PromotionContext, ValidationIssue, ScoredEvidence, SessionEvent)
- `MHE/src/metaharness/core/brain.py` (BrainProvider protocol)
- `MHE/src/metaharness/sdk/base.py` (HarnessComponent)
- `MHE/src/metaharness/sdk/manifest.py` (ComponentManifest)

---

## 6.2 设计立场

QCompute 的运行模型与现有扩展的根本差异：

| 维度 | ABACUS / Nektar | QCompute |
|------|-----------------|----------|
| 执行模型 | 本地二进制 + workspace | 远程 SDK 调用 + 异步轮询 |
| 结果确定性 | 确定性（相同输入 = 相同输出） | 概率性（shots 统计 + 硬件噪声） |
| 环境前提 | 二进制存在 + 文件可写 | API token 有效 + 后端在线 + 配额充足 |
| 时间约束 | 秒–分钟级 | 秒（模拟器）到小时级（真机排队） |
| 编译阶段 | 生成输入文件 | 电路 transpilation + qubit mapping |

因此 QCompute 的设计立场：

1. **后端抽象优先**：模拟器与真机通过同一套 contract 访问，模拟器用于快速迭代，真机用于最终验证
2. **噪声作为一等概念**：contract 层原生表达噪声模型、校准数据、保真度阈值
3. **异步执行模型**：量子任务提交后不阻塞，采用 Fibonacci 轮询 + 配额感知调度
4. **证据贡献者而非门控执行者**：QComputeValidator 产出领域验证结果进入 `PromotionContext`，真正的 promotion 决策由 MHE runtime 完成
5. **两层级 Agent 分离**：框架级 `BrainProvider`（graph mutation）与领域级 QAgent（电路优化）分层，框架不感知领域 Agent 内部架构
6. **委托而非自研**：编译用 Qiskit/QSteed，错误缓解用自实现 ZNE/REM（纯 NumPy），不重复造轮子

---

## 6.3 组件链

```
QComputeGateway
  -> QComputeEnvironment
    -> QComputeConfigCompiler
      -> QComputeExecutor
        -> QComputeValidator
```

### Gateway (`qcompute_gateway.primary`)
- 接收 `QComputeExperimentSpec`，解析执行意图
- 编排五阶段流水线：Environment → ConfigCompiler → Executor → Validator
- 暴露 `compile_experiment()` 和 `run_baseline()` 便捷入口
- 生命周期：`declare_interface()` 声明 input/output/capability → `activate()` 获取依赖组件引用

### Environment (`qcompute_environment.primary`)
- 探测后端可用性（Quafu 芯片状态 / Qiskit Aer 版本）
- 获取校准数据（T1/T2、门保真度、读出误差）
- 验证前提条件（SDK 版本、API token、每日配额）
- 生成 `QComputeEnvironmentReport`，含 `blocks_promotion` 标记

### ConfigCompiler (`qcompute_config_compiler.primary`)
- 电路生成（Qiskit QuantumCircuit / OpenQASM 2.0）
- transpilation：逻辑电路 → 物理电路映射
- 三种编译策略：`baseline` / `sabre` / `agentic`
- 产出 `QComputeRunPlan`

### Executor (`qcompute_executor.primary`)
- 多后端调度：Quafu（quarkstudio SDK / MCP）、Qiskit Aer、IBM Quantum（预留）
- 异步任务生命周期管理（Fibonacci 轮询，上限 600s）
- 错误缓解集成（自实现 ZNE/REM，纯 NumPy）
- 产出 `QComputeRunArtifact`

### Validator (`qcompute_validator.primary`) — **protected**
- 验证运行结果完整性（status、counts、shots）
- 计算保真度指标（与参考解 / 已知基态能量对比）
- 噪声影响评分（ESP / QVA）
- 生成 `QComputeValidationReport`，含 `blocks_promotion` 和 `ScoredEvidence`
- **角色定位**：evidence contributor，不是 gate controller

### Study (`qcompute_study.primary`) — 增强阶段
- C×L×K 结构化实验网格搜索
- 配额感知调度（模拟器优先，真机按信息增益排序）
- 通过 `BrainProvider` 协议交互（框架级），内部可使用 QAgent 三 Agent 模式（领域级）

---

## 6.4 Contracts 设计

### 6.4.1 核心类型

| 类型 | 角色 | 阶段 |
|------|------|------|
| `QComputeExperimentSpec` | 用户输入 | Spec |
| `QComputeBackendSpec` | 后端规格 | Spec |
| `QComputeCircuitSpec` | 电路规格 | Spec |
| `QComputeNoiseSpec` | 噪声配置 | Spec |
| `QComputeRunPlan` | 编译产出 | Plan |
| `QComputeRunArtifact` | 执行产物 | Artifact |
| `QComputeEnvironmentReport` | 环境报告 | Report |
| `QComputeValidationReport` | 验证报告 | Report |
| `QComputeEvidenceBundle` | 证据打包 | Bundle |
| `QComputeStudySpec` | 研究规格 | Study |
| `QComputeStudyTrial` | 研究试验 | Study |
| `QComputeStudyReport` | 研究报告 | Study |

### 6.4.2 治理元数据

所有核心 contract 类型携带 MHE 治理元数据（对齐 `nektar` 约定）：

- `graph_metadata: dict[str, Any]`
- `candidate_identity: QComputeCandidateIdentity`
- `promotion_metadata: QComputePromotionMetadata`
- `checkpoint_refs: list[str]`
- `provenance_refs: list[str]`
- `trace_refs: list[str]`
- `scored_evidence: ScoredEvidence | None`
- `execution_policy: QComputeExecutionPolicy`

### 6.4.3 设计原则

- **后端无关**：同一套 Spec 描述模拟器和真机实验
- **噪声可表达**：`QComputeNoiseSpec` 支持 depolarizing / thermal_relaxation / real 模型
- **promotion-readable**：所有 report 携带 `blocks_promotion` 和 MHE `ValidationIssue`
- **首版约束**：只包含 Quafu + Qiskit Aer 后端，VQE/QAOA/QPE 三种 ansatz

---

## 6.5 包结构（目标）

```
MHE/src/metaharness_ext/qcompute/
├── __init__.py              # 公共 API re-export
├── manifest.json            # Gateway 入口清单
├── contracts.py             # 全部 Pydantic 模型
├── capabilities.py          # CAP_QCOMPUTE_* 常量
├── slots.py                 # QCOMPUTE_*_SLOT 常量
├── types.py                 # 共享字面量/枚举
├── gateway.py               # QComputeGatewayComponent
├── environment.py           # QComputeEnvironmentComponent
├── config_compiler.py       # QComputeConfigCompilerComponent
├── executor.py              # QComputeExecutorComponent
├── validator.py             # QComputeValidatorComponent (protected)
├── evidence.py              # QComputeEvidenceBuilder
├── policy.py                # QComputePolicyEngine
├── governance.py            # QComputeGovernanceAdapter
├── study.py                 # QComputeStudyComponent (增强阶段)
├── mitigation.py            # ZNE/REM 错误缓解（纯 NumPy）
├── fcidump.py               # FCIDUMP 解析器
├── fermion_mapper.py        # Fermion→Qubit 映射
├── mitigation_pennylane.py  # PennyLane 集成错误缓解
├── pennylane_aer.py         # PennyLane Aer 后端适配器
└── backends/
    ├── __init__.py
    ├── qiskit_aer.py        # Qiskit Aer 适配器
    ├── quafu.py             # quarkstudio 适配器
    └── mock.py              # MockBackend（测试用）
```

配套资产：

```
MHE/tests/
├── test_metaharness_qcompute_contracts.py
├── test_metaharness_qcompute_environment.py
├── test_metaharness_qcompute_compiler.py
├── test_metaharness_qcompute_executor.py
├── test_metaharness_qcompute_validator.py
├── test_metaharness_qcompute_policy.py
├── test_metaharness_qcompute_gateway.py
├── test_metaharness_qcompute_study.py
├── test_metaharness_qcompute_integration.py
└── test_metaharness_qcompute_manifest.py
```

---

## 6.6 外部依赖策略

### 6.6.1 必需依赖（首版）

| SDK | 最低版本 | 用途 |
|-----|---------|------|
| `qiskit` | ≥1.0 | 电路构造（QuantumCircuit） |
| `qiskit-aer` | ≥0.14 | 模拟器后端 |

### 6.6.2 可选依赖（运行时 try/except 检测）

| SDK | 最低版本 | 用途 | 检测时机 |
|-----|---------|------|---------|
| `quarkstudio` | ≥7.0 | Quafu 真机硬件（from quark import Task） | Environment.probe() |
| `quarkcircuit` | — | 芯片可视化（可选） | Environment.probe() |
| `qsteed` | ≥0.1.0 | 编译加速（VQPU） | ConfigCompiler |
| `tensorcircuit` | ≥2.0 | 变分加速器 | Study 组件 |
| `pyscf` | ≥2.0 | 活性空间选择 | ABACUS 联动 |

可选依赖 **首版**通过运行时 `try/except import` 检测。
若增强后 core `DependencySpec.optional_components`/`optional_capabilities` 已落地，
则改为在 manifest 中显式声明（见 6.7.5）。
缺失时降级而非失败。

### 6.6.3 环境变量

| 变量 | 用途 | 必需 |
|------|------|------|
| `Qcompute_Token` | Quafu 云端访问令牌 | 真机执行时 |
| `QISKIT_CACHE_DIR` | Qiskit 缓存目录 | 可选 |
| `ALIBABA_API_KEY` | QuafuCloud MCP 通道 | 可选 |

---

## 6.7 与 MHE 核心的集成面

QCompute 以增强后的 MHE core 为目标平台。以下映射关系基于
`MHE-core-enhancement-roadmap.md` 和 `mhe-extension-mhe-hazy-octopus.md` 的实施路径。

### 6.7.1 Core Run Contracts 对齐

增强后 MHE core 将提供 Protocol 级运行协议（`sdk/execution.py`），
QCompute 的具体类型满足这些 Protocol：

| Core Protocol | QCompute 类型 | 满足方式 |
|--------------|--------------|---------|
| `RunPlanProtocol` | `QComputeRunPlan` | structural subtyping（`plan_id`, `experiment_ref`, `target_backend`, `execution_params`） |
| `RunArtifactProtocol` | `QComputeRunArtifact` | structural subtyping（`artifact_id`, `plan_ref`, `status`, `raw_output_path`） |
| `EnvironmentReportProtocol` | `QComputeEnvironmentReport` | structural subtyping（`task_id`, `available`, `blocks_promotion`） |
| `ValidationOutcomeProtocol` | `QComputeValidationReport` | structural subtyping（`status`, `blocks_promotion`, `evidence_refs`） |
| `EvidenceBundleProtocol` | `QComputeEvidenceBundle` | structural subtyping（`bundle_id`, `evidence_refs`） |
| `AsyncExecutorProtocol` | `QuafuBackendAdapter` | 显式实现（`submit/poll/cancel/await_result`） |

QCompute 不需要继承 core 基类，只需字段名和类型匹配 Protocol 即可被 core 执行治理路径消费。

### 6.7.2 Core Execution Layer 使用

增强后 MHE core 将提供：
- `ExecutionStatus` 枚举（created/queued/running/completed/failed/timeout/cancelled）
- `JobHandle` 模型
- `FibonacciPollingStrategy`（延迟序列 1,1,2,3,5,8,13,21,34,55，上限 60s，总超时 600s）
- `AsyncExecutorProtocol`（submit/poll/cancel/await_result）

QCompute 的 Quafu backend adapter 实现 `AsyncExecutorProtocol`，
不再自行实现 Fibonacci 轮询逻辑，而是复用 core 提供的 `FibonacciPollingStrategy`。

### 6.7.3 Core Governance 增强

| Core 能力 | QCompute 使用方式 |
|----------|-----------------|
| `SafetyGate.evaluate_promotion()` | QComputeValidator 的领域验证结果通过 gate 进入正规评估路径 |
| `PolicyDecision.DEFER` | 噪声影响高时 defer（保留 candidate，不 commit，不 reject） |
| `MutationProposal.domain_payload` | Study 组件通过 domain_payload 携带 QComputeExperimentSpec |
| `ResourceQuota` | Quafu 真机每日配额通过 ResourceQuota 协议表达 |
| `ArtifactSnapshotStore` | RunArtifact / ValidationReport 持久化快照 |
| `FileSessionStore` | 执行事件持久化 |

### 6.7.4 Core Enhancement Phase 对齐

QCompute 的实现依赖增强后 MHE core 的特定 phase：

| Core Phase | 提供的能力 | QCompute 依赖 |
|-----------|----------|-------------|
| Phase 0 (模型增量) | `MutationProposal.domain_payload`、`DependencySpec.optional_*`、执行事件枚举 | QCompute Phase 0, 4 |
| Phase 1 (Run contracts) | `RunPlanProtocol`、`AsyncExecutorProtocol`、`FibonacciPollingStrategy` | QCompute Phase 1, 2 |
| Phase 2 (Run-level governance) | `evaluate_promotion` gates、tri-state policy、`ResourceQuota` | QCompute Phase 2, 3 |
| Phase 3 (Durable evidence) | `FileSessionStore`、`ArtifactSnapshotStore`、artifact lineage | QCompute Phase 3+ |
| Phase 4 (Optimizer) | `domain_payload` bridge in optimizer | QCompute Phase 4 |

QCompute Phase 0 可在 core Phase 0 之前启动（不依赖 `domain_payload`）。
QCompute Phase 1 需要 core Phase 1 的 run contracts protocols。
QCompute Phase 2 需要 core Phase 2 的 tri-state policy。

### 6.7.5 Manifest 增强

增强后 `DependencySpec` 将支持可选依赖声明：

```json
"deps": {
    "components": ["qcompute_environment", "qcompute_config_compiler", "qcompute_executor", "qcompute_validator"],
    "optional_components": ["qsteed_compiler"],
    "optional_capabilities": ["error_mitigation.zne", "error_mitigation.mem"]
}
```

若 core Phase 0 已落地 `optional_components`/`optional_capabilities`，
QCompute manifest 将直接使用这些字段替代当前的运行时 `try/except import` 方案。

### 6.7.6 QCompute 不自行实现

以下能力由增强后 MHE core 提供，QCompute 不重复实现：

- `SessionStore` / `SessionEvent`（由 core 提供）
- `SafetyPipeline`（由 core 执行）
- `commit_graph()` / `PromotionContext` 构建（由 `HarnessRuntime` 完成）
- `BrainProvider` 协议定义（由 `core/brain.py` 定义）
- `FibonacciPollingStrategy`（由 core `sdk/execution.py` 提供）
- `ArtifactSnapshotStore`（由 core `provenance/` 提供）
- `ResourceQuota` 协议（由 core `models.py` 提供，若已落地）
- Deferred candidate 生命周期管理（由 core governance 提供）

---

## 6.8 首版明确不做

| 排除项 | 原因 |
|--------|------|
| IBM Quantum / AWS Braket 后端 | 网络延迟和账户障碍；首版聚焦 Quafu |
| 本源 pyQPanda / 华为 MindQuantum | API 成熟度和生态绑定问题 |
| 脉冲级优化 | 门级电路是首版边界 |
| 自主量子纠错码设计 | QEC 前沿研究，不宜进入工程扩展 |
| HI-VQE handover 协议实现 | contract 预留，实现版不包含 |
| QSteed VQPU 强制集成 | 可选依赖，运行时检测 |
| QAgent 三 Agent 模式实现 | BrainProvider 实现细节，首版用简化 propose/evaluate |

---

## 6.9 与其他扩展的协作面

### ABACUS → QCompute
- ABACUS 输出 FCIDUMP 文件（哈密顿量）
- QCompute 读取 FCIDUMP，做活性空间选择 + Fermion→Qubit 映射
- 参考能量由 ABACUS DFT 提供
- 数据交换格式：FCIDUMP (ASCII) 为主，HDF5 为备选

### QCompute ↔ DeepMD / JEDI
- 间接协同，首版不涉及

---

## 6.10 结论

QCompute 在 MHE 中被设计为一个 **SDK-driven, backend-abstracted, noise-aware, evidence-contributing** 的量子计算 Worker。

它的实现路径是渐进式的：
1. 先在模拟器（Qiskit Aer）上打通完整闭环
2. 再接入 Quafu 真机后端
3. 再集成错误缓解（自实现 ZNE/REM）
4. 再构建 Study 组件（C×L×K）
5. 远期对接 ABACUS 的 HI-VQE 协同

每一步都是可独立验证的，不依赖后续步骤的完成。这份 blueprint 的用途，是作为 QCompute 代码实现与测试的统一架构底稿。
