# QCompute Extension — Feasibility Improvement Plan

> 基于 `research/` 目录 7 份深度研究报告与当前 QCompute wiki v0.1 的逐文件交叉分析。
> 共识别 **19 项具体改进**，按优先级排序：P0 = 首版必须修正，P1 = 增强 feasibility，P2 = 远期优化。

---

## 一、`02-workflow-and-components.md` — 流水线与组件设计

### 1.1 [P0] ConfigCompiler 增加 Qiskit transpiler level 映射

**研究发现**：Qiskit transpiler 有 4 级优化（0=trivial, 1=standard, 2=enhanced, 3=maximum），SabreLayout 的关键参数（`layout_trials`, `swap_trials`, `max_iterations`）从 20→200 可额外减少 10% SWAP。QSteed 的 VQPU 选择 + Qiskit L3 编译可在百花芯片上产生 15-20% 的深度减少。

**wiki 当前状态**：`02-workflow-and-components.md` 中定义了 `compilation_strategy` 枚举 `["baseline", "sabre", "agentic"]`，但未将其映射到具体 transpiler 参数。

**改进**：在 2.4.1 节增加以下编译策略到 transpiler 参数的映射表：

| QCompute strategy | Qiskit level | SabreLayout trials | QSteed VQPU |
|---|---|---|---|
| `baseline` | 1 | 20 (default) | 否 |
| `sabre` | 3 | 200 | 否 |
| `agentic` | 3 | 200+ (iterative) | 是 |

### 1.2 [P0] Executor 增加异步轮询与异常分类

**研究发现**：pyQuafu 的 `task.send()` 返回 job 对象，状态枚举为 Created/In Queue/Running/Completed/Failed。推荐轮询策略是起始 1s 按斐波那契数列递增至 60s 上限。异常明确分为可重试（QueueTimeoutError, NetworkConnectivityError）和不可重试（CircuitTopologyError, QuotaExceededError）。任务仅在 In Queue 状态下可取消。

**wiki 当前状态**：`02-workflow-and-components.md` 2.5 节 Executor 只提到 `execute_plan()` 和 `execute_batch()`，未涉及异步生命周期管理。

**改进**：在 2.5 节增加 `_poll_job_with_backoff()` 伪代码和异常分类表。在 `QComputeRunArtifact` 增加 `retry_count` 和 `terminal_error_type` 字段。

### 1.3 [P1] 增加 Quafu MCP 双通道适配描述

**研究发现**：QuafuCloud MCP 暴露 4 个工具：`list_backends`, `submit_qasm`, `get_result`, `calculate_observable`。MCP 适合快速原型和自然语言交互，SDK 适合需要低延迟和细粒度控制的变分算法迭代。

**wiki 当前状态**：未明确区分 MCP 和 SDK 的使用场景。

**改进**：在 2.5 节增加 MCP 通道的说明和选择决策树：

```
QComputeExecutor 通道选择:
  ├─ mode="simulate" → 直接使用 Qiskit Aer (SDK)
  ├─ mode="run" + 需要细粒度控制 → pyQuafu SDK
  └─ mode="run" + 快速原型/自然语言 → QuafuCloud MCP
```

### 1.4 [P1] 采纳 QAgent 的 Planner-Coder-Reviewer 模式

**研究发现**：QAgent 的三 Agent 架构（Planner 分解任务 → Coder 实现电路 → Reviewer 在模拟器上验证并反馈修改策略）使 OpenQASM 代码生成准确率提升 71.6%。其 RAG 知识库包含规范量子算法和 backend-specific 文档。

**wiki 当前状态**：2.7 节 Agent 闭环仅描述了单层 Generator→Evaluator→Policy 循环。

**改进**：在 2.7 节增加多层 Agent 交互模式作为 `agentic` 编译策略的可选实现路径。将 RAG 知识库的概念纳入 `QComputeCircuitSpec` 的元数据字段。

---

## 二、`03-contracts-and-artifacts.md` — Contracts 设计

### 2.1 [P0] 增加 Data Exchange Format 字段

**研究发现**：量子化学计算中，哈密顿量交换标准格式为 FCIDUMP（ASCII, 互操作性好，双精度）和 HDF5（二进制, 高效但缺乏统一 schema）。费米子到量子比特的映射（Jordan-Wigner / Bravyi-Kitaev）由哪一侧负责是必须明确的设计决策。

**wiki 当前状态**：`QComputeCircuitSpec` 有 `ansatz` 和 `parameters` 字段，但未定义哈密顿量输入的格式。

**改进**：在 `QComputeExperimentSpec` 增加：

```python
hamiltonian_source: str | None = None          # FCIDUMP 文件路径或 HDF5 路径
hamiltonian_format: Literal["fcidump", "hdf5", "pauli_dict"] = "fcidump"
fermion_mapping: Literal["jordan_wigner", "bravyi_kitaev"] = "jordan_wigner"
active_space: tuple[int, int] | None = None    # (n_active_electrons, n_active_orbitals)
```

### 2.2 [P0] 修正 QComputeRunArtifact 的 status 枚举

**研究发现**：pyQuafu 的实际任务状态是 Created/In Queue/Running/Completed/Failed。此外存在"部分执行"情况（请求 1024 shots 但仅完成 512），此时 pyQuafu 抛出异常而非返回残缺结果。

**wiki 当前状态**：`QComputeRunArtifact.status` 定义为 `Literal["completed", "failed", "timeout", "queued"]`，遗漏 `created`（已创建未排队）和 `running`（正在执行）。

**改进**：修正为 `Literal["created", "queued", "running", "completed", "failed", "timeout", "cancelled"]`，并增加 `shots_requested` 和 `shots_completed` 字段以检测部分执行。

### 2.3 [P1] 采纳 QUASAR 的分层评估维度

**研究发现**：QUASAR 的 4 级奖励机制（syntax→distributional→semantic→optimization）是 **gated** 的：任一级失败即为 terminal negative reward。这确保资源不浪费在评估语法错误的电路上。

**wiki 当前状态**：`QComputeValidationReport` 只有扁平化的 `status` 枚举和 `metrics`，缺少分层评估结构。

**改进**：在 `QComputeValidationMetrics` 增加分层字段：

```python
syntax_valid: bool | None = None               # OpenQASM 语法校验
distributional_jsd: float | None = None         # Jensen-Shannon divergence
semantic_expectation_error: float | None = None # 期望值误差
optimization_efficiency: float | None = None   # (深度×SWAP)^-1 复合分
```

### 2.4 [P2] 增加 CalibrationSnapshot 合约

**研究发现**：pyQuafu 返回的校准数据包含 per-qubit T1/T2（μs），per-qubit 单比特门保真度，per-qubit-pair 双比特门保真度，以及区分 |0⟩→|1⟩ 和 |1⟩→|0⟩ 方向的读出错误率。预执行保真度估计的 r² 仅为 0.70-0.85，校准超过数小时则显著衰减。

**wiki 当前状态**：`QComputeCalibrationData` 只有聚合均值（`t1_us_avg`, `single_qubit_gate_fidelity_avg`），丢失了 per-qubit 粒度。

**改进**：增加 `CalibrationSnapshot` 类型保存完整 per-qubit 校准数据，与 `QComputeCalibrationData`（聚合摘要）互补。在 `QComputeEnvironmentReport` 增加 `calibration_age_minutes` 字段。

---

## 三、`04-environment-validation-and-evidence.md` — 环境与验证

### 3.1 [P0] 细化配额管理与错误码

**研究发现**：免费用户每日 1000 个任务，超出排队处理。配额在"北京时间 0 点"重置。配额超限的错误类型为 `QuotaExceededError`（不可重试）。真机执行无超时参数——任务可能在队列中无限等待。

**wiki 当前状态**：4.2 节有 `QUOTA_EXHAUSTED` 前提条件分类，但配额数量、重置时间、错误处理策略均未指定。

**改进**：在 4.2 节增加配额管理具体参数：

| 参数 | 默认值 | 来源 |
|------|--------|------|
| `daily_task_limit` | 1000 | pyQuafu 文档 |
| `quota_reset_time` | 00:00 CST | 推断（需验证） |
| `max_polling_seconds` | 600 | 推荐上限 |
| `retry_base_delay_seconds` | 1 | 斐波那契起点 |
| `retry_max_delay_seconds` | 60 | 斐波那契上限 |

### 3.2 [P1] 增加噪声感知评分的具体公式

**研究发现**：
- SimpleTES 评分: `Score = w1 × N_SWAP + w2 × Depth - w3 × log(Fidelity_est)`
- ESP (Estimated Success Probability): 电路中所有门保真度的乘积
- QVA (Quantum Vulnerability Analysis): 考虑 2-qubit 门误差传播，r²≈0.82 vs ESP
- 误差缓解叠加开销: `N_total = N_shots × Π γ_i`

**wiki 当前状态**：4.7 节仅给出 `noise_impact_score = f(gate_error_accumulation, ...)` 的函数签名，未提供具体公式。

**改进**：在 4.7 节提供 ESP 和 QVA 的具体计算公式。在 `QComputeValidationMetrics` 中增加 `qva_score` 字段。在 policy 评估中使用 `noise_impact_score` 的实际计算。

### 3.3 [P1] 校准时效性检查

**研究发现**：校准数据的 r² 相关性随时间衰减——超过数小时的校准用于预执行保真度估计时不再可靠。QSteed 通过实时查询校准数据库来绕过此问题。

**改进**：在 4.2 节增加校准时效性检查逻辑：`calibration_age_minutes > 180`（3 小时）→ 标记 `blocks_promotion=False` 但发出 `QCOMPUTE_CALIBRATION_STALE` 警告。

---

## 四、`05-family-design.md` — Family 与 Study 设计

### 4.1 [P0] 采纳 SimpleTES 的精确 C×L×K 资源配置

**研究发现**：SimpleTES 在 C=32, L=100, K=16 设定下取得量子比特路由突破。C×L×K 资源配置是任务依赖的，当前需人工设定——更理想的方向是系统自身动态调配。

**wiki 当前状态**：5.3 节描述了 C×L×K 与 Study 的关系，但未给出具体的资源配置指导。

**改进**：在 5.3 节增加资源配置参考表：

| 场景 | C (并发) | L (迭代深度) | K (候选) | 说明 |
|------|---------|-------------|---------|------|
| 电路编译（模拟器） | 16-32 | 50-100 | 8-16 | 评估成本低，可大规模搜索 |
| 电路编译（真机） | 4-8 | 10-20 | 2-4 | 评估成本高，保守搜索 |
| ansatz 搜索 | 8-16 | 20-50 | 4-8 | 中等成本 |
| 错误缓解策略 | 4-8 | 10-30 | 2-4 | 高采样开销 |

### 4.2 [P0] 增加 Ansatz 资源缩放公式

**研究发现**：UCCSD 的参数为 O(n_occ² n_virt²)，门深度 O(N⁴)；HEA 参数 O(L·N)，深度 O(L)，但易遭遇 barren plateau；ADAPT-VQE 自适应增长。对 H₂/LiH，UCCSD+L-BFGS-B 可达到化学精度 (≤1.6 mHa)；对 H₂O，必须使用活性空间选择将 qubit 数控制在 4-12。

**wiki 当前状态**：5.2.1 节 `AnsatzFamily` 有 `parameter_count_formula` 字段但未填充具体公式。

**改进**：为三种主要 ansatz 提供具体的资源缩放公式和适用规模范围。

### 4.3 [P1] 增加 RPUCB 概念用于 Study 历史管理

**研究发现**：SimpleTES 的 RPUCB（Replay-Prioritized UCB）策略在"高价值历史节点"和"低频潜力节点"之间做探索-利用平衡，避免将全部历史轨迹塞入 prompt 导致上下文溢出。

**改进**：在 5.3.1 节 Study×Agent 交互协议中增加历史轨迹管理策略描述。

---

## 五、`06-packaging-and-registration.md` — 注册与依赖

### 5.1 [P0] 增加 QSteed 作为可选依赖

**研究发现**：QSteed 依赖 MySQL（生产环境），但支持纯内存模式（轻量 Agent 场景）。pip install qsteed 可用。QSteed 在百花芯片上深度减少 15-20%，保真度显著优于 Qiskit L3。

**wiki 当前状态**：6.4.1 节 Gateway 的 manifest.json 中 `deps.components` 仅包含 qcompute 内部组件，未考虑 QSteed 集成。

**改进**：在 manifest.json 的 `deps` 中增加 `optional_components: ["qsteed_compiler"]`。在 `bins` 中标注 QSteed 为可选（`"qsteed (optional)"`）。

### 5.2 [P1] 增加 Mitiq 错误缓解依赖

**研究发现**：Mitiq 提供 `execute_with_zne()`, `LinearFactory`, `RichardsonFactory`, `PolyFactory`, `AdaExpFactory` 等即用工具。它与 Qiskit/Cirq/pyQuafu 后端均兼容。

**改进**：在错误缓解策略执行路径中增加 Mitiq 集成点。在 Executor 的 manifest.json 的 `requires` 中增加 `"error_mitigation.zne"` 能力。

---

## 六、`07-scope-and-boundaries.md` — 范围与边界

### 6.1 [P0] 明确 ABACUS→QCompute 数据契约的格式

**研究发现**：
- ABACUS 可输出 FCIDUMP 格式的一电子/二电子积分
- 活性空间选择的 Python 实现需要 PySCF 或 Qiskit Nature
- 费米子→量子比特映射在 Qiskit Nature / OpenFermion / PySCF 中均有实现，但输入格式要求不同
- HI-VQE 范式下，经典端和量子端进行"信息交接"迭代，而非一次性求解

**wiki 当前状态**：7.3.1 节描述了 ABACUS↔QCompute 协作流程，但数据契约的格式、映射位置、中间文件格式均未指定。

**改进**：在 7.3.1 节明确：

1. ABACUS 输出 FCIDUMP 文件 → QCompute 读取
2. 活性空间选择由 QCompute ConfigCompiler 负责（调用 PySCF）
3. 费米子→量子比特映射由 QCompute ConfigCompiler 负责（默认 Jordan-Wigner）
4. HI-VQE 迭代协议：QCompute 采样 Slater 行列式 → ABACUS 子空间对角化 → 循环

### 6.2 [P1] 增加 HI-VQE 作为远期扩展点

**研究发现**：HI-VQE（北京量子院提出）显著降低了对量子电路深度的要求。其核心是量子端采样而非全求解，经典端做子空间对角化。

**改进**：在 7.5 节扩展点表中增加 HI-VQE 范式支持。

### 6.3 [P1] 增加 TensorCircuit Agentic-NG 作为中远期后端

**研究发现**：TensorCircuit 已发布 Agentic-NG 版本，是首个 AI-native 量子软件框架，支持 `/arxiv-reproduce` 命令。其张量网络模拟器原生支持 JAX/TensorFlow/PyTorch 自动微分。

**改进**：在 7.5 节增加 TensorCircuit 作为模拟器后端选项。

---

## 七、`08-testing-and-review.md` — 测试策略

### 7.1 [P0] 增加 Quafu Cup 基准作为集成测试参照

**研究发现**：Quafu 杯的评估标准综合考虑保真度、门数量、运行时间，这正是自动化量子 Agent 的理想基准。赛题覆盖量子 ML、量子化学、组合优化、噪声抑制——与 QCompute 的目标场景高度吻合。

**改进**：在 8.3 节增加 Quafu Cup 风格测试用例。在 8.6 节测试覆盖矩阵中增加"Quafu Cup 基准"行。

### 7.2 [P0] 增加校准数据时效性测试

**研究发现**：校准超过数小时后 r² 显著下降。Environment 组件应能检测校准年龄并发出相应警告。

**改进**：在 8.2 节增加校准时效性的单元测试用例。

### 7.3 [P1] 增加 Mitiq 集成测试

**改进**：在 8.3 节增加 ZNE + MEM stacking 的集成测试示例，使用 Mitiq 的 `execute_with_zne()`。

---

## 八、跨文件改进

### 8.1 [P0] 增加 pyQuafu 具体 API 引用

**问题**：wiki 中多处使用抽象描述（"提交至后端"「获取校准数据」等），缺少与实际 SDK API 的映射。

**改进**：在 `02-workflow-and-components.md` 和 `03-contracts-and-artifacts.md` 的关键位置增加 pyQuafu API 映射注释。例如：

```
# QCompute Executor 中的 task.send() 实际映射：
# pyquafu: task.config(backend="ScQ-P18", shots=2000, compile=True)
#           res = task.send(circuit)
# MCP:     submit_qasm(qasm=circuit_str, backend="ScQ-P18")
```

### 8.2 [P0] 增加配额感知的全局调度说明

**研究发现**：免费用户每日 1000 个任务，超出排队。Study 组件需要配额感知调度——优先模拟器试验，再按 information gain 排序真机试验。

**wiki 当前状态**：5.4.2 节有配额感知调度伪代码，但未在其他组件中体现。

**改进**：在 Gateway 的 `run_baseline()` 描述中增加配额检查步骤。在 Executor 的错误处理中增加 `QuotaExceededError → blocks_promotion=True` 的映射。

### 8.3 [P1] 增加轨迹级评估概念

**研究发现**：SimpleTES 的核心创新——不按单步 reward 优化，而看整条探索轨迹的最终效果——对 Agent 行为建模有深远影响。它表明优化目标应该是"什么样的整条探索路径更可能成功"而非"下一步怎么走更安全"。

**改进**：在 `03-contracts-and-artifacts.md` 的 Study 类型中增加 `trajectory_score` 字段，支持轨迹级而非单步级评估。

---

## 九、优先级汇总

| 优先级 | 数量 | 涉及文件 |
|--------|------|---------|
| **P0** (必须修正) | 10 | 02 (2项), 03 (2项), 04 (1项), 05 (2项), 06 (1项), 07 (1项), 08 (2项), 跨文件 (2项) |
| **P1** (增强 feasibility) | 7 | 02 (2项), 03 (1项), 04 (2项), 05 (1项), 06 (1项), 07 (2项), 08 (1项), 跨文件 (1项) |
| **P2** (远期优化) | 1 | 03 (1项) |

## 十、最关键的单一改进

如果只能做一个改动，应该修改 **`03-contracts-and-artifacts.md`** 中的 `QComputeExperimentSpec`，增加：

1. 哈密顿量来源格式（FCIDUMP / HDF5 / pauli_dict）
2. 费米子映射方法（Jordan-Wigner / Bravyi-Kitaev）
3. 活性空间规格

这三项直接决定了 ABACUS→QCompute 的数据契约是否可落地——没有它们，整个经典-量子混合工作流就缺少最关键的数据交接面。
