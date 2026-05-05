# MOOSE Usage Validation Method

> 版本：v0.1 | 状态：dry-run comparison implemented; opt-in real extension smoke gated by local `moose_test-opt`.

## Purpose

This page defines the first MOOSE comparison benchmark for `metaharness_ext.moose`. It compares three workflow lanes for a narrow INL MOOSE test-app case:

- `extension`: typed `MooseProblemSpec` compiled through the MHE MOOSE compiler/executor/validator/evidence path;
- `direct`: direct Claude proposal lane with the same proposal contract and no silent repair unless the case explicitly allows fallback evidence;
- `agent`: agent-assisted lane that may repair malformed proposals from deterministic case defaults and records the repair as workflow evidence.

The goal is workflow validation, not solver ranking. The suite proves whether MHE can make MOOSE input handling, environment gating, evidence identity, repair outcomes, and comparison bundles auditable.

## Claim Boundary

Allowed claims after the dry-run comparison:

- MOOSE benchmark cases can be represented as structured benchmark specs and lane summaries;
- extension dry-run evidence can materialize `MooseProblemSpec`, `MooseRunPlan`, and `MooseEvidenceBundle` artifacts;
- malformed proposal contrast can make direct failure and agent repair evidence comparator-visible;
- comparison output can report `proposal_contract_status`, `repair_outcome`, `repair_count`, and `repair_advantage`.

Allowed claims after an opt-in real extension smoke:

- a local built MOOSE test application can be driven through the MHE MOOSE extension for the selected simple diffusion case;
- the extension can discover the expected Exodus output, validate evidence, and produce an `allow` policy decision for that local case.

Excluded claims:

- no MOOSE numerical accuracy, convergence, or runtime superiority claim;
- no claim that `moose-opt` is system-installed;
- no broad MOOSE app coverage claim beyond the local `test/moose_test-opt` case;
- no direct-vs-agent real-tool superiority claim until direct and agent real MOOSE CLI lanes are implemented and repeated.

## Case Catalog

| Case | Purpose | Default mode | Evidence meaning |
|---|---|---|---|
| `simple-diffusion-hit` | HIT input workflow for the MOOSE simple diffusion test case | dry-run all lanes; opt-in real extension lane | structured spec/plan/evidence, and real local output discovery when enabled |
| `malformed-hit-proposal` | proposal-contract contrast | dry-run all lanes | direct lane fails malformed proposal, agent lane records deterministic repair |

Source anchors:

```text
MOOSE source root: /home/linden/code/work/Solvers/FEM/moose
Local test app:    /home/linden/code/work/Solvers/FEM/moose/test/moose_test-opt
Reference input:   /home/linden/code/work/Solvers/FEM/moose/test/tests/kernels/simple_diffusion/simple_diffusion.i
```

The source-truth boundary is the INL MOOSE source tree and test input, not the unrelated biological MOOSE manual found under local `docs/moose-docs`.

## Lane Protocol

The default dry-run command is:

```bash
PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite moose-usage \
  --lanes extension,direct,agent \
  --runs-root .runs/moose-usage-validation

PYTHONPATH=src python -m metaharness.cli benchmark-compare \
  --suite moose-usage \
  --runs-root .runs/moose-usage-validation
```

The opt-in real extension smoke command is:

```bash
unset PETSC_ARCH
export MHE_MOOSE_BINARY=/home/linden/code/work/Solvers/FEM/moose/test/moose_test-opt
export PETSC_DIR=/usr/lib64/petscdir
export LIBMESH_DIR=/home/linden/code/work/Solvers/FEM/moose/libmesh/installed
export WASP_DIR=/home/linden/code/work/Solvers/FEM/moose/wasp_conda_install
export PKG_CONFIG_PATH=/usr/lib64/pkgconfig:${PKG_CONFIG_PATH}

PYTHONPATH=src python -m metaharness.cli benchmark-run \
  --suite moose-usage \
  --lanes extension \
  --cases simple-diffusion-hit \
  --runs-root .runs/moose-real-tool-benchmark \
  --allow-real-tools
```

Direct and agent real MOOSE CLI lanes are intentionally skipped in this first slice. They need a separate safe direct-run contract so benchmark reports do not confuse extension real execution with direct-Claude solver quality.

## Artifact Layout

Default run root:

```text
.runs/moose-usage-validation/moose-usage-benchmark/
```

Important artifacts:

```text
extension/<case>/moose_problem_spec.json
extension/<case>/moose_run_plan.json
extension/<case>/moose_evidence_bundle.json
direct/<case>/moose_proposal_contract.json
agent/<case>/moose_proposal_contract.json
comparison/result_bundle.json
comparison/summary_table.csv
comparison/comparison_report.md
reports/moose-usage-analysis-report.md
reports/moose-usage-backlog.md
```

For real extension smoke, the extension lane also writes:

```text
moose_environment_report.json
moose_run_artifact.json
moose_validation_report.json
moose_policy_report.json
workspace/input_out.e
workspace/stdout.log
workspace/stderr.log
```

## Acceptance Criteria

The first slice is complete when:

- `benchmark-run --suite moose-usage` supports dry-run extension/direct/agent lanes;
- `malformed-hit-proposal` produces direct failed / agent passed with `repair_advantage = agent_repaired_direct_failure` in comparison evidence;
- real extension smoke skips truthfully when the local MOOSE binary is missing;
- real extension smoke can pass locally when `MHE_MOOSE_BINARY` and dependency environment variables point to the built test app;
- docs and central comparison conclusions retain numerical and performance non-claims.

## Next Evidence Needed

- Implement safe real direct and agent MOOSE CLI lanes with proposal preflight and workspace isolation.
- Add repeated real extension smoke for `simple-diffusion-hit`.
- Parse MOOSE solver logs for domain-specific convergence/residual evidence before any scientific claim.
- Add more MOOSE app/input families only after each has source-truth anchors and stable expected outputs.
