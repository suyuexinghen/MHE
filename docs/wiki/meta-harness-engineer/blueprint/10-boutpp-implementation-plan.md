# BOUT++ Extension Implementation Plan

> Status: implemented baseline
> Scope: first complete implementation slice for `metaharness_ext.boutpp`.
> Acceptance: focused tests and ruff pass without requiring a local BOUT++ build.

## Implementation Objective

Implement a complete, mock-testable BOUT++ MHE extension that can compile typed run specs into BOUT++ data directories and commands, execute or classify unavailable runs, postprocess filesystem/log/NetCDF evidence, validate artifacts, assemble evidence bundles, evaluate policy gates, support parameter studies, and expose manifests.

## In-Scope Files

Production package:

```text
src/metaharness_ext/boutpp/
  __init__.py
  types.py
  slots.py
  capabilities.py
  contracts.py
  gateway.py
  environment.py
  compiler.py
  executor.py
  postprocess.py
  validator.py
  evidence.py
  policy.py
  study.py
  governance.py
```

Manifests:

```text
examples/manifests/boutpp/boutpp_gateway.json
examples/manifests/boutpp/boutpp_environment.json
examples/manifests/boutpp/boutpp_compiler.json
examples/manifests/boutpp/boutpp_executor.json
examples/manifests/boutpp/boutpp_postprocess.json
examples/manifests/boutpp/boutpp_validator.json
examples/manifests/boutpp/boutpp_policy.json
examples/manifests/boutpp/boutpp_study.json
```

Tests:

```text
tests/test_metaharness_boutpp_contracts.py
tests/test_metaharness_boutpp_environment.py
tests/test_metaharness_boutpp_compiler.py
tests/test_metaharness_boutpp_executor.py
tests/test_metaharness_boutpp_postprocess.py
tests/test_metaharness_boutpp_validator_policy.py
tests/test_metaharness_boutpp_study.py
tests/test_metaharness_boutpp_manifest.py
tests/test_metaharness_boutpp_benchmark_runner.py
```

## Contracts and Public Surface

Implement:

- literal/enumerated type aliases for statuses, restart modes, launcher modes, validation states, and policy decisions.
- `BoutPPOptionValue`, `BoutPPOptions`, `BoutPPMpiSpec`, `BoutPPRestartSpec`, `BoutPPOutputSpec`, `BoutPPValidationSpec`.
- `BoutPPProblemSpec`, `BoutPPEnvironmentReport`, `BoutPPRunPlan`, `BoutPPRunArtifact`, `BoutPPPostprocessReport`, `BoutPPValidationReport`.
- evidence, policy, and study models.
- slot and capability constants.
- package exports.

Acceptance:

- invalid task IDs, process counts, empty executable paths, invalid timeout, and empty study paths are rejected.
- default problem specs can be serialized and used to build deterministic plan IDs.

## Gateway and Environment Probe

Implement:

- gateway intake from a dictionary or `BoutPPProblemSpec`.
- environment probe resolving `BOUTPP_ROOT`, optional build root, MPI launcher, CMake, `ncxx4-config` or `nc-config`, `bout-config`, and Python postprocess libraries.
- executable discovery under common build paths.
- non-blocking optional dependency warnings.

Acceptance:

- tests cover ready, missing root, missing executable, missing launcher, and optional postprocess availability.
- missing optional Python readers does not block basic readiness.
- `boutpp` Python module availability is recorded when the BOUT++ build exposes it.
- usage-validation benchmark coverage compares the extension baseline against direct CLI/manual and agent-assisted workflows without requiring a local BOUT++ build.

## Compiler

Implement:

- deterministic `plan_id` from stable spec JSON excluding promotion/runtime metadata.
- BOUT++ `BOUT.inp` renderer for nested sections.
- value formatting for bools, strings, numbers, and expression-like strings.
- command argv construction for direct and MPI execution.
- restart/append and `-d <data_dir>` support.
- expected artifact path declaration.

Acceptance:

- tests lock option rendering for nested sections, CLI override ordering, direct/MPI command construction, and data directory naming.

## Executor

Implement:

- workspace creation under `.runs/boutpp` by default.
- safe `run_id` and path handling.
- `BOUT.inp` materialization into the runtime data directory.
- optional copying of existing data-directory contents.
- subprocess execution with timeout and stdout/stderr capture.
- artifact discovery for logs, settings, dumps, and restart files.
- graceful `unavailable`, `timeout`, and `failed` artifact statuses.

Acceptance:

- mocked subprocess tests cover success, nonzero exit, timeout, missing executable, and artifact discovery.

## Postprocess, Validator, Evidence, and Policy

Implement:

- postprocess file discovery and log/settings parsing.
- optional NetCDF variable listing when `netCDF4` is importable.
- parse run-finished, runtime, and step-summary text from logs.
- treat xBOUT / `boutdata` / `boutpp` as optional readers, not hard dependencies.
- validator statuses for unavailable, runtime failure, missing artifacts, missing variables, metric threshold failure, and passed.
- evidence bundle refs and warnings.
- non-short-circuit evidence policy gates.

Acceptance:

- tests cover every validator status and policy allow/defer/reject outcomes.
- evidence refs are stable and deduplicated.

## Study and Governance

Implement:

- Cartesian sweep over dotted spec paths.
- trial-level compile/execute/postprocess/validate flow.
- best-trial selection by minimize/maximize objective.
- governance adapter comparable to other extension adapters.

Acceptance:

- tests cover snapshot generation, nested mutation, failed trial capture, and report recommendations.

## Manifests and Documentation Sync

Implement:

- component manifests with declared contracts, capabilities, sandbox tiers, and required binaries.
- manifest tests for importability and slot/capability alignment.
- update this plan, roadmap, and blueprint if implementation scope changes.

Acceptance:

- focused BOUT++ tests pass.
- `ruff check` passes for new files.
- docs do not claim real BOUT++ execution unless opt-in smoke evidence exists.

## Out-of-Scope for This Slice

- generating arbitrary C++ `PhysicsModel` files.
- building BOUT++ from source.
- orchestrating upstream BOUT++ native test suites such as unit, integrated, and MMS tests.
- scheduler submission for HPC clusters.
- real xBOUT plots or visual diagnostics.
- replacing upstream BOUT++ integrated tests.

## Verification Commands

```bash
PYTHONPATH=src python -m pytest tests/test_metaharness_boutpp_*.py -q
ruff check src/metaharness_ext/boutpp tests/test_metaharness_boutpp_*.py
```

Optional real smoke command, only when the local BOUT++ example is built:

```bash
MHE_RUN_REAL_BOUTPP=1 PYTHONPATH=src python -m pytest tests/test_metaharness_boutpp_smoke.py -q
```
