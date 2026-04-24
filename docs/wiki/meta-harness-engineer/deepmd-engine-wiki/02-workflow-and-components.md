# 02. 工作流与组件链

## 2.1 canonical 组件链

`metaharness_ext.deepmd` 的当前设计，不是把 DeePMD 与 DP-GEN 做成两套互不相干的子系统，而是让它们共享一套 family-aware contracts、environment / validation surface 与 evidence / policy seam。

### 2.1.1 DeepMD train family

```text
DeepMDGatewayComponent
  -> DeepMDEnvironmentProbeComponent
    -> DeepMDTrainConfigCompilerComponent
      -> DeepMDExecutorComponent
        -> DeepMDValidatorComponent
          -> build_evidence_bundle(...)
            -> DeepMDEvidencePolicy.evaluate(...)
```

### 2.1.2 DP-GEN families

```text
DeepMDEnvironmentProbeComponent
  -> build_dpgen_param_json(...) / build_dpgen_machine_json(...)
    -> DeepMDWorkspacePreparer
      -> DeepMDExecutorComponent
        -> DPGenIterationCollector
          -> DeepMDValidatorComponent
            -> build_evidence_bundle(...)
              -> DeepMDEvidencePolicy.evaluate(...)
```

### 2.1.3 Study family

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

关键原则是：**study 只改 typed spec，不直接 patch 已生成的 JSON。**

---

## 2.2 组件职责

### `gateway.py`

`DeepMDGatewayComponent` 当前负责 DeePMD train 侧的入口语义：

- 输出 `DeepMDTrainSpec`
- 为最小 train baseline 提供受控 task 入口
- 避免把训练入口退化成松散 shell 参数

从包级设计看，DeepMD extension 已经支持四个 family；但当前注册的 gateway surface 仍是 train-only，而不是统一 family-aware public entry。

它不是编译器，也不是 validator。

### `environment.py`

`DeepMDEnvironmentProbeComponent` 负责 environment probe：

- 检查 binary 是否可用
- 检查 Python runtime 是否可用
- 检查 dataset path 或 workspace files 是否存在
- 对 DP-GEN family 额外检查 `machine.local_root`、`machine.remote_root`、`machine.command`、`machine.python_path`
- 返回 `DeepMDEnvironmentReport`

它的职责是**前置暴露环境前提**，避免把前置条件缺失误判成运行失败。

### `train_config_compiler.py`

`DeepMDTrainConfigCompilerComponent` 负责 DeePMD train family：

- 从 `DeepMDTrainSpec` 生成稳定 `input.json`
- 构造 `DeepMDRunPlan`
- 固化 command、working directory、expected outputs、dataset paths
- 保持 compiler 是白名单驱动，而不是任意 JSON 透传器

### `dpgen_param_compiler.py` / `dpgen_machine_compiler.py`

这两个模块负责 DP-GEN families：

- 生成受控 `param.json`
- 生成受控 `machine.json`
- 保持 machine / resource 描述与 workflow param 描述分离

### `workspace.py`

`DeepMDWorkspacePreparer` 负责 workspace 准备：

- materialize workspace 输入
- 准备 DP-GEN 所需文件布局
- 在运行前暴露 workspace 级失败

它是目录与输入边界，不承担 validator 职责。

### `executor.py`

`DeepMDExecutorComponent` 负责 mode-aware 执行：

- 运行 DeePMD CLI：`train`、`freeze`、`test`、`compress`、`model_devi`、`neighbor_stat`
- 运行 DP-GEN CLI：`dpgen_run`、`dpgen_simplify`、`dpgen_autotest`
- 收集 stdout / stderr / return code / 产物路径
- 组装 `DeepMDRunArtifact`
- 生成 `DeepMDDiagnosticSummary`

executor 的职责是产生 run artifact，不负责给出最终治理判据。

### `collector.py`

`DPGenIterationCollector` 负责 DP-GEN iteration evidence：

- 识别 `record.dpgen`
- 收集 `iter.*` 结构
- 汇总 candidate / accurate / failed 计数
- 输出 `DPGenIterationCollection`

它让 DP-GEN 路径不退化成“只看 return code”。

### `validator.py`

`DeepMDValidatorComponent` 是当前 extension-local 的 protected governance boundary：

- 基于 run artifact 给出 `DeepMDValidationReport`
- 区分 environment / workspace / runtime / validation 失败态
- 区分 DeePMD 与 DP-GEN 的 mode-aware 成功态
- 为下游 policy / promotion path 提供稳定的 validation signal

当前真正受保护的是 validator，而不是所有 helper。

### `evidence.py` / `policy.py`

这一层构成当前的 evidence / policy seam：

- `build_evidence_bundle(...)` 汇总 evidence files、warnings、metadata
- `DeepMDEvidencePolicy.evaluate(...)` 把 validation + evidence completeness 解释为 `allow` / `defer` / `reject`

它们当前是 helper seam，不是单独注册的 protected component。

### `study.py`

`DeepMDStudyComponent` 负责最小研究入口：

- 在 typed whitelist 轴上做 mutation
- 串联 compiler -> executor -> validator -> evidence -> policy
- 生成 trial-level 结果与推荐值

它的价值不是自动调参魔法，而是把最小研究面纳入 typed、可验证、可审计的扩展边界。

---

## 2.3 关键执行语义

### 2.3.1 environment probe 必须前置

DeepMD / DP-GEN 的早期失败经常来自：

- binary 缺失
- Python runtime 缺失
- dataset / workspace path 缺失
- machine root / remote root / scheduler command 不完整

因此环境检查必须在 compiler / executor 前暴露出来。

### 2.3.2 JSON 是控制面，不是任意透传面

当前设计必须坚持：

- compiler 只从 typed spec 生成受控 JSON
- 不直接接受任意 JSON patch
- study 不直接改 compiler 产物文本
- family boundary 不因“方便”而退化成一个大字典

### 2.3.3 validator、evidence、policy 各自承担不同职责

- **validator**：解释运行结果是否达到当前最小判据
- **evidence**：聚合 artifacts、diagnostics、warnings 与 metadata
- **policy**：基于 validation + completeness 给出 review-ready 决策

三者不应被压扁成一个布尔值。

---

## 2.4 与 runtime authority 的关系

DeepMD 扩展当前不负责实现完整 runtime promotion engine，但必须保证自己的输出可以自然接入上层 authority path：

- `DeepMDValidationReport` 提供 mode-aware status
- `DeepMDEvidenceBundle` 提供 artifacts、warnings、metadata
- `DeepMDPolicyReport` 提供 `allow` / `defer` / `reject`
- runtime 再基于 `PromotionContext`、session / provenance / policy authority 决定是否允许 graph promotion

因此 extension-local 的成功态，只表示当前候选具备进入下游治理路径的资格，不表示 graph 已自动晋升。

---

## 2.5 结论

DeepMD 扩展的组件链重点不在“再造训练框架”，而在：

- 固化 family boundary
- 固化 compiler / workspace / executor 语义
- 固化 validator boundary
- 固化 evidence / policy seam
- 为 study 与后续 runtime governance 对齐提供稳定接口
