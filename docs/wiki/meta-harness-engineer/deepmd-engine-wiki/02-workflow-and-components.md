# 02. 工作流与组件链

## 2.1 首版组件链

首版 `metaharness_ext.deepmd` 建议拆成两条可复用但共享 contracts 的组件链。

### 2.1.1 DeePMD-kit 基础训练链

```text
DeepMDGateway
  -> DeepMDEnvironmentProbe
    -> DeepMDDataCompiler
      -> DeepMDTrainConfigCompiler
        -> DeepMDExecutor
          -> DeepMDDiagnosticsCollector
            -> DeepMDValidator
              -> DeepMDEvidenceManager
```

### 2.1.2 DP-GEN 并发学习链

```text
DPGenGateway
  -> DeepMDEnvironmentProbe
    -> DPGenParamCompiler
      -> DPGenMachineCompiler
        -> DPGenWorkspacePreprocessor
          -> DPGenExecutor
            -> DPGenIterationCollector
              -> DPGenValidator
                -> DeepMDEvidenceManager
```

两条链共享：

- environment probe
- evidence manager
- 部分 diagnostics / validator contracts

---

## 2.2 DeePMD-kit 基础训练链职责

### `DeepMDGateway`

职责：

- 接收高层 issue request
- 规范化 `DeepMDTrainSpec`
- 决定运行模式：`prepare_data` / `train` / `freeze` / `compress` / `test` / `model_devi` / `neighbor_stat` / `convert_from`
- 选择最小 happy-path 还是完整 train-test path
- 显式区分训练、测试、模型冻结/压缩、统计与部署前准备路径

### `DeepMDEnvironmentProbe`

职责：

- 检查 `dp` / `dpdata` / `lmp` / `python` 是否存在
- 检查 DeePMD 环境变量与依赖是否满足
- 检查训练数据路径、输出目录、模型文件是否存在
- 需要时检查 `mpirun` 可用性
- 返回结构化 `DeepMDEnvironmentReport`

### `DeepMDDataCompiler`

职责：

- 将上游数据说明编译为可执行的数据准备计划
- 支持：
  - 已有 `deepmd/npy` 数据目录
  - 从 raw/system 目录整理为 `set.*` 结构
  - 借助 `dpdata` 从外部标注数据转换到 `deepmd/npy`
  - HDF5 风格系统路径，如 `file.hdf5#/system`
  - train/validation split 描述
- 只生成受控 data plan，不直接透传任意脚本
- 显式记录 `type.raw`、`type_map.raw`、`coord.npy`、`box.npy`、`energy.npy`、`force.npy`、`virial.npy` 等标签与布局要求

### `DeepMDTrainConfigCompiler`

职责：

- 将 typed `DeepMDTrainSpec` 编译为 `input.json`
- 只允许白名单字段进入 descriptor / fitting / lr / loss / training 块
- 支持模板 + overlay，而不是任意 JSON 注入
- 在需要时显式纳入 `neighbor-stat` 前置统计结果，或记录 `--skip-neighbor-stat` 的风险
- 产出 `DeepMDRunPlan`

### `DeepMDExecutor`

职责：

- 按 mode 调用 `dp` 子命令：
  - `dp train`
  - `dp freeze`
  - `dp compress`
  - `dp test`
  - `dp model-devi`
  - `dp neighbor-stat`
  - `dp convert-from`
- 固化工作目录
- 收集 stdout / stderr / return code / 产物路径
- 维护 checkpoint / frozen / compressed model 产物关系
- 对分布式训练显式记录 Horovod / MPI launcher、worker 数与日志策略

### `DeepMDDiagnosticsCollector`

职责：

- 提取 `lcurve.out` 中的 loss / RMSE / lr 轨迹
- 识别 checkpoint、frozen、compressed model 是否生成
- 提取 `dp test` 的 energy / force / virial RMSE
- 汇总 train.log 中的环境、时间、版本线索
- 生成 `DeepMDDiagnosticSummary`

### `DeepMDValidator`

职责：

- 区分环境失败、配置失败、训练失败、测试失败与已验证成功
- 生成 `DeepMDValidationReport`
- 不直接承担 config compiler 与 process execution 逻辑

### `DeepMDEvidenceManager`

职责：

- 打包：
  - config
  - logs
  - checkpoints
  - model artifacts
  - diagnostics
  - validation summary
  - graph version / provenance refs
- 形成稳定 `DeepMDEvidenceBundle`

---

## 2.3 DP-GEN 并发学习链职责

### `DPGenGateway`

职责：

- 接收 `DPGenRunSpec` / `DPGenSimplifySpec` / `DPGenAutotestSpec`
- 决定运行模式：`init` / `run` / `simplify` / `autotest`
- 指定是否是 dry-run、resume、real-run

### `DPGenParamCompiler`

职责：

- 将 typed spec 编译为受控 `param.json`
- 支持系统与数据、training、exploration、labeling 四大块
- 只允许受控 trust level、jobs、batch、labeling 参数进入

### `DPGenMachineCompiler`

职责：

- 将机器与调度资源描述编译为受控 `machine.json`
- 支持：
  - local shell
  - local slurm
  - remote pbs / ssh
- 明确 command / machine / resources 的边界

### `DPGenWorkspacePreprocessor`

职责：

- 准备 run workspace
- 检查 `init_data_sys`、`sys_configs`、POTCAR / INCAR / 模型文件等输入
- 固化 local/remote root、任务目录、必要软链接
- 明确 resume 所需的 `record.dpgen` 与现有 iter 目录状态

### `DPGenExecutor`

职责：

- 调用：
  - `dpgen init_*`
  - `dpgen run`
  - `dpgen simplify`
  - `dpgen autotest make|run|post`
- 收集 stdout / stderr / return code / 关键目录
- 支持 resume / dry-run / limited-iteration execution

### `DPGenIterationCollector`

职责：

- 识别 `iter.000000/00.train/01.model_devi/02.fp` 结构
- 解析：
  - `record.dpgen`
  - `dpgen.log`
  - `model_devi.out`
  - `candidate.shuffled.*.out`
  - `rest_accurate.*.out`
  - `rest_failed.*.out`
  - `data.000` 等新增数据目录
- 生成 `DPGenIterationReport` / `DPGenRunReport`

### `DPGenValidator`

职责：

- 生成 typed `DPGenValidationReport`
- 区分：
  - environment invalid
  - workspace invalid
  - training incomplete
  - model_deviation incomplete
  - fp incomplete
  - converged
  - scientific check failed
- 对 `simplify` / `autotest` 也返回统一状态模型

---

## 2.4 首版运行语义

### 2.4.1 DeePMD-kit 模式必须显式分层

不应把 DeePMD 视为单一 `run` 动作，而应显式区分：

1. `prepare_data`
2. `neighbor_stat`
3. `train`
4. `freeze`
5. `compress`
6. `test`
7. `model_devi`
8. `convert_from`

这些动作的成本、输入边界和 validator 语义都不同。

这里尤其不应把 `apply` 写成一个笼统黑盒，因为上游实际落地路径通常应进一步拆分为：

- Python inference
- C/C++ inference
- LAMMPS integration
- DP-GEN / autotest consumption

首版扩展可以先不把这些部署路径全部做成独立 mode，但文档与 validator 至少应承认它们是不同的下游集成语义。

### 2.4.2 DP-GEN 模式必须保留阶段语义

DP-GEN 的 `run` 不是黑盒。至少应显式表达：

```text
00.train -> 01.model_devi -> 02.fp
```

以及每个 iteration 的阶段推进与恢复点。这样才能：

- 把 early failure 定位在正确阶段
- 让 MHE 正确理解“停在何处、下一步是什么”
- 为审计与 resume 提供稳定证据

### 2.4.3 JSON 是稳定控制面，但不是任意透传面

扩展必须坚持：

- agent 不直接自由拼接任意 shell/JSON 片段
- compiler 只从 typed spec 生成受控 JSON
- study / mutation 只能作用于 typed spec
- 不直接在已生成 `input.json` / `param.json` 上做无约束 patch

---

## 2.5 首版目录与产物布局建议

### DeePMD-kit

```text
runtime.storage_path / "deepmd_runs" / <task_id> / <run_id>/
  |- input.json
  |- stdout.log
  |- stderr.log
  |- train.log
  |- lcurve.out
  |- checkpoints/
  |- models/
  |   |- graph.pb
  |   |- graph-compress.pb
  |- test/
  |   |- results.e.out
  |   |- results.f.out
  |- validation.json
```

### DP-GEN

```text
runtime.storage_path / "dpgen_runs" / <task_id> / <run_id>/
  |- param.json
  |- machine.json
  |- stdout.log
  |- stderr.log
  |- dpgen.log
  |- record.dpgen
  |- iter.000000/
  |- iter.000001/
  |- reports/
  |   |- iteration-summary.json
  |   |- validation.json
```

---

## 2.6 首版最小 happy path

### DeePMD-kit

```text
DeepMDTrainSpec
  -> environment probe
    -> compile input.json
      -> dp train
        -> dp freeze
          -> dp compress
            -> dp test
              -> diagnostics
                -> validation
                  -> evidence bundle
```

对应的最小命令路径应尽量保持贴近上游 CLI：

```bash
dp train input.json
dp freeze -o graph.pb
dp compress -i graph.pb -o graph-compress.pb
dp test -m graph.pb -s /path/to/system -n 30
```

如果 `sel`、`rcut` 或体系规模仍不稳定，建议在 `dp train` 前先显式执行 `dp neighbor-stat` 以获取邻居统计，而不是直接把相关风险隐藏进训练失败里。

### DP-GEN

```text
DPGenRunSpec
  -> environment probe
    -> compile param/machine
      -> workspace preprocess
        -> dpgen run
          -> iteration collector
            -> validation
              -> evidence bundle
```

首版文档还应把数据与初始化来源说清楚：

- `init_data_sys` 与 `sys_configs` 指向的系统集合
- `training_init_model`、`--restart`、`--init-frz-model`、finetune 等初始化路径
- `record.dpgen` 与 `iter.*` 目录共同定义 resume/recover 语义
- 高成本 `fp`、remote root、scheduler 仅应在环境与 policy 层被显式放行后进入执行链

---

## 2.7 结论

DeepMD 的关键不是“再造一个训练框架”，而是把已有稳定工作流包装成：

- 可声明
- 可验证
- 可审计
- 可恢复
- 可进入后续研究 / mutation / governance 体系

的 MHE 域扩展。

因此首版组件链应优先解决：**config 边界、workspace 边界、artifact 边界、validation 边界**，而不是一开始追求复杂自动优化器。
