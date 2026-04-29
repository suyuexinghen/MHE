# Real Repeated Octave / Nektar Benchmark Analysis

> 日期：2026-04-28  
> 证据根目录：`.runs/real-repeated-20260428/`  
> 运行模式：`--allow-real-tools`，真实 `octave-cli` / Nektar solver / Claude CLI (`cc-gpt-5.5`)  
> 重复次数：Octave final roots 2 次；Nektar final roots 2 次

## 1. Executive Summary

这轮实验把此前 dry-run / mocked benchmark 推进到了真实工具执行，并做了重复运行。结论仍需要分两层看：

1. **数值求解优劣**：
   - Octave final runs 中，`extension`、`direct`、`agent` 三条 lane 在 3 个 case × 2 次重复中全部通过，因此目前不能声称 MHE extension 在 Octave 数值精度上优于 direct Claude Code；它们在这些小型 case 上都能得到满足 tolerance 的真实数值结果。
   - Nektar final runs 中，`direct` lane 在 3 个 ADRSolver case × 2 次重复中全部通过 L2/Linf 解析与 reference tolerance；但 `extension` 和 `agent` real replay 当前仍是 capability skip，因此不能做 Nektar 上 MHE extension vs direct 的真实数值优劣结论。
2. **Workflow / Harness 优劣**：
   - Octave 的 MHE `extension` / `agent` lane 产生了更完整的 wrapper、workspace outputs、validation metrics、stdout/stderr 和 evidence 链；`direct` lane 也能成功，但依赖生成脚本的格式和环境兼容性。
   - Nektar 的结果暴露了当前 MHE extension 的 capability gap：真实 solver 可运行，direct 能解析 L2/Linf，但 extension/agent 尚未实现 reference XML replay 与 session mapping。
   - 这轮最有价值的反馈不是“谁的 solver 更强”，而是：真实重复实验开始把 workflow 可复现性、capability skip、证据完整性和 driver portability 问题转成可执行 backlog。

## 2. Inputs and Commands

参考报告：`docs/wiki/meta-harness-engineer/benchmark/reports/analysis.md`。

最终证据根目录：

- Octave repeat 1: `.runs/real-repeated-20260428/octave-final-1/`
- Octave repeat 2: `.runs/real-repeated-20260428/octave-final-2/`
- Nektar repeat 1: `.runs/real-repeated-20260428/nektar-final-1/`
- Nektar repeat 2: `.runs/real-repeated-20260428/nektar-final-2/`

Representative commands:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite octave-native \
  --lanes extension,direct,agent \
  --cases sinc-values,roots-cubic,ode45-exp-decay \
  --runs-root .runs/real-repeated-20260428/octave-final-1 \
  --allow-real-tools \
  --claude-binary /home/linden/.npm-global/bin/claude \
  --claude-model cc-gpt-5.5

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite octave-native \
  --runs-root .runs/real-repeated-20260428/octave-final-1
```

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite nektar-pde \
  --lanes extension,direct,agent \
  --cases advection-1d,advdiff-2d,advdiff-imex-2d \
  --runs-root .runs/real-repeated-20260428/nektar-final-1 \
  --allow-real-tools \
  --claude-binary /home/linden/.npm-global/bin/claude \
  --claude-model cc-gpt-5.5

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite nektar-pde \
  --runs-root .runs/real-repeated-20260428/nektar-final-1
```

## 3. Tool Availability

本机 real-tool probe 显示以下工具可用：

- `octave-cli`: `/usr/bin/octave-cli`
- `Tester`: `/home/linden/usr/nektar/nektar-5.9.0/bin/Tester`
- `ADRSolver`: `/home/linden/usr/nektar/nektar-5.9.0/bin/ADRSolver`
- `DiffusionSolver`: `/home/linden/usr/nektar/nektar-5.9.0/bin/DiffusionSolver`
- `CompressibleFlowSolver`: `/home/linden/usr/nektar/nektar-5.9.0/bin/CompressibleFlowSolver`
- `IncNavierStokesSolver`: `/home/linden/usr/nektar/nektar-5.9.0/bin/IncNavierStokesSolver`
- Claude CLI: `/home/linden/.npm-global/bin/claude`

因此本轮不是 dry-run；Octave 和 Nektar direct lane 都实际调用了外部 solver。Nektar extension/agent 的 skip 是 runner capability skip，不是系统缺 solver。

## 4. Octave Real Repeated Results

Cases:

- `sinc-values`
- `roots-cubic`
- `ode45-exp-decay`

Final comparison bundles:

- `.runs/real-repeated-20260428/octave-final-1/octave-native-benchmark/comparison/result_bundle.json`
- `.runs/real-repeated-20260428/octave-final-2/octave-native-benchmark/comparison/result_bundle.json`

### 4.1 Pass / Fail Summary

| Repeat | Case | Extension | Direct | Agent | Comparator verdict |
|---|---|---:|---:|---:|---|
| `octave-final-1` | `sinc-values` | passed | passed | passed | `all_passed` |
| `octave-final-1` | `roots-cubic` | passed | passed | passed | `all_passed` |
| `octave-final-1` | `ode45-exp-decay` | passed | passed | passed | `all_passed` |
| `octave-final-2` | `sinc-values` | passed | passed | passed | `all_passed` |
| `octave-final-2` | `roots-cubic` | passed | passed | passed | `all_passed` |
| `octave-final-2` | `ode45-exp-decay` | passed | passed | passed | `all_passed` |

Across the clean final roots:

| Lane | Runs | Passed | Skipped | Pass rate |
|---|---:|---:|---:|---:|
| `extension` | 6 | 6 | 0 | 100% |
| `direct` | 6 | 6 | 0 | 100% |
| `agent` | 6 | 6 | 0 | 100% |

### 4.2 Numerical Metrics

The final runs show stable Octave numeric correctness for all three lanes.

| Case | Metric | Observed diff / value | Tolerance | Result |
|---|---|---:|---:|---|
| `sinc-values` | `max_abs_error` | `3.8981718325193755e-17` | `1e-12` | within tolerance |
| `roots-cubic` | `root_inf_error` | `5.10702591327572e-15` | `1e-10` | within tolerance |
| `ode45-exp-decay` | `max_error` | `8.50692741805048e-08` | `1e-6` | within tolerance |
| `ode45-exp-decay` | `endpoint_error` | `2.7478702341321437e-08` | `1e-6` | within tolerance |

Representative evidence:

- `.runs/real-repeated-20260428/octave-final-1/octave-native-benchmark/extension/ode45-exp-decay/summary.json`
- `.runs/real-repeated-20260428/octave-final-1/octave-native-benchmark/direct/ode45-exp-decay/summary.json`
- `.runs/real-repeated-20260428/octave-final-1/octave-native-benchmark/agent/ode45-exp-decay/summary.json`
- `.runs/real-repeated-20260428/octave-final-2/octave-native-benchmark/comparison/result_bundle.json`

### 4.3 Timing Observations

Timing is reported as observed run timing, not as a statistically strong performance claim.

| Repeat | Lane | Median `elapsed_seconds` across 3 cases |
|---|---|---:|
| `octave-final-1` | `extension` | `0.0005140304565429688` |
| `octave-final-1` | `direct` | `0.0004870891571044922` |
| `octave-final-1` | `agent` | `0.0005049705505371094` |
| `octave-final-2` | `extension` | `0.0005118846893310547` |
| `octave-final-2` | `direct` | `0.0004878044128417969` |
| `octave-final-2` | `agent` | `0.0005090236663818359` |

These cases are too small to support a robust solver-performance conclusion. The timing mainly confirms that the final runner path records `elapsed_seconds` without using it as a zero-tolerance correctness gate.

### 4.4 Octave Workflow Findings

- `extension` lane produced deterministic MHE wrapper/workspace outputs and validation/evidence artifacts without LLM calls.
- `direct` lane succeeded after the runner used portable manual JSON writing instead of Octave `jsonencode`, which is unavailable in this local Octave build.
- `agent` lane succeeded and combined Claude proposal evidence with the same extension execution/validation path.
- Clean final results do not show a numerical advantage for MHE over direct Claude Code on the selected Octave cases; they show comparable real numerical success plus stronger structured workflow evidence for extension/agent lanes.

## 5. Nektar Real Repeated Results

Cases:

- `advection-1d`
- `advdiff-2d`
- `advdiff-imex-2d`

Final comparison bundles:

- `.runs/real-repeated-20260428/nektar-final-1/nektar-pde-benchmark/comparison/result_bundle.json`
- `.runs/real-repeated-20260428/nektar-final-2/nektar-pde-benchmark/comparison/result_bundle.json`

### 5.1 Pass / Skip Summary

| Repeat | Case | Extension | Direct | Agent | Comparator verdict |
|---|---|---:|---:|---:|---|
| `nektar-final-1` | `advection-1d` | skipped | passed | skipped | `capability_skip` |
| `nektar-final-1` | `advdiff-2d` | skipped | passed | skipped | `capability_skip` |
| `nektar-final-1` | `advdiff-imex-2d` | skipped | passed | skipped | `capability_skip` |
| `nektar-final-2` | `advection-1d` | skipped | passed | skipped | `capability_skip` |
| `nektar-final-2` | `advdiff-2d` | skipped | passed | skipped | `capability_skip` |
| `nektar-final-2` | `advdiff-imex-2d` | skipped | passed | skipped | `capability_skip` |

Across clean final roots:

| Lane | Runs | Passed | Skipped | Pass rate among attempted real executions |
|---|---:|---:|---:|---:|
| `extension` | 6 | 0 | 6 | not attempted |
| `direct` | 6 | 6 | 0 | 100% |
| `agent` | 6 | 0 | 6 | not attempted |

Skip reasons are explicit and stable:

- Extension: `real Nektar reference-XML extension replay is not enabled by default`
- Agent: `real Nektar agent replay requires a dedicated extension session mapping`

### 5.2 Nektar Numerical Metrics

The Nektar `direct` lane successfully executed real `ADRSolver` cases and parsed L2/Linf metrics.

| Case | Metric | Repeat 1 | Repeat 2 | Reference diff | Result |
|---|---|---:|---:|---:|---|
| `advection-1d` | `l2_error_u` | `0.00960004` | `0.00960004` | `0.0` | passed |
| `advection-1d` | `linf_error_u` | `0.0177832` | `0.0177832` | not reference-gated in current catalog | observed |
| `advdiff-2d` | `l2_error_u` | `0.00135233` | `0.00135233` | `0.0` | passed |
| `advdiff-2d` | `linf_error_u` | `0.00275937` | `0.00275937` | `0.0` | passed |
| `advdiff-imex-2d` | `l2_error_u` | `1.85113e-07` | `1.85113e-07` | `1.0e-12` | passed |
| `advdiff-imex-2d` | `linf_error_u` | `7.82281e-07` | `7.82281e-07` | not reference-gated in current catalog | observed |

Representative evidence:

- `.runs/real-repeated-20260428/nektar-final-1/nektar-pde-benchmark/direct/advection-1d/summary.json`
- `.runs/real-repeated-20260428/nektar-final-1/nektar-pde-benchmark/direct/advdiff-2d/solver.stdout.log`
- `.runs/real-repeated-20260428/nektar-final-2/nektar-pde-benchmark/direct/advdiff-imex-2d/summary.json`
- `.runs/real-repeated-20260428/nektar-final-2/nektar-pde-benchmark/preflight/advection-1d/tester_summary.json`

### 5.3 Nektar Timing Observations

| Repeat | Lane | Median `elapsed_seconds` across 3 cases |
|---|---|---:|
| `nektar-final-1` | `direct` | `3.9711995770339854` |
| `nektar-final-2` | `direct` | `2.206578941026237` |

The direct lane solver timing varied materially between the two repeats. With only two repeats, this should be treated as timing variability requiring more samples, not a stable performance finding.

### 5.4 Nektar Workflow Findings

- Real Nektar solver binaries and `.tst` / `.xml` references are available.
- The direct benchmark runner can materialize a session XML, call the solver, capture stdout/stderr, and parse L2/Linf metrics.
- The MHE Nektar extension path still does not replay reference XML sessions in real mode, so extension/agent cannot yet compete with direct execution numerically.
- This is a clear MHE extension optimization target: implement real reference-XML replay and agent session mapping before making Nektar extension-vs-direct numerical claims.

## 6. Pilot-Run Failures and Fixes

Earlier pilot roots under `.runs/real-repeated-20260428/octave-run-*` and `.runs/real-repeated-20260428/nektar-run-*` exposed real-mode runner bugs. They are useful engineering evidence but are not used as final comparison conclusions.

Observed pilot issues:

- Octave extension/agent initially failed because `elapsed_seconds` was treated as a zero-tolerance numerical output. The final runner now records timing but does not use it as a correctness gate.
- Octave direct initially failed because this Octave build lacks RapidJSON-backed `jsonencode`; direct scripts now write metrics JSON with portable `fprintf`.
- Nektar direct initially failed because the solver was invoked with a path duplicated under `cwd`; final runs invoke the session file by basename.

These fixes are reflected in final successful artifacts and focused test results.

## 7. Interpretation

### What This Round Supports

- Real Octave execution works across `extension`, `direct`, and `agent` lanes for the selected first-round cases.
- Real Nektar direct execution works for the selected ADRSolver cases and produces stable L2/Linf values across two repeats.
- MHE benchmark infrastructure is now useful for finding real portability and capability bugs that dry-run could not expose.
- MHE extension/agent lanes provide stronger workflow structure where implemented: declared specs, validation, evidence files, summaries, comparison bundles, and capability skips.

### What This Round Does Not Support

- It does not prove MHE extension improves Octave numerical accuracy over direct Claude Code; both passed the selected Octave cases.
- It does not prove MHE extension improves solver runtime; the sample size is small and timing variance exists.
- It does not prove Nektar MHE extension numerical capability; real extension/agent Nektar lanes are skipped by current implementation.
- It does not demonstrate adaptive LLM repair yet; current agent lane is still mostly Claude proposal plus fixed extension pipeline, not a multi-step scientific repair loop.

## 8. MHE Extension Optimization Backlog

| ID | Area | Symptom | Evidence | Suggested fix | Priority |
|---|---|---|---|---|---|
| B1 | Nektar real execution coverage | Extension/agent real lanes always skipped | `.runs/real-repeated-20260428/nektar-final-*/nektar-pde-benchmark/*/*/summary.json` | Implement reference `.tst`/`.xml` replay through `metaharness_ext.nektar` and write validation/evidence bundles | High |
| B2 | Agent session mapping | Nektar agent cannot route proposal into extension replay | skip reason: `real Nektar agent replay requires a dedicated extension session mapping` | Add structured proposal-to-session-plan mapping and extension validation gate | High |
| B3 | Repeated-run aggregation | Repeats are separate roots and manually aggregated | final roots under `.runs/real-repeated-20260428/*-final-*` | Add `--repeat` or an aggregation command with median/IQR/flaky flags | High |
| B4 | Timing statistics | Nektar direct median changed from `3.97s` to `2.21s` across two repeats | `nektar-final-1` / `nektar-final-2` summaries | Separate solver runtime, driver overhead, Claude overhead, and repeated-run timing distribution | Medium |
| B5 | Direct lane portability | Octave direct initially failed on `jsonencode` | pilot direct stderr under `.runs/real-repeated-20260428/octave-run-3/` | Keep generated direct scripts portable across Octave builds and validate metrics file before comparison | Medium |
| B6 | Adaptive LLM participation | Agent pass does not include repair/parameter-selection loop | `attempt_count=1`, `repair_count=0` in final summaries | Add repair attempts driven by validation errors and stdout/stderr diagnostics | Medium |
| B7 | Evidence validation | Comparator verdicts do not yet deeply score missing evidence quality | comparison bundles in final roots | Add required evidence existence checks and report missing evidence as workflow gap | Medium |

## 9. Boss-Facing Conclusion

目前我们已经完成了从 dry-run 到真实工具执行的下一轮对比实验。

结论分两层：

1. **数值求解优劣**：Octave 的真实重复实验中，MHE extension、agent、direct Claude Code 三条 lane 都能通过选定 case，因此不能说 MHE extension 在 Octave 数值精度上更强。Nektar 的真实重复实验中，direct lane 已经能跑真实 solver 并解析 L2/Linf，但 MHE extension/agent 真实 replay 还没有实现，所以也不能说 MHE extension 在 Nektar 数值求解上优于 direct。
2. **Workflow 优劣**：MHE extension 的优势更清楚地体现在 workflow：结构化 case spec、固定执行边界、validation、evidence、summary schema、comparison bundle、capability skip 和可追溯报告。真实运行还暴露出 dry-run 看不到的问题，并把它们转成了明确 backlog。

下一阶段应该优先做 Nektar real extension replay、agent session mapping、重复运行聚合和 LLM repair loop。只有当 agent 能在真实 solver failure 后参与诊断、修复、参数选择并提升成功率时，才能把当前的 workflow 优势进一步转化为真实 scientific-computing agent 优势。
