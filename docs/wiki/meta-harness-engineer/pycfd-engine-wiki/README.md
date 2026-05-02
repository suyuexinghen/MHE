# PyCFD Extension for MHE Wiki

> Version: v1.0 | Last updated: 2026-05-01 | Status: **Complete**

This directory discusses **how to design `metaharness_ext.pycfd` inside `MHE`**.

Focuses on extension-level design boundaries: 2D Euler FVM case types, typed contracts, environment/validation/evidence surfaces, packaging/registration, and seams to the MHE governance path.

**This extension development is complete.** 74 tests pass + 3 smoke gated, ruff clean, 15 production files, 12 test files.

## What Is the PyCFD Extension

`metaharness_ext.pycfd` integrates [PyCFD](https://github.com/linden/PyCFD) — a 2D Euler finite-volume solver — as a controlled, declarable, verifiable, auditable CFD worker inside MHE. It wraps PyCFD's cell-centered FVM pipeline (Roe flux, RK2 time-marching, unstructured hybrid meshes) as a chain of MHE components.

**Core capabilities:**
- 5 2D Euler case types: vortex, airfoil, cylinder, MMS, shock-diffraction
- Cell-centered finite-volume with Roe flux and RK2 time-marching
- Complete MHE pipeline: Gateway → Environment → Compiler → Executor → Validator → Evidence → Policy
- Residual-based validation (L1/L2 norms) with 5-state validator
- 5-gate non-short-circuit evidence policy chain
- Parameter sweep study component (Cartesian product generation)
- 3-lane benchmark runner (extension/direct/agent)
- Path-based discovery via `PYCFD_SRC_PATH` (not a pip package)

## Navigation

| Document | Topic | Audience |
|---|---|---|
| [01-overview](01-overview.md) | Extension positioning, scope boundaries, design goals, MHE integration seams | Everyone |
| [02-workflow-and-components](02-workflow-and-components.md) | Canonical component chain (9 components), responsibilities, data flow | Architects / runtime engineers |
| [03-contracts-and-artifacts](03-contracts-and-artifacts.md) | 14 Pydantic contracts, Run Plan, Run Artifact, Validation Surface | Developers |
| [04-environment-validation-and-evidence](04-environment-validation-and-evidence.md) | Environment probe, 5-state validation taxonomy, 5-gate policy chain | Operators / governance |
| [05-family-design](05-family-design.md) | 5 case types, per-case compiler templates, solver/flux/limiter families | Domain specialists |
| [06-packaging-and-registration](06-packaging-and-registration.md) | 15-file layout, 30+ exports, 9 capabilities, 7 slots, 6 manifests | Packaging / registration |
| [07-scope-and-boundaries](07-scope-and-boundaries.md) | Wiki/blueprint/roadmap responsibility split, explicit out-of-scope | Everyone |
| [09-pycfd-extension-blueprint](../blueprint/09-pycfd-extension-blueprint.md) | Formal design blueprint (comprehensive) | Everyone |
| [09-pycfd-roadmap](../blueprint/09-pycfd-roadmap.md) | Execution roadmap (Phase 0–5 all complete) | Development / PM |

## Terminology

| Term | Meaning |
|---|---|
| **Case type** | One of 5 PyCFD test problems (vortex-2d, airfoil-2d, cylinder-2d, mms-2d, shock-diffraction-2d) |
| **Residual L1** | L1 norm of the steady-state residual |
| **Residual L2** | L2 norm of the steady-state residual |
| **Roe flux** | Approximate Riemann solver for convective fluxes |
| **RK2** | Second-order Runge-Kutta time-marching |
| **Artifact** | Single execution output (residuals, wall time, mesh statistics, iterations) |
| **Evidence bundle** | Aggregated environment + plan + artifact + validation structured evidence |
| **Policy gate** | 5-gate chain, each producing ALLOW/DEFER/REJECT |
| **Study** | Parameter sweep over a task template on specified axes |

## Design Principles

- **Path-based discovery** — PyCFD is not a pip package; `PYCFD_SRC_PATH` locates `Solvers.py`
- **Subprocess isolation** — PyCFD runs in an isolated Python subprocess with timeout enforcement
- **Compiler-generated scripts only** — external scripts are not accepted
- **Residual-first validation** — FVM solver quality is measured by residual decay, not FEM error norms
- **Evidence-first promotion** — exit code is necessary but not sufficient; residuals must pass tolerance gates
- **No full-PyCFD parity** — focuses on the 2D Euler FVM validation pipeline

## Division of Responsibility with `blueprint/`

- **wiki** = how the extension should be designed (stable design boundaries)
- **blueprint** = formal design position
- **roadmap** = phase sequencing and remaining gaps (currently: all complete)
- **implementation plan** = executable slices (lives in `.claude/plans/`)

## Recommended Reading Order

1. **Boundary first**: 01-overview → 07-scope → blueprint → roadmap
2. **Runtime semantics**: 02-workflow → 03-contracts → 04-validation-evidence
3. **Family/registration**: 05-family-design → 06-packaging
4. **Execution path**: roadmap (Phase 0–5 all complete)

## Out of Scope for This Wiki

- Upstream PyCFD user manual
- PyCFD full build/install guide
- MHE core architecture docs (see `meta-harness-wiki/`)
- Daily rollout logs
- Anything not necessary for extension design
