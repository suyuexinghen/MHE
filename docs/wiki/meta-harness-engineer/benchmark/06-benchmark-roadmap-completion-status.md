# 06. Benchmark Roadmap Completion Status

> 版本：v0.3 | 范围：`01` / `02` / `03` benchmark roadmap | 日期：2026-04-30

## 6.1 总体结论

The benchmark roadmap is implemented as a runnable benchmark-driver layer with safe default dry-run behavior. It now supports both independent suites described by the planning documents:

1. `octave-native`: 10 GNU Octave native numerical cases.
2. `nektar-pde`: 6 Nektar++ PDE regression cases.

Both suites support `extension`, `direct`, and `agent` lanes, produce normalized summaries, write Claude CLI evidence in LLM lanes, and generate comparison CSV / Markdown / JSON bundles. Real external execution remains opt-in through `--allow-real-tools`.

This status report intentionally does not claim that all real-mode scientific workflows are complete. It distinguishes implemented harness/comparison behavior from pending real solver execution depth. As of 2026-04-29, Octave has additional bounded evidence for real-Claude preflight traceability and controlled failing-fixture repair classification, but not for numerical superiority, general repair ability, or solver performance.

## 6.2 Implemented components

| Roadmap item | Status | Evidence |
|---|---|---|
| Core benchmark models | Complete | `src/metaharness/benchmark_drivers/models.py` |
| Deterministic IO layout | Complete | `src/metaharness/benchmark_drivers/io.py` |
| Run manifest capture | Complete | `src/metaharness/benchmark_drivers/manifests.py` |
| Claude CLI brain adapter | Complete | `src/metaharness/benchmark_drivers/claude_cli.py` |
| Octave case catalog | Complete | `src/metaharness/benchmark_drivers/octave_cases.py` |
| Octave generated scripts | Complete for first-round cases | `src/metaharness/benchmark_drivers/octave_scripts.py` |
| Octave lane runner | Complete for dry-run, real-mode foundation, proposal preflight, and controlled repair classification | `src/metaharness/benchmark_drivers/octave_runner.py` |
| Nektar case catalog | Complete | `src/metaharness/benchmark_drivers/nektar_cases.py` |
| Nektar `.tst` parser | Complete | `src/metaharness/benchmark_drivers/nektar_runner.py` |
| Nektar direct real-mode foundation | Complete | `src/metaharness/benchmark_drivers/nektar_runner.py` |
| Nektar preflight metadata | Complete as capability probe | `.runs/benchmark-wiki/nektar-pde-benchmark/preflight/*/tester_summary.json` |
| Comparator and reports | Complete | `src/metaharness/benchmark_drivers/compare.py` |
| CLI integration | Complete | `src/metaharness/cli.py` |
| Focused tests | Complete | `tests/test_benchmark_drivers_*.py` |

## 6.3 Generated benchmark artifacts

Dry-run artifacts were generated under `.runs/benchmark-wiki/`:

- `.runs/benchmark-wiki/octave-native-benchmark/comparison/summary_table.csv`
- `.runs/benchmark-wiki/octave-native-benchmark/comparison/comparison_report.md`
- `.runs/benchmark-wiki/octave-native-benchmark/comparison/result_bundle.json`
- `.runs/benchmark-wiki/octave-native-benchmark/comparison/run_manifest.json`
- `.runs/benchmark-wiki/octave-native-benchmark/reports/octave-native-analysis-report.md`
- `.runs/benchmark-wiki/octave-native-benchmark/reports/octave-native-backlog.md`
- `.runs/octave-real-claude-preflight-smoke-20260429-visible/octave-native-benchmark/comparison/result_bundle.json`
- `.runs/octave-real-claude-preflight-smoke-20260429-visible/octave-native-benchmark/comparison/run_manifest.json`
- `.runs/benchmark-wiki/nektar-pde-benchmark/comparison/summary_table.csv`
- `.runs/benchmark-wiki/nektar-pde-benchmark/comparison/comparison_report.md`
- `.runs/benchmark-wiki/nektar-pde-benchmark/comparison/result_bundle.json`
- `.runs/benchmark-wiki/nektar-pde-benchmark/comparison/run_manifest.json`
- `.runs/benchmark-wiki/nektar-pde-benchmark/reports/nektar-pde-analysis-report.md`
- `.runs/benchmark-wiki/nektar-pde-benchmark/reports/nektar-pde-backlog.md`

The wiki-level analysis files are:

- `04-octave-native-experiment-analysis.md`
- `05-nektar-pde-experiment-analysis.md`
- `06-benchmark-roadmap-completion-status.md`

## 6.4 Acceptance criteria status

| Acceptance criterion | Status | Notes |
|---|---|---|
| Two independent suites, no category-error comparison | Complete | Octave and Nektar reports are separate. |
| Octave has at least 10 cases | Complete | 10 dry-run cases emitted and compared. |
| Nektar has at least 3/6 cases attempted or unavailable reasons | Complete | 6 cases emitted; 2 extension cases are capability skips. |
| Three workflow lanes | Complete | `extension`, `direct`, `agent` supported by CLI and summaries. |
| Default run avoids real external tools | Complete | Real tools require `--allow-real-tools`. |
| Claude CLI evidence captured | Complete | Direct and agent lanes write prompt/command/stdout/stderr/result/proposal evidence. |
| Comparator writes bundle and reports | Complete | CSV, Markdown, JSON, manifest, report/backlog files generated. |
| Schema failure is explicit | Complete | Malformed summaries are converted to `schema_failed` with `schema_validation.json`. |
| Proposal preflight status is explicit | Complete for Octave direct/agent | `proposal_contract_status`, `preflight_status`, and `failure_category` are emitted and compared. |
| Controlled repair classification is explicit | Complete for focused Octave fixture | `repair_outcome`, `diagnostics_files`, `agent_repaired_success`, and `unrepaired_failure` distinguish repaired success from unrepaired failure. |
| Reports explain zero hypothesis, observations, limitations, backlog | Complete at wiki level | `04`, `05`, and this file cover these points. |
| Repeated real-run formal report | Pending | Requires explicit real execution and repeated runs. |

## 6.5 Known limitations

- Dry-run results validate workflow mechanics, not solver accuracy.
- Octave direct real mode depends on Claude proposal quality and `octave-cli` availability.
- Nektar extension real-mode replay is not complete for every solver family.
- Nektar agent real-mode replay needs a dedicated proposal-to-extension session mapping.
- Repeated-run statistics and `flaky_numeric` aggregation are not yet implemented.
- Real-Claude preflight smoke currently demonstrates `proposal_max_turns` classification, not successful solver execution.
- Controlled repair tests demonstrate repair classification mechanics, not general agent repair ability.
- Exact source line references for Octave BIST-derived cases can be improved.

## 6.6 Manager-facing evidence status

Current evidence supports a workflow-quality claim: MHE benchmark drivers now make proposal generation, preflight failure, controlled repair classification, evidence files, and comparator verdicts auditable. The clean short statement is:

> Benchmark now has real-tool/real-Claude smoke traceability and a controlled repair-classification fixture; the next gap is broader real-solver repeated runs before any performance, robustness, or numerical-superiority claim.

This statement should not be shortened to “agent repair works” or “MHE solves better.” The evidence only supports real-Claude preflight classification plus controlled failing-fixture repair classification.

## 6.7 Next formal real-run protocol

The next benchmark iteration must convert the current workflow-quality evidence into real-run evidence without overclaiming. It should run in three gated phases so dependency skips, LLM proposal failures, solver failures, and numerical results remain separable.

### Phase A — safe repeated dry-run smoke

Purpose: verify repeat aggregation, comparator output, and report wiring without invoking external solvers or real Claude.

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes extension,direct,agent --cases sinc-values --runs-root .runs/octave-repeat-dry --repeat 3 --adaptive-agent
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-repeat-dry --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite qcompute-abacus --lanes extension,direct,agent --cases h2-fcidump-vqe-proxy --runs-root .runs/qcompute-repeat-dry --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite qcompute-abacus --runs-root .runs/qcompute-repeat-dry --repeat 3
```

Acceptance: `repeat_summary.json`, `result_bundle.json`, and generated reports exist; any `flaky_status` or `flaky_timing` flags are reported as workflow observations only.

### Phase B — dependency-gated real solver runs

Purpose: establish real solver execution evidence before introducing real Claude proposal variability.

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes extension --cases sinc-values,roots-cubic,expm-jordan-2x2 --runs-root .runs/octave-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite nektar-pde --lanes direct --cases advection-1d,advdiff-2d,advdiff-imex-2d --runs-root .runs/nektar-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite nektar-pde --runs-root .runs/nektar-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite qcompute-abacus --lanes extension --cases h2-fcidump-vqe-proxy --runs-root .runs/qcompute-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite qcompute-abacus --runs-root .runs/qcompute-real-solver --allow-real-tools --repeat 3
```

Acceptance: dependency skips are preserved as skips, not failures; real solver metrics, timing medians, and flaky flags are reported only for cases that actually execute.

### Phase C — real Claude + real solver workflow comparison

Purpose: compare direct Claude and MHE agent workflow outcomes after real solver execution has a baseline. In this repository, `--allow-real-claude` defaults Claude CLI to `--permission-mode bypassPermissions` unless `--claude-permission-mode` is explicitly provided, so authorized benchmark runs do not stop for per-call permission prompts.

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes direct,agent --cases sinc-values,roots-cubic --runs-root .runs/octave-real-claude-repeat --allow-real-tools --allow-real-claude --claude-model cc-gpt-5.5 --claude-max-turns 12 --repeat 3 --adaptive-agent --max-repair-attempts 1
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-real-claude-repeat --allow-real-tools --allow-real-claude --claude-model cc-gpt-5.5 --claude-max-turns 12 --repeat 3
```

Acceptance: if Claude still reaches `proposal_max_turns`, report that as proposal-budget evidence. If proposals execute, compare pass rate, repair outcome, diagnostics count, elapsed time, and evidence completeness; do not claim numerical superiority unless repeated real solver metrics support it.

Only after Phase B/C should reports draw numerical conclusions about Octave, Nektar, or QCompute solver behavior. The first conclusion to seek is not “MHE solves better,” but whether MHE improves workflow success rate, failure diagnosis, repair traceability, and reproducibility under real execution.
