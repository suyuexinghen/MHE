# 04. DeepMD Roadmap

> 状态：merged from blueprint + engine wiki | 面向 `metaharness_ext.deepmd` 的正式执行路线图

## 4.1 当前实现快照

截至当前代码基线，DeepMD roadmap 已不应再被阅读为纯未来规划：

- DeePMD `train` / `freeze` / `compress` / `test` / `model_devi` / `neighbor_stat` 已实现
- DP-GEN `run` / `simplify` / `autotest` 已实现
- validator status 已覆盖 `trained`、`frozen`、`tested`、`compressed`、`model_devi_computed`、`neighbor_stat_computed`、`baseline_success`、`simplify_success`、`converged`、`autotest_validated` 等阶段性结果
- evidence bundle、policy `allow` / `defer` / `reject`、study baseline 已存在
- environment report 已能表达 workspace / machine root / remote / scheduler prerequisites
- 当前主要剩余缺口，是继续与 strengthened MHE 的 promotion context、session event/store、manifest policy、scored evidence 与 provenance authority 做更完整对齐

因此本路线图采用 **“已实现 / 待补齐” 混合结构**，而不是把所有阶段都写成 proposal。

---

## 4.2 推荐执行顺序

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
- 再进入 DP-GEN 的 iteration workflow
- 最后再引入参数研究、治理与高成本执行控制

**通用验收标准**：每个 Phase 完成后，相关测试与 lint 必须保持零回归。

---

## 4.3 Phase 0：Environment Probe + DeePMD Minimal Train/Test Foundation

> 状态：已完成

### 目标

先交付一个“可以检查 DeepMD 环境、生成 `input.json`、完成 train/freeze/compress/test 并返回结构化结果”的最小可用链路。

### 已落地结果

- `metaharness_ext.deepmd` 包骨架与 manifests 已存在
- `DeepMDTrainSpec` 与 family-aware contracts 已建立
- `environment.py` 已实现 DeePMD / DP-GEN 环境探测，并产出 `DeepMDEnvironmentReport`
- `train_config_compiler.py` 已能生成受控 `input.json`
- `executor.py` 已支持 DeePMD 执行模式 `train` / `freeze` / `test` / `compress` / `model_devi` / `neighbor_stat`
- `validator.py` 已能区分 `environment_invalid`、`workspace_failed`、`runtime_failed`、`validation_failed` 等状态，并对不同 mode 给出成功态

### 验收标准

- 能从 typed spec 生成稳定 `input.json`
- 能明确报告关键二进制或数据目录缺失
- 能区分配置错误、环境错误与训练错误
- 能显式产出 checkpoint / frozen / compressed / test artifacts
- 不需要真实大规模训练也能完成首批测试

---

## 4.4 Phase 1：DeePMD Artifact & Diagnostics Strengthening

> 状态：已大体完成

### 目标

把 Phase 0 从“能运行 DeePMD”推进到“能结构化解释训练与测试结果”。

### 已落地结果

- 学习曲线与 RMSE 指标已可解析
- frozen / compressed model 产物已规范收集
- validator 已基于 run artifact + summary 做 mode-aware 判定
- evidence bundle 已能稳定引用训练与测试产物

### 仍待补齐

- 与 runtime 统一 `ScoredEvidence` 形状对齐
- 更正式的 provenance / checkpoint refs 语义

### 验收标准

- diagnostics 不再只看 return code
- `lcurve.out` 与 `dp test` 输出可结构化提取
- 缺失诊断时返回稳定默认状态
- evidence bundle 可以稳定引用训练与测试产物

---

## 4.5 Phase 2：DP-GEN Run Baseline

> 状态：已完成

### 目标

把 DeePMD 单体链路扩展到 DP-GEN 的最小 `run` baseline。

### 已落地结果

- `DPGenRunSpec` / `DPGenMachineSpec` 已建立
- `dpgen_param_compiler.py` / `dpgen_machine_compiler.py` 已建立
- `workspace.py` 已支持 workspace 准备
- executor 已支持 execution mode `dpgen_run`
- iteration collector 已能解析 `record.dpgen` 与 iteration 目录
- validator 已能区分 `workspace_failed`、`run_failed` 与 `baseline_success`

### 验收标准

- 能从 typed spec 生成稳定 `param.json` / `machine.json`
- 能识别 `iter.000000/00.train/01.model_devi/02.fp`
- 能解析 `record.dpgen` 与最小 candidate/accurate/failed 统计
- validator 能区分 workspace failure、run failure 与 baseline success

---

## 4.6 Phase 3：DP-GEN Simplify / Transfer Learning Baseline

> 状态：已完成基础闭环，仍需继续对齐治理证据语义

### 目标

让 `simplify` / transfer-learning 进入同一套 typed workflow，支持 relabeling 风格迭代。

### 已落地结果

- `DPGenSimplifySpec` 已建立
- `training_init_model`、`trainable_mask` 与 `relabeling` 已进入 typed workflow
- executor 已支持 execution mode `dpgen_simplify`
- collector / validator 已支持 simplify iteration 与 convergence clues
- evidence / policy 已可表达 relabeling 与 simplify-not-converged warning

### 仍待补齐

- 把 simplify 证据进一步对齐 promotion / provenance 语义
- 如需继续扩展 simplify study，优先先把 raw dict relabeling 收为 typed 子模型

### 验收标准

- simplify 进入同一套 gateway/compiler/executor/collector/validator 体系
- 能识别 relabeling 任务与已收敛状态
- 不因 simplify 扩展破坏 DeePMD / DP-GEN run baseline

---

## 4.7 Phase 4：Autotest & Property Validation Layer

> 状态：已完成最小实现，仍需继续补齐治理整合

### 目标

把系统从“训练链可用”升级到“模型性质验证链可用”。

### 已落地结果

- `DPGenAutotestSpec` 已建立
- autotest 结果已能以 `summary.autotest_properties` 的形式结构化进入 evidence bundle
- validator 已能给出 `autotest_validated` 结论
- policy 已能识别 autotest property evidence 不完整时的 `defer` 条件

### 仍待补齐

- 更正式的 property evidence -> scored evidence 映射
- 与 session / provenance evidence path 的统一引用语义

### 验收标准

- 至少一类 autotest 结果可被结构化消费
- evidence bundle 中包含性质验证证据
- validator 能给出最小性质验证结论

---

## 4.8 Phase 5：Study / Mutation Layer

> 状态：已建立 baseline，仍待补齐 `ScoredEvidence` / `BrainProvider` 等更上层接缝

### 目标

在稳定 baseline 之上，加入最小研究能力，让 MHE 可以系统比较 DeepMD / DP-GEN 配置。

### 已落地结果

- `DeepMDMutationAxis` / `DeepMDStudySpec` / `DeepMDStudyReport` 已建立
- 只允许对白名单字段做 typed mutation
- study 已串联 compiler -> executor -> validator
- study trial 已附带 `evidence_bundle` 与 `policy_report`
- 当前文档只把 `study.py` 中 `_mutate_task(...)` 已实现的参数轴记为“已支持”：
  - DeePMD：`numb_steps`、`rcut`、`rcut_smth`、`sel`
  - DP-GEN run：`model_devi_f_trust_lo` / `model_devi_f_trust_hi`
  - DP-GEN simplify：`relabeling.pick_number`

### 仍待补齐

- 与 `BrainProvider` / 更上层 evaluator seam 对齐
- 更明确的 promotion-aware study evidence 语义
- 如需继续扩展 runtime review facade，保持 `external_review` 与 extension-produced `candidate_record` 的职责边界清晰

### 验收标准

- 至少一种参数轴可做多 trial sweep
- study report 有推荐结果与理由
- mutation 不绕过 typed spec 边界
- 不直接在生成后的 JSON 上做无约束 patch

---

## 4.9 Phase 6：HPC / Governance Hardening

> 状态：已完成首批治理硬化；剩余工作集中在更细粒度 HPC/resource taxonomy 与上层 authority seam

### 目标

补强真实外部环境与高成本 relabeling 场景下的稳定性和治理边界。

### 已落地结果

- `DPGenMachineSpec` 保持 typed contract 边界：非法组合仍在 schema 层拒绝，但缺失 `remote_root` / scheduler `command` 保留为 environment / governance-time finding
- environment probe 已能表达 machine root、remote root、scheduler command、Python runtime 与 workspace path 缺口
- validator 已能把 unavailable artifact 中的 `missing_remote_root`、`missing_scheduler_command`、`missing_machine_root` / `missing_python_runtime` 映射为 promotion-blocking failure status
- policy 已显式 reject `remote_invalid`、`scheduler_invalid`、`machine_invalid`
- `environment_report` 已通过 evidence bundle 进入 metadata / warnings / provenance refs
- policy 已能基于 evidence bundle 中的 environment findings 追加 `environment_prerequisites` gate
- governance 已能把该 policy gate 转成 promotion-blocking `ValidationIssue`，同时 gateway baseline 仍保持 environment -> compiler -> executor -> validator -> policy/governance 的非 short-circuit 执行顺序
- manifest policy surface 已显式声明 `policy.credentials` / `policy.sandbox`，并与当前 sandbox profile 兼容策略对齐

### 仍待补齐

1. 继续扩展真实 scheduler / remote / queue / resource failure 的稳定错误语义
2. 引入高成本 `fp` 与长时训练审批 gate
3. 引入 reproducibility / budget / relabeling 风险检查
4. 明确 observation window 与 candidate promotion 语义（当前仍属上层 runtime 对齐项，不应表述为 DeepMD contracts 已内建）
5. 把 validation / evidence 与 session event、audit、provenance refs 的预期形状进一步对齐
6. 视需要把 extension evidence 与 `ScoredEvidence`、`BrainProvider` seam 对齐，而不是继续停留在 extension-local report

### 验收标准

- 环境缺失时失败语义清晰
- scheduler / remote root / source_list 错误不再混成训练失败
- environment findings 能进入 evidence bundle、policy gate 与 governance issue，而不 short-circuit executor
- 高成本步骤可进入 policy gate
- 外部环境差异不会被误判成“模型逻辑错误”
- extension-local validation / evidence 能自然进入 runtime promotion authority

---

## 4.10 测试路线

### 单元测试优先级

1. `test_metaharness_deepmd_environment.py`
2. `test_metaharness_deepmd_executor.py`
3. `test_metaharness_dpgen_compiler.py`
4. `test_metaharness_dpgen_collector.py`
5. `test_metaharness_deepmd_validator.py`
6. `test_metaharness_deepmd_evidence.py`
7. `test_metaharness_deepmd_policy.py`
8. `test_metaharness_deepmd_study.py`

### governance-oriented coverage

- promotion blocker 候选失败态是否被稳定表达
- protected validator boundary 是否不会被普通组件语义绕开
- DP-GEN iteration evidence、autotest property evidence 不完整时是否进入 `defer`
- environment prerequisite / workspace prerequisite 是否能与 runtime governance 证据对齐
- `scored_evidence`、`evidence_refs` 与 runtime handoff payload 是否保持稳定形状
- `external_review` 等 runtime review 字段是否在 handoff 过程中被正确保留

### e2e 测试优先级

1. DeePMD minimal train/freeze/test
2. DP-GEN minimal run baseline
3. DP-GEN simplify baseline
4. Autotest property baseline
5. 参数 sweep / study case

---

## 4.11 里程碑

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

## 4.12 风险与取舍

### 高收益投入

- `environment probe + controlled JSON compiler + diagnostics/evidence` 的投入最小、收益最大
- 它们最早建立 DeepMD 接入的契约边界、环境边界与错误语义

### 高风险投入

- 过早覆盖复杂外部 first-principles 后端
- 过早引入无约束 scheduler 编排
- 过早做无约束 JSON mutation
- 过早把 DP-GEN 当成通用 shell 平台
- 在未对齐 runtime evidence shape 前就继续发散 extension-local report 类型

### 关键控制点

- compiler 不应退化成任意 JSON 透传器
- workspace preprocessor 不应退化成任意文件搬运层
- executor 不应知道过多业务级 scientific policy 细节
- validator 不应承担 config compiler 职责
- study 层不应绕过 typed spec 直接改 JSON
- evidence / policy 不应形成绕开 runtime promotion authority 的私有决策面

---

## 4.13 结论

合并后的正式路线图应以 `deepmd-engine-wiki/05-roadmap.md` 的“当前实现快照 + 已实现/待补齐”结构为主，并吸收原 blueprint 路线图更清楚的 phase 定义与阶段边界。

当前 DeepMD 的正确推进方式已经不是“从零实现扩展”，而是：

- 维护已有 DeePMD / DP-GEN / simplify / autotest / study baseline
- 继续把 validator / evidence / policy / study 输出对齐到 promotion context、session evidence、provenance 与 scored evidence 主路径
- 让文档、代码和测试同时承认这些能力已经存在，并明确剩余缺口在哪里
