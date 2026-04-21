# NEKTAR_BLUEPRINT Feasibility & Rigor Review

Date: 2026-04-20
Reviewed: `MHE/docs/NEKTAR_BLUEPRINT.md` (625 lines)

---

## Verdict

**Feasible with corrections.** The overall staged approach (typed contracts → XML rendering → execution → validation → mutation → scaffolding) is sound and well-aligned with existing MHE patterns. However, there are 6 factual inaccuracies, 4 structural gaps, and 3 logical tensions that must be resolved before implementation.

---

## 1. Factual Inaccuracies Against Nektar++ Documentation

### 1.1 GEOMETRY section model is incomplete (Section 11)

**Blueprint says:** `GeometrySection` implicitly covers `VERTEX`, `EDGE`, `COMPOSITE`, `DOMAIN`.

**Reality:** GEOMETRY has 7 sub-elements: `VERTEX`, `EDGE`, `FACE`, `ELEMENT`, `CURVED`, `COMPOSITE`, `DOMAIN`.
- `EDGE` is only required for DIM ≥ 2.
- `FACE` is only required for DIM = 3.
- `ELEMENT` is always present.
- `CURVED` is required when high-order curved entities exist.

**Impact:** The `GeometrySection` model in Section 11 must include `FACE`, `ELEMENT`, and `CURVED` fields. A 3D case will fail if these are missing.

**Fix:** Expand `GeometrySection` to:
```python
class GeometrySection(BaseModel):
    dimension: int
    space_dimension: int
    vertices: list[VertexDef]
    edges: list[EdgeDef] = []
    faces: list[FaceDef] = []       # required for 3D
    elements: list[ElementDef]
    curved: list[CurvedDef] = []    # required for high-order
    composites: list[CompositeDef]
    domain: list[str]
```

### 1.2 BC type "R" requires PRIMCOEFF, not documented in ch03

**Blueprint says (Section 11, 8.7):** BC types are `D` (Dirichlet), `N` (Neumann), `R` (Robin), `P` (Periodic).

**Reality:**
- `D`, `N`, `P` are documented in `ch03-XML-guide.md:323-409`.
- `R` exists and works (confirmed in `ch07-ADR` examples) but **requires a `PRIMCOEFF` attribute**. There is no standalone Robin section in ch03.
- Additionally, many solver-specific `USERDEFINEDTYPE` values exist beyond what the blueprint mentions: `H`, `HOutflow`, `TimeDependent`, `Womersley`, `MovingBody`, `Flowrate`, `Rotated`.

**Impact:** The `BoundarySection` model must encode `PRIMCOEFF` for Robin BCs and `USERDEFINEDTYPE` semantics. Validation logic must reject Robin BCs missing `PRIMCOEFF`.

### 1.3 Expression variables are more restricted than implied

**Blueprint says (Section 19):** "misuse yields undefined behavior (`-9999` placeholders)."

**Reality (ch03:1215-1220):** Available spatial variables are strictly `x` (1D), `x,y` (2D), `x,y,z` (3D). There are **no** `r`, `theta`, `phi` native expression variables. The functions `rad(x,y)` and `ang(x,y)` exist as math functions, not spatial variables. `r` appears only as a special EVARS attribute in Absorption forcing.

**Impact:** The `FunctionSection` model must validate expression variable usage against dimension. An agent generating `r` or `theta` in expressions would silently get `-9999` in some coordinates.

### 1.4 NektarSessionPlan.solver_info uses raw dict instead of structured model

**Blueprint says (Section 7.4):** `solver_info: dict[str, str]`.

**MHE reality:** `contracts.py` uses typed enums for all solver-family selections (`SolverFamily` enum). Raw `dict[str, str]` contradicts the established pattern and loses type safety at the most critical configuration surface.

**Impact:** `solver_info` should be modeled as a structured type with validated keys/values per solver family, not an opaque dict. At minimum, `equation_type` and `projection` should be enums.

### 1.5 NektarProblemSpec.equation_family is a free-form string

**Blueprint says (Section 7.1):** `equation_family: str`.

**MHE reality:** `types.py` defines `SolverFamily(str, Enum)` with narrow values. A free-form string here means the session compiler has no compile-time guarantee that the request is routable.

**Impact:** Should be a `Literal` union or `Enum` covering at least `"adr"`, `"incns"`, `"compressible"`, `"elasticity"`, `"cardiac_ep"`, `"pulse_wave"`, `"shallow_water"`, `"acoustic"`.

### 1.6 ADR EQTYPE list in the roadmap is incomplete

**Blueprint says (Section 15):** Phase 1 supports "ADRSolver" generically.

**Reality:** ADR supports 12 distinct EQTYPE values: `Projection`, `Laplace`, `Poisson`, `Helmholtz`, `SteadyAdvectionDiffusion`, `SteadyDiffusionReaction`, `SteadyAdvectionDiffusionReaction`, `UnsteadyAdvection`, `UnsteadyDiffusion`, `UnsteadyReactionDiffusion`, `UnsteadyAdvectionDiffusion`, `UnsteadyInviscidBurger`. The blueprint should explicitly enumerate which EQTYPEs Phase 1 supports.

---

## 2. Structural Gaps

### 2.1 Missing slot definitions

Every `metaharness_ai4pde` component has a corresponding slot in `slots.py` (e.g., `PDE_GATEWAY_SLOT`, `SOLVER_EXECUTOR_SLOT`). The blueprint proposes 7 components but never defines their slot IDs or connection topology.

**Fix:** Add a `slots.py` section with constants for each component slot and a graph topology diagram showing which component connects to which.

### 2.2 No manifest or discovery integration

The MHE boot system (`boot.py`) discovers components through manifests. The blueprint never mentions how `metaharness_nektar` components get discovered, what their manifest looks like, or how they interact with the existing `metaharness_ai4pde` graph.

**Fix:** Add a section on manifest design and whether `metaharness_nektar` forms an independent graph or shares nodes with `metaharness_ai4pde`.

### 2.3 No `pyproject.toml` integration plan

The current `MHE/pyproject.toml` builds `metaharness` and `metaharness_ai4pde` as separate packages. Adding `metaharness_nektar` requires a second `packages` entry and likely a new console script. The blueprint does not mention this.

**Fix:** Add a section on build/packaging integration.

### 2.4 `NektarRunArtifact.filter_outputs: dict[str, Any]` is underspecified

The blueprint says filter outputs are `dict[str, Any]` but Nektar++ filters produce diverse output types: checkpoint files, history point CSVs, energy norms, moving-body forces, FieldConvert-intermediate files, etc. A `dict[str, Any]` gives no guidance on what keys to expect.

**Fix:** Define at least a `FilterOutputSummary` model with typed fields for common filter categories (checkpoint, history_points, energy, errors).

---

## 3. Logical Tensions

### 3.1 "Six layers" vs. "five layers implemented first"

Section 4 lists 6 layers but says "the first release should fully implement the first five." However, the extension/scaffolding layer is listed as layer 6 and is explicitly deferred. The remaining 5 layers (problem specification, compilation, execution, post-processing, validation) are reasonable. This is fine structurally but the wording implies 5 layers will ship in one release, which is unrealistic for an MVP.

**Recommendation:** Clarify that Phase 1 implements compilation + execution + validation only, and that problem specification and post-processing are partial.

### 3.2 Package layout has 30+ files for a "minimum viable" module

The recommended layout in Section 5 lists `analyzers/` (5 files), `mutations/` (4 files), `executors/` (4 files), `templates/` (3 files), and `components/` (7 files). That is 25+ source files before tests. For an MVP targeting 2 solver families, this is overbuilt.

**Recommendation:** Start with a flat layout:
```
metaharness_nektar/
├── __init__.py
├── contracts.py
├── types.py
├── capabilities.py
├── slots.py
├── xml_renderer.py
├── session_compiler.py
├── solver_executor.py
├── postprocess.py
├── validator.py
└── analyzers.py
```
Refactor into subpackages only when the flat file grows unwieldy.

### 3.3 Validation strategy claims too many channels for Phase 1

Section 13 lists 7 evidence channels. For Phase 1 (ADR + IncNS), only 3 are reliably available:
1. process exit code + stdout/stderr,
2. `.fld`/`.chk` existence,
3. `FieldConvert`-derived error against an exact solution.

Filter outputs, convergence signals, conservation checks, and boundary-condition consistency are either solver-specific or require running `FieldConvert` with specific modules. The blueprint should be honest that Phase 1 validation is limited to these 3 channels.

---

## 4. Alignment With Existing MHE Patterns

| Aspect | Blueprint | MHE Reality | Verdict |
|--------|-----------|-------------|---------|
| Pydantic v2 BaseModel contracts | Yes | Yes | Aligned |
| `task_id` on every model | Yes | Yes | Aligned |
| `str, Enum` types | No (uses free-form strings) | Yes | **Misaligned** |
| Dotted-string capabilities | Yes | Yes (`ai4pde.<cat>.<name>`) | Aligned |
| `HarnessComponent` subclass | Implied but not shown | Explicit in all components | Gap |
| Slot-based graph topology | Not defined | Explicit in `slots.py` | **Missing** |
| `protected` component flag | Not mentioned | Used for reference solver | Gap |
| `activate`/`deactivate` lifecycle | Not shown | Required | Gap |
| `pyproject.toml` packaging | Not mentioned | Required for discovery | **Missing** |

---

## 5. Recommendations Summary

### Must fix before implementation

1. **Type-enforce `equation_family`, `solver_info`, `equation_type`** — use enums or Literals, not raw strings.
2. **Add `slots.py`** — define slot constants and graph topology.
3. **Expand `GeometrySection`** — include FACE, ELEMENT, CURVED fields.
4. **Add manifest/packaging section** — show how the package integrates with MHE boot.

### Should fix for quality

5. **Flatten the MVP layout** — start with ~10 files, not 30+.
6. **Model Robin BC's `PRIMCOEFF`** — add to `BoundarySection` validation.
7. **Constrain expression variables by dimension** — validate in `FunctionSection`.
8. **Narrow Phase 1 validation** — be explicit about which evidence channels are actually available.
9. **Enumerate Phase 1 EQTYPEs** — list exact ADR and IncNS equation types supported.

### Nice to have

10. **Define `FilterOutputSummary`** — typed summary of common filter outputs.
11. **Add graph topology diagram** — ASCII or mermaid showing component connections.
12. **Add `protected` component annotations** — mark which components should not be hot-swapped.

---

## 6. Overall Assessment

The blueprint is **directionally correct** and its core design principle (typed models as internal truth, XML as external artifact) is exactly right. The staged roadmap (case compilation → execution → validation → mutation → scaffolding) is well-ordered.

The main risks are:
- Over-engineering the initial package layout (too many files for MVP scope),
- Under-specifying the type constraints (raw strings where enums are needed),
- Missing MHE integration details (slots, manifests, packaging).

With the 4 must-fix items addressed, the blueprint is ready to serve as an implementation reference.
