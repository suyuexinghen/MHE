# 04. 治理、可观测性与审计

## 4.1 为什么 AI4PDE 需要更强治理

`AI4PDE Agent` 的风险远高于普通问答 Agent：

- PDE 训练与求解可能消耗大量 GPU / HPC 资源
- 任务时长可能跨越数小时到数天
- workflow 演化可能在运行时发生
- 结果可能被解释为正式科学结论
- 错误不仅是“答案不准”，还可能是：
  - 浪费计算预算
  - 破坏验证标准
  - 污染模板库
  - 产生不可复现结论

因此，治理、观测与审计必须成为一等基础设施，而不是附加日志功能。

---

## 4.2 治理平面的职责

建议 `Scientific Governance Plane` 至少负责：

- 风险分级
- 预算约束
- 变更审批
- 不变量检查
- 观察窗口管理
- 回滚准备
- 证据与溯源要求
- 审计链生成

其作用不是阻碍探索，而是确保：

- 高成本探索可控
- 自增长不失控
- 最终结论可信

---

## 4.3 科学治理不变量

## 4.3.1 为什么要用不变量

在 AI4PDE 中，很多原则不应由“经验判断”决定，而应被编码为显式规则。

这样：

- Planner 无法绕过它们
- Optimizer 无法静默侵蚀它们
- worker 不能无意破坏它们

---

## 4.3.2 建议的核心不变量

### `ProvenanceRequired`

无溯源对象，不得把结果标记为正式交付。

### `RollbackRequired`

无 rollback target，不得激活新的 active graph。

### `BudgetBound`

无预算许可，不得启动高成本训练、超长 walltime 作业或 HPC 提交。

### `ValidatorIntegrity`

验证标准不得在同一任务中静默变更。

### `ReferenceIntegrity`

reference solver / baseline 结果不得由普通 worker 改写。

### `ProtectedSlots`

以下 slot 属于受保护基础设施，普通 Optimizer 路径不可直接修改：

- `PolicyGuard`（策略守卫）
- `EvidenceManager`（证据管理）
- `ObservabilityHub`（观测中枢）
- `ReferenceSolver`（参考求解器，输出不得被普通 worker 改写）

### `ReproducibilityThreshold`

模板、candidate graph 或新 workflow 若未达到最低复现阈值，不得晋升为 `stable`。

### `ConflictFreeMutation`

同一 graph_version 上不可同时存在多个活跃 proposal。Mutation Manager 必须序列化处理同一目标的变更请求。

### `RetirementBeforeReuse`

处于 `retired` 或 `degraded` 状态的模板不得被实例化用于新任务。

> 各不变量涉及的数据模型（如 `WorkflowGraphVersion`、`PDETemplate`）见 [03-data-models.md](03-data-models.md)。

---

## 4.4 风险分级模型

建议采用三档风险：

## 4.4.1 `Green`

低风险、低成本操作，例如：

- 文献检索
- 参数分析
- 小规模推理
- 只读数据查询

默认策略：

- 自动放行
- 强制记录审计日志

## 4.4.2 `Yellow`

中等风险操作，例如：

- 中等成本训练
- batch operator inference
- candidate graph benchmark
- 大量数据预处理

默认策略：

- 预算检查
- 限制资源
- 保留 observation hooks

## 4.4.3 `Red`

高风险操作，例如：

- 高成本 PINN / PINO 训练
- HPC 提交
- live graph cutover
- validator / policy 相关变更
- 热加载关键组件

默认策略：

- coordinator 批准
- policy 审查
- 强制 checkpoint
- observation window
- 必须具备 rollback target

#### 量化阈值建议

| 维度 | Green | Yellow | Red |
|---|---|---|---|
| GPU 时间 | < 1 小时 | 1–10 小时 | > 10 小时 |
| LLM Token | < 100K | 100K–1M | > 1M |
| HPC 提交 | 无 | 测试规模 | 生产规模 |
| Walltime | < 30 分钟 | 30 分钟–4 小时 | > 4 小时 |
| 图版本变更 | 无 | 候选评估 | live graph cutover |

满足任一 Red 维度即按 Red 级管理。

#### PDE 特有风险场景

- **多物理耦合**（如流固耦合、热力耦合）：耦合本身引入稳定性风险，独立于成本
- **反问题迭代循环**：单次前向求解可能为 Green/Yellow，但累计成本可能达到 Red
- **网格生成失败**：几何预处理损坏导致下游求解全部失效
- **外部数据完整性**：实验数据、CAD 文件引入的质量风险
- **自增长累积成本**：多次 Level 1 参数调优的累计消耗可能超过单次 Level 3

建议：当累计 Yellow 级操作超过 5 次或累计 GPU 时间超过 10 小时，自动升级为 Red 级。

---

## 4.5 预算治理

## 4.5.1 预算维度

建议同时管理：

- `token_budget`
- `gpu_hours`
- `cpu_hours`
- `walltime`
- `hpc_quota`
- `storage_budget`
- `candidate_eval_budget`

## 4.5.2 预算作用点

预算检查不应只在任务入口出现，而应在以下位置反复检查：

- 任务接入前
- 每次 worker 波次执行前
- 长航时任务心跳点
- candidate graph 验证前
- hot reload / migration 前

### 预算超限后的动作

- `soft_limit`：降级路径 / 减少并发 / 改用 surrogate
- `hard_limit`：立即阻断，进入 `ESCALATE` 或 `FAILED`

---

## 4.6 观察窗口与回滚

## 4.6.1 为什么需要观察窗口

即使 candidate graph 已通过静态与沙盒验证，也可能在真实任务中退化。

因此激活后应保留一段 observation window，用于监控：

- scientific accuracy 是否下降
- residual / BC satisfaction 是否退化
- latency / cost 是否超预期
- failure rate 是否上升

#### 观察窗口参数

- **默认持续时间**：`min(K=3 个已完成任务, T=30 分钟)`
- **稳定判定**：Evaluation Engine 判定核心指标（精度、残差、可复现性）稳定在 cutover 前基线的 ±5% 范围内
- **退化判定**：任一核心指标低于基线超过 10%，自动触发 rollback
- **决策者**：Evaluation Engine 收集指标并给出 stabilize / rollback 建议；Policy Engine 保留最终否决权
- **最大窗口**：不超过 2 小时，超时未稳定则自动 rollback

## 4.6.2 回滚条件

建议在以下情况下触发 rollback：

- 关键指标显著退化
- 不变量被触发
- 热加载迁移失败
- validator 发现系统性违规
- candidate graph 进入 dead-end family

回滚对象应包括：

- active graph version
- runtime config
- validator pack
- template binding
- checkpoint lineage

> 自增长四级阶梯与升级触发条件见 [05-template-library-and-self-growth.md](05-template-library-and-self-growth.md) 第 5.9 节。

---

## 4.7 可观测性分层

## 4.7.1 L1：Telemetry

关注运行时资源与效率：

- latency
- GPU utilization
- memory
- walltime
- token usage
- retry count
- queue wait time

### 用途

- 成本控制
- 性能分析
- 预算预警

---

## 4.7.2 L2：Lifecycle

关注团队与工作流状态：

- team state
- worker active / idle / exited
- task state transitions
- graph version changes
- proposal lifecycle
- rollback events
- hot reload events

### 用途

- 定位系统运行时发生了什么
- 确认是执行问题还是演化问题

---

## 4.7.3 L3：Scientific Evidence

关注科学正确性与证据：

- residual curves
- BC / IC violation maps
- conservation metrics
- energy consistency checks
- baseline comparisons
- confidence / uncertainty summaries
- checkpoint lineage
- validation bundles
- provenance records

### 用途

- 解释为什么结论可信
- 支撑复核与复现
- 支撑 counterfactual 对比

---

## 4.8 审计对象

建议至少审计以下事件：

- team create / delete
- worker spawn / idle / shutdown
- task assignment / completion / cancellation
- budget warnings / denials
- HPC submission
- candidate graph activation
- rollback
- validator upgrade
- hot reload migration
- template promotion / retirement
- final delivery

---

## 4.9 审计链与证据链

## 4.9.1 审计链

审计链强调：

- 谁触发了什么操作
- 何时触发
- 用了什么资源
- 被哪个 policy 判定
- 是否批准 / 回滚

## 4.9.2 证据链

证据链强调：

- 哪个结果来自哪个 graph version
- 哪个 graph version 来自哪个 template / proposal
- 哪个 artifact 支撑哪个结论
- 哪个 validator 给出了通过结论

二者结合后，系统不仅“记录了操作”，也“解释了结果”。

---

## 4.10 replay 与 counterfactual

## 4.10.1 replay

建议支持以下 replay：

- replay 某次 task 的 workflow
- replay 某个 graph version 的执行
- replay 某个 proposal 的验证过程
- replay 某次 hot reload 切换

## 4.10.2 counterfactual

建议支持以下对比：

- `active graph` vs `candidate graph`
- `PINN` vs `PINO`
- `template A` vs `template B`
- `旧 validator` vs `新 validator`

### 价值

这使 AI4PDE 的优化从“感觉更好”变成“证据更强”。

---

## 4.11 热加载治理

热加载不是普通配置刷新，而是高风险治理动作。

### 热加载前必须满足

- 有 checkpoint
- 有 migration adapter
- 有 rollback target
- 有 policy 批准（至少对 `Red` 级变更）

### 热加载后必须满足

- 进入 observation window
- 持续记录指标与证据
- 若退化则立即回滚

---

## 4.12 模板治理

模板是高价值资产，也可能成为污染源。

因此模板治理应包括：

- `draft -> candidate -> stable -> retired` 状态流转
- 模板入库前验证
- 模板表现统计
- 模板退役机制
- 模板与 graph version / proposal 的双向映射

### 晋升条件建议

- 连续通过多个 benchmark
- 满足 reproducibility threshold
- 无关键不变量违规
- 有完整 evidence bundle

---

## 4.13 失败治理

不是所有失败都应直接“修复并继续”。

建议区分：

### 运行期失败

如：

- solver 崩溃
- job timeout
- 资源不足
- artifact 缺失

### 演化失败

如：

- candidate graph 被 policy 否决
- observation window 中性能恶化
- migration 不安全
- validator integrity 被破坏

运行期失败应进入 `FailurePattern`；演化失败应进入 `DeadEndRecord`。

---

## 4.14 对 Aeloon 的实现启发

如果落地到 Aeloon，治理与观测层最好独立于 solver / planner 代码：

- `budget.py`
- `risk_gate.py`
- `audit.py`
- `checkpoint.py`
- `policy.py`
- `evaluation.py`
- `graph_versions.py`

不要把这些横切关注点混入单个 orchestrator 中。

---

## 4.15 最后总结

AI4PDE 的治理、可观测性与审计设计应坚持以下原则：

- 预算不是提示，而是硬边界
- 证据不是附件，而是交付主体的一部分
- rollback 不是异常路径，而是标准演化语义
- 审计不是记日志，而是保留责任链
- replay 不是调试额外功能，而是科学比较能力

只有这样，AI4PDE Agent 才能从“自动化求解器代理”进化为“可信科学运行时”。
