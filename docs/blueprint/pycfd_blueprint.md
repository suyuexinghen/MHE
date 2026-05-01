 PyCFD MHE Extension — Development Analysis

  1. Domain Mapping: PyCFD vs fealpy

  ┌────────────────┬──────────────────────────────────────────────────┬─────────────────────────────────────────────────┐
  │   Dimension    │                 fealpy Extension                 │                 PyCFD Extension                 │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Physics        │ 19 PDE families (Poisson→Navier-Stokes)          │ 2D Euler equations (inviscid compressible)      │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Discretization │ Finite Element (Lagrange, Nedelec, RT, etc.)     │ Finite Volume (cell-centered, Roe flux)         │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Meshes         │ 6 types, generated in-code                       │ Unstructured hybrid tri/quad, file-based        │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Solver         │ Direct/iterative linear algebra                  │ Explicit RK2 time-marching                      │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Validation     │ L2/H1/Linf error vs exact solution               │ Residual norms, MMS truncation error            │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Package        │ pip-installable (fealpy)                         │ Flat scripts in src/, no package                │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Output         │ JSON stdout line                                 │ VTK files + ASCII dat files                     │
  ├────────────────┼──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
  │ Test cases     │ 8 benchmark cases (Poisson, Stokes, Darcy, etc.) │ 5 cases (vortex, airfoil, cylinder, MMS, shock) │
  └────────────────┴──────────────────────────────────────────────────┴─────────────────────────────────────────────────┘

  2. Proposed Extension Structure

  src/metaharness_ext/pycfd/
  ├── __init__.py              # Public re-exports (~15 names)
  ├── types.py                 # Type aliases + enums
  ├── contracts.py             # 10 Pydantic models
  ├── slots.py                 # Slot constants
  ├── capabilities.py          # Capability constants
  ├── gateway.py               # PyCFDGatewayComponent
  ├── environment.py           # PyCFDEnvironmentProbeComponent
  ├── compiler.py              # PyCFDCompilerComponent (5 case templates)
  ├── executor.py              # PyCFDExecutorComponent
  ├── validator.py             # PyCFDValidatorComponent
  ├── evidence.py              # build_evidence_bundle()
  ├── policy.py                # PyCFDEvidencePolicy
  ├── study.py                 # PyCFDStudyComponent (parameter sweeps)
  ├── governance.py            # PyCFDGovernanceAdapter
  ├── benchmark_runner.py      # PyCFDBenchmarkRunner (3-lane)
  └── benchmark_cases.py       # pycfd_case_catalog()

  3. Component-by-Component Design

  Contracts (contracts.py):
  - PyCFDMeshSpec — mesh source (generated/file), type (tri/quad), resolution (nx, ny), case file path
  - PyCFDFlowSpec — M_inf, aoa, gamma (default 1.4), flow state
  - PyCFDSolverSpec — CFL, flux_type (roe), second_order, limiter (venkatakrishnan/van_albada/none), max_iterations
  - PyCFDProblemSpec — task_id, case_type (vortex/airfoil/cylinder/mms/shock_diffraction), mesh, flow, solver, t_final, timeout_seconds
  - PyCFDEnvironmentReport — available, pycfd_path, numpy_version, matplotlib_available, case_files_available, blocks_promotion
  - PyCFDRunPlan — deterministic plan_id (SHA256 of spec), script_source, workspace_dir
  - PyCFDRunArtifact — status, return_code, residual_l1, residual_l2, residual_linf, wall_time_seconds, iterations, vtk_output_path
  - PyCFDValidationReport — passed, residual tolerances, convergence check, MMS error check
  - PyCFDEvidenceBundle / PyCFDPolicyReport — same pattern as fealpy

  Compiler (compiler.py):
  - 5 templates (one per case type), much simpler than fealpy's 7 templates:
    a. _render_vortex() — unsteady isentropic vortex convection
    b. _render_airfoil() — steady flow over airfoil
    c. _render_cylinder() — steady flow over cylinder
    d. _render_mms() — MMS truncation error verification
    e. _render_shock_diffraction() — Mach 5.09 shock over step
  - Each template generates a self-contained Python script that:
    - Sets up sys.path to include PyCFD src/
    - Imports and configures the solver
    - Runs to completion
    - Outputs a JSON metrics line to stdout (like fealpy's pattern)
  - Key challenge: PyCFD doesn't natively output JSON. The compiler must inject a JSON output wrapper into the generated script.

  Executor (executor.py):
  - Runs the generated script via subprocess.run([sys.executable, script_path])
  - Parses JSON from stdout (last line pattern)
  - Collects VTK output files as artifacts
  - Timeout handling, error capture

  Validator (validator.py):
  - Different validation metrics than fealpy (no L2/H1 FEM error):
    - Vortex case: L2 error of density vs exact solution (should decrease with mesh refinement)
    - Steady cases: Residual norm < tolerance (1e-5 default)
    - MMS case: Truncation error norms (L1 of residual − forcing)
    - Shock diffraction: Qualitative + shock position check
  - 5-state validation: unavailable, timeout, failed, residual_exceeded, passed

  Environment (environment.py):
  - Probes for PyCFD source at configured path (not a pip package)
  - Checks numpy availability
  - Validates that case mesh files exist for the 5 standard cases
  - Reports PyCFD "version" as git hash or hardcoded version

  Key Architectural Difference from fealpy:

  PyCFD is not a pip package. The environment probe must locate the PyCFD source directory. The compiler must inject sys.path manipulation into generated scripts. This is the biggest design divergence from
  the fealpy extension.

  4. PyCFD-Specific Modifications Needed

  The PyCFD codebase itself needs two minimal changes to be MHE-compatible:

  1. JSON metrics output (~30 lines added to Solvers.py):
    - After solver_solve() completes, print a JSON line with: status, residual_l1, residual_l2, residual_linf, iterations, wall_time, ncells, nnodes
    - This mirrors what fealpy already does natively
  2. Deterministic entry point: Ensure the solver can be driven entirely from a Python dict/config without editing input.nml or the __main__ block — ideally via a single function call like
  run_pycfd_case(config: dict) -> dict

  These are minor, backward-compatible additions (a new function + JSON print).

  5. Benchmark Cases

  5 cases map directly from PyCFD's existing test suite:

  ┌──────────────────────┬────────────────────────────────────┬───────────────────────────┬────────────────────────────────┐
  │       Case ID        │            Description             │     Validation Metric     │              Mesh              │
  ├──────────────────────┼────────────────────────────────────┼───────────────────────────┼────────────────────────────────┤
  │ vortex-2d            │ Isentropic vortex convection       │ L2 ρ error after 1 period │ Structured tri, 64×64          │
  ├──────────────────────┼────────────────────────────────────┼───────────────────────────┼────────────────────────────────┤
  │ airfoil-2d           │ NACA 0012, M=0.80, α=1.25°         │ Residual < 1e-5           │ Unstructured quad              │
  ├──────────────────────┼────────────────────────────────────┼───────────────────────────┼────────────────────────────────┤
  │ cylinder-2d          │ M=0.3 inviscid cylinder            │ Residual < 1e-5           │ Unstructured tri               │
  ├──────────────────────┼────────────────────────────────────┼───────────────────────────┼────────────────────────────────┤
  │ mms-2d               │ Manufactured solution verification │ Truncation error norms    │ Structured quad, 4 resolutions │
  ├──────────────────────┼────────────────────────────────────┼───────────────────────────┼────────────────────────────────┤
  │ shock-diffraction-2d │ M=5.09 shock over step             │ Shock position, residual  │ Structured quad                │
  └──────────────────────┴────────────────────────────────────┴───────────────────────────┴────────────────────────────────┘

  6. Implementation Phases

  Phase 0 — PyCFD Preparation (upstream changes):
  - Add run_pycfd_case(config) entry point to Solvers.py
  - Add JSON stdout output to solver
  - Add a minimal pyproject.toml or ensure PYTHONPATH works

  Phase 1 — Core Contracts + Environment:
  - types.py, contracts.py, slots.py, capabilities.py
  - environment.py — probe + report
  - Tests for all contract models and environment probe

  Phase 2 — Compiler + Executor:
  - compiler.py with 5 case templates
  - executor.py subprocess runner
  - Tests with mocked subprocess

  Phase 3 — Validator + Evidence + Policy:
  - validator.py with residual-based validation
  - evidence.py, policy.py — 5-gate chain
  - gateway.py — task intake

  Phase 4 — Benchmark Runner:
  - benchmark_runner.py — 3-lane comparison (extension/direct/agent)
  - benchmark_cases.py — case catalog
  - Real PyCFD integration tests (gated behind MHE_RUN_REAL_PYCFD=1)

  Phase 5 — Study + Governance:
  - study.py — parameter sweeps (mesh resolution, CFL, flux type)
  - governance.py — MHE core integration

  7. Risk Points

  1. PyCFD is not packaged — path management is fragile. Mitigation: the environment probe validates paths explicitly and the compiler injects absolute paths.
  2. Python 2/3 mix in PyCFD — some files use Python 2 syntax. Mitigation: test with Python 3; fix syntax issues upstream if needed.
  3. PyCFD has no existing test suite — no regression safety net. Mitigation: the MHE extension's own tests become the test suite.
  4. Mesh files are external — cases depend on .grid/.bc files. Mitigation: bundle mesh files with the extension or add structured mesh generation to the compiler.
  5. Validation metrics differ fundamentally — residual norms vs FEM error norms. Mitigation: design validation gates appropriate to finite-volume explicit solvers.

  8. Estimated Scope

  ┌────────────────────────┬────────────┬─────────────┐
  │       Component        │ Est. Lines │ Complexity  │
  ├────────────────────────┼────────────┼─────────────┤
  │ Contracts + Types      │ ~400       │ Low         │
  ├────────────────────────┼────────────┼─────────────┤
  │ Environment            │ ~200       │ Low         │
  ├────────────────────────┼────────────┼─────────────┤
  │ Compiler (5 templates) │ ~800       │ Medium      │
  ├────────────────────────┼────────────┼─────────────┤
  │ Executor               │ ~200       │ Low         │
  ├────────────────────────┼────────────┼─────────────┤
  │ Validator              │ ~250       │ Medium      │
  ├────────────────────────┼────────────┼─────────────┤
  │ Evidence + Policy      │ ~400       │ Low-Medium  │
  ├────────────────────────┼────────────┼─────────────┤
  │ Gateway + Governance   │ ~400       │ Medium      │
  ├────────────────────────┼────────────┼─────────────┤
  │ Benchmark runner       │ ~600       │ Medium-High │
  ├────────────────────────┼────────────┼─────────────┤
  │ Study                  │ ~300       │ Medium      │
  ├────────────────────────┼────────────┼─────────────┤
  │ Tests                  │ ~1500      │ —           │
  ├────────────────────────┼────────────┼─────────────┤
  │ Total                  │ ~5000      │ —           │
  └────────────────────────┴────────────┴─────────────┘
