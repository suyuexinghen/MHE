# 05. Family Design

## 1. Why Case Type Is a First-Class Design Object

PyCFD's 5 test cases differ in flow physics, mesh requirements, and solver configuration. Case type determines:

- **Flow type**: subsonic, transonic, supersonic (auto-inferred)
- **Solver type**: explicit-rk or implicit-lu (auto-inferred)
- **Mesh configuration**: structured vs. external-file
- **Compiler template**: case-specific `run_pycfd_case()` configuration
- **Expected physical behavior**: vortex preservation, shock capture, MMS convergence

Making case type a first-class field ensures the compiler generates correct configurations and the validator applies appropriate expectations.

## 2. Supported Cases

| Case ID | Description | Flow Type | Solver Type | Mesh | Key Physics |
|---|---|---|---|---|---|
| `vortex-2d` | Isentropic vortex convection | subsonic | explicit-rk | Structured 101×101 | Vortex preservation, minimal dissipation |
| `airfoil-2d` | NACA0012 transonic flow | transonic | implicit-lu | External mesh file | Shock wave, lift/drag |
| `cylinder-2d` | Subsonic flow past circular cylinder | subsonic | explicit-rk | Structured 101×101 | Wake, separation |
| `mms-2d` | Method of manufactured solutions | subsonic | explicit-rk | Structured 101×101 | Convergence rate verification |
| `shock-diffraction-2d` | Shock wave diffraction over step | supersonic | explicit-rk | Structured 101×101 | Shock capture, expansion fan |

## 3. Per-Case Boundaries

### vortex-2d
- Default mesh: 101×101 structured
- Default Mach: 0.5
- Default tfinal: 1.0, dt: 0.01
- Key config: `free_stream_mach`, `vortex_strength`

### airfoil-2d
- Requires external mesh file (`mesh_file` parameter)
- Uses implicit LU solver for stiff transonic conditions
- Default Mach: 0.8 (transonic)
- Key config: `mach`, `aoa`, `naca_airfoil`, `mesh_file`

### cylinder-2d
- Default mesh: 101×101 structured
- Default Mach: 0.3
- Default tfinal: 5.0, dt: 0.02
- Key config: `cylinder_radius`, `mach`

### mms-2d
- Method of manufactured solutions for convergence testing
- Default mesh: 101×101 structured
- Default Mach: 0.5
- Compiler adds `compute_te_mms` flag for truncation error computation
- Key config: `compute_te_mms`

### shock-diffraction-2d
- Default mesh: 101×101 structured
- Default Mach: 2.0 (supersonic)
- Default tfinal: 0.2, dt: 0.002
- Key config: `shock_mach`, `step_height`

## 4. Case-to-Flow Mapping

```python
_CASE_FLOWTYPE_MAP = {
    "vortex-2d": "subsonic",
    "airfoil-2d": "transonic",
    "cylinder-2d": "subsonic",
    "mms-2d": "subsonic",
    "shock-diffraction-2d": "supersonic",
}
```

```python
_CASE_SOLVER_MAP = {
    "vortex-2d": "explicit-rk",
    "airfoil-2d": "implicit-lu",
    "cylinder-2d": "explicit-rk",
    "mms-2d": "explicit-rk",
    "shock-diffraction-2d": "explicit-rk",
}
```

These are computed fields on `PyCFDProblemSpec` — they are auto-inferred from `case_type` but can be overridden in advanced use cases.

## 5. Solver Family Design

| Solver Type | Time Integration | Stability | Use Case |
|---|---|---|---|
| `explicit-rk` | 2nd-order Runge-Kutta | CFL-limited | Subsonic, supersonic |
| `implicit-lu` | LU decomposition | Unconditionally stable | Transonic, stiff problems |

## 6. Flux Family Design

| Flux Method | Description | Best For |
|---|---|---|
| `roe` | Approximate Riemann solver | General compressible flow (default) |
| `hllc` | Harten-Lax-van Leer Contact | Strong shocks |
| `van-leer` | Flux-vector splitting | Hypersonic flows |

## 7. Limiter Family Design

| Limiter | Description | Properties |
|---|---|---|
| `barth` | Barth-Jespersen limiter | Smooth, good convergence (default) |
| `venkatakrishnan` | Venkatakrishnan limiter | Better convergence on unstructured meshes |

## 8. Current Tested Support Matrix

| Case | Compiler | Executor (mock) | Validator | Evidence | Policy | Study |
|---|---|---|---|---|---|---|
| vortex-2d | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| airfoil-2d | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| cylinder-2d | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| mms-2d | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| shock-diffraction-2d | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

All 5 cases are covered by 74 unit tests. Smoke tests (3) require `MHE_RUN_REAL_PYCFD=1` for real PyCFD execution and are opt-in.

## 9. Case Extension Rules

To add a new case type:
1. Add the case ID to `PyCFDCaseType` literal in `types.py`
2. Add default configuration to `_CASE_DEFAULTS` in `compiler.py`
3. Add flow type and solver type mappings in `contracts.py`
4. Add the case to `pycfd_case_catalog()` in `benchmark_cases.py`
5. Add compiler test for the new case template
6. Add validator test for the new case's expected residual range
