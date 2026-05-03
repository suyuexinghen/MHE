# PyCFD PDE Comparison Benchmark Method

> Version: v0.1 | Last updated: 2026-05-03 | Suite: `pycfd-pde`

## Purpose

This document defines how to run and report a PyCFD comparison benchmark in the same evidence-first style as the Octave, Nektar, QCompute, and ABACUS benchmark documents in this directory.

The benchmark compares three workflow lanes on the same PyCFD 2D Euler case catalog:

- **Extension lane**: deterministic `metaharness_ext.pycfd` pipeline with no LLM generation.
- **Direct lane**: Claude CLI proposes a standalone `solve.py` script, then the runner executes it under controlled subprocess boundaries.
- **Agent lane**: Claude CLI proposes a `pycfd_spec` or `spec_patch`, then MHE validates and executes the task through the PyCFD extension pipeline.

The primary question is workflow quality, not solver superiority: does the MHE extension/agent path improve controllability, validation, evidence capture, repair traceability, and batch comparison against a direct Claude CLI workflow using the same case spec?

## Scope and Non-Claims

This benchmark covers:

- PyCFD's current 2D Euler finite-volume benchmark catalog.
- Path-based PyCFD discovery through `PYCFD_SRC_PATH` or `--pycfd-src-path`.
- Residual-based validation using `residual_l1` and `residual_l2` tolerances.
- Real solver execution when `--allow-real-tools` is explicitly enabled.
- Real Claude proposal evidence when `--allow-real-claude` is explicitly enabled.
- Proposal preflight, repair attempts, attempt logs, lane summaries, comparison bundles, approval gates, and claim-boundary reporting.

This benchmark does not claim:

- PyCFD is numerically superior to Fealpy, Nektar, Octave, QCompute, or direct Claude Code.
- Residual norms are FEM-style error norms or sufficient scientific validation by themselves.
- Dry-run metrics are real solver evidence.
- Admin approval proves CFD correctness or runtime superiority.
- Direct lane correctness is established when the runner falls back to the internal PyCFD compiler instead of executing Claude-generated `solve.py`.
- New 3D, viscous, turbulence, or multiphysics PyCFD capability exists before upstream PyCFD supports it and the extension adds tested cases.

## Evidence Roots

Planned canonical output root:

```text
<runs-root>/pycfd-pde-benchmark/
```

Existing observed PyCFD evidence may also live under a named run root such as:

```text
.runs/pycfd-benchmark/pycfd-pde-benchmark/
```

Checked-in claim-boundary and approval references:

```text
.mhe/benchmarks/pycfd-approval.json
.mhe/approvals/pycfd_pde_benchmark_approval.json
.mhe/approvals/pycfd_direct_lane_code_review.json
.mhe/evidence/pycfd_pde_evidence_bundle.json
.mhe/evidence/comparison_benchmark_evidence_bundle.json
```

Related design/reporting documents:

```text
docs/wiki/meta-harness-engineer/pycfd-engine-wiki/README.md
docs/wiki/meta-harness-engineer/blueprint/09-pycfd-comprehensive-work-report.md
docs/wiki/meta-harness-engineer/blueprint/09-pycfd-cross-extension-comparison.md
docs/wiki/meta-harness-engineer/benchmark/08-real-run-evidence-plan-analysis.md
```

## Suite and Cases

Suite name:

```text
pycfd-pde
```

The case catalog is defined by `pycfd_case_catalog()` in `src/metaharness_ext/pycfd/benchmark_cases.py`.

| Case ID | Physics | Mesh / setup | Expected metrics | Validation role |
|---|---|---|---|---|
| `vortex-2d` | Isentropic vortex advection | Structured generated tri mesh | residuals, timing, mesh counts | Unsteady smooth-flow residual behavior |
| `airfoil-2d` | NACA 0012 inviscid flow | Quad/unstructured-style airfoil setup | residuals, timing, mesh counts | Steady engineering-style CFD workflow |
| `cylinder-2d` | Inviscid cylinder flow | Structured tri setup | residuals, timing, mesh counts | Steady external-flow workflow |
| `mms-2d` | Manufactured-solution case | Structured quad mesh | residuals, timing, mesh counts | Verification-oriented residual surface |
| `shock-diffraction-2d` | Mach shock diffraction | Structured quad setup | residuals, timing, mesh counts | Shock-capturing workflow |

Common metrics:

```text
residual_l1
residual_l2
wall_time_seconds
iterations
ncells
nnodes
nfaces
return_code
```

Residual tolerances must come from the case spec or reviewed tolerance table. They must not be relaxed after seeing a run result without updating the case spec and recording the reason.

## Case Spec Contract

Each case must use one shared `BenchmarkCaseSpec` across all lanes. The shared spec prevents direct and agent lanes from silently solving different problems.

Minimum fields:

```json
{
  "case_id": "vortex-2d",
  "suite": "pycfd-pde",
  "task_family": "pycfd_vortex",
  "description": "Isentropic vortex convection (2D Euler, unsteady)",
  "source_reference": "PyCFD vortex case: isentropic vortex advection, structured tri mesh",
  "expected_metrics": [
    "residual_l1",
    "residual_l2",
    "wall_time_seconds",
    "iterations",
    "ncells",
    "nnodes",
    "nfaces"
  ],
  "tolerance": {"residual_l1": 1e-4, "residual_l2": 1e-4},
  "problem_definition": {
    "case_type": "vortex",
    "mesh": {"mesh_type": "tri", "nx": 64, "ny": 64},
    "flow": {"M_inf": 0.3, "aoa": 0.0},
    "solver": {"CFL": 0.5, "second_order": true, "use_limiter": true},
    "timeout_seconds": 600
  }
}
```

PyCFD-specific requirements:

- `problem_definition.case_type` must map to an extension-supported PyCFD case.
- `problem_definition.mesh`, `flow`, and `solver` are the only fields the agent lane may patch.
- Dotted-path overrides from the gateway must validate against `PyCFDProblemSpec` / `PyCFDMeshSpec`.
- Unknown case types, unsupported mesh fields, or missing residual tolerances must fail preflight.

## Workflow Lanes

### Extension Lane

The extension lane is the deterministic baseline. It should not call Claude.

Real mode flow:

1. Load the shared `BenchmarkCaseSpec`.
2. Build `PyCFDProblemSpec` from `problem_definition`.
3. Probe `PyCFDEnvironmentProbeComponent` using `PYCFD_SRC_PATH` / `--pycfd-src-path`.
4. Compile with `PyCFDCompilerComponent`.
5. Execute with `PyCFDExecutorComponent`.
6. Validate with `PyCFDValidatorComponent`.
7. Build evidence with `build_evidence_bundle(...)`.
8. Write normalized `summary.json` and `attempt_log.json`.

If PyCFD is unavailable, the lane must write `status="skipped"` with a clear dependency-skip reason, not a benchmark failure.

### Direct Lane

The direct lane represents Claude CLI solving the same PyCFD task without calling the PyCFD extension API.

Real Claude + real tool flow:

1. Load the same `case_spec.json`.
2. Prompt Claude CLI to produce a standalone `solve.py` with JSON metrics on stdout.
3. Write Claude evidence: `claude_prompt.txt`, `claude_command.json`, `claude_stdout.json`, `claude_stderr.txt`, `claude_result.json`, and proposal/preflight files.
4. Validate generated script extraction before execution.
5. Execute `solve.py` in the case output directory with timeout enforcement.
6. Parse JSON metrics from stdout and write `summary.json`.
7. Record every attempt and repair in `attempt_log.json`.

Boundary rule: if the current runner uses the internal `PyCFDCompilerComponent` fallback because Claude did not provide `solve_py`, the result may count as real PyCFD execution evidence but must not count as direct-Claude code-generation success. The summary and comparison report must expose this as `direct_proposal_source="fallback_compiler"` before any direct-vs-agent claim is made.

### Agent Lane

The agent lane uses Claude CLI for proposal generation but keeps execution inside the MHE extension boundary.

Real Claude + real tool flow:

1. Load the same `case_spec.json`.
2. Prompt Claude CLI for either a full `pycfd_spec` or a constrained `spec_patch`.
3. Validate proposal structure with Pydantic preflight.
4. If preflight fails, optionally run bounded repair and preserve each proposal attempt under `proposal_attempt_<n>/`.
5. Run the final validated spec through compile → execute → validate → evidence.
6. Write proposal evidence, extension evidence, `attempt_log.json`, `validation.json`, `evidence.json`, and `summary.json`.

The agent lane may claim workflow advantages only when it improves pass rate, diagnosis, repair traceability, evidence completeness, or failure classification under comparable real-tool/real-Claude settings.

## Artifact Layout

Canonical layout:

```text
<runs-root>/pycfd-pde-benchmark/
  specs/
    vortex-2d.json
    airfoil-2d.json
    cylinder-2d.json
    mms-2d.json
    shock-diffraction-2d.json
  extension/
    <case_id>/
      case_spec.json
      environment.json
      run_plan.json
      solve.py
      stdout.txt
      stderr.txt
      run_artifact.json
      metrics.json
      validation.json
      evidence.json
      attempt_log.json
      summary.json
  direct/
    <case_id>/
      case_spec.json
      claude_prompt.txt
      claude_command.json
      claude_stdout.json
      claude_stderr.txt
      claude_result.json
      proposal_preflight.json
      solve.py
      stdout.txt
      stderr.txt
      metrics.json
      attempt_log.json
      summary.json
  agent/
    <case_id>/
      case_spec.json
      claude_prompt.txt
      claude_command.json
      claude_stdout.json
      claude_stderr.txt
      claude_result.json
      proposal_attempt_1/
      proposal_attempt_2/
      proposal_preflight.json
      pycfd_spec.json
      run_plan.json
      run_artifact.json
      validation.json
      evidence.json
      attempt_log.json
      summary.json
  comparison/
    summary_table.csv
    comparison_report.md
    result_bundle.json
    run_manifest.json
    repeat_summary.json
    approval_gate.json
  reports/
    pycfd-pde-analysis-report.md
    pycfd-pde-backlog.md
```

The final analysis report must cite these artifacts, not chat history.

## Commands

Safe dry-run across all cases and lanes:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite pycfd-pde \
  --lanes extension,direct,agent \
  --runs-root .runs/pycfd-dry

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite pycfd-pde \
  --runs-root .runs/pycfd-dry
```

Real solver baseline without real Claude variability:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite pycfd-pde \
  --lanes extension \
  --cases vortex-2d,mms-2d \
  --runs-root .runs/pycfd-real-solver \
  --allow-real-tools \
  --pycfd-src-path /home/linden/code/work/Helmholtz/git/PyCFD \
  --repeat 3

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite pycfd-pde \
  --runs-root .runs/pycfd-real-solver \
  --allow-real-tools \
  --repeat 3
```

Real Claude + real solver workflow comparison:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite pycfd-pde \
  --lanes direct,agent \
  --cases vortex-2d,mms-2d \
  --runs-root .runs/pycfd-real-claude-repeat \
  --allow-real-tools \
  --allow-real-claude \
  --pycfd-src-path /home/linden/code/work/Helmholtz/git/PyCFD \
  --claude-model cc-gpt-5.5 \
  --claude-max-turns 12 \
  --adaptive-agent \
  --max-repair-attempts 1 \
  --repeat 3

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite pycfd-pde \
  --runs-root .runs/pycfd-real-claude-repeat \
  --allow-real-tools \
  --allow-real-claude \
  --repeat 3
```

Approval check for manager-facing comparison outputs:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-approval-check \
  --suite pycfd-pde \
  --config-root .mhe \
  --strict
```

Long cases such as `airfoil-2d`, `cylinder-2d`, and `shock-diffraction-2d` should be run only after short-case real-run plumbing is stable because they can take several minutes each.

## Real-Run Phases

### Dry-Run Schema Smoke

Purpose: verify case catalog, summary schema, comparison bundle, approval-gate wiring, and report generation without real solver or real Claude.

Acceptance:

- all lanes produce summaries;
- comparison bundle exists;
- dry-run status is labeled as dry-run evidence;
- no report claims real residual convergence.

### Real Solver Baseline

Purpose: establish that the extension lane can run PyCFD with real tool execution before introducing real Claude proposal variability.

Acceptance:

- environment probe records `PYCFD_SRC_PATH` / `--pycfd-src-path`;
- executed cases write real residuals, timing, and mesh counts;
- skipped cases preserve dependency-skip reasons;
- repeat summaries compute median/min/max/IQR from real runs only;
- direct-vs-agent conclusions remain out of scope in this phase.

### Real Claude Workflow Comparison

Purpose: compare direct and agent workflows under real Claude and real PyCFD execution.

Acceptance:

- direct and agent use the same Claude binary, model, max turns, and repair budget;
- proposal failures are separated from solver failures;
- direct fallback compiler use is clearly marked and excluded from direct-Claude success claims;
- agent preflight and repair evidence is retained per attempt;
- comparator discusses success rate, repairs, diagnostics, evidence completeness, and overhead before any numerical interpretation.

### Full Catalog Confirmation

Purpose: repeat all five PyCFD cases after the short-case workflow is stable.

Acceptance:

- all five cases are attempted or dependency-skipped with explicit reasons;
- long-case wall time is reported as observed timing, not performance superiority;
- shock/limiter requirements remain documented as solver constraints;
- final report separates current-catalog evidence from future case-family capability.

## Comparator Design

The comparator reads normalized `LaneSummary` outputs from all lanes and writes:

```text
comparison/summary_table.csv
comparison/comparison_report.md
comparison/result_bundle.json
comparison/run_manifest.json
comparison/approval_gate.json
```

Recommended summary table columns:

```text
case_id,task_family,extension_status,direct_status,agent_status,extension_passed,direct_passed,agent_passed,extension_residual_l1,direct_residual_l1,agent_residual_l1,extension_residual_l2,direct_residual_l2,agent_residual_l2,direct_attempts,agent_attempts,direct_repairs,agent_repairs,direct_llm_calls,agent_llm_calls,direct_preflight_status,agent_preflight_status,direct_failure_category,agent_failure_category,direct_proposal_source,agent_repair_outcome,extension_driver_time,direct_driver_time,agent_driver_time,extension_evidence_count,direct_evidence_count,agent_evidence_count,verdict
```

Recommended verdicts:

| Verdict | Meaning |
|---|---|
| `all_passed_real_solver` | All requested lanes executed real PyCFD and passed residual tolerances. |
| `agent_more_evidence` | Direct and agent both pass, but agent has stronger validation/evidence/provenance. |
| `direct_lighter` | Direct and agent both pass, direct is simpler/faster, and evidence gaps do not block reproduction. |
| `agent_recovered_direct_failed` | Direct proposal or execution failed; agent repaired or constrained the task and passed. |
| `direct_passed_agent_failed` | Direct passed but agent failed; treat as extension/agent gap. |
| `proposal_failure` | Claude proposal did not satisfy direct/agent preflight. |
| `solver_failure` | Proposal was valid but PyCFD execution failed. |
| `dependency_skip` | PyCFD source path or required case asset is unavailable. |
| `dry_run_only` | The run validated benchmark plumbing only. |

Comparator reports must never compare PyCFD residuals against Nektar L2/Linf or Fealpy FEM error norms as if they were the same scientific metric.

## Approval and Claim Gates

Manager-facing reports must include approval state from:

```text
.mhe/benchmarks/pycfd-approval.json
.mhe/benchmarks/comparison-approval.json
.mhe/approvals/pycfd_pde_benchmark_approval.json
```

Supported limited claims after current approval:

- PyCFD comparison benchmark outputs are governed by a suite-level approval profile.
- Workflow/reporting claims may be promoted with explicit limitations.
- Evidence bundles and direct-lane code review are referenced for auditability.

Blocked stronger claims until additional evidence exists:

- numerical solver superiority;
- runtime superiority;
- direct-vs-agent superiority without real Claude + real solver repeated evidence;
- CFD solver accuracy beyond reviewed residual/tolerance evidence;
- new case-family capability beyond current 2D Euler catalog.

## Analysis Report Requirements

Final reports should be written under:

```text
<runs-root>/pycfd-pde-benchmark/reports/pycfd-pde-analysis-report.md
<runs-root>/pycfd-pde-benchmark/reports/pycfd-pde-backlog.md
```

The analysis report must include:

- executive summary with one evidence-backed conclusion;
- run environment and `PYCFD_SRC_PATH` provenance;
- case/lane status table;
- residual and mesh metric table;
- proposal/preflight/repair taxonomy;
- evidence completeness table;
- repeated-run timing table when `--repeat` is used;
- approval status and excluded claims;
- backlog items tied to artifact paths.

Backlog format:

```markdown
| ID | Area | Symptom | Evidence | Suggested fix | Priority |
|---|---|---|---|---|---|
| PYCFD-BENCH-001 | direct-lane-preflight | Direct used fallback compiler, so direct Claude success is not proven | direct/<case_id>/proposal_preflight.json | record proposal_source and tighten solve.py extraction prompt | P1 |
```

## Fairness Constraints

- Every lane uses the same `BenchmarkCaseSpec`.
- Real solver runs use the same PyCFD source tree and Python environment.
- Direct and agent lanes use the same Claude binary, model, max-turn budget, and permission mode.
- Direct lane must not call `metaharness_ext.pycfd` unless the fallback is explicitly labeled and excluded from direct-Claude success claims.
- Agent lane must not bypass compile → execute → validate → evidence.
- All failed attempts must be recorded in `attempt_log.json`.
- Timing must separate solver time, driver time, Claude time, and harness overhead where available.
- Reports must distinguish workflow evidence from numerical solving evidence.

## Acceptance Criteria

The design is implemented only when:

- `benchmark-run --suite pycfd-pde` supports dry-run and real-tool modes for all five cases;
- at least two short cases have repeated real extension-lane baseline evidence before real Claude comparison;
- all five cases are attempted in a full-catalog run or explicitly dependency-skipped;
- direct and agent lanes preserve Claude prompt/command/stdout/stderr/result/proposal evidence;
- preflight status, failure category, repair outcome, and attempt counts are visible in summaries and comparison bundles;
- `comparison/result_bundle.json`, `comparison/run_manifest.json`, `comparison/summary_table.csv`, and `comparison/comparison_report.md` exist;
- approval status and excluded claims are embedded in comparison outputs;
- final reports cite artifact paths and avoid numerical superiority claims.

## Recommended Implementation Slices

| Slice | Goal | Output | Priority |
|---|---|---|---|
| PyCFD dry-run parity smoke | Confirm schema/comparator/report wiring | `.runs/pycfd-dry/pycfd-pde-benchmark/comparison/result_bundle.json` | P0 |
| Short real extension baseline | Establish real PyCFD residual evidence without Claude variability | `.runs/pycfd-real-solver/pycfd-pde-benchmark/comparison/repeat_summary.json` | P0 |
| Direct proposal-source audit | Ensure fallback compiler is visible in summaries | `proposal_source` / equivalent evidence field | P1 |
| Real Claude short-case comparison | Compare direct vs agent workflow under real PyCFD | `.runs/pycfd-real-claude-repeat/.../result_bundle.json` | P1 |
| Full five-case repeated run | Confirm current PyCFD catalog coverage | full-catalog comparison bundle and report | P2 |
| Cross-extension parity report | Compare evidence maturity with Fealpy/Nektar without metric category errors | updated cross-extension analysis | P2 |

## Manager-Facing Summary Template

Safe summary after a successful real PyCFD comparison run:

> PyCFD now has a comparison benchmark protocol that separates deterministic extension execution, direct Claude-generated scripts, and MHE agent-mediated proposals. Real PyCFD residual and timing evidence can support current-catalog execution claims, while direct-vs-agent workflow claims require repeated real Claude runs and must exclude fallback-compiler cases from direct-Claude success counts.

Avoid saying:

- “PyCFD is more accurate than Nektar/Fealpy.”
- “MHE improves CFD solver accuracy.”
- “Direct Claude failed” when the recorded issue was a dependency skip, proposal preflight failure, or fallback-compiler substitution.
- “All PyCFD case families are supported” when only the current 2D Euler catalog is benchmarked.
