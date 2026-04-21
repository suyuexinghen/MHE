# 08. Development Roadmap

## 8.1 文档目的

本文将 `07-scaffold-plan.md` 中的文件级脚手架方案，进一步转化为里程碑驱动的执行路线图。

目标不是一次性把 AI4PDE 全部实现完，而是将其拆成一系列：

- 可以验证的 milestone
- 可以交付的最小增量
- 可以度量的技术完成标准
- 可以挂接到后续 template / mutation / hot reload 的演进节点

因此，这份 roadmap 关注的是：

- 每个阶段要完成哪些任务
- 每个阶段的产出物是什么
- 哪些任务是阻塞项
- 什么叫“这个 milestone 完成了”

---

## 8.2 路线设计原则

### 8.2.1 先跑通，再泛化

先证明：

- MHE 可以承载 AI4PDE domain package
- PDE happy path 能形成完整闭环
- scientific validation 与 evidence delivery 能接进 graph runtime

再逐步加入：

- baseline/reference compare
- budget/risk/policy
- template catalog
- mutation proposal
- observation window

### 8.2.2 先稳定边界，再引入自增长

优先稳定：

- data contracts
- slot vocabulary
- capability vocabulary
- component boundaries
- graph topology

而不是优先稳定：

- optimizer autonomy
- code generation
- topology synthesis

### 8.2.3 让每个里程碑都有演示路径

每个 milestone 都应能回答：

- 有没有 demo graph
- 有没有 benchmark case
- 有没有测试验证
- 有没有清晰的 done criteria

### 8.2.4 提前划清平台与领域边界

roadmap 中所有任务都应遵循：

- 除非绝对必要，不修改 `MHE` core
- AI4PDE 作为 domain package 演进
- 若需要扩展 MHE，只做明确且最小的 extension point 补充

---

## 8.3 Milestone 总览

建议将开发拆为 6 个 milestone：

- `M0`：Domain Foundation
- `M1`：Minimal PDE Happy Path
- `M2`：Reference / Baseline Validation Loop
- `M3`：Scientific Governance and Observability
- `M4`：Template Catalog and Reusable Workflows
- `M5`：Controlled Evolution and Candidate Graph Proposals

其中：

- `M0-M2` 是“把 AI4PDE 跑起来”
- `M3-M5` 是“把 AI4PDE 变成可治理、可演化系统”

---

## 8.4 Milestone M0：Domain Foundation

### 8.4.1 目标

建立 AI4PDE domain package 的最小基础设施，使后续组件不必一边开发一边反复重写词汇表与契约。

### 8.4.2 任务列表

#### Task M0-1：创建 package skeleton

创建目录：

```text
MHE/src/metaharness_ai4pde/
MHE/src/metaharness_ai4pde/components/
MHE/src/metaharness_ai4pde/executors/
MHE/src/metaharness_ai4pde/validation/
MHE/src/metaharness_ai4pde/evidence/
MHE/src/metaharness_ai4pde/policies/
MHE/src/metaharness_ai4pde/templates/
MHE/src/metaharness_ai4pde/mutations/
MHE/src/metaharness_ai4pde/fixtures/
MHE/src/metaharness_ai4pde/benchmarks/
```

并同步更新：

- `MHE/pyproject.toml`

确保新 package 能被 wheel / editable install / pytest 正式识别。
#### Task M0-2：定义基础类型与枚举

实现文件：

- `types.py`
- `slots.py`
- `capabilities.py`

最少要稳定：

并在此阶段完成一次 SDK 对齐检查，确保命名和语义不偏离：

- `metaharness.sdk.base.HarnessComponent`
- `metaharness.sdk.manifest.ComponentManifest`
- `metaharness.sdk.contracts.*`
- `MHE/examples/manifests/baseline/` 的现有写法
- problem type
- solver family
- risk level
- next action
- template status
- protected slots
- canonical capabilities

#### Task M0-3：定义核心 contracts

实现文件：

- `contracts.py`

至少定义：

- `PDETaskRequest`
- `PDEPlan`
- `PDERunArtifact`
- `ValidationBundle`
- `ScientificEvidenceBundle`
- `BudgetRecord`

#### Task M0-4：补充基础单元测试

实现文件：

- `MHE/tests/test_ai4pde_contracts.py`

测试重点：

- schema validity
- type serialization
- required field completeness

### 8.4.3 产出物

- 一个可 import 的 `metaharness_ai4pde` package
- 一套基础 AI4PDE vocabulary
- 一套可复用 contracts
- 第一批 contract tests

### 8.4.4 完成标准

满足以下条件可认为 `M0` 完成：

- 所有基础模块可导入
- contracts 测试通过
- 后续组件无需再自定义重复 schema

### 8.4.5 阻塞关系

- `M0` 是所有后续 milestone 的前置条件

---

## 8.5 Milestone M1：Minimal PDE Happy Path

### 8.5.1 目标

在 MHE 上跑通一个最小 PDE 任务闭环：

```text
input → formulate → route → execute → validate → evidence
```

### 8.5.2 任务列表

#### Task M1-1：实现最小组件集

创建：

- `components/pde_gateway.py`
- `components/problem_formulator.py`
- `components/method_router.py`
- `components/solver_executor.py`
- `components/physics_validator.py`
- `components/evidence_manager.py`

要求：

- 每个组件都以 `metaharness.sdk.base.HarnessComponent` 为真实基类
- 至少实现 `declare_interface(api)`、`activate(runtime)`、`deactivate()`
- 组件声明通过 `HarnessAPI` 完成，而不是绕开 SDK 直接写 registry/internal graph
#### Task M1-2：实现一个最小 executor backend

创建：

- `executors/pinn_strong.py`

要求：

- 不追求复杂 solver 集成
- 先用可测试、可重复的小路径打通 contract flow

#### Task M1-3：实现基础 validation helpers

创建：

- `validation/residuals.py`
- `validation/boundary_conditions.py`

至少支持：

- minimal residual summary
- minimal BC/IC consistency summary

#### Task M1-4：实现 evidence bundling

创建：

- `evidence/bundle.py`

要求：

- 能把运行结果 + validation summary + graph metadata 打成最小证据包

#### Task M1-5：创建 minimal manifests

创建目录及文件：

```text
MHE/examples/manifests/ai4pde/
pde_gateway.json
problem_formulator.json
method_router.json
solver_executor.json
physics_validator.json
evidence_manager.json
```

要求：

- manifest schema 严格对齐 `metaharness.sdk.manifest.ComponentManifest`
- 至少包含 `name`、`version`、`kind`、`entry`、`harness_version`、`contracts`、`safety`、`state_schema_version`
- `slots` / `provides` / `requires` 主要落在 `contracts` 内，而不是额外自造顶层字段
#### Task M1-6：创建最小 graph

创建：

- `MHE/examples/graphs/ai4pde-minimal.xml`

说明：

- XML 在当前 MHE 中是 graph 的导入/配置格式
- 运行时真正提交的是由 XML 解析得到的 `PendingConnectionSet / GraphSnapshot`
- 因此该任务的目标是“形成可导入、可校验、可提交的 graph 示例”，而不是把 XML 当作唯一运行时真相
#### Task M1-7：添加最小 E2E 测试

创建：

- `MHE/tests/test_ai4pde_graphs.py`
- `MHE/tests/test_ai4pde_minimal_demo.py`

### 8.5.3 产出物

- 最小 AI4PDE demo graph
- 一个可执行 happy path
- 最小证据包输出
- E2E 回归测试

### 8.5.4 完成标准

满足以下条件可认为 `M1` 完成：

- `ai4pde-minimal.xml` 可以通过结构与语义校验
- minimal graph 可以 boot + commit + run
- output 中包含 validation summary 与 evidence bundle
- E2E 测试通过

### 8.5.5 阻塞关系

- 依赖 `M0`
- `M2-M5` 依赖 `M1`

---

## 8.6 Milestone M2：Reference / Baseline Validation Loop

### 8.6.1 目标

把“能运行”升级为“能做科学对照”，形成 baseline/reference compare 闭环。

### 8.6.2 任务列表

#### Task M2-1：实现 `ReferenceSolver`

创建：

- `components/reference_solver.py`

#### Task M2-2：实现 reference comparison helper

创建：

- `validation/reference_compare.py`

要求：

- 至少给出 candidate vs baseline 的 divergence summary

#### Task M2-3：实现 `ExperimentMemory`

创建：

- `components/experiment_memory.py`

要求：

- 记录 benchmark snapshot
- 记录 run summary
- 记录 failure summary

#### Task M2-4：扩展 graph

创建：

- `MHE/examples/graphs/ai4pde-baseline.xml`

#### Task M2-5：扩展 evidence bundle

更新：

- `contracts.py`
- `evidence/bundle.py`

使其包含：

- reference comparison refs
- baseline metadata
- benchmark snapshot refs

#### Task M2-6：添加基线回归测试

创建：

- `MHE/tests/test_ai4pde_validation.py`

### 8.6.3 产出物

- baseline/reference path
- active-vs-baseline compare 输出
- benchmark snapshots 写入 memory

### 8.6.4 完成标准

满足以下条件可认为 `M2` 完成：

- baseline graph 可运行
- validator 能同时消费 candidate 与 baseline 结果
- evidence bundle 中包含 reference compare 信息
- validation tests 通过

### 8.6.5 阻塞关系

- 依赖 `M1`
- `M3-M5` 强依赖 `M2`

---

## 8.7 Milestone M3：Scientific Governance and Observability

### 8.7.1 目标

把 generic MHE safety 升级为 AI4PDE-specific scientific governance。

### 8.7.2 任务列表

#### Task M3-1：实现 `RiskPolicy`

创建：

- `components/risk_policy.py`

说明：

- 在当前 MHE 模式下，`RiskPolicy` 更适合作为 governance/control-plane helper 或已 boot 组件
- 不要求它在第一版 graph XML 中就是主数据流节点
- 其职责应与 MHE 的 mutation `SafetyPipeline` 区分：前者面向 PDE 科学治理，后者面向 proposal gating
#### Task M3-2：实现 policy helpers

创建：

- `policies/budget.py`
- `policies/risk.py`
- `policies/reproducibility.py`

要求：

- budget checks
- Green/Yellow/Red classification
- reproducibility threshold checks

#### Task M3-3：实现 `ObservabilityHub`

创建：

- `components/observability_hub.py`

#### Task M3-4：定义 observation window 语义

创建：

- `policies/observation_window.py`

至少定义：

- 最小任务数
- 最小时长
- degrade trigger
- rollback recommendation 规则

#### Task M3-5：扩展 contracts

更新：

- `contracts.py`

加入更明确的：

- telemetry refs
- lifecycle refs
- budget state

#### Task M3-6：创建 expanded graph

创建：

- `MHE/examples/graphs/ai4pde-expanded.xml`

#### Task M3-7：增加 policy tests

创建：

- `MHE/tests/test_ai4pde_policy.py`

### 8.7.3 产出物

- PDE-specific budget/risk governance
- scientific observability hooks
- observation window semantics

### 8.7.4 完成标准

满足以下条件可认为 `M3` 完成：

- 高成本操作能经过 policy classification
- 观测数据能够进入 evidence / observation flow
- policy tests 通过
- expanded graph 通过验证

### 8.7.5 阻塞关系

- 依赖 `M2`
- `M4-M5` 依赖 `M3`

---

## 8.8 Milestone M4：Template Catalog and Reusable Workflows

### 8.8.1 目标

把可运行图与经验路径沉淀成模板库，减少从零规划。

### 8.8.2 任务列表

#### Task M4-1：建立模板目录

创建：

- `templates/catalog.py`
- `templates/status.py`

初始模板建议：

- `ForwardSolidMechanicsTemplate`
- `ForwardFluidMechanicsTemplate`
- `InverseParameterIdentificationTemplate`
- `OperatorSurrogateTemplate`
- `PINOHybridCorrectionTemplate`
- `ValidationBundleTemplate`
- `EvidencePackagingTemplate`

#### Task M4-2：实现模板实例化

创建：

- `templates/instantiation.py`

职责：

- task → template match
- template → slot binding
- parameter overrides application

#### Task M4-3：让 planner 接 template

更新：

- `components/method_router.py`
- `components/pde_planner.py`

使其支持：

- candidate template list
- template-aware planning

#### Task M4-4：扩展 benchmark memory

更新：

- `components/experiment_memory.py`

加入：

- template performance summaries
- promotion inputs

#### Task M4-5：添加模板相关测试

扩展或新增：

- `MHE/tests/test_ai4pde_components.py`
- 可选新增 `MHE/tests/test_ai4pde_templates.py`

### 8.8.3 产出物

- AI4PDE template catalog
- template-aware planner
- reusable workflow skeletons

### 8.8.4 完成标准

满足以下条件可认为 `M4` 完成：

- 至少 3 个模板可被实例化
- planner 能基于 task family 命中模板
- 模板状态与 metadata 可追踪

### 8.8.5 阻塞关系

- 依赖 `M3`
- `M5` 依赖 `M4`

---

## 8.9 Milestone M5：Controlled Evolution and Candidate Graph Proposals

### 8.9.1 目标

在不破坏 MHE authority model 的前提下，引入 AI4PDE 的 proposal-based controlled evolution。

### 8.9.2 任务列表

#### Task M5-1：定义 AI4PDE mutation triggers

创建：

- `mutations/triggers.py`

建议触发条件：

- repeated `PARTIAL`
- benchmark plateau
- repeated failure family
- baseline divergence widening
- cost too high

#### Task M5-2：定义 proposal builders

创建：

- `mutations/proposals.py`

至少支持：

- parameter tuning proposal
- validator profile adjustment proposal
- graph rewiring proposal
- template substitution proposal

#### Task M5-3：扩展 benchmark runner

创建：

- `benchmarks/runner.py`

职责：

- 对 active/candidate graph 做对照评估
- 生成 evaluation snapshot

#### Task M5-4：把 observation window 接到 mutation flow

更新：

- `policies/observation_window.py`
- `components/observability_hub.py`
- `components/risk_policy.py`

#### Task M5-5：增加 mutation flow tests

创建：

- `MHE/tests/test_ai4pde_mutation_flow.py`

重点验证：

- AI4PDE proposal 仍然遵守 proposal-only 语义
- 不能直接写 active graph

### 8.9.3 产出物

- AI4PDE mutation trigger system
- proposal builders
- candidate-vs-active benchmark runner
- 观察窗口 acceptance path

### 8.9.4 完成标准

满足以下条件可认为 `M5` 完成：

- proposal 可生成、可评估、可提交审查
- active/candidate graph 能在固定 benchmark 上对比
- mutation tests 通过
- proposal 不绕过 MHE governance

### 8.9.5 阻塞关系

- 依赖 `M4`

---

## 8.10 关键交付节奏建议

建议按以下节奏推进：

### Wave 1

- `M0`
- `M1`

目标：证明 domain package 路线成立。

### Wave 2

- `M2`
- `M3`

目标：证明 AI4PDE 已具备“科学 runtime”而非普通 demo graph。

### Wave 3

- `M4`
- `M5`

目标：证明 AI4PDE 已具备“可复用 + 可演化”的系统特征。

---

## 8.11 关键风险与控制点

### 风险 1：过早改 MHE core

控制策略：

- 先用 domain package 完成 `M0-M2`
- 只有当 extension point 不足时，才做最小 core patch
- 若确需扩展，优先补充 `sdk`/loader/packaging 级 extension point，而不是直接改写 graph authority 或 boot/commit 主流程
### 风险 2：过早引入复杂 solver integration

控制策略：

- `M1` 只要求最小可测执行路径
- 复杂外部 solver integration 放到后续迭代

### 风险 3：过早做 optimizer autonomy

控制策略：

- `M5` 前不引入复杂自增长
- proposal-only 语义必须保持

### 风险 4：验证与证据语义滞后

控制策略：

- `M1` 就必须落最小 evidence bundle
- `M2-M3` 持续增强 scientific validation 与 observability

---

## 8.12 最后总结

这份 development roadmap 将 AI4PDE 的实现拆解为一条从“可运行”到“可治理”再到“可演化”的路线：

- `M0`：稳定 domain vocabulary 与 contracts
- `M1`：打通最小 PDE happy path
- `M2`：加入 baseline/reference compare
- `M3`：加入 budget/risk/observation governance
- `M4`：加入 template catalog
- `M5`：加入 controlled mutation proposal

这条路线的核心优点是：

- 每个阶段都有明确产出
- 每个阶段都可测试、可演示、可回归
- 不会一开始就把 AI4PDE 变成过度复杂的“自增长大系统”
- 始终保持 `MHE` 负责平台 authority，AI4PDE 负责科学领域语义
