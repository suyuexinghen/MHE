# 04. DeepMD Extension Blueprint

> 状态：merged from blueprint + engine wiki | 面向 `MHE/src/metaharness_ext/deepmd` 的正式实现蓝图

## 4.1 目标

`metaharness_ext.deepmd` 的目标，不是重写 DeePMD-kit / DP-GEN，也不是把它们包装成任意命令执行器，而是把 DeepModeling 的典型训练、并发学习与性质验证工作流，以 **受控、可声明、可验证、可审计、可进入统一治理路径** 的方式接入 MHE。

当前扩展已经不再是纯 proposal：

- DeePMD `train` / `freeze` / `compress` / `test` / `model_devi` / `neighbor_stat` 已有实现
- DP-GEN `run` / `simplify` / `autotest` 已有实现
- validator、evidence bundle、policy evaluator、study baseline 已存在
- 剩余工作重点不再是“先把 DeepMD 跑起来”，而是继续与 strengthened MHE 的 promotion / policy / session / provenance authority 对齐

DeepModeling 生态当前最稳定的运行模型仍然是：

```text
JSON config + workspace + executable
  -> logs + checkpoints + models + iteration evidence + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 DeepMD / DP-GEN spec
2. 将 spec 编译成稳定 JSON，而不是透传任意 JSON
3. 以受约束的 workspace / executable 运行 DeePMD 与 DP-GEN
4. 收集 artifacts、diagnostics 与 iteration evidence
5. 生成包含工程结果、科学证据与治理线索的 validator/report
6. 为后续 study / mutation / promotion review 提供稳定证据面

---

## 4.2 平台与领域边界

### 平台层：MHE 继续负责

- manifest discovery / component boot
- graph candidate staging / semantic validation
- graph version commit / rollback
- hot reload / checkpoint / migration
- provenance / audit
- mutation proposal safety pipeline
- `PromotionContext` 与 policy-gated graph commit authority
- session evidence 流、audit linkage、provenance anchoring
- protected-component enforcement
- manifest-level policy surface，包括 `kind`、`safety.protected`、`policy.credentials`、`policy.sandbox`

### 领域层：DeepMD 扩展自己负责

- dataset / training / run / simplify / autotest 的 typed spec
- DeePMD / DP-GEN config compiler
- workspace 准备语义
- diagnostics / iteration collection
- training / iteration validator
- evidence packaging
- DeepMD-specific policy / readiness / reproducibility clues
- study / mutation 的 typed whitelist 入口

核心原则：**MHE = 平台级 promotion / policy / provenance authority；DeepMD = 领域级 workflow、证据与 mode-aware 判据提供者。**

---

## 4.3 设计立场

结合当前代码与 DeepMD wiki，DeepModeling 生态可粗分为四层：

- Level 1：物理与数据源层（第一性原理数据、标注来源、体系构造）
- Level 2：模型训练层（descriptor、fitting net、train/freeze/compress/test）
- Level 3：并发学习与工作流层（DP-GEN run / simplify / autotest）
- Level 4：外部封装与工作区控制层（JSON、workspace、launcher、wrapper）

对 MHE 来说，正式落点应是：

- **Level 4 为主**：gateway、compiler、workspace、executor、validator、evidence、policy
- **Level 3 为辅**：包装 `dpgen run` / `simplify` / `autotest` 的稳定控制面
- **Level 2 只做受控参数化入口**：通过 typed spec 改 descriptor / fitting / training，不直接嵌入训练内核
- **不进入 Level 1**：不把 DeepMD 扩展做成任意 first-principles backend 集成平台

---

## 4.4 当前实现快照

当前目录已经形成的核心模块大致为：

```text
MHE/src/metaharness_ext/deepmd/
├── __init__.py
├── capabilities.py
├── collector.py
├── contracts.py
├── dpgen_machine_compiler.py
├── dpgen_param_compiler.py
├── environment.py
├── evidence.py
├── executor.py
├── gateway.py
├── policy.py
├── slots.py
├── study.py
├── train_config_compiler.py
├── validator.py
└── workspace.py
```

这意味着本蓝图应以**现有实现为基线**，而不是回退到早期的纯 proposal 形态。

---

## 4.5 家族与模式边界

### 正式支持的 application family

- `deepmd_train`
- `dpgen_run`
- `dpgen_simplify`
- `dpgen_autotest`

### 当前执行模式

- DeePMD：`train` / `freeze` / `test` / `compress` / `model_devi` / `neighbor_stat`
- DP-GEN：`dpgen_run` / `dpgen_simplify` / `dpgen_autotest`

### 首版明确不支持的方向

- 任意 first-principles backend 的自动适配平台
- 在线 DP Library 同步与写回
- 无约束 autotuning / NAS
- 把 DP-GEN 当成任意 shell workflow 平台
- 直接嵌入 DeePMD 训练内核作为 Python 子系统

---

## 4.6 槽位与治理责任

### 当前关键槽位

- `deepmd_gateway.primary`
- `deepmd_environment.primary`
- `deepmd_config_compiler.primary`
- `deepmd_executor.primary`
- `deepmd_validator.primary`
- `deepmd_study.primary`

### 当前治理边界

- 当前真正带 `protected = True` 的组件是 `DeepMDValidatorComponent`
- `slots.py` 中唯一进入 `PROTECTED_SLOTS` 的槽位是 `deepmd_validator.primary`
- `validator` 的职责不是普通 helper，而是 extension-local 的 mode-aware validation boundary
- `evidence.py` 提供 `build_evidence_bundle(...)` helper；`policy.py` 提供 `DeepMDEvidencePolicy` helper；它们当前都不是单独注册的 protected slot
- `study` 有注册槽位 `deepmd_study.primary`，但并不属于受保护边界

因此文档上的正式解释应是：

- `DeepMDValidatorComponent.validate_run(...)` 决定 extension-local 的 mode-aware 判据与失败形态
- `build_evidence_bundle(...)` 决定哪些 artifacts / warnings / completeness clues 被交给下游
- `DeepMDEvidencePolicy.evaluate(...)` 基于 validation + evidence 给出 `allow` / `defer` / `reject`
- runtime 再基于 `PromotionContext`、candidate state 与 session / provenance authority 决定是否允许 graph promotion

---

## 4.7 组件链蓝图

### 4.7.1 DeepMD minimal train/test family

```text
DeepMDGateway
  -> DeepMDEnvironmentProbe
    -> DeepMDTrainConfigCompiler
      -> DeepMDExecutor
        -> DeepMDValidator
          -> DeepMDEvidenceBundle
            -> DeepMDEvidencePolicy
```

### 4.7.2 DP-GEN workflow family

```text
DeepMDGateway
  -> DeepMDEnvironmentProbe
    -> DPGenParamCompiler / DPGenMachineCompiler
      -> DeepMDWorkspacePreparer
        -> DeepMDExecutor
          -> DPGenIterationCollector
            -> DeepMDValidator
              -> DeepMDEvidenceBundle
                -> DeepMDEvidencePolicy
```

### 4.7.3 Study / mutation family

```text
DeepMDStudyComponent
  -> mutate typed spec
    -> compiler
      -> executor
        -> validator
          -> evidence bundle
            -> policy report
              -> study report
```

这个链路的关键原则是：**study 作用于 typed whitelist fields，而不是对生成后的 JSON 做无约束 patch。**

---

## 4.8 关键执行语义

### 4.8.1 Environment probe 必须前置

DeepMD / DP-GEN 最常见失败不是模型本身，而是：

- `dp` / `dpgen` / `python` 不可用
- 数据目录、初始模型、workspace 文件缺失
- `machine.json` 描述的 remote/scheduler 环境不可用
- workspace root / machine root / source_list 准备不完整

因此 `environment probe` 必须在 compiler / executor 之前，避免把环境故障误报成训练故障或科学故障。

### 4.8.2 Workspace-driven workflow 是正式边界

DeepMD / DP-GEN 并不是“给一条命令就跑”的系统，而是强依赖目录布局、输入文件位置、iteration 状态和恢复语义的 workspace-driven workflow。

因此以下能力必须是正式职责：

- 工作目录准备
- 数据软链接 / 拷贝策略
- config / model / record 文件布局
- `iter.*` / `record.dpgen` / `model_devi.out` 的稳定识别
- resume / recover 语义的结构化表达

### 4.8.3 Validator 必须区分工程通过、科学通过与治理可晋升

例如：

- `dp train` 跑完 ≠ 模型已经足够可信
- `dpgen run` 结束 ≠ 覆盖边界已经满足目标问题
- `simplify` 完成一轮 ≠ transfer-learning 已经收敛
- `autotest` 产出文件 ≠ 证据已经足以晋升到 promotion-ready

因此当前 DeepMD 侧至少要表达：

- environment valid / invalid
- workspace prepare failure 与 runtime command failure 的区分
- mode-aware validation statuses：`trained`、`frozen`、`tested`、`compressed`、`model_devi_computed`、`neighbor_stat_computed`、`baseline_success`、`simplify_success`、`converged`、`autotest_validated`
- failure statuses：`environment_invalid`、`workspace_failed`、`run_failed`、`runtime_failed`、`validation_failed`
- evidence completeness 是否足够
- policy 是 `allow` / `defer` / `reject`

并且这些结论要进一步服务于 promotion authority：

- validator 提供 mode-aware status 与失败原因
- evidence bundle 提供 artifacts、iteration details、autotest properties 与 completeness warning
- policy 根据 validation + evidence 给出 extension-local review result
- runtime 再基于 promotion context、candidate state、session / provenance evidence 决定是否允许 graph promotion

---

## 4.9 Contracts 蓝图

### 核心 contracts

- family / mode / status literals：`DeepMDApplicationFamily`、`DeepMDExecutionMode`、`DeepMDRunStatus`、`DPGenStageName`
- execution / dataset / model 输入：`DeepMDExecutableSpec`、`DeepMDDatasetSpec`、`DeepMDDescriptorSpec`、`DeepMDFittingNetSpec`、`DeepMDModeInputSpec`
- task specs：`DeepMDTrainSpec`、`DPGenMachineSpec`、`DPGenRunSpec`、`DPGenSimplifySpec`、`DPGenAutotestSpec`
- planning / diagnostics / artifacts：`DeepMDEnvironmentReport`、`DPGenCompiledDocument`、`DeepMDRunPlan`、`DPGenIterationSummary`、`DPGenIterationCollection`、`DeepMDDiagnosticSummary`、`DeepMDRunArtifact`
- validation / evidence / policy：`DeepMDValidationReport`、`DeepMDEvidenceWarning`、`DeepMDEvidenceBundle`、`DeepMDPolicyReport`
- study：`DeepMDMutationAxis`、`DeepMDStudySpec`、`DeepMDStudyTrial`、`DeepMDStudyReport`

### contracts 设计原则

- family-aware typed models，而不是把 DeePMD 与 DP-GEN 混成一个松散 spec
- compiler 从 typed spec 生成稳定 JSON；当前 train family 走 `input.json`，DP-GEN family 走 `param.json` / `machine.json`
- run artifact 保留 `command`、`stdout_path`、`stderr_path`、`working_directory`、workspace / checkpoint / model / diagnostic outputs，并附带 `summary`
- validation report 同时表达 `passed` 与 mode-aware `status`，而不是只有布尔值
- evidence bundle 当前聚合 `run`、`validation`、`summary`、`evidence_files`、`warnings` 与 `metadata`
- study 只允许对白名单字段做 typed mutation

### 仍待对齐的 contracts 缺口

当前 DeepMD contracts 已有 validation / evidence / policy / study 基线，但仍未完全对齐 strengthened MHE 的统一 runtime evidence shape：

- 还没有正式的 `ScoredEvidence` 接缝
- `DeepMDRunArtifact` 当前只有 `workspace_files` / `checkpoint_files` / `model_files` / `diagnostic_files`；并没有显式 `checkpoint_refs` / `provenance_refs` / `session_events` 载体
- `DeepMDEvidenceBundle.metadata` 当前只稳定携带 `status`、`return_code`、`validation_status`
- 还没有把 validation failure 系统映射为 runtime-level `ValidationIssue.blocks_promotion`

这些是后续对齐重点，而不是否定现有 contracts 的理由。

---

## 4.10 验证与 evidence 蓝图

### 最小工程证据

- stdout / stderr
- `input.json` / `param.json` / `machine.json`
- checkpoint 文件
- frozen / compressed model
- `record.dpgen`
- iteration 目录存在性
- autotest 输出目录与结构化 property results

### 最小科学证据

- `lcurve.out` 可解析
- `dp test` RMSE 可提取
- DP-GEN candidate / accurate / failed 指标可提取
- simplify 的 convergence / relabeling clues 可识别
- autotest property evidence 可结构化消费

### 最小治理证据

- validation status
- evidence completeness warning
- policy decision 与 `GateResult`
- `DeepMDEnvironmentReport` 中 machine / scheduler / remote prerequisites 线索
- 后续 session / audit / provenance 需要挂接的 candidate、graph version、policy gate 记录（当前尚未由 DeepMD contracts 直接承载）

### runtime evidence integration

DeepMD extension 侧不要求自己实现 session store、audit store 或 graph promotion engine，但它必须保证产物形状与这些 runtime evidence 流兼容：

- run artifact 要有稳定的 `run_id`、working directory、stdout/stderr 与 command provenance
- validation 要能表达 promotion-blocking 候选失败态与 mode-aware 成功态
- evidence bundle 要能容纳 warning、policy refs 与后续 provenance linkage
- roadmap 中尚未落地的部分，应明确标注为“待对齐 strengthened MHE”，而不是假装 extension 已经自带完整 session / scored-evidence 子系统

---

## 4.11 Study / mutation 蓝图

当前 study baseline 已存在，`DeepMDMutationAxis.kind` 当前白名单包括：

- DeePMD train：`numb_steps`、`rcut`、`rcut_smth`、`sel`
- DP-GEN run：`model_devi_f_trust_lo`、`model_devi_f_trust_hi`
- DP-GEN simplify：`relabeling.pick_number`

需要严格说明的是：`contracts.py` 中的 axis 白名单还包含 `relabeling.pick_number` 之外的这些 literal；是否真正可运行，取决于 `study.py` 中 `_mutate_task(...)` 是否实现对应 family 的 mutation 分支。当前文档只把代码里已经实现 mutation 逻辑的轴写成“已支持”。

当前设计规则应明确写死：

- mutation 只改 typed spec
- 不允许直接 patch compiler 输出的 JSON
- study report 附带 evidence bundle 与 policy report
- 后续要补的是 `ScoredEvidence` / `BrainProvider` 对齐，而不是回退到无类型的研究接口

---

## 4.12 范围边界

当前不要求 DeepMD 扩展自己实现：

- 完整 graph promotion engine
- session store / audit store / provenance graph
- 完整 hot-swap / recovery 子系统
- 任意 HPC / scheduler 编排平台
- 任意 first-principles backend 适配平台

但 DeepMD 必须保证：

- validator、evidence、policy、workspace/provenance 语义可以被 runtime 的 hot-swap governance、checkpoint、audit、promotion path 正确消费
- roadmap 中已实现的能力不能继续被文档写成纯 future plan

---

## 4.13 结论

合并后的正式蓝图应以以下路线为准：

- family-aware typed contracts
- environment probe
- controlled JSON compiler
- explicit workspace preparation
- mode-aware executor
- iteration / diagnostics collection
- protected validator boundary
- evidence-first packaging
- policy-bearing review seam
- study baseline with typed whitelist mutation
- continued alignment with promotion context / session evidence / provenance / scored evidence

这条路线同时保留了原 blueprint 的平台/治理视角，也吸收了 deepmd-engine-wiki 中更贴近当前代码的 contracts / family / baseline 结构，因此应作为 `blueprint` 目录中的更可靠版本。