# Octave MHE Extension — 设计方案

> 状态：proposal | 目标 package：`metaharness_ext.octave`
> 参考：`docs/.trash/plan/Octave-Ext.md`、`blueprint/07-octave-extension-blueprint.md`、MHE 现有 extension wiki（JEDI / DeepMD / ABACUS / QCompute）、Meta-Harness wiki（01–10）

## 1. 定位与目标

### 1.1 Octave 是什么

GNU Octave 是一门面向数值计算的高级解释型语言，语法与 MATLAB 高度兼容，覆盖线性代数、ODE/PDE 求解、信号处理、统计分析、优化、绘图等科学计算核心场景。它的稳定运行入口是 `octave-cli`，通过 `.m` 脚本或函数文件驱动计算，产出数值结果、`.mat` 数据文件和图形输出。

### 1.2 MHE 扩展的目标

`metaharness_ext.octave` 的目标，是把 GNU Octave 作为一种**受控、可声明、可验证、可审计**的科学计算执行 worker 接入 MHE。核心价值：

1. 复用 Octave/MATLAB-like 脚本生态，降低已有科研脚本迁移成本；
2. 将脚本、函数、输入数据、package 依赖、数值输出和图像产物显式建模为 typed contracts；
3. 用 MHE 的 component graph、session、provenance、policy、evidence 和 promotion 语义治理科学计算任务；
4. 用可测试、可复现、可回滚的方式替代"手动打开 Octave/MATLAB 跑脚本并人工检查结果"的非结构化流程；
5. 为后续 AI-native 科学计算平台中的 Live Workspace、Scientific Context Engine、多 Agent 编排与 HPC 集成保留稳定扩展面。

Octave 的稳定运行模型：

```text
typed spec + input assets + package requirements
  -> generated wrapper .m + workspace layout
  -> octave-cli --no-gui --quiet --no-init-file
  -> logs + .mat / JSON / CSV / figures
  -> numeric validation + evidence bundle + policy handoff
```

### 1.3 与 AI-native 科学计算平台愿景的关系

`docs/.trash/plan/Octave-Ext.md` 提出了一个六层 AI-native 科学计算平台（用户交互层 → Live Workspace Engine → Scientific Context Engine → Agent 编排层 → 专业科学 Agent 层 → 块图仿真引擎）作为 MATLAB 替代方案。Octave MHE 扩展不应一次性吞下整个愿景，而应把首版范围收敛到 MHE 能稳定治理的 **Octave worker 控制面**。

v1/v2/v3 拆解：

| 层次 | 内容 | 本扩展覆盖 |
|------|------|------------|
| **v1 Octave worker** | 可控 Octave 执行、证据与验证 | 首版覆盖，保持 deterministic wrapper + typed validation |
| **v2 Scientific workflow substrate** | Scientific Context Adapter、sessionized study、execution lifecycle、governance/optimizer bridge | `02-v2-alignment.md` 详细设计 |
| **v3 Live Workspace / Multi-Agent / HPC platform** | 持久变量空间、多 Agent 协同、生产级集群调度、Notebook/UI | 后续平台能力，通过 MHE runtime service、BrainProvider、ExecutionLifecycleService 对接 |

首版定位不是"MATLAB 替代平台"，而是：

> MHE-managed Octave scientific-computing worker, with a path toward v2 AI-native scientific workflows.

---

## 2. 设计立场与首版边界

### 2.1 设计立场

- **CLI-first**：以 `octave-cli` 非交互执行为主，不做 GUI / IDE / Live Editor
- **wrapper-first**：由 compiler 生成受控 wrapper `.m`，避免透传任意命令/脚本
- **workspace-first**：所有输入、脚本、输出、日志、证据都落在明确的受控工作目录
- **evidence-first**：return code 只是必要条件，不是成功的充分条件
- **numeric-validation-first**：输出变量、shape、dtype、容差、NaN/Inf、warning 都进入验证
- **package-aware**：Octave package 是环境事实，不假设所有 MATLAB toolbox 等价能力存在
- **promotion-readable**：validator 产出 MHE 可消费的 `ValidationIssue`、`blocks_promotion`、`ScoredEvidence`
- **no MATLAB parity claim**：不承诺 Simulink、App Designer、commercial toolbox 或完整 MATLAB 兼容性

### 2.2 首版 application family

| Family | 说明 |
|--------|------|
| `script_run` | 运行受控 `.m` 脚本或由 spec 生成的 wrapper；图形输出通过 `OctaveOutputSpec(kind="figure")` 支持 |
| `function_eval` | 调用指定函数并保存结构化返回值 |
| `numeric_benchmark` | 运行小型数值 benchmark，输出指标与容差判断 |

package 探测通过 `OctaveEnvironmentProbe.probe()` 组件方法提供，不作为独立 task family。

### 2.3 首版明确不支持

- 任意 shell command execution
- GUI Octave、交互式 REPL、notebook kernel 常驻会话
- MATLAB proprietary toolbox、Simulink、App Designer、Live Editor
- 对所有 Octave packages 的 blanket support
- 自动把任意历史 MATLAB 工程转换为 Octave 工程
- 在 extension 内部重建 MHE session / audit / graph promotion 系统
- 未经白名单的网络访问、文件系统越界访问或动态 package 安装

---

## 3. MHE 平台层与扩展层职责划分

### 3.1 MHE 平台层负责

- manifest discovery / component boot
- graph candidate staging / semantic validation
- graph version commit / rollback
- session event、audit log、artifact snapshot、provenance graph
- protected-component enforcement
- policy-gated promotion authority
- runtime recovery、execution lifecycle service、resource quota
- BrainProvider / optimizer / mutation proposal 的平台级入口

### 3.2 Octave 扩展层负责

- Octave task / workspace / script / function / package / output 的 typed spec
- Octave environment probe 与 package discovery
- wrapper `.m` 生成、input asset staging、output schema 编译
- `octave-cli` 执行、timeout、stdout/stderr capture
- `.mat` / JSON / CSV / figure / log artifact discovery
- numeric tolerance、expected variables、warning policy、evidence completeness validation
- domain-local policy hints 和 governance-shaped evidence bundle
- 后续 study / mutation 对 typed whitelist fields 的受控扫描

核心原则：**MHE = platform promotion / session / policy / provenance authority；Octave extension = Octave workflow、workspace、numeric evidence 与 validation contributor。**

---

## 4. 架构总览

### 4.1 组件链

```text
OctaveGateway
  -> OctaveEnvironmentProbe
    -> OctaveScriptCompiler
      -> OctaveExecutor
        -> OctaveValidator
          (-> OctaveEvidencePolicy)
```

斜体部分为可选的 policy helper，负责将 validation report 映射为 `ready / defer / blocked` 建议。

### 4.2 组件职责

#### OctaveGateway (`octave_gateway.primary`)

- 接收 `OctaveExperimentSpec`
- 选择 family：`script_run` / `function_eval` / `numeric_benchmark`
- 拒绝越界模式（任意 shell、GUI、未声明 package、未声明 output schema）
- 提供 `issue_task(...)`、`compile_experiment(...)`、`run_baseline(...)` 便捷入口
- `declare_interface()` 声明 slot、output contract 与 capability

**不负责**：直接构造命令行细节、解析 Octave warning、直接判定 scientific success

#### OctaveEnvironmentProbe (`octave_environment.primary`)

- 检查 `octave-cli` 是否存在
- 运行 `octave-cli --version` 获取版本
- 探测 `pkg list` 或受控 probe 脚本，记录 package/version
- 检查 workspace 写入能力
- 可选记录 BLAS/LAPACK、OpenMP、graphics backend（`graphics_toolkit`）等事实
- 产出 `OctaveEnvironmentReport`

**不负责**：自动修复环境、隐式安装 package、编译脚本

#### OctaveScriptCompiler (`octave_script_compiler.primary`)

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

**不负责**：接收任意脚本透传、运行外部进程、根据 stderr 反推配置逻辑

#### OctaveExecutor (`octave_executor.primary`)

- 在 `.runs/octave/<task_id>/<run_id>/` 或 runtime-injected storage 下准备 workspace
- 写入 wrapper、输入文件和 manifest-like execution metadata
- 执行 `octave-cli --no-gui --quiet --no-init-file <wrapper.m>`
- 控制 timeout、working directory、environment variables
- 捕获 stdout/stderr
- 收集 `.mat`、JSON、CSV、figures、logs、status 文件
- 产出 `OctaveRunArtifact`，区分 `completed`、`failed`、`timeout`、`unavailable`

**不负责**：理解业务级脚本语义、解释 scientific result、管理跨 run 的 workspace 持久化

#### OctaveValidator (`octave_validator.primary`) — protected candidate

- 区分 `environment_invalid` / `compile_failed` / `runtime_failed` / `output_missing` / `output_parse_failed` / `numeric_validation_failed` / `executed`
- 检查 return code、status file、expected output files
- 解析 JSON / CSV / `.mat` 元数据或变量摘要
- 对 expected variables 做存在性、shape、dtype、NaN/Inf 和 tolerance 检查
- 对 warning 进行分类：benign / suspicious / blocking
- 生成 `OctaveValidationReport`，包含 `ValidationIssue`、`blocks_promotion`、`governance_state`、`ScoredEvidence`、`evidence_refs`

**不负责**：再次编译脚本、直接运行 executable、执行 graph promotion

#### OctaveEvidencePolicy（helper）

- 基于 environment、artifact、validation 和 output completeness 生成 `ready` / `defer` / `blocked`
- 默认策略建议：
  - environment missing 或 package missing：`blocked`
  - run completed 但缺少结构化输出：`defer` 或 `blocked`
  - numeric tolerance failed：`blocked`
  - warning suspicious 但核心输出完整：`defer`
  - all checks passed 且 evidence complete：`ready`

### 4.3 架构边界（不可违反）

- gateway 不承担 compiler/executor 细节
- compiler 不退化为脚本透传
- executor 不理解 family-specific 脚本结构
- validator 不回头补做环境探测或配置编译
- study/mutation 不绕过 typed spec 直接改最终脚本

这些边界一旦混掉，后续扩展到更多 application family 和 Scientific Context Engine 会迅速失控。

### 4.4 MHE 组件图装配视角

每个组件通过 `HarnessComponent.declare_interface()` 声明其 slot、contracts、capabilities：

```text
Slot bindings:
  octave_gateway.primary       -> OctaveGateway
  octave_environment.primary   -> OctaveEnvironmentProbe
  octave_script_compiler.primary -> OctaveScriptCompiler
  octave_executor.primary      -> OctaveExecutor
  octave_validator.primary     -> OctaveValidator (protected)

Key capabilities:
  octave.task.issue
  octave.environment.probe
  octave.script.compile
  octave.execute.run
  octave.validate.report
  octave.evidence.bundle
```

ConnectionEngine 基于 contracts 连通组件：gateway 输出 spec → environment probe 输出 report → compiler 输出 plan → executor 输出 artifact → validator 输出 report → evidence bundle。

---

## 5. Contracts 与数据模型

### 5.1 核心类型总览

| 类型 | 角色 | 所属阶段 |
|------|------|----------|
| `OctaveExperimentSpec` | 用户任务入口 | Spec |
| `OctaveExecutableSpec` | `octave-cli`、timeout、env、版本要求 | Spec |
| `OctaveWorkspaceSpec` | 工作目录、输入资产、输出目录、清理策略 | Spec |
| `OctaveScriptSpec` | 脚本/函数/wrapper 生成规则 | Spec |
| `OctavePackageSpec` | package 名称、版本约束、required/optional | Spec |
| `OctaveInputAssetSpec` | 输入数据文件、变量名、加载方式 | Spec |
| `OctaveOutputSpec` | 预期输出文件/变量/schema/容差 | Spec |
| `OctaveRunPlan` | 编译后的 wrapper、argv、workspace、expected outputs | Plan |
| `OctaveEnvironmentReport` | binary/package/workspace readiness | Report |
| `OctaveRunArtifact` | stdout/stderr、return code、output files、diagnostics | Artifact |
| `OctaveValidationReport` | 验证状态、issues、metrics、promotion hints | Report |
| `OctaveEvidenceBundle` | environment + plan + artifact + validation evidence | Bundle |
| `OctaveStudySpec` | 后续参数扫描/benchmark 研究 | Study |
| `OctaveStudyReport` | study trials、推荐参数、收敛证据 | Study |

### 5.2 `OctaveExperimentSpec` 关键字段

```text
task_id: str
family: "script_run" | "function_eval" | "numeric_benchmark"
executable: OctaveExecutableSpec
script: OctaveScriptSpec
workspace: OctaveWorkspaceSpec | None
packages: list[OctavePackageSpec]
inputs: list[OctaveInputAssetSpec]
expected_outputs: list[OctaveOutputSpec]
parameters: dict[str, Any]
promotion_metadata: dict[str, Any]
graph_metadata: dict[str, Any]
```

### 5.3 `OctaveRunArtifact` 关键字段

```text
run_id, task_id, plan_ref
status: "completed" | "failed" | "timeout" | "unavailable"
return_code, terminal_error_type
working_directory
wrapper_files, input_files, output_files, figure_files, log_files
stdout_path, stderr_path, status_path (mhe_status.txt / mhe_status.json)
summary_metrics: dict
warnings: list[OctaveWarning]
evidence_refs: list[str]
scored_evidence: ScoredEvidence | None = None
```

### 5.4 `OctaveValidationReport` 关键字段

```text
passed: bool
status: "environment_invalid" | "compile_failed" | "runtime_failed"
      | "output_missing" | "output_parse_failed"
      | "numeric_validation_failed" | "executed"
issues: list[ValidationIssue]
blocks_promotion: bool  # aggregate: any(issue.blocks_promotion for issue in issues)
governance_state: Literal["ready", "defer", "blocked"]
missing_evidence: list[str]
numeric_metrics: dict  # tolerance checks, NaN/Inf counts
package_facts: dict     # resolved package versions
evidence_refs: list[str]
scored_evidence: ScoredEvidence | None = None
```

### 5.5 Contract 兼容性规则

与 MHE SDK 的 5 条静态规则对齐：

1. compiler 的 output contract 与 executor 的 input contract 必须兼容
2. executor 的 output contract 与 validator 的 input contract 必须兼容
3. 每个组件的 required input 必须能在图中被满足
4. component id 全局唯一
5. `octave_validator.primary` 作为 protected slot，不能被未授权实现覆盖

---

## 6. 执行管线

### 6.1 主链路

```text
┌─────────────────────────────────────────────────────────────┐
│  1. Gateway: 接收 spec，选择 family，拒绝越界模式            │
│     -> OctaveExperimentSpec                                  │
├─────────────────────────────────────────────────────────────┤
│  2. Environment Probe: 检测 octave-cli、packages、workspace  │
│     -> OctaveEnvironmentReport                               │
├─────────────────────────────────────────────────────────────┤
│  3. Script Compiler: spec -> wrapper .m + workspace staging  │
│     -> OctaveRunPlan                                         │
├─────────────────────────────────────────────────────────────┤
│  4. Executor: octave-cli --no-gui --quiet --no-init-file <wrapper.m>       │
│     -> OctaveRunArtifact (stdout/stderr/outputs/figures)     │
├─────────────────────────────────────────────────────────────┤
│  5. Validator: output schema + numeric tolerance + warnings  │
│     -> OctaveValidationReport                                │
├─────────────────────────────────────────────────────────────┤
│  6. Evidence Policy: report -> ready/defer/blocked           │
│     -> governance_state + blocks_promotion                   │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Wrapper `.m` 生成规则

Compiler 生成的 wrapper 必须 structural deterministic：同样的 spec 产生相同的逻辑结构（相同的路径、package load、执行和输出步骤），便于 hash、审计和回滚。元数据行（如 plan_id、task_id）可能因运行实例而异，不影响逻辑等价性。

```matlab
% --- Auto-generated by metaharness_ext.octave ---
% Plan: <plan_id>  Task: <task_id>

% 1. Paths and packages
addpath('/path/to/workspace');
pkg load statistics;   % only if declared in spec

% 2. Load inputs (only declared assets)
load('input_data.mat');  % -> variables a, b, c

% 3. Controlled execution
<inline_source | function_call>

% 4. Validate expected outputs exist
assert(exist('result', 'var'), 'mhe:missing_output', 'result not defined');

% 5. Save outputs (save -text is always available)
save('-text', 'output.txt', 'result');
save('-mat', 'output.mat', 'result');

% 5a. Optional JSON export if jsonencode is available (compile-time probe)
% if exist('jsonencode', 'builtin')
%   fid = fopen('output.json', 'w');
%   fputs(fid, jsonencode(struct('result', result)));
%   fclose(fid);
% endif

% 6. Write machine-readable status (using save -text)
mhe_status = struct('status', 'completed', 'plan_id', '<plan_id>', ...
    'outputs', {{'result'}}, 'warnings', {{}});
save('-text', 'mhe_status.txt', 'mhe_status');
```

### 6.3 Warning 分类策略

Executor 捕获的 stderr 和 Octave warning 按严重程度分类：

| 级别 | 示例 | 对 promotion 的影响 |
|------|------|---------------------|
| `benign` | `warning: division by zero (result set to Inf)` — 已知数值行为 | 不阻塞 |
| `suspicious` | `warning: load: variable 'x' not found` — 可能表示输入问题 | defer |
| `blocking` | `error: 'statistics' package not installed` — 环境不完整 | blocked |

### 6.4 数值验证规则

Validator 对 `OctaveOutputSpec` 中声明的每个 expected variable 执行：

1. 存在性：变量是否在输出中
2. Shape/dtype：维度与类型是否与声明一致
3. NaN/Inf 检查：是否包含非有限值（可配置为 blocking 或 warning）
4. 容差检查：`abs(actual - expected) <= atol + rtol * abs(expected)`
5. 相对误差：对接近零的值使用绝对容差为主

---

## 7. 环境与验证

### 7.1 Environment Probe 探测内容

| 探测项 | 方法 | 失败后果 |
|--------|------|----------|
| `octave-cli` 存在 | `shutil.which('octave-cli')` | blocking — 无法执行 |
| Octave 版本 | `octave-cli --version` | 可配置最低版本要求 |
| Package 可用性 | `pkg list` 或 probe 脚本 | 按 spec 中 required/optional 判定 |
| Workspace 可写 | 尝试创建临时文件 | blocking — 无法保存输出 |
| BLAS/LAPACK | `octave --eval "version -blas"` 等 | 记录到 environment facts |
| Graphics backend | `graphics_toolkit()`（仅当 spec 声明 figure 输出时探测） | 可选事实，不阻塞执行；`--no-gui` 下可能未初始化 |

### 7.2 Validation Report 状态机

```text
                    +---------------------+
                    | environment_invalid |
                    +---------------------+
                              |
                    +---------------------+
                    | compile_failed      |
                    +---------------------+
                              |
                    +---------------------+
                    | runtime_failed      |
                    +---------------------+
                              |
                    +---------------------+
                    | output_missing      |
                    +---------------------+
                              |
                    +---------------------+
                    | output_parse_failed |
                    +---------------------+
                              |
                    +---------------------+
                    | numeric_validation  |
                    | _failed             |
                    +---------------------+
                              |
                    +---------------------+
                    | executed (success)  |
                    +---------------------+
```

当多个 failure 同时存在时，取最先触发的状态（最早阶段优先）。

---

## 8. 安全与治理

### 8.1 安全边界

Octave extension 把"运行脚本"视为高风险边界。首版安全策略：

- 默认只允许在 extension-managed workspace 内读写
- 输入资产必须显式声明在 `OctaveInputAssetSpec` 中
- output files 必须显式声明或匹配受限 pattern
- 安全依赖 OS 级隔离（文件系统权限、容器、MHE SandboxTier）。对 `.m` 内容中 `system()`、`unix()`、`!cmd` 的静态扫描为后续加固项（见开放问题）
- 不允许未声明网络访问（`urlread`、`urlwrite`、`web` 等）
- 不在 extension 内保存 credentials
- `OctaveValidatorComponent` 设为 protected
- manifest 中显式声明 sandbox、credentials 和 workspace-write policy
- 所有 run artifact 都要能追溯到 plan、script hash、input asset hash 与 output hash

### 8.2 与 MHE 安全基础设施的集成

| MHE 基础设施 | Octave 扩展的用法 |
|-------------|-------------------|
| `ComponentRuntime.storage_path` | 定位 `.runs/octave/` 工作目录 |
| `RuntimeServices.artifact_store` | 记录 run/validation/evidence snapshot |
| `audit_log` | 连接 task、plan、artifact、validation event |
| `provenance_graph` | 追溯 script hash → input hash → output hash → validation |
| `sandbox_client` | 后续隔离执行环境 |
| `ExecutionLifecycleService` | 后续长时间执行和 HPC 后端 |
| `resource_quota` | 后续 resource-sensitive 任务 |

### 8.3 治理集成点

MHE 事件总线（`metaharness.core.event_bus`）定义 4 个 promotion 相关事件：

| 事件常量 | 用途 |
|---------|------|
| `BEFORE_COMMIT_GRAPH` | promotion 前最后一跳，扩展在此订阅 governance gate 逻辑 |
| `AFTER_COMMIT_GRAPH` | promotion 完成后触发，用于记录固化后的证据/审计 |
| `CANDIDATE_REJECTED` | 候选被拒绝时发布 |
| `CANDIDATE_DEFERRED` | 候选被延迟时发布 |

Octave 扩展的治理集成策略：

- **promotion gating**：validator 完成后，扩展订阅 `BEFORE_COMMIT_GRAPH` 检查 `blocks_promotion` 和 `governance_state`，产出 `ready`/`defer`/`blocked` 决策。
- **proposal pre-check**：在 gateway 的 `issue_task()` 方法内部调用 component-internal 检查，拒绝未声明 package / 任意 shell 的 spec。
- **environment / compiler / executor 阶段**：这些阶段不直接触发事件总线 hook，而是通过 component-internal 方法调用产出报告，由后续的 validator 和 policy 组件汇总为 governance decision。

---

## 9. 包结构与外部依赖

### 9.1 推荐包结构

```text
MHE/src/metaharness_ext/octave/
├── __init__.py
├── capabilities.py          # capability 常量
├── slots.py                 # slot 常量
├── types.py                 # 共享类型字面量
├── contracts.py             # Pydantic contracts
├── gateway.py               # OctaveGateway
├── environment.py           # OctaveEnvironmentProbe
├── script_compiler.py       # OctaveScriptCompiler
├── executor.py              # OctaveExecutor
├── validator.py             # OctaveValidator
├── evidence.py              # OctaveEvidenceBundle / OctaveEvidencePolicy
├── policy.py                # governance_state 判定
├── study.py                 # OctaveStudyComponent (Phase 5)
├── workspace.py             # workspace staging 工具
├── manifest.json            # extension manifest
├── gateway.json             # component manifests
├── environment.json
├── script_compiler.json
├── executor.json
└── validator.json
```

配套资产：

```text
MHE/examples/manifests/octave/
MHE/examples/graphs/octave-minimal.xml
MHE/tests/test_metaharness_octave_contracts.py
MHE/tests/test_metaharness_octave_manifest.py
MHE/tests/test_metaharness_octave_compiler.py
MHE/tests/test_metaharness_octave_environment_executor.py
MHE/tests/test_metaharness_octave_validator_policy_study.py
MHE/tests/test_metaharness_octave_pipeline.py
```

### 9.2 外部依赖策略

#### 必需运行时前提

| 依赖 | 用途 | 检测位置 |
|------|------|----------|
| `octave-cli` | 非交互执行 Octave 脚本 | Environment probe |
| 可写 workspace | 输入/输出/日志/证据落盘 | Environment probe / Executor |

#### 可选 Octave package（按需声明）

| Package | 典型用途 | 策略 |
|---------|---------|------|
| `io` | 表格、Excel/CSV 数据交换 | required/optional by spec |
| `statistics` | 统计分析 | required/optional by spec |
| `signal` | 信号处理 | required/optional by spec |
| `control` | 控制系统 | required/optional by spec |
| `optim` | 优化 | required/optional by spec |
| `symbolic` | 符号计算 | optional, version-sensitive |
| `image` | 图像处理 | optional |

**首版不在 executor 中自动安装 package。** 缺失 package 进入 environment report 和 validation issue，由用户或外部环境管理解决。

---

## 10. 与 v2 Scientific Context Adapter 的衔接

首版在 contracts 中预留 Scientific Context Engine 扩展点；v2 将这些字段收敛为 `OctaveScientificContextAdapter` 的 pre-compile 与 post-validation hooks。完整 v2 对齐方案见 `02-v2-alignment.md`。

### 10.1 量纲检查（预留）

`OctaveInputAssetSpec` 和 `OctaveOutputSpec` 保留 `unit: str | None` 字段。后续 compiler 可通过 pint/uncertainties 做量纲一致性验证：

```python
# 后续: Scientific Context Engine 接入点
class OctaveOutputSpec(BaseModel):
    variable: str
    unit: str | None = None        # "m/s^2", "eV/c^2", etc.
    tolerance: ToleranceSpec | None = None
```

### 10.2 数值方法推荐（预留）

`OctaveScriptSpec` 保留 `method_hints: dict[str, Any]` 字段，为后续自动选择数值方法（刚性/非刚性 ODE、稀疏/稠密求解器）留接口。

### 10.3 物理常数（预留）

`OctaveExperimentSpec.parameters` 字典中的物理常量（如 `h_bar`、`c_light`）可被后续 Scientific Context Engine 自动注入 CODATA/PDG 推荐值并标注数据来源。

---

## 11. Manifest 示例

```json
{
  "name": "octave_gateway",
  "version": "0.1.0",
  "kind": "custom",
  "entry": "metaharness_ext.octave.gateway:OctaveGatewayComponent",
  "harness_version": ">=0.1.0",
  "contracts": {
    "inputs": [
      {"name": "experiment_spec", "type": "OctaveExperimentSpec", "required": true}
    ],
    "outputs": [
      {"name": "task", "type": "OctaveExperimentSpec", "mode": "sync"}
    ],
    "events": [],
    "provides": [
      {"name": "octave.task.issue"}
    ],
    "requires": [
      {"name": "octave.environment.probe"},
      {"name": "octave.script.compile"}
    ],
    "slots": [
      {"slot": "octave_gateway.primary"}
    ]
  },
  "safety": {
    "protected": false,
    "mutability": "mutable",
    "hot_swap": true
  },
  "policy": {
    "sandbox": {
      "tier": "standard"
    }
  },
  "provides": ["octave.task.issue"],
  "requires": ["octave.environment.probe", "octave.script.compile"],
  "deps": {
    "components": [],
    "capabilities": ["octave.environment.probe", "octave.script.compile"]
  },
  "bins": ["octave-cli"],
  "state_schema_version": 1
}
```

Validator manifest 的 `safety.protected` 为 `true`。

---

## 12. 实施路线图

### Phase 0：Design baseline（当前）

- 完成 blueprint、roadmap、wiki skeleton
- 冻结首版 family、contracts、manifest slot/capability
- 明确不支持 MATLAB parity / Simulink / GUI

### Phase 1：Typed contracts + gateway + compiler

- 实现 contracts、slots、capabilities、manifest
- 实现 gateway skeleton（`issue_task`、`compile_experiment` 入口、family 分发）
- 实现 deterministic wrapper compiler
- gateway / compiler / contract / manifest tests

### Phase 2：Environment + executor

- 实现 `octave-cli` 与 package probe
- 实现 workspace staging 和 mocked subprocess executor
- 所有输出写入 `.runs/octave/...` 或 runtime storage
- missing binary、timeout、nonzero return tests

### Phase 3：Validator + evidence + policy

- 实现 output schema、numeric tolerance、warning classification
- 产出 MHE-compatible `ValidationIssue`、`ScoredEvidence`、`evidence_refs`
- evidence bundle / policy / governance tests

### Phase 4：Integration + minimal demo

- 实现 `run_baseline(...)` 全链路
- graph example、manifest example、minimal demo
- 可选真实 Octave smoke（future gated，当前默认测试 mock/avoid real `octave-cli`）

### Phase 5：Scientific workflow expansion（v2 alignment）

完整 v2 roadmap 见 `02-v2-alignment.md`。Phase 5 拆为以下独立子阶段：

- **Phase 5a Study Component**：`OctaveStudyComponent`、grid parameter sweep、metric extraction、best-trial recommendation
- **Phase 5b Governance Adapter + Evidence Pipeline**：candidate record、session events、artifact snapshot、provenance/audit recording
- **Phase 5c Scientific Context Adapter**：unit、uncertainty、method hints、invariants 的 pre-compile 与 post-validation hooks
- **Phase 5d Execution Lifecycle + Security**：`OctaveAsyncExecutor`、`ExecutionLifecycleService`、static scanner、MAT/artifact detector、scheduler seam
- **Phase 5e Optimizer Bridge**：`OctaveDomainBrainProvider`、`MutationProposal`、`OptimizerComponent`、`TripleConvergence`

### 阶段依赖

```text
Phase 0: Design baseline
    |
Phase 1: Typed contracts + gateway + compiler
    |
Phase 2: Environment + executor
    |
Phase 3: Validator + evidence + policy
    |
Phase 4: Integration + minimal demo
    |
Phase 5: Scientific workflow expansion (v2 alignment)
```

---

## 13. 测试策略

### 默认测试层（不依赖真实 Octave）

- contracts Pydantic validation
- manifest static validation
- gateway family/mode dispatch
- environment missing binary / missing package mocked tests
- compiler wrapper generation snapshot tests
- executor subprocess mocked tests
- validator JSON/CSV/status parsing tests
- warning classification 与 `blocks_promotion` tests
- evidence refs / scored evidence / governance state tests

### 可选真实 Octave smoke（future gated）

当前默认测试全部 mock 或绕过真实 `octave-cli`，因此不注册 `octave` pytest marker。后续若增加真实 smoke，可再引入显式 marker 与自动 skip 逻辑。

候选 smoke 场景：

- minimal script：`x = 1 + 1`，保存 JSON/MAT 输出
- function eval：调用受控函数并验证变量
- package probe：检测已安装 package
- numeric tolerance：线性代数/ODE 小例子并校验容差
- plot export：生成 PNG/PDF 并验证文件存在

### 推荐命令

```bash
python -m pytest tests/test_metaharness_octave_*.py -q
ruff check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
ruff format --check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
```

---

## 14. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 任意脚本执行带来安全风险 | 高 | wrapper-first、workspace allowlist、sandbox policy、protected validator |
| MATLAB 兼容性被过度承诺 | 高 | 文档明确 Octave worker，不承诺 toolbox/Simulink parity |
| package 生态差异 | 中 | package probe + required/optional spec + missing prerequisite report |
| 输出格式不稳定 | 中 | 首版优先 JSON/CSV/status file，`.mat` 作为增强 |
| 图像/plot backend 环境差异 | 中 | 图形输出通过 `OctaveOutputSpec(kind="figure")` 支持，真实 smoke gated |
| 长时间任务阻塞 | 中 | 后续接入 ExecutionLifecycleService 和 scheduler adapter |
| 数值结果平台差异 | 中 | 容差、BLAS/LAPACK facts、seed、environment evidence |

### 开放问题

- 首版是否需要支持 `.mat` 解析，还是只要求 wrapper 产出 JSON/CSV 摘要？
- 是否需要内置脚本静态扫描器来拒绝 `system(...)`、`unix(...)`、`!cmd` 等语义？
- Live Workspace（持久变量空间）是否应作为 Octave extension 内部能力，还是作为更上层 MHE scientific workspace service？
- HPC/SLURM 执行是否属于 Octave executor mode，还是单独 scheduler adapter？
- Scientific Context Engine 的量纲/误差传播应在 compiler 前（pre-compile check）还是 validator 后（post-hoc verification）接入？

---

## 15. 首版完成判据

首版 Octave extension 可称为 MVP 的条件：

- `OctaveExperimentSpec -> OctaveRunPlan -> OctaveRunArtifact -> OctaveValidationReport` 全链路可运行
- 默认测试不依赖真实 Octave
- 真实 `octave-cli` smoke gated 且自动 skip
- 所有生成文件默认写入 `.runs/` 或 runtime storage
- validator 能区分环境、编译、运行、输出缺失、数值失败和成功执行
- validation report 包含 `blocks_promotion`、`ValidationIssue`、`ScoredEvidence`、`evidence_refs`
- blueprint、roadmap、wiki、manifest、tests 与实现边界一致
- 文档不声称 MATLAB / Simulink / GUI / toolbox 完整替代

---

## 16. 对 Aeloon Plugin SDK 的映射

与 Aeloon Plugin SDK 的关系，沿袭 MHE extension 的标准映射：

| Aeloon Plugin SDK | Octave MHE Extension |
|-------------------|----------------------|
| `Plugin` 基类 | `HarnessComponent` 基类 |
| `aeloon.plugin.json` | 各组件 `harness.component.json` |
| `PluginAPI.register_command()` | `HarnessAPI.declare_input/output/event()` |
| `PluginRuntime` | `ComponentRuntime`（含 llm、sandbox_client、graph_reader 等） |
| `PluginRegistry` | `ComponentRegistry`（含 slot/capability 索引） |
| `HookDispatcher` (GUARD) | `PolicyLayer`（governance_state: ready/defer/blocked） |

核心差异仍与 MHE Component SDK 一致：注册粒度从 command/tool 变为 input/output/event port；通信从 AgentLoop 间接变为 ConnectionEngine 直连；生命周期从"加载即激活"变为 staged lifecycle（discover → validate → assemble → validate → commit）。

---

## 17. 参考文档

- `docs/.trash/plan/Octave-Ext.md` — AI-native 科学计算平台六层愿景
- `blueprint/07-octave-extension-blueprint.md` — 本设计的 blueprint 草案
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md` — MHE 概述
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/02-component-sdk.md` — Component SDK
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/10-extension-guide.md` — 扩展指南
- `docs/wiki/meta-harness-engineer/jedi-engine-wiki/` — JEDI extension 参考实现
- `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/` — DeepMD extension 参考实现
