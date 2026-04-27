# 01. JEDI Extension Blueprint

> 状态：proposed | 面向 `MHE/src/metaharness_ext/jedi` 的正式实现蓝图（与当前 JEDI wiki 对齐）

## Technical Alignment Notes

本 blueprint 以 **当前已修正的** `MHE/docs/wiki/meta-harness-engineer/jedi-engine-wiki/` 为事实基线，而不是早期调研阶段的未校正版笔记。实现和后续评审应默认遵循以下技术事实：

- QG toy-model executable 使用实际二进制名，如 `qg4DVar.x`、`qgLETKF.x`、`qgHofX3D.x`、`qgHofX4D.x`，不要沿用早期下划线命名的占位写法
- `3DFGAT` 不是独立 `cost_type`；FGAT 是 `3D-Var` / `4D-Var` 内通过时间插值体现的运行语义
- 当前本地 GCC 15.2.1 环境下，至少 OOPS 与部分 L95/QG toy-model 路径已被观察到可构建/可运行；但 `ioda` / `ufo` / `saber` 相关 observation stack 的本地可用性不应在 formal docs 中预设为稳定事实，而应由 `environment probe` 与数据就位状态在运行前显式判定
- diagnostics/output 不应被简化为“纯 NetCDF 日志文件”假设；当前更准确的口径是 IODA/HDF5/ODB diagnostics + 组级证据提取
- 标准 UFO 配置优先使用 `obs operator.name`；`obs space.obs type` 仅应视作 QG legacy YAML 兼容语义
- 文档和实现都必须区分 **CTest test name** 与 **executable name**，例如 `qg_4dvar_rpcg` 可作为测试名存在，但实际运行二进制应写成 `qg4DVar.x`

## 1.1 目标

`metaharness_ext.jedi` 的目标，不是重写 JEDI，也不是把 OOPS / UFO / IODA / SABER 的 C++ 内核直接封装成 Python API，而是把 JEDI 的典型数据同化工作流以 **受控、可声明、可验证、可审计** 的方式接入 MHE。

首阶段应围绕 JEDI 已经稳定存在的运行模型展开：

```text
YAML config + model-specific executable + launcher
  -> stdout/stderr + IODA/HDF5/ODB diagnostics + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 JEDI experiment spec
2. 将 spec 编译成稳定 YAML，而不是透传任意 YAML
3. 以受约束的 launcher / executable 运行 JEDI
4. 显式 materialize 运行输入、检查 required runtime paths，并归档 runtime evidence
5. 生成稳定的 environment / run / validation contracts 与 evidence-first validation report
6. 为后续 smoke policy、diagnostics interpretation 与 agent 决策提供稳定骨架

---

## 1.2 设计立场：选择 JEDI 的哪一层作为 MHE 接口

根据当前 JEDI wiki 中的分层分析，JEDI 的扩展面可分为四层：

- Level 1：模型接口层（C++ Traits / Geometry / State / Model / LinearModel）
- Level 2：观测算子层（UFO / ObsOperator / QC）
- Level 3：配置与实验层（YAML）
- Level 4：外部封装层（Python / Shell / workflow wrapper）

对 MHE 来说，**首版明确选择 Level 4 为主、Level 3 为辅**：

- **Level 4**：MHE 负责 gateway、compiler、preprocessor、executor、diagnostics、validator
- **Level 3**：MHE 负责编译受控 YAML 模板与参数覆盖
- **不进入 Level 1/2**：不在首版中实现新的 model interface、obs operator 或 C++ binding

这与当前 JEDI wiki 的“YAML 是稳定控制面、launcher + executable 是执行面”的结论一致。

---

## 1.3 为什么 JEDI 适合接入 MHE

从当前 JEDI wiki 与本地 workspace 可见，JEDI 的控制面天然是声明式和分阶段的：

- 配置使用 YAML，而不是交互式命令流
- 应用通过 `<launcher> <app>.x config.yaml` 方式启动
- 支持 `--validate-only` 做执行前配置校验
- 支持 `--output-json-schema=...` 生成 schema
- 应用层（`Variational`、`LocalEnsembleDA`、`HofX`、`Forecast`）与算法层（OOPS）之间有清晰边界
- 观测系统（IODA/UFO）与背景误差（SABER）虽然复杂，但对首版 wrapper 来说可以先作为黑盒消费

这与 MHE 的 `compiler -> executor -> diagnostics -> validator` 体系高度同构。

---

## 1.4 关键现实约束

### 1.4.1 本地 workspace 是 bundle + 多仓结构

当前本地 JEDI 工作区并非单仓，而是：

- `jedi-bundle/`：超级构建入口
- `oops/`：应用层与同化算法核心
- `ioda/`：观测数据访问层
- `ufo/`：观测算子与 QC
- `saber/`：背景误差与局地化
- `local/bin/`：已构建可执行程序

### 1.4.2 本地环境优先消费“已安装 toy binaries”

当前对 MHE 最现实的切入点，是优先消费本地已安装 toy-model binaries，而不是假设完整 bundle 所有能力都可用。

在当前调研中，已经明确观察到的可包装 binary 包括：

- `qg4DVar.x`
- `qgLETKF.x`
- `qgHofX4D.x`
- `qgHofX3D.x`
- `qgForecast.x`
- `qgEDA.x`
- `l95_4dvar.x`
- `l95_letkf.x`
- `l95_hofx.x`
- `l95_hofx3d.x`
- `l95_forecast.x`

### 1.4.3 构建环境并不保证完整 JEDI 生态全可用

当前 JEDI wiki 已记录：

- 官方主要支持 GCC 13–14
- 本地 GCC 15.2.1 环境下，至少 OOPS 核心与部分 L95/QG toy-model 路径已被观察到可构建或可运行
- 但 `ioda/ufo/saber` 相关 observation stack 在当前环境中的“可编译”“可安装”“可真实运行”并不等价，不应在首版 blueprint 中被直接写死为稳定前提
- 因此 `metaharness_ext.jedi` 的首版必须把 executable、launcher、shared library、testinput/data readiness 与 observation-path 可用性都视为 **environment-gated facts**，而不是把它们当作零成本已知条件

因此，`metaharness_ext.jedi` 的首版必须：

- 以 **当前已安装、可运行的 toy executables** 为真实 baseline
- 不把“新增 IODA/UFO/SABER 源码能力”作为首批交付前提
- 把数据准备、路径检查、输出判定做成显式步骤

---

## 1.5 JEDI 应用族与首版支持边界

当前 JEDI wiki 已整理出多种 application family。MHE 首版按下列边界支持。

### 首版正式支持的 family

1. `variational`
   - 覆盖 3D-Var / 4D-Var / 4DEnsVar 这一大类
   - FGAT 不作为独立 family 或独立 `cost_type`；它是在 `3D-Var` / `4D-Var` 内通过时间插值体现的运行语义
   - 首版重点落在 toy-model 的 4D-Var baseline
2. `local_ensemble_da`
   - 覆盖 LETKF / GETKF
3. `hofx`
   - 用于轻量 smoke / observation path / diagnostics probing
4. `forecast`
   - 作为后续补强与辅助工作流入口，不进入首个真实 baseline 的优先实现范围

### 首版明确不支持的 family

- `EnsembleApplication` 的多文件顶层 `files:` 聚合模式
- 面向复杂业务模式（如 `fv3-jedi` / `mpas-jedi`）的完整工作流
- 自定义 model interface / obs operator / covariance 实现
- IODA converter pipeline

> 设计上，`variational` 是 family；`3D-Var` / `4D-Var` / `4DEnsVar` / `4D-Weak` 是其内部 `cost_type` 变体。FGAT 不是独立 `cost_type`，而是 `3D-Var` / `4D-Var` 内的运行语义。

---

## 1.6 首版组件链

首版组件链如下：

```text
JediGateway
  -> JediEnvironmentProbe
    -> JediConfigCompiler
      -> JediInputPreprocessor
        -> JediExecutor
          -> JediValidator
```

### `JediGateway`

职责：

- 接收高层 issue request
- 规范化 `JediExperimentSpec`
- 选择 application family 与 target executable
- 决定运行模式：schema / validate-only / real-run

### `JediEnvironmentProbe`

职责：

- 检查 binary 是否存在于 PATH
- 检查动态链接是否可解析（`ldd`）
- 检查 launcher 是否可用（`mpiexec` / `mpirun` / `srun`）
- 检查所需 YAML / testinput / data path 是否存在
- 返回结构化 `JediEnvironmentReport`

> 这个步骤应先于 compiler/executor；否则很多错误会被误判为“配置错误”，而实际是环境错误。

### `JediConfigCompiler`

职责：

- 将 typed spec 编译为 YAML config
- 只允许受控字段进入 YAML
- 支持模板 + overlay，而不是任意 YAML 注入
- 在 family 内部根据 `cost type` 或 `solver` 生成不同块结构
- 产出 `JediRunPlan`

### `JediInputPreprocessor`

职责：

- 在 run directory 中 materialize `config.yaml`
- 校验 `required_runtime_paths` 是否存在
- 记录 `prepared_inputs`
- 为后续运行产物保留统一目录布局入口

> 当前首版 preprocessor 是显式但收敛的 execution-time materialization step，不负责自动下载数据、修复环境，亦不退化为任意外部数据搬运层。

### `JediExecutor`

职责：

- 以 launcher + executable + YAML 的方式运行 JEDI
- 至少支持三种执行模式：
  1. `schema`：`<app>.x --output-json-schema=...`
  2. `validate_only`：`<app>.x --validate-only config.yaml`
  3. `real_run`：`<launcher> ... <app>.x config.yaml`
- 收集退出码、stdout、stderr、运行目录、关键输出文件
- 提供超时与清理语义

### `JediValidator`

职责：

- 将环境、运行与诊断结果综合为稳定判定
- 生成 typed `JediValidationReport`
- 区分“配置通过”和“科学结果通过”
- 不直接承担 YAML 编译或进程执行

---

## 1.7 typed contracts

首版 contracts 采用 **discriminated union**。这样可以避免把所有 family 混进一个松散的 `JediExperimentSpec`，并保持与当前 JEDI wiki 的 application family 边界一致。

### `JediApplicationFamily`

```python
Literal["variational", "local_ensemble_da", "hofx", "forecast"]
```

### `JediExecutionMode`

```python
Literal["schema", "validate_only", "real_run"]
```

### `JediExecutableSpec`

字段：

- `binary_name: str`
- `launcher: Literal["direct", "mpiexec", "mpirun", "srun"] = "direct"`
- `np: int | None = None`
- `execution_mode: JediExecutionMode = "validate_only"`
- `timeout_seconds: int | None = None`
- `schema_output_path: str | None = None`

### `JediCommonSpec`

所有 family 共用字段：

- `task_id: str`
- `study_id: str | None = None`
- `application_family: JediApplicationFamily`
- `executable: JediExecutableSpec`
- `template_name: str | None = None`
- `working_directory: str | None = None`
- `overrides: dict[str, object] = Field(default_factory=dict)`

### `JediVariationalSpec`

字段：

- `application_family: Literal["variational"]`
- `cost_type: Literal["3D-Var", "4D-Var", "4DEnsVar", "4D-Weak"]`
- `fgat_enabled: bool = False` 或等价时间插值配置入口（用于表达 FGAT 运行语义，而不是新增独立 `cost_type`）
- `window_begin: str`
- `window_length: str`
- `analysis_variables: list[str]`
- `geometry: dict[str, object]`
- `model: dict[str, object] | None = None`
- `background: dict[str, object]`
- `background_error: dict[str, object] | None = None`
- `observations: dict[str, object]`（标准 UFO 路径下应优先使用 `obs operator.name`，QG legacy YAML 中可能仍可见 `obs space.obs type`）
- `variational: dict[str, object]`
- `output: dict[str, object] | None = None`
- `final: dict[str, object] | None = None`
- `test: dict[str, object] | None = None`

### `JediLocalEnsembleDASpec`

字段：

- `application_family: Literal["local_ensemble_da"]`
- `window_begin: str`
- `window_length: str`
- `geometry: dict[str, object]`
- `background: dict[str, object]`
- `observations: dict[str, object]`
- `driver: dict[str, object] | None = None`
- `local_ensemble_da: dict[str, object]`
- `output: dict[str, object] | None = None`
- `test: dict[str, object] | None = None`

### `JediHofXSpec`

字段：

- `application_family: Literal["hofx"]`
- `geometry: dict[str, object]`
- `state_or_initial_condition: dict[str, object]`
- `time_window: dict[str, object]`
- `observations: dict[str, object]`
- `model: dict[str, object] | None = None`
- `make_obs: bool | None = None`

### `JediForecastSpec`

字段：

- `application_family: Literal["forecast"]`
- `geometry: dict[str, object]`
- `initial_condition: dict[str, object]`
- `model: dict[str, object]`
- `forecast_length: str`
- `output: dict[str, object] | None = None`

### `JediExperimentSpec`

```python
Annotated[
    JediVariationalSpec
    | JediLocalEnsembleDASpec
    | JediHofXSpec
    | JediForecastSpec,
    Field(discriminator="application_family"),
]
```

### `JediRunPlan`

字段：

- `task_id: str`
- `run_id: str`
- `application_family: JediApplicationFamily`
- `execution_mode: JediExecutionMode`
- `command: list[str]`
- `working_directory: str`
- `config_path: str`
- `schema_path: str | None`
- `expected_outputs: list[str]`
- `expected_logs: list[str]`
- `expected_diagnostics: list[str]`
- `expected_references: list[str]`
- `required_runtime_paths: list[str]`
- `scientific_check: Literal["runtime_only", "rms_improves", "ensemble_outputs_present"]`
- `config_text: str`
- `executable: JediExecutableSpec`

### `JediEnvironmentReport`

字段：

- `binary_available: bool`
- `launcher_available: bool`
- `shared_libraries_resolved: bool`
- `required_paths_present: bool`
- `workspace_testinput_present: bool`
- `data_paths_present: bool`
- `data_prerequisites_ready: bool`
- `binary_path: str | None`
- `launcher_path: str | None`
- `workspace_root: str | None`
- `missing_required_paths: list[str]`
- `missing_data_paths: list[str]`
- `missing_prerequisites: list[str]`
- `ready_prerequisites: list[str]`
- `prerequisite_evidence: dict[str, list[str]]`
- `environment_prerequisites: list[str]`
- `smoke_candidate: JediApplicationFamily | None`
- `smoke_ready: bool`
- `messages: list[str]`

### `JediRunArtifact`

字段：

- `task_id: str`
- `run_id: str`
- `application_family: JediApplicationFamily`
- `execution_mode: JediExecutionMode`
- `command: list[str]`
- `return_code: int | None`
- `config_path: str | None`
- `schema_path: str | None`
- `stdout_path: str | None`
- `stderr_path: str | None`
- `prepared_inputs: list[str]`
- `working_directory: str`
- `output_files: list[str]`
- `diagnostic_files: list[str]`
- `reference_files: list[str]`
- `status: JediRunStatus`
- `result_summary: dict[str, Any]`

### `JediValidationReport`

字段：

- `task_id: str`
- `run_id: str`
- `passed: bool`
- `status: Literal[
    "environment_invalid",
    "validated",
    "executed",
    "validation_failed",
    "runtime_failed",
]
`
- `messages: list[str]`
- `summary_metrics: dict[str, float | str]`
- `evidence_files: list[str]`
- `blocking_reasons: list[str]`
- `policy_decision: Literal["allow", "defer", "reject"] | None`
- `prerequisite_evidence: dict[str, list[str]]`
- `provenance_refs: list[str]`
- `checkpoint_refs: list[str]`

---

## 1.8 运行语义

### 1.8.1 执行模式必须显式分层

JEDI 的执行不应被抽象成单一“run”动作，而应显式区分：

1. **schema mode**
   - 用于生成 schema 或补助 editor/agent 约束
2. **validate-only mode**
   - 用于确认 YAML 结构、字段和引用关系合法
3. **real-run mode**
   - 用于真正执行 DA / HofX / Forecast 计算

这三者的 validator 语义不同，不能共用一个“passed=true 就算完成”的简单规则。

### 1.8.2 validate-only 是首选前置检查，但不是对 real-run 的强制阶段门

Phase 0 的基础执行闭环定义为：

```text
spec -> env probe -> YAML -> preprocess -> mode-aware execution -> evidence-first validation
```

其中 execution mode 显式包含：

- `schema`
- `validate_only`
- `real_run`

`validate_only` 仍然是最便宜、最推荐的前置检查路径，但当前 execution foundation 不把“先 validate_only，后 real_run”写成唯一合法执行序列。这样既保留快速失败能力，也与当前 executor/contracts/tests 的真实行为一致。

### 1.8.3 YAML 是稳定控制面，但不是任意透传面

扩展必须坚持：

- agent 不直接自由拼接业务命令行参数
- 不允许把任意外部 YAML 原封不动透传进 executor
- compiler 只从 typed spec 生成受控 YAML
- 后续 mutation / study 也只能作用在 typed spec 上

### 1.8.4 工作目录与证据目录应标准化

每次运行生成以下稳定目录布局：

```text
runtime.storage_path / ".runs" / "jedi" / <task_id> / <run_id>/
  |- config.yaml
  |- stdout.log
  |- stderr.log
  |- outputs/
  |- diagnostics/
  |- schema.json   (optional)
  |- validation.json
```

---

## 1.9 首版 baseline 策略

### A. Smoke baseline

首个真实 baseline 不应一开始就要求最复杂的 variational 场景，而应优先选择“当前环境中最轻、最稳定、最能证明 wrapper 跑通”的 toy executable。

首个 smoke baseline 的**首选候选**应是 `hofx`，但是否真的由 `hofx` 先行，必须由当前环境中的 observation stack 与 test data readiness 决定。理由如下：

1. 在 observation-path 可用时，`hofx` 是最轻的真实 baseline 之一，通常比完整 variational / local ensemble DA 更容易先跑通
2. `hofx` 仍然完整覆盖 MHE 最关心的首轮主链：YAML -> executable -> optional launcher -> stdout/stderr -> obs diagnostics
3. `hofx` 能更早逼出 `observations`、IODA 诊断文件、`HofX` / departures 相关证据，而不要求先把 minimizer、background error、outer/inner iteration 全部跑通
4. 因此，在环境允许时，它比“直接上 4D-Var”更适合作为 wrapper 首个 smoke：失败时更容易定位为 environment / input / obs-path 问题，而不是把所有失败都混进 variational 算法复杂度里

执行顺序应写成 environment-gated 形式：

1. 若当前环境已确认 observation stack 与 test data 就位，则优先 `hofx` smoke
2. 否则退到当前环境中更少依赖 observation stack 的轻量 toy variational 路径
3. 再进入 `qg4DVar.x` / `l95_4dvar.x` 一类正式 variational baseline

### B. Variational baseline

在当前本地环境下，`qg4DVar.x + 4dvar_rpcg.yaml` 仍是最有代表性的正式 baseline：

- 有现成样例
- `cost function` / `variational` 结构清晰
- 能覆盖 window、background、observations、minimizer、iterations
- 能为后续 cost / gradient / outer-loop 诊断提供证据

### C. Local Ensemble DA baseline

第二个正式 baseline 使用以下路径之一：

- `qgLETKF.x + letkf.yaml`
- 更轻量时使用 `l95_letkf.x`

它能稳定逼出：

- `local ensemble DA` family 的独立 contracts
- ensemble background / members-from-template 语义
- observer / output states / localization / inflation 参数边界

---

## 1.10 诊断与验证边界

当前 blueprint 的另一个缺口，是把 diagnostics 放得太后、把 validator 定义得太“工程化”。与当前 JEDI wiki 对齐后，应明确：

### 首版最小工程证据

- binary / launcher / shared libraries / required paths 是否满足
- `schema` / `validate_only` / `real_run` 是否按 execution mode 返回稳定结果
- return code 是否为 0（当该 mode 需要时）
- stdout/stderr 是否存在且可审计
- `config.yaml`、`schema.json`（如存在）、`prepared_inputs`、`output_files`、`diagnostic_files`、`reference_files` 是否被稳定归档

### 首版 validator 语义

- `environment_invalid`：环境或输入前提未满足，不应继续归因于配置逻辑
- `validated`：`schema` / `validate_only` 路径通过当前最小判定面
- `executed`：`real_run` 完成且存在最小 runtime evidence
- `validation_failed`：配置或当前 mode 的最小 evidence 判定未通过
- `runtime_failed`：运行失败、超时、缺少退出信息或未形成必要运行证据
- `blocking_reasons`：显式列出当前会阻断 promotion/policy 消费的缺口
- `policy_decision`：首版只提供轻量 allow/defer/reject 语义，为后续 policy layer 铺路
- report 还应被理解为 runtime evidence handoff 面：它不是 extension-local 的一次性终端输出，而是 candidate review、graph lifecycle、session/audit 记录与 provenance link 的上游输入

> `executed` 表示“runtime completed with evidence”，不等于 scientific success。当前 blueprint 还要求 validator 逐步从 extension-local report 升级为 governance-bearing surface：先补 blocker / policy / prerequisite evidence / provenance refs，再衔接独立的 evidence bundle 与 policy layer。candidate / graph version / session-event / audit / provenance 这类 runtime-level handoff 在本阶段先保留稳定接口语义，后续由统一治理路径继续承接。

---

## 1.11 观测系统与输入数据边界

### 首版输入边界

首版只消费以下来源：

- JEDI workspace 内现成 `testinput/*.yaml`
- workspace 中已有的 toy-model 数据文件
- 当前 baseline 明确需要的 reference/test output

同时必须把数据准备语义写成显式环境前提，而不是隐含假设：

- 若测试数据由 Git LFS 管理，则应先确认对应数据已被拉取，而不是等运行时再把缺失文件误报成 YAML 错误
- 若当前 workspace 依赖 CTest 数据准备目标，则应显式检查并记录 `ctest -R get_` / `ctest -R qg_get_data` / `ctest -R l95_get_data` 一类步骤是否已执行；对当前能由引用路径直接判定的前提，还应返回 `ready_prerequisites` 与 `prerequisite_evidence`
- 文档与实现应区分 **CTest test name** 和 **executable name**：前者可保持 `qg_4dvar_rpcg` 这类测试名，后者应使用实际二进制名如 `qg4DVar.x`
- `environment probe` / `preprocessor` 应把“binary 存在但 testinput / obsdata / reference data 未就位”判定为环境或输入准备失败，而不是 validation failure
- Phase 0 的 preprocessor 只 materialize config、校验 `required_runtime_paths`、记录 `prepared_inputs`，不自动触发 `ctest -R get_`、`qg_get_data`、`l95_get_data` 或等价数据准备步骤

### 首版不承担的责任

首版不做：

- 新观测格式到 IODA 的 converter pipeline
- 新的 UFO obs operator 开发
- 新的 ObsFilter / QC 策略实现
- 生产级 observation ingestion

### 但需要尊重的外部事实

由于 diagnostics / obs outputs 往往是 IODA/HDF5/ODB 风格产物，collector/validator 设计应为后续 IODA-aware 解析留出接口，而不要把输出假设成纯文本日志或单一 NetCDF 约定。

首版 diagnostics collector 默认支持“组级证据”语义：`ObsValue`、`HofX`、`ObsError`、`EffectiveError`、`PreQC`、`MetaData`、`DerivedObsValue`、`DerivedMetaData`、`ObsErrorData` 是否存在，以及当 workflow 提供时 `QCFlags` 等线索是否可见；否则 validator 很容易退化成只看 return code 和日志字符串。

---

## 1.12 范围边界

首版明确不做：

- Level 1/2 的 JEDI 内核扩展（新 model interface / obs operator / covariance）
- 任意 public JEDI executable 的自动发现与无约束支持
- 完整 HPC scheduler 编排（`sbatch` / `qsub` / job arrays）
- `EnsembleApplication` 的多文件聚合模式
- IODA converter pipeline
- 直接绑定 OOPS / IODA / UFO / SABER 的 C++ API
- 无约束 YAML round-trip 编辑
- 高级 meta-optimization 算法落地

---

## 1.13 结论

`metaharness_ext.jedi` 的最合理落地方式，不是把 JEDI 视为 Python SDK，而是把它视作一个：

- **YAML-configured**
- **launcher-driven**
- **evidence-producing**
- **family-typed**
- **environment-sensitive**

的数据同化应用族。

因此首版的正式扩展路线应是：

- family-aware typed contracts
- environment probe
- controlled YAML compiler
- explicit input preprocessor
- mode-aware executor
- evidence-first validator
- Phase 1+ diagnostics/scientific layers built on the same execution foundation

这条路线既符合当前 10 篇 JEDI wiki 的工程事实，也符合 MHE 一贯的 contract-first、evidence-first 扩展模式。
