# BOUT++ Extension Roadmap

> Status: baseline implemented; roadmap continues
> Scope: staged delivery path for the MHE BOUT++ extension.

## Current Baseline

No BOUT++ extension exists under `MHE/src/metaharness_ext/boutpp` at roadmap start. The closest implemented classical solver precedent is `metaharness_ext.nektar`, with PyCFD providing the most complete modern extension pattern for environment, evidence, policy, study, governance, and handoff structure.

The primary BOUT++ planning reference is the in-repo tutorial corpus under `docs/Tutorial/bout_docs/user_docs/`, with source examples and current implementation details cross-checked against `/home/linden/code/work/Solvers/Nektar/BOUT-dev/examples/`.

## Design and Claim Boundary

Goal: define a truthful BOUT++ extension scope.

Deliverables:

- extension blueprint.
- implementation plan.
- roadmap.
- claim boundaries and non-goals.

Exit criteria:

- documents distinguish orchestration of existing BOUT++ executables from C++ model generation.
- documents state that real BOUT++ execution remains opt-in and environment-gated.

## Typed Surface

Goal: establish the extension's stable contract, capability, and slot surface.

Deliverables:

- `types.py`, `contracts.py`, `slots.py`, `capabilities.py`, `__init__.py`.
- contract tests.

Exit criteria:

- default specs serialize cleanly.
- invalid unsafe identifiers and impossible run settings are rejected.
- protected slots are declared for validation and policy.

## Intake and Environment

Goal: detect whether a host can run or postprocess BOUT++ jobs.

Deliverables:

- gateway component.
- environment probe component.
- environment tests.

Exit criteria:

- probe reports BOUT++ root/build root, launcher, CMake, NetCDF config, `bout-config`, executable availability, and optional Python readers.
- missing optional postprocess tools produce warnings, not hard failure.
- missing executable or required launcher blocks real execution promotion.

## Compilation to Runtime Plan

Goal: convert a typed BOUT++ run request into materialized inputs and command metadata.

Deliverables:

- compiler component.
- option-file renderer.
- deterministic plan ID.
- compiler tests.

Exit criteria:

- BOUT++ INI sections render deterministically and preserve documented example workflow option patterns.
- MPI/direct command construction is tested.
- restart/append and `-d data_dir` are represented in the plan.

## Execution Evidence

Goal: run a plan or classify why it cannot run while preserving partial evidence.

Deliverables:

- executor component.
- artifact discovery.
- executor tests with mocked subprocesses.

Exit criteria:

- success, nonzero exit, timeout, missing executable, and missing expected artifacts are distinguishable.
- stdout/stderr/log excerpts are preserved.
- run artifacts contain discovered `BOUT.log.*`, `BOUT.settings`, dump, and restart paths.

## Postprocess and Validation

Goal: turn run outputs into structured evidence and validation decisions.

Deliverables:

- postprocess component.
- validator component.
- evidence bundle builder.
- evidence policy.
- tests for all validation/policy states.

Exit criteria:

- artifact-oriented validation works without optional NetCDF readers.
- NetCDF variable checks run when the reader is available.
- policy gates evaluate non-short-circuit and return allow/defer/reject.

## Study and Governance

Goal: support reproducible parameter sweeps and bridge validation to MHE governance.

Deliverables:

- study component.
- governance adapter.
- study/governance tests.

Exit criteria:

- dotted-path mutations support option, MPI, restart, and validation fields.
- study reports trial refs and best passing trial.
- governance adapter can build core validation and candidate records from BOUT++ evidence.

## Manifests and Focused Verification

Goal: make the extension discoverable and regression-tested.

Deliverables:

- manifests under `examples/manifests/boutpp/`.
- manifest tests.
- focused verification command output.

Exit criteria:

- all focused BOUT++ tests pass.
- `ruff check` passes for new BOUT++ files and tests.
- docs remain aligned with the implemented scope.

## Optional Real Smoke Evidence

Goal: prove the typed pipeline against a local compiled BOUT++ example when available.

Deliverables:

- opt-in smoke test, if added.
- small `conduction` example run evidence, only when `MHE_RUN_REAL_BOUTPP=1` and the binary exists.

Exit criteria:

- smoke test skips cleanly without a local build.
- no default CI path requires BOUT++ binaries.

## Next Evidence Roadmap

The CI/CD benchmark integration made the remaining evidence gaps concrete. Treat the next work as evidence production, not as a claim of solver superiority.

| Priority | Evidence slice | Implementation target | Acceptance evidence | Claim boundary |
|---|---|---|---|---|
| High | Proposal contract visibility | Replace dry-run `not_checked` BOUT++ direct/agent proposal status with deterministic contract artifacts derived from case defaults when fake Claude is used | `result_bundle.json` shows `proposal_contract_status = valid` and comparator-visible proposal sources | Workflow contract evidence only; not real Claude quality |
| High | Repeated real-smoke promotion | Surface retained `boutpp_real_repeated_smoke_summary.json` through comparator-visible promotion or capability rows | Comparison bundle links the repeated real-smoke root and preserves skip reasons for non-promoted cases | Case-scoped local executable integration only |
| Medium | Domain artifact metrics | Add optional NetCDF variable discovery and validation when `netCDF4` or another reader is available | Validation report records variable presence and reader availability | Artifact/domain evidence only; no convergence claim without reference metrics |
| Medium | Real direct/agent prompt evidence | Run gated real-Claude direct/agent comparison after contract evidence is stable | Proposal validity rate, preflight status, failure categories, and retained prompts are visible | Proposal/workflow quality only unless real tools also run |
| Later | Broader BOUT++ examples | Promote additional examples only after stable executable, input directory, and output contract are known | Capability-gated skips become passing real-smoke cases with retained artifacts | No broad solver-family claim from one example |

## Future Work

Keep these items outside the accepted baseline and treat them as roadmap backlog rather than acceptance debt:

- comparator-visible repeated real BOUT++ smoke promotion rows.
- richer postprocess and evidence examples, including expanded xBOUT/boutdata notes.
- real-Claude benchmark comparison coverage with explicit proposal contracts and failure classification.
- solver-specific manifest examples for additional BOUT++ cases and variants.
