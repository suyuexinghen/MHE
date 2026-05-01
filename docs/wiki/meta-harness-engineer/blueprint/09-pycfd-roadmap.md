# PyCFD Extension Roadmap

> Status: complete | Formal execution roadmap for `metaharness_ext.pycfd`

## Technical Alignment Notes

- PyCFD is **not a pip package** — it lives at a configurable filesystem path (`PYCFD_SRC_PATH`). The environment probe validates the path; the compiler injects it into generated scripts.
- PyCFD solves the **2D Euler equations** (inviscid compressible flow) via cell-centered finite-volume with Roe flux and RK2 time-marching.
- Validation metrics are **residual norms and MMS truncation errors**, not FEM L2/H1 norms.
- PyCFD has no existing test suite — the MHE extension tests become the primary regression safety net.
- Mesh files are external for the airfoil case; all other cases use structured mesh generation added to the compiler.

## 1. Current State Snapshot

- **Code truth**: Extension fully implemented at `src/metaharness_ext/pycfd/` (15 production files).
- **Docs truth**: Blueprint analysis at `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-blueprint.md`.
- **Upstream PyCFD**: `run_pycfd_case()` function added to `Solvers.py` for JSON output.

## 2. Execution Order (Completed)

```
Phase 0 (PyCFD prep) → Phase 1 (Contracts+Env) → Phase 2 (Compiler+Executor)
    → Phase 3 (Validator+Evidence+Policy+Gateway) → Phase 4 (Benchmark) → Phase 5 (Study+Governance)
```

## 3. Phase Map

### Phase 0: PyCFD Upstream Preparation
- **Status**: complete
- **Goal**: Add JSON output and deterministic entry point to upstream PyCFD
- **Key tasks**:
  - Add `run_pycfd_case(config: dict) -> dict` function to `Solvers.py` ✓
  - Add JSON metrics line to stdout after solver completion ✓
  - Verify PyCFD runs under Python 3 with all 5 test cases ✓
- **Acceptance**: `python -c "from Solvers import run_pycfd_case; print(run_pycfd_case({...}))"` produces valid JSON ✓

### Phase 1: Core Contracts + Environment + Registration
- **Status**: complete
- **Goal**: Typed contract models, environment probe, capabilities/slots, and package skeleton
- **Key tasks**:
  - `types.py` — type aliases and enums ✓
  - `contracts.py` — 14 Pydantic models ✓
  - `slots.py` — 7 slot constants ✓
  - `capabilities.py` — 9 capability constants ✓
  - `environment.py` — `PyCFDEnvironmentProbeComponent` ✓
  - `__init__.py` — public re-exports ✓
  - Tests: contracts (13 tests), environment probe (3 tests) ✓
- **Acceptance**: All contract models validate correctly; environment probe detects PyCFD availability; tests pass ✓

### Phase 2: Compiler + Executor
- **Status**: complete
- **Goal**: Script generation for 5 case types and subprocess execution
- **Key tasks**:
  - `compiler.py` — 5 template renderers, deterministic plan_id via SHA256 ✓
  - `executor.py` — subprocess runner with timeout, JSON stdout parsing ✓
  - Tests: compiler templates (6 tests), executor with mocked subprocess (6 tests) ✓
- **Acceptance**: Compiler generates valid Python scripts for all 5 cases; executor runs scripts and parses JSON output ✓

### Phase 3: Validator + Evidence + Policy + Gateway
- **Status**: complete
- **Goal**: Validation, evidence assembly, policy gating, task intake
- **Key tasks**:
  - `validator.py` — residual-based validation (5 states: unavailable/timeout/failed/residual_exceeded/executed) ✓
  - `evidence.py` — evidence bundle assembly ✓
  - `policy.py` — 5-gate non-short-circuit policy chain ✓
  - `gateway.py` — task intake with case type validation and dotted-path overrides ✓
  - Tests: validator (8 tests), evidence+policy (8 tests), gateway (5 tests) ✓
- **Acceptance**: Full pipeline from gateway through policy works end-to-end; all tests pass ✓

### Phase 4: Benchmark Runner
- **Status**: complete
- **Goal**: 3-lane benchmark comparison (extension/direct/agent) with Claude CLI integration
- **Key tasks**:
  - `benchmark_cases.py` — `pycfd_case_catalog()` with 5 cases ✓
  - `benchmark_runner.py` — Full 3-lane runner with ClaudeCLIBrainProvider, `FakeClaudeCLIBrainProvider`, direct lane (script generation + subprocess execution), agent lane (spec proposal + preflight + repair attempts), extension lane (full MHE pipeline) ✓
  - `pycfd-pde` suite added to shared `BenchmarkSuite` and `SUITE_DIRS` ✓
  - Tests: benchmark cases (7 tests), benchmark runner (5 tests) ✓
- **Acceptance**: All 3 lanes produce `LaneSummary` results; dry-run mode passes ✓

### Phase 5: Study + Governance
- **Status**: complete
- **Goal**: Parameter sweeps and full MHE core governance integration with runtime backends
- **Key tasks**:
  - `study.py` — parameter sweep component with Cartesian product generation ✓
  - `governance.py` — Full MHE core governance adapter with `SessionStore`, `AuditLog`, `ProvGraph` runtime injection; `build_candidate_record()` with `GraphSnapshot`/`CandidateRecord`; `build_session_events()` via `make_session_event`; `emit_runtime_evidence()` with runtime backend integration ✓
  - Tests: study (6 tests), governance (11 tests including session store, prov graph, audit log, candidate record, policy gate issues), smoke (3 tests) ✓
- **Acceptance**: All tests passing, ruff clean ✓

## 4. Test Results

```
80 passed, 3 skipped (smoke tests requiring MHE_RUN_REAL_PYCFD=1) in 1.50s
ruff check: All checks passed
```

### Test File Summary

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
| **Total** | **83** | **80 passed, 3 skipped** |

### Production File Summary

| File | Lines | Purpose |
|------|-------|---------|
| types.py | ~55 | Type aliases, enums, status types |
| contracts.py | ~310 | 14 Pydantic contract models |
| slots.py | ~25 | 7 slot constants + protected set |
| capabilities.py | ~25 | 9 capability constants |
| environment.py | ~80 | Path-based PyCFD discovery probe |
| compiler.py | ~200 | 5-case script generator with SHA256 plan_id |
| executor.py | ~103 | Subprocess runner with JSON parsing |
| validator.py | ~149 | 5-state residual-based validation |
| evidence.py | ~60 | Evidence bundle assembly |
| policy.py | ~120 | 5-gate non-short-circuit policy chain |
| gateway.py | ~145 | Task intake with dotted-path overrides |
| benchmark_cases.py | ~95 | 5-case catalog |
| benchmark_runner.py | ~190 | 3-lane benchmark runner |
| study.py | ~190 | Parameter sweep component |
| governance.py | ~99 | MHE core governance adapter |
| __init__.py | ~45 | Public API re-exports |

## 5. Risks / Dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| PyCFD Python 2/3 syntax issues | Medium | Fix syntax errors upstream; test with Python 3.12 |
| Mesh files not portable | Medium | Bundle mesh files; add structured mesh generation to compiler |
| PyCFD path fragility | Medium | Environment probe validates path; compiler uses absolute paths |
| No upstream test suite | Low | MHE extension tests serve as regression suite |
| Residual norms differ from FEM errors | Low | Design validation gates appropriate to FVM explicit solvers |
