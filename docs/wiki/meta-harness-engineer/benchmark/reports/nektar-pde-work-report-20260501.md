# Nektar PDE Benchmark Work Report

> Date: 2026-05-01 | Scope: Nektar PDE benchmark workflow, real-run evidence, reportability, and next actions

## Executive Summary

The Nektar PDE benchmark work has moved from a dry-run-only workflow demonstration into a partially real, evidence-backed comparison framework. The current implementation can run three workflow lanes (`extension`, `direct`, and `agent`), capture Claude proposal evidence, execute bounded real Nektar solver workflows for selected ADRSolver cases, parse L2/Linf norms, aggregate comparison bundles, and surface preflight/metric details in generated reports.

The strongest current conclusion is a workflow-quality conclusion: MHE benchmark drivers improve controllability, provenance, preflight visibility, failure classification, and artifact completeness. Current evidence does not prove that MHE extension or agent workflows are numerically superior to direct Claude Code, nor does it prove broad Nektar solver-family coverage. Numerical and performance claims require more real solver families, retained repeated-run artifacts, and formal administrator-approved report scope.

The highest-value next work is to convert the remaining capability boundaries into auditable evidence and then expand real execution coverage in a gated order: refresh generated dry-run artifacts with capability skip evidence, validate extension replay for DiffusionSolver and CompressibleFlowSolver, then run repeated real Phase B/C comparisons from durable `/var/tmp/mhe-runs/<run-id>` roots.

## Work Completed

### 1. Benchmark Driver Foundation

The `nektar-pde` suite is implemented as a runnable benchmark-driver layer rather than an ad hoc script collection.

Implemented capabilities:

- Six first-round benchmark cases are catalogued: `advection-1d`, `diffusion-2d`, `advdiff-2d`, `advdiff-imex-2d`, `taylor-vortex-2d`, and `euler-1d`.
- Three workflow lanes are supported: deterministic `extension`, Claude `direct`, and MHE `agent`.
- Case specs preserve `.tst` and `.xml` source references.
- `.tst` parsing extracts solver executable, parameters, reference metrics, and tolerance values.
- Solver stdout parsing extracts `L 2 error` and `L inf error` metrics with variable names.
- Lane summaries include status, metrics, metric diffs, missing metrics, evidence files, attempt counts, LLM calls, preflight status, proposal contract status, and failure category.

Key implementation files:

- `src/metaharness/benchmark_drivers/nektar_cases.py`
- `src/metaharness/benchmark_drivers/nektar_runner.py`
- `src/metaharness/benchmark_drivers/compare.py`
- `tests/test_benchmark_drivers_nektar.py`

### 2. Real-Mode Preflight Evidence

The Nektar preflight path now distinguishes dry-run capability probing from real reference validation.

Current behavior:

- In dry-run mode, preflight probes tool visibility and file availability without executing `Tester`.
- When `--allow-real-tools` is set and `Tester` plus `.tst` are available, the runner executes `Tester <case.tst>`.
- Preflight writes `tester.stdout.log`, `tester.stderr.log`, and `tester_summary.json`.
- `tester_summary.json` records `preflight_executed`, `tester_command`, `tester_return_code`, and `status` values such as `ready`, `reference_failed`, `reference_timeout`, or `missing_files`.

Value:

- Reviewers can separate environment readiness from solver execution evidence.
- Failed reference validation is visible as preflight evidence rather than being conflated with Claude proposal quality.
- Dry-run safety remains intact because no real external tools execute unless explicitly enabled.

### 3. Real-Claude Phase C Evidence

Real Claude and real Nektar solver smoke/repeat runs have been completed for selected ADRSolver cases.

Evidence roots documented in the analysis report:

- `.runs/nektar-real-claude-phase-c-20260430`
- `.runs/nektar-phase-c-promptfix-20260430`
- `/tmp/mhe-runs/nektar-phase-c-advdiff2d-20260501`
- `/var/tmp/mhe-runs/nektar-phase-c-advdiff-imex2d-path-20260501`

Observed successful Phase C repeated cases:

| Case | Direct Passed / Runs | Agent Passed / Runs | Notes |
|---|---:|---:|---|
| `advection-1d` | 3 / 3 | 3 / 3 | Prompt/preflight fix validated. |
| `advdiff-2d` | 3 / 3 | 3 / 3 | Real solver and real Claude proposals both stable. |
| `advdiff-imex-2d` | 3 / 3 | 3 / 3 | Required explicit Claude binary and explicit Nektar PATH. |

Important interpretation:

- These runs prove that direct and agent lanes can be wired to stable executable Nektar workflows for selected ADRSolver cases.
- They do not prove broad solver-family coverage.
- They do not prove MHE numerical superiority because both lanes produced matching solver metrics for the selected reference cases.
- They provide workflow evidence: bounded prompts, proposal preflight, executable artifact paths, stable repeat accounting, and clearer failure classification.

### 4. Generated Report Improvements

The comparator/reporting layer now surfaces more reviewer-facing evidence directly in generated reports and bundles.

Implemented report improvements:

- `metric_rows` are included in `result_bundle.json`.
- Generated Markdown reports include `## Metric details` tables.
- `elapsed_seconds` is excluded from scientific metric detail rows so L2/Linf rows remain readable.
- `preflight_rows` are included in `result_bundle.json`.
- Generated Markdown reports include `## Preflight summaries` when preflight artifacts exist.

Value:

- Reviewers no longer need to manually open every lane directory to find L2/Linf values or preflight status.
- Real preflight evidence can be discussed in reports without overstating solver conclusions.
- Metric-level evidence becomes easier to compare across direct and agent lanes.

### 5. Capability-Gated Skip Artifacts

The latest safe implementation slice makes Nektar capability skips auditable.

Before this change, a capability-gated extension case could produce only a skipped summary. That made the skip truthful but not sufficiently reviewable. The runner now writes explicit skip artifacts for capability-gated extension cases:

- `source_refs.json`
- `capability_status.json`

`capability_status.json` records:

- `status="capability_gated"`
- `promotion_ready=false`
- `missing_capabilities`
- `solver_binary`
- `solver_family`
- `plan_status="extension_dispatch_unverified"`
- source reference provenance

For `euler-1d`, the focused test verifies:

- the extension lane remains skipped;
- `source_refs.json` and `capability_status.json` are included in `summary.evidence_files`;
- `promotion_ready` is false;
- the missing capability is `nektar_compressible_solver_extension_dispatch`;
- the solver binary is `CompressibleFlowSolver`.

Value:

- Skips are now explicit scientific capability boundaries, not silent omissions.
- Reviewers can inspect exactly what source files were not promoted and why.
- The artifact contract matches the broader unsupported-capability pattern already used in the QCompute/ABACUS bridge work.

## Current Evidence Assessment

### What Is Well Supported

The current evidence supports these claims:

1. The Nektar benchmark suite has runnable, repeatable benchmark-driver plumbing.
2. Dry-run mode is safe and does not execute external Nektar tools.
3. Real-tool mode can execute `Tester` preflight when explicitly enabled.
4. Real-Claude Phase C can run selected ADRSolver cases successfully with bounded prompt contracts.
5. Direct and agent lanes preserve Claude proposal artifacts, solver logs, metric summaries, and comparison bundles.
6. Generated reports can now surface metric and preflight details without manual artifact inspection.
7. Capability-gated extension skips can now preserve provenance and missing-capability evidence.

### What Is Not Yet Proven

The current evidence does not support these stronger claims:

1. MHE agent is numerically more accurate than direct Claude Code.
2. MHE extension or agent lanes are faster than direct Claude Code.
3. Nektar extension replay is complete for all solver families.
4. DiffusionSolver and CompressibleFlowSolver are fully validated through the same extension-dispatch path as ADRSolver cases.
5. Real Claude repair behavior is generally superior across Nektar cases.
6. The benchmark has a complete formal repeated-run report suitable for broad product claims.

### Main Risk Areas

| Risk | Impact | Mitigation |
|---|---|---|
| Overclaiming numerical superiority | Misleading report conclusions | Keep conclusions separated into workflow quality vs solver quality. |
| Incomplete solver-family coverage | False sense of benchmark completeness | Keep `euler-1d` gated until CompressibleFlowSolver dispatch is validated. |
| External run-root loss | Missing audit trail for real repeated runs | Preserve `/var/tmp/mhe-runs/<run-id>` or copy comparison bundles into durable storage. |
| PATH / Claude binary mismatch | Real runs fail before solver execution | Always set Nektar PATH and pass executable `--claude-binary`. |
| Proposal-budget failures | Misclassified as solver failures | Continue using `proposal_max_turns` and proposal preflight classification. |
| Report drift | Docs describe behavior no longer matching code | Keep method docs, experiment report, and tests updated in the same slice. |

## Detailed Analysis

### Workflow Quality

The MHE benchmark layer is now strongest as a workflow-governance tool. Compared with direct manual Claude Code usage, it offers:

- standardized case specs;
- fixed lane directories;
- normalized summary schemas;
- explicit preflight/proposal status;
- retained stdout/stderr logs;
- attempt logs and LLM call counts;
- metric diff computation against references;
- generated CSV/Markdown/JSON comparison bundles;
- auditable skipped-capability artifacts.

This is a meaningful product-facing advantage, but it should be described as reproducibility and controllability, not as solver intelligence or numerical superiority.

### Numerical Evidence

For the successful ADRSolver Phase C cases, direct and agent lanes both reproduced expected solver metric outputs. This is good evidence that the workflow can execute correctly, but it is not evidence that one lane solves the PDE better. The same Nektar solver is doing the numerical work, and the current task is primarily session materialization, execution, parsing, and evidence capture.

Numerical conclusions require:

- retained raw solver logs;
- repeated runs across more cases;
- stable metric diffs;
- timing medians and variance;
- clear dependency skip handling;
- solver-family-specific validation.

### Agent vs Direct Comparison

The current comparison is best framed as follows:

- Direct Claude Code is flexible and can generate runnable session proposals, but it needs strict prompt contracts and preflight checks to avoid non-reproducible behavior.
- MHE agent workflow adds structure around the proposal: typed evidence, stable execution boundaries, validation, provenance, and comparator automation.
- The practical advantage to measure next is not raw solver accuracy, but pass rate, failure diagnosis quality, repair traceability, and reproducibility under repeated real execution.

### Capability Boundary

`euler-1d` remains the most important sentinel case. It represents CompressibleFlowSolver coverage and should stay gated until extension dispatch is validated. The new `capability_status.json` artifact makes this boundary explicit and gives reviewers enough information to decide whether the case is ready for promotion.

The `diffusion-2d` case is now marked replay-enabled in tests and should be treated separately from `euler-1d`: its next need is validation evidence, not continued blanket gating.

## Recommended Next Actions

### Priority 1 — Refresh Dry-Run Artifacts With New Skip Evidence

Run a safe dry-run for `euler-1d` extension and a suite comparison so generated artifacts include `source_refs.json` and `capability_status.json`.

Suggested commands:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite nektar-pde --lanes extension --cases euler-1d --runs-root .runs/nektar-capability-skip-refresh
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite nektar-pde --runs-root .runs/nektar-capability-skip-refresh
```

Acceptance criteria:

- `extension/euler-1d/source_refs.json` exists.
- `extension/euler-1d/capability_status.json` exists.
- `summary.json` lists both files in `evidence_files`.
- Comparison output preserves the skipped status without treating it as a failed solver run.

### Priority 2 — Add Generated-Report Surfacing for Capability Skip Rows

The artifact files now exist, but generated reports do not yet have a dedicated `## Capability gates` table. Add comparator support to surface capability skip rows in `result_bundle.json` and Markdown reports.

Recommended fields:

- `case_id`
- `lane`
- `status`
- `promotion_ready`
- `missing_capabilities`
- `solver_binary`
- `solver_family`
- `plan_status`
- `source_refs_path`
- `capability_status_path`

Acceptance criteria:

- `result_bundle.json` includes `capability_gate_rows`.
- `comparison_report.md` includes a `## Capability gates` section when artifacts exist.
- Tests cover malformed or missing capability status files without breaking report generation.

### Priority 3 — Validate `diffusion-2d` Extension Replay

Because `diffusion-2d` is no longer capability-gated, the next useful solver-family expansion should validate DiffusionSolver replay in a controlled way.

Recommended approach:

1. Start with dry-run artifact refresh for `diffusion-2d`.
2. Run real-tool extension or direct lane only after confirming local `DiffusionSolver` availability.
3. Capture `Tester` preflight before interpreting solver results.
4. Keep direct/agent real-Claude runs out of scope until extension/direct real-tool execution is stable.

Acceptance criteria:

- `tester_summary.json` records real preflight status.
- Solver stdout includes parseable L2/Linf rows or a clear solver-specific failure.
- Report classifies dependency skip, runner bug, or solver failure separately.

### Priority 4 — Keep `euler-1d` as a CompressibleFlowSolver Sentinel

Do not promote `euler-1d` until CompressibleFlowSolver extension dispatch is verified.

Promotion prerequisites:

- Extension dispatch mapping exists for CompressibleFlowSolver.
- Real preflight can run `Tester <Euler1D.tst>` or a documented equivalent.
- Solver execution writes parseable `l2_error_rho` / `linf_error_rho` metrics.
- Validation tolerances match `.tst` references.
- Capability status changes from `promotion_ready=false` only after a passing real-tool test exists.

### Priority 5 — Formalize Repeated Real-Run Report

After the artifact/reporting improvements above, produce a formal repeated real-run report from durable roots.

Recommended run-root policy:

- Use `.runs/` only for small dry-runs and local smoke artifacts.
- Use `/var/tmp/mhe-runs/<run-id>` for real repeated runs when `/home` is space-constrained.
- Always record external run roots in reports.
- Copy final comparison bundles into a durable location if `/var/tmp` retention is uncertain.

Recommended Nektar Phase C command pattern:

```bash
NEKTAR_BIN=/home/linden/usr/nektar/nektar-5.9.0/bin
CLAUDE_BIN=/var/tmp/npm-cache/_npx/becf7b9e49303068/node_modules/.bin/claude
PATH="$NEKTAR_BIN:$PATH" PYTHONPATH=src python -m metaharness.cli benchmark-run --suite nektar-pde --lanes direct,agent --cases advection-1d,advdiff-2d,advdiff-imex-2d --runs-root /var/tmp/mhe-runs/nektar-phase-c-real-claude-repeat --allow-real-tools --allow-real-claude --claude-binary "$CLAUDE_BIN" --claude-model cc-gpt-5.5 --claude-max-turns 10 --repeat 3
PATH="$NEKTAR_BIN:$PATH" PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite nektar-pde --runs-root /var/tmp/mhe-runs/nektar-phase-c-real-claude-repeat --allow-real-tools --allow-real-claude --claude-binary "$CLAUDE_BIN" --claude-model cc-gpt-5.5 --claude-max-turns 10 --repeat 3
```

Acceptance criteria:

- `repeat_summary.json` exists.
- `result_bundle.json` contains metric, preflight, and capability evidence rows where applicable.
- Report separates solver execution, Claude proposal quality, workflow evidence, and non-claims.

## Recommended Decision for Project Administrators

The project should position the current result as a benchmark-governance milestone, not a solver-performance milestone.

Recommended wording:

> Current Nektar evidence does not prove MHE numerical or runtime superiority. It does show that MHE benchmark workflows make scientific agent runs more controllable, reproducible, diagnosable, and reviewable through structured specs, gated real-tool execution, proposal preflight, retained evidence, comparator bundles, and explicit capability boundaries.

Before making stronger claims, require:

1. repeated real-tool runs across more solver families;
2. durable artifact retention;
3. generated report surfacing for capability gates;
4. administrator approval of the report scope;
5. explicit separation of workflow-quality claims from numerical-quality claims.

## Immediate Recommended Slice

The next implementation slice should be small and safe:

1. Add comparator/report support for `capability_status.json` rows.
2. Add tests proving capability gates appear in `result_bundle.json` and Markdown reports.
3. Run a dry-run artifact refresh for `euler-1d` only.
4. Update the Nektar analysis report with the generated capability-gate table evidence.

This slice improves reviewer visibility without requiring real external tools and directly builds on the latest capability-skip artifact work.

## Follow-up Implementation Status

The immediate safe slice has been implemented:

- Comparator output now includes `evidence_context.capability_gate_rows`.
- Generated comparison and analysis reports include `## Capability gates` when capability artifacts exist.
- A safe `.runs/nektar-capability-skip-refresh` dry-run produced reviewer-facing `euler-1d` gate evidence.
- Focused tests now cover valid, malformed, and missing `capability_status.json` cases so report generation degrades safely instead of crashing or hiding incomplete evidence.

The controlled `diffusion-2d` dry-run refresh has also been completed:

- Run root: `.runs/nektar-diffusion-dry-refresh`
- Compare bundle: `.runs/nektar-diffusion-dry-refresh/nektar-pde-benchmark/comparison/result_bundle.json`
- Generated report: `.runs/nektar-diffusion-dry-refresh/nektar-pde-benchmark/comparison/comparison_report.md`
- Result: `extension`, `direct`, and `agent` all passed in dry-run mode; verdict `all_passed`; `real_tools=false`; `real_claude=false`; preflight status `available`; `preflight_executed=false`.

The next unimplemented recommendation is real DiffusionSolver preflight/execution, but that must wait for explicit real-tool authorization and environment confirmation. Until then, the truthful claim is only that `diffusion-2d` dry-run benchmark wiring and report generation are validated.
