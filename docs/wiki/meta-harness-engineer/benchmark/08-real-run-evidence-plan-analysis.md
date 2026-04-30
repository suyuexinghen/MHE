# 08. Real-run Evidence Plan and Deeper Benchmark Analysis

> 版本：v0.1 | 生成依据：`06-benchmark-roadmap-completion-status.md`、`.runs/octave-repeat-dry-20260430/`、`.runs/qcompute-repeat-dry-20260430/` | 日期：2026-04-30

## 8.1 Executive conclusion

Current benchmark evidence does not prove that MHE extension workflows are numerically more accurate, faster, or more robust than direct Claude Code / Claude CLI workflows. The evidence does show that MHE benchmark drivers improve workflow controllability: lane separation, schema validation, evidence capture, preflight classification, repair-outcome classification, repeated-run aggregation, and manager-facing non-claim reporting are now auditable.

The next evidence gap is broader real solver repeated runs. The benchmark should first establish dependency-gated real solver baselines, then introduce real Claude proposal variability and adaptive repair. Until that happens, the truthful conclusion remains:

> MHE has evidence for better scientific workflow auditability, not yet for better numerical solving quality.

## 8.2 Evidence layers

| Layer | Current evidence | Supports | Does not support |
|---|---|---|---|
| Dry-run suite coverage | Octave, Nektar, and QCompute benchmark suites produce summaries and comparison bundles | Harness wiring, schema, lane layout, report generation | Real solver accuracy, timing, convergence |
| Real-Claude Octave preflight smoke | `.runs/octave-real-claude-preflight-smoke-20260429-visible/` records `proposal_max_turns` for `sinc-values` direct/agent lanes | Real Claude traceability and failure classification | Solver execution success or repair success |
| Controlled repair fixture | Focused Octave tests cover `repaired_success`, `unrepaired_failure`, diagnostics, and comparator verdicts | Repair artifact semantics and failure taxonomy | General agent repair ability |
| Repeated dry-run smoke | `.runs/octave-repeat-dry-20260430/` and `.runs/qcompute-repeat-dry-20260430/` use `--repeat 3` | Repeat aggregation and report plumbing | Real repeated-run stability |

## 8.3 Test planning roadmap

### Phase A — safe repeated dry-run smoke

Run this phase whenever benchmark schema, comparator, repeat aggregation, or report generation changes. It is safe for CI-like local validation because it does not invoke real solvers or real Claude.

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes extension,direct,agent --cases sinc-values --runs-root .runs/octave-repeat-dry --repeat 3 --adaptive-agent
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-repeat-dry --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite qcompute-abacus --lanes extension,direct,agent --cases h2-fcidump-vqe-proxy --runs-root .runs/qcompute-repeat-dry --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite qcompute-abacus --runs-root .runs/qcompute-repeat-dry --repeat 3
```

Acceptance criteria:

- `comparison/repeat_summary.json` exists.
- `comparison/result_bundle.json` includes `repeat_count` and repeat rows.
- Reports list any `flaky_status` or `flaky_timing` flags without treating them as solver evidence.

### Phase B — real solver baseline

Run this phase only when the user explicitly authorizes real tools. It should avoid real Claude at first so dependency skips and solver failures are not mixed with proposal failures.

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes extension --cases sinc-values,roots-cubic,expm-jordan-2x2 --runs-root .runs/octave-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite nektar-pde --lanes direct --cases advection-1d,advdiff-2d,advdiff-imex-2d --runs-root .runs/nektar-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite nektar-pde --runs-root .runs/nektar-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite qcompute-abacus --lanes extension --cases h2-fcidump-vqe-proxy --runs-root .runs/qcompute-real-solver --allow-real-tools --repeat 3
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite qcompute-abacus --runs-root .runs/qcompute-real-solver --allow-real-tools --repeat 3
```

Acceptance criteria:

- Missing binaries or unavailable dependencies are reported as skips.
- Executed cases record real metrics and timing values.
- Repeated-run medians and flaky flags are computed from real execution only.
- Reports avoid direct-vs-agent conclusions because real Claude is not in this phase.

### Phase C — real Claude + real solver workflow comparison

Run this phase only after Phase B has a usable solver baseline. It is the first phase that can evaluate whether MHE improves workflow success rate or repair traceability under real execution. In this repository, `--allow-real-claude` now defaults Claude CLI to `--permission-mode bypassPermissions` unless `--claude-permission-mode` is explicitly provided, so the authorized benchmark can run without per-call user prompts.

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes direct,agent --cases sinc-values,roots-cubic --runs-root .runs/octave-real-claude-repeat --allow-real-tools --allow-real-claude --claude-model cc-gpt-5.5 --claude-max-turns 12 --repeat 3 --adaptive-agent --max-repair-attempts 1
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-real-claude-repeat --allow-real-tools --allow-real-claude --claude-model cc-gpt-5.5 --claude-max-turns 12 --repeat 3
```

ACP-backed alternative, using the Claude agent ACP server instead of invoking Claude CLI directly:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite octave-native --lanes direct,agent --cases sinc-values,roots-cubic --runs-root .runs/octave-real-acp-repeat --allow-real-tools --allow-real-claude --brain-provider acp --acp-command npx @agentclientprotocol/claude-agent-acp --acp-env ACP_PERMISSION_MODE=acceptEdits --repeat 3 --adaptive-agent --max-repair-attempts 1
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite octave-native --runs-root .runs/octave-real-acp-repeat --allow-real-tools --allow-real-claude --brain-provider acp --repeat 3
```

Acceptance criteria:

- Proposal failures are classified separately from solver failures.
- `proposal_contract_status`, `preflight_status`, and `failure_category` are present for direct and agent lanes.
- Adaptive agent runs record `repair_outcome` and `diagnostics_files` when repair is attempted.
- The comparison discusses pass rate, diagnostics quality, evidence completeness, and repeated-run stability before any numerical-performance claim.

## 8.4 Executed validation on 2026-04-30

Safe validation was executed without real external tools.

| Command family | Result | Evidence root |
|---|---|---|
| Octave repeated dry-run smoke | Passed; `sinc-values` ran `extension`, `direct`, and `agent` lanes with `--repeat 3` | `.runs/octave-repeat-dry-20260430/` |
| QCompute repeated dry-run smoke | Passed; `h2-fcidump-vqe-proxy` ran `extension`, `direct`, and `agent` lanes with `--repeat 3` | `.runs/qcompute-repeat-dry-20260430/` |
| Focused benchmark driver tests | Passed: `53 passed` with `PYTHONPATH=src` | `tests/test_benchmark_drivers_cli.py`, `tests/test_benchmark_drivers_models.py`, `tests/test_benchmark_drivers_octave.py`, `tests/test_benchmark_drivers_qcompute_abacus.py` |
| Authorized real-Claude permission smoke | Passed; command evidence records `--permission-mode bypassPermissions` when `--allow-real-claude` is set and no explicit permission mode is provided | `.runs/permission-bypass-smoke-20260430/` |
| Authorized Octave real-Claude smoke | Executed without permission prompts; direct and agent lanes both classified `proposal_max_turns` at `--claude-max-turns 2` | `.runs/octave-real-claude-authorized-smoke-20260430/` |
| ACP provider missing-server smoke | Wrote ACP evidence paths and failed safely because the isolated MHE environment lacks the Aeloon ACP SDK import path/dependencies | `.runs/acp-provider-missing-smoke-20260430/` |
| ACP provider connected smoke | ACP transport connected through the Aeloon SDK root and recorded usage/session metadata, but the Claude ACP server returned empty `content` with `stop_reason = end_turn`; proposal generation is therefore blocked by empty ACP response content, not by MHE import/config wiring | `.runs/acp-provider-self-contained-smoke-20260430/` |
| ACP JSON diagnostic + ABACUS reviewer schema | Implemented local JSON-only diagnostic classification and `review_signoff.json` schema for ABACUS bridge evidence; this makes ACP reviewer evidence auditable once ACP content is stable, while preserving the human/scientific sign-off blocker | `src/metaharness/benchmark_drivers/acp_provider.py`, `src/metaharness_ext/qcompute/abacus_bridge.py`, `review_signoff.json` |
| Octave Phase B real-solver baseline | Passed; `sinc-values`, `roots-cubic`, and `expm-jordan-2x2` ran extension-only with `--allow-real-tools --repeat 3`; all 9 runs passed with real Octave 9.2.0 metrics, and timing flags were recorded where IQR/median was high | `.runs/octave-real-solver-phase-b-20260430/` |

A first focused pytest attempt without `PYTHONPATH=src` exposed stale/import-path-sensitive failures around `metaharness_ext.qcompute.abacus_bridge`. Re-running with the repository source path selected the current local code and passed. Future local benchmark verification should use `PYTHONPATH=src` consistently, matching the documented CLI command pattern.

## 8.5 Interpretation of the executed dry-run results

The 2026-04-30 repeat smoke validates repeat aggregation and report generation, not solver quality. The important observations are:

1. Octave `sinc-values` dry-run produced `all_passed` comparator output across all three lanes.
2. QCompute `h2-fcidump-vqe-proxy` dry-run produced `all_passed` comparator output across all three lanes.
3. Both runs wrote repeated summaries for three iterations.
4. Direct and agent lanes recorded fake/dry-run Claude evidence, not real proposal quality.
5. Metrics such as `max_abs_error = 0.0` and `energy_error = 0.0` remain reference echoes in dry-run mode.

Therefore, these runs strengthen confidence in benchmark infrastructure but do not change the numerical non-claim boundary. The authorized real-Claude smoke additionally proves that the local benchmark configuration can run Claude CLI in `bypassPermissions` mode, but the observed `proposal_max_turns` outcome remains proposal-budget evidence rather than solver evidence.

The Phase B Octave run changes the evidence boundary for the extension-only Octave baseline: it is now real solver evidence for three small native Octave cases, not a dry-run echo. It still does not compare against direct Claude or agent lanes, so the comparator verdict is intentionally `incomplete`. The useful facts are: all three cases passed over three real Octave runs, no dependency skips occurred, no LLM calls were made, and timing variability was flagged for `sinc-values` and `roots-cubic` because their median elapsed times are very small.

The ACP connected smoke changes the ACP boundary: MHE can import the Aeloon SDK, launch/connect to `@agentclientprotocol/claude-agent-acp`, and record session/usage metadata. Real ACP proposal generation remains blocked because the server returns empty `content` with `stop_reason = end_turn`; this is an upstream ACP collector/server behavior to investigate before treating ACP as a usable benchmark brain provider. The new JSON diagnostic and ABACUS `review_signoff.json` schema separate transport/proposal health from reviewer evidence: ACP can help produce auditable review artifacts once stable, but it does not replace administrator-approved ABACUS fixtures or human scientific sign-off.

## 8.6 Manager-facing message

A concise manager-facing summary is:

> We now have a benchmark framework that can repeatedly compare extension, direct, and agent lanes with auditable evidence and failure taxonomy. The Octave extension lane now has a small real-solver repeated baseline, while direct/agent superiority claims remain blocked until real Claude/agent proposal runs produce executable proposals and comparable solver outcomes.

Avoid these unsupported shortcuts:

- “MHE solves better than Claude Code.”
- “Agent repair works generally.”
- “Dry-run zero error proves solver correctness.”
- “Real-Claude preflight failure proves solver failure.”
- “ACP transport success proves ACP proposal generation works.”
- “Extension-only real Octave baseline proves MHE beats direct Claude or agent workflows.”

## 8.7 Next report after real runs

After Phase B or Phase C executes, create a follow-up report that includes:

1. dependency availability table;
2. per-case lane status table;
3. repeated-run timing table with median and IQR;
4. failure taxonomy table separating dependency skip, proposal failure, solver failure, schema failure, and repair failure;
5. evidence completeness table;
6. supported claims and explicit non-claims;
7. backlog items ranked by what most improves workflow evidence or numerical evidence.
