---
name: mhe-benchmark-iteration
description: Run the MHE extension benchmark improvement loop from design docs to executable comparison tests, analysis reports, backlog-driven extension optimization, and benchmark conclusion summaries. Use when the user asks to compare MHE extension vs direct Claude Code/CLI, design or run benchmark suites, write experiment reports, judge extension advantages, summarize comparison conclusions, or turn benchmark findings into MHE extension improvement tasks. Triggers: "MHE benchmark", "extension vs Claude Code", "对比实验", "自动化测试改进", "benchmark reports", "scientific workflow comparison", "harness iteration loop", "summarize comparison conclusion", "comparison conclusion", "benchmark conclusion summary".
---

# MHE Benchmark Iteration Loop

Use this skill as a lightweight router for the MHE benchmark improvement loop.

The loop is:

1. write truthful benchmark design documents;
2. implement or reuse runnable benchmark drivers;
3. execute safe comparison tests;
4. generate comparison bundles;
5. write evidence-based analysis reports;
6. convert findings into MHE extension optimization backlog;
7. repeat until the harness design improves.

## Core Principle

Do not claim solver superiority from workflow dry-runs. Always separate:

- **Numerical solving quality**: real solver accuracy, convergence, residual/error norms, timing, and repeated-run stability.
- **Workflow quality**: reproducibility, schema validation, evidence completeness, provenance, failure diagnosis, repair attempts, batch case management, and comparator automation.

MHE extension advantages usually appear first in workflow quality. Numerical advantages require real external tools, repeated runs, and solver-specific metrics.

## Choose Mode First

- **Design / Planning**: use when benchmark method docs, case lists, lane design, or non-claims are missing.
- **Implementation**: use when adding or fixing case catalogs, runners, CLI support, comparator outputs, schemas, or tests.
- **Execution / Reporting**: use when running dry-run or real-run benchmark commands and writing analysis reports. For real runs, first classify outcomes as capability skip, dependency skip, runner bug, solver failure, or LLM proposal failure before drawing conclusions.
- **Audit / Improvement**: use when reviewing existing reports and turning findings into extension backlog or skill improvements.

## Minimal Startup Checklist

Before doing multi-step work, confirm current truth from files, not memory:

1. Read benchmark index: `MHE/docs/wiki/meta-harness-engineer/benchmark/README.md`.
2. Read the relevant method document, analysis report, and completion/backlog report.
3. Inspect current benchmark code under `MHE/src/metaharness/benchmark_drivers/`.
4. Inspect focused tests under `MHE/tests/test_benchmark_drivers_*.py`.
5. If artifacts exist, inspect `.runs/<suite>-benchmark/comparison/result_bundle.json` and `run_manifest.json`.
6. Decide whether current evidence is dry-run, real solver, real Claude, or repeated real-run before drawing conclusions.
7. Check whether the agent lane's Claude proposal actually parameterizes/repairs the extension pipeline; if it is only logged as evidence, do not claim LLM-in-the-loop workflow advantage.

## Read References On Demand

Use progressive disclosure: read only the reference needed for the current phase.

- `references/design-method-docs.md`
  - method doc template, scope/non-claims, case catalog requirements, and category-error guardrails.
- `references/lane-runner-protocol.md`
  - standard lanes, lane boundaries, safe runner behavior, preflight, real-tool gating, and fairness constraints.
- `references/comparator-reporting.md`
  - comparator outputs, schema/evidence validation, verdict taxonomy, repeated-run/flaky rules, artifact truth hierarchy, and report requirements.
- `references/real-run-repeated-protocol.md`
  - real-run/repeat protocol, clean final roots vs pilot roots, failure rerun rules, and final-report evidence hierarchy.
- `references/iteration-backlog.md`
  - boss-facing summary, backlog table format, extension optimization categories, and iteration exit criteria.

## Default Behavior

- Prefer dry-run first unless the user explicitly asks for real tools.
- Treat `.runs/**/summary.json`, `attempt_log.json`, `result_bundle.json`, `run_manifest.json`, and evidence files as truth.
- For real comparison, prefer this order: Octave real-mode smoke first, QCompute FCIDUMP proxy second, Nektar real replay after session mapping, PyCFD short-case real solver baseline before full catalog, ABACUS bridge only after parser/converter evidence exists.
- If `--allow-real-tools` and `--allow-real-claude` are separate flags in the current repo, record and report both; do not conflate solver execution with real Claude proposal quality.
- Never use chat memory alone as report evidence.
- Do not hide unsupported capabilities; encode them as skipped sentinel cases.
- For skipped sentinel cases, write reviewer-facing artifacts that explain the skip: original source refs, parsed metadata if available, missing capabilities, promotion readiness, and a conversion/execution plan status. Tests should assert both the skip and the evidence fields, not only `summary.status == "skipped"`.
- Do not merge unrelated scientific categories into one superiority claim.
- Do not compare unrelated domain metrics as if they share one meaning: PyCFD residuals, Nektar L2/Linf, Fealpy FEM errors, Octave analytic errors, QCompute energy errors, and ABACUS converter status require separate interpretation.
- Do not treat evidence count alone as workflow superiority.
- When comparing direct vs agent lanes, surface proposal contract, proposal source, preflight status, and repair evidence explicitly; do not bury them in lane summaries.
- If direct lane uses an extension-generated fallback script/config, expose a field such as `direct_proposal_source="fallback_compiler"` and exclude that row from direct-Claude code-generation success claims.
- For dry-run repair claims, require `proposal_contract_status`, `repair_outcome`, `repair_count`, and comparator-visible `repair_advantage` before saying the agent lane is stronger.
- Manager-facing reports must include approval status, excluded claims, and evidence required to unlock stronger scientific/numerical claims.
- When summarizing any MHE benchmark comparison conclusion, append or update the central report at `docs/wiki/meta-harness-engineer/benchmark/mhe-extension-comparison-conclusions.md` unless the user explicitly asks for chat-only output.
- Do not commit changes unless explicitly asked.
- If the work spans reporting, roadmap updates, or handoff decisions, load and use `project-leader` to keep state coherent and separate active execution from stop/handoff guidance.

## Suite Onboarding Gate

Before implementing a new comparison suite, require the method document to name the suite, case catalog, positive and sentinel cases, lane boundaries, artifact layout, commands, comparator columns, approval gates, and non-claims. Do not begin real-run execution until this design exists and the first dry-run schema smoke can be validated.

## Proposal Contract and Repair Evidence Pattern

When an MHE agent lane claims workflow advantage over direct Claude Code, make the repair path auditable:

1. define a narrow proposal contract for the case family, including required fields and allowed claim boundaries;
2. validate direct and agent proposals against the same contract;
3. let the direct lane fail malformed proposals instead of silently repairing them unless the direct baseline explicitly includes repair logic;
4. let the agent lane repair only from deterministic case defaults or validated proposals, and record the repair as workflow evidence, not solver evidence;
5. write contract artifacts such as `qec_proposal_contract.json` beside lane summaries;
6. propagate `proposal_contract_status`, `repair_outcome`, `repair_count`, and `repair_advantage` into `result_bundle.json`, `summary_table.csv`, `comparison_report.md`, and generated analysis reports;
7. test both valid-proposal consumption and malformed-proposal repair, including a contrast where direct fails and agent repairs;
8. claim only structured workflow controllability unless real tools, real Claude, repeated runs, and domain metrics support a stronger claim.

Useful `repair_advantage` labels:

- `agent_repaired_direct_failure`: direct failed contract validation while agent repaired and passed.
- `agent_more_repair_evidence`: agent produced additional audited repair evidence while both lanes passed.
- `direct_more_repair_evidence`: direct produced more repair evidence than agent.
- `none`: no repair contrast is present.

## Real QEC Gate Pattern

For quantum error-correction benchmark slices, keep the real-execution gate explicit:

1. dry-run QEC can validate topology, stabilizer shape, proposal contracts, artifact schemas, and non-claims;
2. dry-run QEC must not claim real syndrome sampling, decoder execution, threshold behavior, hardware logical error suppression, or QCompute/CUDA-Q numerical superiority;
3. real-mode QEC should stay skipped until `qec_backend_adapter`, `real_syndrome_sampling`, `decoder_execution`, and `repeat_run_validation` exist;
4. write `qec_real_execution_gate.json` with `promotion_ready = false`, missing capabilities, and the proposal contract status;
5. promote a QEC case from dry-run to real execution only after backend adapter tests, repeated validation, and scientific review evidence exist.

Recommended QEC iteration order:

1. comparator/report upgrade for proposal contract and repair evidence;
2. evidence-based analysis report and backlog update;
3. real Claude challenge run with underspecified, malformed, and overclaiming prompts;
4. repeated-run aggregation for contract pass rate, repair rate, flaky count, and median driver time;
5. real QEC backend integration only after the workflow evidence is reviewer-visible.

## Unsupported Capability Pattern

When a benchmark suite includes a not-yet-supported scientific bridge or solver capability, make the unsupported state auditable instead of merely skipping:

1. keep the benchmark case capability-gated and skipped;
2. preserve source provenance in a `source_refs` artifact;
3. parse safe metadata if available, but do not convert or execute unsupported formats;
4. write a status artifact with `missing_capabilities`, `promotion_ready = false`, and a plan/status field such as `metadata_only` or `converter_missing`;
5. add a real-looking fixture test that proves metadata parsing does not accidentally enable conversion;
6. document the artifact fields reviewers should inspect;
7. whenever the status artifact schema gains reviewer-facing fields, update method/report JSON snippets in the same slice or record a named evidence-completeness follow-up;
8. only promote the sentinel after conversion/execution tests and scientific validation exist.

## Benchmark Conclusion Summary Pattern

When summarizing benchmark comparison conclusions, always use a rule-based structure before any recommendation and keep the central comparison report current:

- **Numerical solving quality** — state exactly what real solver, real Claude, repeated-run, and domain-metric evidence supports. If both direct and agent lanes pass repeated real runs, say they both stably drove the workflow; do not turn that into an accuracy or runtime superiority claim.
- **Workflow quality** — state evidence-backed differences in controllability, reproducibility, schema completeness, attempt logs, proposal preflight, metric detail tables, repeat summaries, approval gates, failure classification, artifact retention, and report automation.
- **Proven framework capability** — separately summarize what the benchmark harness itself has proven, such as unified `benchmark-run` / `benchmark-compare`, lane summaries, manifests, comparison bundles, repeat aggregation, report plumbing, dry-run/real-run labeling, dependency skips, proposal failures, solver failures, and repair outcomes.
- **Limitations and non-claims** — explicitly list unsupported scientific bridges, skipped sentinels, proxy-only conversions, missing production converters, absent human/scientific signoff, and dry-run limits. Never let reviewer evidence, approval status, or proxy validation replace scientific validation.
- **Product value** — express the strongest current value as workflow controllability, evidence completeness, claim-boundary enforcement, and overclaim prevention, not direct numerical superiority.
- **Current external statement** — combine the evidence and limitations into one claim-boundary-safe sentence: current evidence may support workflow controllability and auditability, while numerical/performance superiority remains unproven unless clean repeated final real-run evidence supports it.
- **Central report update** — append the conclusion to `docs/wiki/meta-harness-engineer/benchmark/mhe-extension-comparison-conclusions.md` under `Dated conclusion log`, or update the relevant suite section if the new evidence supersedes an older statement. Include evidence root/source document, real/dry-run state, supported conclusion, explicit non-claims, and next evidence needed.
- **Next evidence needed** — name the smallest evidence-producing step that would unlock stronger claims, such as accepted reference fixtures, production converters, broader real preflight, additional solver families, retained repeated-run artifacts, direct-lane review, human/scientific signoff, or repair/success-rate comparison.
- **Terminology explanation** — when the summary uses potentially unfamiliar English benchmark terms, append a short explanation paragraph in the user's language. Explain terms such as `dry-run`, `real tools`, `lane`, `proposal contract`, `repair_outcome`, `repair_advantage`, `artifact`, `evidence bundle`, `sentinel`, and `claim boundary` so the conclusion is understandable outside the benchmark implementation context.

## Boss-Facing Short Answer

When asked whether MHE extension is better than direct Claude Code, answer in two layers:

1. **Numerical solving quality**: dry-run or mocked benchmark cannot prove real solver accuracy or runtime superiority. Real conclusions require `--allow-real-tools`, real solvers/hardware, repeated runs, and domain metrics.
2. **Workflow quality**: MHE extension can show advantages in structured specs, fixed execution boundaries, validation, evidence, provenance, schema, batch case management, capability skips, and comparator/report automation. Direct Claude Code is more flexible but easier to make non-reproducible.

Recommended conclusion pattern:

> Current evidence does not yet prove that MHE extension improves solver numerical accuracy or runtime. It does show that MHE extension improves scientific workflow controllability and reproducibility. The next iteration should use real runs and LLM-in-the-loop repair/validation to turn workflow advantages into measurable success-rate and repair-rate advantages.
