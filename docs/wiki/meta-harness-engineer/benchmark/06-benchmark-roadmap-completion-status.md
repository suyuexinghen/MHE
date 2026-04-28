# 06. Benchmark Roadmap Completion Status

> 版本：v0.1 | 范围：`01` / `02` / `03` benchmark roadmap | 日期：2026-04-28

## 6.1 总体结论

The benchmark roadmap is implemented as a runnable benchmark-driver layer with safe default dry-run behavior. It now supports both independent suites described by the planning documents:

1. `octave-native`: 10 GNU Octave native numerical cases.
2. `nektar-pde`: 6 Nektar++ PDE regression cases.

Both suites support `extension`, `direct`, and `agent` lanes, produce normalized summaries, write Claude CLI evidence in LLM lanes, and generate comparison CSV / Markdown / JSON bundles. Real external execution remains opt-in through `--allow-real-tools`.

This status report intentionally does not claim that all real-mode scientific workflows are complete. It distinguishes implemented harness/comparison behavior from pending real solver execution depth.

## 6.2 Implemented components

| Roadmap item | Status | Evidence |
|---|---|---|
| Core benchmark models | Complete | `src/metaharness/benchmark_drivers/models.py` |
| Deterministic IO layout | Complete | `src/metaharness/benchmark_drivers/io.py` |
| Run manifest capture | Complete | `src/metaharness/benchmark_drivers/manifests.py` |
| Claude CLI brain adapter | Complete | `src/metaharness/benchmark_drivers/claude_cli.py` |
| Octave case catalog | Complete | `src/metaharness/benchmark_drivers/octave_cases.py` |
| Octave generated scripts | Complete for first-round cases | `src/metaharness/benchmark_drivers/octave_scripts.py` |
| Octave lane runner | Complete for dry-run and real-mode foundation | `src/metaharness/benchmark_drivers/octave_runner.py` |
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
| Reports explain zero hypothesis, observations, limitations, backlog | Complete at wiki level | `04`, `05`, and this file cover these points. |
| Repeated real-run formal report | Pending | Requires explicit real execution and repeated runs. |

## 6.5 Known limitations

- Dry-run results validate workflow mechanics, not solver accuracy.
- Octave direct real mode depends on Claude proposal quality and `octave-cli` availability.
- Nektar extension real-mode replay is not complete for every solver family.
- Nektar agent real-mode replay needs a dedicated proposal-to-extension session mapping.
- Repeated-run statistics and `flaky_numeric` aggregation are not yet implemented.
- Exact source line references for Octave BIST-derived cases can be improved.

## 6.6 Next formal real-run protocol

When ready to produce a formal numerical report, run:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes extension,direct,agent --runs-root .runs/octave-real --allow-real-tools
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-real
```

For Nektar, start with supported ADRSolver cases before expanding solver families:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite nektar-pde --lanes direct --cases advection-1d,advdiff-2d,advdiff-imex-2d --runs-root .runs/nektar-real --allow-real-tools
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite nektar-pde --runs-root .runs/nektar-real
```

Only after those runs should the reports draw numerical conclusions about Octave or Nektar solver behavior.
