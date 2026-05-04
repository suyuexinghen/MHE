# Iteration Backlog

Use this reference when turning benchmark findings into MHE extension improvement tasks, boss-facing summaries, and next-iteration plans.

## Boss-Facing Summary

Use this structure when a manager asks whether the MHE extension is better than direct Claude Code.

```markdown
目前我们完成了从 benchmark 设计、执行、comparison bundle 到分析报告的第一轮闭环。

结论分两层：

1. 数值求解优劣：当前如果是 dry-run / mocked benchmark，不能声称 MHE extension 在真实数值精度或求解时间上优于直接 Claude Code。真实结论需要 `--allow-real-tools`、真实 solver、重复运行和 domain metrics。
2. Workflow 优劣：MHE extension 的优势已经体现为结构化输入、固定执行边界、验证、evidence、provenance、schema、批量 case 管理、capability skip 和 comparator/report 自动化。直接 Claude Code 更灵活，但更容易缺 evidence、缺 schema、输出不可复查。

因此当前判断是：MHE extension 的短期优势是科学计算 workflow 的可控性和可复现性；下一步要让 LLM 更多参与 repair、validation、参数选择和失败诊断，把 workflow 优势转化为真实求解成功率优势。
```

If real repeated solver runs exist, add the supported numerical conclusion separately and cite the run bundle path.

When writing comparison conclusions, explain the rule rather than pasting a fixed example:

- Start by separating numerical solving quality from workflow quality. This prevents repeated real-run pass rates from being overread as solver accuracy or runtime superiority.
- For numerical solving quality, name the evidence class first: dry-run, single real run, repeated final real run, real Claude enabled or disabled, and domain metrics available. Only state numerical or performance advantage when clean repeated final roots and domain metrics support it.
- When direct and agent lanes both pass repeated real runs, summarize that as stable workflow execution for both lanes. Do not claim that the agent lane solved the scientific problem more accurately, faster, or more intelligently unless the metric table proves that exact contrast.
- For workflow quality, compare auditability and reproducibility features: summary schema, attempt log, proposal preflight, metric detail table, repeat summary, approval gate, preflight summary, failure classification, evidence retention, and report automation.
- Describe direct Claude Code fairly: it is more flexible, but its benchmark weakness is usually weaker structure, environment dependence, shell/manual assumptions, and less standardized evidence.
- Add a separate proven-framework-capability paragraph when the benchmark system itself is the strongest result. Summarize whether unified `benchmark-run` / `benchmark-compare`, three-lane structure, summaries, attempt logs, manifests, comparison bundles, repeat summaries, dry-run/real-run labels, failure categories, proposal failures, dependency skips, solver failures, and repair outcomes are working.
- Add a limitations and non-claims paragraph before the plan. Keep proxy conversions, skipped sentinels, missing production converters, absent reference fixtures, missing tolerance tables, and missing human/scientific signoff explicit. Do not let ACP/reviewer evidence or admin approval replace scientific signoff.
- State product value as workflow controllability, evidence completeness, claim-boundary enforcement, and overclaim prevention. Avoid framing product value as numerical accuracy or performance superiority unless repeated final real-run metrics prove it.
- End with a claim-boundary-safe external conclusion and the next evidence needed. The external conclusion should say what is proven now, what is not proven, and which next run or artifact would unlock a stronger claim.
- When planning the next phase, prefer evidence that changes claim boundaries over larger proxy coverage. Examples include accepted reference fixtures, production converters, human/scientific signoff, broader real solver preflight, retained repeated-run artifacts, and repair/success-rate comparisons.

## Backlog Table Format

Use a compact backlog table so benchmark findings become implementable work.

```markdown
| ID | Area | Symptom | Evidence | Suggested fix | Priority |
|---|---|---|---|---|---|
| B1 | Real execution coverage | Dry-run only for Octave positive cases | `.runs/.../run_manifest.json` reports dry-run | Add gated real Octave smoke and repeated-run metrics | High |
```

Each row should include:

- **Area** — one of the optimization categories below.
- **Symptom** — observed benchmark limitation or failure.
- **Evidence** — concrete artifact path, verdict, skipped case, or test failure.
- **Suggested fix** — the smallest actionable implementation slice.
- **Priority** — High, Medium, or Low based on whether it blocks truthful claims.

Common rows after first-round benchmark audits:

```markdown
| B-real-claude | Boundary gaps | Real Claude and real solver gates are coupled or unclear | `run_manifest.json` lacks separate `real_claude`/`real_tools` fields | Split gates and record both in manifest/report | High |
| B-proposal-source | Boundary gaps | Direct lane uses extension-generated fallback script/config without labeling it | `summary.json` lacks `direct_proposal_source` or comparison report credits fallback as direct-Claude success | Record proposal source and exclude fallback rows from direct-Claude generation success claims | High |
| B-proposal-repair | Boundary gaps | QEC or similar workflow repair is reported only as lane success without provenance | comparison rows omit `proposal_contract_status`, `repair_outcome`, or `repair_advantage` | Surface proposal provenance + repair evidence in comparator and report outputs | High |
| B-direct-review | Boundary gaps | Direct lane generated code is treated as trusted without human or automated review evidence | `claude_result.json` exists but no review/preflight status is comparator-visible | Add direct-lane code review or proposal-contract preflight and expose the result | High |
| B-agent-loop | LLM participation | Agent lane only stores `proposal.json` and never changes execution input | `attempt_log.json` has no repair attempts or proposal delta | Add bounded validation-triggered repair loop | High |
| B-approval-gate | Schema gaps | Reports omit approval status, excluded claims, or promotion blockers | `result_bundle.json` has approval context but analysis report does not cite it | Propagate approval profile, limitations, excluded claims, and evidence needed for promotion | High |
| B-domain-metric-boundary | Schema gaps | Report compares unrelated domain metrics as if they share one meaning | report mixes residuals, FEM errors, analytic errors, energy errors, or converter status | Add domain-specific metric interpretation and non-claim wording | High |
| B-real-run-parity | Real execution coverage | Suite jumps from dry-run to broad comparison without short real-solver baseline | final root missing small-case solver baseline or repeat aggregate | Add phase ladder: dry-run schema smoke, real solver baseline, real Claude comparison, repeated full catalog | High |
| B-abacus-bridge | Capability gaps | ABACUS H/S source cannot flow into QCompute | `bridge_status.json` reports converter missing | Add parser fixture, converter, and validation before promoting sentinel | High |
| B-nektar-real | Real execution coverage | Nektar extension/agent real replay is skipped or unmapped | tester/preflight summary or lane skip reason | Map sessions to solver binaries and extension dispatch | Medium |
| B-driver-portability | Driver portability bugs | Real tools expose assumptions hidden by dry-run, such as Octave `jsonencode` or Nektar cwd/path handling | pilot run stdout/stderr and failed summary | Fix runner portability, then rerun in clean final root | High |
| B-governance-placeholder | Governance gaps | `emit_runtime_evidence()` returns dict without backend persistence | `audit_refs` empty in real mode; no session events persisted | Inject SessionStore/AuditLog/ProvGraph into governance adapter | High |
| B-claude-nulls | Schema gaps | Claude proposal contains null for required numeric fields | preflight log shows Pydantic validation error on `None` | Add `_coerce` helper to normalize nulls to domain defaults before model construction | Medium |
| B-path-probe | Real execution coverage | Path-based dependency not gated before compilation | preflight summary reports env var not found or key file missing | Add env var / path existence / file check to suite preflight | High |
```

Avoid backlog entries that are just aspirations. Every item should trace to a benchmark finding or a documented non-claim.

## Optimization Categories

### Real Execution Coverage

Use when dry-run coverage exists but real solver/hardware/tool execution is missing or a suite needs phased parity evidence.

Examples:

- add `--allow-real-tools` smoke for supported Octave cases;
- run a short PyCFD real solver baseline before full-catalog comparison;
- gate Nektar solver execution on `Tester` and solver binary availability;
- run QCompute proxy cases only when `qiskit` and `qiskit_aer` are available;
- capture stdout/stderr, versions, timeout failures, and partial outputs.

### LLM Participation

Use when the current pipeline is too fixed and Claude only generates a one-shot proposal.

Examples:

- add repair attempts after validation failure;
- let Claude propose solver parameters within extension-validated schema bounds;
- ask Claude to diagnose failed solver stdout/stderr;
- compare direct vs agent success rate across repeated attempts;
- record proposal deltas and repair decisions in `attempt_log.json`.

### Schema Gaps

Use when summaries or reports lack fields needed for fair comparison.

Examples:

- require run mode on every summary;
- validate `attempt_log.json` shape;
- add missing evidence file checks;
- distinguish solver runtime from driver overhead;
- normalize skip reasons across suites.

### Capability Gaps

Use when unsupported solver families, source formats, or converters block real cases.

Examples:

- implement Nektar `DiffusionSolver` extension dispatch before promoting `diffusion-2d`;
- implement ABACUS H/S-to-Hamiltonian conversion before promoting bridge sentinel;
- add source parser support for a new upstream fixture format;
- keep unsupported cases skipped until extension tests pass.

### Provenance Gaps

Use when reports cannot trace outputs to source fixtures, upstream tests, or generated artifacts.

Examples:

- copy or reference upstream source files;
- record source line numbers or test IDs;
- include environment probes in evidence bundles;
- add artifact lineage from proposal to generated script/config to validated metrics.

### Statistics Gaps

Use when single runs are not enough for timing, stability, or success-rate claims.

Examples:

- add repeated-run counts;
- compute median/IQR timing;
- flag flaky numeric, timing, parse, dependency, or LLM behavior;
- report pass/fail and repair success rates.

### Driver Portability Bugs

Use when real-run pilot artifacts expose runner assumptions hidden by dry-run or mocked tests.

Examples:

- Octave script uses functions unavailable in the target `octave-cli`, such as version-specific `jsonencode` behavior;
- Nektar replay assumes cwd-relative paths that fail under isolated run roots;
- solver wrapper drops partial stdout/stderr on timeout;
- generated scripts work in tests but fail under the real binary's path/module environment.

Portability bug rows should point to pilot artifacts and require a clean final rerun after the fix.

### Boundary Gaps

Use when lane separation, proposal provenance, approval limits, or claim boundaries are ambiguous or unenforced.

Examples:

- assert direct lane never imports `metaharness_ext.<name>` unless explicitly labeled as fallback/compiler baseline;
- assert extension lane never consumes Claude proposal output;
- assert agent lane writes under `agent/<case_id>/`;
- expose `direct_proposal_source` and exclude fallback rows from direct-Claude success claims;
- include approval status, excluded claims, and promotion blockers in reports;
- keep domain metrics interpreted separately instead of merging residuals, FEM errors, analytic errors, energy errors, and converter status;
- ensure unsupported sentinels are skipped, not fake-passed.

### Governance Gaps

Use when the extension's governance adapter is a placeholder and needs runtime backend injection for audit trail, provenance, and session event persistence.

Examples:

- migrate `emit_runtime_evidence()` from dict-return to SessionStore/AuditLog/ProvGraph persistence;
- add `build_candidate_record()` with `GraphSnapshot` construction and `CandidateRecord` output;
- emit `CANDIDATE_VALIDATED`, `SAFETY_GATE_EVALUATED`, `CANDIDATE_REJECTED` session events via `make_session_event()`;
- verify Merkle-anchored audit records in `AuditLog` and PROV-O entities/relations in `ProvGraph`;
- add tests that exercise each backend (InMemorySessionStore, AuditLog, ProvGraph) independently.

## Prioritization Rules

Use High priority for items that block truthful benchmark claims:

- real-mode support for the suite's main positive case;
- missing required evidence or malformed summaries;
- lane-boundary violations;
- unsupported sentinel promoted as passed;
- comparator crash on malformed artifacts.

Use Medium priority for items that improve scientific confidence:

- repeated-run statistics;
- richer provenance;
- repair loop instrumentation;
- additional source fixture coverage.

Use Low priority for polish:

- report wording refinements;
- additional convenience commands;
- optional visualization;
- extra cases after the first-round catalog is stable.

## Next-Iteration Plan

A good next iteration should name:

1. One suite and task family.
2. One or two positive cases.
3. Any sentinel cases that remain skipped.
4. Real-tool prerequisites.
5. The exact benchmark command.
6. Comparator/report outputs to inspect.
7. The claim that would become newly supportable if the iteration succeeds.

Template (existing suite):

```markdown
Next iteration: `<suite>` real-mode smoke for `<case_ids>`.

- Prerequisites: `<binaries/dependencies>`.
- Command: `PYTHONPATH=src python -m metaharness.cli benchmark-run ... --allow-real-tools`.
- Compare: `PYTHONPATH=src python -m metaharness.cli benchmark-compare ...`.
- New supportable claim: `<real numeric correctness | repair success rate | dependency skip truthfulness | provenance completeness>`.
- Remaining non-claims: `<what still cannot be concluded>`.
```

Template (new suite first-round):

```markdown
Next iteration: onboard `<suite>` with dry-run smoke for all first-round cases.

- Registration: add suite to `BenchmarkSuite` literal and `SUITE_DIRS` mapping.
- Cases: `<positive_case_ids>`; sentinels: `<skipped_case_ids>`.
- Command: `PYTHONPATH=src python -m metaharness.cli benchmark-run --suite <suite> --cases <case_ids> --lanes extension,direct,agent`.
- New supportable claim: dry-run workflow produces `LaneSummary` with domain-specific metrics for all 3 lanes; capability-gated cases skip truthfully.
- Remaining non-claims: no real-solver execution; real-mode gated behind `--allow-real-tools`; agent lane uses fake brain provider.
```

## Iteration Exit Criteria

An iteration is complete when:

- design/method docs state scope and non-claims;
- runner outputs exist for selected lanes/cases;
- comparator bundle is generated;
- analysis report cites actual artifact paths;
- backlog rows map directly to evidence;
- unsupported capabilities remain explicit skips;
- conclusions separate numerical solving quality from workflow quality;
- the next iteration has a smallest actionable slice.

Do not exit an iteration by claiming extension superiority from dry-run artifacts alone.
