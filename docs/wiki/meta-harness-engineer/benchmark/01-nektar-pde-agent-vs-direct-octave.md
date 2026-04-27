# 01. Octave-native 与 Nektar PDE 双任务 Benchmark

## 1.1 调整背景

本 benchmark 原计划把 Nektar++ PDE case、`metaharness_ext.octave` / agent flow 和 Claude Code direct `octave-cli` 放入同一个三方比较。审查意见指出这会产生类别错误：Nektar++ 是 spectral/hp element PDE solver，而 Octave 是通用数值计算环境。让 Octave 复刻 Helmholtz、ADR、Taylor vortex 等 PDE solver，会把实验重点转移到“Octave 是否适合从零实现 PDE solver”，而不是“agent workflow 是否有优势”。

进一步探索 GNU Octave 9.2.0 source distribution 后，确认 Octave 自身已经提供大量可直接复用的原生 benchmark 资源：`scripts/ode/`、`scripts/optimization/`、`scripts/linear-algebra/`、`scripts/sparse/`、`scripts/signal/`、`scripts/polynomial/` 中的 BIST / demo 块包含硬编码参考解、解析解或 full solver reference。因此方向 A 不应局限于手写 ODE case，而应基于 Octave 原生测试资源构建一个 Octave-native benchmark suite。

因此本计划改为两个相互独立、可测量、类别匹配的测试任务：

1. **方向 A — Octave-native Benchmark Suite**：使用 GNU Octave 9.2.0 内置 BIST / demo 中已有参考解的 ODE、优化、线性代数、信号处理、多项式任务，对比 direct Claude CLI、deterministic `metaharness_ext.octave` pipeline baseline，以及 Claude CLI brain + Octave extension pipeline。
2. **方向 B — Nektar PDE Benchmark**：使用 Nektar++ 原生 PDE solver cases，对比 direct Claude CLI 操作 Nektar++、deterministic `metaharness_ext.nektar` pipeline baseline，以及 Claude CLI brain + Nektar extension pipeline。

两个任务共享实验方法论、summary schema 风格和报告标准，但不再把 Octave 当作 Nektar++ PDE solver 的替代实现。

## 1.2 总体假设

### 零假设

- Agent pipeline 相比 direct CLI workflow 没有显著 workflow 优势。
- Direct CLI 在小规模单次任务中可能更轻、更快。

### 待验证假设

- Agent pipeline 在可复现性、输入规范化、错误诊断、证据链、批量 case 管理和报告自动化上优于 direct CLI。
- Agent pipeline 的额外 ceremony 会带来 overhead，优势应主要体现在多 case、失败恢复、可审计性和后续自动比较中。
- 对方向 A，`metaharness_ext.octave` 的优势应体现在 Octave-native task spec、执行封装、输出解析、validation 和 evidence，而不是在 Octave solver 本身。
- 对方向 B，`metaharness_ext.nektar` 的优势不应体现在“求解器性能”，而应体现在 Nektar session 生成、执行、postprocess、validation 和 provenance 的 workflow 质量。

## 1.3 非目标

- 不比较 Nektar++ 与 Octave 的数值能力或性能。
- 不要求 Octave 实现 Nektar++ spectral/hp PDE solver。
- 不把 Nektar++ mesh utility test 当成 PDE solver benchmark；`utilities/NekMesh/Tests/Nektar++` 只作为 mesh/geometry 参考。
- 不用主观印象证明 agent 优势；所有结论必须回到 summary JSON、日志、evidence 文件和明确记录的失败/修复事件。
- 不预设 agent 一定优于 direct；报告应能接受 agent 无显著优势或 overhead 不值得的结论。

## 1.4 技术路线：Claude CLI Brain + Extension Pipeline

当前 MHE extension 核心流程是确定性 pipeline，不自带大模型，也不依赖 Aeloon 注入 LLM。为了验证“agent + scientific computing”的闭环，本 benchmark 不把 LLM 调用嵌入 extension executor / validator，而是在 benchmark driver 层增加 Claude CLI brain adapter。

### 三层 lane

| Layer | Lane | LLM | Extension | 目的 |
|---|---|---|---|---|
| Layer 1 | `extension_pipeline` | 无 | 使用 `metaharness_ext.octave` 或 `metaharness_ext.nektar` | 验证确定性 extension pipeline baseline |
| Layer 2 | `direct_claude_cli` | Claude Code CLI | 不调用 extension | 模拟 Claude Code 直接生成脚本 / XML、调用 solver、整理结果 |
| Layer 3 | `mhe_claude_cli_agent` | Claude Code CLI | 调用 extension pipeline | 用同一 Claude CLI 生成 / 修复 candidate，再交给 extension 执行验证 |

这样 direct Claude CLI lane 与 MHE Claude CLI agent lane 背后可以使用同一个 `claude` CLI 和同一个模型配置，差异主要来自 workflow 结构、case spec、validation、evidence 和 repair policy；extension lane 则提供无 LLM 的确定性基线。

### Claude CLI Brain Adapter

建议在 benchmark driver 层实现 `ClaudeCLIBrainProvider` 或 `ClaudeCLIAgentRunner`，不修改 extension 核心组件：

```text
case_spec + prompt_template
  -> claude -p --output-format json --no-session-persistence
  -> proposal.json / generated solve.m / generated session.xml / repair patch
  -> extension compile / execute / validate
  -> attempt_log + summary
```

每次 Claude CLI 调用必须保存：

```text
claude_prompt.txt
claude_command.json
claude_stdout.json
claude_stderr.txt
claude_result.json
proposal.json
```

`run_manifest.json` 必须记录 Claude CLI 信息：

```json
{
  "claude_cli": {
    "binary": "claude",
    "version": "<claude --version>",
    "model": "<configured-model>",
    "output_format": "json",
    "max_turns": 5,
    "permission_mode": "auto",
    "no_session_persistence": true
  }
}
```

如果本地使用的是 `gclaude` wrapper，`binary` 记录 `gclaude`，并把 wrapper 配置摘要写入 manifest。报告必须区分模型差异与 workflow 差异；direct Claude CLI lane 和 MHE Claude CLI agent lane 应尽量使用相同 Claude CLI binary、model 和 budget。

## 1.5 方向 A — Octave-native Benchmark Suite

### 目标

基于 GNU Octave 9.2.0 自带 BIST / demo / examples，验证 `metaharness_ext.octave` / agent pipeline 是否在 Octave 原生数值任务中，比 Claude Code direct `octave-cli` 更稳定、更可复现、更易批量化。

### 资源来源

Octave source distribution：

```text
/home/myfile/distfiles/octave-9.2.0
```

重点目录：

| 目录 | 内容 | Benchmark 价值 |
|---|---|---|
| `scripts/ode/` | `ode45`、`ode23`、`ode23s`、`ode15s`、`ode15i` 等 BIST / demo | ODE / stiff ODE / implicit ODE，含解析解或硬编码参考解 |
| `scripts/optimization/` | `fsolve`、`fminunc`、`fminsearch`、`fminbnd`、`sqp`、`qp`、`lsqnonneg` | 非线性求解、无约束优化、约束优化、QP，含已知最优解 |
| `scripts/linear-algebra/` | `expm`、`condest`、`subspace` 等 | 矩阵函数、条件数估计、子空间角度，含解析或可验证参考 |
| `scripts/sparse/` | `pcg`、`bicgstab`、`gmres`、`eigs`、`svds` | 稀疏迭代求解、稀疏特征值 / SVD，部分依赖 ARPACK |
| `scripts/signal/` | `sinc`、window functions、`fftconv`、`fftfilt`、`unwrap` | 信号函数值、窗口性质、FFT 卷积，部分依赖 FFTW |
| `scripts/polynomial/` | `polyfit`、`roots`、`polyeig`、`spline` | 多项式拟合、求根、多项式特征值 |
| `examples/code/` | `oregonator.m`、`west0479.mat`、`@polynomial/` | ODE example、稀疏矩阵、OOP 示例 |
| `test/` | `.tst` regression tests、`fntests.m` | 回归测试与 BIST runner 参考 |

Octave 9.2.0 没有专用 `benchmarks/` 目录，也未发现标准 `benchmark*.m` 性能套件；方向 A 的 benchmark 应从 BIST / demo 中抽取 correctness cases，并额外包裹 `tic` / `toc` 记录执行时间。

### 对比对象

| Lane | 描述 | 输出目录 |
|---|---|---|
| `octave_extension_pipeline` | 无 LLM，直接把预定义 case spec / script 交给 `metaharness_ext.octave` compile → execute → validate，作为 deterministic baseline | `.runs/octave-native-benchmark/extension/<case_id>/` |
| `octave_direct_claude_cli` | Claude CLI 直接根据 case spec 生成 `.m` 脚本、调用 `octave-cli`、整理 metrics 和 summary，不调用 extension | `.runs/octave-native-benchmark/direct/<case_id>/` |
| `octave_mhe_claude_cli_agent` | Claude CLI brain 生成 / 修复 candidate，再交给 `metaharness_ext.octave` pipeline 执行、验证和归档 | `.runs/octave-native-benchmark/agent/<case_id>/` |

### 首轮 case matrix

首轮选择 10–12 个无需外部库或仅依赖标准 Octave 功能的 case，覆盖多个 Octave-native 任务类型。

| Case ID | 领域 | Octave source | 问题 | 参考解 / reference | 主要指标 | Suitability |
|---|---|---|---|---|---|---|
| `ode45-vanderpol` | ODE | `scripts/ode/ode45.m` | Van der Pol, `t=[0,2]` | `[0.32331666704577, -1.83297456798624]` | endpoint inf error, steps, elapsed | ready-to-use |
| `ode45-exp-decay` | ODE | `scripts/ode/ode45.m` demo | `y'=-y`, `y(0)=1` | `exp(-t)` | max error, endpoint error, convergence slope | ready-to-use |
| `ode23-exp-decay` | ODE | `scripts/ode/ode23.m` demo | `y'=-y`, lower-order solver | `exp(-t)` | max error, endpoint error, convergence slope | ready-to-use |
| `ode23s-linear-stiff` | ODE / stiff | `scripts/ode/ode23s.m` | `y'=t-y+1`, `t=[0,10]` | `y(10)=exp(-10)+10` | endpoint error, solver status | ready-to-use |
| `fsolve-3x3` | nonlinear solve | `scripts/optimization/fsolve.m` | 3x3 nonlinear system | `[0.599054; 2.395931; 2.005014]` | `norm(x-x_ref, Inf)`, residual norm | ready-to-use |
| `fsolve-exp-fit` | curve fitting | `scripts/optimization/fsolve.m` | exponential fit | `a0=0.2`, `b0=3` | parameter error, residual norm | ready-to-use |
| `fminunc-rosenbrock-2d` | optimization | `scripts/optimization/fminunc.m` | Rosenbrock 2D | `[1,1]`, `fval=0` | solution error, objective, iterations | ready-to-use |
| `sqp-constrained-5d` | constrained optimization | `scripts/optimization/sqp.m` | 5D constrained problem | hard-coded optimum / objective | solution error, constraint violation, objective | ready-to-use |
| `qp-bound-1d` | quadratic programming | `scripts/optimization/qp.m` | QP with `x>=1` | `x=1`, `obj=0.5` | solution error, objective error | ready-to-use |
| `expm-jordan-2x2` | linear algebra | `scripts/linear-algebra/expm.m` | `expm([1 -1; 0 1])` | `[e -e; 0 e]` | matrix norm error | ready-to-use |
| `roots-cubic` | polynomial | `scripts/polynomial/roots.m` | polynomial roots | `[3;2;1]` | root matching error | ready-to-use |
| `sinc-values` | signal | `scripts/signal/sinc.m` | `sinc(0)`, `sinc(1)`, `sinc(1/2)` | `1`, `0`, `2/pi` | max abs error | ready-to-use |

### Optional / conditional case matrix

这些 case 需要检测外部 capability，适合作为二阶段扩展，不应阻塞首轮 benchmark。

| Case ID | 领域 | Source | 条件 | 用途 |
|---|---|---|---|---|
| `ode15i-robertson` | stiff implicit ODE | `scripts/ode/ode15i.m` | SUNDIALS | Robertson stiff chemistry reference |
| `ode15s-vanderpol` | stiff ODE | `scripts/ode/ode15s.m` | SUNDIALS | stiff Van der Pol |
| `eigs-tridiagonal-20` | sparse eigenvalue | `scripts/sparse/eigs.m` | ARPACK | compare `eigs` with full `eig` reference |
| `svds-sparse` | sparse SVD | `scripts/sparse/svds.m` | ARPACK | compare `svds` with full `svd` reference |
| `glpk-linear-program` | linear programming | `scripts/optimization/glpk.m` | GLPK | LP feasibility / optimum |
| `fftconv-reference` | FFT signal | `scripts/signal/fftconv.m` | FFTW | compare FFT convolution with `conv` |

### 统一输入 spec

每个 case 写入：

```text
.runs/octave-native-benchmark/specs/<case_id>.json
```

建议字段：

```json
{
  "case_id": "fsolve-3x3",
  "task_family": "nonlinear_solve",
  "source_reference": "/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fsolve.m:594",
  "description": "3x3 nonlinear system from Octave fsolve BIST",
  "required_capabilities": ["octave-cli"],
  "solver_function": "fsolve",
  "problem_definition": {"kind": "inline_octave"},
  "reference": {
    "kind": "hard_coded_solution",
    "value": [0.599054, 2.395931, 2.005014]
  },
  "tolerance": {"solution_inf_error": 1e-5, "residual_norm": 1e-8},
  "expected_metrics": ["solution_inf_error", "residual_norm", "elapsed_seconds"]
}
```

### 方向 A summary schema

```json
{
  "task": "octave_native",
  "case_id": "fsolve-3x3",
  "lane": "octave_extension_pipeline|octave_direct_claude_cli|octave_mhe_claude_cli_agent",
  "backend": "octave-cli|metaharness_ext.octave",
  "source_reference": "/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fsolve.m:594",
  "command": ["octave-cli", "solve.m"],
  "return_code": 0,
  "environment": {"octave_version": "...", "cwd": "..."},
  "method": {"solver_function": "fsolve", "tolerance": {}, "capabilities": ["octave-cli"]},
  "metrics": {"solution_inf_error": 0.0, "residual_norm": 0.0, "elapsed_seconds": 0.0},
  "validation": {"passed": true, "status": "executed|skipped_capability|failed|output_missing|numeric_failed", "issues": []},
  "effort": {"attempt_count": 1, "repair_count": 0, "manual_interventions": 0},
  "timing": {"driver_elapsed_wall_time_seconds": 0.0, "solver_elapsed_wall_time_seconds": 0.0},
  "evidence_files": ["case_spec.json", "solve.m", "stdout.txt", "stderr.txt", "metrics.json", "summary.json"]
}
```

### 方向 A 可测量指标

- 数值正确性：solution error、residual、objective error、matrix norm error、root matching error 是否在 tolerance 内。
- 稳定性：一次成功率、输出缺失次数、数值失败次数、capability skip 是否清晰。
- 可复现性：是否有 source reference、case spec、command、version、cwd、script、stdout/stderr、metrics、summary。
- 证据质量：是否能由 comparator 无人工解释地读取 summary 和 evidence refs。
- 成本：attempt count、repair count、driver wall time、pipeline overhead。
- 覆盖度：ODE、optimization、linear algebra、polynomial、signal 是否至少各有一个通过 case。

## 1.6 方向 B — Nektar PDE Benchmark

### 目标

验证 `metaharness_ext.nektar` / agent pipeline 是否在 Nektar++ 原生 PDE workflow 中，比 Claude Code direct Nektar++ CLI 更可靠、更可审计、更利于错误诊断和批量实验。

### 对比对象

| Lane | 描述 | 输出目录 |
|---|---|---|
| `nektar_extension_pipeline` | 无 LLM，直接用 `metaharness_ext.nektar` 执行 reference case，作为 deterministic baseline | `.runs/nektar-pde-benchmark/extension/<case_id>/` |
| `nektar_direct_claude_cli` | Claude CLI 直接准备 / 修改 Nektar XML，调用 solver / FieldConvert，手动解析输出，不调用 extension | `.runs/nektar-pde-benchmark/direct/<case_id>/` |
| `nektar_mhe_claude_cli_agent` | Claude CLI brain 生成 / 修复 Nektar candidate，再交给 `metaharness_ext.nektar` pipeline 执行、验证和归档 | `.runs/nektar-pde-benchmark/agent/<case_id>/` |

### Nektar 参考来源

优先复用当前 MHE Nektar extension 已覆盖的 solver tests：

- `tests/test_metaharness_nektar_e2e.py` 中的 `HELMHOLTZ_1D`、`HELMHOLTZ_2D`、`TAYLOR_VORTEX`。
- `src/metaharness_ext/nektar/solver_executor.py` 当前支持 `ADRSolver` 与 `IncNavierStokesSolver` execution artifact。
- `src/metaharness_ext/nektar/contracts.py` 中的 `NektarProblemSpec`、`NektarSessionPlan`、`NektarRunArtifact`。

用户给出的 NekMesh 路径：

```text
/home/linden/code/work/Solvers/Nektar/nektar/utilities/NekMesh/Tests/Nektar++
```

该目录主要测试 mesh / geometry quality，例如 Jacobian quality 和 negative Jacobians，不作为方向 B 的主 PDE solver benchmark 来源。

### 候选 case

| Case ID | PDE 类型 | Reference XML | Solver | 主要指标 |
|---|---|---|---|---|
| `helmholtz-1d` | Elliptic / Helmholtz | `Helmholtz1D_8modes.xml` | `ADRSolver` | solver return code, field output, optional error norm |
| `helmholtz-2d` | Elliptic / Helmholtz | `Helmholtz2D_DirectFull.xml` | `ADRSolver` | solver return code, field output, optional error norm |
| `taylor-vortex-2d` | IncNS / unsteady flow | `TaylorVor_dt1.xml` | `IncNavierStokesSolver` | checkpoint/field output, log status, optional postprocess metrics |
| `advection-1d` | ADR / advection | `ADRSolver/Tests/Advection1D_*.xml` if available | `ADRSolver` | solver return code, output presence, optional error norm |

首轮至少运行前三个 case；如果 solver binary 或 XML 不存在，summary 必须写 `status="unavailable"` 和明确原因。

### 方向 B summary schema

```json
{
  "task": "nektar_pde",
  "case_id": "helmholtz-1d",
  "lane": "nektar_extension_pipeline|nektar_direct_claude_cli|nektar_mhe_claude_cli_agent",
  "backend": "nektar_cli|metaharness_ext.nektar",
  "solver_backend": "ADRSolver|IncNavierStokesSolver",
  "source_reference": ".../Helmholtz1D_8modes.xml",
  "command": ["ADRSolver", "session.xml"],
  "return_code": 0,
  "environment": {"nektar_version": null, "cwd": "..."},
  "artifacts": {"session_xml": "session.xml", "field_files": [], "checkpoint_files": [], "log_files": []},
  "metrics": {"l2_error_u": null, "linf_error_u": null, "divergence_residual": null},
  "validation": {"passed": true, "status": "executed|unavailable|failed|output_missing|numeric_failed", "issues": []},
  "diagnostics": {"detected_error_type": null, "suggested_fix": null, "postprocess_status": null},
  "effort": {"attempt_count": 1, "repair_count": 0, "manual_interventions": 0},
  "timing": {"driver_elapsed_wall_time_seconds": 0.0, "solver_elapsed_wall_time_seconds": 0.0},
  "evidence_files": ["session.xml", "solver.stdout.log", "solver.stderr.log", "summary.json"]
}
```

### 方向 B 可测量指标

- PDE workflow correctness：solver return code、field/checkpoint/log output 是否存在、可选 error norm 是否在 tolerance 内。
- Reference fidelity：是否真实运行 Nektar++ reference XML，而不是 Octave-inspired 改写。
- 错误诊断：XML 缺字段、solver binary 缺失、FieldConvert 失败、输出缺失、solver 发散是否被明确分类。
- 可追溯性：session XML、command、cwd、solver logs、field/checkpoint files、postprocess evidence 是否完整。
- 批量可用性：是否能在多个 case 中复用相同 summary schema 和 comparator。

## 1.7 Comparator Design

两个任务分别比较，不做跨任务数值比较。

### 方向 A comparator

读取：

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

比较维度：extension baseline health、correctness、一次成功率、Claude CLI call count、repair count、evidence completeness、schema completeness、pipeline overhead、domain coverage。

### 方向 B comparator

读取：

```text
.runs/nektar-pde-benchmark/extension/*/summary.json
.runs/nektar-pde-benchmark/direct/*/summary.json
.runs/nektar-pde-benchmark/agent/*/summary.json
```

输出：

```text
.runs/nektar-pde-benchmark/comparison/summary_table.csv
.runs/nektar-pde-benchmark/comparison/comparison_report.md
```

比较维度：extension baseline health、reference fidelity、solver execution status、output completeness、diagnostic quality、Claude CLI call count、evidence chain、repair count。

## 1.8 报告结构

建议最终产出两个报告，而不是一个混合结论：

```text
docs/wiki/meta-harness-engineer/benchmark/02-octave-native-agent-vs-direct-report.md
docs/wiki/meta-harness-engineer/benchmark/03-nektar-pde-agent-vs-direct-report.md
```

每个报告包含：

1. Executive summary：是否观察到 agent workflow 优势。
2. Hypothesis：零假设与待验证假设。
3. Environment：Octave 或 Nektar++ 版本、路径、MHE 版本。
4. Case matrix：case 来源、设置、reference 解或 reference XML。
5. Per-case results：extension / direct / agent 指标表。
6. Workflow comparison：正确性、可复现性、Claude CLI 调用成本、证据、错误诊断、overhead。
7. Failure analysis：失败、修复、warnings、schema 问题。
8. Conclusion：接受或拒绝待验证假设，列出不确定性。
9. Optimization backlog：将发现的问题转为具体优化项。

## 1.9 Roadmap

### Phase 0 — Feasibility + Hypothesis

- 固定方向 A 与方向 B 的独立实验假设。
- 确认 Octave 9.2.0 source path、`octave-cli` 版本和 capability：SUNDIALS、ARPACK、GLPK、FFTW。
- 确认方向 A 首轮 case 都来自 Octave built-in BIST / demo，且有解析解、硬编码参考解或 full solver reference。
- 确认 Nektar PDE case XML、solver binary、FieldConvert 是否可用。
- 定义 `skipped_capability` 与 `unavailable` 记录方式，避免环境缺失被误判为 workflow 失败。

### Phase 1 — Unified Specs

- 为方向 A 写 Octave-native `case_spec.json`，包含 `source_reference`、`task_family`、`required_capabilities`、reference 和 tolerance。
- 为方向 B 写 Nektar `case_spec.json` 或 reference XML manifest。
- 固定 summary schema、metrics、tolerance、evidence 文件命名。
- 明确三条 lane 的边界：extension baseline 不调用 Claude CLI；direct Claude CLI 不调用 extension；MHE Claude CLI agent lane 必须走对应 extension pipeline。

### Phase 2A — Octave Extension Baseline

- 不调用 Claude CLI，直接把 Octave-native case spec / fixed script 交给 `metaharness_ext.octave`。
- 执行 compile → execute → validate → evidence。
- 写 `extension/<case_id>/summary.json`、`validation.json`、`evidence.json`。
- 记录 deterministic pipeline health 和 capability skip。

### Phase 2B — Octave Direct Claude CLI Baseline

- Claude CLI 为每个 Octave-native case 直接生成 `.m` 脚本。
- 调用 `octave-cli`，不调用 extension。
- 写 `direct/<case_id>/summary.json` 和 Claude evidence。
- 记录 attempts、repairs、stdout/stderr、metrics、wall time、LLM call count。
- 首轮覆盖 ODE、optimization、linear algebra、polynomial、signal 五类任务。

### Phase 2C — Octave MHE Claude CLI Agent Pipeline

- Claude CLI brain 读取相同 Octave-native case spec，生成 / 修复 candidate。
- Candidate 交给 `metaharness_ext.octave` compile → execute → validate → evidence。
- 写 `agent/<case_id>/summary.json`、`validation.json`、`evidence.json` 和 Claude evidence。
- 记录 extension friction、自动诊断和修复能力。
- 对 capability-gated case 写 `skipped_capability`，不影响首轮通过标准。

### Phase 3A — Nektar Extension Baseline

- 不调用 Claude CLI，直接把 Nektar case spec / reference XML 交给 `metaharness_ext.nektar`。
- 使用 SolverExecutor / Postprocess / Validator 产出 artifact 和 validation。
- 写 `extension/<case_id>/summary.json`、`validation.json`、evidence bundle。
- 对不可用环境写 `status="unavailable"`。

### Phase 3B — Nektar Direct Claude CLI Baseline

- Claude CLI 直接复制或准备 Nektar reference XML。
- 调用 `ADRSolver` / `IncNavierStokesSolver`，必要时调用 `FieldConvert`，不调用 extension。
- 写 `direct/<case_id>/summary.json` 和 Claude evidence。
- 记录 solver logs、field/checkpoint files、error parsing 结果、LLM call count。

### Phase 3C — Nektar MHE Claude CLI Agent Pipeline

- Claude CLI brain 生成 / 修复 Nektar candidate。
- Candidate 交给 `metaharness_ext.nektar` 执行 reference case。
- 使用 SolverExecutor / Postprocess / Validator 产出 artifact 和 validation。
- 写 `agent/<case_id>/summary.json`、`validation.json`、evidence bundle 和 Claude evidence。
- 对不可用环境写 `status="unavailable"`。

### Phase 4 — Comparators

- 分别读取方向 A、方向 B summaries。
- 检查 schema completeness 和 evidence refs。
- 方向 A 生成按 domain 分组的 comparison table。
- 方向 B 生成按 PDE solver family 分组的 comparison table。
- 小样本下不强行做统计显著性结论；如 case 数足够，再对 paired metrics 做辅助统计。

### Phase 5 — Reports + Backlog

- 写两个 benchmark report。
- 明确区分 agent workflow gain 与 pipeline overhead。
- 将问题转为可实现 backlog，例如 metrics 自动解析、validator error taxonomy、evidence schema 改进、case spec 校验、Octave BIST case library、Nektar error norm 标准化。

## 1.10 Acceptance Criteria

- 方向 A 至少完成 10 个 Octave-native case 的 extension、direct Claude CLI 与 MHE Claude CLI agent lane，覆盖 ODE、optimization、linear algebra、polynomial、signal 中至少 4 类；或明确记录 capability skip。
- 方向 B 至少完成 3 个 Nektar PDE case 的 extension、direct Claude CLI 与 MHE Claude CLI agent lane，或明确记录不可用原因。
- 每个完成 case 都有同构 `summary.json`。
- 两个 comparator 分别生成 summary table。
- 两个报告都显式写出零假设、观察结果、限制和 backlog。
- 报告不得声称 Octave 与 Nektar++ solver 能力可直接比较。
- 方向 A 必须引用 Octave source file / line 或 BIST origin，避免 benchmark case 来源不明。

## 1.11 Initial Risks

| 风险 | 影响 | 缓解 |
|---|---|---|
| 再次混淆 Octave 与 Nektar++ 类别 | 结论失效 | 两个任务独立比较，不跨 solver 做数值能力结论 |
| Direct Claude CLI lane 被 Claude 过度手工优化 | direct baseline 不公平 | 使用统一 spec，记录 attempts、repair count 和 Claude CLI 调用 |
| MHE Claude CLI agent lane 证据质量指标循环论证 | 偏向 agent | 把 evidence completeness 定义为 schema 字段和文件存在性，而非主观评分 |
| Octave BIST 被直接复制但缺来源 | benchmark 不可审计 | 每个 spec 必须写 `source_reference` 和 extracted reference |
| 条件库缺失 | 部分 case 无法运行 | 首轮只用 no-extra-library case；条件 case 使用 `skipped_capability` |
| Nektar++ solver binary 缺失 | PDE benchmark 无法运行 | 写 `status="unavailable"`，不把环境缺失当成 agent/direct 失败 |
| case 太简单 | agent 优势不明显 | 覆盖 ODE、优化、线性代数、信号和多项式，多 case 比较流程价值 |
| repair count 难自动统计 | 指标不可复现 | 每次运行尝试写入 `attempt_log.json`，由 driver 记录而非事后回忆 |

## 1.12 First Implementation Slice

建议最小起步：

1. 方向 A 先抽取 10 个 no-extra-library Octave-native cases：`ode45-vanderpol`、`ode45-exp-decay`、`ode23-exp-decay`、`ode23s-linear-stiff`、`fsolve-3x3`、`fsolve-exp-fit`、`fminunc-rosenbrock-2d`、`expm-jordan-2x2`、`roots-cubic`、`sinc-values`。
2. 方向 B 先选 `helmholtz-1d`、`helmholtz-2d`、`taylor-vortex-2d`。
3. 先写两套 case spec 和 summary schema fixtures。
4. 先跑 direction A extension lane，确认 Octave extension deterministic baseline 可执行。
5. 再跑 direction A direct Claude CLI lane 和 MHE Claude CLI agent lane，保证三份 summary 同构。
6. 之后跑 direction B extension / direct Claude CLI / MHE Claude CLI agent lane，明确记录 Nektar solver availability。
7. 写两个最小 comparator，只做 schema completeness、pass/fail、metrics 表格和 evidence 文件检查。
8. 最后写两个报告，不合并为一个跨 solver 优劣结论。
