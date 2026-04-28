# 04. Octave-native Benchmark 实验分析报告

> 版本：v0.1 | 生成依据：`.runs/benchmark-wiki/octave-native-benchmark/` | 日期：2026-04-28

## 4.1 实验范围

本报告对应 `octave-native` suite，用于验证 Octave 9.2.0 native numerical cases 在三条 workflow lane 下的 benchmark driver、summary schema、evidence layout、comparison bundle 和报告生成路径。

本轮是安全 dry-run / mocked benchmark，不声明真实 Octave 数值运行结论。它验证的是：case catalog、lane 边界、Claude CLI evidence 记录、MHE extension pipeline evidence 记录、comparator 汇总和 report bundle 可复查。

## 4.2 数据来源

- 运行根目录：`.runs/benchmark-wiki`
- Suite 目录：`.runs/benchmark-wiki/octave-native-benchmark/`
- Case specs：`.runs/benchmark-wiki/octave-native-benchmark/specs/*.json`
- Lane summaries：`.runs/benchmark-wiki/octave-native-benchmark/{extension,direct,agent}/*/summary.json`
- Comparison bundle：`.runs/benchmark-wiki/octave-native-benchmark/comparison/result_bundle.json`
- Manifest：`.runs/benchmark-wiki/octave-native-benchmark/comparison/run_manifest.json`
- Generated report：`.runs/benchmark-wiki/octave-native-benchmark/reports/octave-native-analysis-report.md`

Manifest 记录的环境包括 Python 3.13.11、Claude Code `2.1.114`、GNU Octave 9.2.0，以及本地可见的 Nektar++ solver binaries。该 manifest 只说明环境探测结果；本轮 `benchmark-run` 未使用 `--allow-real-tools`，所以 Octave case 结果仍是 dry-run。

## 4.3 Case 覆盖

首轮 10 个 Octave-native cases 均进入三条 lane：

| Case | Extension | Direct | Agent | Verdict |
|---|---|---|---|---|
| `ode45-vanderpol` | passed | passed | passed | all_passed |
| `ode45-exp-decay` | passed | passed | passed | all_passed |
| `ode23-exp-decay` | passed | passed | passed | all_passed |
| `ode23s-linear-stiff` | passed | passed | passed | all_passed |
| `fsolve-3x3` | passed | passed | passed | all_passed |
| `fsolve-exp-fit` | passed | passed | passed | all_passed |
| `fminunc-rosenbrock-2d` | passed | passed | passed | all_passed |
| `expm-jordan-2x2` | passed | passed | passed | all_passed |
| `roots-cubic` | passed | passed | passed | all_passed |
| `sinc-values` | passed | passed | passed | all_passed |

Observed summary:

- Cases compared: 10
- Fully passed dry-run cases: 10
- Capability skips: 0
- Schema failures observed by comparator: 0
- Direct Claude CLI calls recorded: 10
- Agent Claude CLI calls recorded: 10

## 4.4 Workflow lane observations

### Extension baseline

The extension lane records deterministic MHE evidence under each `extension/<case_id>/` directory. In dry-run mode, each case records extension validation/evidence files and generated wrapper/source placeholders. This lane is the no-LLM baseline and is used as the reproducibility anchor.

### Direct Claude CLI lane

The direct lane records one Claude CLI proposal attempt per case and writes `claude_prompt.txt`, `claude_command.json`, `claude_stdout.json`, `claude_stderr.txt`, `claude_result.json`, and `proposal.json`. In real mode, this lane writes `solve.m` from the Claude proposal when present and runs `octave-cli` only with `--allow-real-tools`.

### MHE Claude CLI agent lane

The agent lane records one Claude CLI call per case, then routes through the MHE extension-shaped execution path. The important boundary is that agent artifacts are written under `agent/<case_id>/`, not relabeled from `extension/<case_id>/`. This preserves evidence separation between deterministic baseline and LLM-assisted extension workflow.

## 4.5 Numeric interpretation

Because this run is dry-run, all reported metric diffs are harness-level reference echoes rather than fresh Octave solver measurements. The run validates that `expected_metrics`, `reference_metrics`, `metric_diffs`, `missing_metrics`, and verdict logic are wired, but it does not prove that the generated Octave scripts reproduce Octave BIST values under real execution.

For a formal numerical report, rerun with real tools enabled and repeat each case at least three times. Median timing and flaky flags should be computed only from real `octave-cli` output.

## 4.6 Evidence completeness

The comparison bundle shows direct lane evidence count of 8 for each case and agent lane evidence count of 5 for each case. Extension lane evidence count is 4 for each case in dry-run mode. These counts are useful for reproducibility auditing, but they must not be interpreted as workflow superiority by themselves.

Evidence quality should be evaluated by whether an independent reviewer can reconstruct:

1. The case spec.
2. The prompt and Claude command metadata.
3. The generated or proposed script.
4. The stdout/stderr and metrics path.
5. The final summary and comparator verdict.

## 4.7 Acceptance status

| Requirement | Status | Notes |
|---|---|---|
| 10 Octave-native cases | Complete for dry-run | All documented first-round cases are catalogued and emitted. |
| Three lanes per case | Complete for dry-run | `extension`, `direct`, and `agent` summaries are generated. |
| Claude evidence capture | Complete for dry-run and adapter path | Real CLI execution remains opt-in. |
| Comparator bundle | Complete | CSV, Markdown, JSON bundle and manifest are generated. |
| Schema failure handling | Implemented via Pydantic load failure path | Malformed summaries produce `schema_validation.json`. |
| Repeated real runs | Pending | Not executed in this dry-run report. |
| Formal Octave numeric conclusions | Pending | Requires `--allow-real-tools` and repeated runs. |

## 4.8 Backlog

1. Run real Octave smoke cases with `--allow-real-tools` and compare dry-run vs real summary contents.
2. Add exact Octave BIST source line references where practical for each case.
3. Add repeated-run aggregation fields such as median elapsed time and `flaky_numeric`.
4. Tighten generated `solve.m` validation against Octave JSON/metrics conventions.
5. Expand report generation to include per-case metric diff tables from real runs.
