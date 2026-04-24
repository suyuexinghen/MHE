# 05. 路线图

> 状态：mixed baseline + remaining alignment | 面向 `metaharness_ext.deepmd` 的正式执行路线图

## 5.1 推荐执行顺序

### 当前实现快照

截至当前实现，DeepMD wiki 对应的代码基线已经不再是纯 phase-0 规划：

- DeePMD `train` / `freeze` / `compress` / `test` / `model_devi` / `neighbor_stat` 已实现
- DP-GEN `run` / `simplify` / `autotest` 已实现
- validator status 已覆盖 `baseline_success`、`simplify_success`、`converged`、`autotest_validated` 等模式结果
- evidence bundle、policy `allow` / `defer` / `reject`、study baseline 已存在
- 当前主要缺口是继续与 strengthened MHE 的 promotion context、session event/store、manifest policy、scored evidence 与 provenance authority 做更完整对齐

建议执行顺序如下：

```text
Phase 0: Environment Probe + DeePMD Minimal Train/Test Foundation
  -> Phase 1: DeePMD Artifact & Diagnostics Strengthening
    -> Phase 2: DP-GEN Run Baseline
      -> Phase 3: DP-GEN Simplify / Transfer Learning Baseline
        -> Phase 4: Autotest & Property Validation Layer
          -> Phase 5: Study / Mutation Layer
            -> Phase 6: HPC / Governance Hardening
```

这一路线的关键点是：

- 先解决环境、配置和产物边界
- 先用 DeePMD 单体训练链打通最小闭环
- 再进入 DP-GEN 的迭代工作流
- 最后再引入参数研究、治理与高成本执行控制

**通用验收标准**：每个 Phase 完成后，相关测试与 lint 必须保持零回归。

---

## 5.2 Phase 0：Environment Probe + DeePMD Minimal Train/Test Foundation

> 状态：已完成

### 5.2.1 目标

先交付一个“可以检查 DeepMD 环境、生成 `input.json`、完成 train/freeze/compress/test 并返回结构化结果”的最小可用链路。

### 5.2.2 任务

1. 新增 `MHE/src/metaharness_ext/deepmd/` 包骨架与 manifests
2. 新增最小 `gateway.py`，负责接收 request 并规范化 `DeepMDTrainSpec`
3. 在 `contracts.py` 中引入 DeePMD family-aware contracts
4. 新增 `environment.py`，实现 `dp` / `dpdata` / `lmp` / `python` probe
5. 新增 `train_config_compiler.py`，把 typed spec 编译成受控 `input.json`
6. 新增 `executor.py`，先支持 `train` / `freeze` / `compress` / `test`
7. 新增 `validator.py`，区分 environment failure / runtime failure / tested
8. 新增定向测试

### 5.2.3 交付物

- `metaharness_ext.deepmd` 最小包骨架
- DeePMD typed contracts
- environment probe
- 可生成 `input.json` 的 compiler
- 可运行 DeePMD 基础命令的 executor
- 结构化 validator 与单测

### 5.2.4 验收标准

- 能从 typed spec 生成稳定 `input.json`
- 能明确报告 `dp` / `dpdata` / 数据目录缺失
- 能区分配置错误、环境错误与训练错误
- 能显式产出 checkpoint / frozen / compressed / test artifacts
- 不需要真实大规模训练也能完成首批测试

---

## 5.3 Phase 1：DeePMD Artifact & Diagnostics Strengthening

> 状态：已大体完成

### 5.3.1 目标

把 Phase 0 从“能运行 DeePMD”推进到“能结构化解释训练与测试结果”。

### 5.3.2 任务

1. 新增 `diagnostics.py`
2. 提取 `lcurve.out` 的最后一步与关键 RMSE
3. 提取 `train.log` 中的环境、时间与版本线索
4. 规范 frozen / compressed model 产物收集
5. 在 validator 中加入最小科学判据
6. 新增相关测试

### 5.3.3 验收标准

- diagnostics 不再只看 return code
- `lcurve.out` 与 `dp test` 输出可结构化提取
- 缺失诊断时返回稳定默认状态
- evidence bundle 可以稳定引用训练与测试产物

---

## 5.4 Phase 2：DP-GEN Run Baseline

> 状态：已完成

### 5.4.1 目标

把 DeePMD 单体链路扩展到 DP-GEN 的最小 `run` baseline，验证：

```text
param/machine compile -> workspace -> dpgen run -> iteration collect -> validate
```

### 5.4.2 任务

1. 新增 `DPGenRunSpec` / `DPGenMachineSpec`
2. 新增 `dpgen_param_compiler.py`
3. 新增 `dpgen_machine_compiler.py`
4. 新增 `workspace.py`
5. 扩展 `executor.py` 支持 `dpgen run`
6. 新增 `DPGenIterationCollector`
7. 新增 DP-GEN baseline 测试

### 5.4.3 验收标准

- 能从 typed spec 生成稳定 `param.json` / `machine.json`
- 能识别 `iter.000000/00.train/01.model_devi/02.fp`
- 能解析 `record.dpgen` 与最小 candidate/accurate/failed 统计
- validator 能区分 workspace failure、run failure 与 baseline success

---

## 5.5 Phase 3：DP-GEN Simplify / Transfer Learning Baseline

> 状态：已完成基础闭环，仍需继续对齐治理证据语义

### 5.5.1 目标

让 `simplify` / transfer-learning 进入同一套 typed workflow，支持 relabeling 风格迭代。

### 5.5.2 任务

1. 定义 `DPGenSimplifySpec`
2. 支持 `training_init_model`、trainable mask、pick/relabel 参数
3. 扩展 executor 支持 `dpgen simplify`
4. 在 collector 中支持 simplify iteration 语义
5. 新增 transfer-learning / simplify 测试

### 5.5.3 验收标准

- simplify 进入同一套 gateway/compiler/executor/collector/validator 体系
- 能识别 relabeling 任务与已收敛状态
- 不因 simplify 扩展破坏 DeePMD / DP-GEN run baseline

---

## 5.6 Phase 4：Autotest & Property Validation Layer

> 状态：已完成最小实现，仍需继续补齐治理整合

### 5.6.1 目标

把系统从“训练链可用”升级到“模型性质验证链可用”。

### 5.6.2 任务

1. 定义 `DPGenAutotestSpec`
2. 支持 `autotest make/run/post`
3. 识别 EOS / elastic / vacancy / surface 等结果目录
4. 结构化读取 `result.out` / `result.json`
5. 把结果接入 `DeepMDEvidenceBundle`
6. 新增 autotest 测试

### 5.6.3 验收标准

- 至少一类 autotest 结果可被结构化消费
- evidence bundle 中包含性质验证证据
- validator 能给出最小性质验证结论

---

## 5.7 Phase 5：Study / Mutation Layer

> 状态：已建立 baseline，仍待补齐 `ScoredEvidence` / `BrainProvider` 等更上层接缝

### 5.7.1 目标

在稳定 baseline 之上，加入最小研究能力，让 MHE 可以系统比较 DeepMD / DP-GEN 配置。

### 5.7.2 首批参数轴

- DeePMD：`sel`、`rcut`、network width、`numb_steps`
- DP-GEN：`model_devi_f_trust_lo` / `hi`
- exploration 温压 / 时长计划
- simplify pick number / 冻结层级

### 5.7.3 任务

1. 定义 `DeepMDMutationAxis` / `DeepMDStudySpec` / `DeepMDStudyReport`
2. 仅允许对白名单字段做 typed mutation
3. 串联 compiler -> executor -> diagnostics -> validator
4. 输出结构化 study report
5. 新增 study 测试

### 5.7.4 验收标准

- 至少一种参数轴可做多 trial sweep
- study report 有推荐结果与理由
- mutation 不绕过 typed spec 边界
- 不直接在生成后的 JSON 上做无约束 patch

---

## 5.8 Phase 6：HPC / Governance Hardening

> 状态：待对齐 strengthened MHE 的重点剩余项

### 5.8.1 目标

补强真实外部环境与高成本 relabeling 场景下的稳定性和治理边界。

### 5.8.2 任务

1. 扩展 `machine.json` 验证与 scheduler probe
2. 增加远程 SSH / queue / resource failure 的稳定错误语义
3. 引入高成本 `fp` 与长时训练审批 gate
4. 引入 reproducibility / budget / relabeling 风险检查
5. 明确 observation window 与 candidate promotion 语义
6. 把 manifest `policy.credentials` / `policy.sandbox`、HPC / credential boundary 与当前 manifest 兼容策略写清楚
7. 把 validation / evidence 与 session event、audit、provenance refs 的预期形状进一步对齐
8. 视需要把 extension evidence 与 `ScoredEvidence`、`BrainProvider` seam 对齐，而不是继续停留在 extension-local report

### 5.8.3 验收标准

- 环境缺失时失败语义清晰
- scheduler / remote root / source_list 错误不再混成训练失败
- 高成本步骤可进入 policy gate
- 外部环境差异不会被误判成“模型逻辑错误”

---

## 5.9 测试路线

### 单元测试优先级

1. `test_metaharness_deepmd_environment.py`
2. `test_metaharness_deepmd_compiler.py`
3. `test_metaharness_deepmd_executor.py`
4. `test_metaharness_deepmd_diagnostics.py`
5. `test_metaharness_dpgen_compiler.py`
6. `test_metaharness_dpgen_collector.py`
7. `test_metaharness_deepmd_validator.py`

这里还应显式加入 governance-oriented coverage：

- promotion blocker 候选失败态是否被稳定表达
- protected validator boundary 是否不会被普通组件语义绕开
- DP-GEN iteration evidence、autotest property evidence 不完整时是否进入 `defer`
- environment prerequisite / workspace prerequisite 是否能与 runtime governance 证据对齐

### e2e 测试优先级

1. DeePMD minimal train/freeze/test
2. DP-GEN minimal run baseline
3. DP-GEN simplify baseline
4. Autotest property baseline
5. 参数 sweep / study case

---

## 5.10 里程碑

### M1：DeepMD Minimal Foundation

交付：Phase 0 完成。环境探测、typed contracts、`input.json` compiler、基础 executor、validator。

### M2：Diagnostics Layer

交付：Phase 1 完成。学习曲线与测试指标可结构化消费。

### M3：DP-GEN Run Baseline

交付：Phase 2 完成。`dpgen run` 进入同一套受控链路。

### M4：Simplify Baseline

交付：Phase 3 完成。transfer-learning / relabeling 路径可用。

### M5：Autotest Layer

交付：Phase 4 的最小实现已存在。至少一类性质验证结果可被结构化消费；后续重点转为把这些结果接到更完整的 governance / provenance path。

### M6：Study Layer

交付：Phase 5 的 baseline 已存在。至少一种参数轴可做 typed sweep；后续重点转为 scored evidence 与上层决策接缝。

### M7：Governance Hardening

交付：Phase 6 完成。高成本步骤与外部环境治理更清晰稳健，并与 strengthened MHE 的 promotion context、session evidence、manifest policy 和 provenance authority 一致。

---

## 5.11 风险与取舍

### 高收益投入

- `environment probe + controlled JSON compiler + diagnostics` 的投入最小、收益最大
- 它们最早建立 DeepMD 接入的契约边界、环境边界与错误语义

### 高风险投入

- 过早覆盖复杂外部 first-principles 后端
- 过早引入无约束 scheduler 编排
- 过早做无约束 JSON mutation
- 过早把 DP-GEN 当成通用 shell 平台

### 关键控制点

- compiler 不应退化成任意 JSON 透传器
- workspace preprocessor 不应退化成任意文件搬运层
- executor 不应知道过多业务级 scientific policy 细节
- validator 不应承担 config compiler 职责
- study 层不应绕过 typed spec 直接改 JSON

---

## 5.12 结论

`metaharness_ext.deepmd` 的正式推进顺序，应是：

- 先 DeePMD minimal foundation
- 再 diagnostics
- 再 DP-GEN run / simplify / autotest
- 最后 study 与 governance

这一路线最符合 DeepModeling 生态当前的工程现实：其稳定控制面是 JSON，其执行面是 workspace + executable，其高价值信息集中在 artifacts、iteration 状态与科学验证证据，而这些正是 MHE 最擅长承接的部分。
