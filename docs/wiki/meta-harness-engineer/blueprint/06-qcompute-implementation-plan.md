# 06. QCompute Implementation Plan

> 状态：Phase 0–4 implemented | Phase 5 pending | 对 `06-qcompute-roadmap.md` Phase 0–5 的逐步实施计划

## Technical Alignment Notes

本 implementation plan 以以下文档为事实基线：

- `qcompute-engine-wiki/` (01–08) —— 设计规格
- `06-qcompute-extension-blueprint.md` —— 架构蓝图
- `06-qcompute-roadmap.md` —— 阶段路线图
- `MHE-core-enhancement-roadmap.md` —— Core 增强路线图

实现与评审遵循以下技术事实：

**当前已确认的 core 能力**：
- MHE `HarnessComponent` 基类提供 `declare_interface()` / `activate()` / `deactivate()` 生命周期钩子
- `ComponentManifest` schema 包含 `deps`、`bins`、`env`、`provides`、`requires` 字段
- `PromotionContext`、`ValidationIssue.blocks_promotion`、`ScoredEvidence`、`SessionEvent` 已存在于 `core/models.py`
- `BrainProvider` protocol 签名：`propose(optimizer, observations) -> list[MutationProposal]`、`evaluate(optimizer, proposal, observations) -> ProposalEvaluation`
- Nektar 和 ABACUS 的 contract 模式已包含治理元数据字段（`candidate_identity`、`promotion_metadata` 等），QCompute 应遵循相同模式
- Qiskit ≥1.0 使用新式 API（`qiskit.transpiler.preset_passmanagers`、`QuantumCircuit` 无需 `QuantumRegister`）
- pyQuafu 使用 `execute_task()` / `query_task()` 异步任务模型

**Core Enhancement 路线图对齐**（参照 `MHE-core-enhancement-roadmap.md`）：
- Core Phase 0：`MutationProposal.domain_payload`、`DependencySpec.optional_components`/`optional_capabilities`
- Core Phase 1：`RunPlanProtocol` / `RunArtifactProtocol` / `EnvironmentReportProtocol` / `ValidationOutcomeProtocol` / `EvidenceBundleProtocol`（Protocol 级，不要求继承）、`AsyncExecutorProtocol`、`FibonacciPollingStrategy`、`JobHandle`
- Core Phase 2：`SafetyGate.evaluate_promotion()`、`PolicyDecision` tri-state、`ResourceQuota`
- Core Phase 3：`FileSessionStore`、`ArtifactSnapshotStore`、scientific artifact lineage
- Core Phase 4：`domain_payload` bridge in optimizer

**实现策略**：QCompute 以增强后 MHE core 为目标平台。对于尚未落地的 core 能力，
每个步骤标注 **降级方案**——即不依赖 core 新能力时的本地实现。
当 core 能力落地后，通过 adapter 层切换，不改变 QCompute 的 contract 定义。

---

## Phase 0：Scaffold + Contracts + Mock Backend

### P0.1 创建包结构

**文件**：`src/metaharness_ext/qcompute/__init__.py`

- 空包骨架，后续步骤填充 re-exports

**文件**：`src/metaharness_ext/qcompute/types.py`

- `QComputeExecutionMode = Literal["simulate", "run", "hybrid"]`
- `QComputeValidationStatus` 枚举（8 个值）

**文件**：`src/metaharness_ext/qcompute/slots.py`

```python
QCOMPUTE_GATEWAY_SLOT = "qcompute_gateway.primary"
QCOMPUTE_ENVIRONMENT_SLOT = "qcompute_environment.primary"
QCOMPUTE_CONFIG_COMPILER_SLOT = "qcompute_config_compiler.primary"
QCOMPUTE_EXECUTOR_SLOT = "qcompute_executor.primary"
QCOMPUTE_VALIDATOR_SLOT = "qcompute_validator.primary"
QCOMPUTE_STUDY_SLOT = "qcompute_study.primary"
PROTECTED_SLOTS = frozenset({QCOMPUTE_VALIDATOR_SLOT})
```

**文件**：`src/metaharness_ext/qcompute/capabilities.py`

```python
CAP_QCOMPUTE_CASE_COMPILE = "qcompute.compile.case"
CAP_QCOMPUTE_ENV_PROBE = "qcompute.environment.probe"
CAP_QCOMPUTE_CIRCUIT_COMPILE = "qcompute.circuit.compile"
CAP_QCOMPUTE_CIRCUIT_RUN = "qcompute.circuit.run"
CAP_QCOMPUTE_RESULT_VALIDATE = "qcompute.result.validate"
CAP_QCOMPUTE_EVIDENCE_BUILD = "qcompute.evidence.build"
CAP_QCOMPUTE_POLICY_EVALUATE = "qcompute.policy.evaluate"
CAP_QCOMPUTE_GOVERNANCE_REVIEW = "qcompute.governance.review"
CAP_QCOMPUTE_STUDY_RUN = "qcompute.study.run"
CANONICAL_CAPABILITIES = frozenset({...})
```

### P0.2 Contracts 模型

**文件**：`src/metaharness_ext/qcompute/contracts.py`

按 `qcompute-engine-wiki/03` 中的定义实现全部 Pydantic 模型。创建顺序：

1. 治理元数据类型：
   - `QComputeCandidateIdentity`
   - `QComputePromotionMetadata`
   - `QComputeExecutionPolicy`

2. Spec 类型：
   - `QComputeBackendSpec`
   - `QComputeCircuitSpec`
   - `QComputeNoiseSpec`
   - `QComputeExperimentSpec`（含治理元数据字段）

3. Plan 类型：
   - `QComputeExecutionParams`
   - `QComputeRunPlan`（含治理元数据字段）

4. Report 类型：
   - `QComputeCalibrationData`
   - `CalibrationSnapshot`
   - `QComputeEnvironmentReport`
   - `QComputeValidationMetrics`
   - `QComputeValidationReport`（含 `scored_evidence`、治理元数据字段）

5. Artifact 类型：
   - `QComputeRunArtifact`（含 `scored_evidence`、治理元数据字段）

6. Bundle 类型：
   - `QComputeEvidenceBundle`

7. Study 类型：
   - `QComputeStudyAxis`
   - `QComputeStudySpec`
   - `QComputeStudyTrial`
   - `QComputeStudyReport`

关键实现细节：
- 从 `metaharness.core.models` 导入 `ScoredEvidence`
- 所有治理元数据字段使用 `Field(default_factory=...)` 提供默认值
- `QComputeValidationReport` 不直接 import `ValidationIssue`，而是在 governance adapter 中做映射

### P0.3 Mock Backend

**文件**：`src/metaharness_ext/qcompute/backends/__init__.py`

**文件**：`src/metaharness_ext/qcompute/backends/mock.py`

```python
class MockQuantumBackend:
    def __init__(self, deterministic_counts: dict[str, int]) -> None:
        self._counts = deterministic_counts

    def run(self, circuit, shots: int = 1024) -> dict[str, int]:
        return self._counts
```

### P0.4 Manifest JSON

**文件**：`src/metaharness_ext/qcompute/manifest.json`

Gateway manifest，参照 nektar 格式。注意：
- 不含 `optional_deps`（不在 ComponentManifest schema 中）
- `kind: "core"`，`safety.protected: false`
- `policy.sandbox.tier: "workspace-read"`

### P0.5 测试

**文件**：`tests/test_metaharness_qcompute_contracts.py`

- `test_experiment_spec_roundtrip`：序列化 + 反序列化
- `test_validation_report_issues`：status → blocks_promotion 映射
- `test_governance_metadata_defaults`：治理字段有默认值
- `test_study_spec_roundtrip`：Study 类型序列化

**文件**：`tests/test_metaharness_qcompute_manifest.py`

- `test_gateway_manifest_loads`：manifest 可被 ComponentManifest 解析
- `test_gateway_manifest_provides`：provides 列表正确

### P0 验收

- `pytest tests/test_metaharness_qcompute_contracts.py tests/test_metaharness_qcompute_manifest.py` 通过
- `ruff check src/metaharness_ext/qcompute/` 零错误

---

## Phase 1：Qiskit Aer Simulation Baseline

### P1.1 Environment 组件

**文件**：`src/metaharness_ext/qcompute/environment.py`

- 继承 `HarnessComponent`
- `declare_interface()`：声明 input `backend_spec`、output `environment_report`、capability `qcompute.environment.probe`
- `activate()`：无特殊初始化
- `probe()`：
  - 检测 `qiskit_aer` 可用性（try/except import）
  - 获取 AerSimulator 版本
  - 报告 qubit_count_available（Aer 无硬限制，取 None）
  - 生成 `QComputeEnvironmentReport`

### P1.2 ConfigCompiler 组件

**文件**：`src/metaharness_ext/qcompute/config_compiler.py`

- `declare_interface()`：声明 capability `qcompute.circuit.compile`
- `compile()`：
  - 根据 `QComputeCircuitSpec` 构建 Qiskit QuantumCircuit
  - 处理 `openqasm` 直接提供 vs `ansatz` 模板生成两种模式
  - transpilation：`generate_preset_pass_manager(optimization_level=1, ...)` + `pm.run(circuit)`
  - 收集编译元数据（depth、SWAP count）
  - 构建 `QComputeRunPlan`

### P1.3 Executor 组件

**文件**：`src/metaharness_ext/qcompute/executor.py`

- `declare_interface()`：声明 capability `qcompute.circuit.run`
- `execute_plan()`：
  - 根据 `RunPlan.target_backend.platform` 选择适配器
  - `backends/qiskit_aer.py`：`AerSimulator().run(circuit, shots=shots).result()`
  - 构建 `QComputeRunArtifact`

**文件**：`src/metaharness_ext/qcompute/backends/qiskit_aer.py`

- AerBackendAdapter：封装 `AerSimulator` 调用
- 支持噪声模型（`NoiseModel.from_backend` 或自定义 depolarizing）

### P1.4 Validator 组件

**文件**：`src/metaharness_ext/qcompute/validator.py`

- `protected: bool = True`
- `declare_interface()`：声明 capability `qcompute.result.validate`，slot `qcompute_validator.primary`
- `validate()`：
  - 完整性检查：`artifact.status == "completed"`，counts 非空
  - 保真度计算：与理想模拟器结果对比（如有参考）
  - VQE 能量误差：`abs(energy - energy_target)`（如有 energy_target）
  - 构建 `QComputeValidationReport`，含 `blocks_promotion`
  - 构建 `ScoredEvidence`

### P1.5 Evidence + Policy + Governance

**文件**：`src/metaharness_ext/qcompute/evidence.py`

- `build_bundle()`：组装 `QComputeEvidenceBundle`

**文件**：`src/metaharness_ext/qcompute/policy.py`

- `evaluate()`：基于 fidelity_threshold / noise_impact_score 的 allow/reject/defer

**文件**：`src/metaharness_ext/qcompute/governance.py`

- `map_to_validation_issues()`：`QComputeValidationReport` → `list[ValidationIssue]`

### P1.6 Gateway 组件

**文件**：`src/metaharness_ext/qcompute/gateway.py`

- `declare_interface()`：声明 input/output/capability
- `activate()`：获取 env / compiler / executor / validator 引用
- `compile_experiment()`：编排 Environment → ConfigCompiler
- `run_baseline()`：编排完整五阶段流水线

### P1.7 测试

**文件**：`tests/test_metaharness_qcompute_environment.py`
- `test_aer_environment_probe`：检测 Aer 可用性
- `test_aer_environment_report`：报告结构正确

**文件**：`tests/test_metaharness_qcompute_compiler.py`
- `test_bell_state_compilation`：Bell 态电路生成 + transpilation
- `test_custom_openqasm`：OpenQASM 直接提供路径
- `test_vqe_ansatz_generation`：VQE ansatz 模板生成

**文件**：`tests/test_metaharness_qcompute_executor.py`
- `test_aer_bell_state_execution`：Aer 执行 Bell 态
- `test_mock_backend_execution`：MockBackend 确定性结果
- `test_aer_with_noise_model`：噪声模型下的执行

**文件**：`tests/test_metaharness_qcompute_validator.py`
- `test_validate_completed_run`：正常执行通过验证
- `test_validate_failed_run`：失败执行标记 `EXECUTION_FAILED`
- `test_validate_below_fidelity`：低保真度标记 `BELOW_FIDELITY_THRESHOLD`
- `test_blocks_promotion_mapping`：validation status → blocks_promotion 正确映射

**文件**：`tests/test_metaharness_qcompute_policy.py`
- `test_allow_high_fidelity` / `test_reject_precondition_failed` / `test_defer_high_noise`

**文件**：`tests/test_metaharness_qcompute_gateway.py`
- `test_bell_state_simulate`：端到端 Bell 态（集成测试）
- `test_vqe_h2_minimal`：VQE H₂ 最小闭环（集成测试）

### P1 验收

- `pytest tests/test_metaharness_qcompute_*.py` 全部通过
- Bell 态结果只含 `|00⟩` 和 `|11⟩`
- VQE H₂ 能量误差 < 0.1 Hartree
- `ruff check` + `ruff format` 零错误

---

## Phase 2：Quafu Environment Probe + Real Backend

### P2.1 Quafu Backend Adapter

**文件**：`src/metaharness_ext/qcompute/backends/quafu.py`

- `try: import pyquafu` 检测可用性
- QuafuBackendAdapter 实现 core `AsyncExecutorProtocol`（若 core Phase 1 已落地）：
  - `submit(plan) -> JobHandle` → 提交电路到 Quafu
  - `poll(job_id) -> ExecutionStatus` → 查询任务状态
  - `cancel(job_id)` → 取消排队中的任务
  - `await_result(job_id, timeout) -> dict[str, int]` → 等待结果
- 使用 core `FibonacciPollingStrategy` 管理轮询延迟（若已落地）
- **降级方案**：QCompute 内置 Fibonacci 轮询实现（不依赖 core）

### P2.2 Environment 增强

在 `environment.py` 中增加：
- `Quafu` 芯片状态查询（`pyquafu.get_backend_info()`）
- 校准数据采集 → `QComputeCalibrationData`
- Token 有效性验证
- 配额余量查询 → 若 core `ResourceQuota` 已落地，通过该协议表达；否则通过 `QComputeExecutionPolicy.daily_quota` 记录
- `_check_calibration_freshness()`：3h 警告、24h 阻断

### P2.3 Executor 增强

在 `executor.py` 中增加：
- 异步任务提交（Quafu 真机）
- 使用 core `JobHandle` 模型（若 core Phase 1 已落地）
- 异常分类（`QueueTimeoutError` retriable / `CircuitTopologyError` non-retriable）
- 重试逻辑

### P2.4 ConfigCompiler 增强

- `sabre` 策略：`generate_preset_pass_manager(optimization_level=3)` + `swap_trials=200`

### P2.5 测试

- `test_metaharness_qcompute_environment.py`：增加 Quafu mock 探测测试
- 校准时效性测试（fresh / stale / very_stale）
- 异步轮询逻辑测试
- 配额感知调度测试
- `@pytest.mark.quafu` 真机冒烟测试

### P2 验收

- 环境探测能正确区分 Aer 可用 / Quafu 可用 / 两者可用
- 校准 24h 过期 → `blocks_promotion=True`
- 异步超时正确失败
- Phase 1 测试零回归

---

## Phase 3：Error Mitigation (Mitiq)

### P3.1 Mitiq 集成

在 `executor.py` 中增加 `_apply_error_mitigation()`：

```python
async def _apply_error_mitigation(self, circuit, strategies, executor_func):
    if "zne" in strategies:
        result = zne.execute_with_zne(
            circuit, executor_func,
            factory=zne.inference.AdaExpFactory(scale_factor=2.0, steps=5),
            scale_noise=fold_global,
        )
    return result
```

当噪声影响评分高时，若 core tri-state policy（`PolicyDecision.DEFER`）已落地，
policy engine 可产出 defer 决策——保留 candidate 不 commit 也不 reject，等待补充 evidence。

### P3.2 噪声模型

在 `config_compiler.py` 或 `executor.py` 中：
- `QComputeNoiseSpec.model == "depolarizing"` → `noise.depolarizing_error()`
- `QComputeNoiseSpec.model == "thermal_relaxation"` → `noise.thermal_relaxation_error()`

### P3.3 测试

- ZNE 集成测试：噪声模拟器 + ZNE → 改善能量估计
- 噪声影响评分验证
- Quafu Cup Bell 态基准测试

### P3 验收

- ZNE 在噪声下改善结果
- 无 Mitiq 时不影响模拟器执行
- Phase 0–2 测试零回归

---

## Phase 4：Study Component (C×L×K)

### P4.1 Study 组件

**文件**：`src/metaharness_ext/qcompute/study.py`

- `run_study()`：接受 `QComputeStudySpec`，执行 C×L×K 网格
- `run_single_trial()`：单次 trial → `QComputeStudyTrial`
- `evaluate_pareto_front()`：多目标 Pareto 选择
- `_schedule_trials()`：配额感知调度
- `_select_trajectory_context()`：RPUCB 轨迹选择

### P4.2 Family 类型

在 `contracts.py` 中增加：
- `AnsatzFamily`
- `BackendFamily`
- `ErrorMitigationFamily`

### P4.3 BrainProvider 集成

Study 的 `agentic` 策略调用 `BrainProvider.propose()` / `evaluate()`。
首版提供一个简化 `FunctionalBrainProvider` 实现。

### P4.4 测试

- Study 调度逻辑测试
- Pareto 前沿计算测试
- 配额感知调度测试
- 轨迹级评分测试

### P4 验收

- Grid search 可执行
- Pareto 前沿正确
- Phase 0–3 测试零回归

---

## Phase 5：ABACUS Integration

### P5.1 FCIDUMP 解析器

在 `config_compiler.py` 中增加 FCIDUMP 解析：
- 读取 FCIDUMP ASCII 格式
- 提取一电子、二电子积分
- 构建 Qiskit Nature Hamiltonian

### P5.2 活性空间选择

- `try: import pyscf` 检测
- 从全轨道中选择 active 子集
- 输出 `active_space` 规格

### P5.3 Fermion→Qubit 映射

- Jordan-Wigner（默认）
- Bravyi-Kitaev（可选）

### P5.4 VQE 能量对比

- VQE 能量 vs `reference_energy`（DFT）
- 映射到 `energy_error` metric

### P5.5 测试

- FCIDUMP 解析测试（用 H₂ 最小测试数据）
- Fermion→Qubit 映射正确性测试
- ABACUS → QCompute 联调测试（mock FCIDUMP 输入）
- `provenance_inputs` 引用验证

### P5 验收

- FCIDUMP 正确解析
- 映射后 qubit 数与 active_space 一致
- VQE 能量与 DFT 参考可对比
- Phase 0–4 测试零回归

---

## 依赖安装顺序

```bash
# Phase 0–1：必需
pip install qiskit>=1.0 qiskit-aer>=0.14

# Phase 2：可选（真机）
pip install pyquafu>=0.1.0

# Phase 3：可选（错误缓解）
pip install mitiq>=0.30

# Phase 4：无新依赖

# Phase 5：可选（ABACUS 联动）
pip install pyscf>=2.0
```

---

## 实现顺序总表

| 步骤 | Phase | 主要文件 | 前置依赖 |
|------|-------|---------|---------|
| P0.1 | 0 | `__init__.py`, `types.py`, `slots.py`, `capabilities.py` | 无 |
| P0.2 | 0 | `contracts.py` | P0.1 |
| P0.3 | 0 | `backends/mock.py` | P0.2 |
| P0.4 | 0 | `manifest.json` | P0.1 |
| P0.5 | 0 | `test_contracts.py`, `test_manifest.py` | P0.2, P0.4 |
| P1.1 | 1 | `environment.py` | P0.2 |
| P1.2 | 1 | `config_compiler.py` | P0.2 |
| P1.3 | 1 | `executor.py`, `backends/qiskit_aer.py` | P0.2, P0.3 |
| P1.4 | 1 | `validator.py` | P0.2 |
| P1.5 | 1 | `evidence.py`, `policy.py`, `governance.py` | P0.2, P1.4 |
| P1.6 | 1 | `gateway.py` | P1.1–P1.5 |
| P1.7 | 1 | 全部 Phase 1 测试 | P1.6 |
| P2.1 | 2 | `backends/quafu.py` | P1.3 |
| P2.2 | 2 | `environment.py` 增强 | P2.1 |
| P2.3 | 2 | `executor.py` 增强 | P2.1 |
| P2.4 | 2 | `config_compiler.py` 增强 | P1.2 |
| P2.5 | 2 | Phase 2 测试 | P2.1–P2.4 |
| P3.1 | 3 | `executor.py` 增强（Mitiq） | P1.3 |
| P3.2 | 3 | 噪声模型 | P1.2 |
| P3.3 | 3 | Phase 3 测试 | P3.1 |
| P4.1 | 4 | `study.py` | P1.6 |
| P4.2 | 4 | Family 类型（contracts.py 增强） | P0.2 |
| P4.3 | 4 | BrainProvider 集成 | P4.1 |
| P4.4 | 4 | Phase 4 测试 | P4.1–P4.3 |
| P5.1 | 5 | FCIDUMP 解析器 | P1.2 |
| P5.2 | 5 | 活性空间选择 | P5.1 |
| P5.3 | 5 | Fermion→Qubit 映射 | P5.1 |
| P5.4 | 5 | VQE 能量对比 | P5.3 |
| P5.5 | 5 | Phase 5 测试 | P5.1–P5.4 |
