# `metaharness_nektar` Module Blueprint

This document proposes a practical blueprint for a future `metaharness_nektar` package that connects the Meta-Harness Engineering (`MHE`) runtime with the Nektar++ framework.

The target is not only to run existing Nektar++ cases, but to let an agent progressively:

1. compile high-level PDE problem specs into Nektar++ session artifacts,
2. execute solver workflows end to end,
3. inspect results and validation signals,
4. iteratively improve case configuration, and
5. eventually scaffold new Nektar++ solver extensions when XML-level control is no longer sufficient.

The design is intentionally staged. The first implementation should focus on reliable case compilation and execution on top of existing Nektar++ solver applications. Native C++ solver generation should come later.

## 1. Goals

`metaharness_nektar` should provide a stable bridge between:

- the typed, graph-driven MHE runtime, and
- the file-oriented, solver-specific Nektar++ workflow.

The module should make it possible for an agent to:

- express a PDE problem in a typed internal form,
- generate or adapt a Nektar++ mesh/session workflow,
- choose an appropriate Nektar++ solver family,
- run pre-processing, solving, and post-processing steps,
- collect machine-readable evidence from logs, filters, and converted fields,
- decide whether the run is valid, and
- repeat the loop with improved parameters or structure.

## 2. Non-Goals For The First Slice

The first implementation should not try to do all of the following:

- replace the internal Nektar++ C++ solver architecture,
- synthesize arbitrary new numerical methods directly into Nektar++ core,
- support every Nektar++ solver family at once,
- solve CAD-heavy mesh construction in the first phase,
- build a perfect XML round-trip layer for every Nektar++ dialect.

Instead, the first slice should optimize for:

- typed case compilation,
- deterministic session generation,
- reproducible solver execution,
- post-processing integration, and
- validation-oriented iteration.

## 3. Why Nektar++ Fits An Agent Loop

Nektar++ already exposes much of its runtime behavior through session XML rather than hard-coded solver source changes.

The key configuration surfaces are:

- `GEOMETRY`
- `EXPANSIONS`
- `CONDITIONS`
- `PARAMETERS`
- `SOLVERINFO`
- `TIMEINTEGRATIONSCHEME`
- `VARIABLES`
- `BOUNDARYREGIONS`
- `BOUNDARYCONDITIONS`
- `FUNCTION`
- `FORCING`
- `FILTERS`

This means an agent can control a large part of the workflow without immediately editing C++.

Nektar++ also provides two natural surrounding tools:

- `NekMesh` for mesh import, generation, conversion, and repair,
- `FieldConvert` for post-processing, diagnostics, interpolation, extraction, and visualization export.

Together, these make Nektar++ a good target for an agent that reasons over a typed plan, emits files, executes tools, observes outputs, and iterates.

## 4. High-Level Architecture

A practical `metaharness_nektar` package should be structured around six main layers:

1. **problem specification layer**
2. **Nektar compilation layer**
3. **execution orchestration layer**
4. **post-processing layer**
5. **validation layer**
6. **extension/scaffolding layer** (deferred)

Phase 1 implements compilation, execution, and validation as the core loop. Problem specification and post-processing are partial in Phase 1: specification covers ADR and IncNS only, and post-processing covers basic `FieldConvert` conversion plus error extraction. The extension/scaffolding layer is explicitly deferred to Phase 4.

## 5. Package Layout

Start flat. Refactor into subpackages only when a single file grows unwieldy.

```
MHE/src/metaharness_nektar/
├── __init__.py
├── capabilities.py
├── contracts.py
├── types.py
├── slots.py
├── xml_renderer.py
├── session_compiler.py
├── solver_executor.py
├── postprocess.py
├── validator.py
└── analyzers.py
```

This mirrors the `metaharness_ai4pde` pattern of keeping typed contracts and component logic separate from CLI/process details, but avoids premature subpackaging.

Future expansion (Phase 2+) may extract:
- `components/` when graph nodes grow complex,
- `executors/` when solver dispatch needs per-family modules,
- `mutations/` when optimization helpers are added,
- `templates/` when session templates accumulate.

## 6. Core Design Principle

`metaharness_nektar` should not treat Nektar++ session XML as the primary internal truth.

The internal authority should remain typed Python models. XML should be the external artifact emitted for Nektar++.

This follows the same design rule already present in MHE: external representations are not the runtime truth.

In practice:

- the agent reasons over typed problem and solver models,
- components pass structured data between each other,
- XML is rendered near the execution boundary,
- logs, filters, and post-processing outputs are parsed back into typed summaries.

This is the key requirement if the system is expected to iterate safely instead of doing brittle string edits.

## 7. Types And Enums

All domain-specific selections must be typed enums, not free-form strings. This follows the `metaharness_ai4pde/types.py` pattern of `str, Enum` classes.

```python
class NektarSolverFamily(str, Enum):
    ADR = "adr"
    INCNS = "incns"
    COMPRESSIBLE = "compressible"
    ELASTICITY = "elasticity"
    CARDIAC_EP = "cardiac_ep"
    PULSE_WAVE = "pulse_wave"
    SHALLOW_WATER = "shallow_water"
    ACOUSTIC = "acoustic"


class NektarAdrEqType(str, Enum):
    PROJECTION = "Projection"
    LAPLACE = "Laplace"
    POISSON = "Poisson"
    HELMHOLTZ = "Helmholtz"
    STEADY_ADVECTION_DIFFUSION = "SteadyAdvectionDiffusion"
    STEADY_DIFFUSION_REACTION = "SteadyDiffusionReaction"
    STEADY_ADVECTION_DIFFUSION_REACTION = "SteadyAdvectionDiffusionReaction"
    UNSTEADY_ADVECTION = "UnsteadyAdvection"
    UNSTEADY_DIFFUSION = "UnsteadyDiffusion"
    UNSTEADY_REACTION_DIFFUSION = "UnsteadyReactionDiffusion"
    UNSTEADY_ADVECTION_DIFFUSION = "UnsteadyAdvectionDiffusion"
    UNSTEADY_INVISCID_BURGER = "UnsteadyInviscidBurger"


class NektarIncnsEqType(str, Enum):
    STEADY_STOKES = "SteadyStokes"
    STEADY_OSEEN = "SteadyOseen"
    UNSTEADY_STOKES = "UnsteadyStokes"
    STEADY_LINEARISED_NS = "SteadyLinearisedNS"
    UNSTEADY_LINEARISED_NS = "UnsteadyLinearisedNS"
    UNSTEADY_NAVIER_STOKES = "UnsteadyNavierStokes"


class NektarProjection(str, Enum):
    CONTINUOUS = "Continuous"
    DISCONTINUOUS = "DisContinuous"


class NektarIncnsSolverType(str, Enum):
    VELOCITY_CORRECTION = "VelocityCorrectionScheme"
    VCS_WEAK_PRESSURE = "VCSWeakPressure"
    COUPLED_LINEARISED_NS = "CoupledLinearisedNS"
    SMOOTHED_PROFILE = "SmoothedProfileMethod"
    VCS_MAPPING = "VCSMapping"


class NektarBoundaryConditionType(str, Enum):
    DIRICHLET = "D"
    NEUMANN = "N"
    ROBIN = "R"
    PERIODIC = "P"


class NektarUserDefinedBc(str, Enum):
    """Solver-specific USERDEFINEDTYPE values for boundary conditions."""
    H = "H"                       # high-order pressure BC (IncNS)
    H_OUTFLOW = "HOutflow"        # outflow (IncNS)
    TIME_DEPENDENT = "TimeDependent"
    WOMERSLEY = "Womersley"       # Womersley BC (IncNS)
    MOVING_BODY = "MovingBody"    # (IncNS)
    FLOWRATE = "Flowrate"         # (IncNS)
    ROTATED = "Rotated"           # rotated BCs (IncNS)
    WALL = "Wall"                 # (Compressible, Elasticity)
    WALL_VISCOUS = "WallViscous"  # (Compressible)
    WALL_ADIABATIC = "WallAdiabatic"  # (Compressible)
    PRESSURE_OUTFLOW = "PressureOutflow"  # (Compressible)


class NektarGeometryMode(str, Enum):
    DIM_2D = "2D"
    DIM_2D_HOMO1D = "2D-homogeneous-1D"
    DIM_3D = "3D"
```

Phase 1 only needs `NektarAdrEqType`, `NektarIncnsEqType`, `NektarProjection`, and `NektarIncnsSolverType`. The remaining enums are placeholder definitions for later phases.

## 8. Core Contracts

The following contracts should exist before implementation starts. All follow the `metaharness_ai4pde/contracts.py` pattern: Pydantic v2 `BaseModel` with `task_id` as a cross-cutting correlation key and `dict[str, Any]` `Field(default_factory=dict)` for extensible sub-specs.

### 8.1 Problem-level contract

```python
class NektarProblemSpec(BaseModel):
    task_id: str
    title: str
    solver_family: NektarSolverFamily
    dimension: int
    space_dimension: int | None = None
    variables: list[str]
    domain: dict[str, Any] = Field(default_factory=dict)
    materials: dict[str, float | str] = Field(default_factory=dict)
    parameters: dict[str, float | str] = Field(default_factory=dict)
    initial_conditions: list[dict[str, Any]] = Field(default_factory=list)
    boundary_conditions: list[dict[str, Any]] = Field(default_factory=list)
    forcing: list[dict[str, Any]] = Field(default_factory=list)
    reference: dict[str, Any] | None = None
    objectives: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
```

Note: `equation_family` is now `solver_family: NektarSolverFamily` (typed enum, not free-form string).

### 8.2 Mesh contract

```python
class NektarMeshSpec(BaseModel):
    source_mode: Literal["existing_xml", "nekg", "gmsh", "generated"]
    source_path: str | None = None
    geometry_mode: NektarGeometryMode = NektarGeometryMode.DIM_2D
    composites: list[dict[str, Any]] = Field(default_factory=list)
    periodic_pairs: list[dict[str, Any]] = Field(default_factory=list)
    curved_entities: list[dict[str, Any]] = Field(default_factory=list)
    mesh_processes: list[dict[str, Any]] = Field(default_factory=list)
```

### 8.3 Expansion contract

```python
class NektarExpansionSpec(BaseModel):
    field: str
    composite_ids: list[str]
    basis_type: str
    num_modes: int | dict[str, int]
    points_type: str | None = None
    homogeneous_length: float | None = None
```

### 8.4 Session plan contract

```python
class NektarSessionPlan(BaseModel):
    task_id: str
    plan_id: str
    solver_family: NektarSolverFamily
    solver_binary: str
    equation_type: NektarAdrEqType | NektarIncnsEqType | str  # typed per family
    projection: NektarProjection | None = None
    solver_type: NektarIncnsSolverType | None = None  # IncNS-specific
    solver_info: dict[str, str] = Field(default_factory=dict)  # remaining free keys
    parameters: dict[str, float | str] = Field(default_factory=dict)
    time_integration: dict[str, Any] | None = None
    variables: list[str] = Field(default_factory=list)
    expansions: list[NektarExpansionSpec] = Field(default_factory=list)
    boundary_regions: list[dict[str, Any]] = Field(default_factory=list)
    boundary_conditions: list[dict[str, Any]] = Field(default_factory=list)
    functions: list[dict[str, Any]] = Field(default_factory=list)
    forcing: list[dict[str, Any]] = Field(default_factory=list)
    filters: list[dict[str, Any]] = Field(default_factory=list)
    postprocess_plan: list[dict[str, Any]] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    validation_targets: list[str] = Field(default_factory=list)
```

Note: `equation_type`, `projection`, and `solver_type` are now typed enums. `solver_info` retains dict form for remaining free keys not covered by the typed fields. `postprocess_plan` is new: declares `FieldConvert` chains before execution.

### 8.5 Run artifact contract

```python
class FilterOutputSummary(BaseModel):
    """Typed summary of common Nektar++ filter outputs."""
    checkpoint_files: list[str] = Field(default_factory=list)
    history_point_files: list[str] = Field(default_factory=list)
    energy_norms: dict[str, float] = Field(default_factory=dict)
    error_norms: dict[str, float] = Field(default_factory=dict)
    moving_body_forces: dict[str, list[float]] = Field(default_factory=dict)
    fieldconvert_intermediates: list[str] = Field(default_factory=list)
    other: dict[str, Any] = Field(default_factory=dict)


class NektarRunArtifact(BaseModel):
    task_id: str
    run_id: str
    solver_family: NektarSolverFamily
    session_files: list[str] = Field(default_factory=list)
    mesh_files: list[str] = Field(default_factory=list)
    field_files: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    derived_files: list[str] = Field(default_factory=list)
    filter_outputs: FilterOutputSummary = Field(default_factory=FilterOutputSummary)
    result_summary: dict[str, Any] = Field(default_factory=dict)
```

### 8.6 Validation contract

```python
class NektarValidationReport(BaseModel):
    task_id: str
    passed: bool
    solver_exited_cleanly: bool | None = None
    field_files_exist: bool | None = None
    error_vs_reference: float | None = None
    residual_ok: bool | None = None
    bc_ok: bool | None = None
    reference_ok: bool | None = None
    conservation_ok: bool | None = None
    messages: list[str] = Field(default_factory=list)
    metrics: dict[str, float | str] = Field(default_factory=dict)
```

Note: Phase 1 validation fields are `solver_exited_cleanly`, `field_files_exist`, and `error_vs_reference`. All other fields are `None` by default and populated in later phases.

## 9. Slot Definitions And Graph Topology

### 9.1 Slot constants (`slots.py`)

```python
NEKTAR_GATEWAY_SLOT = "nektar.gateway"
SESSION_COMPILER_SLOT = "nektar.session_compiler"
SOLVER_ROUTER_SLOT = "nektar.solver_router"
SOLVER_EXECUTOR_SLOT = "nektar.solver_executor"
POSTPROCESS_EXECUTOR_SLOT = "nektar.postprocess"
NEKTAR_VALIDATOR_SLOT = "nektar.validator"
```

### 9.2 Graph topology

```
NektarGatewayComponent ──(NektarProblemSpec)──> SessionCompilerComponent
                                                    │
                                          (NektarSessionPlan)
                                                    │
                                                    v
                                            SolverRouterComponent
                                                    │
                                          (NektarSessionPlan, enriched)
                                                    │
                                                    v
                                            SolverExecutorComponent
                                                    │
                                          (NektarRunArtifact)
                                                    │
                                            ┌───────┴───────┐
                                            v               v
                                  PostprocessComponent  NektarValidatorComponent
                                            │               │
                                  (derived artifacts)  (NektarValidationReport)
```

`MeshGatewayComponent` is not a graph node in Phase 1. Mesh preparation is handled inside `SessionCompilerComponent` as a pre-compilation step. If mesh handling grows complex enough to warrant its own node, it can be extracted in Phase 2.

## 10. Capabilities

Capability constants follow the `metaharness_ai4pde/capabilities.py` pattern: dotted-string constants in namespace `<domain>.<category>.<name>`.

```python
CAP_NEKTAR_CASE_COMPILE = "nektar.compile.case"
CAP_NEKTAR_MESH_PREPARE = "nektar.mesh.prepare"
CAP_NEKTAR_SOLVE_ADR = "nektar.solver.adr"
CAP_NEKTAR_SOLVE_INCNS = "nektar.solver.incns"
CAP_NEKTAR_POSTPROCESS = "nektar.postprocess.fieldconvert"
CAP_NEKTAR_VALIDATE = "nektar.validation.check"
CAP_NEKTAR_SCAFFOLD_SOLVER = "nektar.scaffold.solver"  # reserved, Phase 4

CANONICAL_CAPABILITIES: frozenset[str] = frozenset({
    CAP_NEKTAR_CASE_COMPILE,
    CAP_NEKTAR_MESH_PREPARE,
    CAP_NEKTAR_SOLVE_ADR,
    CAP_NEKTAR_SOLVE_INCNS,
    CAP_NEKTAR_POSTPROCESS,
    CAP_NEKTAR_VALIDATE,
    # CAP_NEKTAR_SCAFFOLD_SOLVER excluded until Phase 4
})
```

## 11. Graph Components

All components subclass `HarnessComponent` from `metaharness.core.component`, implement `activate(runtime)` / `deactivate()` / `declare_interface(api)`, and use `api.bind_slot()` / `declare_input()` / `declare_output()` / `provide_capability()` / `require_capability()`.

### 11.1 `NektarGatewayComponent`

- **Slot:** `NEKTAR_GATEWAY_SLOT`
- **Inputs:** none (root component)
- **Outputs:** `"problem_spec": NektarProblemSpec`
- **Capabilities provided:** `CAP_NEKTAR_CASE_COMPILE`
- **Protected:** no
- **Responsibilities:**
  - accept a high-level PDE or case request,
  - decide whether the request targets an existing Nektar++ solver or a future scaffold flow,
  - normalize request metadata,
  - emit a `NektarProblemSpec`.

### 11.2 `SessionCompilerComponent`

- **Slot:** `SESSION_COMPILER_SLOT`
- **Inputs:** `"problem_spec": NektarProblemSpec`
- **Outputs:** `"session_plan": NektarSessionPlan`
- **Capabilities provided:** `CAP_NEKTAR_CASE_COMPILE`, `CAP_NEKTAR_MESH_PREPARE`
- **Protected:** no
- **Responsibilities:**
  - compile `NektarProblemSpec` into `NektarSessionPlan`,
  - resolve mesh input (existing file, `NekMesh` conversion, or inline generation),
  - render session XML via `xml_renderer.py`,
  - keep mesh XML and conditions/session overlay separate when the source is a multi-file workflow,
  - attach filters and post-processing expectations.

### 11.3 `SolverRouterComponent`

- **Slot:** `SOLVER_ROUTER_SLOT`
- **Inputs:** `"session_plan": NektarSessionPlan`
- **Outputs:** `"routed_plan": NektarSessionPlan` (enriched with solver binary, validated `equation_type`)
- **Capabilities required:** `CAP_NEKTAR_SOLVE_ADR` or `CAP_NEKTAR_SOLVE_INCNS`
- **Protected:** no
- **Responsibilities:**
  - validate that the requested solver family is supported,
  - map `NektarSolverFamily` to the correct Nektar++ solver binary,
  - validate `equation_type` against the solver family's admissible values,
  - fill in any default `solver_info` keys not set by the compiler.

### 11.4 `SolverExecutorComponent`

- **Slot:** `SOLVER_EXECUTOR_SLOT`
- **Inputs:** `"routed_plan": NektarSessionPlan`
- **Outputs:** `"run_artifact": NektarRunArtifact`
- **Capabilities provided:** `CAP_NEKTAR_SOLVE_ADR`, `CAP_NEKTAR_SOLVE_INCNS`
- **Protected:** no
- **Responsibilities:**
  - execute the selected solver with rendered files,
  - manage working directories and output locations,
  - collect standard outputs (`.fld`, `.chk`, logs),
  - expose a typed `NektarRunArtifact`.

### 11.5 `PostprocessComponent`

- **Slot:** `POSTPROCESS_EXECUTOR_SLOT`
- **Inputs:** `"run_artifact": NektarRunArtifact`
- **Outputs:** `"derived_artifacts": NektarRunArtifact` (updated with derived files)
- **Capabilities provided:** `CAP_NEKTAR_POSTPROCESS`
- **Protected:** no
- **Responsibilities:**
  - invoke `FieldConvert` chains,
  - generate visualization artifacts (`.vtu`, `.dat`),
  - compute derived quantities (vorticity, boundary extraction, error norms).

### 11.6 `NektarValidatorComponent`

- **Slot:** `NEKTAR_VALIDATOR_SLOT`
- **Inputs:** `"run_artifact": NektarRunArtifact`
- **Outputs:** `"validation_report": NektarValidationReport`
- **Capabilities provided:** `CAP_NEKTAR_VALIDATE`
- **Protected:** yes (validators should not be hot-swapped)
- **Responsibilities:**
  - parse solver logs for convergence/failure signals,
  - check output artifact existence,
  - compare results against reference functions or expected metrics,
  - emit `NektarValidationReport`.

## 12. End-To-End Workflow

The recommended runtime flow is:

1. receive high-level problem request,
2. `NektarGatewayComponent` builds `NektarProblemSpec`,
3. `SessionCompilerComponent` resolves mesh, compiles `NektarSessionPlan`, renders session XML,
4. `SolverRouterComponent` validates and enriches the plan,
5. `SolverExecutorComponent` executes the selected Nektar++ solver,
6. `PostprocessComponent` runs `FieldConvert` and derived post-processing,
7. `NektarValidatorComponent` parses logs and diagnostics, emits validation report,
8. either stop or schedule mutation/optimization for another run.

## 13. Session Compilation Strategy

The system should avoid raw string templating for entire session files.

Instead, it should:

1. build typed intermediate XML section models,
2. render deterministic XML from those models,
3. optionally split mesh and conditions/session overlays (Nektar++ supports this: later files override earlier top-level sections),
4. preserve stable ordering for reproducible diffs.

### 13.1 XML section models

Each section maps to a typed model. This is important because many future agent mutations will target only one section.

```python
class GeometrySection(BaseModel):
    """Full GEOMETRY model matching Nektar++ XML schema.

    Sub-elements: VERTEX, EDGE (DIM>=2), FACE (DIM=3),
    ELEMENT (always), CURVED (high-order), COMPOSITE, DOMAIN.
    """
    dimension: int
    space_dimension: int
    vertices: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    faces: list[dict[str, Any]] = Field(default_factory=list)
    elements: list[dict[str, Any]] = Field(default_factory=list)
    curved: list[dict[str, Any]] = Field(default_factory=list)
    composites: list[dict[str, Any]] = Field(default_factory=list)
    domain: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_dimension_fields(self) -> "GeometrySection":
        if self.dimension >= 2 and not self.edges:
            raise ValueError("EDGE required for DIM >= 2")
        if self.dimension == 3 and not self.faces:
            raise ValueError("FACE required for DIM = 3")
        return self


class ExpansionSection(BaseModel):
    expansions: list[NektarExpansionSpec]


class ConditionsSection(BaseModel):
    parameters: dict[str, float | str] = Field(default_factory=dict)
    solver_info: dict[str, str] = Field(default_factory=dict)
    variables: list[str] = Field(default_factory=list)
    time_integration: dict[str, Any] | None = None
    global_sys_soln_info: dict[str, dict[str, str]] = Field(default_factory=dict)


class BoundarySection(BaseModel):
    """Boundary regions and conditions.

    BC types: D (Dirichlet), N (Neumann), R (Robin, requires PRIMCOEFF),
    P (Periodic). Solver-specific semantics via USERDEFINEDTYPE.
    """
    boundary_regions: list[dict[str, Any]] = Field(default_factory=list)
    boundary_conditions: list[dict[str, Any]] = Field(default_factory=list)


class FunctionSection(BaseModel):
    """Named functions for ICs, forcing, exact solutions, baseflows.

    Spatial expression variables are strictly dimension-dependent:
    - 1D: x
    - 2D: x, y
    - 3D: x, y, z

    No r, theta, phi. Use rad(x,y) / ang(x,y) for polar-like expressions.
    Dimension-mismatched variables silently evaluate to -9999.
    """
    functions: list[dict[str, Any]] = Field(default_factory=list)


class ForcingSection(BaseModel):
    forcing: list[dict[str, Any]] = Field(default_factory=list)


class FilterSection(BaseModel):
    filters: list[dict[str, Any]] = Field(default_factory=list)
```

### 13.2 Robin BC validation

The `BoundarySection` model must enforce:

- Robin (`R`) BCs include a `PRIMCOEFF` attribute.
- Periodic (`P`) BCs come in paired regions with matching composite sizes.

```python
def validate_boundary_conditions(
    bc_type: str, bc_value: dict[str, Any], *, dimension: int,
) -> list[str]:
    errors: list[str] = []
    if bc_type == "R" and "PRIMCOEFF" not in bc_value:
        errors.append("Robin BC requires PRIMCOEFF attribute")
    if bc_type == "P":
        if "paired_region" not in bc_value:
            errors.append("Periodic BC requires paired_region")
    return errors
```

### 13.3 Expression variable validation

The `FunctionSection` comment above documents the constraint. Validation should check expression strings against allowed variables for the given dimension:

```python
_ALLOWED_SPATIAL_VARS: dict[int, set[str]] = {
    1: {"x"},
    2: {"x", "y"},
    3: {"x", "y", "z"},
}

def validate_expression(expr: str, *, dimension: int) -> list[str]:
    """Check for disallowed spatial variables in analytic expressions."""
    allowed = _ALLOWED_SPATIAL_VARS[dimension]
    # Naive check: look for bare variable tokens
    # Real implementation would parse the expression more carefully
    tokens = _extract_variable_tokens(expr)
    disallowed = tokens - allowed - _MATH_FUNCTIONS
    if disallowed:
        return [f"Variables {disallowed} not available in {dimension}D; "
                f"evaluates to -9999"]
    return []
```

## 14. Post-Processing Strategy

`FieldConvert` should be treated as a first-class executor, not a final add-on.

Module ordering is significant: execution follows command-line argument order.

Supported output formats: `.vtu` (ParaView/VisIt), `.dat` (Tecplot), `.plt` (Tecplot/VisIt), `.fld` (native, including HDF5 variant), `.xml` (deform module).

Phase 1 post-processing operations:

- field-to-visualization conversion (`.fld` to `.vtu`),
- L2 error computation against an exact solution (via `FieldConvert -m ...`),
- basic field norm extraction.

Phase 2+ operations:

- vorticity, Q-criterion, gradient generation,
- boundary extraction (`extract:bnd=N`),
- interpolation to a target mesh,
- probe/sample extraction.

The post-process plan is part of `NektarSessionPlan.postprocess_plan` so expected downstream artifacts are declared before execution.

## 15. Validation Strategy

Phase 1 validation is limited to three evidence channels:

1. **process exit code + stdout/stderr** — did the solver terminate cleanly?
2. **`.fld`/`.chk` existence** — did the solver produce output?
3. **`FieldConvert`-derived error** — L2 error against an exact or reference solution (when available).

Later phases add:

- filter output parsing (checkpoint history, energy norms),
- convergence signal extraction from logs,
- conservation residual checks (divergence for IncNS),
- boundary-condition consistency checks.

The validator should report both binary status (`passed`) and explainable metrics (`error_vs_reference`, `messages`).

## 16. Agent Mutation And Optimization Surface

Once the basic loop works, `metaharness_nektar` becomes useful because it exposes structured mutation targets.

High-value first mutation targets:

- `TimeStep`
- `NumSteps` / `FinalTime`
- `NUMMODES`
- basis type
- `Projection`
- advection or diffusion operator selection
- Riemann solver choice for compressible flow (Phase 2)
- filter density and checkpoint cadence
- initial condition expressions
- boundary expressions

These should be changed through typed plan mutations (modifying `NektarSessionPlan` fields) rather than ad hoc XML edits.

## 17. Solver Support Roadmap

### Phase 1: ADR + IncNS (MVP)

Solver binaries:

- `ADRSolver`
- `IncompressibleNavierStokesSolver`

ADR equation types supported in Phase 1:

| EQTYPE | Steady/Unsteady |
|--------|----------------|
| `Laplace` | Steady |
| `Poisson` | Steady |
| `Helmholtz` | Steady |
| `SteadyAdvectionDiffusion` | Steady |
| `UnsteadyAdvectionDiffusion` | Unsteady |
| `UnsteadyReactionDiffusion` | Unsteady |

ADR projections: `Continuous`, `DisContinuous`.

IncNS equation types supported in Phase 1:

| EQTYPE | Steady/Unsteady |
|--------|----------------|
| `SteadyStokes` | Steady |
| `UnsteadyStokes` | Unsteady |
| `UnsteadyNavierStokes` | Unsteady |

IncNS solver types: `VelocityCorrectionScheme`, `VCSWeakPressure`.

Capabilities:

- compile typed case into session XML,
- execute solver,
- run basic `FieldConvert` post-processing,
- validate outputs against 3 evidence channels.

### Phase 2: broader solver family coverage

Add:

- `CompressibleFlowSolver`
- `LinearElasticSolver`

New work:

- richer `SOLVERINFO` enumerations,
- solver-specific BC modeling,
- more complex filters and forcing types,
- expanded validation channels.

### Phase 3: adaptive iteration

Add:

- mutation heuristics,
- parameter search,
- run-to-run metric comparison,
- automated solver strategy selection.

### Phase 4: scaffold generation for new solver development

Only after phases 1 to 3 are stable.

At this point, the system may help generate:

- a new Nektar++ solver directory scaffold,
- boilerplate registration code,
- default session schema fragments,
- boundary-condition and filter hook stubs,
- harness-side tests and templates.

## 18. Manifest And Packaging Integration

### 18.1 Manifest design

`metaharness_nektar` components are discovered through the same manifest system used by `metaharness_ai4pde`. A minimal manifest:

```yaml
# MHE/src/metaharness_nektar/MANIFEST.yaml
id: metaharness_nektar
version: "0.1.0"
harness_version: ">=0.1.0"
components:
  - module: metaharness_nektar.session_compiler
    class: SessionCompilerComponent
  - module: metaharness_nektar.solver_router
    class: SolverRouterComponent
  - module: metaharness_nektar.solver_executor
    class: SolverExecutorComponent
  - module: metaharness_nektar.postprocess
    class: PostprocessComponent
  - module: metaharness_nektar.validator
    class: NektarValidatorComponent
  - module: metaharness_nektar.nektar_gateway
    class: NektarGatewayComponent
```

### 18.2 Relationship to `metaharness_ai4pde`

`metaharness_nektar` forms an **independent graph**. It does not share nodes with `metaharness_ai4pde`. The two packages may coexist in the same runtime, but their component graphs are separate.

A future integration point could be an `ai4pde` solver family that delegates to Nektar++ as a classical backend, but this is not in scope for Phase 1.

### 18.3 `pyproject.toml` changes

Add to `MHE/pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel.packages]
# Existing:
"src/metaharness" = "metaharness"
"src/metaharness_ai4pde" = "metaharness_ai4pde"
# New:
"src/metaharness_nektar" = "metaharness_nektar"

[project.scripts]
# Existing:
metaharness = "metaharness.cli:main"
"metaharness-demo" = "metaharness_ai4pde.demo:main"
# New:
"nektar-demo" = "metaharness_nektar.__main__:demo"
```

## 19. Example Development Targets

Good early cases for template-driven support:

| Case | Solver | EQTYPE | Reference | Key BCs |
|------|--------|--------|-----------|---------|
| Helmholtz | ADR | `Helmholtz` | analytic | D + N |
| Poisson | ADR | `Poisson` | analytic | D + N |
| Advection–Diffusion | ADR | `SteadyAdvectionDiffusion` | analytic | D + N |
| Kovasznay flow | IncNS | `UnsteadyNavierStokes` | exact | D + periodic |
| 2D channel flow | IncNS | `UnsteadyNavierStokes` | parabolic profile | D (walls) + D (inlet) + N (outlet) |

These cover steady and unsteady flows, scalar and vector PDEs, exact/reference solutions, and boundary-condition diversity.

## 20. Testing Strategy

Tests should be layered.

### 20.1 Unit tests

For:

- session-plan compilation (typed models to XML sections),
- XML rendering (deterministic output, stable ordering),
- solver routing (enum validation, binary selection),
- log/filter parsing,
- expression variable validation,
- Robin BC PRIMCOEFF validation,
- boundary condition dimension checks.

### 20.2 Golden artifact tests

For:

- stable XML output from typed plans,
- stable post-processing command generation.

### 20.3 Integration tests

For:

- end-to-end case compilation and execution on small reference cases (Helmholtz, Poisson),
- success/failure validation branches,
- rerun after parameter mutation.

Integration tests that invoke real Nektar++ solvers should be marked `@pytest.mark.nektar` and skipped when the solver binary is not on PATH.

### 20.4 Negative tests

For:

- Robin BC missing `PRIMCOEFF`,
- invalid `equation_type` for a given `solver_family`,
- expression variables exceeding dimension (e.g., `z` in 2D),
- unsupported solver family requests,
- missing mesh inputs,
- periodic BC with mismatched region sizes.

## 21. Risks And Constraints

Important risks include:

- Nektar++ solver families encode many solver-specific semantics in `SOLVERINFO` and BC tags. The typed enum layer must track these accurately.
- Some workflows depend on auxiliary files beyond a single session XML (e.g., Womersley Fourier coefficients). Phase 1 should avoid these.
- Real mesh preparation can become the hardest part before solving starts. Phase 1 should rely on existing mesh files.
- Expression variables are dimension-strict. An agent generating `r` or `theta` or using `z` in 2D will silently get `-9999`. Validation must catch this.
- Process-level success may not imply numerical correctness. The validator must check actual field content, not just exit codes.
- XML generation without typed constraints will quickly become brittle. The section model layer is mandatory.

## 22. Recommended First Implementation Order

1. **types.py** — all enums (`NektarSolverFamily`, `NektarAdrEqType`, `NektarIncnsEqType`, `NektarProjection`, `NektarIncnsSolverType`, BC types).
2. **capabilities.py** — capability constants and `CANONICAL_CAPABILITIES` frozenset.
3. **slots.py** — slot ID constants.
4. **contracts.py** — all Pydantic models (`NektarProblemSpec`, `NektarMeshSpec`, `NektarExpansionSpec`, `NektarSessionPlan`, `NektarRunArtifact`, `FilterOutputSummary`, `NektarValidationReport`).
5. **xml_renderer.py** — section models + XML rendering (GeometrySection, ExpansionSection, ConditionsSection, BoundarySection, FunctionSection, ForcingSection, FilterSection) + Robin BC validation + expression variable validation.
6. **session_compiler.py** — `SessionCompilerComponent` compiling `NektarProblemSpec` to `NektarSessionPlan` and rendering XML.
7. **solver_executor.py** — `SolverRouterComponent` + `SolverExecutorComponent` for ADR and IncNS.
8. **postprocess.py** — `PostprocessComponent` with basic `FieldConvert` conversion + error extraction.
9. **validator.py** — `NektarValidatorComponent` consuming 3 Phase 1 evidence channels.
10. **analyzers.py** — log parser and FieldConvert output parser.
11. **nektar_gateway.py** — `NektarGatewayComponent` as entrypoint.
12. **tests** — golden XML tests, unit tests, negative tests, integration tests (marked `@pytest.mark.nektar`).

Only after steps 1–12 are stable:

13. add mesh preparation support through `NekMesh`,
14. add mutation and optimization helpers,
15. begin scaffold-generation support for new native solvers.

## 23. Bottom Line

The right way to build `metaharness_nektar` is to treat Nektar++ as a structured external execution substrate.

The agent should first become excellent at:

- compiling typed problem specs into valid Nektar++ session workflows,
- running those workflows reproducibly,
- reading back evidence,
- and iterating safely.

Once that loop is stable, the same architecture can be extended to help author genuinely new Nektar++ solver scaffolds.

That staged design is the shortest path to an agent that can eventually develop new solvers while still being able to run the whole workflow end to end from day one.
