# MHE Core 架构增强总报告

> 综合 ABACUS、DeepMD、JEDI、AI4PDE、Nektar、QCompute 六个扩展对 MHE core 的独立分析，
> 收敛为统一的架构改进方向。
>
> 日期：2026-04-25

## 1. 核心判断

**当前 MHE 是"图治理框架"，不是"运行治理框架"。**

六个扩展的独立分析——分别从第一性原理计算、分子动力学、数据同化、偏微分方程、
有限元求解、量子计算六个完全不同的科学领域出发——收敛到了同一个结论：

MHE core 在**组件发现 → 图装配 → 版本提交 → 安全审查**这条路径上已经建立了
坚实的基础（candidate staging、protected components、promotion gating、
safety pipeline、checkpoint/hot-swap、session events、provenance）。

但一旦组件被激活并开始**真正执行科学计算任务**——提交量子电路、启动 HPC 作业、
运行 PDE 求解器——core 就不再提供任何结构化支持。执行、验证、证据收集、
配额管理、结果治理全部下放到 extension 自行解决。

这意味着每个 extension 都在独立重新发明：
- 任务提交/轮询/重试/取消的状态机
- 执行产物与验证报告的类型约定
- 运行级证据如何进入治理流程
- 资源配额的感知与调度
- 持久化的检查点与恢复

六个 extension 各自造了一遍轮子，彼此不兼容。

## 2. 六条改进主线

以下按优先级排列。P0 是所有 extension 共同需要的最小公约数；
P1 是多数 extension 需要的增强；P2 是部分 extension 需要的专项能力。

---

### 2.1 [P0] 运行期核心合约

**现状**：core 只有图级合约（`PendingConnectionSet`、`GraphSnapshot`、
`ValidationReport`），没有运行期数据模型。

**需要的核心类型**：

| 类型 | 语义 | 提出者 |
|------|------|--------|
| `EnvironmentReport` | 后端探测结果：可用性、能力、约束 | ABACUS、QCompute、JEDI |
| `RunPlan` | 编译后的执行计划：做什么、怎么做、用什么资源 | ABACUS、Nektar、QCompute、JEDI |
| `RunArtifact` | 执行产物：原始输出、状态、耗时、错误信息 | ABACUS、Nektar、QCompute、AI4PDE |
| `ExecutionStatus` | 任务生命周期状态机 | Nektar、QCompute、AI4PDE |
| `ValidationOutcome` | 领域验证结论：不只是 valid/invalid，包含评分与置信度 | DeepMD、QCompute、Nektar |
| `EvidenceBundle` | 完整证据元组：环境 + 产物 + 验证 + 来源引用 | QCompute、JEDI、DeepMD |

**设计原则**：
- 这些类型定义为 **core 协议**（protocol / abstract base），不是具体类
- 每个 extension 提供自己的 Pydantic 实现，但共享字段语义
- 类型设计应足够通用，不偏向任何特定科学领域

**受益面**：全量——所有六个 extension 都能直接使用。

---

### 2.2 [P0] 任务执行控制面

**现状**：`HarnessComponent` 只有 `activate/deactivate` 生命周期钩子。
没有任务提交、异步轮询、重试、取消、批量执行的抽象。
`ExecutorComponent` 和 `RuntimeComponent` 是空 stub。

**需要的核心能力**：

```
submit(plan) → task_id
poll(task_id) → status
cancel(task_id) → void
await_result(task_id, timeout) → artifact
submit_batch(plans) → list[task_id]
```

**设计原则**：
- 定义为 `AsyncExecutorProtocol`，可选实现——不需要任务管理的组件不实现
- 轮询策略可配置（固定间隔、指数退避、斐波那契——QCompute 用后者）
- 异常分类：可重试 vs 不可重试，由 extension 定义，core 只传输
- 批量执行支持：用于 Study 组件的 C×L×K 并行试验

**受益面**：Nektar（HPC 作业）、QCompute（量子真机）、ABACUS（DFT 计算）、
AI4PDE（PDE 求解器）——四个 extension 直接受益。DeepMD 和 JEDI 暂无强需求。

---

### 2.3 [P0] 运行级治理门控

**现状**：`SafetyPipeline.evaluate_graph_promotion()` 只调用可选的 policy reviewer，
完全绕过了 gate chain。Domain validation 结果（保真度、误差、配额）不经过任何安全门。
治理是纯二元的 `blocks_promotion: bool`，没有 defer 语义。

**需要的核心改进**：

1. **让 domain validation evidence 进入 gate chain**：
   `evaluate_graph_promotion` 应同时运行 gates，让运行级验证结果
   （保真度不足、配额耗尽、校准过期）能触发安全门拒绝。

2. **从二元扩展为三元决策**：`allow / defer / reject`
   - `allow`：正常提交
   - `defer`：结果不确定，需要更多数据或人工审查
   - `reject`：不可恢复的失败，阻止提交

3. **证据完整性 gate**：验证 evidence bundle 是否完整——
   环境报告存在、执行产物非空、验证报告有结论。

**受益面**：DeepMD（defer 语义）、QCompute（保真度/噪声/配额 gate）、
Nektar（复现性 gate）、AI4PDE（风险 gate）。

---

### 2.4 [P1] 持久化证据与审计存储

**现状**：
- `SessionStore` 只有 `InMemorySessionStore`，进程退出即丢失
- `CheckpointManager` 只保存 component state，不保存运行产物
- `AuditLog` 支持 JSONL + Merkle anchoring，是最成熟的部分
- `ProvGraph` 是内存图，没有持久化

**需要的核心改进**：

1. **SessionStore 可插拔后端**：接口不变，增加 `FileSessionStore`
   （JSONL 追加）和可选的数据库后端。

2. **运行阶段事件类型**：当前 `SessionEventType` 只有图级事件
   （`GRAPH_COMMITTED`、`CANDIDATE_REJECTED` 等）。需要增加：
   - `TASK_SUBMITTED` / `TASK_COMPLETED` / `TASK_FAILED` / `TASK_RETRIED`
   - `DOMAIN_EVIDENCE_PRODUCED`
   - `ENVIRONMENT_PROBED`

3. **Checkpoint 从 component state 扩展为 run state**：
   保存的不只是组件激活状态，还要包含运行计划、执行产物路径、验证上下文。

4. **Artifact lineage**：provenance graph 能原生表达
   `spec → plan → artifact → validation → evidence` 链，
   而不只是 `entity A WAS_DERIVED_FROM entity B` 的泛化关系。

**受益面**：全量——所有需要审计和恢复能力的 extension。

---

### 2.5 [P1] Optimizer 双层架构

**现状**：`MutationProposal` 只携带 `PendingConnectionSet`（图拓扑变更）。
`BrainProvider.propose()` 返回的是图级 mutation，无法表达领域级实验候选。
`FitnessEvaluator` 只输出单标量 fitness，不支持多目标权衡。

**需要的核心改进**：

1. **MutationProposal 增加 domain_payload 通道**：
   可选字段 `domain_payload: dict[str, Any] | None`，
   让 extension 携带领域特定的候选参数而不污染图模型。

2. **多目标评分支持**：
   `ScoredEvidence.metrics` 已经是 `dict[str, float]`，
   在 optimizer 层增加 Pareto 前沿计算能力。

3. **Study loop 协议**：定义 `StudyComponent` 的标准接口——
   `run_study(spec) → report`、`run_single_trial(spec) → trial`、
   `evaluate_pareto_front(trials, objective) → front`。

**受益面**：QCompute（C×L×K agentic 搜索）、DeepMD（候选物理方案搜索）、
Nektar（收敛研究）、AI4PDE（方法选择）。通用 Study 协议让所有 extension 的
实验网格搜索复用同一框架。

---

### 2.6 [P2] 资源配额与依赖声明

**现状**：`ComponentManifest.deps` 没有可选依赖分支。
core 没有外部资源配额的概念。`BudgetState` 语义是优化器搜索预算，
不是外部服务配额。

**需要的核心改进**：

1. **Manifest 增加可选依赖**：`DependencySpec` 增加
   `optional_components` / `optional_capabilities` 字段。
   QCompute 的 QSteed/Mitiq/TensorCircuit、Nektar 的可选后处理工具
   都需要这种声明方式。

2. **ResourceQuota 协议**：让 Executor 级组件声明和管理外部资源约束
   （每日配额、核心时间、API 调用限制），
   与 Study 调度器配合实现配额感知的实验编排。

3. **ComponentRuntime 服务化**：将当前的空槽位
   （`brain_provider`、`sandbox_client`、`tool_execute` 等）
   正式化为可注入的运行时服务协议——workspace manager、artifact registrar、
   evidence emitter、job runner。

**受益面**：QCompute（真机配额）、Nektar（HPC 核心时间）、ABACUS（计算资源）。

---

## 3. 不属于本次改进范围的事项

以下内容在个别 extension 分析中提出，但属于更远的未来方向，
不应纳入近期 core 改进：

| 方向 | 提出者 | 排除原因 |
|------|--------|---------|
| Team/approval/budget 控制平面 | AI4PDE | 控制面过强，与外部 agent 编排系统可能重叠 |
| Template 生命周期管理 | AI4PDE | 语义过重，当前 extension 各自管理模板即可 |
| Invariant engine（声明式不变量） | AI4PDE | 设计复杂度高，当前 `blocks_promotion` 足够 |
| 量子纠错码集成 | QCompute | 前沿研究，不宜进入工程框架 |
| 脉冲级控制 | QCompute | 门级电路是当前边界 |
| 量子数据同化 | QCompute/JEDI | 远期交叉方向 |

## 4. 实施策略

### 增量原则

每一条改进都是**向后兼容的增量修改**：
- 新增协议/接口，不替换现有机制
- 新增可选字段，不改变现有字段语义
- 新增枚举值，不删除现有值
- 现有 extension 在未适配的情况下应继续正常工作

### 建议阶段划分

**第一阶段：数据模型准备**
- 在 `core/models.py` 中定义运行期核心合约的协议/基类
- `SessionEventType` 增加执行生命周期事件
- `DependencySpec` 增加可选依赖字段
- `MutationProposal` 增加 domain_payload 字段

不改变任何运行时行为。所有新类型有默认值，旧代码不受影响。

**第二阶段：执行与治理增强**
- 引入 `AsyncExecutorProtocol`
- 让 `evaluate_graph_promotion` 经过 gate chain
- 扩展 governance 决策为 allow/defer/reject

**第三阶段：持久化与优化器**
- `SessionStore` 可插拔后端
- Checkpoint 扩展为 run state
- Optimizer 双层架构（domain payload + Pareto）

**第四阶段：Extension 适配**
- 各 extension 按自身节奏接入新 core 能力
- 优先级：QCompute（最新设计，无历史包袱）→ Nektar（已有部分治理元数据）→ 其余

### 与现有 strengthening 计划的关系

本报告与已批准的 MHE strengthening 计划（Phase 1a-6）互补而非替代：
- strengthening 计划聚焦于**图治理路径的强化**（PromotionContext、protected components、evidence flow、hot-reload governance）
- 本报告聚焦于**运行治理路径的新建**（任务执行、领域验证、资源配额、持久化证据）

两条路径可以并行推进，因为它们操作不同的控制面，修改不重叠的文件。

## 5. 风险评估

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| Run model 设计过早过重，束缚 extension | 高 | 定义为 protocol 而非具体类；extension 自由实现 |
| 持久化引入 schema 演进成本 | 中 | 先做 JSONL 追加（无 schema 约束），后续再演进 |
| 三元 governance 增加流程复杂度 | 中 | `defer` 默认行为等同于 `reject`，需显式配置才启用 |
| Graph 治理与 Run 治理过度耦合 | 高 | 两条控制面保持独立，只在 evidence handoff 点交叉 |
| Optional deps 检测不一致 | 低 | 统一使用 `try/except import` 模式，在 activate 时检测 |

## 6. 总结

六个科学计算扩展从六个不同领域出发，独立分析后收敛到同一个结论：

**MHE core 的下一步不是"再加几个组件"，而是从图治理框架演进为运行治理框架。**

具体来说，需要新增三条并行的控制面：

```
当前 MHE core:
  组件发现 → 图装配 → 版本提交 → 安全审查 → 检查点
  ████████████████████████████████████████████████  ← 已有，较成熟

需要新增:
  环境探测 → 计划编译 → 任务执行 → 领域验证 → 证据治理
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ← 缺失

交汇点:
  领域验证的结果通过 EvidenceBundle 进入图治理的 promotion 决策
  ↑                                              ↑
  运行治理面                                      图治理面
```

这两条控制面的交汇点——运行证据如何进入图提升决策——是整个架构增强的
关键设计决策。做好了，每个 extension 只需实现自己的执行/验证逻辑，
就能自动获得 MHE 的治理、审计、检查点、回滚能力。
