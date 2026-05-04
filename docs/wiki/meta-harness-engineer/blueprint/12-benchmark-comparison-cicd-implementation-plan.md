# Benchmark Comparison CI/CD Implementation Plan

> Status: proposed | Scope: first implementation slice for benchmark CI/CD workflows

## Goal

Create CI/CD workflows that reuse the existing benchmark CLI and approval policy instead of adding a parallel runner. The first implementation should prioritize deterministic dry-run validation, conservative real-tool smoke jobs, explicit real-Claude gates, artifact retention, and release approval checks.

## Commands To Reuse

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite <suite> --lanes extension,direct,agent --runs-root <root>
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite <suite> --runs-root <root>
PYTHONPATH=src python -m metaharness.cli benchmark-approval-check --suite <suite> --config-root .mhe
```

Real-tool jobs add `--allow-real-tools`. Real-Claude jobs add `--allow-real-claude`. Jobs that intentionally repeat a suite should pass `--repeat <n>` and retain the resulting aggregate artifacts.

## PR Dry-Run Workflow

Create `.github/workflows/benchmark-pr.yml`.

Behavior:

- run on pull requests and pushes to `main`;
- install the package with development extras;
- run `ruff check .` and changed-file `ruff format --check` for Python files touched by the PR or push;
- run focused benchmark CLI and approval tests;
- run a matrix across `octave-native`, `nektar-pde`, `qcompute-abacus`, `fealpy-pde`, and `pycfd-pde`;
- execute `benchmark-run`, `benchmark-compare`, and non-strict `benchmark-approval-check` for each suite;
- upload `.runs/ci-pr/<suite>-benchmark/` artifacts.

Supported conclusion: dry-run benchmark plumbing, schema, comparison outputs, and approval checks are wired.

Unsupported conclusion: real solver accuracy, runtime superiority, or real Claude proposal quality.

## Nightly Real-Tool Workflow

Create `.github/workflows/benchmark-nightly-real-tools.yml`.

Behavior:

- run on a nightly schedule and `workflow_dispatch`;
- keep real-tool execution opt-in through `--allow-real-tools`;
- use conservative case selections where supported;
- run the first real-tool smoke on the `extension` lane only, because direct/agent real comparisons need real Claude proposal evidence or explicit fallback provenance;
- allow dependency skips to complete as truthful evidence rather than masking them;
- run comparison and approval checks after each suite;
- write a GitHub job summary from `extension/*/summary.json`, because extension-only comparator rows can be `incomplete` by design;
- upload retained artifacts with a longer retention period than PR artifacts.

Suggested initial case policy:

| Suite | Initial smoke case input |
|---|---|
| `octave-native` | `ode45-exp-decay` |
| `nektar-pde` | `advdiff-2d` |
| `qcompute-abacus` | `h2-fcidump-vqe-proxy`; QEC real gate remains skipped |
| `pycfd-pde` | `vortex-2d` when `PYCFD_SRC_PATH` exists |
| `fealpy-pde` | `poisson-2d-numpy` when dependencies exist |

Supported conclusion: selected real tools either executed or skipped with dependency evidence.

Unsupported conclusion: broad numerical superiority or production readiness.

## Weekly Real-Claude Workflow

Create `.github/workflows/benchmark-weekly-real-claude.yml`.

Behavior:

- run on a controlled weekly schedule and `workflow_dispatch`;
- accept inputs for `suite`, `cases`, `repeat`, and whether real tools are also enabled;
- require a real Claude CLI/API environment through repository secrets or runner setup;
- write an explicit dependency-skip artifact when the Claude CLI is unavailable instead of silently failing or claiming proposal evidence;
- pass `--allow-real-claude` and optionally `--allow-real-tools` when the Claude CLI is available;
- keep direct and agent proposal outputs under separate lane directories;
- retain `claude_command.json`, `claude_result.json`, proposal files, summaries, and comparison bundles;
- upload artifacts for proposal/preflight/repair review.

Supported conclusion: selected real-Claude prompts produced auditable proposal, preflight, failure, and repair evidence.

Unsupported conclusion: general Claude capability, solver superiority, or scientific validation.

## Release Approval Workflow

Create `.github/workflows/benchmark-release-approval.yml`.

Behavior:

- run on release events and `workflow_dispatch`;
- validate the approval policy under `.mhe/benchmarks/comparison-approval.json`;
- run strict `benchmark-approval-check` for each suite;
- optionally inspect retained comparison bundles when provided by the release process;
- fail if required approval policy is malformed or intentionally blocked under strict mode;
- publish a short job summary that says CI validation is necessary but not sufficient.

Supported conclusion: approval gate policy is enforced and claim boundaries are visible.

Unsupported conclusion: CI has granted scientific, admin, or production promotion approval.

## Documentation Updates

Update `docs/wiki/meta-harness-engineer/benchmark/README.md` to link:

- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-blueprint.md`;
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md`;
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-roadmap.md`.

## Verification

Run focused checks after implementation:

```bash
python -m pytest tests/test_benchmark_drivers_cli.py -q
python -m pytest tests/test_benchmark_approval_policy.py -q
python -m pytest tests/test_metaharness_pycfd_benchmark_ci.py -q
ruff check .
# Full repository format currently exposes unrelated baseline drift; PR CI checks changed Python files.
ruff format --check <changed-python-files>
PYTHONPATH=src python -m metaharness.cli benchmark-run --suite pycfd-pde --lanes extension,direct,agent --runs-root .runs/ci-smoke
PYTHONPATH=src python -m metaharness.cli benchmark-compare --suite pycfd-pde --runs-root .runs/ci-smoke
PYTHONPATH=src python -m metaharness.cli benchmark-approval-check --suite pycfd-pde --config-root .mhe
```

If no local GitHub Actions YAML validator is available, treat remote CI as the final workflow syntax validation and keep YAML simple.

## Local Validation Result

2026-05-03 local CI-equivalent checks produced these design updates:

- Full-repository `ruff format --check .` is currently blocked by unrelated baseline formatting drift, so the benchmark PR workflow checks formatting only for changed Python files while keeping full `ruff check .`.
- The dry-run matrix completed for `octave-native`, `nektar-pde`, `qcompute-abacus`, `fealpy-pde`, and `pycfd-pde`, and wrote comparison bundles under `.runs/ci-check/<suite>/`.
- Strict `benchmark-approval-check` passed for all five suites from the current `.mhe` approval manifests.
- `actionlint` was not available locally; workflow YAML was parsed with Python YAML loading and should still be validated by GitHub Actions on first remote run.
- The real-Claude workflow now records an explicit `unavailable_dependency` skip artifact when `claude` is missing from the runner.

2026-05-03 real-tool CI-equivalent smoke then refined the nightly workflow:

- The first attempt used `extension,direct,agent` with `--allow-real-tools`, which exposed that real-tool smoke without real Claude can mix solver evidence with fake direct/agent proposal paths. The nightly real-tool workflow now runs `--lanes extension` only; direct/agent real comparisons belong in the real-Claude workflow.
- The nightly real-tool workflow now uses one initial smoke case per suite: `ode45-exp-decay`, `advdiff-2d`, `h2-fcidump-vqe-proxy`, `poisson-2d-numpy`, and `vortex-2d`.
- Extension-only real-tool smoke produced retained bundles under `.runs/ci-real-tools-extension-check/<suite>/` for all five suites.
- Observed real-tool outcomes: Octave `ode45-exp-decay`, QCompute `h2-fcidump-vqe-proxy`, and Fealpy `poisson-2d-numpy` passed; PyCFD `vortex-2d` skipped because `PYCFD_SRC_PATH` / environment was unavailable; Nektar `advdiff-2d` failed with `ADRSolver` exit code `-11` and missing L2/Linf metrics.
- Comparator rows are `incomplete` for extension-only smoke because direct and agent lanes are intentionally absent; interpret the lane `summary.json` status as the real-tool smoke truth and reserve three-lane verdicts for PR dry-run or real-Claude comparison jobs.
- The nightly workflow now appends a GitHub step summary from extension-lane `summary.json` files so reviewers can see passed, skipped, and failed smoke outcomes without mistaking `incomplete` comparison rows for suite failure.