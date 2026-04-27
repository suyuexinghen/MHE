# 05. Nektar Next-Phase Blueprint

> 状态：proposed | 面向 `metaharness_ext.nektar` 下一阶段实现的正式蓝图

## 5.1 目标

当前 `metaharness_ext.nektar` 已具备稳定的执行闭环：

```text
NektarGateway
  -> SessionCompiler
    -> XML Renderer
      -> SolverExecutor
        -> Postprocess(FieldConvert)
          -> Validator
```

当前测试基线：76 tests（70 mock + 6 e2e），ruff clean，Nektar++ 5.9.0 本机可用。

下一阶段的目标不是重写这条链，而是在其上补齐三个高价值方向：

1. **分析器实现**：让日志、派生文件和误差指标变成稳定的结构化分析对象
2. **收敛 / 细化研究**：让系统能够回答"结果是否足够好"
3. **3D + 非平凡网格支持**：扩大可覆盖问题空间

这三个方向都应坚持同一原则：

- 通过 typed contracts 和 typed plan mutation 扩展能力
- 不引入 XML 级 ad hoc 编辑
- 提取逻辑靠近数据源，判定逻辑留在 validator / report layer
- 先补单元测试，再补 `@pytest.mark.nektar` e2e

**所有阶段必须维持当前 76+ 测试基线零回归。**

---

## 5.2 Blueprint A：Convergence Study

## 5.2.1 设计意图

新增 `ConvergenceStudyComponent`，围绕单个 `NektarProblemSpec` 生成一组受控变体，并执行：

```text
base problem
  -> mutate discretization level
    -> compile
      -> execute
        -> postprocess
          -> validate
            -> compare trials
              -> produce study report
```

首版应聚焦最有价值、最易验证的扫描维度：

- `NUMMODES`
- 可选的 external mesh level
- 可选的 `TimeStep`

该组件的目标不是做通用优化器，而是提供 **数值收敛研究** 的最小可靠实现。

## 5.2.2 新增对象

建议在 `MHE/src/metaharness_ext/nektar/contracts.py` 新增：

### `NektarMutationAxis`

字段建议：

- `kind: Literal["num_modes", "mesh_path", "time_step"]`
- `values: list[int | float | str]`
- `label: str | None = None`

### `ConvergenceStudySpec`

当前 Phase 2 字段：

- `study_id: str`
- `task_id: str`
- `base_problem: NektarProblemSpec`
- `axis: NektarMutationAxis`
- `metric_key: str = "l2_error_u"`
- `convergence_rule: Literal["absolute", "relative_drop", "plateau"] = "absolute"`
- `target_tolerance: float | None = None`
- `relative_drop_ratio: float = 0.5`
- `plateau_tolerance: float = 0.1`
- `min_points: int = 3`
- `stop_on_first_pass: bool = False`
- `postprocess_plan_override: list[dict[str, str]] | None = None`

> **设计说明**：`postprocess_plan_override` 使用 `list[dict[str, str]]` 而非 `list[dict[str, Any]]`，将值类型约束为 `str` 以防止欠类型化逃逸。每个 dict 至少包含 `"type"` 和 `"output"` 键。若后续需要更丰富的参数类型，应先提升为独立的 Pydantic model（如 `PostprocessStep`），而非放松为 `Any`。

### `ConvergenceStudyReport`

当前 Phase 2 字段：

- `study_id: str`
- `task_id: str`
- `axis_kind: str`
- `metric_key: str`
- `trials: list[ConvergenceTrialReport]`
- `recommended_value: int | None`
- `recommended_trial_id: str | None`
- `converged: bool`
- `observed_order: float | None`
- `recommended_reason: str | None`
- `error_sequence: list[float]`
- `drop_ratios: list[float]`
- `messages: list[str]`
- `summary_metrics: dict[str, float | str]`

每个 `trial` 当前携带完整 typed evidence：

- mutation value / `axis_value`
- `run` / `validation`
- `status`
- `metric_value`
- `solver_log_analysis`
- `filter_output_analysis`
- `error_summary`

## 5.2.3 新增组件

建议新增：

- `MHE/src/metaharness_ext/nektar/convergence.py`
- `MHE/src/metaharness_ext/nektar/convergence.json`

建议新增 slot / capability：

- slot: `convergence_study.primary`
- capability: `nektar.study.convergence`

## 5.2.4 运行语义

首版 `ConvergenceStudyComponent` 应：

1. 接收 `ConvergenceStudySpec`
2. 复制 `base_problem`
3. 通过 typed mutation 修改 `parameters` 或 `domain.mesh_path`
4. 复用 `build_session_plan()`、`SolverExecutorComponent`、`PostprocessComponent`、`NektarValidatorComponent`
5. 汇总 run artifact 与 validation 结果
6. 生成 `ConvergenceStudyReport`

### 子组件运行时注入

`ConvergenceStudyComponent` 需要协调多个现有组件。子组件（executor、postprocess、validator）通过 `activate(runtime)` 接收 `ComponentRuntime`，其中 `SolverExecutorComponent` 依赖 `runtime.storage_path`。

推荐方案：**构造时注入已激活实例**。

```python
class ConvergenceStudyComponent(HarnessComponent):
    def run_study(
        self,
        spec: ConvergenceStudySpec,
        *,
        executor: SolverExecutorComponent,       # 必须已调用 activate()
        postprocessor: PostprocessComponent | None = None,
        validator: NektarValidatorComponent | None = None,
    ) -> ConvergenceStudyReport:
        ...
```

调用方负责创建和激活子组件，convergence 组件只负责编排。这避免了 convergence 组件自身需要持有 `ComponentRuntime` 来激活子组件的复杂度。

备选方案（如需 convergence 组件自己激活子组件）：convergence 组件自身持有 runtime，通过 `activate()` 接收，然后在内部创建并激活子组件。但这增加了生命周期管理的复杂度，首版不推荐。

结果落盘建议：

```text
runtime.storage_path / ".runs" / "nektar" / <task_id> / "studies" / <study_id>.json
```

study 子运行命名建议：

```text
<task_id>__study__<axis_kind>__<value>
```

> **注意**：当 `value` 为 float 时（如 `time_step`），目录名中会包含小数点。这不会导致文件系统问题，但建议使用下划线替代（如 `0_001` 代替 `0.001`）以避免混淆。

## 5.2.5 Phase 2 判据

当前实现支持三类收敛判据：

- `absolute`：最早满足 `metric_value <= target_tolerance` 的 trial 被推荐；若未命中则退化为最佳可用 metric trial
- `relative_drop`：对相邻 trial 计算 `next_error / current_error`；当该 ratio `<= relative_drop_ratio`（默认 `0.5`）时，后一个 trial 被推荐
- `plateau`：先要求 error sequence 单调不增，再比较相邻 drop ratio 的变化量；当 `abs(ratio_i - ratio_{i-1}) < plateau_tolerance`（默认 `0.1`）时，后一个 trial 被推荐

`stop_on_first_pass` 在 Phase 2 中是 rule-aware 的：只有当前规则已经形成 recommendation 条件时，study 才提前停止。

`observed_order` 则作为经验误差衰减阶，从已完成且 metric 为正的 trial 序列上按
`log(e_i / e_{i+1}) / log(N_{i+1} / N_i)` 计算；若存在至少两段有效局部阶，则取最后两段平均，否则退化为最后一段，若无有效序列则返回 `None`。

## 5.2.6 范围边界

首版不做：

- Bayesian optimization
- 跨 solver family 自动重路由
- HPC 调度
- 任意 mesh refinement pipeline

---

## 5.3 Blueprint B：Analyzers

## 5.3.1 设计意图

`MHE/src/metaharness_ext/nektar/analyzers.py` 当前仍是存根。下一阶段应把它补成 **共享分析层**，服务于：

- convergence study report
- CLI / report generation
- 后续 agent 决策与解释

这一层应保持为 **纯函数工具层**，而不是新组件。

## 5.3.2 目标函数与返回类型

所有三个函数应返回类型化的 Pydantic model，而非非结构化 `dict`。这与项目 "typed contracts" 原则一致，确保 Phase 2 convergence 消费 analyzer 输出时有稳定契约。

建议在 `contracts.py` 新增：

### `SolverLogAnalysis`

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

### `FilterOutputAnalysis`

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

### `ErrorSummary`

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

函数签名相应更新：

```python
def parse_solver_log(log_path: str | Path) -> SolverLogAnalysis: ...
def parse_filter_outputs(paths: list[str] | None = None) -> FilterOutputAnalysis: ...
def summarize_reference_error(metrics: dict[str, float | str] | None = None) -> ErrorSummary: ...
```

> **兼容性说明**：当前 `parse_filter_outputs()` 返回 `FilterOutputSummary`，修改为 `FilterOutputAnalysis`。经 grep 确认，该函数在 `analyzers.py` 外无任何调用方，因此返回类型变更安全。

## 5.3.3 提取逻辑归属

`solver_executor.py` 已有 `_extract_error_norms()` 和 `_extract_step_metrics()`，使用经过 Nektar++ 5.9.0 真实输出验证的正则表达式。`analyzers.py` 的 `parse_solver_log()` 需要相同的解析能力。

**归属决策**：两者共存，各有侧重。

- `solver_executor`：在运行时实时提取，结果写入 `NektarRunArtifact`。正则定义在 executor 内部（私有方法）。
- `analyzers`：在运行后对日志文件做全面分析（包括 warnings、fatals、performance），可复用相同模式。正则定义在 analyzers 内部（私有函数）。

**不抽取共享正则模块**。理由：

- 两组正则的捕获目的不同（executor 只提取数值，analyzers 还要分类和统计）
- 正则模式各自演进的风险可控（均有对应测试覆盖）
- 避免引入新的模块级依赖

若后续发现正则严重分化，可在收敛研究阶段再考虑提取共享层。

## 5.3.4 结构分工

职责边界建议如下：

- executor / postprocess：提取原始指标到 artifact（运行时，靠近数据源）
- analyzers：把日志与指标转为结构化解释（运行后，纯函数）
- validator：消费原始指标并生成 pass/fail（运行后，组件）
- convergence：消费 analyzer 输出并做多次运行比较（运行后，组件）

## 5.3.5 工程要求

analyzer 层应保持：

- 纯函数
- 无 runtime 依赖
- 对缺失文件或空输入返回结构化状态（Pydantic model 默认值）
- 易于单元测试

---

## 5.4 Blueprint C：3D + Non-trivial Mesh Support

## 5.4.1 设计意图

当前实现已支持：

- 3D geometry contract 字段（`NektarGeometrySection` 含 `faces` 字段，并有 `dimension == 3` 校验）
- external mesh path
- renderer 中的 `FACE` / 3D geometry section

但仍缺少让 3D 问题自然进入系统的关键桥梁。该方向目标是把系统从"2D 优先演示实现"推进到"可处理更真实几何输入"的阶段。

## 5.4.2 分层目标

### C1. 3D baseline support

目标：支持基础 3D 问题最小跑通。

需要：

- **Gateway `issue_task()` 参数扩展**：增加 `dimension`、`space_dimension`、`variables` 参数（当前 `NektarProblemSpec` 已有这些字段，但 `issue_task()` 硬编码 `dimension=2`）
- compiler 支持默认 3D inline geometry
- contracts / renderer 对 3D completeness 有更明确校验

### C2. external mesh strengthening

目标：让 external mesh support 更稳健。

需要：

- 更清晰的 `source_mode` 语义
- mesh file existence / compatibility 预检查
- 更好的错误消息与负向测试

### C3. advanced geometry modes

目标：支持更复杂几何形态。

潜在范围：

- curved elements
- prism / hex 支持
- homogeneous strip
- `NekMesh` 接入

## 5.4.3 首阶段实现

建议首先完成 C1：

- 为 `NektarGatewayComponent.issue_task()` 增加 `dimension`、`space_dimension`、`variables` 参数（`NektarProblemSpec` 已有对应字段，此处仅为网关参数透传）
- 将 `_default_geometry()` 拆为 `_default_geometry_2d()` 与 `_default_geometry_3d()`
- 首版 `_default_geometry_3d()` 提供 unit hexahedron baseline
- 强化 3D geometry completeness 校验
- 增加 3D golden XML 与 negative tests

## 5.4.4 范围边界

首阶段不做：

- 自动从 CAD 生成 mesh
- 完整 `NekMesh` 编排
- 复杂多块域 authoring
- 任意高阶几何编辑体验

---

## 5.5 优先级与依赖

三个方向的依赖关系如下：

```text
B analyzers
  -> 为 A convergence study 提供结构化分析底座

A convergence study
  -> 提升系统的科学研究能力

C 3D / mesh support
  -> 扩大问题覆盖面（与 A/B 正交）
```

**业务价值排序**：A（收敛研究）> B（分析器）> C（3D 扩展）

**实施顺序**：B → A → C

理由：

- A 消费 B 的输出（`ErrorSummary` 等），先做 B 可避免 A 返工
- C 与 A/B 正交，可随时插入，不影响主线
- 优先级和价值排序不同是正常的 — 依赖约束应优先于价值排序

---

## 5.6 结论

`metaharness_ext.nektar` 的下一阶段不需要推倒重来，而应沿着现有 typed architecture 补三类能力：

- 用 `analyzers.py` 建立结构化解释层（Pydantic-typed 返回值）
- 用 `ConvergenceStudyComponent` 建立真正的数值研究闭环
- 用 3D / mesh 扩展扩大输入问题空间

其中最关键的不是覆盖面，而是保持：

- contract 稳定
- 运行证据完整
- 测试基线可信（76+ tests 零回归）
- 扩展路径清晰

这条路线与当前代码成熟度匹配，也与 `NEKTAR_BLUEPRINT` 中 `typed mutation -> parameter search -> adaptive iteration` 的演进方向一致。
