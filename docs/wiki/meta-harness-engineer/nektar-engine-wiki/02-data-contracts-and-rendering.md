# 02. Data Contracts and Rendering

## 2.1 设计原则

`metaharness_ext.nektar` 的实现高度依赖 Pydantic contract。当前包的运行稳定性，很大程度上来自四类对象的清晰分层：

1. `NektarProblemSpec`：问题描述
2. `NektarSessionPlan`：可执行计划
3. `NektarRunArtifact`：运行产物
4. `NektarValidationReport`：结果判断

这些模型定义在 `MHE/src/metaharness_ext/nektar/contracts.py:20` 之后。

---

## 2.2 类型枚举

`MHE/src/metaharness_ext/nektar/types.py:6` 定义了当前实现的枚举边界。

### 2.2.1 Solver family

- `NektarSolverFamily.ADR`
- `NektarSolverFamily.INCNS`

### 2.2.2 方程类型

ADR 支持：

- `Laplace`
- `Poisson`
- `Helmholtz`
- `SteadyAdvectionDiffusion`
- `UnsteadyAdvectionDiffusion`
- `UnsteadyReactionDiffusion`

IncNS 支持：

- `SteadyStokes`
- `UnsteadyStokes`
- `UnsteadyNavierStokes`

### 2.2.3 其他关键枚举

- `NektarProjection`：`Continuous` / `DisContinuous`
- `NektarIncnsSolverType`：当前默认 `VelocityCorrectionScheme`
- `NektarBoundaryConditionType`：`D / N / R / P`
- `NektarGeometryMode`：`2D / 2D-homogeneous-1D / 3D`

这些类型直接约束 compiler 和 renderer 的允许输入集合。

---

## 2.3 `NektarProblemSpec`

定义在 `MHE/src/metaharness_ext/nektar/contracts.py:70`。

它是最接近“用户任务/上游规划结果”的对象，包含：

- 任务标识：`task_id`、`title`
- 求解选择：`solver_family`、`equation_type`
- 维度信息：`dimension`、`space_dimension`
- 变量与参数：`variables`、`materials`、`parameters`
- 域信息：`domain`
- 条件与约束：`initial_conditions`、`boundary_conditions`
- 外源项与参考：`forcing`、`reference`
- 后处理与高层目标：`postprocess_plan`、`objectives`、`constraints`

### 2.3.1 关键校验

`validate_equation_type()` 在 `MHE/src/metaharness_ext/nektar/contracts.py:89` 保证：

- `ADR` family 只能绑定 `NektarAdrEqType`
- `INCNS` family 只能绑定 `NektarIncnsEqType`

这一步把错误尽量前移到 problem -> plan 阶段之前。

---

## 2.4 `NektarSessionPlan`

定义在 `MHE/src/metaharness_ext/nektar/contracts.py:122`。

它是运行时最核心的对象：已经不再描述“想求什么”，而是在描述“怎么渲染、怎么执行、期待哪些输出”。

主要字段包括：

- 求解信息：`solver_family`、`solver_binary`、`equation_type`、`projection`、`solver_type`
- mesh/geometry：`mesh`
- 场与离散：`variables`、`expansions`
- XML 条件区：`solver_info`、`parameters`、`time_integration`
- 边界：`boundary_regions`、`boundary_conditions`
- 函数与 forcing：`functions`、`forcing`
- 过滤器与输出：`filters`、`expected_outputs`
- 验证与渲染：`validation_targets`、`render_geometry_inline`、`session_file_name`
- 后处理：`postprocess_plan`

### 2.4.1 `global_system_solution_info`

虽然 plan 中保留了 `global_system_solution_info` 字段，但当前 renderer 明确拒绝它，见 `MHE/src/metaharness_ext/nektar/xml_renderer.py:37`。这说明该字段目前更像未来扩展预留，而非已落地 surface。

---

## 2.5 运行期产物：`FilterOutputSummary` 与 `NektarRunArtifact`

### 2.5.1 `FilterOutputSummary`

定义在 `MHE/src/metaharness_ext/nektar/contracts.py:161`，用于汇总后处理与指标层数据：

- `files`
- `checkpoint_files`
- `history_point_files`
- `fieldconvert_intermediates`
- `error_norms`
- `metrics`
- `metadata`

这里的 `error_norms` 与 `metrics` 是 validator 的主要数据来源。

### 2.5.2 `NektarRunArtifact`

定义在 `MHE/src/metaharness_ext/nektar/contracts.py:171`。

它是 solver executor 与 postprocess 之间的稳定桥梁，保存：

- session/mesh/field/log/derived 文件路径
- `filter_output`
- `result_summary`
- `postprocess_plan`
- `status`

设计上，artifact 既要能承载“solver 刚跑完”的状态，也要能承载“后处理已完成”的状态，因此 `PostprocessComponent` 会对它做 deep copy 后更新。

---

## 2.6 `NektarValidationReport`

定义在 `MHE/src/metaharness_ext/nektar/contracts.py:187`。

它对外提供最简洁的结果摘要：

- `passed`
- `solver_exited_cleanly`
- `field_files_exist`
- `error_vs_reference`
- `messages`
- `metrics`

这类对象适合挂在更上层的 evidence / orchestration / CLI 输出里，而不需要暴露所有底层日志细节。

---

## 2.7 XML 渲染模型

渲染逻辑位于 `MHE/src/metaharness_ext/nektar/xml_renderer.py:49` 之后。

### 2.7.1 受支持 section

当前 renderer 能输出的核心结构包括：

- `GEOMETRY`
- `EXPANSIONS`
- `FORCING`
- `CONDITIONS`
  - `PARAMETERS`
  - `TIMEINTEGRATIONSCHEME`
  - `SOLVERINFO`
  - `VARIABLES`
  - `BOUNDARYREGIONS`
  - `BOUNDARYCONDITIONS`
  - `FUNCTION`
- `FILTERS`

### 2.7.2 渲染顺序

`render_session_element()` 在 `MHE/src/metaharness_ext/nektar/xml_renderer.py:236` 固定了节点顺序：

1. `GEOMETRY`（仅当 inline）
2. `EXPANSIONS`
3. `FORCING`（可选）
4. `CONDITIONS`
5. `FILTERS`（可选）

固定顺序的好处是：

- 便于 snapshot / string-level 测试
- 降低 diff 抖动
- 强迫 plan 对 XML 结构有稳定映射

### 2.7.3 boundary 渲染

渲染器使用：

- `_render_boundary_regions()` 输出 `B[ID] -> composite`
- `_render_boundary_conditions()` 按 region 分组输出 `REGION REF`
- `_render_bc_entry()` 把 `D/N/R/P` 写成对应 Nektar 标签

特别地：Robin 边界条件通过 `PRIMCOEFF` 写出，前提是 contract 校验已经保证存在该值，见 `MHE/src/metaharness_ext/nektar/contracts.py:28`。

---

## 2.8 compiler 与 renderer 的接口契约

这两个模块是强耦合但分职责的：

- compiler 负责生成“合法且可渲染”的 plan
- renderer 负责拒绝超出当前支持面的 plan

这种设计比“renderer 默默兼容一切”更安全，因为它能清楚表达当前实现边界。

例如：

- `num_modes` 必须是整数，见 `MHE/src/metaharness_ext/nektar/xml_renderer.py:114`
- external mesh 模式必须有 `mesh.source_path`，见 `MHE/src/metaharness_ext/nektar/xml_renderer.py:39`
- 缺少 boundary/variables/expansions 会直接报错，见 `MHE/src/metaharness_ext/nektar/xml_renderer.py:41`

---

## 2.9 当前 contract 设计的工程含义

从当前实现可以看出几个明确取向：

### 2.9.1 优先约束，而不是泛化

当前 contract 没有试图覆盖所有 Nektar XML 结构，而是只覆盖已经被 compiler / executor / tests 真正使用的字段。

### 2.9.2 plan 是系统边界

一旦进入 `NektarSessionPlan`，后续 renderer / executor / postprocess 都不该重新理解用户意图，而只消费计划结果。

### 2.9.3 artifact 是运行边界

一旦进入 `NektarRunArtifact`，后续 validator 不应该重建 solver 过程，而是只消费证据和指标。

这让不同阶段可以独立测试，也让以后接入新 compiler 或新 validator 更容易。