# 07. Repo-Ready Scaffold Plan

## 7.1 文档目的

本文将 `AI4PDE-on-MHE` 的实现蓝图转化为可直接落地的脚手架计划，重点回答：

- 应该创建哪些文件
- 每个文件负责什么
- 应该按什么顺序实现
- 哪些边界必须在一开始就划清

本文不是最终代码结构的唯一可能形式，但它提供了一套尽量贴近当前 `MHE` 仓库状态的可执行脚手架方案。

---

## 7.2 根目录建议

建议新增一个独立 domain package：

```text
MHE/src/metaharness_ai4pde/
```

这样做的好处是：

- 不污染 `metaharness` 核心命名空间
- 便于把 AI4PDE 视作建立在 MHE 之上的 domain layer
- 后续若扩展更多 scientific domains，也能保持对称结构

但必须同时注意当前打包现实：`MHE/pyproject.toml` 现在只打包 `src/metaharness`，因此若真正落地该 package，还需要同步更新打包配置，使 `metaharness_ai4pde` 能进入 wheel / editable install。否则该目录即使存在，也不会成为正式分发包的一部分。
---

## 7.3 顶层包结构

建议目录：

```text
MHE/src/metaharness_ai4pde/
├── __init__.py
├── contracts.py
├── types.py
├── slots.py
├── capabilities.py
├── components/
├── executors/
├── validation/
├── evidence/
├── policies/
├── templates/
├── mutations/
├── fixtures/
└── benchmarks/
```

---

## 7.4 顶层模块

### 7.4.1 `__init__.py`

职责：

- package marker
- 暴露最关键的 public symbols
- 不放复杂逻辑

### 7.4.2 `contracts.py`

职责：

- 定义 AI4PDE 的核心共享契约
- 建议使用与 MHE 一致的 typed model 风格

这里的“与 MHE 一致”具体应指向当前 SDK / Pydantic 模型风格，而不是自定义一套与 `metaharness.sdk.*` 脱节的 schema 约定。
建议放入：

- `PDETaskRequest`
- `PDEPlan`
- `PDERunArtifact`
- `ReferenceResult`
- `ValidationBundle`
- `ScientificEvidenceBundle`
- `BudgetRecord`

这是整个 AI4PDE domain layer 的公共数据边界。

### 7.4.3 `types.py`

职责：

- 放置枚举与字面值常量类型

建议放入：

- `ProblemType`
- `SolverFamily`
- `RiskLevel`
- `NextAction`
- `TemplateStatus`
- `ProposalType`

### 7.4.4 `slots.py`

职责：

- 统一声明 AI4PDE 的 canonical slot names
- 声明 protected slot 集合

建议放入：

- `PROBLEM_FORMULATOR_SLOT`
- `METHOD_ROUTER_SLOT`
- `KNOWLEDGE_ADAPTER_SLOT`
- `GEOMETRY_ADAPTER_SLOT`
- `SOLVER_EXECUTOR_SLOT`
- `REFERENCE_SOLVER_SLOT`
- `PHYSICS_VALIDATOR_SLOT`
- `EVIDENCE_MANAGER_SLOT`
- `ASSET_MEMORY_SLOT`
- `OBSERVABILITY_HUB_SLOT`
- `POLICY_GUARD_SLOT`
- `PROTECTED_SLOTS`

其中：

- `ExperimentMemory` 建议作为领域组件存在，不直接替代 canonical `AssetMemory` slot
- `PROTECTED_SLOTS` 应至少与架构规范保持一致，包含 `PolicyGuard`、`EvidenceManager`、`ObservabilityHub`、`ReferenceSolver`
### 7.4.5 `capabilities.py`

职责：

- 统一 capability IDs
- 为 manifest 与 planner/method-router 提供共享 capability vocabulary

建议放入：

- `CAP_PINN_STRONG`
- `CAP_DEM_ENERGY`
- `CAP_OPERATOR_LEARNING`
- `CAP_PINO`
- `CAP_CLASSICAL_HYBRID`
- `CAP_REFERENCE_BASELINE`
- `CAP_RESIDUAL_VALIDATION`
- `CAP_CONSERVATION_VALIDATION`
- capability matching helpers

---

## 7.5 Components 目录

```text
MHE/src/metaharness_ai4pde/components/
```

### 7.5.1 `components/__init__.py`

职责：

- 导出组件类
- 不放业务逻辑

### 7.5.2 `components/pde_gateway.py`

职责：

- 原始输入边界
- 将上游输入规范化为 `PDETaskRequest`
- 适合成为 graph entry component

输入：

- raw task payload

输出：

- normalized `PDETaskRequest`

### 7.5.3 `components/problem_formulator.py`

职责：

- 生成：
  - `physics_spec`
  - `geometry_spec`
  - `data_spec`
- 若输入不完整，可标记 clarification-required 状态

输出：

- enriched `PDETaskRequest`

### 7.5.4 `components/method_router.py`

职责：

- 根据任务三元组选择 solver family
- 给出 template 候选
- 输出 routing decision

输出：

- `selected_method`
- `candidate_templates`
- `risk_hint`

### 7.5.5 `components/pde_planner.py`

职责：

- 将 task + routing result 整合为 `PDEPlan`
- 明确 expected artifacts、validator requirements、slot bindings

输出：

- `PDEPlan`

### 7.5.6 `components/geometry_adapter.py`

职责：

- 把 mesh / CAD / SDF / point cloud 整理为 solver-ready artifact refs
- 后期可扩展几何预处理策略

输出：

- geometry artifact bundle

### 7.5.7 `components/solver_executor.py`

职责：

- 作为统一求解槽位的入口
- 选择具体 executor implementation 并调用
- 提供共享执行辅助逻辑

输出：

- `PDERunArtifact`

### 7.5.8 `components/reference_solver.py`

职责：

- 运行 baseline / classical path
- 输出用于 reference compare 的结果

输出：

- `ReferenceResult`

### 7.5.9 `components/physics_validator.py`

职责：

- 统一调度科学验证逻辑
- 调用 residual / BC / IC / conservation / reference compare helpers
- 输出 `ValidationBundle`

输出：

- `ValidationBundle`
- `next_action`

### 7.5.10 `components/evidence_manager.py`

职责：

- 组装 `ScientificEvidenceBundle`
- 将 graph version、template id、validation summary、provenance refs 合并

输出：

- `ScientificEvidenceBundle`

### 7.5.11 `components/knowledge_adapter.py`

职责：

- 提供文献、规则、模板与经验知识的统一查询入口
- 为 router / planner / validator 提供知识上下文
- 对齐 canonical `KnowledgeAdapter` slot

### 7.5.12 `components/experiment_memory.py`

职责：

- 记录 benchmark snapshot
- 存储 failure pattern 摘要
- 提供供 template/mutation 复用的历史上下文

### 7.5.13 `components/risk_policy.py`

职责：

- 做 PDE-specific risk gate
- 判断是否允许高成本训练、HPC 提交、candidate cutover

### 7.5.14 `components/observability_hub.py`

职责：

- 记录 L1 telemetry
- 记录 L2 lifecycle
- 记录 L3 scientific evidence metrics
- 为 observation window 提供输入

### 7.5.15 `components/pde_coordinator.py`（可选，偏控制面）

职责：

- 若后续将 team runtime 语义也下沉到 MHE 扩展层，则充当协调与审批桥
- 不建议作为 M1 的必需 graph node；更适合作为控制面角色或后续扩展组件
---

## 7.6 Executors 目录

```text
MHE/src/metaharness_ai4pde/executors/
```

### 7.6.1 `executors/__init__.py`

职责：

- 导出各 executor

### 7.6.2 `executors/pinn_strong.py`

职责：

- strong-form PINN execution path

### 7.6.3 `executors/dem_energy.py`

职责：

- DEM / energy-form path

### 7.6.4 `executors/operator_learning.py`

职责：

- operator learning path

### 7.6.5 `executors/pino.py`

职责：

- PINO path

### 7.6.6 `executors/classical_hybrid.py`

职责：

- classical baseline / hybrid correction path

### 关键边界

- `components/solver_executor.py` 负责统一调用入口
- `executors/*.py` 负责具体方法族实现
- 不要把所有方法族逻辑塞进一个类

---

## 7.7 Validation 目录

```text
MHE/src/metaharness_ai4pde/validation/
```

### 7.7.1 `validation/__init__.py`

职责：

- 导出验证 helper

### 7.7.2 `validation/residuals.py`

职责：

- residual metric helpers

### 7.7.3 `validation/boundary_conditions.py`

职责：

- BC / IC checks

### 7.7.4 `validation/conservation.py`

职责：

- conservation / energy consistency checks

### 7.7.5 `validation/reference_compare.py`

职责：

- candidate vs baseline compare
- 形成 divergence / agreement summary

### 边界原则

- 这里尽量写 pure validation helpers
- `PhysicsValidator` 负责 orchestration，不直接堆全部公式逻辑

---

## 7.8 Evidence 目录

```text
MHE/src/metaharness_ai4pde/evidence/
```

### 7.8.1 `evidence/__init__.py`

职责：

- 导出 evidence helpers

### 7.8.2 `evidence/bundle.py`

职责：

- evidence bundle assembly
- 保证交付对象不只是文本，而是结果 + 证据 + 图版本 + provenance

### 7.8.3 `evidence/provenance.py`

职责：

- 把 AI4PDE 领域对象映射到 MHE provenance primitives

---

## 7.9 Policies 目录

```text
MHE/src/metaharness_ai4pde/policies/
```

### 7.9.1 `policies/__init__.py`

职责：

- 导出 policy helpers

### 7.9.2 `policies/budget.py`

职责：

- GPU / CPU / walltime / HPC quota checks

### 7.9.3 `policies/risk.py`

职责：

- Green / Yellow / Red classification
- 多物理、inverse loop、HPC、高成本训练场景归类

### 7.9.4 `policies/reproducibility.py`

职责：

- reproducibility threshold checks

### 7.9.5 `policies/observation_window.py`

职责：

- AI4PDE-specific observation window semantics
- 例如：最小任务数、最小时长、退化阈值

---

## 7.10 Templates 目录

```text
MHE/src/metaharness_ai4pde/templates/
```

### 7.10.1 `templates/__init__.py`

职责：

- 导出模板相关接口

### 7.10.2 `templates/catalog.py`

职责：

- 定义初始模板 catalog

建议先放：

- `ForwardSolidMechanicsTemplate`
- `ForwardFluidMechanicsTemplate`
- `InverseParameterIdentificationTemplate`
- `OperatorSurrogateTemplate`
- `PINOHybridCorrectionTemplate`
- `ValidationBundleTemplate`
- `EvidencePackagingTemplate`

### 7.10.3 `templates/instantiation.py`

职责：

- task 到 template 的匹配
- template 到 slot binding 的实例化

### 7.10.4 `templates/status.py`

职责：

- 模板状态与晋升规则 helper

---

## 7.11 Mutations 目录

```text
MHE/src/metaharness_ai4pde/mutations/
```

### 7.11.1 `mutations/__init__.py`

职责：

- 导出 mutation helper

### 7.11.2 `mutations/proposals.py`

职责：

- 构造 AI4PDE-specific `MutationProposal`
- 只构造 proposal，不直接 commit active graph

### 7.11.3 `mutations/triggers.py`

职责：

- plateau / failure / budget / repeated partial 触发条件

### 关键原则

- proposal-only
- 不绕过 MHE mutation authority

---

## 7.12 Fixtures 与 Benchmarks

### 7.12.1 `fixtures/problem_cases.py`

路径：

```text
MHE/src/metaharness_ai4pde/fixtures/problem_cases.py
```

职责：

- 定义最小 canonical PDE case
- 供 demo / tests / benchmarks 复用

### 7.12.2 `benchmarks/runner.py`

路径：

```text
MHE/src/metaharness_ai4pde/benchmarks/runner.py
```

职责：

- 在固定 benchmark cases 上运行 active/candidate graph
- 生成 evaluation snapshot 输入

---

## 7.13 Manifest 文件计划

建议新增目录：

```text
MHE/examples/manifests/ai4pde/
```

建议第一批文件：

- `pde_gateway.json`
- `problem_formulator.json`
- `method_router.json`
- `pde_planner.json`
- `geometry_adapter.json`
- `solver_executor.json`
- `reference_solver.json`
- `physics_validator.json`
- `evidence_manager.json`
- `experiment_memory.json`
- `risk_policy.json`
- `observability_hub.json`

### manifest responsibility

每个 manifest 应至少声明或考虑以下字段（与当前 `metaharness.sdk.manifest.ComponentManifest` 对齐）：

- `name`
- `version`
- `kind`
- `entry`
- `harness_version`
- `contracts`
- `safety`
- `state_schema_version`
- `deps`
- 可选：`bins` / `env` / `provides` / `requires` / `default_impl` / `enabled`

其中：

- `slots` 与 `capabilities` 不应作为 manifest 顶层自由字段，而应主要落在 `contracts.slots` / `contracts.provides` / `contracts.requires` 中
- 若需要额外 module-level capability 语义，可使用 `provides` / `requires` 顶层字段
---

## 7.14 Graph 文件计划

建议新增目录：

```text
MHE/examples/graphs/
```

当前 MHE 使用 XML 作为 graph 导入与配置格式，但运行时权威模型仍是内部 `PendingConnectionSet / GraphSnapshot`。因此这里的 graph 文件计划应理解为“导入源与示例拓扑”，而不是系统唯一架构真相。

建议新增图：
### 7.14.1 `ai4pde-minimal.xml`

职责：

- 打通最小 happy path

### 7.14.2 `ai4pde-baseline.xml`

职责：

- 在 minimal 基础上加入 reference solver 与 memory

### 7.14.3 `ai4pde-expanded.xml`

职责：

- 在 baseline 基础上加入 policy 与 observability
- 为后续 mutation proposal 做准备

---

## 7.15 Test 文件计划

建议新增：

```text
MHE/tests/test_ai4pde_contracts.py
MHE/tests/test_ai4pde_components.py
MHE/tests/test_ai4pde_graphs.py
MHE/tests/test_ai4pde_minimal_demo.py
MHE/tests/test_ai4pde_validation.py
MHE/tests/test_ai4pde_policy.py
MHE/tests/test_ai4pde_mutation_flow.py
```

### 各测试职责

#### `test_ai4pde_contracts.py`

- schema validity
- serialization / deserialization

#### `test_ai4pde_components.py`

- component declaration correctness
- activation baseline behavior

#### `test_ai4pde_graphs.py`

- graph semantic validation
- slot/port/capability wiring correctness

#### `test_ai4pde_minimal_demo.py`

- end-to-end minimal workflow

#### `test_ai4pde_validation.py`

- residual / BC / IC / conservation / reference compare helpers

#### `test_ai4pde_policy.py`

- risk/budget/reproducibility gate behavior

#### `test_ai4pde_mutation_flow.py`

- AI4PDE mutation proposal path仍然遵守 proposal-only semantics

---

## 7.16 实现顺序建议

### Step 1：稳定基础词汇表

先创建：

- `contracts.py`
- `types.py`
- `slots.py`
- `capabilities.py`

目标：

- 统一领域 vocabulary
- 避免组件边写边改 schema
- 在编码前对齐 `metaharness.sdk.manifest`、`metaharness.sdk.base` 与现有 examples/test patterns

并建议在 Step 1 同步完成一个额外任务：更新 `MHE/pyproject.toml` 的打包配置，确保 `metaharness_ai4pde` 能被安装与测试发现。
### Step 2：最小执行路径组件

先创建：

- `pde_gateway.py`
- `problem_formulator.py`
- `method_router.py`
- `solver_executor.py`
- `physics_validator.py`
- `evidence_manager.py`

目标：

- 打通最小闭环

### Step 3：最小 manifests + graph

创建：

- `examples/manifests/ai4pde/*.json`
- `ai4pde-minimal.xml`

目标：

- 让 AI4PDE graph 能被 MHE 正式 boot + validate + commit
- 确保 manifests 严格遵守当前 SDK schema，graph XML 只承担导入/示例职责
- 优先复用现有 `MHE/examples/manifests/baseline/` 与 `MHE/examples/graphs/` 的粒度与写法
### Step 4：最小测试闭环

创建：

- `test_ai4pde_contracts.py`
- `test_ai4pde_graphs.py`
- `test_ai4pde_minimal_demo.py`

目标：

- 有最基本回归保护

### Step 5：baseline / memory

创建：

- `reference_solver.py`
- `experiment_memory.py`
- `ai4pde-baseline.xml`

目标：

- 建立 reference compare 闭环

### Step 6：治理与观测

创建：

- `risk_policy.py`
- `observability_hub.py`
- `policies/*.py`

目标：

- 把 scientific governance 拉进正式架构

### Step 7：模板与 mutation

创建：

- `templates/*.py`
- `mutations/*.py`
- `benchmarks/runner.py`

目标：

- 让系统从“可运行”升级到“可控演化”

---

## 7.17 最小可交付 cut

如果只做第一个最小可交付版本，建议至少创建：

```text
MHE/src/metaharness_ai4pde/contracts.py
MHE/src/metaharness_ai4pde/types.py
MHE/src/metaharness_ai4pde/slots.py
MHE/src/metaharness_ai4pde/components/pde_gateway.py
MHE/src/metaharness_ai4pde/components/problem_formulator.py
MHE/src/metaharness_ai4pde/components/method_router.py
MHE/src/metaharness_ai4pde/components/solver_executor.py
MHE/src/metaharness_ai4pde/components/physics_validator.py
MHE/src/metaharness_ai4pde/components/evidence_manager.py
MHE/examples/manifests/ai4pde/*.json
MHE/examples/graphs/ai4pde-minimal.xml
MHE/tests/test_ai4pde_minimal_demo.py
```

这套最小 cut 的目标不是“完整 AI4PDE 平台”，而是：

- 证明 domain package 路线可行
- 证明 MHE 可承载 PDE happy path
- 证明 scientific validation + evidence packaging 能接进 runtime

---

## 7.18 最后总结

这份 scaffold plan 的本质是：

- 把 AI4PDE 明确建成一个 `MHE domain package`
- 先稳定契约与组件边界
- 再稳定 graph 与 baseline path
- 再逐步引入治理、模板、自增长

如果严格按这个结构推进，后续将更容易做到：

- 文件职责清晰
- 组件边界清楚
- manifest 与 graph 可维护
- 测试和演化路径可控
