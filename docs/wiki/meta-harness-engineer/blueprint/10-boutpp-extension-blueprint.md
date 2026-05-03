# BOUT++ Extension Blueprint

> Status: implemented baseline
> Scope: `metaharness_ext.boutpp`, focused tests, manifests, and opt-in real BOUT++ smoke coverage.
> Primary reference corpus: `/home/linden/code/git/Aeloon/Aeloon-science-agent/MHE/docs/Tutorial/bout_docs/user_docs/`.
> Additional source reference: `/home/linden/code/work/Solvers/Nektar/BOUT-dev`.

## Purpose

The BOUT++ extension integrates BOUT++ as a controlled, typed, auditable MHE solver backend. It follows the Nektar extension pattern, but maps the execution surface to BOUT++ concepts documented in the tutorial corpus: example build targets, `BOUT.inp`, optional NetCDF grid files, MPI execution, restart/output artifacts, stop-file control, post-processing through xBOUT / `boutdata` / optional `boutpp`, and validation from collected evidence.

The first supported slice is intentionally limited. It is not a full BOUT++ case-authoring system and does not generate arbitrary `PhysicsModel` C++ sources. It orchestrates existing compiled BOUT++ examples or user-provided executables with typed option-file generation, run planning, execution evidence, postprocess summaries, and validation.

## Design Principles

- Use typed contracts as the stable control surface.
- Keep BOUT++ source and compiled model code outside MHE ownership.
- Treat `BOUT.inp`, command-line overrides, grid refs, logs, settings, dumps, and restart files as the primary evidence surface.
- Keep extraction close to executor/postprocess stages and keep judgement in validator/policy layers.
- Gate real BOUT++ execution behind explicit environment availability and opt-in tests.
- Avoid claims of full physics coverage until real example families are covered by executable evidence.

## Extension Chain

```text
BoutPPGateway
  -> BoutPPEnvironmentProbe
    -> BoutPPCompiler
      -> BoutPPExecutor
        -> BoutPPPostprocess
          -> BoutPPValidator
            -> BoutPPEvidencePolicy
```

Optional study layer:

```text
BoutPPStudyComponent
  -> mutate typed spec fields
    -> compile / execute / postprocess / validate each trial
      -> compare requested metric
```

## Contract Model

### `BoutPPProblemSpec`

The problem spec describes a run request, not arbitrary C++ model generation.

Core fields:

- `task_id`: stable simple identifier.
- `case_name`: human-readable BOUT++ case label.
- `executable`: compiled BOUT++ model binary, such as `conduction`.
- `source_case_dir`: optional upstream example or model directory.
- `data_dir`: runtime data directory, default `data`.
- `grid_file`: optional NetCDF grid file ref.
- `options`: typed nested option sections rendered to `BOUT.inp`.
- `cli_overrides`: BOUT++ command-line options such as `solver:type=rk4`.
- `mpi`: process count and launcher settings.
- `restart`: restart/append mode.
- `output`: expected file prefixes and formats.
- `validation`: metric expectations and required artifacts.
- `timeout_seconds`, metadata, evidence refs, promotion metadata.

### `BoutPPRunPlan`

The run plan is execution-grade:

- deterministic `plan_id` from the spec.
- materialized `BOUT.inp` content.
- resolved command argv.
- workspace/run directories.
- expected logs, dump files, restart files, settings file.
- sandbox and binary requirements.

### `BoutPPRunArtifact`

The artifact records what happened:

- execution status and return code.
- stdout/stderr/log excerpts.
- paths to `BOUT.log.*`, `BOUT.settings`, `BOUT.dmp.*`, `BOUT.restart.*`.
- extracted runtime metadata and summary metrics.
- missing artifacts and warnings.

### `BoutPPPostprocessReport`

The postprocess report extracts evidence without deciding promotion:

- available variable names if NetCDF readers are present.
- output file counts.
- settings/options summary.
- timestep/runtime metrics parsed from logs.
- optional xBOUT/boutdata availability notes.

### `BoutPPValidationReport`

Validation consumes run and postprocess evidence:

- environment unavailable.
- runtime failed or timed out.
- required artifact missing.
- required variable missing.
- metric threshold exceeded.
- validation passed.

## Capabilities and Slots

Suggested capabilities:

- `boutpp.environment.probe`
- `boutpp.options.compile`
- `boutpp.mpi.execute`
- `boutpp.restart.execute`
- `boutpp.output.postprocess`
- `boutpp.validation.basic`
- `boutpp.evidence.bundle`
- `boutpp.policy.evaluate`
- `boutpp.study.sweep`

Suggested slots:

- `boutpp_gateway.primary`
- `boutpp_environment.primary`
- `boutpp_compiler.primary`
- `boutpp_executor.primary`
- `boutpp_postprocess.primary`
- `boutpp_validator.primary`
- `boutpp_evidence_policy.primary`
- `boutpp_study.primary`

Protected slots:

- `boutpp_validator.primary`
- `boutpp_evidence_policy.primary`

## Environment Surface

The environment probe should detect:

- `BOUTPP_ROOT` or constructor-provided source/build root.
- `cmake`, `mpiexec`/`mpirun`, and `ncxx4-config` or `nc-config`.
- optional `python`, `netCDF4`, `xarray`, `xbout`, `boutdata`, and `boutpp` readers.
- whether BOUT++ was configured with `BOUT_ENABLE_PYTHON=ON` when a Python module path is exposed.
- example executables under common build paths such as `build/examples/<case>/<binary>`.
- compile-time feature hints from BOUT++ configuration artifacts when available, including PETSc, SUNDIALS, OpenMP, GPU/RAJA, and 3D metric support.
- stop-file support, `BOUT.stop`, `bout-stop-script`, restart/append flags, `restart=true`, `append=true`, `dump_on_restart`, and restart-file naming conventions as runtime evidence targets.

Missing optional postprocess tools should not block basic execution. Missing executable, MPI launcher, or required data directory should block real execution promotion.

## Compiler Semantics

The compiler renders a BOUT++ option file from nested typed sections:

```ini
[solver]
type = rk4
atol = 1e-10
rtol = 1e-8

[mesh]
nx = 16
ny = 8
```

It must preserve BOUT++ semantics:

- INI-like sections and `section:subsection` names.
- string, bool, int, float, and expression values.
- CLI overrides without spaces around `=`.
- restart/append tokens after the executable.
- custom `-d <data_dir>` support.

## Execution Semantics

The executor materializes the run under `.runs/boutpp/<run_id>` by default, copies or writes the data directory, writes `BOUT.inp`, then launches:

```text
<mpi_launcher> -np <processes> <executable> [restart] [append] -d <data_dir> <cli_overrides...>
```

For non-MPI single-process runs, it may execute the binary directly when `processes == 1` and no launcher is configured.

The executor should preserve partial evidence on failure and classify missing prerequisites as `unavailable`, not as solver failure.

## Postprocess Semantics

Postprocess starts with filesystem evidence and only uses Python readers if available. Minimum supported summaries:

- discovered log/settings/dump/restart files.
- parsed run-finished and runtime lines from logs.
- parsed settings file presence and selected option keys.
- discovered NetCDF variable names when `netCDF4` is installed.

Future phases may add xBOUT-derived dataset summaries, reduced diagnostics, plots, and convergence traces.

## Validation Semantics

Initial validation is artifact-oriented:

- return code must be zero.
- required logs and `BOUT.settings` must exist if configured.
- dump/restart requirements are checked according to spec.
- required variables are checked only when NetCDF variable extraction is available.
- threshold metrics are checked from postprocess summaries.

The validator should not reinterpret physics equations or assert numerical correctness beyond available evidence.

## Study Semantics

The first study component should support Cartesian sweeps over dotted spec paths, such as:

- `options.solver.type`
- `options.solver.atol`
- `options.solver.rtol`
- `mpi.processes`
- `options.mesh.nx`
- `options.mesh.ny`

It should return trial-level plan/artifact/postprocess/validation refs and recommend the best passing trial by a requested metric.

## Testing Strategy

Focused tests should cover:

- contract validation and deterministic plan IDs.
- option rendering and command construction.
- environment probe with patched filesystem/tool availability.
- executor success/failure/timeout/unavailable paths with mocked subprocesses.
- postprocess file discovery and log/settings parsing.
- validator statuses and policy gates.
- study mutation and trial aggregation.
- manifest importability, slots, capabilities, and protected slot declarations.

Real BOUT++ smoke tests must stay opt-in, for example `MHE_RUN_REAL_BOUTPP=1`, and should use a small compiled example such as `conduction` only when available.

## Claim Boundaries

This blueprint supports the claim that MHE can orchestrate typed BOUT++ runs and evaluate filesystem/log/output evidence. It does not support claims that MHE can synthesize arbitrary BOUT++ physics models, verify all plasma-fluid physics, or replace BOUT++ native testing infrastructure.
