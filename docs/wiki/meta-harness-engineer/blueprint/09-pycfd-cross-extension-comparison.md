# Cross-Extension PDE Benchmark Comparison

**Date**: 2026-05-01
**Scope**: PyCFD vs Fealpy vs Nektar — PDE extensions in MHE

## Evidence quality

| Extension | Real solver execution | Real metrics | Dry-run only | Cases |
|-----------|----------------------|-------------|-------------|-------|
| pycfd-pde | Yes (all 5 cases) | Yes (residuals, wall time, cell counts) | No | 5 |
| fealpy-pde | No | No | Yes | 1 (poisson-2d-numpy) |
| nektar-pde | No | No | Yes | 6 |

PyCFD is currently the only PDE extension with real solver execution evidence collected through the MHE benchmark pipeline.

## PyCFD benchmark results (real execution)

| Case | Wall time | Cells | L1 residual | L2 residual | Solver type |
|------|----------|-------|-------------|-------------|-------------|
| vortex-2d | 161.2s | 32,768 | 0.00487 | 0.000146 | explicit_unsteady_solver |
| airfoil-2d | 394.6s | 3,120 | 0.00165 | 4.06e-5 | explicit_steady_solver |
| cylinder-2d | 495.1s | 6,240 | 0.00328 | 4.04e-5 | explicit_steady_solver |
| mms-2d | 9.1s | 32,768 | 0.819 | 0.00372 | mms_solver |
| shock-diffraction-2d | 530.1s | 10,000 | 0.0402 | 0.00191 | explicit_unsteady_solver_efficient_shockdiffraction |

## Case type coverage

| Physics domain | PyCFD | Fealpy | Nektar |
|---------------|-------|--------|--------|
| Inviscid compressible (Euler) | 5 cases (vortex, airfoil, cylinder, MMS, shock) | 0 | 1 (euler-1d) |
| Incompressible viscous (NS) | 0 | 0 | 1 (taylor-vortex-2d) |
| Elliptic (Poisson) | 0 | 1 (poisson-2d-numpy) | 0 |
| Advection-diffusion | 0 | 0 | 4 (advdiff-2d, advdiff-imex-2d, advection-1d, diffusion-2d) |

## Solver surface

| Capability | PyCFD | Fealpy | Nektar |
|-----------|-------|--------|--------|
| 2D unstructured mesh | Tri + Quad | Tri (numpy backend) | Quad |
| Explicit time stepping | Yes (RK2) | No (steady only) | Yes (IMEX, explicit) |
| Second-order spatial | Yes (gradient recon) | Yes (fem) | Yes (fem/hp) |
| Flux schemes | Roe, HLLC, van Leer | N/A | N/A |
| Limiters | vk_limiter, van Albada | N/A | N/A |
| Shock capturing | Yes (specialized solver) | No | No |
| MMS verification | Yes | No | No |
| Multi-backend | No (NumPy only) | Yes (numpy, pytorch, jax) | No (Nektar++ binary) |

## Pipeline maturity

| Aspect | PyCFD | Fealpy | Nektar |
|--------|-------|--------|--------|
| Environment probe | Yes | Yes | Yes |
| Compiler | Yes (pformat template) | Yes | Yes |
| Executor | Yes (subprocess) | Yes | Yes |
| Validator | Yes (per-case tolerance) | Yes | Yes |
| Evidence bundle | Yes | Yes | Yes |
| Policy/Governance | Yes | Yes | Yes |
| Study component | Yes | Yes (multi-backend) | Yes |
| CLI integration | Yes (benchmark-run, benchmark-compare, benchmark-approval-check) | Yes | Yes |
| Three-lane benchmark | Yes (extension, direct, agent) | Yes | Yes |
| Real Claude lanes | Direct lane with real execution | Dry-run only | Dry-run only |
| Fallback compiler (no Claude) | Yes | Partial | Partial |

## Key findings

1. **Only PyCFD has real execution evidence**: All 5 cases compile, execute, and produce valid metrics against the real PyCFD solver. Fealpy and Nektar benchmarks are dry-run validated only.

2. **PyCFD covers the full Euler surface**: Vortex convection, steady airfoil/cylinder, MMS verification, and shock capturing — all 5 canonical CFD verification cases.

3. **Solver robustness issues exist**: Vortex case required limiter enabled (CFL 0.5, use_limiter=True) to avoid negative pressure in Roe flux. Shock case requires pre-created VTK output directories. Both are upstream PyCFD issues now mitigated.

4. **Nektar has more case diversity** (6 cases across advection-diffusion, Euler, NS) but no real execution. Fealpy has the fewest cases (1).

5. **Fealpy's multi-backend claim** (numpy/pytorch/jax) is not yet validated with real execution evidence.

## Next actions

- P6: Add CI dry-run for PyCFD benchmarks
- Run real Nektar and Fealpy benchmarks to collect execution evidence
- Add more PyCFD cases (3D, viscous) as the upstream solver matures
