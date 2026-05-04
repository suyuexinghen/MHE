# MHE Closed-Loop Benchmark Automation

Use this skill to run a CI/CD-backed benchmark comparison workflow as a Claude-orchestrated closed loop. The loop applies only to the scoped MHE comparison suites, turns benchmark evidence into truthful conclusions, converts gaps into extension improvement plans, and reruns only the suites or cases affected by accepted improvements.

Do not implement the loop as a new repository controller command, background script, generated `loop_control.json`, or CI fanout unless the user explicitly asks for repository automation.

## Closed-Loop Lifecycle

Run the loop in this order:

1. **Compare** — inspect or run CI/CD-equivalent benchmark comparisons for scoped suites.
2. **Conclude** — summarize benchmark results from retained artifacts with strict claim boundaries.
3. **Analyze gaps** — identify extension weaknesses that block stronger future comparison claims.
4. **Plan** — produce a development plan or roadmap for the smallest evidence-producing improvement.
5. **Implement** — modify MHE extensions only when the user explicitly asks to proceed.
6. **Targeted rerun** — rerun only the affected suites, lanes, and cases after improvements.
7. **Update comparison list** — update human-facing conclusions and comparison-list tiers only when evidence changes.

Stop after each lifecycle pass with conclusions, improvement recommendations, and targeted rerun commands unless the user explicitly asks for implementation.

## Scope Lock

Only apply this closed-loop process to the comparison benchmark list:

- `octave-native`
- `nektar-pde`
- `qcompute-abacus`
- `fealpy-pde`
- `pycfd-pde`

Do not include unrelated or newly added extensions unless the user explicitly expands the comparison list and the suite onboarding gate is satisfied.

## Process Rules

Default to Claude-skill orchestration, not repo automation code.

Claude should directly read existing artifacts, summarize conclusions, draft backlog or roadmap content, and recommend targeted rerun commands in chat or requested docs. Keep analysis advisory by default. Use plan mode before non-trivial implementation. Do not implement multiple extension fixes blindly from a conclusion summary.

Ask before or stop before:

- promoting QEC or ABACUS bridge sentinels to real execution;
- changing the five-suite comparison scope;
- turning a skill recommendation into repository automation code;
- claiming numerical, runtime, solver, QEC, ABACUS bridge, or cross-suite superiority;
- auto-committing central conclusion updates;
- creating automatic PRs, issues, workflow fanout, or scheduled jobs.

## Allowed Existing Commands

It is OK to reuse existing benchmark commands:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite <suite> --lanes <lanes> --runs-root <root>
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite <suite> --runs-root <root>
PYTHONPATH=src python -m metaharness.cli benchmark-approval-check --suite <suite> --config-root .mhe
```

Do not add by default:

- `benchmark-loop-analyze` or similar CLI commands;
- `loop.py` controller modules;
- `loop_control.json`, `loop_summary.md`, or `rerun_targets.json` schemas;
- workflow steps that call a new loop controller;
- tests for a script-based loop controller.

## Inputs And Outputs

Required inputs for a lifecycle pass:

- benchmark index and conclusion docs;
- CI/CD blueprint, implementation plan, and roadmap docs;
- `.github/workflows/benchmark-*.yml` when workflow behavior matters;
- suite runner and case catalog files for affected extensions;
- relevant tests under `tests/test_benchmark_drivers_*.py` and suite-specific tests;
- retained artifacts under `.runs/**/<suite>-benchmark/`.

Artifact truth inputs include:

- lane `summary.json`;
- `attempt_log.json`;
- `comparison/result_bundle.json`;
- `comparison/summary_table.csv`;
- `comparison/comparison_report.md`;
- `comparison/approval_gate.json`;
- `comparison/run_manifest.json`;
- optional `comparison/repeat_summary.json`.

Expected outputs from an analysis pass:

- evidence classification per scoped suite;
- benchmark conclusion summary with non-claims;
- suite-specific extension improvement backlog;
- development plan or roadmap entries for accepted next steps;
- targeted rerun commands for affected suites and cases;
- comparison-list tier recommendation;
- central conclusion update when the user did not request chat-only output.

Never use chat memory alone as benchmark evidence.

## Core Claim Boundary

Never let CI/CD, approval status, dry-run pass, proxy execution, or artifact count become a scientific superiority claim.

Always separate:

- **Numerical/scientific quality** — real tools, real Claude where relevant, repeated runs, domain metrics, and scientific review.
- **Workflow quality** — schema, evidence bundles, lane separation, proposal provenance, repair evidence, skips, approval gates, and report automation.
- **Extension improvement needs** — runner fixes, dependency gates, backend labels, proposal contracts, repeat evidence, and sentinel promotion gates.

## Startup Checklist

Before drawing conclusions or planning improvements, inspect current files and artifacts:

1. `docs/wiki/meta-harness-engineer/benchmark/README.md`
2. `docs/wiki/meta-harness-engineer/benchmark/mhe-extension-comparison-conclusions.md`
3. `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-*.md`
4. `.github/workflows/benchmark-*.yml`
5. relevant suite runner and case catalog under `src/metaharness/benchmark_drivers/` or `src/metaharness_ext/`
6. relevant tests under `tests/test_benchmark_drivers_*.py` and suite-specific runner tests
7. artifacts under `.runs/**/<suite>-benchmark/`

## Evidence Classification

Classify each suite before recommending improvements:

- **Dry-run** — supports workflow/schema/report plumbing only.
- **Real-tool smoke** — supports selected extension-lane real execution, truthful dependency skip, or solver failure only.
- **Real-Claude comparison** — supports selected prompt/proposal/preflight/repair evidence only.
- **Repeated real-tool evidence** — supports selected pass-rate, flaky-status, and timing-stability evidence.
- **Repeated real-Claude evidence** — supports selected proposal pass-rate and repair-rate evidence.

For extension-only real-tool smoke, lane `extension/*/summary.json` is the primary truth source. Comparator rows may be `incomplete` because `direct` and `agent` lanes are intentionally absent.

## Skill-Driven Loop Procedure

### Inspect Results

For each scoped suite, read artifacts and classify:

- flags: `real_tools`, `real_claude`, `repeat_count`;
- lane statuses: passed, failed, skipped, schema_failed;
- verdicts: all_passed, capability_skip, incomplete, extension_baseline_failed, proposal failure patterns;
- approval status and excluded claims;
- proposal contract, preflight, repair outcome, repair count, and proposal source;
- missing metrics and domain-specific metric rows;
- dependency skips, capability skips, solver failures, and runner bugs.

### Summarize Conclusions

Use this structure:

- **Numerical/scientific quality** — what the evidence supports and what remains unproven.
- **Workflow quality** — what became more auditable or controllable.
- **Extension improvement backlog** — suite-specific changes needed before stronger claims.
- **Comparison-list update** — keep in dry-run, keep in smoke, move to repeat, move to real-Claude challenge, or remain blocked.
- **Non-claims** — explicit unsupported claims.
- **Next evidence needed** — smallest retained run/artifact needed to unlock the next tier.

When summarizing benchmark conclusions for the user, update `docs/wiki/meta-harness-engineer/benchmark/mhe-extension-comparison-conclusions.md` unless the user asks for chat-only output.

### Derive Extension Improvements

Map evidence to extension work:

- `octave-native`
  - Single smoke pass means repeat coverage is needed before timing or stability claims.
  - Useful improvements: stiffness cases, event handling, output/plot evidence, analytic-error retention.

- `nektar-pde`
  - `ADRSolver` crash, `execution_failed`, missing `l2_error_u`/`linf_error_u`, or session incompatibility means high-priority runner/preflight work.
  - Useful improvements: solver/session compatibility diagnosis, stderr classification, dependency-skip versus solver-crash separation, clean rerun root.

- `qcompute-abacus`
  - H2 proxy pass means proxy workflow evidence only.
  - Keep QEC and ABACUS H/S bridge blocked until backend adapter, decoder execution, syndrome sampling, converter evidence, repeated validation, and scientific review exist.

- `fealpy-pde`
  - One backend pass means only that backend has smoke evidence.
  - Useful improvements: backend-specific smoke cases, backend labels in summaries, retained L2/H1 metrics per backend.

- `pycfd-pde`
  - Environment skip means no real CI coverage claim.
  - Useful improvements: explicit `PYCFD_SRC_PATH` / dependency probe, truthful skip artifacts, short real-solver baseline with residual/timing/mesh metrics.

### Plan Development

For each recommended extension improvement, produce:

- target suite and case IDs;
- files likely to change;
- evidence gap being closed;
- implementation steps;
- focused tests;
- rerun command;
- claim unlocked if the rerun succeeds;
- claims still blocked.

Use plan mode for non-trivial implementation. Prioritize the smallest evidence-producing next step.

### Targeted Rerun Selection

After an extension improvement, recommend reruns like:

- failed/skipped extension case fixed:
  - `benchmark-run --suite <suite> --lanes extension --cases <case> --allow-real-tools`
- passing real-tool smoke promoted to repeat:
  - `benchmark-run --suite <suite> --lanes extension --cases <case> --allow-real-tools --repeat 3`
- real-Claude proposal/preflight issue fixed:
  - `benchmark-run --suite <suite> --lanes direct,agent --cases <case> --allow-real-claude`
- dry-run regression:
  - full comparison-list suite with `extension,direct,agent`.

Keep full PR dry-run coverage even when targeted reruns are used for improved suites.

## Comparison List Decision Matrix

| Tier decision | Trigger | Action | Forbidden interpretation |
|---|---|---|---|
| `keep_in_dry_run` | only dry-run workflow evidence exists | keep the suite in PR dry-run comparison | do not claim real solver execution |
| `keep_in_smoke` | single real-tool pass, dependency skip, solver failure, or unresolved runner issue | keep nightly/manual smoke coverage and backlog the blocker | do not claim repeat stability or superiority |
| `move_to_repeat` | selected real-tool smoke passes cleanly with retained metrics | add repeat-run review for the same suite/case | do not compare unrelated domain metrics as one score |
| `move_to_real_claude_challenge` | proposal/preflight/repair quality is the next evidence question | run controlled direct/agent prompts with `--allow-real-claude` | do not treat fake/fallback proposals as direct-Claude success |
| `remain_blocked` | sentinel, unsupported bridge, missing backend, or missing scientific gate remains unresolved | preserve explicit skip/block evidence | do not promote QEC, ABACUS H/S, or unsupported solver families |

Do not rewrite case catalogs just because a result improved. Update docs or workflow case selections only when evidence supports the tier change and the user accepts the direction.

## Multi-Teammate Operating Model

Use teammates when the loop spans evidence review, roadmap design, implementation, and verification. Keep roles separate so no single lane both writes and approves its own conclusion.

Recommended roles:

- **Evidence analyst** — reads artifacts, classifies suite evidence, and reports claim boundaries.
- **Extension planner** — maps evidence gaps to suite-specific improvement plans and rerun targets.
- **Implementer** — changes the selected extension only after user approval.
- **Verifier** — checks tests, rerun artifacts, comparison-list tier changes, and non-claims.
- **Lead synthesizer** — integrates teammate findings, updates docs, and stops at the right gate.

Use this handoff packet between teammates:

- suite and case IDs;
- evidence root and artifact paths;
- evidence class and lane status;
- failure or skip category;
- missing metrics;
- proposed extension change;
- targeted rerun command;
- claim unlocked if successful;
- claims still blocked.

For a single lifecycle pass, evidence analysis and improvement planning can run in parallel. Implementation must wait for an accepted plan. Verification must run after implementation or doc updates, not in the same authoring lane.

### Rehearsed Teammate Pattern

A 2026-05-03 rehearsal used a spawned `evidence-analyst` teammate for artifact classification while the main lane handled skill rewriting and improvement planning. The split was useful because evidence classification stayed separate from writing decisions, and the main lane could update the skill only after identifying the handoff fields needed by downstream planners.

When teammate pane capacity prevents spawning all planned roles, keep the evidence analyst as the highest-priority teammate and handle planning in the main lane. Record the fallback explicitly in the handoff: which role ran as a teammate, which role ran in the main lane, and which verifier step remains before claiming completion.

The same rehearsal produced a useful evidence handoff pattern: classify each scoped suite by evidence tier, comparison-list recommendation, evidence root, case status, next evidence needed, and doc drift. The evidence analyst flagged that current dated smoke evidence can conflict with older summary tables, so future loop runs must include a doc-drift check before reporting benchmark conclusions as current.

## Human Approval Gates

Ask before or stop before:

- implementing extension fixes after an advisory analysis pass;
- promoting a smoke case to repeated-run workflow coverage;
- promoting QEC or ABACUS bridge sentinels to real execution;
- changing the five-suite comparison scope;
- turning a skill recommendation into repository automation code;
- claiming numerical, runtime, solver, QEC, ABACUS bridge, or cross-suite superiority;
- auto-committing central conclusion updates;
- creating automatic PRs/issues/workflow fanout.

## Verification

For skill-driven analysis, verify by checking artifacts and command outputs rather than testing a new controller script.

Useful checks:

```bash
python -m pytest tests/test_benchmark_drivers_cli.py -q
python -m pytest tests/test_benchmark_drivers_models.py -q
python -m pytest tests/test_benchmark_approval_policy.py -q
```

For workflow edits:

```bash
python - <<'PY'
from pathlib import Path
import yaml
for path in Path('.github/workflows').glob('benchmark-*.yml'):
    with path.open(encoding='utf-8') as handle:
        yaml.safe_load(handle)
    print(f'parsed {path}')
PY
git diff --check
ruff check .
```

For real-tool work, run only when authorized and classify outcomes as dependency skip, capability skip, runner bug, solver failure, or valid real execution before drawing conclusions.
