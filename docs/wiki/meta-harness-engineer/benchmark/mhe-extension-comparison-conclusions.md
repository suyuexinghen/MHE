# MHE Extension Comparison Conclusions

> Last updated: 2026-05-03  
> Purpose: central record of claim-boundary-safe comparison conclusions for MHE extension benchmarks.

## How to read this report

This report records comparison conclusions across MHE benchmark suites. It is intentionally conservative: dry-run evidence supports workflow and harness claims, while numerical or scientific superiority requires real tools, real Claude proposals when relevant, repeated runs, retained artifacts, and domain-specific metrics.

## Global conclusion

Current evidence does not prove that MHE extensions are numerically more accurate, faster, or scientifically stronger than direct Claude Code / Claude CLI workflows. Current evidence does show that MHE improves scientific workflow controllability and auditability through structured case specs, lane separation, schema validation, evidence bundles, preflight/failure classification, repair tracking, repeat aggregation, approval gates, and comparison/report automation.

The strongest current external statement is:

> MHE has evidence for better scientific workflow auditability and claim-boundary enforcement; broad numerical/performance superiority over direct Claude remains unproven until clean repeated real-run evidence supports it.

## Cross-suite conclusion table

| Suite / area | Evidence state | Supported conclusion | Explicit non-claims | Next evidence needed |
|---|---|---|---|---|
| Octave native | Dry-run 10-case comparison complete; real-Claude preflight smoke and controlled repair fixtures exist; later extension-only real Octave baseline passed 3 small cases over repeated real runs. | Benchmark framework captures Octave lane evidence, proposal failures, repair taxonomy, and real extension solver execution for a small baseline. | Does not prove MHE/direct/agent numerical superiority; controlled repair fixture does not prove general repair ability. | Broader real tools + real Claude repeated comparison with executable direct/agent proposals. |
| Nektar PDE | Dry-run 6-case comparison complete; extension real-solver Phase B evidence exists for selected cases; Phase C real-Claude/direct/agent runs passed selected ADR cases under bounded prompts. | Nektar workflow can be run through real tools and real Claude lanes for selected cases, with proposal failures separated from solver failures. | Does not prove broad Nektar superiority; skipped solver families remain capability-gated. | Expand retained real repeated runs, validate more solver families, and preserve external run roots. |
| QCompute × ABACUS | Hamiltonian proxy and mapping dry-runs pass; H/S bridge remains sentinel; QEC dry-run repair evidence is comparator-visible. | QCompute benchmark expresses proxy Hamiltonian workflow, explicit unsupported bridge evidence, and QEC proposal-contract repair evidence. | Does not prove quantum advantage, real QPU/QEC execution, ABACUS H/S conversion, or QEC numerical superiority. | Run real Qiskit Aer proxy when authorized; add real Claude QEC challenge prompts; keep QEC real gate blocked until backend/decoder/repeat validation exists. |
| PyCFD PDE | Earlier PyCFD docs recorded real execution evidence for the current catalog; the latest CI/CD real-tool smoke skipped `vortex-2d` because the PyCFD environment was unavailable. | PyCFD has prior real-run evidence, but current CI/CD smoke does not yet provide retained real PyCFD coverage on the benchmark runner. | Does not prove PyCFD is numerically superior to Fealpy, Nektar, Octave, QCompute, or direct Claude Code; current CI smoke must not be reported as PyCFD real execution coverage. | Configure `PYCFD_SRC_PATH` / environment gating, retain a clean real smoke root, expose direct proposal source, and collect repeated pass/repair rates. |
| Fealpy PDE | Earlier comparison docs identified Fealpy as dry-run only; the latest CI/CD real-tool smoke passed `poisson-2d-numpy` once with real backend metrics. | Fealpy now has selected single-case numpy-backend real smoke evidence, plus benchmark plumbing and multi-backend design surface. | Does not validate all numpy/pytorch/jax backend claims, repeated stability, or numerical superiority over PyCFD/Nektar. | Add backend-labeled real smoke and repeats, then compare evidence with PyCFD/Nektar only by domain-specific metrics. |
| Approval and reporting framework | Approval gates and evidence bundles exist for benchmark promotion. | MHE can make manager-facing claim boundaries explicit and auditable. | Approval does not replace scientific validation or prove numerical/runtime superiority. | Attach scientific/domain signoff and retained real-run evidence to stronger claims. |

## Detailed conclusions

### Octave native

The Octave benchmark has a complete dry-run 10-case suite across `extension`, `direct`, and `agent` lanes. It proves case catalog wiring, lane summaries, comparison bundles, evidence capture, proposal failure classification, and controlled repair taxonomy. Later evidence adds a small extension-only real Octave baseline, but because direct and agent real solver comparisons are not broadly complete, the conclusion remains workflow/auditability first rather than superiority.

Current claim boundary:

> Octave evidence supports MHE benchmark plumbing, real extension baseline capability for selected small cases, and repair/failure taxonomy. It does not yet prove MHE beats direct Claude or agent workflows numerically.

### Nektar PDE

The Nektar benchmark started as dry-run/preflight evidence and later accumulated selected real-tool and real-Claude runs. Successful repeated direct/agent runs for selected ADR cases show that bounded prompts, proposal preflight, and real solver execution can produce stable executable workflows. Capability-gated cases such as CompressibleFlowSolver coverage remain intentionally non-promoted.

Current claim boundary:

> Nektar evidence supports selected real executable direct/agent workflows and improved failure classification. It does not yet support broad solver-family superiority or complete extension coverage claims.

### QCompute × ABACUS and QEC

The QCompute benchmark supports H2 FCIDUMP Hamiltonian proxy dry-runs, JW/BK metadata comparison, explicit ABACUS H/S bridge skip evidence, and QEC dry-run proposal-contract repair evidence. The new QEC comparison fields surface `proposal_contract_status`, `repair_outcome`, `repair_count`, and `repair_advantage` in comparison artifacts and reports.

Current claim boundary:

> QCompute/QEC evidence supports structured workflow control, unsupported-capability truthfulness, and agent repair auditability in dry-run QEC proposal tests. It does not support real QEC execution, quantum advantage, hardware error-suppression, or numerical superiority.

### PyCFD PDE

PyCFD has prior timestamped real solver evidence for the current 2D Euler catalog, but the latest CI/CD real-tool smoke did not reproduce that coverage because `vortex-2d` skipped truthfully when the PyCFD environment was unavailable. Treat this as a split evidence state: prior real execution exists, while current CI real-tool coverage remains environment-gated.

Current claim boundary:

> PyCFD evidence supports prior real execution maturity for the current 2D Euler catalog, but current CI/CD smoke only proves truthful environment gating until a retained real PyCFD smoke root exists. It does not prove cross-solver numerical superiority or direct-Claude code-generation success when fallback compiler paths are used.

### Cross-extension PDE comparison

The PDE cross-extension comparison has changed over time: earlier snapshots said PyCFD had real execution evidence while Fealpy and Nektar were dry-run-only; later smoke evidence adds a selected Fealpy real numpy-backend pass, records a PyCFD environment skip in CI, and records a Nektar real-tool failure for `advdiff-2d`. Cross-suite summaries should therefore cite the dated evidence root they use instead of treating one snapshot as current truth.

Current claim boundary:

> Cross-extension comparisons must compare evidence maturity and workflow surfaces separately from numerical/scientific performance. Different PDE residuals, FEM error norms, and solver domains are not interchangeable metrics.

## Terminology explanation

`dry-run` means the benchmark checks workflow structure and output files without real solver or hardware execution. `real tools` means external solvers or simulators such as Octave, Nektar++, Qiskit Aer, CUDA-Q, ABACUS, or PyCFD are actually executed. A `lane` is one comparison route, such as deterministic `extension`, standalone `direct` Claude, or `agent` Claude plus MHE validation. A `proposal contract` is a schema-like requirement for what a Claude proposal must contain. `repair_outcome` records whether a bad proposal was repaired. `repair_advantage` records whether one lane shows more useful repair evidence than another. An `artifact` or `evidence bundle` is a saved file that lets reviewers audit what happened. A `sentinel` is an intentionally skipped case that proves unsupported capability is not being faked. A `claim boundary` states what the evidence supports and what it must not be stretched to claim.

## Maintenance rule

Append a new dated entry here whenever a benchmark comparison conclusion is summarized for the user. Each entry should state: evidence root or source document, real/dry-run state, supported conclusion, explicit non-claims, and next evidence needed.

## Dated conclusion log

### 2026-05-03 — QCompute QEC dry-run repair comparison

Source evidence:

- `.runs/qec-benchmark-smoke-v3/qcompute-abacus-benchmark/comparison/result_bundle.json`
- `.runs/qec-benchmark-smoke-v3/qcompute-abacus-benchmark/comparison/comparison_report.md`
- `docs/wiki/meta-harness-engineer/benchmark/07-qcompute-abacus-experiment-analysis.md`

Conclusion:

- Numerical/QEC quality: unproven, because the run is dry-run with no real QEC backend, syndrome sampling, decoder execution, threshold behavior, or repeated real-run evidence.
- Workflow quality: improved for the MHE agent lane, because QEC proposal contract status, repair outcome, repair count, and repair advantage are now comparator-visible.
- Strongest supported statement: MHE agent is stronger than direct Claude for structured dry-run workflow control and deterministic repair evidence under malformed QEC proposal tests.
- Non-claim: this is not QEC numerical superiority, quantum advantage, runtime superiority, or hardware logical error suppression evidence.
- Next evidence needed: real Claude QEC challenge prompts, repeated repair-rate aggregation, then a real QEC backend adapter only after workflow evidence remains stable.

### 2026-05-03 — Benchmark comparison CI/CD dry-run workflow

Source evidence:

- `.runs/ci-check/octave-native/octave-native-benchmark/comparison/result_bundle.json`
- `.runs/ci-check/nektar-pde/nektar-pde-benchmark/comparison/result_bundle.json`
- `.runs/ci-check/qcompute-abacus/qcompute-abacus-benchmark/comparison/result_bundle.json`
- `.runs/ci-check/fealpy-pde/fealpy-pde-benchmark/comparison/result_bundle.json`
- `.runs/ci-check/pycfd-pde/pycfd-pde-benchmark/comparison/result_bundle.json`
- `.github/workflows/benchmark-pr.yml`
- `.github/workflows/benchmark-nightly-real-tools.yml`
- `.github/workflows/benchmark-weekly-real-claude.yml`
- `.github/workflows/benchmark-release-approval.yml`
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md`

Conclusion:

- Numerical/scientific quality: unproven, because the local CI/CD workflow evidence is dry-run only: `real_tools = false`, `real_claude = false`, and `repeat_count = 1` for all five suite bundles.
- Workflow quality: improved, because the CI/CD design now runs a five-suite dry-run matrix, writes persisted comparison bundles, checks approval policy, validates workflow YAML shape locally, records changed-file format checks, and separates real-tool and real-Claude gates.
- Suite results: Octave native produced 10 `all_passed` rows; PyCFD PDE produced 5 `all_passed` rows; Nektar PDE produced 5 `all_passed` rows and 1 truthful `capability_skip`; QCompute × ABACUS produced 3 `all_passed` rows and 1 truthful `capability_skip`; Fealpy PDE produced 1 `all_passed` row and 7 truthful `capability_skip` rows.
- Approval status: Octave, Nektar, Fealpy, and PyCFD were `approved_with_limitations`; QCompute × ABACUS remained `blocked` by `abacus_hs_scientific`, which is correct because the ABACUS H/S scientific bridge remains unsupported.
- Strongest supported statement: the benchmark framework can now be checked by CI/CD for dry-run workflow reproducibility, suite coverage, comparator/report generation, approval-boundary visibility, and truthful capability skips across the five target suites.
- Non-claim: this CI/CD dry-run evidence does not prove solver accuracy, runtime superiority, real Claude proposal quality, QEC execution, ABACUS conversion readiness, Fealpy backend real execution, or cross-domain numerical superiority.
- Next evidence needed: remote GitHub Actions execution, retained nightly real-tool artifacts, real-Claude challenge runs with proposal/preflight/repair summaries, repeated-run aggregation, and human/scientific signoff for stronger release claims.

### 2026-05-03 — Benchmark comparison CI/CD real-tool smoke

Source evidence:

- `.runs/ci-real-tools-extension-check/octave-native/octave-native-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/nektar-pde/nektar-pde-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/qcompute-abacus/qcompute-abacus-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/fealpy-pde/fealpy-pde-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/pycfd-pde/pycfd-pde-benchmark/comparison/result_bundle.json`
- `docs/wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md`
- `.github/workflows/benchmark-nightly-real-tools.yml`

Conclusion:

- Numerical/scientific quality: partially evidenced only for selected extension-lane smoke cases. The run used `real_tools = true`, `real_claude = false`, and `repeat_count = 1`, so it supports single-run real execution evidence for individual cases, not repeated stability, direct-vs-agent superiority, or cross-solver numerical claims.
- Workflow quality: improved, because the nightly real-tool CI design now runs one smoke case per suite on the `extension` lane only, avoiding fake direct/agent proposal ambiguity while preserving comparison bundles and approval checks.
- Suite results: Octave `ode45-exp-decay` passed with real Octave metrics; QCompute `h2-fcidump-vqe-proxy` passed as a real-tool/proxy execution; Fealpy `poisson-2d-numpy` passed with real backend metrics; PyCFD `vortex-2d` skipped truthfully because the PyCFD environment was unavailable; Nektar `advdiff-2d` failed with `ADRSolver` exit code `-11` and missing L2/Linf metrics.
- Approval status: all five real-tool smoke bundles reported `approved_with_limitations`; this approval status preserves excluded claims and does not replace scientific validation.
- Strongest supported statement: the CI/CD real-tool smoke can now distinguish real extension execution, dependency skip, and solver/driver failure across the target suites while keeping real-Claude comparison separate.
- Non-claim: this is not proof that MHE beats direct Claude Code, not proof of numerical or runtime superiority, not a repeated-run stability result, and not real QEC or ABACUS H/S bridge validation.
- Next evidence needed: diagnose the Nektar `ADRSolver` crash, configure PyCFD real environment gating, run remote GitHub Actions with retained artifacts, add repeated real-tool runs for passing smoke cases, and run separate real-Claude direct/agent comparison prompts.

### 2026-05-03 — Real-tool smoke extension improvement analysis

Source evidence:

- `.runs/ci-real-tools-extension-check/octave-native/octave-native-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/nektar-pde/nektar-pde-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/qcompute-abacus/qcompute-abacus-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/fealpy-pde/fealpy-pde-benchmark/comparison/result_bundle.json`
- `.runs/ci-real-tools-extension-check/pycfd-pde/pycfd-pde-benchmark/comparison/result_bundle.json`

Conclusion:

- Numerical/scientific quality: the current smoke run supports selected extension-baseline evidence only. Octave, QCompute, and Fealpy produced real metrics for one smoke case each; PyCFD produced a truthful environment skip; Nektar produced a solver crash with missing domain metrics.
- Workflow quality: the smoke run shows that extension-only CI should report lane summaries as the truth source, because comparator rows are incomplete without direct and agent lanes.
- Strongest supported statement: the extension suite backlog should now prioritize solver portability, dependency gating, backend labeling, and repeated-run retention before any broader performance or superiority claim.
- Non-claim: this does not prove cross-solver ranking, direct-vs-agent superiority, or stable repeated-run performance.
- Next evidence needed: repeated Octave smoke cases, Nektar crash diagnosis and clean rerun, PyCFD environment probing and a retained baseline root, Fealpy backend-by-backend smoke, and QCompute/QEC backend-adapter evidence before promoting real QEC execution.
