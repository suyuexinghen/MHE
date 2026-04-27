# 02. 工作流与组件链

## 2.1 组件链总览

```text
OctaveGateway
  -> OctaveEnvironmentProbe
    -> OctaveScriptCompiler
      -> OctaveExecutor
        -> OctaveValidator
          (-> OctaveEvidencePolicy)
```

`OctaveEvidencePolicy` 为可选的 policy helper，负责将 validation report 映射为 `ready / defer / blocked` 建议。

## 2.2 组件职责

### OctaveGateway (`octave_gateway.primary`)

**职责：**
- 接收 `OctaveExperimentSpec`
- 选择 family：`script_run` / `function_eval` / `numeric_benchmark`
- 拒绝越界模式（任意 shell、GUI、未声明 package、未声明 output schema）
- 提供 `issue_task(...)`、`compile_experiment(...)`、`run_baseline(...)` 便捷入口
- `declare_interface()` 声明 slot、output contract 与 capability

**不负责：** 直接构造命令行细节、解析 Octave warning、直接判定 scientific success

### OctaveEnvironmentProbe (`octave_environment.primary`)

**职责：**
- 检查 `octave-cli` 是否存在
- 运行 `octave-cli --version` 获取版本
- 探测 `pkg list` 或受控 probe 脚本，记录 package/version
- 检查 workspace 写入能力
- 可选记录 BLAS/LAPACK、OpenMP、graphics backend（`graphics_toolkit`）等事实
- 产出 `OctaveEnvironmentReport`

**不负责：** 自动修复环境、隐式安装 package、编译脚本

### OctaveScriptCompiler (`octave_script_compiler.primary`)

**职责：**
- 将 `OctaveExperimentSpec` 编译为 `OctaveRunPlan`
- 生成 deterministic wrapper `.m`（路径、package、输入加载、受控执行、输出保存、状态写入）
- staging 输入资产：`.m`、`.mat`、CSV、JSON、文本数据
- 声明 expected outputs：变量名、文件名、schema、shape、dtype、数值容差
- 注入 machine-readable status 输出：`mhe_status.txt`（save -text 格式），可选 JSON 输出（需 `jsonencode` 编译时可用）
- 对 inline source、function call、path allowlist、package load 进行约束

Wrapper 典型结构：

```text
1. set up paths and packages
2. load declared inputs
3. run controlled script/function
4. validate expected variables exist
5. save outputs to declared files (.txt via save -text / .mat / figures; JSON if jsonencode available)
6. write mhe_status.txt (save -text format)
```

**不负责：** 接收任意脚本透传、运行外部进程、根据 stderr 反推配置逻辑

### OctaveExecutor (`octave_executor.primary`)

**职责：**
- 在 `.runs/octave/<task_id>/<run_id>/` 或 runtime-injected storage 下准备 workspace
- 写入 wrapper、输入文件和 manifest-like execution metadata
- 执行 `octave-cli --no-gui --quiet --no-init-file <wrapper.m>`
- 控制 timeout、working directory、environment variables
- 捕获 stdout/stderr
- 收集 `.mat`、JSON、CSV、figures、logs、status 文件
- 产出 `OctaveRunArtifact`，区分 `completed`、`failed`、`timeout`、`unavailable`

**不负责：** 理解业务级脚本语义、解释 scientific result、管理跨 run 的 workspace 持久化

### OctaveValidator (`octave_validator.primary`) — protected candidate

**职责：**
- 区分 `environment_invalid` / `compile_failed` / `runtime_failed` / `output_missing` / `output_parse_failed` / `numeric_validation_failed` / `executed`
- 检查 return code、status file、expected output files
- 解析 JSON / CSV / `.mat` 元数据或变量摘要
- 对 expected variables 做存在性、shape、dtype、NaN/Inf 和 tolerance 检查
- 对 warning 进行分类：benign / suspicious / blocking
- 生成 `OctaveValidationReport`，包含 `ValidationIssue`、`blocks_promotion`、`governance_state`、`ScoredEvidence`、`evidence_refs`

**不负责：** 再次编译脚本、直接运行 executable、执行 graph promotion

### OctaveEvidencePolicy（helper）

**职责：**
- 基于 environment、artifact、validation 和 output completeness 生成 `ready` / `defer` / `blocked`
- 默认策略建议：
  - environment missing 或 package missing：`blocked`
  - run completed 但缺少结构化输出：`defer` 或 `blocked`
  - numeric tolerance failed：`blocked`
  - warning suspicious 但核心输出完整：`defer`
  - all checks passed 且 evidence complete：`ready`

## 2.3 组件生命周期

每个组件在 `activate(self, runtime: ComponentRuntime)` 中将 `self._runtime = runtime` 存储 runtime 引用（与 ABACUS 模式一致）。Executor 使用 `runtime.storage_path` 解析 workspace 根路径（`.runs/octave/...`）。`deactivate()` 中进行组件级资源清理（关闭未完成 subprocess、移除临时文件等）。

## 2.4 架构边界（不可违反）

- gateway 不承担 compiler/executor 细节
- compiler 不退化为脚本透传
- executor 不理解 family-specific 脚本结构
- validator 不回头补做环境探测或配置编译
- study/mutation 不绕过 typed spec 直接改最终脚本

这些边界一旦混掉，后续扩展到更多 application family 和 Scientific Context Engine 会迅速失控。

## 2.5 MHE 组件图装配视角

每个组件通过 `HarnessComponent.declare_interface()` 声明其 slot、contracts、capabilities：

```text
Slot bindings:
  octave_gateway.primary           -> OctaveGateway
  octave_environment.primary       -> OctaveEnvironmentProbe
  octave_script_compiler.primary   -> OctaveScriptCompiler
  octave_executor.primary          -> OctaveExecutor
  octave_validator.primary         -> OctaveValidator (protected)

Key capabilities:
  octave.task.issue
  octave.environment.probe
  octave.script.compile
  octave.execute.run
  octave.validate.report
  octave.evidence.bundle
```

ConnectionEngine 基于 contracts 连通组件：gateway 输出 spec → environment probe 输出 report → compiler 输出 plan → executor 输出 artifact → validator 输出 report → evidence bundle。
