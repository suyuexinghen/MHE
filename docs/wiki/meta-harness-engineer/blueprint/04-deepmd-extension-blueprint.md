# 07. DeepMD Extension Blueprint

> 状态：proposed | 面向 `MHE/src/metaharness_ext/deepmd` 的正式实现蓝图

## 7.1 目标

`metaharness_ext.deepmd` 的目标，不是重写 DeePMD-kit / DP-GEN，也不是把它们降格成任意命令执行器，而是把 DeepModeling 的典型训练、并发学习与验证工作流以 **受控、可声明、可验证、可审计** 的方式接入 MHE。

首版应围绕 DeepModeling 生态已经稳定存在的运行模型展开：

```text
JSON config + workspace + executable
  -> logs + checkpoints + models + iteration evidence + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 DeepMD / DP-GEN spec
2. 将 spec 编译成稳定 JSON，而不是透传任意 JSON
3. 以受约束的 workspace / executable 运行 DeePMD 与 DP-GEN
4. 收集 artifacts、diagnostics 与 iteration evidence
5. 生成包含工程结果与科学证据的 validator/report
6. 为后续 study / mutation / agent 决策提供稳定证据面

---

## 7.2 设计立场：选择 DeepMD 的哪一层作为 MHE 接口

结合当前 DeepMD wiki 与教程材料，可将 DeepModeling 生态的接入层大致分为四层：

- Level 1：物理与数据源层（第一性原理数据、标注来源、体系构造）
- Level 2：模型训练层（descriptor、fitting net、train/freeze/compress/test）
- Level 3：并发学习与工作流层（DP-GEN run / simplify / autotest）
- Level 4：外部封装与工作区控制层（JSON、workspace、launcher、wrapper）

对 MHE 来说，**首版明确选择 Level 4 为主、Level 3 为辅、Level 2 只做受控参数化入口**：

- **Level 4**：MHE 负责 gateway、compiler、workspace preprocessor、executor、diagnostics、validator
- **Level 3**：MHE 负责包装 `dpgen run` / `simplify` / `autotest` 的稳定控制面
- **Level 2**：MHE 只负责编译受控 train/test/freeze/compress 配置与执行入口
- **不进入 Level 1**：不在首版中承接任意 first-principles 标注平台或外部势能软件适配

这与当前 DeepMD wiki 的结论一致：**DeepModeling 的稳定控制面是 JSON + workspace，执行面是 executable + 目录语义。**

---

## 7.3 为什么 DeepMD 适合接入 MHE

从 DeePMD-kit / DP-GEN 教程与当前 wiki 可见，其控制面天然具有声明式、分阶段和证据丰富的特征：

- DeePMD 训练以 `input.json` 为核心控制面
- DP-GEN 运行以 `param.json` + `machine.json` + workspace 为核心控制面
- 工作流天然分阶段：`train -> freeze -> compress -> test` 或 `init -> run -> autotest`
- 结果天然产生 artifact、iteration、日志与模型偏差证据
- `simplify` / transfer-learning 这类增量流程也可表达为稳定目录语义和结构化配置

这与 MHE 的 `compiler -> workspace -> executor -> diagnostics -> validator` 体系高度同构。

---

## 7.4 关键现实约束

### 7.4.1 首版必须显式处理环境探测

DeepMD / DP-GEN 首版最常见失败并不是模型本身，而是：

- `dp` / `dpgen` / `dpdata` 不可用
- `input.json` / `param.json` / `machine.json` 所需路径缺失
- `machine.json` 描述的 remote / scheduler 环境不可用
- 数据目录、初始模型、VASP/LAMMPS 相关输入未准备好

因此 `environment probe` 必须先于 compiler / executor，避免把环境故障误报成训练故障或科学故障。

### 7.4.2 Workspace-driven workflow 是正式边界

DeepMD / DP-GEN 并不是“给一条命令就跑”的系统，而是强依赖目录布局、输入文件位置、iteration 状态和恢复语义的 workspace-driven workflow。

因此以下能力必须是正式组件职责，而不是零散脚本：

- 工作目录准备
- 数据软链接 / 拷贝策略
- config / model / record 文件布局
- `iter.*` / `record.dpgen` / `model_devi.out` 的稳定识别
- resume / recover 语义的结构化表达

### 7.4.3 首版不假设完整 HPC 与标注后端全可用

DeepMD / DP-GEN 的完整生产级运行通常涉及：

- 远程 SSH
- queue / scheduler
- VASP / LAMMPS / CP2K 等外部后端
- 高成本 `fp` 标注步骤

这些能力不能在首版 blueprint 中被默认假定为“总是可用”。

因此，`metaharness_ext.deepmd` 的首版必须：

- 优先从本地 DeePMD minimal train/test 闭环切入
- 先把 DP-GEN 视作 workspace + iteration wrapper，而不是通用集群编排平台
- 把高成本 `fp` / remote / scheduler 语义显式记录为环境或 policy 前提

---

## 7.5 应用族与首版支持边界

首版建议按以下 family 支持：

### 首版正式支持的 family

1. `deepmd_train`
   - 覆盖 `train` / `freeze` / `compress` / `test`
   - 作为最小 DeePMD foundation
2. `dpgen_run`
   - 覆盖 `init` / `run` 的最小 baseline
   - 首版重点落在 iteration 识别与证据收集
3. `dpgen_simplify`
   - 作为 transfer-learning / relabeling 路径的受控扩展
4. `dpgen_autotest`
   - 作为后续模型性质验证入口，不进入首个 baseline 的最高优先级

### 首版明确不支持的 family

- 任意 first-principles backend 的自动适配平台
- 在线 DP Library 同步与写回
- 无约束 autotuning / NAS
- 把 DP-GEN 当成任意 shell workflow 平台
- 直接嵌入 DeePMD 训练内核作为 Python 子系统

---

## 7.6 首版组件链

首版组件链如下：

```text
DeepMDGateway
  -> DeepMDEnvironmentProbe
    -> DeepMDTrainConfigCompiler / DPGenParamCompiler / DPGenMachineCompiler
      -> DeepMDWorkspacePreprocessor
        -> DeepMDExecutor / DPGenExecutor
          -> DeepMDDiagnosticsCollector
            -> DeepMDValidator
              -> DeepMDEvidenceManager
```

### `DeepMDGateway`

职责：

- 接收高层 issue request
- 规范化 `DeepMDTrainSpec` / `DPGenRunSpec` / `DPGenSimplifySpec` / `DPGenAutotestSpec`
- 选择 application family 与 execution mode
- 决定走 DeePMD 单体链路还是 DP-GEN workspace 链路

### `DeepMDEnvironmentProbe`

职责：

- 检查 `dp` / `dpgen` / `dpdata` / `python` / `lmp` 是否存在
- 检查数据目录、初始模型、machine config、workspace root 是否存在
- 检查 remote / scheduler 前提是否满足
- 返回结构化 `DeepMDEnvironmentReport`

### `DeepMDTrainConfigCompiler`

职责：

- 将 typed DeePMD train spec 编译为稳定 `input.json`
- 只允许受控字段进入 JSON
- 支持 descriptor、fitting_net、training、learning_rate 等核心块
- 产出 `DeepMDRunPlan`

### `DPGenParamCompiler` / `DPGenMachineCompiler`

职责：

- 将 typed DP-GEN spec 编译为稳定 `param.json` / `machine.json`
- 把 train / model_devi / fp / simplify / autotest 语义保持在受控 schema 内
- 不允许无约束 JSON patch

### `DeepMDWorkspacePreprocessor`

职责：

- 准备工作目录
- 放置或链接数据、模型、config、脚本引用
- 规范 DeePMD 单体训练目录与 DP-GEN iteration 目录
- 为后续恢复、归档和 validator 提供稳定路径布局

### `DeepMDExecutor` / `DPGenExecutor`

职责：

- 以 mode-aware 方式运行 DeePMD / DP-GEN
- 至少支持：
  1. DeePMD：`train` / `freeze` / `compress` / `test`
  2. DP-GEN：`run` / `simplify` / `autotest`
- 收集退出码、stdout、stderr、运行目录与关键产物
- 提供超时、失败与部分完成语义

### `DeepMDDiagnosticsCollector`

职责：

- 提取 `lcurve.out`、`train.log`、`dp test` 输出摘要
- 提取 `record.dpgen`、`model_devi.out`、`iter.*`、candidate/accurate/failed 统计
- 识别 frozen / compressed model、autotest 结果与 iteration 证据
- 生成 `DeepMDDiagnosticSummary` 或 `DPGenIterationReport`

### `DeepMDValidator`

职责：

- 将环境、执行与诊断结果综合为稳定判定
- 区分 environment invalid / runtime failed / tested / scientific check failed / converged
- 不承担 config compiler 或 workspace preprocessor 职责

### `DeepMDEvidenceManager`

职责：

- 打包 DeePMD / DP-GEN artifacts、summary metrics、iteration refs 与 policy evidence
- 为 study / mutation / agent 层提供稳定证据面

---

## 7.7 typed contracts

首版 contracts 应采用 **family-aware typed models**，避免把 DeepMD 与 DP-GEN 的不同工作流混进一个松散 spec。

### `DeepMDApplicationFamily`

```python
Literal["deepmd_train", "dpgen_run", "dpgen_simplify", "dpgen_autotest"]
```

### `DeepMDExecutionMode`

```python
Literal["train", "freeze", "compress", "test", "run", "simplify", "autotest"]
```

### `DeepMDExecutableSpec`

字段：

- `binary_name: str`
- `launcher: Literal["direct", "mpiexec", "mpirun", "srun"] = "direct"`
- `np: int | None = None`
- `execution_mode: DeepMDExecutionMode`
- `timeout_seconds: int | None = None`

### `DeepMDDatasetSpec`

字段：

- `train_systems: list[str]`
- `validation_systems: list[str] | None = None`
- `batch_size: int | str | None = None`
- `numb_test: int | None = None`

### `DeepMDDescriptorSpec`

字段：

- `kind: Literal["se_e2_a", "se_e3", "hybrid"]`
- `sel: list[int] | None = None`
- `rcut: float | None = None`
- `rcut_smth: float | None = None`
- `neuron: list[int] | None = None`

### `DeepMDFittingNetSpec`

字段：

- `neuron: list[int]`
- `resnet_dt: bool | None = None`
- `seed: int | None = None`

### `DeepMDTrainSpec`

字段：

- `task_id: str`
- `study_id: str | None = None`
- `application_family: Literal["deepmd_train"]`
- `executable: DeepMDExecutableSpec`
- `dataset: DeepMDDatasetSpec`
- `descriptor: DeepMDDescriptorSpec`
- `fitting_net: DeepMDFittingNetSpec`
- `training: dict[str, object]`
- `learning_rate: dict[str, object] | None = None`
- `loss: dict[str, object] | None = None`
- `model: dict[str, object] | None = None`
- `working_directory: str | None = None`

### `DPGenMachineSpec`

字段：

- `context_type: str`
- `batch_type: str | None = None`
- `local_root: str | None = None`
- `remote_root: str | None = None`
- `resources: dict[str, object] = Field(default_factory=dict)`

### `DPGenRunSpec`

字段：

- `task_id: str`
- `study_id: str | None = None`
- `application_family: Literal["dpgen_run"]`
- `executable: DeepMDExecutableSpec`
- `param: dict[str, object]`
- `machine: DPGenMachineSpec`
- `training_init_model: list[str] | None = None`
- `working_directory: str | None = None`

### `DPGenSimplifySpec`

字段：

- `task_id: str`
- `application_family: Literal["dpgen_simplify"]`
- `executable: DeepMDExecutableSpec`
- `param: dict[str, object]`
- `machine: DPGenMachineSpec`
- `pick: dict[str, object] | None = None`
- `training_init_model: list[str] | None = None`
- `working_directory: str | None = None`

### `DPGenAutotestSpec`

字段：

- `task_id: str`
- `application_family: Literal["dpgen_autotest"]`
- `executable: DeepMDExecutableSpec`
- `param: dict[str, object]`
- `machine: DPGenMachineSpec`
- `properties: list[str] | None = None`
- `working_directory: str | None = None`

### `DeepMDRunPlan`

字段：

- `task_id: str`
- `run_id: str`
- `application_family: str`
- `execution_mode: str`
- `command: list[str]`
- `working_directory: str`
- `config_files: list[str]`
- `input_files: list[str]`
- `expected_outputs: list[str]`
- `expected_diagnostics: list[str]`

### `DeepMDRunArtifact`

字段：

- `task_id: str`
- `run_id: str`
- `command: list[str]`
- `return_code: int | None`
- `stdout_path: str | None`
- `stderr_path: str | None`
- `working_directory: str`
- `output_files: list[str]`
- `diagnostic_files: list[str]`
- `completed: bool`

### `DeepMDDiagnosticSummary`

字段：

- `training_metrics: dict[str, float]`
- `test_metrics: dict[str, float]`
- `iteration_metrics: dict[str, float | int]`
- `messages: list[str]`

### `DPGenIterationReport`

字段：

- `iteration_ids: list[str]`
- `candidate_count: int | None`
- `accurate_count: int | None`
- `failed_count: int | None`
- `model_deviation_metrics: dict[str, float]`
- `messages: list[str]`

### `DeepMDValidationReport`

字段：

- `task_id: str`
- `run_id: str`
- `passed: bool`
- `status: Literal[
    "environment_invalid",
    "runtime_failed",
    "tested",
    "scientific_check_failed",
    "converged",
    "partial",
]
`
- `messages: list[str]`
- `summary_metrics: dict[str, float | str]`
- `evidence_files: list[str]`

### `DeepMDEvidenceBundle`

字段：

- `bundle_id: str`
- `task_id: str`
- `run_id: str`
- `application_family: str`
- `artifact_refs: list[str]`
- `validation_summary: dict[str, float | str]`
- `iteration_refs: list[str]`
- `policy_refs: list[str]`

---

## 7.8 运行语义

### 7.8.1 DeePMD 与 DP-GEN 必须分模式执行

执行不应被抽象成单一“run”动作，而应显式区分：

1. **DeePMD train/test family**
   - `train`
   - `freeze`
   - `compress`
   - `test`
2. **DP-GEN workflow family**
   - `run`
   - `simplify`
   - `autotest`

不同 mode 的 validator 语义、产物语义与成本语义不同，不能共用一个简单的“return code == 0 就算完成”规则。

### 7.8.2 最小闭环应从 DeePMD foundation 开始

最小闭环定义为：

```text
spec -> env probe -> input.json -> train -> freeze/compress -> test -> structured validation
```

DP-GEN baseline 定义为：

```text
spec -> env probe -> param/machine compile -> workspace -> dpgen run -> iteration collect -> validator
```

这样可以先用最轻的 DeePMD train/test 路径稳定 contracts 与证据，再进入更复杂的 concurrent learning 场景。

### 7.8.3 JSON 是稳定控制面，但不是任意透传面

扩展必须坚持：

- agent 不直接自由拼接任意命令与 JSON 字段
- 不允许把任意外部 JSON 原封不动透传进 executor
- compiler 只从 typed spec 生成受控 `input.json` / `param.json` / `machine.json`
- 后续 mutation / study 也只能作用在 typed spec 上

### 7.8.4 工作目录与证据目录应标准化

每次运行建议生成以下稳定目录布局：

```text
runtime.storage_path / "deepmd_runs" / <task_id> / <run_id>/
  |- input.json / param.json / machine.json
  |- stdout.log
  |- stderr.log
  |- outputs/
  |- diagnostics/
  |- validation.json
  |- evidence.json
```

---

## 7.9 首版 baseline 策略

### A. DeepMD minimal baseline

首个真实 baseline 固定优先选择 DeePMD minimal train/freeze/test 闭环。理由如下：

1. 它比 DP-GEN 并发学习链更轻，最适合先验证 compiler、workspace、executor、validator 主链
2. 它已经能覆盖 config、日志、checkpoint、frozen/compressed model 与测试指标
3. 失败时更容易收敛到 environment / data / config 问题，而不是把失败混进 remote / scheduler / fp 标注链

### B. DP-GEN run baseline

第二个正式 baseline 使用最小 `dpgen run` 路径，重点证明：

- `param.json` / `machine.json` compiler 可稳定工作
- workspace 语义可被正式包装
- iteration 目录、`record.dpgen`、`model_devi.out` 可稳定收集

### C. Simplify / transfer-learning baseline

第三阶段再进入 `simplify` 与 transfer-learning，重点证明：

- relabeling 风格工作流可进入同一套 typed contracts
- `training_init_model`、pick/relabel 参数与 iteration 语义可受控表达

---

## 7.10 诊断与验证边界

### 首版最小工程证据

- `dp` / `dpgen` / `dpdata` / 数据目录是否存在
- `input.json` / `param.json` / `machine.json` 是否稳定生成
- return code 是否为 0
- stdout/stderr 是否包含 fatal/error 迹象
- 关键 output / checkpoint / model / iteration 文件是否生成

### 首版最小科学证据

- `lcurve.out` 是否可解析
- `dp test` RMSE 是否可提取
- `model_devi.out` 的 candidate / accurate / failed 统计是否可见
- autotest 的最小性质验证结果是否可见
- 当必要信息存在时，是否能对 trust level、candidate 规模与训练收敛给出最小判断

### 不应拖到后续 phase 才引入的最小科学判据

当 workflow 已提供必要 diagnostics 时，validator 应尽早支持类似：

- `dp test` 指标达到目标阈值
- `lcurve.out` 显示训练已收敛或持续改善
- `model_devi.out` 中 accurate / candidate 比例满足最小要求
- autotest 结果满足最小性质验证标准

也就是说，**科学判据不应全部推迟到高级 diagnostics phase 才开始出现**；最小可用版本就应该有最小科学验证。

---

## 7.11 范围边界

首版明确不做：

- 任意外部 first-principles 软件的自动适配平台
- 在线数据库回写与远程同步
- 无约束 JSON round-trip 编辑
- 直接替代 DP-GEN 的内部调度系统
- 无审批的大规模 `fp` / relabeling 自动执行
- 无约束 parameter mutation 或结构搜索

---

## 7.12 结论

`metaharness_ext.deepmd` 的最合理落地方式，是把 DeepModeling 视为一个：

- **JSON-configured**
- **workspace-driven**
- **artifact-rich**
- **family-typed**
- **environment-sensitive**

的训练与并发学习应用族。

因此首版的正式扩展路线应是：

- family-aware typed contracts
- environment probe
- controlled JSON compiler
- explicit workspace preprocessor
- mode-aware executor
- diagnostics collector
- science-aware validator
- evidence-first packaging

这条路线既符合当前 DeepMD wiki 的工程事实，也与 JEDI / Nektar 一致地保持了 MHE 的 contract-first、evidence-first 扩展模式。
