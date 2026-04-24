# 04. 扩展蓝图

> 状态：proposed | 面向 `MHE/src/metaharness_ext/deepmd` 的正式实现蓝图

## 4.1 目标

`metaharness_ext.deepmd` 的目标，不是重写 DeePMD-kit / DP-GEN，也不是把它们包装成任意命令执行器，而是把 DeepModeling 的典型训练与并发学习工作流以 **受控、可声明、可验证、可审计** 的方式接入 MHE。

首版应围绕 DeepMD 已经稳定存在的运行模型展开：

```text
JSON config + workspace + executable
  -> logs + checkpoints + models + deviation reports + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 DeepMD / DP-GEN spec
2. 将 spec 编译成稳定 JSON，而不是透传任意 JSON
3. 以受约束的 workspace / executable 运行 DeePMD 与 DP-GEN
4. 收集 artifacts、diagnostics 与 iteration evidence
5. 生成包含工程结果与科学证据的 validator/report
6. 为后续 study / mutation / agent 决策提供稳定证据面

---

## 4.2 设计立场：优先包装控制面，不碰训练内核

建议复用 MHE 的平台层，保持以下边界：

### 平台层：MHE 继续负责

- manifest discovery
- component boot
- graph candidate staging
- semantic validation
- graph version commit / rollback
- hot reload / checkpoint / migration
- provenance / audit
- mutation proposal safety pipeline
- promotion context 与 policy-gated graph commit authority
- session evidence 流、audit linkage、provenance anchoring
- protected-component enforcement
- manifest-level policy surface，包括 `kind`、`safety.protected`、`policy.credentials`、`policy.sandbox` 等当前 strengthened MHE 的治理入口

### 领域层：DeepMD 扩展自己负责

- dataset / training / run / simplify / autotest 的 typed spec
- DeePMD / DP-GEN config compiler
- workspace 准备语义
- diagnostics collector
- training / iteration validator
- evidence packaging
- DeepMD-specific policy / budget / reproducibility gate

这里的核心判断与 AI4PDE 一致：**MHE = 平台 / 控制平面 / 元演化运行时；DeepMD = 领域组件 / 训练工作流 / 科学证据与治理语义。**

---

## 4.3 目录蓝图

建议新增：

```text
MHE/src/metaharness_ext/deepmd/
├── __init__.py
├── contracts.py
├── slots.py
├── capabilities.py
├── gateway.py
├── environment.py
├── data_compiler.py
├── train_config_compiler.py
├── dpgen_param_compiler.py
├── dpgen_machine_compiler.py
├── workspace.py
├── executor.py
├── diagnostics.py
├── validator.py
├── evidence.py
├── policy.py
└── manifests/
    ├── deepmd_gateway.json
    ├── deepmd_executor.json
    └── dpgen_executor.json
```

---

## 4.4 槽位与能力蓝图

### 建议槽位

- `deepmd_gateway.primary`
- `deepmd_environment.primary`
- `deepmd_data_compiler.primary`
- `deepmd_config_compiler.primary`
- `deepmd_executor.primary`
- `deepmd_diagnostics.primary`
- `deepmd_validator.primary`
- `deepmd_evidence.primary`

### 建议 protected slots

- `deepmd_validator.primary`
- `deepmd_evidence.primary`

理由：

- validator 决定什么叫“训练通过 / 科学上够用”，并把结果升级成 promotion-aware governance signal
- evidence manager 决定交付证据结构，不能被普通 proposal 静默弱化
- 当前实现中 validator manifest 已经是 `kind = governance` 且 `protected = true`；文档应把它明确写成治理边界，而不是普通 helper
- policy / review responsibility 可以继续由 runtime-level gate 或 extension-local policy evaluator 承担，但不应允许其绕开 protected validator 所陈述的失败或证据缺口

### 建议 capability IDs

- `deepmd.data.prepare`
- `deepmd.train.run`
- `deepmd.model.freeze`
- `deepmd.model.compress`
- `deepmd.model.test`
- `dpgen.init.run`
- `dpgen.concurrent_learning.run`
- `dpgen.simplify.run`
- `dpgen.autotest.run`
- `deepmd.validation.check`
- `deepmd.evidence.package`

---

## 4.5 首版运行拓扑

### 4.5.1 `deepmd-minimal`

```text
DeepMDGateway
  -> DeepMDEnvironmentProbe
    -> DeepMDTrainConfigCompiler
      -> DeepMDExecutor
        -> DeepMDDiagnosticsCollector
          -> DeepMDValidator
            -> DeepMDEvidenceManager
```

目标：

- 打通单个 DeePMD train/freeze/compress/test 闭环
- 不引入 DP-GEN 与高成本外部 labeling

### 4.5.2 `dpgen-baseline`

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

目标：

- 跑通一个最小 `dpgen run` 或 `simplify` 基线
- 正式纳入 iteration / candidate / fp 证据链

### 4.5.3 `deepmd-expanded`

```text
DeepMDGateway / DPGenGateway
  -> EnvironmentProbe
    -> ConfigCompiler
      -> WorkspacePreprocessor
        -> Executor
          -> DiagnosticsCollector
            -> Validator
              -> EvidenceManager
                -> PolicyGuard / Observability helper
```

目标：

- 把 budget / risk / reproducibility / HPC gating 纳入正式架构
- 为后续 parameter study 与 proposal-only mutation 做准备

---

## 4.6 关键执行语义

### 4.6.1 Environment probe 必须前置

DeepMD 首版最常见失败不是模型本身，而是：

- `dp` / `dpgen` / `dpdata` 不可用
- `input.json` / `param.json` 所需路径缺失
- `machine.json` 描述的 remote/scheduler 环境不可用
- `POTCAR` / `INCAR` / 初始模型 / 数据目录缺失

因此 `environment probe` 必须在 compiler / executor 之前，避免把环境故障误报成训练/科学故障。

### 4.6.2 Workspace preprocessor 是正式组件

DeepMD/DP-GEN 不是“给命令就跑”的系统，而是强依赖目录布局的 workspace-driven workflow。

因此以下能力必须是正式组件职责，而不是零散脚本：

- 工作目录准备
- 输入数据软链接 / 复制
- 模型文件与 config 文件布局
- resume 时对 `record.dpgen` / `iter.*` 的解析
- 结果目录稳定命名

### 4.6.3 Validator 必须区分工程通过与科学通过

例如：

- `dp train` 跑完 ≠ 模型已经足够可信
- `dpgen run` 结束 ≠ 覆盖边界已经满足目标问题
- `simplify` 完成一轮 ≠ transfer-learning 已经收敛

validator 需要至少区分：

- environment valid / invalid
- runtime success / failure
- scientific check pass / fail
- convergence reached / not reached

并且这些结论还要进一步进入 promotion authority：

- validator 提供 mode-aware status 与失败原因
- evidence bundle 提供 artifacts、iteration details、autotest properties 与 completeness warning
- policy 根据 validation + evidence 给出 `allow` / `defer` / `reject`
- runtime 再基于 promotion context、candidate state、session / provenance 证据决定是否允许 graph promotion

这保证 DeepMD 的 validator / policy / study 能服务于统一治理路径，而不是形成一个私有的、不可追溯的本地裁决面。

---

## 4.7 首版验证与 evidence 蓝图

### 最小工程证据

- stdout / stderr
- config JSON
- checkpoint 文件
- frozen / compressed model
- dpgen.log / record.dpgen
- iteration 目录存在性

### 最小科学证据

- `lcurve.out` 可解析
- `dp test` RMSE
- `model_devi.out` 的 candidate / accurate / failed 指标
- autotest 的结果文件
- 当必要信息存在时，对 trust level 与 candidate 规模给出最小科学判断

### 首版不应遗漏的治理证据

- 高成本 `fp` 步骤是否触发
- 使用了哪些 machine / scheduler / remote 资源
- 是否发生 resume / recover
- 当前配置是否属于 transfer-learning / simplify 特殊模式
- validation status 与 policy decision 是什么
- evidence 是否存在 completeness warning，例如 iteration evidence 缺失、autotest property 缺失、stdout/stderr 缺失
- 后续 session / audit / provenance 需要挂接哪些引用，例如 candidate、graph version、session event、policy gate 记录

### runtime evidence integration

DeepMD extension 侧不要求自己实现 session store、audit store 或 graph promotion engine，但它必须保证产物形状与这些 runtime evidence 流兼容：

- run artifact 要有稳定的 run id、working directory、stdout/stderr 与 command provenance
- validation 要能表达 promotion-blocking 失败态与 mode-aware 成功态
- evidence bundle 要能容纳 warning、policy refs 与后续 provenance linkage
- roadmap 中尚未落地的部分，应明确标注为“待对齐 strengthened MHE”，而不是假装 extension 已经自带完整 session / scored-evidence 子系统

---

## 4.8 范围边界

首版明确不做：

- 任意外部 first-principles 软件的自动适配平台
- 任意 JSON round-trip 编辑器
- 直接替代 DP-GEN 内部调度系统
- 在线 DP Library 同步与写回
- 无约束 autotuning / neural architecture search
- 把 DeePMD 训练框架内核作为 MHE 子组件直接嵌入

这里也要澄清：当前不要求 DeepMD 扩展自己实现完整 hot-swap / recovery / session-store 基建，但必须保证 validator、evidence、policy、workspace/provenance 语义可以被 runtime 的 hot-swap governance、checkpoint、audit、promotion path 正确消费。

---

## 4.9 结论

`metaharness_ext.deepmd` 的首版最合理路线是：

- family-aware typed contracts
- environment probe
- controlled JSON compiler
- explicit workspace preprocessor
- mode-aware executor
- diagnostics collector
- science-aware validator
- evidence-first packaging

这条路线与 JEDI/Nektar 的控制面包装模式保持一致，也最符合 DeepModeling 生态当前“配置驱动 + 工作区驱动 + 证据丰富”的工程现实。
