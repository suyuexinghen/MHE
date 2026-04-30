# 05. Nektar PDE Benchmark 实验分析报告

> 版本：v0.1 | 生成依据：`.runs/benchmark-wiki/nektar-pde-benchmark/` | 日期：2026-04-28

## 5.1 实验范围

本报告对应 `nektar-pde` suite，用于验证 Nektar++ native PDE regression cases 在三条 workflow lane 下的 benchmark driver、preflight、error norm parser、summary schema、comparison bundle 和报告生成路径。

本轮是安全 dry-run / mocked benchmark，不声明真实 Nektar++ PDE solver 数值结论。它验证的是：`.tst` / `.xml` source reference 记录、Nektar preflight summary、lane summary layout、capability skip 表达、Claude CLI evidence 记录和 comparator 汇总。

## 5.2 数据来源

- 运行根目录：`.runs/benchmark-wiki`
- Suite 目录：`.runs/benchmark-wiki/nektar-pde-benchmark/`
- Preflight：`.runs/benchmark-wiki/nektar-pde-benchmark/preflight/*/tester_summary.json`
- Case specs：`.runs/benchmark-wiki/nektar-pde-benchmark/specs/*.json`
- Lane summaries：`.runs/benchmark-wiki/nektar-pde-benchmark/{extension,direct,agent}/*/summary.json`
- Comparison bundle：`.runs/benchmark-wiki/nektar-pde-benchmark/comparison/result_bundle.json`
- Manifest：`.runs/benchmark-wiki/nektar-pde-benchmark/comparison/run_manifest.json`
- Generated report：`.runs/benchmark-wiki/nektar-pde-benchmark/reports/nektar-pde-analysis-report.md`

The preflight files record whether `Tester` and the selected solver binary are visible, whether the `.tst` file path exists, and how many reference metrics were parsed from `.tst` when available. Because `--allow-real-tools` was not used, preflight is a capability probe and metadata capture step, not a solver execution claim.

## 5.3 Case 覆盖

首轮 6 个 Nektar PDE cases 均进入三条 lane：

| Case | Extension | Direct | Agent | Verdict |
|---|---|---|---|---|
| `advection-1d` | passed | passed | passed | all_passed |
| `diffusion-2d` | skipped | passed | passed | capability_skip |
| `advdiff-2d` | passed | passed | passed | all_passed |
| `advdiff-imex-2d` | passed | passed | passed | all_passed |
| `taylor-vortex-2d` | passed | passed | passed | all_passed |
| `euler-1d` | skipped | passed | passed | capability_skip |

Observed summary:

- Cases compared: 6
- Fully passed dry-run cases: 4
- Capability skips: 2
- Schema failures observed by comparator: 0
- Direct Claude CLI calls recorded: 6
- Agent Claude CLI calls recorded: 6

## 5.4 Preflight observations

Each case writes `preflight/<case_id>/tester_summary.json`, `tester.stdout.log`, and `tester.stderr.log`. For example, `advdiff-2d` records `tester_available=true`, `solver_binary=ADRSolver`, `solver_available=true`, `tst_available=true`, and `reference_metric_count=2`.

This means the local environment can see Nektar++ test metadata for at least that case, but the current dry-run did not invoke `Tester` or solver commands. Formal Nektar validation must execute the relevant tester or solver command and capture stdout/stderr from that run.

## 5.5 Workflow lane observations

### Extension baseline

The extension lane emits deterministic dry-run evidence for supported current-dispatch cases. `diffusion-2d` and `euler-1d` are intentionally marked `capability_skip` for the current extension dispatch, which is more truthful than faking complete extension support.

### Direct Claude CLI lane

The direct lane records one Claude CLI proposal attempt per case and captures solver stdout/stderr evidence paths. In real mode, it loads `.tst` metadata, selects the `.tst` executable when present, materializes `session.xml`, runs the solver only with `--allow-real-tools`, parses `L 2 error` and `L inf error` stdout lines, and writes `.tst` reference metrics when available.

### MHE Claude CLI agent lane

The agent lane records one Claude CLI proposal per case. Real Nektar agent replay is still a truthful skip unless a dedicated extension session mapping is implemented. The current dry-run evidence verifies lane accounting and report generation, not complete real-mode Nektar agent execution.

## 5.6 Numeric interpretation

Nektar PDE accuracy must be judged by solver-generated L2/Linf error norms against `.tst` reference values and tolerances. In this dry-run, metric values are reference echoes used to validate comparator wiring. They should not be cited as actual solver residuals or convergence evidence.

Formal real-mode analysis should separately report:

1. Native `Tester` or solver preflight result.
2. Extension baseline execution status.
3. Direct Claude CLI generated `session.xml` validity.
4. Agent generated plan/session validity.
5. Parsed L2/Linf metrics and tolerance verdicts.
6. Solver elapsed time versus driver overhead.

## 5.7 Acceptance status

| Requirement | Status | Notes |
|---|---|---|
| 6 Nektar PDE cases | Complete for dry-run | All documented first-round cases are catalogued. |
| Preflight summaries | Complete as capability probes | `tester_summary.json` exists per case; dry-run does not execute Tester. |
| L2/Linf parser | Implemented | Handles `L 2 error` and `L inf error` with optional variable names. |
| `.tst` parsing | Implemented | Extracts executable, parameters, reference metrics, and tolerances. |
| Direct real-mode foundation | Implemented | Real solver invocation remains gated by `--allow-real-tools`. |
| Extension real-mode replay | Pending | Current extension dispatch does not cover every solver family. |
| Agent real-mode replay | Pending | Needs dedicated Nektar extension session mapping. |
| Comparator bundle | Complete | CSV, Markdown, JSON bundle and manifest are generated. |

## 5.8 Phase B real-solver evidence

A later Phase B run executed real Nektar tools for the extension lane only:

- Run root: `.runs/nektar-real-solver-phase-b-20260430`
- Compare bundle: `.runs/nektar-real-solver-phase-b-20260430/nektar-pde-benchmark/comparison/result_bundle.json`
- Real tools: `true`
- Real Claude proposals: `false`
- Repeat count: `3`

| Case | Lane | Passed / Runs | Median elapsed seconds | Flags |
|---|---|---:|---:|---|
| `advection-1d` | extension | 3 / 3 | 1.7995890200254507 | none |
| `advdiff-2d` | extension | 3 / 3 | 2.657321578997653 | none |
| `advdiff-imex-2d` | extension | 3 / 3 | 4.116794275003485 | none |

This proves repeated real Nektar extension execution for the listed cases. It does not prove direct or agent lane superiority because `direct` and `agent` were not run; the comparator therefore reports `verdict="incomplete"` for each case.

## 5.9 Phase C real-Claude smoke evidence

A narrow Phase C smoke then executed `advection-1d` with real tools and real Claude proposals for `direct` and `agent` lanes:

- Run root: `.runs/nektar-real-claude-phase-c-20260430`
- Compare bundle: `.runs/nektar-real-claude-phase-c-20260430/nektar-pde-benchmark/comparison/result_bundle.json`
- Repeat summary: `.runs/nektar-real-claude-phase-c-20260430/nektar-pde-benchmark/comparison/repeat_summary.json`
- Real tools: `true`
- Real Claude proposals: `true`
- Repeat count: `3`

| Case | Lane | Passed / Runs | Median elapsed seconds | LLM calls | Flags |
|---|---|---:|---:|---:|---|
| `advection-1d` | direct | 2 / 3 | 4.281351247482235 | 3 | `flaky_status` |
| `advection-1d` | agent | 1 / 3 | 8.60528252000222 | 3 | `flaky_status` |

The successful direct and agent repeats produced matching `l2_error_u=0.00960004` and `linf_error_u=0.0177832`. Failed repeats did not reach solver execution; their error was `Reached maximum number of turns (5)`, so they should be classified as real-Claude proposal/runtime failures rather than Nektar solver failures.

This Phase C smoke is enough to prove the real-Claude lanes are wired to executable Nektar workflows for `advection-1d`, but it does not support a superiority claim. The immediate optimization target is reducing proposal turn-limit failures and recording proposal/preflight failure categories more explicitly.

## 5.10 Backlog

1. Tighten Nektar direct and agent prompts or Claude turn limits so Phase C proposal generation is stable.
2. Classify `Reached maximum number of turns (5)` as a proposal/runtime failure category in lane summaries.
3. Rerun Phase C `advection-1d` until repeated direct/agent status is stable enough for comparison.
4. Execute native `Tester` or equivalent solver command for each additional case and record real preflight stdout/stderr.
5. Implement or validate Nektar extension replay coverage before expanding to DiffusionSolver, IncNavierStokesSolver, and CompressibleFlowSolver.
6. Define agent proposal-to-`NektarSessionPlan` mapping and validation rules.
7. Add per-variable L2/Linf tables to the generated report.
8. Keep `diffusion-2d` and `euler-1d` capability-gated until extension dispatch support is verified.
