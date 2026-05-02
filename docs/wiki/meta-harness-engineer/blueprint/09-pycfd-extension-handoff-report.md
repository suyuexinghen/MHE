# PyCFD Extension Handoff Report

> Purpose: Provide a directly actionable continuation guide for a new Claude Code conversation window.
> Scope: `MHE/src/metaharness_ext/pycfd/`, corresponding tests, wiki, manifests, and blueprint.
> Status baseline: Phase 0–5 complete. 80 tests pass, 3 smoke gated, ruff clean. No remaining placeholders.

---

## 1. Current Task Background

The PyCFD extension integrates [PyCFD](https://github.com/linden/PyCFD) — a 2D Euler finite-volume solver (cell-centered FVM, Roe flux, RK2 time-marching, unstructured hybrid meshes) — as a controlled, typed, verifiable MHE component chain:

- `gateway → environment → compiler → executor → validator → evidence → policy`
- Control surface: 5 case types (vortex-2d, airfoil-2d, cylinder-2d, mms-2d, shock-diffraction-2d)
- Evidence surface: L1/L2 residual norms, wall time, mesh statistics, iterations
- Validation: residual-based tolerance checks (not FEM error norms)

The extension is **fully implemented** across all 6 roadmap phases. Current state is stable with complete test coverage.

## 2. Completed Progress

### 2.1 Documentation

- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-blueprint.md` — comprehensive analysis blueprint
- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-roadmap.md` — Phase 0–5 execution roadmap (status: complete)
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/README.md` — wiki router
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/01-overview.md` through `07-scope-and-boundaries.md` — 8-page design wiki
- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-handoff-report.md` — this document

### 2.2 Production Code (15 files)

| File | Lines | Purpose |
|------|-------|---------|
| `types.py` | ~55 | Type aliases, enums (PyCFDValidationStatus) |
| `contracts.py` | ~310 | 14 Pydantic models |
| `slots.py` | ~25 | 7 slot constants + PROTECTED_SLOTS |
| `capabilities.py` | ~25 | 9 capability constants |
| `environment.py` | ~80 | Path-based PyCFD discovery probe |
| `compiler.py` | ~200 | 5-case template renderer with SHA256 plan_id |
| `executor.py` | ~103 | Subprocess runner with JSON stdout parsing |
| `validator.py` | ~149 | 5-state residual-based validation (protected) |
| `evidence.py` | ~60 | Evidence bundle assembly |
| `policy.py` | ~120 | 5-gate non-short-circuit policy chain |
| `gateway.py` | ~145 | Task intake with dotted-path overrides |
| `benchmark_cases.py` | ~95 | 5-case catalog |
| `benchmark_runner.py` | ~190 | 3-lane benchmark runner |
| `study.py` | ~190 | Parameter sweep (Cartesian product) |
| `governance.py` | ~99 | MHE core governance adapter |

### 2.3 Manifests (6 files)

- `examples/manifests/pycfd/pycfd_gateway.json`
- `examples/manifests/pycfd/pycfd_environment.json`
- `examples/manifests/pycfd/pycfd_compiler.json`
- `examples/manifests/pycfd/pycfd_executor.json`
- `examples/manifests/pycfd/pycfd_validator.json`
- `examples/manifests/pycfd/pycfd_study.json`

### 2.4 Test Suite (12 files, 83 tests)

```
80 passed, 3 skipped (smoke tests requiring MHE_RUN_REAL_PYCFD=1)
ruff check: All checks passed
```

| Test file | Tests | Status |
|-----------|-------|--------|
| test_metaharness_pycfd_contracts.py | 13 | ✓ |
| test_metaharness_pycfd_environment.py | 3 | ✓ |
| test_metaharness_pycfd_compiler.py | 6 | ✓ |
| test_metaharness_pycfd_executor.py | 6 | ✓ |
| test_metaharness_pycfd_validator.py | 8 | ✓ |
| test_metaharness_pycfd_evidence_policy.py | 8 | ✓ |
| test_metaharness_pycfd_gateway.py | 5 | ✓ |
| test_metaharness_pycfd_benchmark_cases.py | 7 | ✓ |
| test_metaharness_pycfd_benchmark_runner.py | 5 | ✓ |
| test_metaharness_pycfd_study.py | 6 | ✓ |
| test_metaharness_pycfd_governance.py | 11 | ✓ |
| test_metaharness_pycfd_smoke.py | 3 | skipped (opt-in) |

### 2.5 Upstream PyCFD Change

`run_pycfd_case(config: dict) -> dict` was added to `Solvers.py` in the upstream PyCFD repository. This function:
- Creates DataHandler with default params
- Creates Grid with `generated=True`
- Creates Solvers, overrides params directly (bypassing input.nml)
- Boots, solves, computes residuals
- Prints `json.dumps(result)` to stdout for MHE executor parsing

## 3. Key Implementation Details

### 3.1 Architecture Pattern

PyCFD follows the same gateway-oriented pipeline as fealpy:

```
PyCFDGateway.issue_task(spec) → PyCFDEnvironmentProbe.probe(task_id) → PyCFDCompiler.compile(spec) → PyCFDExecutor.execute(plan) → PyCFDValidator.validate(artifact, plan_ref) → build_evidence_bundle(...) → PyCFDEvidencePolicy.evaluate(bundle)
```

### 3.2 Critical Differences from fealpy

| Aspect | fealpy | PyCFD |
|--------|--------|-------|
| Integration | pip package import | Path-based discovery (`PYCFD_SRC_PATH`) |
| Physics | FEM (18 PDE families) | 2D Euler FVM (5 case types) |
| Validation | L2/H1 error norms vs exact solution | L1/L2 residual norms |
| Config format | Dict-based PDE spec | Dict-based FVM config |
| Plan ID | SHA256 of spec JSON | SHA256 of spec JSON (same pattern) |
| Policy gates | 5-gate non-short-circuit | 5-gate non-short-circuit (same pattern) |

### 3.3 Path Resolution (executor.py fix)

The executor constructs `script_path = workspace / "solve.py"` (relative to workspace). The subprocess is run with `cwd=str(workspace)`. The fix applied: `str(script_path.resolve())` ensures the script path is absolute before passing to subprocess.run, preventing doubled relative paths.

### 3.4 Validator Design

The validator checks 5 states in priority order:
1. `unavailable` → `ENVIRONMENT_UNAVAILABLE`
2. `timeout` → `RUNTIME_FAILED`
3. `failed` → `RUNTIME_FAILED`
4. L1 residual exceeds tolerance → `RESIDUAL_EXCEEDED`
5. L2 residual exceeds tolerance → `RESIDUAL_EXCEEDED`
6. All pass → `EXECUTED`

Both residuals must be present AND within tolerance for `passed=True`. Missing residuals (None) are treated as failure.

### 3.5 Summary Metrics Filtering

`summary_metrics` in `PyCFDValidationReport` uses `dict[str, object]` type and filters out None values before inclusion to avoid Pydantic validation errors.

### 3.6 Benchmark Runner (3-Lane)

`PyCFDBenchmarkRunner` follows the fealpy `FealpyBenchmarkRunner` pattern with full Claude CLI integration:

- **Extension lane**: Full MHE pipeline (compile → execute → validate → evidence). Dry-run produces synthetic evidence.
- **Direct lane**: Claude (`ClaudeCLIBrainProvider`/`FakeClaudeCLIBrainProvider`) generates a raw Python script. Preflight validates `solve_py` extraction. Script executes via subprocess with timeout; metrics parsed from JSON stdout.
- **Agent lane**: Claude proposes `pycfd_spec` or `spec_patch`. Preflight validates spec construction. Pipeline runs the proposed spec. Repair loop (configurable `max_repair_attempts`) re-prompts Claude on validation failure.
- All lanes return `LaneSummary` from `write_lane_outputs()`.
- `pycfd-pde` suite added to shared `BenchmarkSuite` literal and `SUITE_DIRS`.

### 3.7 Governance Adapter (Runtime-Injected)

`PyCFDGovernanceAdapter` follows the fealpy `FealpyGovernanceAdapter` pattern with full runtime backend integration:

- `build_core_validation_report()` — merges validation issues + policy gate issues into MHE core `ValidationReport`.
- `build_candidate_record()` — constructs `CandidateRecord` with `GraphSnapshot`, resolves `candidate_id` from metadata/plan/artifact.
- `build_session_events()` — emits `CANDIDATE_VALIDATED`, `SAFETY_GATE_EVALUATED`, and `CANDIDATE_REJECTED` events via `make_session_event()`.
- `emit_runtime_evidence()` — persists to `SessionStore` (append events), `AuditLog` (append records with Merkle anchoring), and `ProvGraph` (add entities + `WAS_DERIVED_FROM` relations). Returns `audit_refs` and `provenance_refs`.
- `_policy_gate_issues()` — extracts `ValidationIssue` list from dict-based policy gates, mapping `result: "reject"` → `blocks_promotion=True`.

## 4. Completion Status

The PyCFD extension is **fully complete** — no remaining placeholders or blocked items. All 80 tests pass, 3 smoke tests gated behind `MHE_RUN_REAL_PYCFD=1`.

### 4.1 What Was Previously Outstanding (Now Done)

1. ~~Wire up direct/agent benchmark lanes~~ — Done. Full Claude CLI integration with `FakeClaudeCLIBrainProvider` for tests, preflight validation, repair loops.
2. ~~Add governance runtime injection~~ — Done. `SessionStore`, `AuditLog`, `ProvGraph` all integrated in `emit_runtime_evidence()`.
3. ~~Copy blueprint to canonical path~~ — Done. Blueprint copied to `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-blueprint.md`. Wiki, manifests, and handoff report all in canonical locations.

## 5. Optional Remaining Work

These are non-blocking quality-of-life improvements:

1. ~~**Add `pycfd-pde` benchmark approval config** at `.mhe/benchmarks/pycfd-approval.json`~~ — Done.
2. ~~**Create comparison benchmark config** at `.mhe/benchmarks/comparison-approval.json`~~ — Done (pycfd-pde conditional profile added).
3. **Run real smoke tests** with `MHE_RUN_REAL_PYCFD=1` against actual PyCFD installation

## 6. Workspace Constraints

When working in new sessions:
- Work within `MHE/src/metaharness_ext/pycfd/`, `MHE/tests/test_metaharness_pycfd_*.py`, `MHE/examples/manifests/pycfd/`, `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/`, and `MHE/docs/wiki/meta-harness-engineer/blueprint/`
- Do not modify other extensions' code or docs
- Do not reintroduce the executor path bug (always use `script_path.resolve()`)

## 7. Reference Document Index

### 7.1 PyCFD Wiki
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/README.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/01-overview.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/02-workflow-and-components.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/03-contracts-and-artifacts.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/04-environment-validation-and-evidence.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/05-family-design.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/06-packaging-and-registration.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/07-scope-and-boundaries.md`

### 7.2 Blueprint / Roadmap
- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-roadmap.md`

### 7.3 Code
- `MHE/src/metaharness_ext/pycfd/` (15 files)
- `MHE/tests/test_metaharness_pycfd_*.py` (12 files)
- `MHE/examples/manifests/pycfd/` (6 files)

### 7.4 Reference Extension
- `MHE/src/metaharness_ext/fealpy/` — primary pattern reference for MHE extension architecture

## 8. Prompt for New Conversation

```markdown
Continue working on the PyCFD MHE extension at `MHE/src/metaharness_ext/pycfd/`.

Read first:
- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-handoff-report.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/09-pycfd-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/README.md`

Current state:
- Phase 0–5 complete. 80 tests pass, 3 smoke gated, ruff clean.
- 15 production files, 12 test files, 6 manifests, 8 wiki pages.
- Benchmark runner: full 3-lane implementation with Claude CLI integration complete.
- Governance adapter: full MHE runtime injection (SessionStore, AuditLog, ProvGraph) complete.

Work only within:
- `MHE/src/metaharness_ext/pycfd/`
- `MHE/tests/test_metaharness_pycfd_*.py`
- `MHE/examples/manifests/pycfd/`
- `MHE/docs/wiki/meta-harness-engineer/pycfd-engine-wiki/`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/`

Constraints:
- Never use relative script paths in executor (always `script_path.resolve()`)
- Validator is protected (`protected = True`)
- PyCFD is NOT a pip package — always use path-based discovery
- Keep ruff clean, all tests passing
```

---

## 9. Conclusion

The PyCFD extension is **fully complete** with no remaining placeholders or blocked items. All 15 production files follow the canonical MHE extension pattern (modeled after fealpy). The 6 manifests enable MHE core registration. The 8-page wiki provides stable design boundary documentation.

**Key deliverables:**
- 15 production files (gateway → environment → compiler → executor → validator → evidence → policy → study → governance → benchmark)
- 12 test files (83 tests: 80 pass, 3 smoke gated)
- 6 manifests under `examples/manifests/pycfd/`
- 8 wiki pages under `docs/wiki/meta-harness-engineer/pycfd-engine-wiki/`
- 1 blueprint, 1 roadmap, 1 handoff report
- 1 upstream PyCFD change (`run_pycfd_case()` in `Solvers.py`)
- 2 shared infrastructure changes (`BenchmarkSuite` + `SUITE_DIRS` for `pycfd-pde`)

**Benchmark runner**: Full 3-lane implementation with Claude CLI integration (extension/direct/agent), preflight validation, repair loops, `FakeClaudeCLIBrainProvider` for testing.

**Governance adapter**: Full MHE core integration with `SessionStore`, `AuditLog` (Merkle-anchored), `ProvGraph` (PROV-O entities + relations), `CandidateRecord`/`GraphSnapshot` construction, and `make_session_event` emission.
