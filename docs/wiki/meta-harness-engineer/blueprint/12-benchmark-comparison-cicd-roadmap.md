# Benchmark Comparison CI/CD Roadmap

> Status: proposed | Scope: staged rollout for MHE benchmark comparison CI/CD

## Current Baseline

The benchmark system already exposes reusable CLI commands for running suites, comparing persisted lane outputs, and checking approval policy. Current evidence supports workflow auditability for dry-run comparisons and selected real-tool evidence for some suites, but it does not prove broad numerical or performance superiority over direct Claude Code.

## Target State

MHE benchmark CI/CD should provide a repeatable evidence ladder:

- fast PR checks prevent schema/report regressions;
- nightly smoke jobs collect real-tool availability and execution evidence;
- weekly/manual jobs collect real-Claude proposal and repair evidence;
- release gates validate approval policy and preserve claim boundaries;
- repeated-run artifacts become available before timing or stability claims are made.

## Phase Map

| Phase | Status | Deliverable | Evidence unlocked |
|---|---|---|---|
| Dry-run CI | first implementation | PR workflow over all five suites | workflow/schema/report regression safety |
| Real-tool smoke | first implementation | nightly/manual `--allow-real-tools` workflow | selected real execution or dependency-skip evidence |
| Real-Claude comparison | first implementation | weekly/manual `--allow-real-claude` workflow | proposal/preflight/repair evidence for selected prompts |
| Release approval | first implementation | release/manual strict approval check | promotion policy compliance evidence |
| Repeated-run aggregation | next iteration | retained `repeat_summary.json` review path | stability, flaky, and pass-rate evidence |
| Scientific signoff | later iteration | human/domain review package | stronger scientific claim readiness |

## Suite Progression

| Suite | First CI target | Next evidence-producing step | Claim boundary after success |
|---|---|---|---|
| Octave native | dry-run PR matrix | nightly `ode45-exp-decay` real Octave smoke with retained artifacts | selected Octave real execution, not superiority |
| Nektar PDE | dry-run PR matrix | `advdiff-2d` real-tool smoke after solver mapping/preflight | selected Nektar execution, not solver-family coverage |
| QCompute/QEC | dry-run PR matrix with proxy/QEC sentinel | `h2-fcidump-vqe-proxy` real-tool smoke before QEC backend work | proxy execution evidence, not real QEC execution |
| PyCFD PDE | dry-run PR matrix plus focused CI tests | `vortex-2d` short real-solver baseline with `PYCFD_SRC_PATH` | real execution maturity for selected cases |
| Fealpy PDE | dry-run PR matrix | `poisson-2d-numpy` backend smoke after dependency gates | backend availability evidence, not backend superiority |

## Promotion Gates

A benchmark suite should not move from one tier to the next unless the previous tier leaves auditable artifacts:

- dry-run to real tools: method doc and dry-run comparison bundle exist;
- real tools to repeated runs: single final real root exists and runner bugs are fixed in a clean rerun;
- repeated runs to manager-facing claims: repeat summary, approval status, excluded claims, and domain metrics are retained;
- manager-facing promotion: admin/scientific signoff is attached outside CI.

## Backlog

| ID | Area | Symptom | Evidence | Suggested fix | Priority |
|---|---|---|---|---|---|
| CI-dry-run | Real execution coverage | No checked-in workflow runs dry-run comparison across all suites | missing `.github/workflows/*.yml` | Add PR dry-run matrix using existing benchmark CLI | High |
| CI-real-tools | Real execution coverage | Real solver evidence is not collected on a schedule | no nightly workflow artifact root | Add dependency-gated `--allow-real-tools` workflow | High |
| CI-real-claude | LLM participation | Real Claude proposal quality is not measured in CI/CD | no workflow-dispatch real-Claude job | Add controlled `--allow-real-claude` workflow with artifacts | High |
| CI-approval | Boundary gaps | Approval policy exists but is not CI-gated for releases | `.mhe/benchmarks/comparison-approval.json` is manual-only | Add strict release approval workflow | High |
| CI-repeat | Statistics gaps | Timing/stability claims lack repeated-run CI artifacts | no retained `repeat_summary.json` path | Add repeated-run aggregation review after first workflows stabilize | Medium |
| CI-nektar-real | Driver portability bugs | Nektar `advdiff-2d` real-tool smoke exits `-11` and emits no L2/Linf metrics | `.runs/ci-real-tools-extension-check/nektar-pde/.../validation.json` | Diagnose ADRSolver/session compatibility, then rerun in a clean final root | High |
| CI-pycfd-env | Real execution coverage | PyCFD real-tool smoke skips because the environment is unavailable | `.runs/ci-real-tools-extension-check/pycfd-pde/.../summary.json` | Configure `PYCFD_SRC_PATH` or dependency gate before claiming PyCFD real CI coverage | High |
| CI-domain-signoff | Governance gaps | CI cannot provide scientific signoff | `.mhe/config.json` says CI validates schema, not scientific truth | Add release package checklist for human/domain review | Medium |

## Extension Improvement Backlog

| Suite | Real-tool smoke finding | Extension improvement | Evidence needed before stronger claims | Priority |
|---|---|---|---|---|
| Octave native | `ode45-exp-decay` passed with endpoint and max-error metrics | Add repeated smoke cases that cover stiffness, event handling, and plotting/output evidence without changing direct/agent claims | retained repeat summaries over multiple real Octave cases | Medium |
| Nektar PDE | `advdiff-2d` failed with `ADRSolver` exit `-11` and missing L2/Linf metrics | Diagnose session/driver portability, capture solver stderr classification, and add a preflight that distinguishes incompatible sessions from solver crashes | clean rerun where either ADR metrics pass or a dependency/compatibility skip is auditable | High |
| QCompute/QEC | `h2-fcidump-vqe-proxy` passed as proxy execution; QEC remains dry-run gated | Keep ABACUS H/S and QEC real gates blocked while improving proposal-contract, decoder-readiness, and backend-adapter sentinel evidence | real Qiskit Aer proxy repeats, then QEC backend adapter tests with decoder and repeated syndrome sampling | Medium |
| Fealpy PDE | `poisson-2d-numpy` passed with FEM error metrics | Promote backend-specific smoke cases one at a time and require backend labels in summaries before comparing numpy, pytorch, or jax maturity | retained real backend smoke for each enabled backend with L2/H1 metrics | Medium |
| PyCFD PDE | `vortex-2d` skipped because `PYCFD_SRC_PATH` / environment was unavailable | Add explicit environment probe docs and CI skip artifact fields, then run the short real-solver baseline where PyCFD is installed | retained real PyCFD smoke root with residual, timing, and mesh metrics | High |

## Exit Criteria

The first CI/CD implementation is complete when:

- the benchmark README links the CI/CD blueprint, plan, and roadmap;
- four workflow files exist for PR dry-run, nightly real tools, weekly real Claude, and release approval;
- workflows call the existing CLI rather than duplicating benchmark logic;
- workflow artifacts retain comparison bundles and manifests;
- documentation states numerical, workflow, approval, and domain-metric boundaries explicitly;
- focused benchmark CLI and approval tests pass locally.