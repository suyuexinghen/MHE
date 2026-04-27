# 07. Octave Extension Blueprint

> 状态：proposal | 面向未来 `MHE/src/metaharness_ext/octave` 的设计方案 | 参考 `docs/.trash/plan/Octave-Ext.md`、现有 MHE extension blueprint 与 Meta-Harness wiki

## 7.1 目标

`metaharness_ext.octave` 的目标，是把 GNU Octave 作为一种 **受控、可声明、可验证、可审计** 的科学计算执行 worker 接入 MHE，而不是把 Octave 包装成任意 shell 运行器，也不是在首版中承诺完整替代 MATLAB / Simulink / App Designer / Live Editor。

Octave extension 的核心价值在于：

1. 复用 Octave / MATLAB-like 脚本生态，降低已有科研脚本迁移成本；
2. 将脚本、函数、输入数据、package 依赖、数值输出和图像产物显式建模为 typed contracts；
3. 用 MHE 的 component graph、session、provenance、policy、evidence 和 promotion 语义治理科学计算任务；
4. 为后续 AI-native 科学计算平台中的 Live Workspace、Scientific Context Engine、多 Agent 编排与 HPC 集成保留稳定扩展面；
5. 用可测试、可复现、可回滚的方式替代“手动打开 Octave/MATLAB 跑脚本并人工检查结果”的非结构化流程。

Octave 的稳定运行模型可以概括为：

```text
typed spec + input assets + package requirements
  -> generated wrapper .m + workspace layout
  -> octave-cli --no-gui --quiet --no-init-file
  -> logs + .mat / text / CSV / figures
  -> numeric validation + evidence bundle + policy handoff
```

因此首版扩展的核心职责是：

1. 用 typed contracts 表达可控的 Octave 任务边界；
2. 将 spec 编译为 deterministic wrapper `.m` 与 workspace，而不是直接透传任意命令；
3. 在受约束的 `.runs/` 工作目录中调用 `octave-cli`；
4. 收集 stdout、stderr、返回码、结构化输出、图像和诊断信息；
5. 基于输出完整性、数值容差、warning/error 分类生成 validation report；
6. 将 evidence refs、scored evidence、validation issues 和 blocks_promotion 交给 MHE runtime / policy / provenance 主路径消费。

---

## 7.2 平台与领域边界

### MHE 平台层负责

- manifest discovery / component boot；
- graph candidate staging / semantic validation；
- graph version commit / rollback；
- session event、audit log、artifact snapshot、provenance graph；
- protected-component enforcement；
- policy-gated promotion authority；
- runtime recovery、execution lifecycle service、resource quota；
- BrainProvider / optimizer / mutation proposal 的平台级入口。

### Octave 扩展层负责

- Octave task / workspace / script / function / package / output 的 typed spec；
- Octave environment probe 与 package discovery；
- wrapper `.m` 生成、input asset staging、output schema 编译；
- `octave-cli` 执行、timeout、stdout/stderr capture；
- `.mat` / JSON / CSV / figure / log artifact discovery；
- numeric tolerance、expected variables、warning policy、evidence completeness validation；
- domain-local policy hints 和 governance-shaped evidence bundle；
- 后续 study / mutation 对 typed whitelist fields 的受控扫描。

核心原则：**MHE = platform promotion / session / policy / provenance authority；Octave extension = Octave workflow、workspace、numeric evidence 与 validation contributor。**

---

## 7.3 设计立场

`docs/.trash/plan/Octave-Ext.md` 提出的是更大的 AI-native 科学计算平台愿景，包含 Live Workspace Engine、Scientific Context Engine、多 Agent 编排、OpenModelica 块图仿真、HPC 集群集成等方向。Octave extension 不应一次性吞下整个愿景，而应把首版范围收敛到 MHE 能稳定治理的 Octave worker 控制面。

首版设计立场：

- **CLI-first**：以 `octave-cli` 非交互执行为主，不做 GUI / IDE / Live Editor；
- **wrapper-first**：由 compiler 生成受控 wrapper `.m`，避免任意 shell 命令；
- **workspace-first**：所有输入、脚本、输出、日志、证据都落在明确工作目录；
- **evidence-first**：return code 只是必要条件，不是成功的充分条件；
- **numeric-validation-first**：输出变量、shape、容差、NaN/Inf、warning 都进入验证；
- **package-aware**：Octave package 是环境事实，不假设所有 MATLAB toolbox 等价能力存在；
- **promotion-readable**：validator 产出 MHE 可消费的 `ValidationIssue`、`blocks_promotion`、`ScoredEvidence` 与 stable `evidence_refs`；
- **no MATLAB parity claim**：不承诺 Simulink、App Designer、commercial toolbox、GPU toolbox 或完整 MATLAB 兼容性。

---

## 7.4 首版支持边界

### 建议 application family

- `script_run`：运行受控 `.m` 脚本或由 spec 生成的 wrapper；
- `function_eval`：调用指定函数并保存结构化返回值；
- `numeric_benchmark`：运行小型数值 benchmark，输出指标与容差判断。

注：`package_probe` 不作为独立 task family，而是 `OctaveEnvironmentComponent` 的方法，用于环境 readiness 探测。Figure 输出通过 `OctaveOutputSpec` 的 output kind 支持，不单独设 `plot_export` family。

### 首版明确不支持

- 任意 shell command execution；
- GUI Octave、交互式 REPL、notebook kernel 常驻会话；
- MATLAB proprietary toolbox、Simulink、App Designer、Live Editor；
- 对所有 Octave packages 的 blanket support；
- 自动把任意历史 MATLAB 工程转换为 Octave 工程；
- 在 extension 内部重建 MHE session / audit / graph promotion 系统；
- 未经白名单的网络访问、文件系统越界访问或动态 package 安装。

---

## 7.5 组件链

```text
OctaveGateway
  -> OctaveEnvironmentProbe
    -> OctaveScriptCompiler
      -> OctaveExecutor
        -> OctaveValidator
          -> OctaveEvidenceBundle
            -> OctaveEvidencePolicy
```

### Gateway (`octave_gateway.primary`)

- 接收 `OctaveExperimentSpec`；
- 选择 family：`script_run` / `function_eval` / `numeric_benchmark`；
- 拒绝越界模式，例如任意 shell、GUI、未声明 package、未声明 output schema；
- 提供 `issue_task(...)`、`compile_experiment(...)`、`run_baseline(...)` 便捷入口；
- `declare_interface()` 声明 slot、output contract 与 capability。

Gateway manifest 示例（`gateway.json`）：

```json
{
  "name": "octave_gateway",
  "version": "0.1.0",
  "kind": "custom",
  "entry": "metaharness_ext.octave.gateway:OctaveGatewayComponent",
  "harness_version": ">=0.1.0",
  "contracts": {
    "inputs": [{"name": "experiment_spec", "type": "OctaveExperimentSpec", "required": true}],
    "outputs": [{"name": "task", "type": "OctaveExperimentSpec", "mode": "sync"}],
    "provides": [{"name": "octave.task.issue"}],
    "requires": [{"name": "octave.environment.probe"}, {"name": "octave.script.compile"}],
    "slots": [{"slot": "octave_gateway.primary"}]
  },
  "safety": {"protected": false, "mutability": "mutable", "hot_swap": true},
  "policy": {"sandbox": {"tier": "standard"}},
  "provides": ["octave.task.issue"],
  "requires": ["octave.environment.probe", "octave.script.compile"],
  "deps": {"capabilities": ["octave.environment.probe", "octave.script.compile"]},
  "bins": ["octave-cli"],
  "state_schema_version": 1
}
```

注：`kind` 使用 `"custom"`（`ComponentType` enum = `CORE | TEMPLATE | META | GOVERNANCE | CUSTOM`，无 `"gateway"` 类型）。`safety.hot_swap` 为 `bool`（非 string）。Sandbox tier 位于 `policy.sandbox.tier`。

### Environment Probe (`octave_environment.primary`)

- 检查 `octave-cli` 是否存在；
- 运行 `octave-cli --version` 获取版本；
- 探测 `pkg list` 或受控 probe 脚本，记录 package/version；
- 检查 workspace 写入能力；
- 可选记录 BLAS/LAPACK、OpenMP、graphics backend 等事实；
- 产出 `OctaveEnvironmentReport`，包含 missing prerequisites、messages、warnings、`blocks_promotion` 和 environment evidence refs。

### Script Compiler (`octave_script_compiler.primary`)

- 将 `OctaveExperimentSpec` 编译为 `OctaveRunPlan`；
- 生成 deterministic wrapper `.m`；
- staging 输入资产：`.m`、`.mat`、CSV、JSON、文本数据；
- 声明 expected outputs：变量名、文件名、schema、shape、dtype、数值容差；
- 注入 machine-readable status 输出，例如 `mhe_status.txt`（save -text 格式）；
- 对 inline source、function call、path allowlist、package load 进行约束。

Wrapper 的典型结构：

```text
set up paths and packages
load declared inputs
run controlled script/function
validate expected variables exist
save outputs to declared files
write mhe_status.txt
```

### Executor (`octave_executor.primary`)

- 在 `.runs/octave/<task_id>/<run_id>/` 或 runtime-injected storage 下准备 workspace；
- 写入 wrapper、输入文件和 manifest-like execution metadata；
- 执行 `octave-cli --no-gui --quiet --no-init-file <wrapper.m>`；
- 控制 timeout、working directory、environment variables；
- 捕获 stdout/stderr；
- 收集 `.mat`、JSON、CSV、figures、logs、status 文件；
- 产出 `OctaveRunArtifact`，区分 `completed`、`failed`、`timeout`、`unavailable`。

### Validator (`octave_validator.primary`) — protected candidate

- 区分 `environment_invalid` / `compile_failed` / `runtime_failed` / `output_missing` / `output_parse_failed` / `numeric_validation_failed` / `executed`；
- 检查 return code、status file、expected output files；
- 解析 JSON / CSV / `.mat` 元数据或变量摘要；
- 对 expected variables 做存在性、shape、dtype、NaN/Inf 和 tolerance 检查；
- 对 warning 进行分类：benign / suspicious / blocking；
- 生成 `OctaveValidationReport`，包含 `ValidationIssue`、`blocks_promotion`、`governance_state`、`ScoredEvidence`、`evidence_refs`；
- 角色定位为 evidence contributor，不直接执行 graph promotion。

### Evidence Policy (`OctaveEvidencePolicy` helper)

- 基于 environment、artifact、validation 和 output completeness 生成 `ready` / `defer` / `blocked`；
- 默认策略建议：
  - environment missing 或 package missing：`blocked`；
  - run completed 但缺少结构化输出：`defer` 或 `blocked`；
  - numeric tolerance failed：`blocked`；
  - warning suspicious 但核心输出完整：`defer`；
  - all checks passed 且 evidence complete：`ready`。

### 组件生命周期：`activate()` / `deactivate()`

每个组件在 `activate(self, runtime: ComponentRuntime)` 中将 `self._runtime = runtime` 存储 runtime 引用（与 ABACUS 模式一致）。Executor 使用 `runtime.storage_path` 解析 workspace 根路径（`.runs/octave/...`）。`deactivate()` 中进行组件级资源清理（关闭未完成 subprocess、移除临时文件等）。

---

## 7.6 Contracts 设计

### 核心类型

| 类型 | 角色 | 阶段 |
|---|---|---|
| `OctaveExperimentSpec` | 用户任务入口 | Spec |
| `OctaveExecutableSpec` | `octave-cli`、timeout、env、版本要求 | Spec |
| `OctaveWorkspaceSpec` | 工作目录、输入资产、输出目录、清理策略 | Spec |
| `OctaveScriptSpec` | 脚本 / 函数 / wrapper 生成规则 | Spec |
| `OctavePackageSpec` | package 名称、版本约束、required/optional | Spec |
| `OctaveInputAssetSpec` | 输入数据文件、变量名、加载方式 | Spec |
| `OctaveOutputSpec` | 预期输出文件/变量/schema/容差 | Spec |
| `OctaveRunPlan` | 编译后的 wrapper、argv、workspace、expected outputs | Plan |
| `OctaveEnvironmentReport` | binary/package/workspace readiness | Report |
| `OctaveRunArtifact` | stdout/stderr、return code、output files、diagnostics | Artifact |
| `OctaveValidationReport` | 验证状态、issues、metrics、promotion hints | Report |
| `OctaveEvidenceBundle` | environment + plan + artifact + validation evidence | Bundle |
| `OctaveStudySpec` | 后续参数扫描 / benchmark 研究 | Study |
| `OctaveStudyReport` | study trials、推荐参数、收敛证据 | Study |

### `OctaveRunPlan` 与 `RunPlanProtocol` 字段映射

`RunPlanProtocol`（`sdk/execution.py:74`）定义平台级 run plan 协议。`OctaveRunPlan` 需按如下映射对接：

| `OctaveRunPlan` 字段 | `RunPlanProtocol` 字段 | 说明 |
|---|---|---|
| `plan_id: str` | `plan_id` | 直接映射 |
| `task_id: str` | `experiment_ref` | 引用发起 task |
| `executable: OctaveExecutableSpec` | `target_backend` | 映射为 `octave-cli` backend 标识 |
| `execution_params: dict` | `execution_params` | 直接映射 |
| `workspace_dir: str` | （注入 `execution_params`） | workspace 路径经由 `execution_params` 传递 |

### 关键字段建议

`OctaveExperimentSpec`：

- `task_id: str`
- `family: Literal["script_run", "function_eval", "numeric_benchmark"]`
- `executable: OctaveExecutableSpec`
- `script: OctaveScriptSpec`
- `workspace: OctaveWorkspaceSpec | None`
- `packages: list[OctavePackageSpec]`
- `inputs: list[OctaveInputAssetSpec]`
- `expected_outputs: list[OctaveOutputSpec]`
- `parameters: dict[str, Any]`
- `promotion_metadata: dict[str, Any]`
- `graph_metadata: dict[str, Any]`

`OctaveRunArtifact`：

- `run_id`、`task_id`、`plan_ref`
- `status`、`return_code`、`terminal_error_type`
- `working_directory`
- `wrapper_files`、`input_files`、`output_files`、`figure_files`、`log_files`
- `stdout_path`、`stderr_path`、`status_path`
- `summary_metrics`
- `warnings`
- `evidence_refs`
- `scored_evidence`

`OctaveValidationReport`：

- `passed`
- `status`
- `issues: list[ValidationIssue]`
- `blocks_promotion`
- `governance_state`
- `missing_evidence`
- `numeric_metrics`
- `package_facts`
- `evidence_refs`
- `scored_evidence`

注：`blocks_promotion` 在 report 层级是聚合值 `any(issue.blocks_promotion for issue in issues)`，与 `ValidationIssue.blocks_promotion`（单个 issue 级别，定义于 `core/models.py`）和 ABACUS 的 `abacus/validator.py:277` 模式一致。`governance_state` 同理为衍生状态，由 evidence policy 根据所有 issue 综合判定。

---

## 7.7 包结构建议

```text
MHE/src/metaharness_ext/octave/
├── __init__.py
├── capabilities.py
├── slots.py
├── types.py
├── contracts.py
├── gateway.py
├── environment.py
├── script_compiler.py
├── executor.py
├── validator.py
├── evidence.py
├── policy.py
├── study.py
├── workspace.py
├── manifest.json
├── gateway.json
├── environment.json
├── script_compiler.json
├── executor.json
└── validator.json
```

配套资产建议：

```text
MHE/examples/manifests/octave/
MHE/examples/graphs/octave-minimal.xml
MHE/tests/test_metaharness_octave_contracts.py
MHE/tests/test_metaharness_octave_manifest.py
MHE/tests/test_metaharness_octave_compiler.py
MHE/tests/test_metaharness_octave_environment_executor.py
MHE/tests/test_metaharness_octave_validator_policy_study.py
MHE/tests/test_metaharness_octave_pipeline.py
MHE/docs/wiki/meta-harness-engineer/octave-engine-wiki/
```

---

## 7.8 外部依赖策略

### 必需运行时前提

| 依赖 | 用途 | 检测位置 |
|---|---|---|
| `octave-cli` | 非交互执行 Octave 脚本 | Environment probe |
| 可写 workspace | 输入/输出/日志/证据落盘 | Environment probe / Executor |

### 可选 package

| Package | 典型用途 | 策略 |
|---|---|---|
| `io` | 表格、Excel/CSV 等数据交换 | required/optional by spec |
| `statistics` | 统计分析 | required/optional by spec |
| `signal` | 信号处理 | required/optional by spec |
| `control` | 控制系统 | required/optional by spec |
| `optim` | 优化 | required/optional by spec |
| `symbolic` | 符号计算 | optional, version-sensitive |
| `image` | 图像处理 | optional |

首版不要在 executor 中自动安装 package。缺失 package 应进入 environment report 和 validation issue，由用户或外部环境管理解决。

---

## 7.9 安全与治理

Octave extension 必须把“运行脚本”视为高风险边界，而不是普通函数调用。

首版建议策略：

- 默认只允许在 extension-managed workspace 内读写；
- 输入资产必须显式声明；
- output files 必须显式声明或匹配受限 pattern；
- 安全依赖 OS 级隔离（MHE SandboxTier）；静态脚本扫描（`system()`/`unix()`/`!cmd` 检测）作为 future hardening 方向（见 7.13 开放问题）；
- 不允许未声明网络访问；
- 不在 extension 内保存 credentials；
- `OctaveValidatorComponent` 建议设为 protected；
- manifest 中显式声明 sandbox、credentials 和 workspace-write policy；
- 所有 run artifact 都要能追溯到 plan、script hash、input asset hash 与 output hash。

与 MHE core 的集成点：

- 使用 `ComponentRuntime.storage_path` 定位 `.runs`；
- 使用 `RuntimeServices.artifact_store` 记录 run/validation/evidence snapshot；
- 使用 `audit_log` 和 `provenance_graph` 连接 task、plan、artifact、validation；
- 对长时间执行或 HPC 后端，后续对齐 `ExecutionLifecycleService`；
- 对 resource-sensitive 任务，后续接入 `resource_quota`。

---

## 7.10 与 AI-native 科学计算平台愿景的关系

`Octave-Ext.md` 中的 AI-native 平台愿景可拆成三层：

1. **Octave worker 层**：本蓝图覆盖。负责可控 Octave 执行、证据与验证；
2. **Scientific Context Engine 层**：后续扩展。可在 spec 编译前增加量纲检查、误差传播、方法推荐；
3. **Live Workspace / Multi-Agent / HPC 层**：后续平台能力。可通过 MHE runtime service、session recovery、BrainProvider、ExecutionLifecycleService 和外部 scheduler adapter 对接。

建议不要把首版 Octave extension 命名为“MATLAB 替代平台”。更准确的定位是：

> MHE-managed Octave scientific-computing worker, with a path toward AI-native MATLAB-like workflows.

---

## 7.11 测试策略

### 默认测试层：不依赖真实 Octave

- contracts Pydantic validation；
- manifest static validation；
- gateway family/mode dispatch；
- environment missing binary / missing package mocked tests；
- compiler wrapper generation snapshot tests；
- executor subprocess mocked tests；
- validator JSON/CSV/status parsing tests；
- warning classification 与 `blocks_promotion` tests；
- evidence refs / scored evidence / governance state tests。

### 可选真实 Octave smoke（future gated）

当前默认测试全部 mock 或绕过真实 `octave-cli`，因此不注册 `octave` pytest marker。后续若增加真实 smoke，可再引入显式 marker 与自动 skip 逻辑。

候选 smoke 场景：

- minimal script：`x = 1 + 1`，保存 JSON / MAT 输出；
- function eval：调用受控函数并验证变量；
- package probe：检测已安装 package；
- numeric tolerance：计算线性代数 / ODE 小例子并校验容差；
- plot export：生成 PNG/PDF 并验证文件存在。

### 推荐命令

```bash
python -m pytest tests/test_metaharness_octave_*.py -q
ruff check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
ruff format --check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
```

---

## 7.12 阶段路线图

### Phase 0：Design baseline

- 创建 blueprint、roadmap、octave-engine-wiki skeleton；
- 冻结首版 family、contracts、manifest slot/capability；
- 明确不支持 MATLAB parity / Simulink / GUI。

### Phase 1：Typed contracts + compiler

- 实现 contracts、slots、capabilities、manifest；
- 实现 deterministic wrapper compiler；
- 实现 gateway skeleton（slot/capability 声明、`declare_interface()`、基本 dispatch）；
- 增加 compiler / contract / manifest tests。

### Phase 2：Environment + executor

- 实现 `octave-cli` 与 package probe；
- 实现 workspace staging 和 mocked subprocess executor；
- 所有输出写入 `.runs/octave/...` 或 runtime storage；
- 增加 missing binary、timeout、nonzero return tests。

### Phase 3：Validator + evidence + policy

- 实现 output schema、numeric tolerance、warning classification；
- 产出 MHE-compatible `ValidationIssue`、`ScoredEvidence`、`evidence_refs`；
- 增加 evidence bundle / policy / governance tests。

### Phase 4：Integration + minimal demo

- 实现 `run_baseline(...)`；
- 增加 graph example、manifest example、minimal demo；
- 增加可选真实 Octave smoke。

### Phase 5：Scientific workflow expansion（v2 alignment）

Phase 5 进入 v2：在稳定 Octave worker 之上叠加 scientific workflow substrate。当前已完成默认测试覆盖的 v2 prototype；真实 SLURM/K8s 后端仍保持 gated/dry-run。完整设计见 `docs/wiki/meta-harness-engineer/octave-engine-wiki/02-v2-alignment.md`。

#### Phase 5a：Study Component

- 实现 `OctaveStudyComponent`、`OctaveStudySpec`、`OctaveStudyReport`；
- 支持 grid parameter sweep、metric extraction、best-trial recommendation；
- 默认测试使用 mocked compiler/executor/validator，不依赖真实 Octave。

#### Phase 5b：Governance Adapter + Evidence Pipeline

- 增加 `OctaveGovernanceAdapter`，按 DeepMD/QCompute pattern 构建 core validation report、candidate record 和 session events；
- 通过可选 runtime services 对接 artifact store、audit log 与 provenance graph；
- 将 study trial evidence 纳入 graph promotion 可读结构。

#### Phase 5c：Scientific Context Adapter

- 增强 `OctaveScientificContextAdapter` 的 pre-compile 与 post-validation hooks；
- 激活 unit、uncertainty、method hints、invariants 等 v2 contract 字段；
- 产出 `ValidationIssue` 与 `ScoredEvidence`，但不直接执行 promotion。

#### Phase 5d：Execution Lifecycle + Security

- 实现 `OctaveAsyncExecutor`，暴露 `ExecutionLifecycleService.run()` / `.cancel()` 可消费的 executor seam；
- 为 long-running 本地任务和后续真实 SLURM/K8s adapter 保留 dry-run backend contract；
- 增加 static script scanner、MAT file parser 和 artifact detector。

#### Phase 5e：Optimizer Bridge

- 实现 `OctaveDomainBrainProvider`，只对 typed whitelist fields 生成 `MutationProposal`；
- 通过 study observations 评估 proposal 与 validation evidence；
- 默认采用 deterministic untried-parameter strategy，Bayesian / LLM-guided 策略保留为后续增强。

---

## 7.13 风险与开放问题

| 风险 | 影响 | 缓解 |
|---|---|---|
| 任意脚本执行带来安全风险 | 高 | wrapper-first、workspace allowlist、sandbox policy、protected validator |
| MATLAB 兼容性被过度承诺 | 高 | 文档中明确 Octave worker，不承诺 toolbox/Simulink parity |
| package 生态差异 | 中 | package probe + required/optional spec + missing prerequisite report |
| 输出格式不稳定 | 中 | 首版优先 JSON/CSV/status file，`.mat` 作为增强 |
| 图像/plot backend 环境差异 | 中 | figure 输出通过 `OctaveOutputSpec` 支持，真实 smoke gated |
| 长时间任务阻塞 | 中 | `OctaveAsyncExecutor` + dry-run scheduler seam；真实集群执行 gated |
| 数值结果平台差异 | 中 | 容差、BLAS/LAPACK facts、seed、environment evidence |

开放问题：

- Live Workspace 是否应作为 Octave extension 内部能力，还是作为更上层 MHE scientific workspace service？
- 真实 HPC/SLURM 执行如何在本地 dry-run scheduler contract 基础上进行 gated submit/poll/collect？
- Scientific Context Engine 是否需要引入真实 pint/uncertainties 依赖，还是继续保持轻量内置检查？

---

## 7.14 首版完成判据

首版 Octave extension 可被称为 MVP 的条件：

- `OctaveExperimentSpec -> OctaveRunPlan -> OctaveRunArtifact -> OctaveValidationReport` 全链路可运行；
- 默认测试不依赖真实 Octave；
- 真实 `octave-cli` smoke gated 且自动 skip；
- 所有生成文件默认写入 `.runs/`；
- validator 能区分环境、编译、运行、输出缺失、数值失败和成功执行；
- validation report 包含 `blocks_promotion`、`ValidationIssue`、`ScoredEvidence`、`evidence_refs`；
- blueprint、roadmap、wiki、manifest、tests 与实现边界一致；
- 文档不声称 MATLAB / Simulink / GUI / toolbox 完整替代。
