# BOUT++ Real Smoke Method

> 版本：v0.1 | 状态：local opt-in method | 面向 `metaharness_ext.boutpp` 的真实 BOUT++ smoke evidence 升级路径。

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

Missing optional Python readers should warn but not block artifact-oriented smoke validation.

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

## Current Limitation

The typed BOUT++ compiler now supports top-level options through `BoutPPProblemSpec.top_level_options`, so the conduction smoke can render `MXG = 0` before named sections. Keep the tutorial mesh, conduction, variable, and solver settings in `options`; otherwise the generated `BOUT.inp` intentionally replaces the copied source input and BOUT++ will report missing mesh values such as `nx`.

## Smoke Execution Gate

The real smoke must stay opt-in. Recommended gate:

```bash
MHE_RUN_REAL_BOUTPP=1 \
BOUT_ROOT=/home/linden/code/work/Solvers/FEM/BOUT-dev \
BOUTPP_ROOT=/home/linden/code/work/Solvers/FEM/BOUT-dev/build \
PYTHONPATH=src \
python -m pytest tests/test_metaharness_boutpp_smoke.py -q
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

NetCDF variable validation should be optional unless `netCDF4` is importable in the active Python environment.

## Comparison Benchmark Integration

For benchmark comparison, keep the existing dry-run `boutpp-usage` suite as the baseline and add real smoke evidence as a gated promotion tier:

| Tier | Evidence | Claim |
|---|---|---|
| dry-run usage validation | generated spec, plan, `BOUT.inp`, lane notes | workflow shape only |
| local real smoke | one local `conduction` executable run | local executable integration evidence |
| repeated real benchmark | multiple clean runs with retained artifacts | stability evidence for this case only |
| broader real benchmark | additional cases and domain metrics | stronger but still case-scoped solver evidence |

Do not merge the real smoke result into direct numerical superiority claims. The strongest current benchmark value remains workflow controllability: schema validation, environment gating, artifact discovery, reproducible run plans, and explicit skip reasons.

## Backlog From This Method

- Add `tests/test_metaharness_boutpp_smoke.py` with `MHE_RUN_REAL_BOUTPP=1` gating.
- Add an MPI launcher flag compatibility option if local `mpiexec` requires `-n` instead of `-np`.
- Add a benchmark comparator row for real-smoke promotion status.
- Add optional NetCDF variable assertions for `T` only when `netCDF4` is available.
- Retain a clean run root under `.runs/boutpp-real-smoke/` or `/var/tmp/mhe-runs/<run-id>` for reviewer inspection when real evidence is reported.
