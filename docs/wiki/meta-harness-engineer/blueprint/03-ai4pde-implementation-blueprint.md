# 06. AI4PDE-on-MHE 实现蓝图

## 6.1 文档目的

本文把前面的 AI4PDE 架构设想进一步落到可实施的软件蓝图上，回答两个问题：

- `AI4PDE` 应如何构建在 `MHE` 之上
- `MHE` 负责什么，AI4PDE 域层自己又要实现什么

这里的核心判断是：

```text
MHE = 平台 / 控制平面 / 元演化运行时
AI4PDE = 领域组件 / 科学工作流 / PDE 治理与证据语义
```

也就是说，AI4PDE 不应直接改写 `MHE` 的核心 authority model，而应把自己实现为一个建立在 `MHE` 之上的 domain package。

需要特别对齐当前 MHE 的真实 API 边界：组件接口、manifest 模型与运行时注入点主要位于 `metaharness.sdk.*`，而不是 `metaharness.core.*`。其中最关键的扩展面是：

- `metaharness.sdk.base.HarnessComponent`
- `metaharness.sdk.api.HarnessAPI`
- `metaharness.sdk.manifest.ComponentManifest`
- `metaharness.core.boot.HarnessRuntime`

因此，AI4PDE-on-MHE 的实现应理解为“复用 MHE 的 SDK + runtime core”，而不是“向 core 目录中继续堆新的领域抽象”。
---

## 6.2 总体定位

建议采用以下分层：

### 6.2.1 平台层：MHE

由 `MHE` 继续负责：

- manifest discovery
- component boot
- graph candidate staging
- semantic validation
- graph version commit / rollback
- hot reload / checkpoint / migration
- mutation proposal safety pipeline
- provenance / audit

这些能力已经在 `MHE` 中具备明确的控制平面含义，因此不应在 AI4PDE 中重复实现。

这里还需明确当前 MHE 的两个事实：

- 图的运行时权威模型是 `PendingConnectionSet / GraphSnapshot` 等内部对象；XML 只是导入与配置格式，不是运行时唯一真相
- `SafetyPipeline` 当前主要面向 `MutationProposal` 的评估链，而不是直接替代领域级 scientific validation
### 6.2.2 领域层：AI4PDE

由 AI4PDE 自己负责：

- PDE task schema
- `physics_spec / geometry_spec / data_spec`
- method routing
- solver family binding
- baseline / reference path
- scientific validation
- evidence packaging
- PDE-specific risk / budget / reproducibility policy
- template catalog and mutation trigger semantics

### 6.2.3 治理连接层：AI4PDE Policy + Evidence

AI4PDE 还应在 `MHE` 之上增加一层科学治理语义：

- 高成本训练审批
- HPC 提交审批
- 证据包完整性检查
- reproducibility threshold
- candidate graph scientific acceptance gate
- active vs candidate 对照评估

---

## 6.3 实现原则

### 6.3.1 优先构建域组件，而不是先改内核

第一阶段不建议直接修改：

- `MHE/src/metaharness/core/boot.py`
- `MHE/src/metaharness/core/connection_engine.py`
- `MHE/src/metaharness/core/mutation.py`

优先做法是：

- 新建 AI4PDE package
- 通过 `HarnessComponent` + `HarnessAPI` + `ComponentManifest` + graph 导入/提交流程接入现有 runtime
- 把 PDE 语义放进组件、契约、模板、验证器中

这里的 `HarnessComponent` 指的是 `metaharness.sdk.base.HarnessComponent`。AI4PDE 组件至少应实现：

- `declare_interface(api)`
- `activate(runtime)`
- `deactivate()`

并在需要热加载时逐步补充：

- `export_state()` / `import_state()`
- `suspend()` / `resume()`
- `transform_state()`
### 6.3.2 先把 happy path 打通，再引入自增长

推荐演进顺序：

1. hand-authored graph
2. 单 benchmark 闭环
3. baseline/reference 对照
4. budget/risk/policy 接入
5. template catalog
6. mutation proposal
7. candidate graph 观察窗口

### 6.3.3 优先参数演化，延后拓扑演化

在真正稳定之前，AI4PDE 应主要做：

- solver 参数优化
- routing threshold 调整
- validation profile 调整

而不是一开始就做：

- 任意 graph rewiring
- 任意 template synthesis
- live component replacement

### 6.3.4 域逻辑进组件，治理逻辑进策略层

不要把所有 PDE 逻辑塞进单个 orchestrator。

建议边界如下：

- 组件：负责执行与领域产物
- validator：负责科学正确性判断
- policy：负责放行 / 否决 / 升级审批
- evidence manager：负责交付语义
- MHE core：负责生命周期与版本控制

---

## 6.4 平台层与领域层职责划分

| 层 | 职责 | 是否复用 MHE |
|---|---|---|
| Boot / discovery | manifest 装配、依赖排序、activation | 是 |
| Graph lifecycle | candidate、commit、rollback、versioning | 是 |
| Safety pipeline | semantic validation、policy veto、auto rollback | 是 |
| Hot reload | checkpoint、migration、observation | 是 |
| Provenance / audit | trace、audit、evidence primitives | 是 |
| PDE task formalization | physics / geometry / data 三元规格化 | 否，AI4PDE 自己实现 |
| Solver execution | PINN / DEM / Operator / PINO / Classical Hybrid | 否，AI4PDE 自己实现 |
| Scientific validation | residual / BC / IC / conservation / baseline compare | 否，AI4PDE 自己实现 |
| Scientific evidence bundle | 结果 + 证据 + 图版本 + provenance 打包 | 否，AI4PDE 自己实现 |
| PDE policy | GPU/HPC 风险、预算、reproducibility | 否，AI4PDE 自己实现 |

---

## 6.5 AI4PDE 领域组件蓝图

建议第一批组件至少包括：

### 6.5.1 `PDEGateway`

职责：

- 接收原始任务输入
- 生成 `PDETaskRequest`
- 作为 AI4PDE graph 的入口边界

### 6.5.2 `PDEProblemFormulator`

职责：

- 把自然语言 / 上层输入整理为：
  - `physics_spec`
  - `geometry_spec`
  - `data_spec`
- 补齐 problem family 与 deliverables 语义

### 6.5.3 `PDEMethodRouter`

职责：

- 根据任务三元组选择方法族
- 决定：
  - `PINN Strong`
  - `DEM / Energy`
  - `Operator Learning`
  - `PINO`
  - `Classical Hybrid`
- 给出 template family 候选

### 6.5.4 `PDEPlanner`

职责：

- 将 task + routing decision 转为 `PDEPlan`
- 明确 slot binding、validator requirements、expected artifacts

### 6.5.5 `GeometryAdapter`

职责：

- 统一 mesh / CAD / point cloud / SDF 的输入处理
- 输出 solver-ready artifact references

### 6.5.6 `SolverExecutor`

职责：

- 作为统一执行槽位
- 由不同实现提供具体求解能力：
  - `PINNStrongExecutor`
  - `DEMEnergyExecutor`
  - `OperatorLearningExecutor`
  - `PINOExecutor`
  - `ClassicalHybridExecutor`

### 6.5.7 `ReferenceSolver`

职责：

- 运行 baseline / classical reference path
- 为 scientific validation 提供对照对象

### 6.5.8 `PhysicsValidator`

职责：

- residual quality
- BC / IC satisfaction
- conservation / energy consistency
- reference divergence
- 输出 `ValidationBundle` 与 `next_action`

### 6.5.9 `EvidenceManager`

职责：

- 构建 `ScientificEvidenceBundle`
- 绑定：
  - graph version
  - template id
  - solver config
  - validation summary
  - checkpoint lineage
  - provenance refs

### 6.5.10 `KnowledgeAdapter`

职责：

- 将文献、规则、经验模板与结构化先验统一映射为可查询输入
- 为 `PDEMethodRouter`、`PDEPlanner` 与 `PhysicsValidator` 提供知识上下文
- 保持为平台可复用的能力组件，而不是把知识逻辑内嵌进单个 planner

### 6.5.11 `ExperimentMemory`

职责：

- 存储 benchmark snapshots
- 记录 failure pattern
- 记录 evaluation summary
- 供 template / mutation 层复用

它更适合扮演领域侧实验记忆，而不是替代架构规范中的平台级 `AssetMemory` / provenance store。

### 6.5.12 `RiskPolicy`

职责：

- 对 GPU / walltime / HPC / reproducibility 风险做审批判断
- 将 generic MHE safety 扩展为 PDE-specific safety

### 6.5.13 `ObservabilityHub`

职责：

- 记录 L1 telemetry
- 记录 L2 lifecycle
- 记录 L3 scientific evidence metrics

### 6.5.14 `PDECoordinator`（控制面角色，不一定作为图节点）

职责：

- 作为用户唯一对话点与高风险审批桥
- 代理 worker / domain proposal 到 MHE mutation authority
- 管理 team runtime 语义（若后续把 AI4PDE team runtime 也落到 MHE 扩展层）

当前更合理的定位是“控制面协调者”而非第一批数据平面 graph node。

---

## 6.6 核心数据契约蓝图

AI4PDE 应先稳定以下核心契约，再推进复杂演化。

### 6.6.1 `PDETaskRequest`

建议字段：

- `task_id`
- `goal`
- `problem_type`
- `physics_spec`
- `geometry_spec`
- `data_spec`
- `deliverables`
- `budget`
- `risk_level`

### 6.6.2 `PDEPlan`

建议字段：

- `plan_id`
- `task_id`
- `selected_method`
- `template_id`
- `graph_family`
- `slot_bindings`
- `parameter_overrides`
- `required_validators`
- `expected_artifacts`

### 6.6.3 `PDERunArtifact`

建议字段：

- `run_id`
- `task_id`
- `solver_family`
- `artifact_refs`
- `checkpoint_refs`
- `telemetry_refs`

### 6.6.4 `ValidationBundle`

建议字段：

- `validation_id`
- `task_id`
- `graph_version_id`
- `residual_metrics`
- `bc_ic_metrics`
- `conservation_metrics`
- `reference_comparison`
- `violations`
- `next_action`

### 6.6.5 `ScientificEvidenceBundle`

建议字段：

- `bundle_id`
- `task_id`
- `graph_version_id`
- `template_id`
- `solver_config`
- `validation_summary`
- `artifact_hashes`
- `checkpoint_refs`
- `provenance_refs`
- `reference_comparison_refs`

### 6.6.6 `BudgetRecord`

建议字段：

- `token_budget`
- `gpu_hours`
- `cpu_hours`
- `walltime`
- `hpc_quota`
- `candidate_eval_budget`

---

## 6.7 第一批图拓扑蓝图

### 6.7.1 `ai4pde-minimal`

最小 happy path：

```text
PDEGateway
  → PDEProblemFormulator
    → PDEMethodRouter
      → SolverExecutor
        → PhysicsValidator
          → EvidenceManager
```

目标：

- 先打通“单路径求解 + 验证 + 证据封装”
- 不引入 reference path
- 不引入 mutation

### 6.7.2 `ai4pde-baseline`

加入 baseline 对照：

```text
PDEGateway
  → PDEPlanner
    → SolverExecutor
      → PhysicsValidator
PDEPlanner
  → ReferenceSolver
    → PhysicsValidator
PhysicsValidator
  → EvidenceManager
    → ExperimentMemory
```

目标：

- 支持 candidate 与 baseline 对比
- 支持 benchmark snapshots 写入 memory

### 6.7.3 `ai4pde-expanded`

加入治理与观测：

```text
PDEGateway
  → PDEProblemFormulator
    → PDEMethodRouter
      → PDEPlanner
        → GeometryAdapter
        → SolverExecutor
        → ReferenceSolver
          → PhysicsValidator
            → EvidenceManager
              → ExperimentMemory

KnowledgeAdapter、RiskPolicy、ObservabilityHub 作为已 boot 的辅助组件或控制面 helper 接入，
不必在第一版 XML 中都表现为主数据流节点。
```

目标：

- 将 PDE policy 与 observability 纳入正式架构
- 与当前 MHE 示例保持一致：主 graph 先表达核心数据流，部分 control-plane helper 可先作为 runtime 辅助组件存在
- 为后续 mutation proposal 做准备

---

## 6.8 槽位与保护策略蓝图

建议 AI4PDE 使用稳定槽位：

- `ProblemFormulator`
- `MethodRouter`
- `KnowledgeAdapter`
- `GeometryAdapter`
- `SolverExecutor`
- `ReferenceSolver`
- `PhysicsValidator`
- `EvidenceManager`
- `AssetMemory`
- `ObservabilityHub`
- `PolicyGuard`

其中：

- `ExperimentMemory` 是 AI4PDE 领域组件，可挂接到 `AssetMemory` / provenance / benchmark 语义之上
- `PDECoordinator` 是控制面角色，不属于 canonical runtime slot

### 建议 protected slots

- `PolicyGuard`
- `EvidenceManager`
- `ObservabilityHub`
- `ReferenceSolver`

理由：

- `PolicyGuard` 负责放行与否决，不能被普通 proposal 静默替换
- `EvidenceManager` 决定交付证据结构，不能在任务中途被弱化
- `ObservabilityHub` 负责观察窗口的输入来源，不能被绕过

---

## 6.9 安全与治理蓝图

AI4PDE 应复用 MHE 已有安全链路：

- candidate graph validation
- policy veto
- A/B shadow evaluation
- auto rollback

但要补充领域特定 gate：

- residual threshold gate
- BC / IC satisfaction gate
- conservation gate
- baseline divergence gate
- budget overrun gate
- reproducibility gate

### 关键原则

- generic safety 交给 MHE
- scientific acceptance gate 交给 AI4PDE
- proposal 只能建议，不能直接写 active graph

---

## 6.10 Hot Reload 与长航时作业蓝图

AI4PDE 不应一开始就支持“任意 solver 中途切换”。

第一阶段仅建议对以下对象启用 hot reload：

- validator upgrade
- evidence schema upgrade
- planner/router upgrade
- 非运行中辅助组件

延后支持：

- 跨 solver family 的中途热切换
- 无 checkpoint 的 live replacement

要做到安全热切换，AI4PDE 需要自己补充：

- solver checkpoint migration adapters
- evidence schema migration adapters
- template metadata migration adapters
- worker state migration adapters

---

## 6.11 模板与优化器接入蓝图

### v0.1

- 不引入 optimizer
- hand-authored graphs only

### v0.2

- 引入 parameter templates
- 支持：
  - PINN
  - DEM
  - Operator
  - PINO
  - Classical Hybrid

### v0.3

- 引入 template instantiation
- 支持 benchmark ranking

### v0.4

- 引入 mutation proposal
- 支持 graph rewiring candidate
- 仍保持 proposal-only authority

### v0.5

- 引入 observation-window-driven promotion
- active vs candidate 科学对照成为常规路径

---

## 6.12 分阶段落地路线

### Phase A：可运行闭环

实现：

- `PDEGateway`
- `PDEProblemFormulator`
- `PDEMethodRouter`
- 一个 `SolverExecutor`
- `PhysicsValidator`
- `EvidenceManager`

目标：

- 跑通一个 benchmark case

### Phase B：baseline 对照

实现：

- `ReferenceSolver`
- `ExperimentMemory`

目标：

- 形成 active path + baseline path

### Phase C：治理与观测

实现：

- `RiskPolicy`
- `ObservabilityHub`
- `BudgetRecord`

目标：

- 具备 PDE-specific 审批与成本治理

### Phase D：模板化

实现：

- template catalog
- template instantiation pipeline

目标：

- 减少从零规划

### Phase E：受控演化

实现：

- mutation triggers
- proposal builders
- observation window acceptance

目标：

- 在不破坏治理边界的前提下引入自增长

---

## 6.13 最后总结

AI4PDE-on-MHE 的正确实现姿势不是“把 PDE 逻辑硬塞进 MHE 内核”，而是：

- 让 `MHE` 继续做控制平面、图生命周期、热加载、安全与审计
- 让 AI4PDE 做领域组件、科学验证、证据语义与治理规则
- 先打通可运行 benchmark 闭环
- 再引入 baseline、模板、proposal、candidate graph 演化

这样可以保证：

- 系统结构清晰
- 域逻辑与平台逻辑边界清楚
- 后续演化不会破坏 runtime authority
- AI4PDE 的自增长始终处在可治理范围内
