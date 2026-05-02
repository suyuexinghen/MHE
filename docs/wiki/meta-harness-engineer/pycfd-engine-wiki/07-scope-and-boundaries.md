# 07. Scope and Boundaries

## 1. Wiki Responsibility

This wiki covers **how the PyCFD extension should be designed** — stable design boundaries that do not change with implementation progress:

- Extension positioning and MHE integration seams
- Component chain and data flow architecture
- Contract model shapes and validation surface
- Environment probe design and failure taxonomy
- Policy gate structure and decision logic
- Case type families and compiler template dispatch
- Package layout, exports, capabilities, slots, and manifests

This wiki is **not** the home for:
- Phase-by-phase implementation sequencing
- Current bug tracking or open issues
- Rollout milestone narration
- Test result logs (except the tested support matrix in 05-family-design)

## 2. Blueprint Responsibility

The blueprint (`blueprint/09-pycfd-extension-blueprint.md`) is the **formal design position** — a comprehensive analysis document that justifies design choices through analysis of the upstream PyCFD codebase, MHE architecture constraints, and comparison to existing extension patterns. It covers:

- Upstream PyCFD architecture analysis
- Integration interface selection rationale
- Complete component design with MHE pattern mapping
- Risk analysis and mitigation strategy

The blueprint is written once as a design reference and should not be continuously updated with implementation progress.

## 3. Roadmap Responsibility

The roadmap (`blueprint/09-pycfd-roadmap.md`) covers **phase sequencing and execution tracking**:

- Phase 0–5 execution order
- Per-phase goals, tasks, acceptance criteria
- Current completion status
- Test result summaries
- Risk/dependency table

The roadmap is the single source of truth for "what has been done and in what order." It is updated when phases complete but does not contain architectural rationale (that belongs in the blueprint).

## 4. What Is Explicitly Not in This Wiki

- **Upstream PyCFD documentation**: The PyCFD solver's user manual, theory guide, and API reference
- **PyCFD build/install guide**: How to clone and set up PyCFD — this is covered in the environment probe design but installation instructions belong upstream
- **MHE core architecture**: See `meta-harness-wiki/` for core component SDK, connection engine, safety governance, etc.
- **Daily development logs**: Implementation notes, debug sessions, and trial runs
- **Other extensions**: fealpy, nektar, deepmd, abacus, jedi, qcompute — each has its own wiki
- **Benchmark approval configs**: `.mhe/benchmarks/pycfd-approval.json` and similar runtime configs
- **Test implementation details**: Individual test case rationale belongs in test file docstrings
- **Non-PyCFD CFD solvers**: SU2, OpenFOAM, Nektar (incompressible), or any solver other than PyCFD
- **GPU acceleration**: PyCFD is CPU-only; GPU ports are out of scope
- **Mesh generation tools**: External mesh generation (Gmsh, Pointwise, etc.) is not covered

## 5. Relationship to `.trash/`

The PyCFD extension has no `.trash/` directory. All current wiki content is canonical and in active use.

## 6. Cross-References

| Document | Path | Purpose |
|---|---|---|
| PyCFD Blueprint | `blueprint/09-pycfd-extension-blueprint.md` | Formal design position |
| PyCFD Roadmap | `blueprint/09-pycfd-roadmap.md` | Execution tracking |
| PyCFD Handoff | `blueprint/09-pycfd-extension-handoff-report.md` | Continuation guide for new sessions |
| fealpy Extension Wiki | `fealpy-engine-wiki/` | Reference pattern for FEM extensions |
| MHE Core Wiki | `meta-harness-wiki/` | MHE architecture and component SDK |
