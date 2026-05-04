# Comparator and Reporting

Use this reference when implementing or auditing benchmark comparison bundles, result reports, and verdict logic.

## Artifact Truth Hierarchy

Final conclusions should cite only clean final roots and the persisted benchmark artifacts. Pilot runs are useful for diagnosing driver bugs, dependency issues, and backlog items, but not for manager-facing solver superiority claims.

Prefer this order when writing or reviewing claims:

1. `summary.json`
2. `attempt_log.json`
3. `result_bundle.json`
4. `run_manifest.json`
5. lane evidence files
6. method docs and chat summaries only as supporting context

Use this order when selecting evidence:

1. clean repeated final real-run roots;
2. clean single final real-run roots;
3. dry-run roots for workflow/schema/evidence claims;
4. pilot roots for bugs and backlog only.

If a runner bug is fixed after a pilot run, rerun into a fresh final root before updating conclusions.

## Comparator Inputs

The comparator should read persisted lane outputs, not in-memory runner state.

Expected input roots:

```text
.runs/<suite>-benchmark/extension/<case_id>/summary.json
.runs/<suite>-benchmark/direct/<case_id>/summary.json
.runs/<suite>-benchmark/agent/<case_id>/summary.json
```

Each lane summary should be normalized before comparison:

- `suite`
- `case_id`
- `lane`
- `status`
- `metrics`
- `diffs`
- `missing_metrics`
- `evidence_files`
- `attempt_count`
- `llm_calls`
- `elapsed_seconds`
- `driver_overhead_seconds`
- `skip_reason`
- `error_message`
- `flags`
- `proposal_contract_status`
- `preflight_status`
- `failure_category`
- `repair_outcome`
- `proposal_source` or lane-specific equivalent such as `direct_proposal_source`

Malformed or incomplete `summary.json` files should become `schema_failed` rows rather than crashing comparison.

## Required Outputs

A completed comparison bundle should write:

```text
comparison/summary_table.csv
comparison/comparison_report.md
comparison/result_bundle.json
comparison/run_manifest.json
reports/<suite>-analysis-report.md
reports/<suite>-backlog.md
```

`result_bundle.json` should include:

- suite name and output root;
- observed cases and lanes;
- normalized per-lane summaries;
- comparison rows;
- verdict counts;
- missing evidence list;
- manifest path;
- report paths.

`run_manifest.json` should record:

- suite;
- observed lanes;
- observed cases;
- run mode (`dry_run`, `real`, or mixed if applicable);
- whether real solver/tools were enabled;
- whether real Claude CLI was enabled;
- repeat count and repeat output layout;
- Claude binary, model, max turns, permission mode, and extra args;
- git revision when available;
- relevant tool versions and dependency availability;
- command/config metadata needed to reproduce the comparison.

## Fairness Checks

Before comparing direct and agent lanes, verify:

- direct and agent used the same Claude binary, model, max turns, permission mode, and extra args;
- real solver execution and real Claude invocation are reported as separate gates;
- all lanes used the same `case_spec.json` and source/reference artifacts;
- direct fallback/compiler substitutions are labeled and excluded from direct-Claude success claims;
- agent outputs came from `agent/<case_id>/`, not relabeled extension outputs;
- adaptive-agent claims cite repair/proposal deltas that changed pipeline input;
- timing separates driver overhead from solver/runtime metrics.

## Reviewer Checklist

Before approving a benchmark comparison claim, check:

- lane separation is explicit and artifact paths match the claimed lane;
- dry-run labels are present where no real solver or real Claude evidence exists;
- proposal source is explicit, including `direct_proposal_source` or an equivalent lane-specific field;
- fallback/compiler-generated direct outputs are excluded from direct-Claude success claims;
- proposal contract, preflight status, failure category, and repair outcome are comparator-visible;
- unsupported sentinels remain skipped and carry source/provenance evidence;
- approval status and excluded claims appear in the report if stronger claims are discussed;
- the report cites artifact roots before docs or chat memory.

## Evidence Validation

Evidence validation should check existence, not just count names in summaries.

For each evidence path listed in `summary.json`:

- resolve it under the lane directory unless already absolute;
- verify it exists;
- include missing files in the comparison row;
- mark rows with missing required evidence as workflow gaps.

Required lane evidence:

- all lanes: `case_spec.json`, `metrics.json`, `attempt_log.json`, `summary.json`;
- Claude lanes: `claude_prompt.txt`, `claude_command.json`, `claude_stdout.json`, `claude_stderr.txt`, `claude_result.json`, `proposal.json`;
- extension and agent positive cases: domain validation/evidence/config/stdout/stderr as appropriate;
- unsupported sentinels: source/provenance evidence and an explicit skip reason.

Policy gate formats vary by extension. Some extensions use structured gate objects (e.g., fealpy: `.gate`, `.decision.value`); others use dict-based gates (e.g., PyCFD: `{"gate": "...", "result": "pass"|"defer"|"reject", "reason": "..."}`). Comparators and governance adapters must handle both representations. Dict-based gates use `result` key with values `"pass"`, `"defer"`, or `"reject"`; gate issues should set `blocks_promotion = result == "reject"`.

## Verdict Taxonomy

Use verdicts that describe what was observed without overclaiming.

Recommended verdicts:

- `all_passed` — all expected lanes passed and required evidence exists.
- `both_passed_agent_more_evidence` — direct and agent passed; agent produced stronger validation/provenance evidence.
- `both_passed_direct_lighter` — direct and agent passed; direct was simpler/faster and evidence requirements were still met.
- `agent_recovered_direct_failed` — direct failed, agent passed after extension validation or repair.
- `agent_diagnosed_issue` — agent did not solve the case but produced useful structured failure evidence.
- `direct_passed_agent_failed` — direct passed while agent or extension-mediated workflow failed.
- `extension_baseline_failed` — extension lane failed for a supported case.
- `workflow_gap` — numeric outputs exist but required schema/evidence/provenance is missing.
- `capability_skip` — a known unsupported capability was skipped truthfully.
- `unavailable_dependency` — real-mode dependency was missing and the run skipped truthfully.
- `schema_failed` — summary or artifact shape could not be parsed/validated.
- `both_failed` — direct and agent failed without a usable recovery advantage.
- `incomplete` — required lanes or summaries are missing.

Do not convert evidence count alone into an advantage claim. Evidence matters when it improves reproducibility, diagnosis, validation, or auditability.

## Repeated-Run Rules

Repeated real runs are required before making timing or numerical stability claims.

For repeated runs, record a `repeat_summary.json` or equivalent aggregate with:

- run count;
- per-run metrics;
- median and interquartile range for driver timing;
- median solver elapsed time when emitted by real tools;
- maximum absolute/relative numeric error;
- pass/fail/skip rate;
- total LLM calls;
- repair count and successful repair count;
- parse failures and missing evidence count.

Suggested flaky flags:

- `flaky_timing` — timing variance exceeds the documented tolerance.
- `flaky_numeric` — numeric metrics cross tolerance across repeated runs.
- `flaky_parse` — solver output parsing intermittently fails.
- `flaky_dependency` — external binary/dependency availability changes between runs.
- `flaky_llm` — Claude proposal success varies across repeated prompts.

Dry-run comparisons should not report median solver timing as scientific evidence.

When `repeat_summary.json` exists, reports should use it for:

- median/IQR timing instead of a single `summary.json` elapsed value;
- pass/fail/skip rate instead of one status;
- repair success rate and total LLM calls;
- flaky flag explanations;
- deciding whether a final repeated run supports timing/stability claims.

## Report Requirements

Each analysis report should answer:

1. What suite, cases, lanes, and commands were run?
2. Was the run dry-run, real-mode, or mixed?
3. Which external tools/dependencies were available?
4. Which cases passed, failed, skipped, or had schema/evidence gaps?
5. What numerical claims are supported?
6. What workflow claims are supported?
7. What remains unsupported or non-claimable?
8. What should be optimized next in the MHE extension or benchmark driver?

Use explicit non-claims for dry-run reports:

```markdown
This report does not claim that the MHE extension improves real solver numerical accuracy or runtime. The current evidence supports workflow controllability and reproducibility claims only.
```

## Completion Criteria

Comparator/reporting work is complete when:

- malformed summaries become `schema_failed` evidence;
- missing evidence files are detected;
- all required comparison outputs are written;
- manifest records observed lanes/cases and tool availability;
- reports separate numerical solving claims from workflow quality claims;
- focused tests cover all-pass, capability skip, missing evidence, malformed summary, and incomplete lane coverage.
