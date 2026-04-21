# 01. Architecture and Flow

## 1.1 目标与分层

`metaharness_ext.nektar` 的核心目标，是把 Nektar++ 求解流程包装成一组可声明、可组合、可验证的 `HarnessComponent`。

从实现上看，它不是一个单体 orchestrator，而是一个按槽位拆开的线性 runtime：

```text
nektar_gateway.primary
  -> session_compiler.primary
    -> solver_executor.primary
      -> postprocess.primary
        -> validator.primary
```

其中每一层都做一件明确的事：

- `NektarGatewayComponent`：发出最小 `NektarProblemSpec`
- `SessionCompilerComponent`：把 problem 编译成可执行 `NektarSessionPlan`
- `xml_renderer`：把 plan 渲染成受限 Nektar session XML
- `SolverExecutorComponent`：执行真实 solver 并收集原始产物
- `PostprocessComponent`：执行 `FieldConvert` 以及误差/收敛提取
- `NektarValidatorComponent`：把执行结果压缩成 pass/fail + metrics + messages

---

## 1.2 槽位与能力

### 1.2.1 稳定槽位

定义在 `MHE/src/metaharness_ext/nektar/slots.py:3`：

| Slot | 组件 | 说明 |
|---|---|---|
| `nektar_gateway.primary` | `NektarGatewayComponent` | 任务入口 |
| `session_compiler.primary` | `SessionCompilerComponent` | plan 编译 |
| `solver_executor.primary` | `SolverExecutorComponent` | 求解执行 |
| `postprocess.primary` | `PostprocessComponent` | 后处理 |
| `validator.primary` | `NektarValidatorComponent` | 结果验证 |

当前唯一的 protected slot 是 `validator.primary`，定义在 `MHE/src/metaharness_ext/nektar/slots.py:9`。

### 1.2.2 能力标签

定义在 `MHE/src/metaharness_ext/nektar/capabilities.py:3`：

- `nektar.compile.case`
- `nektar.mesh.prepare`
- `nektar.solver.adr`
- `nektar.solver.incns`
- `nektar.postprocess.fieldconvert`
- `nektar.validation.check`

这些 capability 主要用于 manifest / registry / graph 装配阶段表达组件能力边界，而不是运行时动态策略本身。

---

## 1.3 模块职责

## 1.3.1 `NektarGatewayComponent`

入口很薄，见 `MHE/src/metaharness_ext/nektar/nektar_gateway.py:12`。

它的职责非常克制：

- 生成最小 `NektarProblemSpec`
- 设定 `task_id`、`title`、`solver_family`
- 默认给出一个二维 `ADR` 风格的起始问题

这意味着 gateway 当前更像 “demo/task seed emitter”，而不是复杂的 case parser。

## 1.3.2 `SessionCompilerComponent`

`SessionCompilerComponent` 是当前包里最关键的 planner，实现在 `MHE/src/metaharness_ext/nektar/session_compiler.py:209`。

它负责把领域层的 `NektarProblemSpec` 压缩成执行层的 `NektarSessionPlan`，主要工作包括：

- 根据 `solver_family` 选择 solver binary
  - `ADR -> ADRSolver`
  - `INCNS -> IncNavierStokesSolver`
- 推导默认 `equation_type`
- 推导默认 `time_integration`
- 决定变量表：`ADR -> ["u"]`，`IncNS -> ["u", "v", "p"]`
- 构造 mesh / geometry 表达
- 生成 boundary regions 与 boundary conditions
- 整理初值、参考解、forcing 到 `functions`
- 生成 expansion、parameters、solver_info
- 默认注入 `postprocess_plan=[{"type": "fieldconvert", "output": "solution.vtu"}]`

它同时支持两种几何输入模式：

1. **inline geometry**：若未提供 mesh path，则自动生成默认二维四边形几何
2. **external mesh overlay**：若存在 `domain.mesh_path` 或 `domain.source_path`，则不内联几何，交由外部 mesh XML 驱动

## 1.3.3 `xml_renderer`

渲染器定义在 `MHE/src/metaharness_ext/nektar/xml_renderer.py:236`。它把 `NektarSessionPlan` 渲染为 `NEKTAR` XML 文本。

当前 renderer 的设计原则是：

- 只支持当前 plan surface 需要的 XML 子集
- 通过 `_validate_renderable()` 明确拒绝超出范围的输入
- 固定输出顺序，降低回归测试波动

重要约束包括：

- 仅支持 `ADR` / `INCNS`
- 不支持 `global_system_solution_info`
- external mesh 模式下必须存在 `mesh.source_path`
- 必须有 `boundary_regions`、`variables`、`expansions`

## 1.3.4 `SolverExecutorComponent`

执行器在 `MHE/src/metaharness_ext/nektar/solver_executor.py:23`，负责把 plan 变成真实运行结果。

它的职责包括：

- 校验 equation type 与 solver family 是否匹配
- 依赖 `runtime.storage_path` 创建运行目录
- 校验 `task_id`，阻止路径穿越
- 写出 `session.xml`
- 解析 solver binary 路径
- 构造 solver command
- 用 `subprocess.run()` 执行真实 solver
- 捕获 stdout / stderr / combined log
- 发现 `.fld` / `.chk` 输出
- 从 solver 输出中提取误差范数与步进指标
- 组装 `NektarRunArtifact`

## 1.3.5 `PostprocessComponent`

后处理组件定义在 `MHE/src/metaharness_ext/nektar/postprocess.py:17`。

它并不直接重跑 solver，而是消费 `NektarRunArtifact`：

- 优先使用 `.fld` 作为 `FieldConvert` 输入
- 若缺少 `.fld`，回退到最新 `.chk`
- 支持普通转换：`FieldConvert input output`
- 支持误差评估：`FieldConvert -e session input output`
- 支持模块式调用：`FieldConvert -m <module> ...`
- 维护 `derived_files`、`fieldconvert_intermediates`
- 从 `FieldConvert` 输出继续提取误差范数
- 对 `IncNS` solver log 提取收敛/迭代指标

## 1.3.6 `NektarValidatorComponent`

验证器在 `MHE/src/metaharness_ext/nektar/validator.py:11`。

它不做复杂数值分析，而是把已有证据归并成一个统一报告：

- `solver_exited_cleanly`
- `field_files_exist`
- `error_vs_reference`
- `messages`
- `metrics`

其中 `passed` 的核心判据是：

```text
solver_exited_cleanly
and field_files_exist
and error_vs_reference is not False
```

也就是说：

- 没有误差范数时，`error_vs_reference` 可以是 `None`
- 只有当误差显式超阈值时，才强制失败

---

## 1.4 端到端执行链路

当前实现的标准链路如下：

### 第一步：生成 problem

由 `NektarGatewayComponent.issue_task()` 或上游系统构造 `NektarProblemSpec`。

### 第二步：编译 plan

`SessionCompilerComponent.build_plan()` 生成 `NektarSessionPlan`，补齐默认值、几何、变量、边界、参数和默认 postprocess 计划。

### 第三步：渲染 XML

`render_session_xml()` / `write_session_xml()` 把 plan 落成 `session.xml`。

### 第四步：执行 solver

`SolverExecutorComponent.execute_plan()`：

- 解析 binary
- 执行 solver
- 记录日志
- 发现 `.fld` / `.chk`
- 提取误差与时间指标

### 第五步：执行后处理

`PostprocessComponent.run_postprocess()`：

- 读取 `postprocess_plan`
- 调用 `FieldConvert`
- 收集 `.vtu` / `.dat` / `.pvtu`
- 提取 `-e` 误差或 IncNS 收敛指标

### 第六步：生成验证报告

`NektarValidatorComponent.validate_run()` 生成 `NektarValidationReport`。

---

## 1.5 当前架构边界

从现有实现看，这个包更接近一个 **可测试、可扩展、受限的 execution slice**，而不是完整 Nektar 平台。它当前强调：

- 运行链完整可落地
- 关键环节都有契约与测试保护
- 真实 solver / `FieldConvert` 可以在本地环境完成 e2e 验证

但还没有覆盖：

- 更复杂的 mesh 预处理工具链
- 更广泛 solver family
- 集群/HPC 调度
- 丰富的 XML schema round-trip 支持
- 高层 case authoring / case parser / template instantiation 体系

因此，阅读这个包时，应把它理解为 `MetaHarness` 中 classical solver backend 的第一阶段工程化实现。