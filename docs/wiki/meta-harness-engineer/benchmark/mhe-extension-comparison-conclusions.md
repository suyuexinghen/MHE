# MHE Extension Comparison Conclusions

> Last updated: 2026-05-05
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
| BOUT++ | Usage comparison with dry-run and real-Claude lanes passes; local opt-in repeated real smoke passes `conduction-real` 2/2 and records candidate skips; comparator-visible promotion rows and optional domain metadata validation now exist. | BOUT++ evidence now covers workflow comparison, Claude proposal preflight, local executable integration, artifact/domain metadata discovery, row-local real-smoke flags, and truthful capability gating for additional examples. | Does not prove BOUT++ numerical accuracy, convergence, runtime superiority, broad physics model coverage, or MHE superiority over direct Claude. | Retain clean real-tools + real-Claude comparison roots, add case-specific `T` NetCDF shape requirements, expand stable compiled examples, and collect repeated direct/agent real-tool proposal/failure rates. |
| MOOSE | Usage comparison dry-run and opt-in local extension real smoke now exist for the INL MOOSE test app. | MOOSE evidence covers structured HIT input specs, extension plan/evidence bundles, malformed proposal repair visibility, and selected local `moose_test-opt` execution. | Does not prove MOOSE numerical accuracy, convergence, runtime superiority, broad MOOSE app coverage, or direct/agent real-tool superiority. | Add repeated real smoke, safe direct/agent real MOOSE CLI lanes, solver-log/domain metrics, and broader input families after source-truth anchoring. |
| PyCFD PDE | Earlier PyCFD docs recorded real execution evidence for the current catalog; the latest CI/CD real-tool smoke skipped `vortex-2d` because the PyCFD environment was unavailable. | PyCFD has prior real-run evidence, but current CI/CD smoke does not yet provide retained real PyCFD coverage on the benchmark runner. | Does not prove PyCFD is numerically superior to Fealpy, Nektar, Octave, QCompute, or direct Claude Code; current CI smoke must not be reported as PyCFD real execution coverage. | Configure `PYCFD_SRC_PATH` / environment gating, retain a clean real smoke root, expose direct proposal source, and collect repeated pass/repair rates. |
| Fealpy PDE | Earlier comparison docs identified Fealpy as dry-run only; the latest CI/CD real-tool smoke passed `poisson-2d-numpy` once with real backend metrics. | Fealpy now has selected single-case numpy-backend real smoke evidence, plus benchmark plumbing and multi-backend design surface. | Does not validate all numpy/pytorch/jax backend claims, repeated stability, or numerical superiority over PyCFD/Nektar. | Add backend-labeled real smoke and repeats, then compare evidence with PyCFD/Nektar only by domain-specific metrics. |
| Lean proof | Dry-run challenge suite now covers `simple-true-proof`, `implication-chain-proof`, and `malformed-proposal-repair`; real Lean extension smoke passes the two positive cases; real-Claude comparison passes the original simple case. | Lean extension has runnable proof-workflow evidence, positive nontrivial proof coverage, and controlled agent repair evidence for malformed proposals. | Does not prove theorem-discovery ability, broad formalization quality, proof search superiority, repeated real-Claude stability, or runtime superiority. | Add repeated real-Claude challenge runs, project-scale Lean fixtures, and comparator-visible approval config plumbing. |
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

### BOUT++

The BOUT++ benchmark now has three separated evidence surfaces: `boutpp-usage` comparison evidence for extension/direct/agent workflow, gated real-Claude proposal preflight evidence, and local opt-in repeated real smoke where `conduction-real` passed 2/2 using the local BOUT++ build. Repeated smoke summaries can now be surfaced as comparator-visible promotion rows, and optional NetCDF/domain metadata validation exists without becoming a default requirement. Additional example candidates remain reviewer-visible skips rather than promoted coverage.

Current claim boundary:

> BOUT++ evidence supports structured workflow comparison, local executable integration for one repeated smoke case, artifact/domain metadata discovery, truthful capability gating, and real-Claude proposal-contract measurement. It does not support numerical accuracy, convergence, runtime superiority, broad BOUT++ solver-family coverage, or MHE superiority over direct Claude.

### MOOSE

The MOOSE benchmark now has a `moose-usage` suite for the INL MOOSE test application. The dry-run comparison captures structured HIT input specs, extension plan/evidence bundles, direct proposal-contract failure, and agent repair evidence. A separate opt-in real extension smoke can execute the local `/home/linden/code/work/Solvers/FEM/moose/test/moose_test-opt` binary for the selected simple diffusion case when the dependency environment is configured.

Current claim boundary:

> MOOSE evidence supports structured workflow comparison, deterministic proposal repair visibility, and selected local test-app execution through the extension lane. It does not support MOOSE numerical accuracy, convergence, runtime superiority, broad app coverage, or direct/agent real-tool superiority claims.

### PyCFD PDE

PyCFD has prior timestamped real solver evidence for the current 2D Euler catalog, but the latest CI/CD real-tool smoke did not reproduce that coverage because `vortex-2d` skipped truthfully when the PyCFD environment was unavailable. Treat this as a split evidence state: prior real execution exists, while current CI real-tool coverage remains environment-gated.

Current claim boundary:

> PyCFD evidence supports prior real execution maturity for the current 2D Euler catalog, but current CI/CD smoke only proves truthful environment gating until a retained real PyCFD smoke root exists. It does not prove cross-solver numerical superiority or direct-Claude code-generation success when fallback compiler paths are used.

### Cross-extension PDE comparison

The PDE cross-extension comparison has changed over time: earlier snapshots said PyCFD had real execution evidence while Fealpy and Nektar were dry-run-only; later smoke evidence adds a selected Fealpy real numpy-backend pass, records a PyCFD environment skip in CI, and records a Nektar real-tool failure for `advdiff-2d`. Cross-suite summaries should therefore cite the dated evidence root they use instead of treating one snapshot as current truth.

Current claim boundary:

> Cross-extension comparisons must compare evidence maturity and workflow surfaces separately from numerical/scientific performance. Different PDE residuals, FEM error norms, and solver domains are not interchangeable metrics.

### Lean proof

The Lean proof benchmark now has a `lean-proof` suite with a simple theorem, a small implication-chain proof, and a controlled malformed proposal repair case. The dry-run challenge comparison passes the two positive rows and exposes `agent_repaired_success` for the malformed proposal case. Real Lean extension smoke also passes the two positive cases with local Lean/Lake, while the earlier real-Claude comparison passes the original simple case.

Current claim boundary:

> Lean proof evidence supports structured proof workflow orchestration, proposal-contract validation, controlled repair visibility, real Lean smoke execution for small positive cases, and comparison artifact generation. It does not prove broad theorem discovery, formalization quality, repeated real-Claude stability, proof search superiority, or runtime superiority over direct Claude.

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

Terminology explanation：这里的 `dry-run` 指只检查 QEC workflow、schema 和 artifact，不运行真实量子纠错 backend；`proposal contract` 是 Claude proposal 必须满足的字段约束；`repair outcome/count/advantage` 记录 agent 是否把不合格 proposal 修复成可审计 workflow evidence；`claim boundary` 表示这些证据只能支持 workflow controllability，不能外推为量子优势或真实 QEC 数值结论。

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

Terminology explanation：这里的 CI/CD `dry-run` 是指 GitHub Actions 或本地 CI 只验证 benchmark workflow 和 comparison artifact，不调用真实 solver 或真实 Claude；`capability_skip` 是有意保留的能力缺口标记，说明某些 case 没有被伪装成已支持；`approval status` 是发布/宣传边界检查，不等于科学审查；`real-Claude challenge run` 才会检查真实 Claude proposal 的质量。

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

Terminology explanation：`real tools` 表示 Octave、Nektar++、Qiskit Aer、Fealpy backend 等真实外部工具被实际执行；`extension lane` 是只跑 MHE extension 的确定性路径，不包含 direct/agent Claude proposal 对比；`repeat_count = 1` 表示只有单次运行，不能说明稳定性；`solver/driver failure` 是真实工具或 runner 失败，必须和 proposal failure 分开解释。

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

Terminology explanation：`smoke run` 是小规模冒烟验证，用来确认 runner、依赖和 artifact 管线能工作；`extension-baseline evidence` 只说明 MHE extension 自身可执行，不说明 direct/agent 对比优势；`dependency gating` 是通过环境变量、路径和 preflight 把缺失依赖变成可审计 skip；`retained baseline root` 是保留 `.runs/...` 结果目录供复查。

### 2026-05-04 — BOUT++ usage comparison with Claude lanes

Source evidence:

- `.runs/boutpp-claude-comparison/boutpp-usage-benchmark/comparison/result_bundle.json`
- `.runs/boutpp-claude-comparison/boutpp-usage-benchmark/comparison/comparison_report.md`
- `.runs/boutpp-real-claude-comparison/boutpp-usage-benchmark/comparison/result_bundle.json`
- `.runs/boutpp-real-claude-comparison/boutpp-usage-benchmark/comparison/comparison_report.md`
- `src/metaharness_ext/boutpp/benchmark_runner.py`
- `src/metaharness/cli.py`

Conclusion:

- 数值/科学求解质量：仍未证明。当前 BOUT++ comparison 主要验证 usage workflow、proposal/preflight、run plan、`BOUT.inp` 和 comparator evidence；即使 real-Claude lanes 通过，也不等同于真实 BOUT++ 数值正确性、收敛性、性能优势或广泛 solver 支持。
- Workflow quality：已形成可审计基线。`extension`、`direct`、`agent` 三个 lane 都能通过 `boutpp-usage` benchmark CLI 运行并进入 comparator；dry-run comparison 与 real-Claude comparison 均得到 `all_passed` verdict。
- Claude lane evidence：direct 与 agent lanes 都产生 Claude proposal、`proposal_preflight.json`、attempt log、lane summary 和 comparison bundle。real-Claude run 中 direct/agent 的 `proposal_contract_status = valid` 且 `preflight_status = passed`，说明 Claude lane 能生成符合当前 BOUT++ usage contract 的 proposal。
- Strongest supported statement：BOUT++ extension benchmark 现在支持结构化 workflow 对比、typed spec / run plan / `BOUT.inp` evidence、Claude proposal preflight、CLI routing、comparison bundle 和 claim-boundary-safe report automation。
- Non-claim：这不是 BOUT++ 数值准确性证明，不是 MHE 相比 direct Claude 的 solver 性能优势证明，不是 repeated real-run stability 证明，也不是广泛 BOUT++ physics model / solver family coverage 证明。
- Next evidence needed：在当前 usage comparison 基线稳定后，下一步应推进 opt-in real BOUT++ repeated smoke，保留 clean run roots，增加 domain-specific artifact/NetCDF validation，并在更多 BOUT++ example cases 上收集 repeated pass-rate、proposal validity rate 和 failure classification evidence。

Terminology explanation：`lane` 是比较路径，`extension/direct/agent` 分别代表 MHE 确定性流程、直接 Claude 流程、Claude proposal 加 MHE 验证流程；`proposal_preflight` 是执行前检查 proposal 是否满足基本约束；`comparison bundle` 是 comparator 输出的一组可审计结果文件；`claim-boundary-safe` 表示结论只说证据支持的 workflow 能力，不夸大成数值优势。

### 2026-05-04 — BOUT++ opt-in repeated real smoke

Source evidence:

- `.runs/boutpp-real-repeated-smoke-v2/boutpp_real_repeated_smoke_summary.json`
- `.runs/boutpp-real-repeated-smoke-v2/conduction-real/conduction-real-repeat-01/boutpp_run_artifact.json`
- `.runs/boutpp-real-repeated-smoke-v2/conduction-real/conduction-real-repeat-02/boutpp_run_artifact.json`
- `docs/wiki/meta-harness-engineer/benchmark/11-boutpp-real-smoke-method.md`
- `src/metaharness_ext/boutpp/real_smoke.py`

Conclusion:

- 数值/科学求解质量：仍然只得到 case-scoped artifact-level evidence。`conduction-real` 在本地 BOUT++ build 上 repeated real-tools smoke 通过 2/2，说明该 tutorial executable 能被 MHE pipeline 稳定驱动并产生日志、settings、dump 与 restart artifacts；但没有 NetCDF 变量解析、解析解误差、收敛阶、性能比较或广泛 physics model coverage。
- Workflow quality：增强。新 harness 会先写 `preflight.json`，再为每次 repeat 保留 problem spec、run plan、run artifact、postprocess report、validation report 和 suite summary；更多 example cases 以 `default_enabled = false` 的 capability-gated skip 暴露，而不是伪装成已支持。
- Strongest supported statement：BOUT++ extension 现在有 opt-in real-tools repeated smoke evidence，证明本地 `examples/conduction` 可通过 MHE typed spec、MPI launcher、workspace isolation、artifact discovery 和 validation pipeline 重复运行成功。
- Non-claim：这不是 BOUT++ 数值准确性、收敛性、运行时优势、广泛 solver-family 支持、direct/agent real-tool superiority 或 real-Claude solver-quality 证明。
- Next evidence needed：增加 NetCDF/domain metrics validation，给 real-smoke promotion 加 comparator-visible row，选择更多具有稳定 executable 和 input contract 的 BOUT++ examples，并在 real-tools + real-Claude direct/agent lanes 中收集 proposal validity、failure classification 和 repeated pass-rate evidence。

Terminology explanation：`opt-in real-tools repeated smoke` 指需要显式打开真实 BOUT++ 依赖并重复运行的冒烟测试；`artifact-level evidence` 是日志、dump、restart、settings 等文件层面的证据；`comparator-visible row` 表示结果进入 comparison 表格而不是只存在单独 smoke summary；`domain metrics` 是 NetCDF 变量、误差、收敛或物理量等领域指标。

### 2026-05-04 — MOOSE usage comparison and local real extension smoke

Source evidence:

- `.runs/moose-usage-validation/moose-usage-benchmark/comparison/result_bundle.json`
- `.runs/moose-usage-validation/moose-usage-benchmark/comparison/comparison_report.md`
- `.runs/moose-real-tool-benchmark/moose-usage-benchmark/extension/simple-diffusion-hit/moose_run_artifact.json`
- `docs/wiki/meta-harness-engineer/benchmark/13-moose-usage-validation-method.md`
- `src/metaharness/benchmark_drivers/moose_runner.py`

Conclusion:

- 数值/科学求解质量：仍未证明。当前 MOOSE evidence 只覆盖 selected INL MOOSE test-app workflow、HIT input handling、Exodus artifact discovery 和 validation/policy outcome；没有残差解析、收敛验证、性能比较、重复稳定性或广泛 app coverage。
- Workflow quality：增强。`moose-usage` suite 能通过 benchmark CLI 产生 extension/direct/agent lane summaries、proposal contract artifacts、comparison bundle 和 repair evidence；`malformed-hit-proposal` 让 direct failure 与 agent deterministic repair 在 comparator 中可见。
- Real-tool evidence：本地 opt-in extension lane 可使用 `/home/linden/code/work/Solvers/FEM/moose/test/moose_test-opt` 跑通 `simple-diffusion-hit`，但 direct/agent real MOOSE CLI lanes 仍被明确跳过。
- Strongest supported statement：MOOSE extension benchmark 现在支持结构化 workflow 对比、proposal repair visibility、extension evidence bundles，以及 selected local real test-app execution。
- Non-claim：这不是 MOOSE 数值准确性、收敛性、运行时优势、广泛 MOOSE app 支持、MHE 相比 direct Claude 的 solver superiority 或 direct/agent real-tool superiority 证明。
- Next evidence needed：增加 repeated real extension smoke，安全实现 direct/agent real MOOSE CLI lanes，解析 solver log/domain metrics，并在更多 source-truth anchored MOOSE inputs 上收集 pass-rate、proposal validity 和 failure classification evidence。

Terminology explanation：`HIT input` 是 MOOSE 的输入文件格式；`proposal contract artifacts` 是保存 Claude proposal 是否合规的证据文件；`agent deterministic repair` 指 agent lane 用确定性规则修复 malformed proposal，并把修复过程作为 workflow evidence；`source-truth anchored` 表示 case 必须绑定到可信的源文件或官方示例，避免凭空生成 benchmark。

### 2026-05-05 — BOUT++ and MOOSE CI/CD benchmark integration

Source evidence:

- `.github/workflows/benchmark-pr.yml`
- `.github/workflows/benchmark-nightly-real-tools.yml`
- `.github/workflows/benchmark-weekly-real-claude.yml`
- `.github/workflows/benchmark-release-approval.yml`
- `.runs/ci-local/boutpp-usage/boutpp-usage-benchmark/comparison/result_bundle.json`
- `.runs/ci-local/moose-usage/moose-usage-benchmark/comparison/result_bundle.json`
- `.runs/ci-local-real-tools/boutpp-usage/boutpp-usage-benchmark/comparison/result_bundle.json`
- `.runs/ci-local-real-tools/moose-usage/moose-usage-benchmark/comparison/result_bundle.json`

Conclusion:

- 数值/科学求解质量：仍未证明。CI/CD integration validates benchmark reproducibility, artifact generation, approval gates, and extension-lane smoke routing; it does not prove BOUT++ or MOOSE numerical accuracy, convergence, runtime superiority, broad physics/app coverage, or MHE superiority over direct Claude Code.
- Workflow quality：明显增强。`benchmark-pr` now runs focused BOUT++/MOOSE tests and includes `boutpp-usage` / `moose-usage` in the dry-run comparison matrix; nightly real-tools and weekly real-Claude workflows can select both suites; release approval checks include both suites.
- BOUT++ result：local CI dry-run comparison produced one `all_passed` row for `conduction-basic` across extension/direct/agent lanes with approval status `approved_with_limitations`. That first CI-local artifact exposed the proposal-contract gap that the later `boutpp-contract-evidence` slice addresses; the benchmark CI path should still not be treated as the richer standalone repeated real-smoke evidence.
- MOOSE result：local CI dry-run comparison produced `all_passed` for `simple-diffusion-hit` and `agent_pipeline_advantage` for `malformed-hit-proposal`; comparator-visible fields show direct fallback for the valid case and agent repair after direct proposal-contract failure for the malformed case.
- Real-tools CI path：extension-only local checks ran for both suites and produced comparison rows with `verdict = incomplete`, which is expected because direct and agent lanes are intentionally absent. For MOOSE this supports selected extension real-tool routing when dependencies are available; for BOUT++ this should remain workflow smoke unless tied to the separate repeated real-smoke runner artifacts.
- Strongest supported statement：CI/CD now makes BOUT++ and MOOSE benchmark regressions visible through focused tests, dry-run comparison bundles, approval checks, and opt-in extension-lane smoke routing, improving extension maintainability and claim-boundary enforcement.
- Improvement priority for BOUT++：after the `boutpp-contract-evidence` slice, promote repeated real-smoke evidence into comparator-visible CI artifacts, add NetCDF/domain metrics validation, and collect direct/agent real-tool proposal validity and failure classification.
- Improvement priority for MOOSE：keep strengthening proposal-contract repair evidence, add repeated real extension smoke, implement safe workspace-isolated direct/agent real MOOSE CLI lanes, and parse solver/domain metrics before any stronger scientific claim.
- Non-claim：this CI/CD integration is not scientific validation, not numerical superiority evidence, not repeated stability evidence for the CI matrix, and not proof that real Claude proposals solve BOUT++ or MOOSE tasks better than deterministic extension workflows.
- Next evidence needed：remote GitHub Actions artifacts for both suites, retained repeated real-tool roots, stricter BOUT++ proposal contracts, MOOSE direct/agent real-lane gates, domain-metric extraction, and independent scientific review before stronger release claims.

Terminology explanation：`CI/CD integration` 是把 benchmark 检查放进 pull request、nightly、weekly 或 release workflow；`approval gate` 是发布前的证据和排除声明检查；`real-lane gate` 是防止未授权真实 solver/Claude 执行的开关；`verdict = incomplete` 在 extension-only smoke 中是预期结果，因为 direct 和 agent lanes 没有运行。

### 2026-05-05 — BOUT++ dry-run proposal contract evidence

Source evidence:

- `.runs/boutpp-contract-evidence/boutpp-usage-benchmark/comparison/result_bundle.json`
- `.runs/boutpp-contract-evidence/boutpp-usage-benchmark/comparison/summary_table.csv`
- `.runs/boutpp-contract-evidence/boutpp-usage-benchmark/comparison/comparison_report.md`
- `src/metaharness_ext/boutpp/benchmark_runner.py`
- `src/metaharness/benchmark_drivers/compare.py`
- `docs/wiki/meta-harness-engineer/benchmark/09-boutpp-usage-validation-method.md`

Conclusion:

- 数值/科学求解质量：仍未证明。This slice is dry-run only with `real_tools = false`, `real_claude = false`, and `repeat_count = 1`; it validates proposal-contract reporting, not BOUT++ numerical behavior.
- Workflow quality：增强。BOUT++ fake-Claude dry-run lanes now write deterministic proposal-contract evidence instead of `not_checked`; the comparison bundle reports `direct_proposal_contract_status = valid`, `agent_proposal_contract_status = valid`, `direct` source `fallback_compiler`, and `agent` source `agent_contract_from_case_defaults`.
- Strongest supported statement：BOUT++ usage comparison can now make dry-run proposal source and contract status reviewer-visible in the same comparator fields used by newer suites.
- Non-claim：this is not real Claude proposal quality, not real BOUT++ execution evidence, not repair superiority, and not numerical/runtime superiority.
- Next evidence needed：retain clean real-tools + real-Claude comparison roots, add case-specific `T` NetCDF shape requirements, expand stable compiled examples, and collect repeated direct/agent real-tool proposal validity and failure-category rates.

Terminology explanation：`fallback_compiler` 指 direct lane 在 fake-Claude dry-run 中用 deterministic case defaults/materialized command 生成 contract evidence；`agent_contract_from_case_defaults` 指 agent lane 用 typed extension defaults 生成 contract evidence；这两者只是 workflow audit evidence，不代表真实 Claude 已经成功生成 BOUT++ workflow。

### 2026-05-05 — Lean proof real smoke and Claude-lane comparison

Source evidence:

- `.runs/user-lean-dry-smoke/lean-proof-benchmark/extension/simple-true-proof/summary.json`
- `.runs/user-lean-real-smoke/lean-proof-benchmark/extension/simple-true-proof/summary.json`
- `.runs/user-lean-real-claude/lean-proof-benchmark/comparison/result_bundle.json`
- `.runs/user-lean-real-claude/lean-proof-benchmark/comparison/run_manifest.json`
- `.runs/user-lean-real-claude/lean-proof-benchmark/comparison/summary_table.csv`
- `.github/workflows/lean-extension.yml`

Conclusion:

- 数值/形式化求解质量：只对 `simple-true-proof` 得到最小正例证据。real tools 和 real Claude lanes 都通过，说明本地 Lean/Lake 与 Claude proposal 能跑通这个简单 theorem；但这不是复杂定理发现、自动形式化能力、proof search superiority 或运行时优势证明。
- Workflow quality：增强。`lean-proof` suite 现在能通过 benchmark CLI 产生 extension/direct/agent lane summaries、valid proposal contracts、Lean evidence bundle、comparison bundle、manifest、summary table 和 claim-boundary artifacts。
- Claude lane evidence：real-Claude comparison 中 direct 与 agent proposal sources 都是 `real`，`proposal_contract_status = valid`，`preflight_status = passed`，`repair_advantage = none`，说明当前简单任务不展示 agent repair advantage。
- Approval status：comparison artifact 内的 approval gate 是 `not_configured`，因为 `benchmark-compare` 当前不接受 config root；单独 `benchmark-approval-check --config-root .mhe` 返回 `approved_with_limitations`，并排除 numerical/runtime/scientific superiority claims。
- Strongest supported statement：Lean extension 现在完成新扩展测试阶梯的静态检查、focused pytest、dry-run smoke、real Lean smoke、real-Claude comparison 和默认 CI dry-run workflow wiring。
- Non-claim：这不证明 Lean extension 比 direct Claude 更会证明定理，不证明广泛 Lean project formalization quality，不证明 proof search/runtime superiority，也不替代人工数学审查。
- Next evidence needed：增加更难 theorem catalog、malformed/underspecified Claude proposal challenge、重复 real-Claude pass/repair-rate aggregation、project-scale Lean fixtures，以及 comparator-visible approval config plumbing。

Terminology explanation：`real Lean smoke` 是实际调用 Lean/Lake 检查 theorem 文件；`real Claude` 表示 proposal 来自真实 Claude CLI 而不是 fake provider；`proposal_contract_status = valid` 只说明返回 JSON 满足当前简单 proof contract；`repair_advantage = none` 表示 direct 和 agent 在这个简单 case 中没有修复差异；`approval config plumbing` 是让 comparator artifact 直接带上 `.mhe` approval policy 结果。

### 2026-05-05 — Lean proof challenge cases and repair evidence roadmap

Source evidence:

- `docs/wiki/meta-harness-engineer/benchmark/14-lean-proof-evidence-roadmap.md`
- `.runs/lean-proof-challenge-dry/lean-proof-benchmark/comparison/result_bundle.json`
- `.runs/lean-proof-challenge-dry/lean-proof-benchmark/comparison/summary_table.csv`
- `.runs/lean-proof-positive-real-smoke/lean-proof-benchmark/extension/simple-true-proof/summary.json`
- `.runs/lean-proof-positive-real-smoke/lean-proof-benchmark/extension/implication-chain-proof/summary.json`
- `src/metaharness_ext/lean/benchmark_cases.py`
- `src/metaharness_ext/lean/benchmark_runner.py`

Conclusion:

- 数值/形式化求解质量：仍然只覆盖小型 theorem。`simple-true-proof` 和 `implication-chain-proof` 在 real Lean extension smoke 中通过，说明本地 Lean/Lake 能检查这些正例；但没有复杂定理、Mathlib 项目、重复 real-Claude 或人工数学审查。
- Workflow quality：增强。`lean-proof` 现在有 detailed evidence roadmap、非平凡正例、controlled malformed proposal repair case，以及 comparator-visible `agent_repaired_success` / `agent_repaired_direct_failure` evidence。
- Proposal/repair evidence：`malformed-proposal-repair` dry-run 中 direct lane 因 `proposal_contract_status = invalid` 和 `preflight_status = failed` 失败；agent lane 从 case defaults 修复，`agent_repairs = 1`，`repair_outcome = repaired_success`，comparison repair row 给出 `repair_advantage = agent_repaired_direct_failure`。
- Strongest supported statement：Lean benchmark 已从单一 happy path 扩展到可审计 challenge suite，能区分正例通过、proposal contract failure、agent repair 和 real Lean positive smoke。
- Non-claim：这不是 theorem discovery superiority，不是 proof search/runtime superiority，不是 repeated real-Claude stability，也不是 broad Lean project formalization quality 证明。
- Next evidence needed：运行 repeated real-Claude challenge comparison，加入 project-scale Lean fixture，补 comparator-visible approval config plumbing，并在更难 theorem catalog 上收集 pass/repair/failure-rate evidence。

Terminology explanation：`challenge case` 是为暴露特定行为设计的 benchmark case，例如 malformed proposal repair；`agent_repaired_success` 是 comparator verdict，表示 extension 基线通过、direct 失败而 agent 修复后通过；`repair_advantage = agent_repaired_direct_failure` 是更细的 repair evidence label；`positive real smoke` 只说明正例能被真实 Lean 检查，不代表广泛证明能力。

### 2026-05-05 — Lean repeated real-Claude challenge and project fixture evidence

Source evidence:

- `.runs/lean-proof-real-claude-challenge-r2/lean-proof-benchmark/comparison/result_bundle.json`
- `.runs/lean-proof-real-claude-challenge-r2/lean-proof-benchmark/comparison/repeat_summary.json`
- `.runs/lean-proof-real-claude-challenge-r2/lean-proof-benchmark/comparison/approval_gate.json`
- `.runs/lean-proof-real-claude-challenge-r2/lean-proof-benchmark/comparison/run_manifest.json`
- `docs/wiki/meta-harness-engineer/benchmark/14-lean-proof-evidence-roadmap.md`
- `src/metaharness_ext/lean/benchmark_cases.py`
- `src/metaharness_ext/lean/benchmark_runner.py`
- `src/metaharness_ext/lean/executor.py`
- `src/metaharness/cli.py`

Conclusion:

- 数值/形式化求解质量：增强但仍有边界。`simple-true-proof`、`implication-chain-proof`、`conjunction-swap-proof`、`project-helper-chain-proof` 和 `malformed-proposal-repair` 在 `repeat_count = 2` 的 real tools + real Claude comparison 中，extension/direct/agent lanes 都通过；这证明小型 theorem catalog 和一个小 Lake project fixture 可被真实 Lean/Lake 检查，但不证明 theorem discovery 或复杂 Mathlib formalization quality。
- Workflow quality：增强。`lean-proof` 现在保留 repeated pass/failure/repair rows、real-Claude proposal contract evidence、project helper file evidence、configured approval gate evidence，以及 CI dry challenge ladder。
- Pass/repair/failure-rate evidence：`repeat_summary.json` 中每个 case/lane row 都是 `passed_count = 2`、`failed_count = 0`、`skipped_count = 0`、`flags = []`；real-Claude direct/agent lanes 均为 `proposal_contract_status = valid`，`total_repairs = 0`。这说明本次真实 Claude prompt 没触发 repair contrast；repair advantage 仍来自 deterministic malformed dry-run challenge。
- Approval status：comparison artifact 现在通过 `benchmark-compare --config-root .mhe` 记录 `approved_with_limitations`，并显式排除 `numerical_solver_superiority`、`runtime_performance_superiority`、`scientific_correctness_without_domain_review` 和 `dry_run_as_real_solver_evidence`。
- Strongest supported statement：Lean benchmark 已完成下一阶段证据切片：更难小型 theorem catalog、project-scale fixture、repeated real-Claude/real-Lean comparison、pass/repair/failure-rate aggregation，以及 comparator-visible approval plumbing。
- Non-claim：这不是 MHE agent 相对 direct Claude 的 theorem-proving superiority，不是 proof search/runtime superiority，不是广泛 Lean 项目形式化能力证明，也不替代人工数学审查。
- Next evidence needed：扩大 repeat count，增加更难且经人工审查的 theorem cases，加入专门诱发 malformed/underspecified real-Claude proposal 的 stress prompts，并引入 Mathlib-scale or blueprint-style project evidence。

Terminology explanation：`repeat_count = 2` 表示每个 case/lane 运行两次，用来观察是否 flaky；`pass/repair/failure-rate evidence` 是按 repeated summaries 统计通过、修复和失败次数；`project fixture` 是包含 `Helper.lean` 和依赖它的 `Main.lean` 的小 Lake project；`approved_with_limitations` 表示 comparison 可以在 claim boundary 内使用，但仍排除数值、运行时和科学正确性优越性声明；`stress prompt` 是故意让 real Claude 面对欠明确或格式错误要求的 prompt，用来测试真实 repair behavior。

### 2026-05-04 — BOUT++ promotion rows, optional domain validation, and real-Claude proposal evidence

Source evidence:

- `.runs/boutpp-next-evidence/boutpp-usage-benchmark/comparison/result_bundle.json`
- `.runs/boutpp-next-evidence/boutpp-usage-benchmark/comparison/comparison_report.md`
- `.runs/boutpp-real-claude-evidence/boutpp-usage-benchmark/comparison/result_bundle.json`
- `src/metaharness/benchmark_drivers/compare.py`
- `src/metaharness_ext/boutpp/postprocess.py`
- `src/metaharness_ext/boutpp/validator.py`
- `docs/wiki/meta-harness-engineer/benchmark/09-boutpp-usage-validation-method.md`
- `docs/wiki/meta-harness-engineer/benchmark/11-boutpp-real-smoke-method.md`

Conclusion:

- 数值/科学求解质量：仍未证明。The new comparator row can surface repeated real-smoke promotion status, and optional NetCDF/domain checks can validate artifact metadata when opted in, but this does not prove BOUT++ numerical accuracy, convergence, runtime superiority, or broad solver-family support.
- Workflow quality：增强。`benchmark-compare` now exposes retained `boutpp_real_repeated_smoke_summary.json` data through `evidence_context.boutpp_real_smoke_rows` and generated report tables; skipped prerequisites remain reviewer-visible instead of hidden.
- Domain validation：新增 opt-in metadata path。Postprocess can collect NetCDF variables, dimension sizes, and variable dimensions when `netCDF4` is available; validator specs can require variables, dimensions, and variable-dimension mappings without making NetCDF mandatory for default dry-run or artifact-only smoke.
- Real-Claude proposal evidence：`.runs/boutpp-real-claude-evidence` ran direct and agent lanes with `real_claude = true`, proposal sources `real`, proposal contracts `valid`, preflight `passed`, and no repair/failure contrast. The verdict is `incomplete` only because the extension lane was intentionally not rerun in that direct/agent proposal-quality slice.
- Strongest supported statement：BOUT++ now has comparator-visible promotion evidence, optional domain metadata validation, and gated real-Claude proposal validity evidence for the usage contract.
- Non-claim：this is not real-tools direct/agent solver execution, not MHE-vs-direct numerical superiority, not performance superiority, not scientific validation, and not a broad BOUT++ application benchmark.
- Next evidence needed：run a clean retained real-tools + real-Claude comparison root with extension/direct/agent lanes where safe, add case-specific `T` NetCDF shape requirements for `conduction-real`, and collect repeated proposal pass/failure rates across more stable BOUT++ examples.

Terminology explanation：`promotion row` 是把 real-smoke summary 中的 pass/skip/prerequisite 状态放进 comparator/report；`optional domain validation` 是只有 case spec 明确要求时才检查 NetCDF 变量或维度；`real-Claude proposal evidence` 说明 proposal 来自真实 Claude CLI，但不代表真实 solver 已由 direct/agent lane 执行；`verdict = incomplete` 在只跑 direct/agent lanes 时是预期的，因为 extension lane 缺席。
