# 02. 工作流与组件链

## 2.1 总体流水线

QCompute 遵循 MHE 标准的五阶段流水线，但增加了量子特有的后端选择与噪声感知维度：

```
Gateway ──→ Environment ──→ ConfigCompiler ──→ Executor ──→ Validator
  │              │                 │                │              │
  │              │                 │                │              │
  └─ 编译        └─ 探测后端       └─ 生成电路      └─ 提交执行    └─ 验证结果
    experiment     可用性/噪声       配置/编译        捕获输出       评分证据
    spec           calibration       策略选择        原始计数       构建 bundle
```

### 流水线数据流

```
QComputeExperimentSpec
  → QComputeRunPlan (ConfigCompiler 产出)
    → QComputeRunArtifact (Executor 产出)
      → QComputeValidationReport (Validator 产出)
        → QComputeEvidenceBundle → Policy → Governance → CandidateRecord
```

### 2.1.1 组件生命周期集成

所有 QCompute 组件继承 `HarnessComponent` 基类（`sdk/base.py`），
遵循统一的生命周期钩子。以 Gateway 为例：

```python
class QComputeGatewayComponent(HarnessComponent):
    protected: bool = False

    def declare_interface(self, api: HarnessAPI) -> None:
        api.declare_input("experiment_spec", type_="QComputeExperimentSpec", required=True)
        api.declare_output("evidence_bundle", type_="QComputeEvidenceBundle", mode="sync")
        api.declare_capability("qcompute.compile.case")

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime
        self._env = runtime.get_component("qcompute_environment.primary")
        self._compiler = runtime.get_component("qcompute_config_compiler.primary")
        self._executor = runtime.get_component("qcompute_executor.primary")
        self._validator = runtime.get_component("qcompute_validator.primary")

    async def deactivate(self) -> None:
        self._env = self._compiler = self._executor = self._validator = None

    # Domain methods (called after activate)
    async def compile_experiment(self, spec: QComputeExperimentSpec) -> QComputeRunPlan: ...
    async def run_baseline(self, spec: QComputeExperimentSpec) -> QComputeEvidenceBundle: ...
```

关键模式：
- `declare_interface()`：声明 ports 和 capabilities，在 graph validation 前调用，禁止 I/O
- `activate(runtime)`：获取运行时引用和依赖组件，建立连接
- `deactivate()`：释放资源，断开引用
- 领域方法（`compile_experiment`、`run_baseline` 等）在 `activate` 之后才可调用

其他组件（Environment、ConfigCompiler、Executor、Validator、Study）遵循相同模式，
各自的 `declare_interface()` 声明不同的 ports 和 capabilities（见 06）。

## 2.2 QComputeGateway —— 入口与编排

**Slot**: `qcompute_gateway.primary`
**Capability**: `qcompute.compile.case`

Gateway 是 QCompute 扩展的入口组件。职责：

1. **接收并校验** `QComputeExperimentSpec`——包含目标电路、后端选择策略、噪声容忍度
2. **解析实验意图**：区分 "模拟验证" / "真机执行" / "混合计算" 三种执行模式
3. **编排流水线**：顺序调度 Environment → ConfigCompiler → Executor → Validator
4. **暴露 `run_baseline()`**：端到端最小闭环的便捷入口

```python
class QComputeGatewayComponent(HarnessComponent):
    async def compile_experiment(self, spec: QComputeExperimentSpec) -> QComputeRunPlan: ...
    async def run_baseline(self, spec: QComputeExperimentSpec) -> QComputeEvidenceBundle: ...
```

### 2.2.1 实验意图解析

Gateway 根据 ExecutionMode 选择不同的编译策略：

| ExecutionMode | 后端策略 | 典型场景 |
|---------------|---------|---------|
| `simulate` | 优先 Qiskit Aer（无噪声/噪声模型） | 算法原型验证、电路结构优化 |
| `run` | 优先 Quafu 真机（指定芯片） | 真实硬件验证、保真度基准 |
| `hybrid` | 经典预处理 + 量子子问题 | 与 ABACUS 联动的 VQE/量子化学 |

## 2.3 QComputeEnvironment —— 环境与后端探测

**Slot**: `qcompute_environment.primary`
**Capability**: `qcompute.environment.probe`

职责：

1. **探测可用后端**：Quafu 芯片状态（在线/维护/排队）、Qiskit Aer 版本与能力
2. **获取噪声校准数据**：从 Quafu 读取最新校准（T1/T2、门保真度、读出误差）
3. **验证前置条件**：pyQuafu SDK 版本、API token 有效性、每日配额余量
4. **生成环境报告**：`QComputeEnvironmentReport`——后端可用性 + 噪声特征 + 前提条件清单

```python
class QComputeEnvironmentComponent(HarnessComponent):
    async def probe(self, backend_spec: QComputeBackendSpec) -> QComputeEnvironmentReport: ...
```

### 2.3.1 环境报告与 promotion prerequisites

环境报告不只是一次性 preflight 记录。在当前 MHE 治理语义下，
它承载 **promotion prerequisites** 信息：

- 若后端不可用或校准过期，`EnvironmentReport` 标记 `blocks_promotion=True`
- 噪声特征作为后续 Validator 评分的基线参照
- 每日配额状态影响 Study 组件的并行度决策

## 2.4 QComputeConfigCompiler —— 电路配置编译

**Slot**: `qcompute_config_compiler.primary`
**Capability**: `qcompute.circuit.compile`

这是 QCompute 最量子特定的组件。职责：

1. **电路生成**：根据 `QComputeCircuitSpec` 生成目标电路（Qiskit QuantumCircuit / OpenQASM 2.0）
2. **后端适配**：transpilation——将逻辑电路映射到目标硬件的物理拓扑
3. **编译优化**：应用编译策略（qubit routing、SWAP 最小化、门分解）

### 2.4.1 编译优化策略

ConfigCompiler 支持三种编译策略，体现 SimpleTES C×L×K 范式：

| 策略 | C (并发) | L (深度) | K (候选) | 适用场景 |
|------|---------|---------|---------|---------|
| `baseline` | 1 | 1 | 1 | 单次标准 transpilation |
| `sabre` | 1 | N (SABRE 多轮) | 1 | 标准 qubit routing 优化 |
| `agentic` | C (并行) | L (迭代轮数) | K (候选数) | Agent 驱动的生成-评估闭环 |

`agentic` 策略是 QCompute 的核心差异化能力：
- Agent 生成 C 个候选电路映射方案
- 每个方案通过模拟器评估 L 轮（含噪声模型）
- 从 K 个终选方案中选择最优（保真度 × 深度 × SWAP 数的 Pareto 前沿）

### 2.4.1b 编译策略到 transpiler 参数的映射

| QCompute strategy | Qiskit level | SabreLayout trials | QSteed VQPU | 适用场景 |
|-------------------|-------------|-------------------|-------------|---------|
| `baseline` | 1 | 20 (default) | 否 | 算法原型验证 |
| `sabre` | 3 | 200 (high effort) | 否 | 标准编译优化 |
| `agentic` | 3 | 200+ (iterative) | 是 | Agent 驱动的搜索式优化 |

注：`sabre` 策略下将 `swap_trials` 从 default 20 提升到 200 可额外减少约 10% 的 SWAP 门。
QSteed VQPU 选择仅在 `agentic` 策略下启用，因为它需要在编译前先查询 Quafu 校准数据库。

### 2.4.2 编译产物

`QComputeRunPlan` 包含：
- 编译后的电路（OpenQASM 2.0 字符串或 Qiskit QuantumCircuit 序列化）
- 目标后端绑定信息
- 编译策略与元数据（SWAP 计数、电路深度、预估保真度）
- 执行参数（shots 数、测量基选择、错误缓解策略标识）

## 2.5 QComputeExecutor —— 量子执行

**Slot**: `qcompute_executor.primary`
**Capability**: `qcompute.circuit.run`

职责：

1. **提交任务**：根据 `QComputeRunPlan` 将电路提交至目标后端
2. **管理任务生命周期**：提交 → 排队 → 执行 → 完成 / 失败
3. **收集原始输出**：测量计数、statevector（模拟器）、概率分布
4. **构建运行产物**：`QComputeRunArtifact`

```python
class QComputeExecutorComponent(HarnessComponent):
    async def execute_plan(self, plan: QComputeRunPlan) -> QComputeRunArtifact: ...
    async def execute_batch(self, plans: list[QComputeRunPlan]) -> list[QComputeRunArtifact]: ...
```

### 2.5.2 异步任务生命周期管理

Executor 不阻塞等待量子任务完成，而是采用异步轮询机制：

```
submit() → Created → In Queue → Running → Completed/Failed/Timeout
                │                     │
                └─ cancel()           └─ (不可取消)
```

轮询策略：起始延迟 1s，按斐波那契数列递增（1, 1, 2, 3, 5, 8, 13, 21, 34, 55），
上限 60s。最大总等待时间为可配置参数（默认 600s）。

**异常分类：**

| 异常类型 | 分类 | 处理策略 |
|---------|------|---------|
| `QueueTimeoutError` | retriable | 重新提交（最多 3 次） |
| `NetworkConnectivityError` | retriable | 指数退避重试 |
| `CircuitTopologyError` | non-retriable | 立即失败，`blocks_promotion=True` |
| `QuotaExceededError` | non-retriable | 等待配额重置（北京时间 0:00） |

### 2.5.1 多后端调度

Executor 根据 `RunPlan.backend` 选择对应的客户端适配器：

| 后端 | 适配器 | 提交方式 |
|------|--------|---------|
| Quafu 真机 | `pyQuafu` SDK | Python API / MCP |
| Qiskit Aer | `qiskit-aer` | `AerSimulator.run()` |
| IBM Quantum | `qiskit-ibm-runtime` (预留) | REST API |

### 2.5.2 错误缓解集成

Executor 在执行层支持以下错误缓解策略（在 `RunPlan` 中指定）：

- **Readout Error Mitigation (REM)**：测量误差矩阵校正
- **Zero-Noise Extrapolation (ZNE)**：通过噪声缩放外推零噪声极限
- **Pauli Twirling**：将相干噪声转换为随机 Pauli 噪声

## 2.6 QComputeValidator —— 验证与评分

**Slot**: `qcompute_validator.primary`（protected）
**Capability**: `qcompute.result.validate`

Validator 是 QCompute 的 **protected governance component**。职责：

1. **验证运行结果完整性**：检查原始计数、statevector 的有效性
2. **计算保真度指标**：与参考解对比（理想模拟器结果 / 已知基态能量）
3. **噪声影响评估**：基于校准数据评估噪声对结果的置信区间
4. **生成验证报告**：`QComputeValidationReport`——通过/失败 + 指标 + promotion 判断

### 2.6.1 验证维度

| 维度 | 指标 | 阈值来源 |
|------|------|---------|
| 执行完整性 | 任务状态、shots 计数 | 硬性要求（必须满足） |
| 统计显著性 | 测量分布 χ² 检验 | Policy 可配置 |
| 保真度 | State fidelity / 能量误差 | 实验规格中指定 |
| 噪声鲁棒性 | 噪声模型下的结果稳定性 | 环境报告的基线噪声 |
| 收敛性 | VQE 能量收敛曲线 | 迭代历史分析 |

### 2.6.2 验证语义

```python
class QComputeValidationStatus(str, Enum):
    ENVIRONMENT_INVALID = "environment_invalid"   # 环境前提不满足
    BACKEND_UNAVAILABLE = "backend_unavailable"   # 目标后端不可用
    EXECUTION_FAILED = "execution_failed"         # 运行失败
    RESULT_INCOMPLETE = "result_incomplete"       # 结果不完整
    BELOW_FIDELITY_THRESHOLD = "below_fidelity"   # 保真度不达标
    NOISE_CORRUPTED = "noise_corrupted"           # 噪声超标
    VALIDATED = "validated"                       # 验证通过
    CONVERGED = "converged"                       # 收敛（VQE 特化）
```

### 2.6.3 验证层级说明

QCompute 的验证涉及两个独立但协作的层级：

1. **MHE 图结构验证**（`validators.py`）：由 `HarnessRuntime.commit_graph()` 自动执行，
   检查图拓扑完整性（循环检测、孤立组件、受保护 slot 冲突）。
   这是所有 MHE 扩展共用的治理基础设施。

2. **QCompute 领域验证**（`QComputeValidatorComponent`）：验证量子实验结果的科学有效性
   （保真度、统计显著性、噪声影响）。其输出通过 `QComputeValidationReport`
   进入 `PromotionContext`，作为 evidence 供 MHE 治理层决策，而非直接控制 promotion 门控。

换言之，QComputeValidator 是 **evidence contributor**（证据贡献者），
不是 **gate controller**（门控执行者）。真正的 promotion 决策由
`HarnessRuntime.commit_graph()` 中 `blocks_promotion` 检查和
`safety_pipeline.evaluate_graph_promotion()` 联合完成。

## 2.7 代理驱动的优化闭环

QCompute 区别于其他 MHE 扩展的核心特征：**Agent 作为优化引擎参与电路编译的迭代过程**。

```
                    ┌──────────────────────────┐
                    │     MHE Agent Loop        │
                    │  (BrainProvider seam)     │
                    └──────────┬───────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ Generator    │   │ Evaluator    │   │ Policy       │
   │ (C 并发生成   │   │ (L 深度评估   │   │ (K 候选筛选   │
   │  候选电路)    │   │  噪声模拟)    │   │  Pareto 选择) │
   └──────────────┘   └──────────────┘   └──────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │   QCompute Study          │
                    │   (C×L×K 结构化管理)       │
                    └──────────────────────────┘
```

### 2.7.1 Agent 与组件的交互协议

QCompute 的 Agent 交互涉及两个层级，需明确区分：

**层级 1：MHE BrainProvider（框架级）**
`BrainProvider` 是 MHE optimizer 的通用协议接口（`core/brain.py`），
签名固定为 `propose(optimizer, observations) -> list[MutationProposal]`
和 `evaluate(optimizer, proposal, observations) -> ProposalEvaluation`。
它操作的是 **graph mutation**（连接变更、参数调整），粒度为组件拓扑。

**层级 2：QAgent 内部 Agent 分工（领域级）**
QAgent 的 Planner-Coder-Reviewer 是量子电路编译的内部协作模式，
操作粒度为 **电路/ansatz 级别**（qubit mapping、gate decomposition、SWAP routing）。
这是 BrainProvider `propose()` 内部的实现细节，不是 MHE 框架可见的分离。

**两者的关系**：Study 组件调用 `BrainProvider.propose()` 时，
返回的 `MutationProposal` 可能内部由 QAgent 三 Agent 协作生成。
框架只看到 `propose()` 的返回值，不感知内部的 Planner-Coder-Reviewer 分工。
这种分层使 QCompute 可以自由替换 Agent 内部架构（如从三 Agent 切换为单 Agent），
而不影响 MHE 框架的调用约定。

QCompute 的 Study 组件将这些操作结构化为 C×L×K 维度管理的实验网格。

### 2.7.2 QAgent 的 Planner-Coder-Reviewer 三 agent 模式

QAgent 的优化闭环内部采用 **Planner-Coder-Reviewer** 三 agent 协作模式：

1. **Planner**（规划者）—— 将电路编译问题分解为子任务：
   - 接收实验规格，分解为 qubit mapping、gate decomposition、SWAP routing 等子问题
   - 为每个子问题选择合适的编译策略（baseline / sabre / agentic）

2. **Coder**（实现者）—— 生成具体的电路映射方案：
   - 通过 RAG 知识库检索历史成功案例作为动态 few-shot 示例
   - 生成 OpenQASM 电路或 Qiskit transpilation 参数组合
   - 每次生成后记录编译元数据（depth、SWAP count）作为后续反馈依据

3. **Reviewer**（审查者）—— 模拟评估并反馈：
   - 在模拟器上运行生成的电路（含噪声模型）
   - 计算保真度、深度、SWAP 数的综合评分
   - 以 CoT（Chain of Thought）形式输出诊断结论和修订建议
   - 若评估未达标，将修订策略反馈给 Planner 进入下一轮迭代

这一三 agent 模式与 QCompute 组件的映射关系：

| Agent 角色 | QCompute 组件映射 | 职责 |
|-----------|------------------|------|
| Planner | Gateway 的实验编译 + ConfigCompiler 的策略选择 | 分解意图、规划路径 |
| Coder | ConfigCompiler 的电路生成 + RAG 知识库检索 | 具体实现、代码/电路产出 |
| Reviewer | Validator 的执行前检查 + 模拟器评估 | 质量验证、反馈生成 |

关键洞察：Reviewer agent 的"修订策略"反馈不是针对单次代码生成步骤的局部修正，
而是一种 **trajectory-level optimization** —— 它优化的是整个问题求解路径，
使得每次迭代都能从上一轮的失败中学习更高层次的策略（如"减少 entanglement 层数"
而非"修改一个旋转角度参数"）。这种轨迹级优化是 QAgent 区别于传统
compile-and-run 管道的核心差异点。

## 2.8 Runtime evidence handoff

QCompute extension 产出的 artifact、validation report 与 evidence bundle，
不只在 extension-local 范围内消费。它们应作为 **runtime evidence handoff 面**：

- `QComputeRunArtifact` 的路径、checksum 与元数据 → session event / audit record
- `QComputeValidationReport` 的 status + metrics → promotion context 的 validation_report 字段
- `QComputeEvidenceBundle` 的 evidence_refs → provenance link (WAS_DERIVED_FROM)

后续 session event、audit record、provenance link 与 candidate/graph version 锚点，
由 strengthened MHE 的统一治理路径（`HarnessRuntime.commit_graph()`）继续承接。

## 2.9 HI-VQE：经典-量子信息交接范式（远期研究）

HI-VQE (Handover-Iterative VQE) 代表了经典-量子混合计算的前沿方向。
其核心思想是：量子端不独立求解完整能量，而是与经典处理器进行"信息交接"迭代。

### 工作流

```
ABACUS (经典)                      QCompute (量子)
─────────────────                  ────────────────
1. DFT → FCIDUMP
2. 活性空间选择        ──────→    3. 初始 VQE ansatz
                                  4. 量子采样 → Slater 行列式
5. 子空间对角化        ←──────     (信息交接)
6. 精确能量 + 修正      ──────→    7. 更新 ansatz 参数
                                  8. 下一轮采样
                                  ...
                                  N. 收敛判断
```

### 对 QCompute 组件的影响

- **Gateway**：需要支持 handover 模式——实验不再是一次性提交，而是迭代 loop
- **ConfigCompiler**：需要根据经典端反馈更新电路参数（而非每次从头编译）
- **Executor**：handover 模式下，量子端只需采样（shots 较少），不要求全状态求解
- **Validator**：收敛判断从"单次能量误差"变为"子空间能量收敛曲线"
- **Evidence**：handover 迭代的每一轮都应产生 checkpoint evidence

### 首版预留

首版通过 `QComputeExperimentSpec.hamiltonian_file` 和 `active_space` 字段
预留了与 HI-VQE 的数据契约兼容性。handover 迭代循环将在远期通过
`QComputeCircuitSpec.parameters` 的动态更新和 Study 组件的迭代模式实现。
