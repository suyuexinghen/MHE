# Lane Runner Protocol

Use this reference when implementing or auditing benchmark runners and CLI behavior.

## Standard Lanes

Use three lanes unless scoped otherwise:

1. **extension** — deterministic MHE extension baseline, no LLM by default.
2. **direct** — Claude Code / Claude CLI directly generates or runs scripts/configs without extension mediation.
3. **agent** — Claude proposal plus MHE extension execution, validation, evidence, and archive path.

## New Suite Onboarding

When adding a benchmark suite for a new extension, touch these registration points before implementing the runner:

1. **`BenchmarkSuite` literal** in `MHE/src/metaharness/benchmark_drivers/models.py` — add the new suite name to the `Literal` type (e.g., `"fealpy-pde"`, `"pycfd-pde"`).
2. **`SUITE_DIRS`** in `MHE/src/metaharness/benchmark_drivers/io.py` — map the suite name to its output directory (e.g., `"pycfd-pde": "pycfd-pde-benchmark"`).
3. **Case catalog** — create a `domain_case_catalog()` function returning `list[BenchmarkCaseSpec]` with at least one positive case and any capability-gated sentinels.
4. **Preflight** — implement suite-specific dependency checks matching one of the dependency archetypes below.
5. **Runner constructor** — wire the preflight, compiler, executor, and validator into the runner; default `allow_real_tools=False`.

## Boundary Rules

Hard boundaries:

- Direct lane must not call `metaharness_ext.<name>` components unless the method doc explicitly defines a non-standard comparison.
- If direct lane uses an extension-generated fallback script/config, record a comparator-visible field such as `direct_proposal_source="fallback_compiler"` and exclude it from direct-Claude code-generation success rates.
- Extension lane must not depend on LLM proposal output.
- Agent lane must not bypass extension execution/validation when real-mode support exists.
- Agent lane must write artifacts under `agent/<case_id>/`, not relabel `extension/<case_id>/` outputs.
- Unsupported source formats or solver families must be skipped with a clear reason.

## Safe Runner Defaults

Default benchmark execution should be safe:

- no real solver calls unless `--allow-real-tools` or equivalent is present;
- no real hardware calls unless the user explicitly requests hardware testing;
- no real Claude CLI calls unless real tools are allowed or the user explicitly asks for them;
- dry-run mode writes deterministic summaries and evidence placeholders;
- generated artifacts stay under `.runs/` or the user-provided `--runs-root`.

## Real-Tool and Real-Claude Gates

Keep solver execution and Claude invocation separately auditable when the repo supports it:

- `--allow-real-tools` controls external solver, simulator, hardware, and scientific runtime calls.
- `--allow-real-claude` controls whether direct/agent lanes call a real Claude CLI instead of a fake brain provider.
- A run can be dry solver + real Claude to measure proposal quality without spending solver budget.
- A run can be real solver + fake Claude only for deterministic extension/agent plumbing tests, but reports must say so.

Real mode must:

- check binary/dependency availability before execution;
- write skip summaries if dependencies are missing;
- capture stdout/stderr;
- catch `TimeoutExpired` and `OSError` as failed summaries;
- preserve partial outputs when available;
- record tool versions in `run_manifest.json`.

## Preflight and Capability Probe

Before lane execution, add suite-specific preflight when the method requires it. Dependencies fall into one of these archetypes:

- **Binary**: check `shutil.which("binary")` — e.g., `octave-cli` (Octave), `Tester` / solver binary (Nektar).
- **Pip package**: check `importlib.util.find_spec("package")` — e.g., `qiskit`, `qiskit_aer` (QCompute).
- **Path-based**: check env var + directory existence + key file presence — e.g., `PYCFD_SRC_PATH` → `Solvers.py` existence and importability (PyCFD); `FEALPY_SRC_PATH` → `fealpy/__init__.py`.
- **Source-format**: check file extension or parser availability — e.g., ABACUS H/S source format → Hamiltonian converter.

Examples:

- **Nektar**: check `Tester`, selected solver binary, `.tst`, `.xml`, and extracted reference metrics.
- **QCompute**: check `qiskit`, `qiskit_aer`, and Hamiltonian fixture/source availability.
- **ABACUS bridge**: check source format availability and mark unsupported H/S bridge as sentinel skip.
- **Octave**: check `octave-cli` for real runs and source references for BIST-derived cases.
- **PyCFD**: check `PYCFD_SRC_PATH` env var or constructor arg, `Solvers.py` existence, numpy availability, Python version; mark unavailable status truthfully.

Preflight outputs should be written under:

```text
.runs/<suite>-benchmark/preflight/<case_id>/
```

Common files:

```text
preflight.stdout.log
preflight.stderr.log
preflight_summary.json
```

Use suite-specific names when already documented, such as `tester_summary.json` for Nektar.

## Adaptive Agent Protocol

If the agent lane claims LLM-in-the-loop behavior, require this loop to be visible in artifacts:

1. baseline extension execution;
2. validation failure or diagnostic trigger;
3. diagnostic bundle with stderr/stdout, validation issues, current spec/script/config, missing metrics, and evidence paths;
4. real or fake brain provider call for a typed repair proposal;
5. bounded recompile/re-execute under the same extension validator;
6. `AttemptLog` entries with `repair=True` and `llm_call=True` for repair attempts.

Do not claim adaptive advantage if Claude output is only stored as `proposal.json` and never changes the pipeline input.

### Claude Proposal Normalization

Claude JSON proposals frequently emit `null` for optional numeric fields. Before constructing Pydantic models from proposals:

- Normalize nulls to domain-appropriate defaults via a `_coerce(v, default)` helper (returns `default` when `v is None`).
- Validate the constructed model; surface schema mismatches as preflight failures with the specific field and error.
- Write preflight failures to `preflight_summary.json` with the raw proposal preserved for diagnosis.

## Fairness Constraints

To keep direct vs agent comparisons meaningful:

- all lanes use the same `case_spec.json`;
- all lanes use the same solver binary and source inputs;
- direct and agent lanes use the same Claude CLI binary, model, max turns, budget, and prompt policy;
- direct lane does not import extension internals, except for explicitly labeled fallback/compiler baselines that are excluded from direct-Claude success claims;
- agent lane does not bypass the extension pipeline;
- proposal source, preflight status, failure category, and repair outcome are comparator-visible;
- timing separates driver overhead from solver runtime;
- failure attempts are recorded in `attempt_log.json`;
- reports do not convert evidence count alone into a superiority claim.

## Evidence Files by Lane

Every lane should write:

```text
case_spec.json
metrics.json
attempt_log.json
summary.json
```

Claude lanes should write:

```text
claude_prompt.txt
claude_command.json
claude_stdout.json
claude_stderr.txt
claude_result.json
proposal.json
```

Extension/agent positive cases should write domain evidence, for example:

- validation result;
- evidence bundle;
- generated script/session/config;
- solver stdout/stderr;
- source/reference artifact copy or pointer;
- environment probe.

Unsupported sentinel cases should write source/provenance evidence and a skip reason.

## Runner Completion Criteria

A runner slice is complete when:

- dry-run works without external tools;
- real mode is gated and skips truthfully when tools are missing;
- every lane writes normalized `LaneSummary` and `AttemptLog`;
- evidence files listed in summary are actually created;
- focused tests cover positive dry-run, skipped sentinel, missing dependency, and failure handling;
- CLI can run selected cases and all cases.
