# Nektar Extension for MHE Wiki

> 版本：v1.0 | 最后更新：2026-04-24

本目录只讨论 **如何在 `MHE` 中设计与理解 `metaharness_ext.nektar`**。

它聚焦于扩展层的稳定边界：architecture、contracts、execution semantics、postprocess / validation surface，以及 testing / extension invariants。

本目录**不再承载**以下内容作为主线：

- 分阶段实施细节
- 里程碑与 roadmap 叙述
- 文件级脚手架清单
- 当前实现状态盘点与推进记录
- 与设计主线混写的 blueprint / implementation plan 内容

这些内容统一下沉到 `blueprint/` 目录中的正式文档。

---

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-Architecture and Flow](01-architecture-and-flow.md) | `gateway -> compiler -> executor -> postprocess -> validator` 的组件链、槽位与能力边界 | 所有人 |
| [02-Data Contracts and Rendering](02-data-contracts-and-rendering.md) | `ProblemSpec / SessionPlan / RunArtifact / ValidationReport` 与 XML rendering surface | 核心开发 / compiler 维护者 |
| [03-Execution, Postprocess and Validation](03-execution-postprocess-and-validation.md) | solver execution、`FieldConvert` 后处理、error / convergence evidence 与 validator 语义 | 运行时工程师 / 平台工程师 |
| [04-Testing and Extension Guide](04-testing-and-extension-guide.md) | 测试分层、review 边界、扩展入口与设计不变量 | reviewer / 测试维护者 |

---

## 术语约定

- prose 中使用 **solver family**；代码字段写作 `solver_family`
- prose 中使用 **session plan**；代码类型写作 `NektarSessionPlan`
- prose 中使用 **run artifact**；代码类型写作 `NektarRunArtifact`
- **postprocess** 指 solver 运行后的派生处理层；**validation** 指消费证据并给出结论的判定层
- **evidence** 指日志、字段文件、误差范数、收敛指标与派生文件的统一证据面

---

## 设计原则

`metaharness_ext.nektar` 的当前版本应被理解为：

- **solver-specific** 的 typed extension
- 以 **Pydantic contracts** 为稳定控制面
- 以 **session XML + solver binary** 为执行面
- 以 **artifact / metrics / logs** 为证据面
- 以 **postprocess + validator** 为结果判定面

因此本目录的写作重点是 **设计边界与工程语义**，而不是交付顺序或实施脚手架。

---

## 与 `blueprint/` 的分工

Nektar 扩展的正式实施材料位于 `MHE/docs/wiki/meta-harness-engineer/blueprint/`：

- `02-nektar-next-phase-blueprint.md`：正式设计蓝图
- `02-nektar-next-phase-roadmap.md`：阶段路线与里程碑
- `02-nektar-analyzers-implementation-plan.md`：分析器实现计划与验收面

分工原则如下：

- **本 wiki**：回答“这个扩展当前应如何被理解、设计与扩展”
- **blueprint**：回答“下一阶段正式设计主张是什么”
- **roadmap**：回答“按什么顺序推进”
- **implementation plan**：回答“当前阶段具体做什么、怎么验收”

---

## 定位

`metaharness_ext.nektar` 不是通用的 Nektar++ Python SDK，也不是完整的 case authoring 系统；它是 `MetaHarness` 的一个 **solver-specific extension package**，目标是把受控的 Nektar++ 工作流纳入 `HarnessComponent` / manifest / slot 体系。

它当前实现了一个受限但完整的 execution slice：

```text
NektarGateway
  -> SessionCompiler
    -> XML Renderer
      -> SolverExecutor
        -> Postprocess(FieldConvert)
          -> Validator
```

这条链路强调：

- **契约优先**：通过 Pydantic contracts 固定输入输出
- **结果可审计**：session、日志、字段文件、误差指标、派生文件全部落盘
- **演进受限**：当前只覆盖 `ADR` / `IncNS` 两个 solver family 和有限 XML surface
- **证据驱动**：validator 直接消费 solver / postprocess 提取出的误差与收敛指标

---

## 与其他 wiki 的关系

- 与 [meta-harness-wiki](../meta-harness-wiki/README.md) 的关系：后者描述通用 `MetaHarness SDK / Runtime / ConnectionEngine`；本目录描述该 SDK 上的 `Nektar++` 域扩展实现。
- 与 [ai4pde-agent-wiki](../ai4pde-agent-wiki/README.md) 的关系：后者描述面向 PDE 科学智能体的上层 runtime；本目录描述其中一个可落地的 classical solver backend。

---

## 推荐阅读顺序

### 想先理解扩展边界

先看：[01-Architecture and Flow](01-architecture-and-flow.md) → [02-Data Contracts and Rendering](02-data-contracts-and-rendering.md)

### 想理解运行与证据语义

先看：[03-Execution, Postprocess and Validation](03-execution-postprocess-and-validation.md)

### 想看测试与扩展边界

先看：[04-Testing and Extension Guide](04-testing-and-extension-guide.md)

### 想看下一阶段实施材料

转到：`blueprint/02-nektar-next-phase-blueprint.md`、`blueprint/02-nektar-next-phase-roadmap.md`、`blueprint/02-nektar-analyzers-implementation-plan.md`

---

## 不在本目录展开的内容

以下内容不再作为本目录主线：

- Nektar++ 软件本体的完整背景综述
- 下一阶段 blueprint / roadmap 的细化推进叙述
- analyzers 实施拆解与当前推进记录
- HPC 调度、分布式编排与大规模运行管理
- 全量 XML schema 或通用 case authoring 教程

本目录只保留 **设计与维护 `metaharness_ext.nektar` 所必需** 的内容。

---

## 当前范围边界

截至当前实现，`metaharness_ext.nektar` 明确支持：

- `ADR` 与 `IncNS` 两个 solver family
- 由 `SessionCompilerComponent` 生成 `NektarSessionPlan`
- 由 `xml_renderer` 渲染受限 Nektar session XML
- 通过标准库 `subprocess` 调用真实 `ADRSolver` / `IncNavierStokesSolver`
- 通过 `FieldConvert` 执行格式转换、`-e` 误差评估与 `-m <module>` 模块化后处理
- 通过 validator 基于退出码、输出文件、L2 误差与 IncNS 收敛指标做结果判定

当前未覆盖或刻意限制：

- 任意 Nektar solver family 的自动扩展
- 通用 mesh generation pipeline
- 完整 `GLOBALSYSSOLNINFO` 支持
- 任意复杂的 session XML round-trip 编辑
- 复杂调度、HPC 作业编排、分布式运行管理

---

## 附录：Nektar++ 与 Meta-Harness 的设计契合性分析

从 Nektar++ 的自身设计出发，可以解释为什么它天然适合被纳入 Meta-Harness 的组件化、声明式、 staged-lifecycle 体系。

### 1. Nektar++ 是"配置驱动"的求解器

Nektar++ 的核心运行模式不是 API 调用链，而是：

```text
session.xml + mesh -> SolverBinary -> field files + log
```

这意味着：
- **输入是声明式的**：session XML 本身就是一种"manifest + contract"的混合体，它声明了方程、边界条件、展开基、时间积分参数等。
- **输出是结构化的**：solver 总是生成 `.fld` / `.chk` 字段文件和文本日志，后处理工具（`FieldConvert`）可以进一步消费这些产物。

这种"声明输入 → 执行 → 结构化输出"的模式，与 Meta-Harness 的 `declare_interface() -> activate() -> emit()` 生命周期高度同构。

### 2. Nektar++ 的模块化结构与 HarnessComponent 的一一对应

Nektar++ 的内部架构本身就是分层的：

| Nektar++ 层级 | Meta-Harness 对应组件 | 对应关系 |
|---|---|---|
| `SpatialDomains` / `MeshGraph` | `SessionCompilerComponent` + `xml_renderer` | 几何/网格描述被编译进 session XML |
| `MultiRegions` / `ExpList` | `NektarExpansionSpec` + `NektarSessionPlan` | 展开基、阶数、复合域的声明 |
| `SolverUtils` / 具体 Solver | `SolverExecutorComponent` | 按 solver family 选择二进制并执行 |
| `FieldConvert` | `PostprocessComponent` | 后处理、格式转换、误差评估 |
| `LibUtilities` / 日志与 I/O | `analyzers.py` + `NektarValidatorComponent` | 从日志和文件中提取结构化指标 |

这意味着 Nektar++ 的每个主要子系统，都可以自然地映射为一个 `HarnessComponent`，而不需要拆解或封装 Nektar++ 的内部对象。

### 3. Nektar++ 的"求解族"概念与 capability 系统匹配

Nektar++ 不是单一的求解器，而是一个**求解器框架**。不同的 PDE 类型由不同的 solver binary 处理：

- `ADRSolver` — 对流-扩散-反应
- `IncNavierStokesSolver` — 不可压 Navier-Stokes
- `ShallowWaterSolver` — 浅水方程
- `PulseWaveSolver` — 脉搏波
- ……

这与 Meta-Harness 的 `capability` 系统天然对应：
- `nektar.solver.adr` → `ADRSolver`
- `nektar.solver.incns` → `IncNavierStokesSolver`

通过 capability 的 provide/require 机制，Meta-Harness 可以在图装配阶段就判断：一个声明了 `nektar.solver.adr` 的组件图，是否具备执行该 solver 的全部前置条件（如 mesh、expansion、BC 声明）。

### 4. Nektar++ 的"session 文件即契约"与 staged lifecycle 契合

Nektar++ 的 session XML 在运行前就被完整解析。这与 Meta-Harness 的 staged lifecycle 完美匹配：

| Meta-Harness 阶段 | Nektar++ 对应动作 |
|---|---|
| `declare_interface()` | 声明 `NektarProblemSpec` 的字段和约束 |
| `VALIDATED_STATIC` | Pydantic contract 校验（方程类型与 solver family 匹配、BC 完整性、几何维度一致性） |
| `ASSEMBLED` | `SessionCompilerComponent` 把 problem spec 编译成 `NektarSessionPlan` |
| `VALIDATED_DYNAMIC` | XML 渲染后的结构校验、文件存在性检查、二进制可用性检查 |
| `ACTIVATED` | 调用 solver binary 执行 |
| `COMMITTED` | 结果文件（`.fld`、`.chk`、日志）落盘并进入 validator |

Nektar++ 的"先编译 session，再执行 solver"流程，天然就是 staged 的。

### 5. Nektar++ 的确定性输出便于观测与回滚

Nektar++ 的执行结果是确定性的（给定同样的 session XML 和 mesh，输出是重现的）。这意味着：

- **Checkpoint 有意义**：`HotSwapOrchestrator` 可以在替换组件前捕获完整的 `.fld` / `.chk` / 日志状态。
- **Migration adapter 可测试**：状态迁移（如从 `num_modes=4` 到 `num_modes=6`）可以通过 `transform_state()` 或 registered adapter 显式建模。
- **Observation window 可量化**：swap 后的稳定性可以通过误差范数、收敛步数、CPU 时间等指标直接判断。

### 6. Nektar++ 的"参数扫描"需求与 optimizer 方向一致

科学计算中最常见的研究模式之一就是参数扫描：

- 改变 `NUMMODES` 观察收敛阶
- 改变时间步长观察稳定性
- 改变网格分辨率观察误差下降

这正好是 Meta-Harness Optimizer 的 sweet spot：
- `NektarMutationAxis` 定义扫描维度
- `ConvergenceStudyComponent` 执行扫描循环
- `ConvergenceStudyReport` 提供 fitness signal（`observed_order`、`converged`、`drop_ratios`）
- Optimizer 可以基于这些信号提出下一轮 mutation

### 7. Nektar++ 的"多文件覆盖"机制与 Template Library 的天然对应

Nektar++ 的 session XML 支持"分段文件 + 后者覆盖前者"（`ch03-XML-guide.md:14-16`）。这与 Meta-Harness 的 `Template Library` 形成直接映射：

- **Base template** → 基础 session XML（通用几何、默认参数）
- **Instance overlay** → 问题特定的覆盖文件（方程类型、边界条件）
- **Experiment overlay** → 实验参数覆盖（`NUMMODES`、时间步长、迭代次数）

这种"声明式叠加"正是 Meta-Harness 模板系统的理想底层机制，Agent 不需要从零生成完整 XML，而是基于模板做约束下的变异。

### 8. "约束优于自由生成"的安全哲学契合

Nektar++ 的设计让 Agent **不需要直接修改 C++ 内核**：

> "Nektar++ 本身已经把'求解器行为'大量暴露在 XML DSL 里，而不是全靠 C++ 改码。"

这与 Meta-Harness 的 **安全治理体系** 高度一致：
- Meta-Harness 强调从"无约束代码搜索"转向"约束 XML/模板搜索"
- Nektar++ 的 XML 边界就是天然的 **Policy Guard** —— Agent 只能在声明式 DSL 内操作，无法随意突破到编译器/内存层面
- 降低了 Agent 的决策空间，提升了 tractability 和安全性

### 9. FieldConvert / Filters 提供"一等可观测性"

Nektar++ 的 `<FILTERS>` 让"运行后自动可视化"成为**一等能力**，而不是事后脚本。Filters（如 `HistoryPoints`、`MeanValue`、`ReynoldsStresses`）在求解**过程中**就持续输出结构化数据，这与 Meta-Harness 的 **三层可观测性**（L1 telemetry / L2 lifecycle / L3 scientific evidence）天然对应：

- Filter 输出 → L2 lifecycle 事件
- FieldConvert `-e` 误差 → L3 scientific evidence
- 日志中的残差历史 → L1 telemetry

### 10. Spectral/hp Element 方法与 Self-Growth 的数学同构

Nektar++ 基于 **spectral/hp element method**，其核心的 h-refinement 和 p-refinement 与 Meta-Harness 的 **四层自我成长策略** 形成深刻类比：

| Nektar++ 机制 | Meta-Harness Self-Growth | 对应关系 |
|---|---|---|
| **h-refinement**（网格细化） | 参数级变异（`NUMMODES`、时间步长、网格分辨率） | 调整"空间"粒度 |
| **p-refinement**（阶数提升） | 模板级变异（离散格式、投影类型） | 调整"精度"阶数 |
| **solver family 扩展**（新增方程支持） | 代码级合成（新 BC、新 forcing、新 solver scaffold） | 增加"维度" |
| **hp-adaptive**（自适应 h/p） | 自适应优化器（基于收敛信号的动态调整） | 闭环自适应 |

Meta-Harness 的设计灵感本就来自 PDE 求解器的"迭代收敛"思想，而 Nektar++ 是这一隐喻的**完美物理载体**。

### 11. NekMesh 补齐前处理，形成完整 Agent 闭环

完整的 Agent 可控流水线应是：

```text
NekMesh (preprocess) → SessionCompiler (compile) → SolverExecutor (activate)
    → FieldConvert (postprocess) → Validator (evaluate) → Optimizer (mutate)
```

Nektar++ 生态提供了 **pre/solve/post** 的完整工具链，与 Meta-Harness 的 `declare_interface() -> activate() -> emit()` 生命周期形成端到端映射。

### 12. 确定性执行与 HotSwap / Migration Adapter 的工程可行性

Nektar++ 的**确定性执行**是 HotSwap 和 Migration Adapter 的**工程前提**：

> "Nektar++ 的执行结果是确定性的（给定同样的 session XML 和 mesh，输出是重现的）。"

这使得以下 Meta-Harness 高级特性在 Nektar++ 场景下**真正可落地**：
- **Blue-green 部署**：同一问题跑两个 graph version，对比 `.fld` 的 L2 差异
- **Migration adapter**：`num_modes=4 → 6` 的状态迁移可以通过 `transform_state()`（插值到更高阶展开基）显式建模
- **Counterfactual replay**：完整保存 session + mesh + 参数，可在任意时刻精确重放
- **Merkle 审计链**：session XML 的哈希可作为计算溯源的锚点

### 13. Session XML 即"Manifest + Contract"

session XML 本身就是一种"manifest + contract"的混合体：

- 它**声明**了方程、边界条件、展开基、时间积分参数等（manifest）
- 它在运行前就被完整解析，任何不匹配都会在启动时 fail-fast（contract）

这与 Meta-Harness 的 `declare_interface()` + `VALIDATED_STATIC` 阶段完全同构 —— 组件在激活前就必须通过静态契约校验。

### 14. 结论

Nektar++ 的设计哲学（声明式配置、模块化 solver 族、结构化输出、确定性重放、多文件覆盖、spectral/hp 自适应）与 Meta-Harness 的设计哲学（声明式组件、capability 匹配、staged lifecycle、状态迁移、观测回滚、模板驱动、约束搜索）在结构上高度同构。

这不是"把 Nektar++ 硬塞进 Meta-Harness"，而是"Nektar++ 的执行模型本身就是 Meta-Harness 想要的那种**受控、可声明、可观测、可回滚的计算单元**"。

> "Nektar++ 的'先编译 session，再执行 solver'流程，天然就是 staged 的。"
