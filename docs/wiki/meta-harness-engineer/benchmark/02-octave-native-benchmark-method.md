# 02. Octave-native Benchmark 测试方法报告

## 2.1 目标

本文具体展开方向 A：如何使用 GNU Octave 9.2.0 内置算例，测试 direct Claude CLI、deterministic `metaharness_ext.octave` pipeline baseline，以及 Claude CLI brain + Octave extension pipeline 的差异。

测试目标不是评估 Octave solver 本身是否正确；Octave 已通过自身 BIST 保证这些函数行为。这里评估的是三种 workflow 在相同 Octave-native 数值任务上的表现：

1. **Extension pipeline baseline**：不调用 LLM，直接使用 `metaharness_ext.octave` compile → execute → validate → evidence，验证确定性 extension pipeline 能力。
2. **Direct Claude CLI lane**：Claude CLI 读取 case spec，生成 `.m` 脚本，调用 `octave-cli`，整理 metrics、stdout/stderr 和 summary，不调用 extension。
3. **MHE Claude CLI agent lane**：benchmark driver 通过 Claude CLI brain adapter 生成 / 修复 candidate，再交给 `metaharness_ext.octave` 执行和验证。

核心问题：

- 三条 lane 是否都能稳定复现 Octave 内置参考解。
- Extension pipeline baseline 是否提供稳定的执行、验证和 evidence 基线。
- Claude CLI agent lane 是否能在使用同一 Claude CLI / model 的前提下，比 direct Claude CLI 更少出现路径、输出命名、验证、证据整理和批量执行错误。
- Claude CLI agent lane 的额外开销是否能被更好的可复现性、证据链和自动比较能力抵消。

## 2.2 测试资源来源

Octave source distribution：

```text
/home/myfile/distfiles/octave-9.2.0
```

首轮只使用不依赖额外外部库的 Octave-native cases，优先从以下文件的 BIST / demo 中抽取：

| 领域 | Source file | 用途 |
|---|---|---|
| ODE | `scripts/ode/ode45.m` | Van der Pol、`y'=-y` 收敛 / 端点误差 |
| ODE | `scripts/ode/ode23.m` | lower-order ODE solver 对比 |
| ODE / stiff | `scripts/ode/ode23s.m` | 简单 stiff / semi-stiff problem |
| Nonlinear solve | `scripts/optimization/fsolve.m` | 已知解非线性方程组、指数拟合 |
| Optimization | `scripts/optimization/fminunc.m` | Rosenbrock 最小化 |
| Constrained optimization | `scripts/optimization/sqp.m` | 约束优化 hard-coded reference |
| Linear algebra | `scripts/linear-algebra/expm.m` | 已知解析矩阵指数 |
| Polynomial | `scripts/polynomial/roots.m` | 已知多项式根 |
| Signal | `scripts/signal/sinc.m` | 已知函数值 |

条件性扩展 case 可后续加入，但不阻塞首轮：`ode15s` / `ode15i` 需要 SUNDIALS，`eigs` / `svds` 需要 ARPACK，`glpk` 需要 GLPK，`fftconv` 依赖 FFTW。

## 2.3 首轮 Case List

首轮建议固定 10 个 no-extra-library cases：

| Case ID | 领域 | Reference | 验证指标 |
|---|---|---|---|
| `ode45-vanderpol` | ODE | endpoint `[0.32331666704577, -1.83297456798624]` | `endpoint_inf_error` |
| `ode45-exp-decay` | ODE | `y(t)=exp(-t)` | `max_error`, `endpoint_error` |
| `ode23-exp-decay` | ODE | `y(t)=exp(-t)` | `max_error`, `endpoint_error` |
| `ode23s-linear-stiff` | stiff ODE | `y(10)=exp(-10)+10` | `endpoint_error` |
| `fsolve-3x3` | nonlinear solve | `[0.599054; 2.395931; 2.005014]` | `solution_inf_error`, `residual_norm` |
| `fsolve-exp-fit` | curve fitting | synthetic true parameters `a0=0.2`, `b0=3`; initial guess `[0,0]` | `parameter_inf_error`, `residual_norm` |
| `fminunc-rosenbrock-2d` | optimization | `[1,1]`, `fval=0` | `solution_inf_error`, `objective_error` |
| `expm-jordan-2x2` | linear algebra | `[e -e; 0 e]` | `matrix_norm_error` |
| `roots-cubic` | polynomial | roots `[1,2,3]` or `[3,2,1]` after sorting | `root_inf_error` |
| `sinc-values` | signal | `sinc(0)=1`, `sinc(1)=0`, `sinc(1/2)=2/pi` | `max_abs_error` |

`sqp-constrained-5d` 可作为首轮增强 case。如果直接脚本和 extension pipeline 对约束优化输出格式都稳定，再加入正式 comparison。

## 2.4 目录结构

所有实验产物写入 `.runs/`，不写入仓库根目录：

```text
.runs/octave-native-benchmark/
  specs/
    ode45-vanderpol.json
    fsolve-3x3.json
  extension/
    <case_id>/
      case_spec.json
      generated_solver.m
      mhe_wrapper.m
      stdout.txt
      stderr.txt
      metrics.json
      validation.json
      evidence.json
      attempt_log.json
      summary.json
  direct/
    <case_id>/
      case_spec.json
      claude_prompt.txt
      claude_command.json
      claude_stdout.json
      claude_stderr.txt
      solve.m
      stdout.txt
      stderr.txt
      metrics.json
      attempt_log.json
      summary.json
  agent/
    <case_id>/
      case_spec.json
      claude_prompt.txt
      claude_command.json
      claude_stdout.json
      claude_stderr.txt
      claude_result.json
      proposal.json
      generated_solver.m
      mhe_wrapper.m
      stdout.txt
      stderr.txt
      metrics.json
      validation.json
      evidence.json
      attempt_log.json
      summary.json
  comparison/
    summary_table.csv
    comparison_report.md
    result_bundle.json
    run_manifest.json
  reports/
    octave-native-analysis-report.md
    octave-native-backlog.md
```

## 2.5 Case Spec 设计

每个 case 先写统一 `case_spec.json`，extension baseline、direct Claude CLI lane 和 MHE Claude CLI agent lane 必须读取同一份 spec。这样避免三条 lane 使用不同问题定义。

示例：`fsolve-3x3.json`

```json
{
  "case_id": "fsolve-3x3",
  "task_family": "nonlinear_solve",
  "source_reference": "/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fsolve.m:594",
  "description": "3x3 nonlinear system from Octave fsolve BIST",
  "required_capabilities": ["octave-cli"],
  "solver_function": "fsolve",
  "problem_definition": {
    "kind": "inline_octave",
    "notes": "Use the same equations and starting point as the Octave BIST block."
  },
  "reference": {
    "kind": "hard_coded_solution",
    "value": [0.599054, 2.395931, 2.005014]
  },
  "tolerance": {
    "solution_inf_error": 1e-5,
    "residual_norm": 1e-8
  },
  "expected_metrics": [
    "solution_inf_error",
    "residual_norm",
    "elapsed_seconds"
  ]
}
```

字段约定：

- `source_reference` 必填，指向 Octave source 文件和行号，保证 case 来源可审计。
- `required_capabilities` 必填，首轮通常只有 `octave-cli`。
- `reference.kind` 可取 `analytic`、`hard_coded_solution`、`full_solver_reference`、`property_reference`。
- `tolerance` 必须按 metric 命名，不使用模糊的 `default_tolerance`。
- `expected_metrics` 必须能在 `metrics.json` 中找到同名字段。
- 对拟合类 case，`problem_definition` 必须区分 `initial_guess` 和 `reference.true_parameters`，避免把初值误写成参考解。

## 2.6 Extension Pipeline Baseline 测试流程

Extension baseline 不调用 Claude CLI，也不做 LLM 生成。它只验证 `metaharness_ext.octave` 作为确定性执行基线是否能稳定完成 compile → execute → validate → evidence。

流程：

1. 读取 `.runs/octave-native-benchmark/specs/<case_id>.json`。
2. 使用预定义 solver template 或手工固定 script 构造 `OctaveExperimentSpec`。
3. 调用 `OctaveEnvironmentProbeComponent`、`OctaveScriptCompilerComponent`、`OctaveExecutorComponent`、`OctaveValidatorComponent`。
4. 写出 `extension/<case_id>/summary.json`、`validation.json`、`evidence.json`。
5. 如果失败，只记录 pipeline failure，不调用 Claude CLI 修复。

该 lane 用于回答：extension pipeline 是否可靠；不用于证明 LLM agent 优势。

## 2.7 Direct Claude CLI Lane 测试流程

Direct Claude CLI lane 模拟 Claude Code 直接使用 Octave 的方式。

流程：

1. 读取 `.runs/octave-native-benchmark/specs/<case_id>.json`。
2. 构造 generation prompt，调用 `claude -p` 或 `gclaude -p` 生成独立 `solve.m`。
3. 保存 `claude_prompt.txt`、`claude_command.json`、`claude_stdout.json`、`claude_stderr.txt`。
4. 调用：

```bash
octave-cli --no-gui --quiet --no-init-file solve.m > stdout.txt 2> stderr.txt
```

5. driver 读取 return code、stdout/stderr、metrics，写 `summary.json`。
6. 如果第一次失败，可以调用同一 Claude CLI 做 repair，但必须记录在 `attempt_log.json` 和 Claude evidence 文件中。

Direct Claude CLI lane 禁止调用 `metaharness_ext.octave`，否则边界不清。

### Direct `solve.m` 最小约定

每个 direct `solve.m` 必须：

- 使用相对路径写入当前 case 目录。
- 写出 `metrics.json`。
- 不依赖交互图形界面。
- 不调用网络、shell、包安装或不必要的外部文件。
- 使用 `tic` / `toc` 记录核心 solver 调用时间。

示例结构：

```octave
more off;
try
  t_start = tic();
  % define problem
  % call solver
  elapsed_seconds = toc(t_start);

  % compute metrics
  fid = fopen('metrics.json', 'w');
  fprintf(fid, '{"solution_inf_error": %.16g, "residual_norm": %.16g, "elapsed_seconds": %.16g}\n', solution_inf_error, residual_norm, elapsed_seconds);
  fclose(fid);
catch err
  fid = fopen('metrics.json', 'w');
  fprintf(fid, '{"error": "%s"}\n', err.message);
  fclose(fid);
  rethrow(err);
end_try_catch
```

## 2.8 MHE Claude CLI Agent Lane 测试流程

MHE Claude CLI agent lane 使用 Claude CLI 作为 benchmark driver 层的 brain adapter，但仍由 `metaharness_ext.octave` 负责受控执行、验证和 evidence 归档。

流程：

1. Agent runner 读取同一份 `case_spec.json`。
2. 构造 prompt，调用 `claude -p` 或 `gclaude -p` 生成 `proposal.json` 和 candidate solver script。
3. 保存 Claude evidence：`claude_prompt.txt`、`claude_command.json`、`claude_stdout.json`、`claude_stderr.txt`、`claude_result.json`、`proposal.json`。
4. 将 candidate script 转换为 `OctaveExperimentSpec`。
5. 通过 `OctaveEnvironmentProbeComponent`、`OctaveScriptCompilerComponent`、`OctaveExecutorComponent`、`OctaveValidatorComponent` 执行。
6. 如果 validation 失败，最多调用 Claude CLI 做受限 repair；每次 repair 都新增 attempt log 和 Claude evidence。
7. 写出 `validation.json`、`evidence.json`、`summary.json`。

MHE Claude CLI agent lane 必须保留两类 evidence：

- Claude evidence：prompt、command、stdout JSON、stderr、proposal、repair proposal。
- Extension evidence：`mhe_wrapper.m`、generated solver script、stdout / stderr、status file、metrics output、validation report、evidence bundle。

### Agent 输出要求

MHE Claude CLI agent lane 的 `summary.json` 必须与 direct / extension lane 同构，至少字段一致：

```json
{
  "task": "octave_native",
  "case_id": "fsolve-3x3",
  "lane": "octave_mhe_claude_cli_agent",
  "backend": "metaharness_ext.octave",
  "source_reference": ".../fsolve.m:594",
  "command": ["/usr/bin/octave-cli", "--no-gui", "--quiet", "--no-init-file", "mhe_wrapper.m"],
  "return_code": 0,
  "environment": {"octave_version": "GNU Octave, version 9.2.0", "cwd": "..."},
  "metrics": {"solution_inf_error": 0.0, "residual_norm": 0.0, "elapsed_seconds": 0.0},
  "validation": {"passed": true, "status": "executed", "issues": []},
  "effort": {"attempt_count": 1, "repair_count": 0, "manual_interventions": 0},
  "timing": {"driver_elapsed_wall_time_seconds": 0.0, "solver_elapsed_wall_time_seconds": 0.0},
  "evidence_files": ["case_spec.json", "mhe_wrapper.m", "stdout.txt", "stderr.txt", "metrics.json", "validation.json", "summary.json"]
}
```

## 2.9 Metric 计算规则

### 通用 metrics

每个 case 都应输出：

| Metric | 含义 |
|---|---|
| `elapsed_seconds` | Octave 内部 solver 调用耗时，来自 `tic` / `toc` |
| `driver_elapsed_wall_time_seconds` | 外层 driver 或 pipeline 耗时 |
| `return_code` | `octave-cli` return code |
| `passed` | 是否满足 tolerance |
| `attempt_count` | 实际执行尝试次数 |
| `repair_count` | 失败后修改脚本 / spec /路径的次数 |

### Case-specific metrics

| 任务类型 | 推荐 metrics |
|---|---|
| ODE | `endpoint_error`、`max_error`、`steps` |
| nonlinear solve | `solution_inf_error`、`residual_norm`、`info` |
| optimization | `solution_inf_error`、`objective_error`、`iterations`、`exitflag` |
| linear algebra | `matrix_norm_error`、`relative_error` |
| polynomial | `root_inf_error`、`residual_norm` |
| signal | `max_abs_error`、`property_error` |

## 2.10 Pass / Fail 判定

每个 case 使用四层判定：

1. **Environment**：`octave-cli` 是否存在，版本是否可记录。
2. **Execution**：return code 是否为 0，stdout/stderr 是否可保存。
3. **Output**：`metrics.json` 和声明的 evidence 文件是否存在。
4. **Numeric**：metrics 是否满足 `case_spec.json` 中的 tolerance。

推荐 status：

| Status | 含义 |
|---|---|
| `executed` | 执行完成且通过 numeric validation |
| `skipped_capability` | 缺少 SUNDIALS / ARPACK / GLPK / FFTW 等条件能力 |
| `failed` | `octave-cli` return code 非 0 |
| `output_missing` | 执行成功但 metrics / evidence 缺失 |
| `numeric_failed` | 输出存在但误差超出 tolerance |
| `schema_failed` | summary 或 metrics 字段不满足 schema |

## 2.11 Attempt Log

为避免“人工修复次数”变成事后主观描述，每个 lane 都必须写 `attempt_log.json`。

示例：

```json
{
  "case_id": "fsolve-3x3",
  "lane": "octave_direct_claude_cli",
  "attempts": [
    {
      "attempt": 1,
      "command": ["octave-cli", "--no-gui", "--quiet", "--no-init-file", "solve.m"],
      "return_code": 1,
      "status": "failed",
      "issue": "metrics.json not written because variable name mismatch",
      "repair": "renamed xref to x_ref in metric calculation"
    },
    {
      "attempt": 2,
      "command": ["octave-cli", "--no-gui", "--quiet", "--no-init-file", "solve.m"],
      "return_code": 0,
      "status": "executed",
      "issue": null,
      "repair": null
    }
  ]
}
```

`summary.effort.attempt_count` 和 `summary.effort.repair_count` 必须从 `attempt_log.json` 派生。Claude CLI direct / MHE Claude CLI agent lane 还必须记录 `llm_call_count`、`model`、`total_cost_usd`（如果 CLI JSON 输出提供）和 `claude_session_id`（如果存在）。

## 2.12 Schema 校验与重复运行策略

### Summary Schema 校验

每个 lane 生成 `summary.json` 后，必须先通过 schema validation，再进入 comparator。建议在首轮实现中提供轻量 JSON Schema 或 Pydantic model，并把 schema 文件保存在：

```text
.runs/octave-native-benchmark/schema/octave_native_summary.schema.json
.runs/octave-native-benchmark/schema/octave_native_result_bundle.schema.json
```

最低校验项：

- `task`、`case_id`、`lane`、`backend`、`source_reference` 必填。
- `lane` 只能是 `octave_extension_pipeline`、`octave_direct_claude_cli` 或 `octave_mhe_claude_cli_agent`。
- `validation.status` 只能取 `executed`、`skipped_capability`、`failed`、`output_missing`、`numeric_failed`、`schema_failed`。
- `metrics` 必须包含 `case_spec.expected_metrics` 中声明的字段，除非 status 为 `failed` 或 `skipped_capability`。
- `evidence_files` 中列出的文件必须实际存在。
- `effort.attempt_count` 与 `attempt_log.json` 中 attempts 长度一致。

schema validation 失败时，case status 设为 `schema_failed`，不得进入 numeric verdict。

### 重复运行与 flaky 处理

Octave-native 首轮 benchmark 默认每个 lane 每个 case 至少运行 1 次。若用于正式报告，建议每个 case 重复运行 3 次：

```text
.runs/octave-native-benchmark/extension/<case_id>/run-001/
.runs/octave-native-benchmark/direct/<case_id>/run-001/
.runs/octave-native-benchmark/agent/<case_id>/run-001/
```

重复运行规则：

- correctness 采用所有 run 必须通过的保守规则。
- timing 使用 median，不使用单次最快值。
- 若只有 timing 抖动且 numeric 全部通过，标记 `flaky_timing=true`，不标记 numeric failure。
- 若同一 lane 同一 case 出现 pass/fail 混合，标记 `flaky_numeric=true`，报告中必须单独分析。
- tolerance 不因本次结果临时放宽；如确需调整，必须修改 case spec 并记录原因。

## 2.13 Comparator

Comparator 读取三条 lane 的 summary，但 workflow 优势判断主要比较同一 case 的 direct Claude CLI lane 与 MHE Claude CLI agent lane，不跨领域比较数值难度。Extension baseline 用于解释 pipeline 是否可靠，以及 agent lane 失败是否源自 extension gap。

输入：

```text
.runs/octave-native-benchmark/extension/*/summary.json
.runs/octave-native-benchmark/direct/*/summary.json
.runs/octave-native-benchmark/agent/*/summary.json
```

输出：

```text
.runs/octave-native-benchmark/comparison/summary_table.csv
.runs/octave-native-benchmark/comparison/comparison_report.md
```

`summary_table.csv` 建议列：

```text
case_id,task_family,extension_status,direct_status,agent_status,extension_passed,direct_passed,agent_passed,direct_metric_error,agent_metric_error,direct_attempts,agent_attempts,direct_repairs,agent_repairs,direct_llm_calls,agent_llm_calls,extension_driver_time,direct_driver_time,agent_driver_time,extension_evidence_count,direct_evidence_count,agent_evidence_count,verdict
```

Comparator verdict 规则：

| Verdict | 条件 |
|---|---|
| `both_passed_agent_more_evidence` | 两边都通过，agent evidence 更完整 |
| `both_passed_direct_lighter` | 两边都通过，direct 更快且 evidence 缺口不影响复现 |
| `agent_recovered_direct_failed` | direct 失败或缺输出，agent 通过 |
| `direct_passed_agent_failed` | direct 通过，agent 失败，需要修 extension |
| `both_failed` | 两边都失败，检查 case spec 或环境 |
| `skipped_capability` | case 依赖缺失能力 |

## 2.14 结果保存与归档

完成 extension baseline、direct Claude CLI lane 与 MHE Claude CLI agent lane 后，必须把分散在各 case 目录中的结果、Claude evidence、validation result 和 attempt log 汇总为可复查的 comparison bundle。该 bundle 是后续分析报告的唯一数据来源，报告不得直接依赖人工记忆或聊天记录。

### Run Manifest

`comparison/run_manifest.json` 记录本次实验运行的环境、case 范围和输入来源：

```json
{
  "benchmark": "octave-native",
  "run_id": "octave-native-20260427-001",
  "created_at": "2026-04-27T00:00:00Z",
  "octave_source_root": "/home/myfile/distfiles/octave-9.2.0",
  "mhe_repo": "/home/linden/code/git/Aeloon/Aeloon-science-agent/MHE",
  "git_commit": "<commit-or-dirty-state>",
  "octave_binary": "/usr/bin/octave-cli",
  "octave_version": "GNU Octave, version 9.2.0",
  "claude_cli": {
    "binary": "claude|gclaude",
    "version": "<claude --version>",
    "model": "<configured-model>",
    "output_format": "json",
    "max_turns": 5,
    "permission_mode": "auto",
    "no_session_persistence": true
  },
  "case_ids": ["ode45-vanderpol", "fsolve-3x3"],
  "lanes": ["octave_extension_pipeline", "octave_direct_claude_cli", "octave_mhe_claude_cli_agent"],
  "notes": []
}
```

### Result Bundle

`comparison/result_bundle.json` 汇总每个 case 的 extension / direct / agent summary、关键 metrics、Claude metadata、evidence refs 和 verdict：

```json
{
  "benchmark": "octave-native",
  "run_id": "octave-native-20260427-001",
  "cases": [
    {
      "case_id": "fsolve-3x3",
      "task_family": "nonlinear_solve",
      "source_reference": "/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fsolve.m:594",
      "extension_summary": "../extension/fsolve-3x3/summary.json",
      "direct_summary": "../direct/fsolve-3x3/summary.json",
      "agent_summary": "../agent/fsolve-3x3/summary.json",
      "extension_passed": true,
      "direct_passed": true,
      "agent_passed": true,
      "metric_deltas": {"solution_inf_error_delta": 0.0},
      "evidence_delta": {"extension_count": 8, "direct_count": 9, "agent_count": 12},
      "llm_delta": {"direct_llm_calls": 1, "agent_llm_calls": 1},
      "timing_delta": {"agent_driver_overhead_seconds": 0.0, "extension_pipeline_overhead_seconds": 0.0},
      "verdict": "both_passed_agent_more_evidence"
    }
  ]
}
```

### 保存原则

- `summary.json` 是单 case 单 lane 的事实来源。
- `summary_table.csv` 是人工快速查看用的扁平表。
- `result_bundle.json` 是分析报告引用的机器可读汇总。
- `run_manifest.json` 记录实验环境和 dirty state，保证之后能解释结果来源。
- `reports/octave-native-analysis-report.md` 只能引用 `summary_table.csv`、`result_bundle.json` 和 case evidence 文件，不引用聊天上下文。

## 2.15 分析报告要求

最终分析报告写入：

```text
.runs/octave-native-benchmark/reports/octave-native-analysis-report.md
```

报告必须包含：

1. **Executive summary**：一句话结论，说明 agent 是否观察到 workflow 优势，以及代价是什么。
2. **Hypothesis review**：逐条回应零假设和待验证假设。
3. **Environment**：Octave 版本、MHE git state、case 数量、跳过 case。
4. **Case results**：引用 `summary_table.csv`，按 ODE / optimization / linear algebra / polynomial / signal 分组。
5. **Correctness analysis**：extension / direct / agent 的 numeric pass/fail 和误差差异。
6. **Workflow quality analysis**：attempts、repairs、Claude CLI calls、output_missing、schema_failed、evidence completeness。
7. **Overhead analysis**：agent driver time、direct driver time 与 extension pipeline time 的差异，不解释为 solver 性能差异。
8. **Failure analysis**：列出失败 case、根因、是否由 agent pipeline 更早诊断。
9. **Backlog**：将发现的问题写入 `reports/octave-native-backlog.md`，每项包含 owner area、symptom、evidence ref、suggested fix。
10. **Conclusion**：接受、部分接受或拒绝 agent workflow 优势假设。

报告中每个结论都必须能追溯到以下之一：

- `comparison/summary_table.csv`
- `comparison/result_bundle.json`
- 某个 case 的 `summary.json`
- 某个 case 的 `attempt_log.json`
- 某个 case 的 stdout / stderr / validation / evidence 文件

### Backlog 格式

`reports/octave-native-backlog.md` 建议使用表格：

```markdown
| ID | Area | Symptom | Evidence | Suggested fix | Priority |
|---|---|---|---|---|---|
| OCT-BENCH-001 | validator | metrics.json exists but numeric metric not parsed | agent/fsolve-3x3/validation.json | add JSON metrics parser | P1 |
```

## 2.16 公平性约束

为保证三条 lane 可比较：

- 三条 lane 使用同一份 `case_spec.json`。
- 三条 lane 使用同一个 `octave-cli` binary。
- 三条 lane 不允许调用不同算法，除非 spec 明确允许。
- Direct Claude CLI lane 与 MHE Claude CLI agent lane 使用同一个 Claude CLI binary、model、budget 和 prompt policy。
- Direct Claude CLI lane 不调用 `metaharness_ext.octave`。
- MHE Claude CLI agent lane 不绕过 extension pipeline 直接运行手写脚本。
- 所有失败尝试必须写入 `attempt_log.json`。
- 报告不把 pipeline overhead 解释成 solver 性能差异。
- 报告不把 agent 自动生成 evidence 直接当作“优势”，必须说明 evidence 是否能支持复现和 comparator 自动读取。

## 2.17 最小执行顺序

建议按以下顺序推进：

1. 写 10 个 `case_spec.json`。
2. 为每个 case 手工确认 reference value 和 tolerance。
3. 先跑 `octave_extension_pipeline` lane，得到 deterministic extension baseline。
4. 再跑 `octave_direct_claude_cli` lane，得到 direct Claude CLI baseline。
5. 再跑 `octave_mhe_claude_cli_agent` lane，得到 Claude CLI brain + extension pipeline result。
6. 生成并执行 summary schema validation，修正 schema 缺项。
7. 写 comparator，生成 `summary_table.csv`、`result_bundle.json` 和 `run_manifest.json`。
8. 如进入正式报告阶段，每个 case 每条 lane 重复运行 3 次并记录 median timing / flaky flags。
9. 写 `reports/octave-native-analysis-report.md`，只陈述观察到的 workflow 差异。
10. 将失败、输出解析问题和 validation 缺口写入 `reports/octave-native-backlog.md`。

## 2.18 Acceptance Criteria

- 至少 10 个 Octave-native cases 完成 extension、direct Claude CLI 与 MHE Claude CLI agent lane。
- 至少覆盖 ODE、optimization、linear algebra、polynomial、signal 中 4 类。
- 每个 case 都有 `source_reference` 指向 Octave 9.2.0 source。
- 每个完成 case 都有 extension / direct / agent 三份同构 `summary.json`。
- 每个 Claude CLI lane 都有 prompt、command、stdout JSON、stderr 和 proposal evidence（如果该 lane 生成 proposal）。
- 每个 lane 都有 `attempt_log.json`。
- 每个 `summary.json` 都通过 schema validation，或明确记录 `schema_failed`。
- Comparator 能生成 `summary_table.csv`、`comparison_report.md`、`result_bundle.json` 和 `run_manifest.json`。
- 分析报告写入 `reports/octave-native-analysis-report.md`。
- Backlog 写入 `reports/octave-native-backlog.md`。
- 报告明确区分：数值正确性、workflow 质量、Claude CLI 调用成本、pipeline overhead、evidence completeness。

## 2.19 预期会暴露的问题

该测试方法预计能暴露以下 Octave extension 优化点：

- `metrics.json` 自动解析是否稳定。
- `OctaveValidatorComponent` 是否能区分输出缺失和 numeric failed。
- `OctaveOutputSpec` 是否适合表达多 metric case。
- wrapper 生成是否便于调试失败 case。
- warning 分类是否会把 Octave 标准库 warning 误判为风险。
- evidence bundle 是否足够 comparator 自动读取。
- agent 是否能从 spec 自动选择合适 solver template，而不是为每个 case 手写特殊逻辑。
