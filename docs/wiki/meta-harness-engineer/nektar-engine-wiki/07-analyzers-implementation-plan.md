# 07. Analyzers Implementation Plan

> 状态：proposed | 对 `06-nektar-next-phase-roadmap.md` 第一阶段（Phase 0: Analyzers）的可执行实施计划

## 7.1 目标

完成 `MHE/src/metaharness_ext/nektar/analyzers.py`，将其从存根升级为 `metaharness_ext.nektar` 的共享分析底座。

本阶段只解决 **结构化解释**，不引入新组件、不改 manifest、不改执行链路。

本阶段完成后，系统应具备三类可复用分析能力：

- solver log 解释
- 派生文件摘要
- reference error 汇总

这些能力将作为下一阶段 `ConvergenceStudyComponent` 的直接输入。

---

## 7.2 范围

## 7.2.1 在范围内

- 在 `contracts.py` 新增三个 Pydantic 返回模型：`SolverLogAnalysis`、`FilterOutputAnalysis`、`ErrorSummary`
- 更新三个函数签名为类型化返回值
- 实现 `parse_solver_log(log_path)` → `SolverLogAnalysis`
- 实现 `parse_filter_outputs(paths=None)` → `FilterOutputAnalysis`
- 实现 `summarize_reference_error(metrics=None)` → `ErrorSummary`
- 新增 `MHE/tests/test_metaharness_nektar_analyzers.py`

## 7.2.2 不在范围内

- 新增 slot / capability / manifest
- 修改 `SolverExecutorComponent` 的运行语义
- 修改 `PostprocessComponent` 的命令构造语义
- 修改 `NektarValidatorComponent` 的 pass/fail 规则
- 新增 e2e 测试
- 引入 `ConvergenceStudyComponent`

---

## 7.3 现状基线

当前 `MHE/src/metaharness_ext/nektar/analyzers.py` 仅包含三个存根：

- `parse_solver_log(log_path: str | Path) -> dict[str, Any]` — 返回 `{"path": ..., "exists": ...}`
- `parse_filter_outputs(paths: list[str] | None = None) -> FilterOutputSummary` — 返回 `FilterOutputSummary(files=paths)`
- `summarize_reference_error(metrics: dict[str, float | str] | None = None) -> dict[str, float | str]` — 返回 metrics 的拷贝

目前它们的返回值不足以支持：

- 面向 agent 的运行解释
- 面向 convergence 的 run-to-run 比较
- 面向 CLI/report 的人类可读摘要

**调用方审计**：经 grep 确认，三个函数在 `analyzers.py` 外无任何调用方。返回类型变更安全。

---

## 7.4 设计决策

## 7.4.1 保持纯函数层

`analyzers.py` 继续作为 library layer，不升级为 component。原因：

- 不需要 runtime 生命周期
- 不需要 manifest 注册
- 更适合作为 executor / postprocess / convergence / CLI 共用工具

## 7.4.2 返回类型为 Pydantic model

三个函数均返回 Pydantic model（而非非结构化 `dict`）。原因：

- 与项目 "typed contracts" 原则一致
- Phase 2 `ConvergenceStudyComponent` 消费 analyzer 输出时有稳定契约
- Pydantic model 提供默认值，对缺失文件和空输入天然友好
- 避免 `dict[str, Any]` 在消费端引入额外的 key-existence 检查

定义位置：`MHE/src/metaharness_ext/nektar/contracts.py`。

## 7.4.3 提取逻辑与 executor 共存

`solver_executor.py` 已有 `_extract_error_norms()` 和 `_extract_step_metrics()`，使用经过 Nektar++ 5.9.0 真实输出验证的正则表达式。

决策：**analyzers 定义自己的私有正则，不共享模块。**

理由：

- executor 的正则只提取数值（运行时写入 artifact），analyzers 的正则还要做分类和统计
- 两组正则的捕获目的不同，强行共享会增加耦合
- 各自有对应测试覆盖，正则分化风险可控
- 避免为两个私有方法引入新的模块级依赖

若后续发现正则严重分化，可在收敛研究阶段再提取共享常量模块。

## 7.4.4 解析逻辑复用现有命名

所有 analyzer 的命名应与现有系统保持一致：

- `l2_error_u`
- `linf_error_u`
- `total_steps`
- `cpu_time`
- `wall_time`
- `incns_velocity_iterations`
- `incns_pressure_iterations`
- `incns_newton_iterations`

避免 analyzer 发明第二套字段名。

## 7.4.5 `parse_filter_outputs()` 返回类型变更

从 `FilterOutputSummary` 变更为 `FilterOutputAnalysis`。原因：

- `FilterOutputSummary` 是运行产物承载（属于 `NektarRunArtifact` 的子字段）
- `FilterOutputAnalysis` 是分析摘要（属于 analyzers 的输出）
- 职责不同，类型不同，避免混淆

经 grep 确认无外部调用方，变更安全。

---

## 7.5 目标返回结构

所有三个 model 定义在 `contracts.py`。

## 7.5.1 `SolverLogAnalysis`

```python
class SolverLogAnalysis(BaseModel):
    path: str
    exists: bool
    warning_count: int = 0
    error_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_steps: int | None = None
    final_time: float | None = None
    cpu_time: float | None = None
    wall_time: float | None = None
    l2_error_keys: list[str] = Field(default_factory=list)
    linf_error_keys: list[str] = Field(default_factory=list)
    has_timeout_marker: bool = False
    incns_metrics: dict[str, float] = Field(default_factory=dict)
```

### 解析来源

复用 `solver_executor.py` 和 `postprocess.py` 中已验证的语义模式（Nektar++ 5.9.0 真实输出验证）：

- `Steps: ... Time: ... CPU Time: ...` → `total_steps`, `final_time`, `cpu_time`
- `Total Computation Time = ...` → `wall_time`
- `L 2 error (variable u) : ...` → `l2_error_keys`
- `L inf error (variable u) : ...` → `linf_error_keys`
- `Pressure system (mapping) converged in ...` → `incns_metrics`
- `Velocity system (mapping) converged in ...` → `incns_metrics`
- `We have done N iteration(s)` → `incns_metrics`

### warning / error 规则

首版采用轻量规则：

- 行内包含 `warning` / `Warning` → warning
- 行内包含 `error` / `Error`，但排除 `L 2 error` / `L inf error` scientific norm lines → error
- 包含 `timed out` → `has_timeout_marker = True`

> **已知限制**：轻量字符串匹配可能产生误报（如路径中包含 "warning"）。首版接受此限制，更复杂的上下文感知规则留待收敛研究阶段按需增强。

## 7.5.2 `FilterOutputAnalysis`

```python
class FilterOutputAnalysis(BaseModel):
    files: list[str] = Field(default_factory=list)
    existing_files: list[str] = Field(default_factory=list)
    missing_files: list[str] = Field(default_factory=list)
    formats: dict[str, str] = Field(default_factory=dict)
    file_sizes: dict[str, int] = Field(default_factory=dict)
    has_vtu: bool = False
    has_dat: bool = False
    has_fld: bool = False
    nonempty_count: int = 0
```

### 格式识别规则

按后缀识别：

- `.vtu` → `vtu`
- `.pvtu` → `pvtu`
- `.dat` → `dat`
- `.fld` → `fld`
- `.chk` → `chk`
- 其他 → `unknown`

## 7.5.3 `ErrorSummary`

```python
class ErrorSummary(BaseModel):
    l2_keys: list[str] = Field(default_factory=list)
    linf_keys: list[str] = Field(default_factory=list)
    max_l2: float | None = None
    max_linf: float | None = None
    primary_variable: str | None = None
    primary_l2: float | None = None
    status: Literal[
        "no_reference_error",
        "reference_error_present",
        "reference_error_within_tolerance",
        "reference_error_exceeds_tolerance",
    ] = "no_reference_error"
    messages: list[str] = Field(default_factory=list)
```

### status 判定逻辑

```text
metrics 为空或无 l2/linf 键
  → no_reference_error

有 error 键但无 tolerance 信息
  → reference_error_present

有 tolerance 且 max_l2 <= tolerance
  → reference_error_within_tolerance

有 tolerance 且 max_l2 > tolerance
  → reference_error_exceeds_tolerance
```

### tolerance 处理

本函数首版不直接依赖 artifact；如需比较 tolerance，允许从 metrics 读取：

- `metrics["error_tolerance"]`

若该键不存在，则只生成 `reference_error_present`，不判断 within/exceeds。

---

## 7.6 实施步骤

## Step 1：新增 Pydantic 返回模型

修改文件：

- `MHE/src/metaharness_ext/nektar/contracts.py`

工作内容：

- 新增 `SolverLogAnalysis`、`FilterOutputAnalysis`、`ErrorSummary` 三个 model
- 确保与现有 model 无命名冲突

完成标志：

- `contracts.py` 可导入三个新 model
- 现有测试仍通过

## Step 2：更新函数签名

修改文件：

- `MHE/src/metaharness_ext/nektar/analyzers.py`

工作内容：

- `parse_solver_log` → 返回 `SolverLogAnalysis`
- `parse_filter_outputs` → 返回 `FilterOutputAnalysis`
- `summarize_reference_error` → 返回 `ErrorSummary`
- 更新 imports

完成标志：

- 三个函数签名固定
- 类型检查通过（mypy 或 pyright）

## Step 3：实现 `parse_solver_log()`

工作内容：

- 读取 log 文件
- 文件不存在时返回 `SolverLogAnalysis(path=..., exists=False)`（所有其他字段为默认值）
- 解析 warning / error / timeout
- 解析 steps / time / wall time
- 解析 L2/Linf error keys
- 解析 IncNS convergence metrics

建议实现方式：

- 在 `analyzers.py` 中定义私有正则常量和辅助函数
- `parse_solver_log()` 调用辅助函数，组装 `SolverLogAnalysis`

完成标志：

- 缺失文件、空文件、普通 solver log、IncNS log 都有稳定输出

## Step 4：实现 `parse_filter_outputs()`

工作内容：

- 遍历输入路径
- 判断存在性
- 读取大小
- 识别格式
- 汇总布尔指标与数量指标

完成标志：

- 对空列表、缺失路径、混合格式路径均输出稳定摘要

## Step 5：实现 `summarize_reference_error()`

工作内容：

- 识别所有 `l2_error_*` / `linf_error_*`
- 忽略无关键
- 选择 `primary_variable`
- 生成 `max_l2` / `max_linf`
- 生成 status / messages

完成标志：

- 空 metrics、单变量、多变量、有无 tolerance 四类输入稳定输出

## Step 6：补测试

新增文件：

- `MHE/tests/test_metaharness_nektar_analyzers.py`

建议测试用例：

### `parse_solver_log()`

- `test_parse_solver_log_returns_missing_state_for_absent_file`
- `test_parse_solver_log_extracts_step_and_time_metrics`
- `test_parse_solver_log_extracts_warning_and_error_lines`
- `test_parse_solver_log_ignores_scientific_error_norm_lines_as_runtime_errors`
- `test_parse_solver_log_extracts_incns_convergence_metrics`
- `test_parse_solver_log_detects_timeout_marker`

### `parse_filter_outputs()`

- `test_parse_filter_outputs_summarizes_existing_and_missing_files`
- `test_parse_filter_outputs_detects_formats_and_sizes`
- `test_parse_filter_outputs_handles_empty_input`

### `summarize_reference_error()`

- `test_summarize_reference_error_returns_no_reference_error_for_empty_metrics`
- `test_summarize_reference_error_extracts_l2_and_linf_extrema`
- `test_summarize_reference_error_marks_within_tolerance_when_available`
- `test_summarize_reference_error_marks_exceeds_tolerance_when_available`

## Step 7：运行定向验证

建议命令：

- `pytest MHE/tests/test_metaharness_nektar_analyzers.py`
- `pytest`（全量回归）
- `ruff check`
- 如改动影响到 validator 约定，可补跑：
  - `pytest MHE/tests/test_metaharness_nektar_postprocess.py`

---

## 7.7 文件级变更清单

### 必改文件

- `MHE/src/metaharness_ext/nektar/contracts.py`（新增 3 个 Pydantic model）
- `MHE/src/metaharness_ext/nektar/analyzers.py`（签名更新 + 实现填充）
- `MHE/tests/test_metaharness_nektar_analyzers.py`（新增）

### 可能修改文件

- `MHE/src/metaharness_ext/nektar/__init__.py`（导出新 model，若需要）

### 本阶段不应修改的文件

- `MHE/src/metaharness_ext/nektar/solver_executor.py`
- `MHE/src/metaharness_ext/nektar/postprocess.py`
- `MHE/src/metaharness_ext/nektar/validator.py`
- `MHE/src/metaharness_ext/nektar/session_compiler.py`
- `MHE/src/metaharness_ext/nektar/xml_renderer.py`

---

## 7.8 风险与决策点

## 决策点 1：返回类型

**已决定**：返回 Pydantic model，不返回 `dict[str, Any]`。

理由：

- 与项目 typed-contracts 原则一致
- 消费方（convergence）有稳定契约
- Pydantic 默认值处理缺失输入更优雅

## 决策点 2：提取逻辑归属

**已决定**：analyzers 定义自己的私有正则，不抽取共享模块。

理由：

- executor 和 analyzers 的捕获目的不同
- 各自有测试覆盖
- 避免过早抽象

## 决策点 3：warning / error 规则的严格程度

**已决定**：首版保持轻量字符串规则。

理由：

- 现有目标是稳定摘要，不是构建完整日志分类器
- 更复杂的分类规则可在 convergence/report 层需求明确后再增强

---

## 7.9 完成定义

当以下条件全部满足时，本阶段可以视为完成：

- `contracts.py` 包含 `SolverLogAnalysis`、`FilterOutputAnalysis`、`ErrorSummary` 三个 model
- `analyzers.py` 三个函数全部不再是存根，返回类型化 model
- 新增 `test_metaharness_nektar_analyzers.py` 且定向测试通过
- 缺失文件、空输入、正常输入、IncNS 特殊日志均被覆盖
- 不引入新的 runtime / manifest / slot 复杂度
- 全量测试套件零回归

---

## 7.10 下一步衔接

本阶段完成后，下一阶段应直接进入：

- `ConvergenceStudyComponent` 的 contracts 与 component 实现

届时可以直接消费：

- `parse_solver_log()` → `SolverLogAnalysis`（运行解释）
- `parse_filter_outputs()` → `FilterOutputAnalysis`（派生文件摘要）
- `summarize_reference_error()` → `ErrorSummary`（误差摘要）

这样能保证 convergence 层从第一天起就不是"只会跑多次 solver"，而是"会解释多次 solver 的结果"。
