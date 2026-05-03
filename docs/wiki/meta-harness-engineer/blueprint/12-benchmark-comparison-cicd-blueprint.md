# Benchmark Comparison CI/CD Blueprint

> Status: proposed | Scope: CI/CD orchestration for MHE benchmark comparison suites

## Purpose

This blueprint defines a claim-boundary-safe CI/CD structure for benchmark comparison across Octave native, Nektar PDE, QCompute/QEC, PyCFD PDE, and Fealpy PDE suites. The pipeline should make benchmark evidence easier to reproduce and audit without turning dry-run or CI schema checks into solver superiority claims.

## Design Principles

- Separate workflow evidence from numerical solving evidence.
- Keep `--allow-real-tools` and `--allow-real-claude` as independent gates.
- Treat missing external solvers or Claude CLI availability as dependency skips in scheduled/manual jobs, not hidden passes.
- Preserve lane boundaries for `extension`, `direct`, and `agent` outputs.
- Surface proposal provenance, preflight status, failure category, repair outcome, and repair advantage in comparison artifacts.
- Upload CI artifacts instead of committing generated `.runs/` outputs.
- Require admin/scientific approval outside CI before manager-facing promotion claims.

## Pipeline Tiers

| Tier | Trigger | Evidence class | Default suites | Supported claim | Non-claim |
|---|---|---|---|---|---|
| PR dry-run | pull request, push | dry-run workflow/schema evidence | all five suites | benchmark commands, schemas, reports, approval checks stay wired | no real solver or real Claude superiority |
| Nightly real tools | schedule, manual | gated extension-lane real solver/tool evidence | conservative smoke cases | selected extension baselines can execute or skip truthfully | no direct/agent proposal quality or broad numerical/performance superiority |
| Weekly real Claude | schedule, manual | real proposal/preflight/repair evidence | selected challenge cases | bounded prompts produce auditable proposal outcomes | no general LLM intelligence claim |
| Release approval | release, manual | policy and artifact completeness evidence | retained comparison outputs | promotion gates and excluded claims are visible | CI does not replace admin or scientific signoff |

## Suite Matrix

| Suite | PR dry-run role | Real-tool smoke role | Real-Claude role | Main boundary |
|---|---|---|---|---|
| `octave-native` | validate Octave benchmark plumbing and reports | run small Octave-native cases when `octave-cli` exists | compare proposal success and repair evidence | analytic error claims require real repeated runs |
| `nektar-pde` | validate PDE lane summaries and capability skips | run selected solver/preflight cases when Nektar tools exist | compare bounded ADR-style prompts | Nektar solver-family coverage remains capability-gated |
| `qcompute-abacus` | validate Hamiltonian proxy, QEC dry-run, and bridge sentinel evidence | run proxy cases only when simulator dependencies exist | challenge QEC proposal contract and repair behavior | QEC real execution stays blocked until backend/decoder/repeat validation exists |
| `pycfd-pde` | validate CI-friendly dry-run catalog and comparison output | run short PyCFD real-solver smoke when `PYCFD_SRC_PATH` exists | compare direct/agent proposal source and repair rates | residuals do not imply cross-solver superiority |
| `fealpy-pde` | validate dry-run benchmark surface and backend labeling | run backend smoke only after dependencies are available | compare proposal/preflight evidence | backend claims need real execution per backend |

## Artifact Layout

CI jobs should write runtime outputs under `.runs/<ci-run-id>/` and upload the relevant benchmark roots as workflow artifacts. The comparator remains responsible for writing:

```text
.runs/<ci-run-id>/<suite>-benchmark/comparison/summary_table.csv
.runs/<ci-run-id>/<suite>-benchmark/comparison/comparison_report.md
.runs/<ci-run-id>/<suite>-benchmark/comparison/result_bundle.json
.runs/<ci-run-id>/<suite>-benchmark/comparison/run_manifest.json
```

Release jobs should consume retained artifacts or checked approval manifests, not regenerate stronger claims from chat summaries.

## Truth Hierarchy

Use benchmark artifacts in this order when summarizing CI results:

- clean repeated final real-run roots;
- clean single final real-run roots;
- dry-run roots for workflow/schema/evidence claims;
- pilot roots for driver bugs and backlog only;
- docs and chat summaries as supporting context only.

## Approval Boundary

The CI/CD pipeline may verify that approval policy files are present, parseable, and applied. It must not state that CI approval replaces:

- benchmark promotion admin approval;
- scientific validation;
- production converter readiness;
- real repeated evidence;
- human review of manager-facing claims.

## Security And Operational Boundary

Real-Claude jobs should run only through `workflow_dispatch` or controlled schedules with explicit secrets and permissions. If the Claude CLI is unavailable, the job should write dependency-skip evidence and avoid proposal-quality claims. Real-tool jobs should avoid destructive operations, external uploads beyond workflow artifacts, or hidden dependency installation. PR jobs should default to dry-run commands and mocked/fake Claude providers.