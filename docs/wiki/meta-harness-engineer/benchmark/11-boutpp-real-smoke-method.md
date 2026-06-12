# BOUT++ Real Smoke Method

> 版本：v0.4 | 状态：local opt-in repeated smoke implemented with comparator-visible promotion rows and `T` NetCDF domain validation | 面向 `metaharness_ext.boutpp` 的真实 BOUT++ smoke evidence 升级路径。

## Purpose

This page documents how to use the local BOUT++ build at `/home/linden/code/work/Solvers/FEM/BOUT-dev/build` to test the MHE BOUT++ extension against a real executable. It extends the dry-run usage-validation method in `09-boutpp-usage-validation-method.md` without changing the default CI boundary.

The goal is narrow: prove that the implemented extension pipeline can compile a typed BOUT++ request, launch a local built example when explicitly enabled, discover runtime artifacts, and validate the resulting evidence.

## Claim Boundary

Allowed claims after a passing local smoke:

- the local BOUT++ `conduction` executable can be driven through an opt-in MHE smoke path;
- `metaharness_ext.boutpp` can materialize `BOUT.inp`, command metadata, runtime workspace, and artifact evidence for that local case;
- logs/settings/dump/restart discovery works for the tested local build and example.

Excluded claims:

- no broad BOUT++ solver support claim;
- no numerical accuracy, convergence, or runtime superiority claim;
- no default CI requirement for BOUT++ binaries;
- no Python `boutpp` module support claim from this build, because the local CMake cache indicates Python support is disabled.

## Local Build Facts

Observed local paths:

```text
BOUT++ source root: /home/linden/code/work/Solvers/FEM/BOUT-dev
BOUT++ build root:  /home/linden/code/work/Solvers/FEM/BOUT-dev/build
conduction binary:  /home/linden/code/work/Solvers/FEM/BOUT-dev/build/examples/conduction/conduction
conduction data:    /home/linden/code/work/Solvers/FEM/BOUT-dev/build/examples/conduction/data
bout-config:        /home/linden/code/work/Solvers/FEM/BOUT-dev/build/bin/bout-config
```

The safest first case is the built `examples/conduction` executable. It is already the smallest BOUT++ tutorial-style example used by the current MHE BOUT++ usage-validation slice, and the local build tree contains prior successful artifacts under the example `data` directory.

## Direct BOUT++ Sanity Command

Use this command only as a direct local sanity check. It runs BOUT++ outside MHE and may overwrite files in the example `data` directory.

```bash
/usr/bin/mpiexec -n 2 /home/linden/code/work/Solvers/FEM/BOUT-dev/build/examples/conduction/conduction -d /home/linden/code/work/Solvers/FEM/BOUT-dev/build/examples/conduction/data
```

Expected artifacts in the data directory:

```text
BOUT.log.0
BOUT.log.1
BOUT.settings
BOUT.dmp.0.nc
BOUT.dmp.1.nc
BOUT.restart.0.nc
BOUT.restart.1.nc
```

A passing direct sanity run is not yet an MHE extension test. It only proves the local executable and example data directory are usable.

## MHE Environment Setup

Use explicit environment variables so the extension probe and executor can find the local build.

```bash
export BOUT_ROOT=/home/linden/code/work/Solvers/FEM/BOUT-dev
export BOUTPP_ROOT=/home/linden/code/work/Solvers/FEM/BOUT-dev/build
export PATH=/home/linden/code/work/Solvers/FEM/BOUT-dev/build/bin:$PATH
```

The current probe records:

- `BOUTPP_ROOT` or `BOUT_ROOT` availability;
- MPI launcher availability from `mpiexec` or `mpirun`;
- `cmake`, `ncxx4-config` or `nc-config`, and `bout-config`;
- optional Python readers: `netCDF4`, `xarray`, `xbout`, `boutdata`, and `boutpp`;
- executable availability for the requested `BoutPPProblemSpec`.

Missing optional Python readers should warn but not block artifact-oriented smoke validation. Promoted cases that opt into NetCDF domain requirements are stricter: missing `netCDF4` blocks promotion because the requested variable/dimension checks cannot be evaluated.

## MHE Smoke Spec Shape

The real smoke should use a typed `BoutPPProblemSpec` that points to the compiled binary and copies the example data directory into an MHE-owned run workspace.

Key fields:

```python
from metaharness_ext.boutpp import (
    BoutPPCompilerComponent,
    BoutPPExecutorComponent,
    BoutPPGatewayComponent,
    BoutPPMpiSpec,
    BoutPPOutputSpec,
    BoutPPProblemSpec,
    BoutPPValidatorComponent,
)

build_root = "/home/linden/code/work/Solvers/FEM/BOUT-dev/build"
case_dir = f"{build_root}/examples/conduction"

spec = BoutPPProblemSpec(
    task_id="boutpp_real_conduction_smoke",
    case_name="conduction",
    executable=f"{case_dir}/conduction",
    source_case_dir=case_dir,
    top_level_options={"MXG": 0},
    options={
        "mesh": {"nx": 1, "ny": 100, "nz": 1, "dy": 0.2, "symmetricGlobalY": True, "ixseps1": -1, "ixseps2": -1},
        "conduction": {"chi": 1.0},
        "T": {"scale": 1.0, "function": "gauss(y-pi, 0.2)", "bndry_all": "dirichlet_o4(0.0)"},
        "solver": {"output_step": 0.1, "nout": 100},
    },
    mpi=BoutPPMpiSpec(launcher_mode="mpi", launcher="mpirun", processes=2),
    output=BoutPPOutputSpec(
        data_dir="data",
        require_settings=True,
        require_logs=True,
        require_dumps=True,
        require_restarts=True,
    ),
    timeout_seconds=300,
)

plan = BoutPPCompilerComponent().compile(
    spec,
    run_id="boutpp-real-conduction-smoke",
    workspace_dir=".runs/boutpp-real-smoke/boutpp-real-conduction-smoke",
)
artifact = BoutPPExecutorComponent(workspace_root=".runs/boutpp-real-smoke").execute(plan)
report = BoutPPValidatorComponent().validate(artifact, plan_ref=plan.plan_id, validation_spec=spec.validation)
```

The local CMake cache records `mpiexec` with `-n`, while the current MHE compiler emits MPI commands as `<launcher> -np <processes> ...`. Prefer `mpirun` for the MHE smoke if it accepts `-np`. If only `mpiexec -n` works locally, treat that as a compiler compatibility backlog item rather than forcing the smoke to pass.

## Current Implementation

`src/metaharness_ext/boutpp/real_smoke.py` now provides an opt-in repeated smoke harness with three cataloged cases:

| Case | Default | Current status | Evidence meaning |
|---|---:|---|---|
| `conduction-real` | enabled | passed 2/2 in retained local evidence | compiled BOUT++ executable integration for one tutorial case |
| `boutpp-python-runexample` | disabled | skipped | Python `boutpp` module support is optional and not promoted by this local build |
| `staggered-grid-wrapper` | disabled | skipped | wrapper example lacks a stable compiled BOUT++ binary contract in the local build |

The harness writes per-case `preflight.json`, per-repeat `boutpp_problem_spec.json`, `boutpp_run_plan.json`, `boutpp_run_artifact.json`, `boutpp_postprocess_report.json`, and `boutpp_validation_report.json`, plus a suite-level `boutpp_real_repeated_smoke_summary.json`.

Retained local evidence:

```text
.runs/boutpp-real-tools-domain-final/boutpp_real_repeated_smoke_summary.json
.runs/boutpp-real-tools-real-claude-final/boutpp-usage-benchmark/boutpp_real_repeated_smoke_summary.json
```

The retained domain run used `real_tools = true`, `real_claude = false`, `repeat_count = 2`, `mpi_launcher = "mpirun"`, and `build_root = "/home/linden/code/work/Solvers/FEM/BOUT-dev/build"`. The enabled `conduction-real` case passed both repeats with `return_code = 0`, `validation_passed = true`, `T` variable dimensions `t/x/y/z`, domain sizes `t=101`, `x=1`, `y=54`, `z=1`, logs, dump files, and restart files. The two additional example candidates were preserved as capability-gated skips with reviewer-visible skip reasons.

## Current Limitation

The typed BOUT++ compiler now supports top-level options through `BoutPPProblemSpec.top_level_options`, so the conduction smoke can render `MXG = 0` before named sections. Keep the tutorial mesh, conduction, variable, and solver settings in `options`; otherwise the generated `BOUT.inp` intentionally replaces the copied source input and BOUT++ will report missing mesh values such as `nx`.

This evidence remains case-scoped even with the `conduction-real` domain requirements enabled. The postprocess layer can collect NetCDF variable, dimension, and variable-dimension metadata when `netCDF4` is importable, and the validator enforces the case-specific `T` variable shape for promoted conduction smoke evidence. It still does not compare against analytic convergence criteria or establish broad BOUT++ physics model coverage.

## Smoke Execution Gate

The real smoke must stay opt-in. Recommended gate:

```bash
MHE_RUN_REAL_BOUTPP=1 \
BOUT_ROOT=/home/linden/code/work/Solvers/FEM/BOUT-dev \
BOUTPP_ROOT=/home/linden/code/work/Solvers/FEM/BOUT-dev/build \
PYTHONPATH=src \
python -m pytest tests/test_metaharness_boutpp_real_smoke.py -q
```

If an automated smoke test is added later, it should skip unless all of these conditions are true:

- `MHE_RUN_REAL_BOUTPP=1` is set;
- the conduction binary exists and is executable;
- a compatible MPI launcher is available;
- the source case data directory exists;
- the run workspace is writable.

Skip conditions must be reported as capability or dependency skips, not solver failures.

## Expected MHE Evidence

A passing MHE smoke should preserve:

- generated `BOUT.inp` in the MHE run workspace;
- `BoutPPRunArtifact` with `status="completed"` and `return_code=0`;
- discovered `BOUT.log.*`, `BOUT.settings`, `BOUT.dmp.*.nc`, and `BOUT.restart.*.nc` paths;
- `BoutPPValidationReport` with a passed artifact-level validation state.

If the smoke harness serializes additional reviewer evidence, it should also write `boutpp_problem_spec.json` and `boutpp_run_plan.json` beside the run artifacts. The current executor itself does not write those JSON files.

NetCDF variable/domain validation is optional. When `netCDF4` is unavailable or dump files are unreadable, postprocess records a warning; only specs that opt into required variables, dimensions, or variable-dimension mappings should block promotion on domain metadata.

## Comparison Benchmark Integration

For benchmark comparison, keep the existing dry-run `boutpp-usage` suite as the baseline and add real smoke evidence as a gated promotion tier:

| Tier | Evidence | Claim |
|---|---|---|
| dry-run usage validation | generated spec, plan, `BOUT.inp`, lane notes | workflow shape only |
| local real smoke | one local `conduction` executable run | local executable integration evidence |
| repeated real benchmark | multiple clean runs with retained artifacts | stability evidence for this case only |
| broader real benchmark | additional cases and domain metrics | stronger but still case-scoped solver evidence |

Do not merge the real smoke result into direct numerical superiority claims. The strongest current benchmark value remains workflow controllability: schema validation, environment gating, artifact discovery, reproducible run plans, optional domain metadata checks, comparator-visible promotion rows, and explicit skip reasons.

## Backlog From This Method

- Add an MPI launcher flag compatibility option if local `mpiexec` requires `-n` instead of `-np`.
- Preserve retained clean real-smoke and real-Claude comparison roots as CI or release artifacts when those gated jobs run remotely.
- Add analytic/error-norm or convergence checks only after a reviewed BOUT++ reference fixture exists for the promoted case.
- Promote more example cases only after each has a stable executable contract, case-local input directory, and reviewer-visible preflight evidence.
