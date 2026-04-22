# 02. JEDI Extension Roadmap

> 状态：updated | 面向 `metaharness_ext.jedi` 的正式执行路线图（与当前 JEDI wiki 对齐；已纳入本地 GCC 15 构建验证结论）

## Technical Alignment Notes

本 roadmap 以 **当前已修正的** `MHE/docs/wiki/meta-harness-engineer/jedi-engine-wiki/` 为事实基线，而不是早期调研阶段的未校正版笔记。阶段划分、baseline 选择与验收标准默认遵循以下技术事实：

- QG toy-model executable 使用实际二进制名，如 `qg4DVar.x`、`qgLETKF.x`、`qgHofX3D.x`、`qgHofX4D.x`，不要沿用早期下划线命名的占位写法
- `3DFGAT` 不是独立 `cost_type`；FGAT 是 `3D-Var` / `4D-Var` 内通过时间插值体现的运行语义
- 当前本地 GCC 15.2.1 环境下，至少 OOPS 与部分 L95/QG toy-model 路径已被观察到可构建/可运行；但 IODA/UFO/SABER 相关 observation stack 的本地“可编译”“可安装”“可真实运行”状态不应在 roadmap 中直接写死，而应由 environment probe 与数据准备状态在执行前显式确认。因此当前主要阻塞点不是抽象的“是否支持 GCC 15”，而是 executable、launcher、shared library、data readiness 与 observation-path 可用性的可审计判定
- diagnostics/output 不应被简化为“纯 NetCDF 日志文件”假设；当前更准确的口径是 IODA/HDF5/ODB diagnostics + 组级证据提取
- 标准 UFO 配置优先使用 `obs operator.name`；`obs space.obs type` 仅应视作 QG legacy YAML 兼容语义
- 文档和实现都必须区分 **CTest test name** 与 **executable name**，例如 `qg_4dvar_rpcg` 可作为测试名存在，但实际运行二进制应写成 `qg4DVar.x`

## 2.1 执行顺序

执行顺序如下：

```text
Phase 0: Environment Probe + Validate-Only Foundation
  -> Phase 1: Toy Smoke Baseline
    -> Phase 2: Real Variational Baseline
      -> Phase 3: Local Ensemble DA Baseline
        -> Phase 4: Diagnostics Strengthening
          -> Phase 5: Study / Mutation Layer
            -> Phase 6: Environment / HPC Hardening
```

这一路线与当前 JEDI wiki 对齐的关键点是：

- 先解决环境与输入边界，而不是直接假定“binary + data + MPI + observation stack 都没问题”；即使当前环境已观察到部分 JEDI 路径可构建/可运行，实际执行前仍需显式核对 executable、launcher、shared library、测试数据与 observation-path 前提
- 先用最轻的 toy smoke case 验证 wrapper 链路
- 再进入正式 variational / local ensemble DA baseline
- 最小科学验证前移，不把科学判据全部推迟到后期

**通用验收标准**：每个 Phase 完成后，相关测试与 lint 必须保持零回归。

---

## 2.2 Phase 0：Environment Probe + Validate-Only Foundation

### 2.2.1 目标

先交付一个“可以检查当前 JEDI 环境、生成 YAML，并通过 `--validate-only` 返回结构化结果”的最小可用链路。Phase 0 的重点不是替当前环境预设一组“已经完全可用”的外部前提，而是把 executable、launcher、shared library、testinput/data 与 observation-path 可用性转化为可探测、可验证、可报告的执行前提。

### 2.2.2 任务

1. 新增 `MHE/src/metaharness_ext/jedi/` 包骨架与 manifest
2. 新增最小 `gateway.py`，负责接收 request 并规范化 `JediExperimentSpec`
3. 在 `contracts.py` 中引入 family-aware contracts
   - `JediCommonSpec`
   - `JediVariationalSpec`
   - `JediLocalEnsembleDASpec`
   - `JediHofXSpec`
   - `JediForecastSpec`
   - `JediEnvironmentReport`
   - `JediRunPlan`
   - `JediRunArtifact`
   - `JediValidationReport`
4. 新增 `environment.py`，实现 binary / launcher / library / path probe
5. 新增 `config_compiler.py`，把 typed spec 编译成受控 YAML
6. 新增 `executor.py`，先支持 `schema` 与 `validate-only`
7. 新增 `validator.py`，区分 environment failure / validation failure / validated
8. 新增 `MHE/tests/test_metaharness_jedi_environment.py`
9. 新增 `MHE/tests/test_metaharness_jedi_validate_only.py`

### 2.2.3 交付物

- `metaharness_ext.jedi` 最小包骨架
- 最小 gateway + family-aware contracts
- environment probe
- 可生成 YAML 的 compiler
- 可运行 `schema` / `--validate-only` 的 executor
- 结构化 validator 与单测

### 2.2.4 验收标准

- 能从 typed spec 生成稳定 YAML
- 能明确报告 binary / launcher / data path 缺失
- 能把“测试数据未准备好”与“YAML 本身非法”明确区分
- 能显式提示或记录 Git LFS / `ctest -R get_` / `ctest -R qg_get_data` / `ctest -R l95_get_data` 一类数据准备前提
- 不把 JEDI 测试数据与 `ENABLE_TESTS=ON` 绑定成硬编码前提；数据准备语义应独立表达
- 能区分 CTest 测试名与实际 executable 名，避免把 `qg_4dvar_rpcg` 这类测试名误当成可执行文件名
- 能构造 `<app>.x --validate-only config.yaml`
- 失败配置返回稳定 `JediValidationReport`
- 不需要真实长时间 MPI run 也能完成首批测试

---

## 2.3 Phase 1：Toy Smoke Baseline

### 2.3.1 目标

把 Phase 0 从“只验证配置”推进到“真实运行一个最轻的 toy application”，验证完整 wrapper 主链：

```text
env probe -> preprocess -> execute -> collect artifacts -> validate
```

### 2.3.2 Smoke baseline

Phase 1 优先选择**当前环境中最轻、最稳定、最容易跑通，且其运行前提已被 environment probe 确认**的 toy executable，执行顺序如下：

1. 若 observation stack 与 test data 已确认可用，则优先 `qgHofX4D.x` / `l95_hofx.x`
2. 当前环境中若存在更轻且更少依赖 observation stack 的 3D-Var 路径，则可优先使用该路径
3. 若前两条路径都不可用，则退回当前明确已观察到的最小 variational binary

把 `hofx` 放在首选位置，不是因为文档预设“它一定能跑”，而是因为在 observation-path 可用时，它最适合作为首个 smoke baseline：

- 它通常比完整 variational / local ensemble DA 少一层 minimizer 与背景误差复杂度，更容易把首轮失败收敛到 environment / input / obs-path 问题
- 它仍然真实覆盖 YAML、binary、launcher（若需要）、working directory、stdout/stderr、observation diagnostics 主链
- 它能尽早产生 `HofX`、`ObsValue`、`ObsError`、`PreQC`、`EffectiveError` 一类 IODA 组级线索，让 collector/validator 从第一轮就面向真实 diagnostics，而不是只验证 return code

### 2.3.3 任务

1. 新增 `preprocessor.py`，负责运行目录与输入文件准备
2. 扩展 `executor.py` 支持 `real_run`
3. 明确 working directory / outputs / diagnostics 的目录布局
4. 跑通至少一个 toy smoke case
5. 收集 stdout/stderr、输出目录与 diagnostics 文件线索
6. 优先验证 IODA 组级 diagnostics 线索：`MetaData`、`ObsValue`、`ObsError`、`PreQC`、`HofX`、`EffectiveError`，并在 workflow 提供时兼容 `QCFlags`
7. 新增 `MHE/tests/test_metaharness_jedi_smoke.py`

### 2.3.4 验收标准

- 至少一个已安装 toy executable 可被稳定调用；这一条的主要风险来自运行数据、launcher 语义与 observation-path 可用性，而不是把某个外部构建状态预设成已完全稳定
- artifact 目录布局稳定可审计
- validator 能区分 validate-only success 与 runtime success/failure
- smoke baseline 的 collector/validator 不只记录文件存在，还能识别最小 IODA 组级 diagnostics 证据
- 不依赖人工整理运行目录

---

## 2.4 Phase 2：Real Variational Baseline

### 2.4.1 目标

在 smoke baseline 之上，进入一个正式的 variational baseline，优先打通 `qg4DVar.x` + `4dvar_rpcg.yaml`。这个阶段可以把“binary 是否存在”视为需要被验证的前提，但不应把 observation stack 或数据前提预设为自动成立；主要工程重心转移到 YAML 编译、数据准备、工作目录管理和最小科学判据。

### 2.4.2 任务

1. 完整支持 `JediVariationalSpec`
2. 让 compiler 正确生成：
   - `cost function`
   - `variational`
   - `output`
   - `final`
   - `test`
3. 支持 `mpiexec` / `mpirun` 风格 launcher
4. 运行真实 `qg4DVar.x` baseline
5. 收集 analysis output、diagnostic output、reference/test output 线索
6. 在 validator 中引入最小科学判据：当 workflow 提供必要 diagnostics 时，至少支持 `RMS(O-A) < RMS(O-B)` 或等价 departures 改善判据
7. 新增 `MHE/tests/test_metaharness_jedi_variational_e2e.py`

### 2.4.3 验收标准

- `qg4DVar.x` 可在本地 workspace 被稳定调用
- baseline 能产出可审计 artifact 与最小科学证据
- validator 不只看 return code，也能给出最小科学结论
- e2e 不依赖人工步骤

---

## 2.5 Phase 3：Local Ensemble DA Baseline

### 2.5.1 目标

扩展到第二类正式应用族：`local_ensemble_da`（对应 JEDI `LocalEnsembleDA` application，首批 baseline 为 LETKF）。

### 2.5.2 任务

1. 完整支持 `JediLocalEnsembleDASpec`
2. 让 compiler 支持以下配置块：
   - `window begin` / `window length`
   - `geometry`
   - `background`
   - `observations`
   - `driver`
   - `local ensemble DA`
   - `output`
   - `test`
3. 跑通 `qgLETKF.x` 或 `l95_letkf.x` baseline
4. 收集 ensemble output / observer output / posterior output 线索
5. 在 validator 中加入最小 ensemble 证据检查
6. 新增 `MHE/tests/test_metaharness_jedi_letkf_e2e.py`

### 2.5.3 验收标准

- 第二类应用族进入同一套 gateway/compiler/preprocessor/executor/validator 体系
- 不因应用族扩展破坏 variational baseline
- ensemble 场景下输出证据仍能稳定归档

---

## 2.6 Phase 4：Diagnostics Strengthening

### 2.6.1 目标

把结果从“跑通 + 最小科学判据”升级到“结构化、可比较、可供 agent 消费”的 diagnostics 层。

### 2.6.2 任务

1. 新增 `diagnostics.py` 或 `analyzers.py`
2. 提取 variational cost history / iteration summary
3. 提取 gradient norm reduction、outer/inner iteration 迹象
4. 提取 observer / HofX / departures 相关输出摘要
5. 提取 ensemble 场景中的 posterior output 线索
6. 把诊断接入 `JediValidationReport.summary_metrics`
7. 新增 `MHE/tests/test_metaharness_jedi_diagnostics.py`

### 2.6.3 验收标准

- `summary_metrics` 不再只含退出码级信息
- 至少一条 variational 诊断和一条 ensemble / observer 诊断被结构化提取
- 缺失诊断时返回稳定默认状态
- collector/validator 对 IODA/HDF5/ODB diagnostics 友好，而不是只依赖纯文本日志

---

## 2.7 Phase 5：Study / Mutation Layer

### 2.7.1 目标

在稳定 baseline 之上，加入最小研究能力，让 MHE 可以系统地比较 JEDI 试验配置。

### 2.7.2 首批参数轴

- minimizer algorithm sweep（如 `RPCG`、`DRPCG`、`RPLanczos`）
- `ninner` / iteration budget sweep
- inflation / localization 参数 sweep
- validate-only schema-guided config mutation

### 2.7.3 任务

1. 定义 `JediMutationAxis` / `JediStudySpec` / `JediStudyReport`
2. 仅允许对白名单字段做 typed mutation
3. 按 family 分别定义允许搜索的参数轴
4. 串联 compiler -> preprocessor -> executor -> diagnostics -> validator
5. 输出结构化 study report

### 2.7.4 验收标准

- 至少一种参数轴可做多 trial sweep
- study report 有推荐结果与理由
- mutation 不绕过 typed spec 边界
- 不直接在生成后的 YAML 上做无约束 patch

---

## 2.8 Phase 6：Environment / HPC Hardening

### 2.8.1 目标

补强真实外部环境下的稳定性，但不改变首版本地 wrapper 架构。

### 2.8.2 任务

1. 扩展 launcher 抽象到 `srun` / `jsrun`（如确有需求）
2. 增加更完整的环境预检查
   - binary
   - launcher
   - shared libs
   - data paths
   - workspace testinput
3. 明确工作目录、数据目录与输出目录策略
4. 明确是否由扩展显式触发 `ctest -R get_` 或等价数据准备步骤；若不触发，则必须把该步骤记录为环境前提
5. 明确 `EnsembleApplication` 顶层 `files:` 多 YAML 模式是否进入下一阶段范围

### 2.8.3 验收标准

- 环境缺失时失败语义清晰
- launcher 扩展不影响 local baseline
- 输出与日志目录布局稳定
- 外部环境差异不会被误判成“YAML 逻辑错误”

---

## 2.9 测试路线

### 单元测试优先级

1. `test_metaharness_jedi_environment.py`
2. `test_metaharness_jedi_validate_only.py`
3. `test_metaharness_jedi_compiler.py`
4. `test_metaharness_jedi_preprocessor.py`
5. `test_metaharness_jedi_validator.py`
6. `test_metaharness_jedi_diagnostics.py`

### e2e 测试优先级

1. Toy smoke case（当前环境最轻可用的 `hofx` / 轻量 variational）
2. QG 4D-Var real run
3. QG / L95 local ensemble DA real run
4. 参数 sweep / study case

### 回归保障

每个 Phase 的 PR 至少应验证：

- `pytest` 针对 JEDI 扩展的目标测试
- `ruff check` 零警告
- 不破坏既有 MHE wiki / docs 导航

---

## 2.10 里程碑

### M1：Environment + Validate-Only Foundation

交付：Phase 0 完成。环境探测、family-aware contracts、YAML compiler、validate-only executor、validator。

### M2：Toy Smoke Baseline

交付：Phase 1 完成。至少一个当前环境中的 toy executable 可被稳定包装与验证。

### M3：Variational Baseline

交付：Phase 2 完成。`qg4DVar.x` 或等价正式 variational baseline 可稳定运行并产出最小科学证据。

### M4：Ensemble Baseline

交付：Phase 3 完成。LETKF / local ensemble DA baseline 可用。

### M5：Diagnostics Layer

交付：Phase 4 完成。关键 cost / iteration / departures / observer diagnostics 可被结构化消费。

### M6：Study Layer

交付：Phase 5 完成。至少一种参数轴可做 typed sweep。

### M7：Environment Hardening

交付：Phase 6 完成。外部环境 / launcher / data-prep 语义更清晰稳健。

---

## 2.11 风险与取舍

### 高收益投入

- `environment probe + validate-only + typed YAML compiler` 的投入最小、收益最大
- 它们能最早建立 JEDI 接入的契约边界、环境边界与错误语义

### 高风险投入

- 过早覆盖复杂 model-specific bundle
- 过早引入 HPC scheduler 编排
- 过早尝试无约束 YAML mutation
- 过早依赖新增 IODA/UFO/SABER 源码改动

### 关键控制点

- compiler 不应退化成任意 YAML 透传器
- preprocessor 不应变成任意外部数据搬运层
- executor 不应知道业务级 YAML 结构细节
- validator 不应承担配置编译职责
- study 层不应绕过 typed spec 直接改 YAML

---

## 2.12 交付节奏

按两轮推进：

### 第一轮

- Phase 0：Environment Probe + Validate-Only Foundation
- Phase 1：Toy Smoke Baseline
- Phase 2：Real Variational Baseline
- Phase 3：Local Ensemble DA Baseline

### 第二轮

- Phase 4：Diagnostics Strengthening
- Phase 5：Study / Mutation Layer
- Phase 6：Environment / HPC Hardening

这一路线最符合当前 10 篇 JEDI wiki 的工程事实：JEDI 的稳定控制面是 YAML，执行面是 launcher + executable，真实落地还必须显式处理环境、输入、diagnostics 和最小科学验证，而这正是 MHE 擅长承接的部分。
