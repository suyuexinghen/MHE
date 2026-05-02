# 01. PyCFD Extension Overview

## 1. Extension Positioning

`metaharness_ext.pycfd` integrates [PyCFD](https://github.com/linden/PyCFD) — a 2D Euler finite-volume solver — as a controlled, declarable, verifiable, auditable CFD worker inside MHE.

**Target software**: PyCFD — Python 2D Euler equations solver using cell-centered finite-volume method with Roe flux and RK2 time-marching on unstructured hybrid meshes.

**Selected interface layer**: PyCFD is NOT a pip package. It lives at a configurable filesystem path (`PYCFD_SRC_PATH`). Integration is through path-based discovery (environment probe validates `Solvers.py` existence and importability), compiler-generated self-contained Python scripts that call `run_pycfd_case()`, and subprocess execution with JSON stdout parsing.

**Core difference from other MHE extensions**: Unlike fealpy (pure Python FEM library), PyCFD requires path-based discovery rather than pip import. Unlike Nektar (compiled C++ executable with XML configuration), PyCFD runs as a Python subprocess with dict-based configuration. Validation uses FVM residual norms (L1/L2) rather than FEM L2/H1 error norms.

## 2. Scope Boundaries

### Supported

- **5 2D Euler case types**: vortex-2d, airfoil-2d, cylinder-2d, mms-2d, shock-diffraction-2d
- **4 flow types**: subsonic, transonic, supersonic, hypersonic (auto-inferred from case type)
- **2 solver types**: explicit-rk (standard), implicit-lu (LU decomposition)
- **3 flux methods**: roe, hllc, van-leer
- **2 limiter methods**: barth, venkatakrishnan
- **Structured mesh generation** (all cases; airfoil requires external mesh file)
- **Complete MHE pipeline**: Gateway → Environment → Compiler → Executor → Validator → Evidence → Policy
- **Residual-based validation**: L1 and L2 residual norms against configurable tolerance (default 1e-5)
- **Parameter sweep study** (Cartesian product generation over spec axes)
- **3-lane benchmark runner** (extension/direct/agent)
- **Governance adapter** bridging to MHE core (SessionEvent, ValidationReport)

### Explicitly Not Supported

- 3D Euler or Navier-Stokes equations
- Implicit time-marching beyond LU decomposition
- Adaptive mesh refinement
- External mesh generation tools
- Turbulence modeling
- Incompressible flow solvers
- Accepting external user-written Python scripts (only compiler-generated scripts execute)

## 3. Design Goals

- **Controllability**: All CFD parameters (case type, mesh, flow, solver, flux, limiter) must be declared through typed spec; no implicit defaults
- **Typed boundary**: 14 Pydantic contracts define spec→plan→artifact→validation→evidence data flow
- **Validation-first**: Exit code is necessary but not sufficient; L1/L2 residual norms must pass tolerance gates
- **Evidence integrity**: Bundle aggregates environment + plan + artifact + validation; 5-gate policy chain evaluates promotion readiness
- **Subprocess isolation**: PyCFD runs in an independent Python subprocess with timeout enforcement
- **Path-based resilience**: Environment probe validates `PYCFD_SRC_PATH` before compilation; compiler injects absolute path into scripts
- **No full-PyCFD parity**: Focuses on the 2D Euler FVM validation pipeline

## 4. MHE Integration Seams

| Integration Point | Extension Provides | MHE Core Owns |
|---|---|---|
| Component lifecycle | `protected` attribute, slot declarations | Component discovery, dependency resolution, boot ordering |
| Graph staging | Slot + capability declarations | `ConnectionEngine` semantic validation, graph version commit/rollback |
| Session / Audit | Evidence refs (`pycfd://` prefix), event payloads | `SessionStore`, `AuditLog`, `ProvenanceGraph` |
| Policy / Promotion | `PyCFDEvidencePolicy` (5-gate chain) | Platform-level promotion authority |
| Execution lifecycle | `PyCFDExecutorComponent` (subprocess.run) | `ExecutionLifecycleService` |
| Benchmark | `PyCFDBenchmarkRunner` (3-lane) | `BenchmarkSuite`, CLI dispatch |
| Storage | Writes to workspace under `.runs/pycfd/` | `.runs/` directory ownership, artifact store |

**Core principle**: MHE = platform promotion / session / policy / provenance authority; PyCFD extension = PyCFD 2D Euler FVM workflow, numeric residual evidence, and validation contributor.
