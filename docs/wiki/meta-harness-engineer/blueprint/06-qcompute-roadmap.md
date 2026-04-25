# 06. QCompute Roadmap

> 状态：pre-implementation | 以 `qcompute-engine-wiki` (01–08) 和 `06-qcompute-extension-blueprint.md` 为准的执行路线图

## 6.1 推荐执行顺序

QCompute 是全新扩展，没有遗留代码。路线图采用 **模拟器优先、渐进接入** 策略，
并以增强后 MHE core 为目标平台。

```text
Phase 0: Scaffold + Contracts + Mock Backend             [当前阶段]
  -> Phase 1: Qiskit Aer Simulation Baseline             [完整模拟器闭环]
    -> Phase 2: Quafu Environment Probe + Real Backend    [真机接入]
      -> Phase 3: Error Mitigation (Mitiq)               [噪声对抗]
        -> Phase 4: Study Component (C×L×K)              [实验网格]
          -> Phase 5: ABACUS Integration                  [经典-量子协同]
```

### Core Enhancement Phase 对齐

QCompute 实现依赖增强后 MHE core 的特定 phase（参照 `MHE-core-enhancement-roadmap.md`）：

| QCompute Phase | Core Phase 依赖 | 说明 |
|---------------|----------------|------|
| Phase 0 | 无依赖（或 core Phase 0 并行） | 纯 contract 模型，不依赖 core 新能力 |
| Phase 1 | Core Phase 1（Run contracts） | 需要 `RunPlanProtocol`、`AsyncExecutorProtocol` 等协议 |
| Phase 2 | Core Phase 1 + 2 | 需要 `FibonacciPollingStrategy`、tri-state policy |
| Phase 3 | Core Phase 2 | 需要 `evaluate_promotion` gates |
| Phase 4 | Core Phase 0 + 4 | 需要 `domain_payload`、optimizer bridge |
| Phase 5 | Core Phase 1 | 需要 `RunPlanProtocol` 等 |

关键原则：

- 每个 Phase 都可独立验证，不依赖后续 Phase
- Phase 0–1 不需要任何量子硬件或 API token
- Phase 2 需要有效的 Quafu API token
- Phase 3–5 是增量增强，不影响已完成 Phase 的功能
- 所有 Phase 完成后都要求：测试通过、manifest 有效、文档同步
- QCompute 的 contracts 通过 structural subtyping 满足 core Protocol，不要求继承

通用验收标准：每个阶段完成后，相关测试全部通过，已有功能零回归，manifest 可被 MHE ComponentDiscovery 正常加载。

---

## 6.2 Phase 0：Scaffold + Contracts + Mock Backend

### 6.2.1 目标

建立 QCompute 扩展的骨架结构和类型系统。不涉及任何外部 SDK 或量子硬件。

### 6.2.2 交付内容

1. `src/metaharness_ext/qcompute/` 包结构（`__init__.py`、`types.py`）
2. `contracts.py`：全部 Pydantic 模型（Spec / Plan / Artifact / Report / Bundle / Study / 治理元数据）
3. `capabilities.py`：`CAP_QCOMPUTE_*` 常量 + `CANONICAL_CAPABILITIES`
4. `slots.py`：`QCOMPUTE_*_SLOT` 常量 + `PROTECTED_SLOTS`
5. `backends/mock.py`：确定性 MockBackend（返回预设 counts）
6. 对应 manifest JSON 文件
7. 基础测试套件：
   - `test_metaharness_qcompute_contracts.py`：序列化/反序列化 roundtrip
   - `test_metaharness_qcompute_manifest.py`：manifest 加载验证

### 6.2.3 验收标准

- 所有 contract 模型可通过 Pydantic 验证和 JSON roundtrip
- MockBackend 返回确定性结果
- Manifest 可被 `ComponentManifest.model_validate_json()` 正确解析
- 治理元数据字段（`candidate_identity`、`promotion_metadata` 等）存在于所有核心 contract 中
- `ruff check` + `ruff format` 零错误

---

## 6.3 Phase 1：Qiskit Aer Simulation Baseline

### 6.3.1 目标

在 Qiskit Aer 模拟器上打通完整的五阶段流水线。这是 QCompute 的 **最小可用闭环**。

### 6.3.2 交付内容

1. `environment.py`：探测 Qiskit Aer 可用性（版本检测、AerSimulator 能力）
   - 产出 `QComputeEnvironmentReport`（满足 core `EnvironmentReportProtocol`）
2. `config_compiler.py`：
   - 电路生成（从 `QComputeCircuitSpec` 到 Qiskit QuantumCircuit）
   - transpilation（`baseline` 策略，level 1）
   - 产出 `QComputeRunPlan`（满足 core `RunPlanProtocol`）
3. `executor.py`：
   - `backends/qiskit_aer.py`：AerBackendAdapter
   - 同步执行（模拟器无需异步轮询）
   - 产出 `QComputeRunArtifact`（满足 core `RunArtifactProtocol`）
4. `validator.py`：
   - 完整性检查（status、counts、shots）
   - 保真度计算（与理想结果对比）
   - 噪声影响评分（无噪声时 score ≈ 0）
   - 产出 `QComputeValidationReport`（满足 core `ValidationOutcomeProtocol`）
   - 含 `blocks_promotion` 和 `ScoredEvidence`
5. `evidence.py`：`QComputeEvidenceBundle` 构建（满足 core `EvidenceBundleProtocol`）
6. `policy.py`：基于 fidelity threshold 的 allow/reject/defer 判断
   - 使用 core `PolicyDecision` tri-state（若 core Phase 2 已落地）
   - 降级方案：自行定义 `QComputePolicyDecision` 枚举
7. `governance.py`：将 validation report 映射到 `ValidationIssue`
8. `gateway.py`：编排五阶段流水线，暴露 `run_baseline()`
9. 测试套件：
   - 单元测试：每个组件独立测试（用 MockBackend 或 Aer）
   - 集成测试：Bell 态端到端（模拟器）
   - 集成测试：VQE H₂ 最小闭环
   - Protocol 满足性测试：确认 QCompute 类型满足 core Protocol

### 6.3.3 验收标准

- Bell 态模拟器测试通过：结果只含 `|00⟩` 和 `|11⟩`
- VQE H₂ 能量误差 < 0.1 Hartree
- Validator 能正确区分 `VALIDATED` / `BELOW_FIDELITY_THRESHOLD` / `EXECUTION_FAILED`
- `blocks_promotion` 在以下场景为 True：执行失败、保真度低于阈值、环境前提不满足
- Policy engine 正确执行 allow（保真度高于阈值）/ reject（前提失败）/ defer（噪声影响高）
- `ScoredEvidence` 被正确构建并附着到 evidence bundle
- 所有组件遵循 `HarnessComponent` 生命周期（`declare_interface` / `activate` / `deactivate`）
- `commit_graph()` 路径通过 `HarnessRuntime` 验证

---

## 6.4 Phase 2：Quafu Environment Probe + Real Backend

### 6.4.1 目标

接入 Quafu 真机后端，增加环境探测、配额感知、异步执行能力。

### 6.4.2 交付内容

1. `backends/quafu.py`：QuafuBackendAdapter（pyQuafu SDK）
   - 实现 core `AsyncExecutorProtocol`（submit/poll/cancel/await_result）
   - 使用 core `FibonacciPollingStrategy`（若 core Phase 1 已落地）
   - 降级方案：QCompute 内置 Fibonacci 轮询实现
2. `environment.py` 增强：
   - Quafu 芯片在线/维护状态查询
   - 校准数据采集（T1/T2、门保真度、读出误差）
   - API token 有效性验证
   - 每日配额余量查询 → 若 core `ResourceQuota` 已落地，则通过该协议表达
   - 校准时效性检查（3h 警告、24h 阻断）
3. `executor.py` 增强：
   - 异步任务提交（Quafu 真机）
   - 使用 core `JobHandle` 模型（若 core Phase 1 已落地）
   - 异常分类（retriable vs non-retriable）
   - 重试策略（QueueTimeoutError 最多 3 次，NetworkConnectivityError 指数退避）
4. `config_compiler.py` 增强：
   - `sabre` 编译策略（level 3, swap_trials=200）
5. 测试：
   - 环境探测单元测试（mock pyQuafu）
   - 异步轮询逻辑测试
   - 校准时效性测试
   - 配额感知调度测试
   - 真机冒烟测试（需 `QUAFU_API_TOKEN`，标记 `@pytest.mark.quafu`）

### 6.4.3 前提条件

- pyQuafu SDK 已安装（`pip install pyquafu`）
- 有效的 `QUAFU_API_TOKEN` 环境变量（真机测试）

### 6.4.4 验收标准

- Environment.probe() 能正确报告后端可用性、校准状态、配额余量
- 校准超过 24h 时 `blocks_promotion=True`
- 异步轮询在超时后正确失败
- retriable 异常触发重试，non-retriable 异常立即失败
- 真机冒烟测试（如可用）完成最小电路提交
- 模拟器测试在 Phase 2 后仍全部通过（零回归）

---

## 6.5 Phase 3：Error Mitigation (Mitiq)

### 6.5.1 目标

通过 Mitiq 集成错误缓解能力，提升噪声环境下的结果质量。

### 6.5.2 交付内容

1. `executor.py` 增强：
   - `_apply_error_mitigation()` 方法
   - ZNE 集成（`mitiq.zne.execute_with_zne` + `AdaExpFactory`）
   - REM 集成（`mitiq.rem`）
   - 错误缓解开销通过 `QComputeExecutionPolicy` 记录
   - 噪声影响评分高时，若 core tri-state policy 已落地，可产出 `DEFER` 决策
2. `config_compiler.py` 增强：
   - 噪声模型集成（depolarizing / thermal_relaxation）
3. 测试：
   - ZNE 集成测试：噪声模拟器 + ZNE → 改善能量估计
   - 噪声影响评分验证：有噪声时 score > 0，ZNE 后 score 下降
   - 校准数据作为噪声模型输入的测试

### 6.5.3 前提条件

- Mitiq 已安装（`pip install mitiq`）
- Phase 1 已完成（模拟器基线）

### 6.5.4 验收标准

- ZNE 在噪声模拟器上改善能量估计（noise_impact_score 下降）
- 错误缓解叠加开销公式正确反映在 execution_policy 中
- 无 Mitiq 时不影响模拟器执行（优雅降级）
- Quafu Cup Bell 态基准测试：保真度 > 0.95（模拟器 + 噪声 + ZNE）

---

## 6.6 Phase 4：Study Component (C×L×K)

### 6.6.1 目标

实现 Study 组件，支持结构化的实验网格搜索和 Agent 驱动的优化闭环。

### 6.6.2 交付内容

1. `study.py`：`QComputeStudyComponent`
   - `run_study()`：执行完整 study
   - `run_single_trial()`：单次试验
   - `evaluate_pareto_front()`：Pareto 最优选择
   - 使用 `MutationProposal.domain_payload` 携带 `QComputeExperimentSpec`（若 core Phase 0 已落地）
2. Family 类型：`AnsatzFamily`、`BackendFamily`、`ErrorMitigationFamily`
3. 配额感知调度：模拟器优先，真机按信息增益排序
4. `agentic` 策略：通过 `BrainProvider` 协议交互
5. RPUCB 轨迹上下文选择
6. 轨迹级评分（`trajectory_score`）
7. 测试：
   - Study 调度逻辑测试（mock gateway）
   - Pareto 前沿计算测试
   - 配额感知调度测试
   - 轨迹级评分测试

### 6.6.3 验收标准

- Study 组件能执行 grid search（ansatz × backend × error_mitigation）
- Pareto 前沿正确识别（多目标：保真度 × 深度 × SWAP）
- 配额约束正确限制真机 trial 数量
- `trajectory_score` 反映整条轨迹的最终评分
- `BrainProvider` 集成点可被 mock 测试验证

---

## 6.7 Phase 5：ABACUS Integration

### 6.7.1 目标

建立 ABACUS → QCompute 的经典-量子协同工作流。

### 6.7.2 交付内容

1. FCIDUMP 解析器（`config_compiler.py` 增强）
2. 活性空间选择（调用 PySCF，可选依赖）
3. Fermion→Qubit 映射（Jordan-Wigner 默认，Bravyi-Kitaev 可选）
4. VQE 能量与 DFT 参考能量对比
5. `provenance_inputs` 引用 ABACUS 产出的哈密顿量 artifact
6. 测试：
   - FCIDUMP 解析测试
   - Fermion→Qubit 映射正确性测试
   - ABACUS → QCompute 端到端联调测试（mock ABACUS 输出）

### 6.7.3 前提条件

- Phase 1 已完成
- PySCF 已安装（可选，`pip install pyscf`）
- FCIDUMP 测试数据可用

### 6.7.4 验收标准

- FCIDUMP 文件可被正确解析为哈密顿量
- Jordan-Wigner 映射后的 qubit 数量与 active_space 一致
- VQE 能量与 DFT 参考能量可在 evidence bundle 中对比
- `provenance_inputs` 正确引用上游 ABACUS artifact

---

## 6.8 测试路线图

### 分层策略

| 层 | 内容 | 外部依赖 | 标记 |
|----|------|---------|------|
| Layer 1 | 单元测试（contracts、validator 逻辑、policy 门控、校准时效性） | 无 | 默认 |
| Layer 2 | 集成测试（Qiskit Aer 端到端、噪声模型、Study 网格） | qiskit-aer | `@pytest.mark.integration` |
| Layer 3 | 真机冒烟测试（Quafu） | pyQuafu + token | `@pytest.mark.quafu` |

### 测试覆盖矩阵

| 覆盖维度 | Phase 0 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|---------|---------|---------|---------|---------|---------|---------|
| Contracts 序列化 | ✅ | — | — | — | — | — |
| Manifest 加载 | ✅ | — | — | — | — | — |
| Validator 逻辑 | — | ✅ | ✅ | ✅ | — | ✅ |
| Policy 门控 | — | ✅ | ✅ | — | — | — |
| Aer 模拟器执行 | — | ✅ | — | ✅ | ✅ | ✅ |
| Bell 态端到端 | — | ✅ | — | — | — | — |
| VQE H₂ 闭环 | — | ✅ | — | — | — | ✅ |
| 噪声模型 | — | — | — | ✅ | — | — |
| Mitiq ZNE | — | — | — | ✅ | — | — |
| Quafu 环境探测 | — | — | ✅ | — | — | — |
| Quafu 真机执行 | — | — | ✅ | ✅ | — | — |
| Study 调度 | — | — | — | — | ✅ | — |
| Pareto 前沿 | — | — | — | — | ✅ | — |
| FCIDUMP 解析 | — | — | — | — | — | ✅ |
| Fermion 映射 | — | — | — | — | — | ✅ |
| Governance 适配 | — | ✅ | ✅ | ✅ | ✅ | ✅ |
| Promotion readiness | — | ✅ | ✅ | ✅ | — | ✅ |

---

## 6.9 远期扩展（不在首版 roadmap 内）

| 方向 | 说明 | 优先级 |
|------|------|--------|
| HI-VQE handover 协议 | 经典-量子信息交接迭代 | 中远期 |
| IBM Quantum 后端 | `ibm_quantum` 平台适配器 | 中 |
| TensorCircuit 后端 | JAX 自动微分加速变分优化 | 中 |
| QAgent 三 Agent 模式 | Planner-Coder-Reviewer 内部架构 | 中 |
| QSteed VQPU 强制集成 | 编译加速器深度集成 | 近期（可选） |
| Quafu MCP 深度集成 | 超越 SDK 的 MCP 工具调用 | 近期 |
| 量子数据同化 | QCompute ↔ JEDI 交叉 | 远期 |

---

## 6.10 完成标准

首版路线图完成的标准：

1. **Phase 0–3 完成**：模拟器 + 真机 + 错误缓解 可用
2. **Phase 4 完成**：Study 组件支持 grid 和 agentic 搜索
3. **测试覆盖**：Layer 1 和 Layer 2 测试全部通过
4. **Governance 对齐**：所有 contract 携带治理元数据，Validator 作为 evidence contributor 正确产出 `blocks_promotion` 和 `ScoredEvidence`
5. **Manifest 有效**：所有 manifest 可被 MHE ComponentDiscovery 正确加载
6. **零回归**：每个 Phase 完成后，前序 Phase 的测试仍然全部通过
7. **文档同步**：wiki、blueprint、roadmap 与代码实现保持一致
