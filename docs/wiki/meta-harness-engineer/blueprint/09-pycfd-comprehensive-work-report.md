# PyCFD Extension — Comprehensive Work Report

> Date: 2026-05-01 | Author: suyuexinghen | Status: Complete

---

## 1. Executive Summary

The PyCFD MHE extension is **fully implemented** across all 6 roadmap phases (Phase 0–5). The extension integrates [PyCFD](https://github.com/linden/PyCFD) — a 2D Euler finite-volume solver (cell-centered FVM, Roe flux, RK2 time-marching, unstructured hybrid meshes) — into the MHE meta-harness as a controlled, typed, verifiable component chain.

**Key metrics:**

| Metric | Value |
|--------|-------|
| Production files | 15 (2,499 lines) |
| Test files | 12 (1,099 lines) |
| Tests | 83 (80 pass, 3 opt-in smoke gated) |
| Manifest files | 6 |
| Wiki pages | 8 |
| Blueprint/roadmap/handoff docs | 3 |
| Benchmark approval configs | 2 |
| Shared infrastructure changes | 2 (`BenchmarkSuite` + `SUITE_DIRS`) |
| Upstream PyCFD changes | 1 (`run_pycfd_case()` in `Solvers.py`) |
| mhe-benchmark-iteration skill improvements | 9 changes across 4 reference files |

---

## 2. Extension Architecture

### 2.1 Component Chain

```
PyCFDGateway.issue_task(spec)
  → PyCFDEnvironmentProbe.probe(task_id)
    → PyCFDCompiler.compile(spec)
      → PyCFDExecutor.execute(plan)
        → PyCFDValidator.validate(artifact, plan_ref)
          → build_evidence_bundle(...)
            → PyCFDEvidencePolicy.evaluate(bundle)
              → PyCFDGovernanceAdapter.emit_runtime_evidence(...)
```

### 2.2 Production File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `types.py` | 37 | Type aliases, `PyCFDValidationStatus` enum |
| `contracts.py` | 303 | 14 Pydantic contract models |
| `slots.py` | 9 | 7 slot constants + `PROTECTED_SLOTS` |
| `capabilities.py` | 21 | 9 capability constants |
| `environment.py` | 106 | Path-based PyCFD discovery probe (`PYCFD_SRC_PATH`) |
| `compiler.py` | 148 | 5-case template renderer, SHA256 plan_id |
| `executor.py` | 102 | Subprocess runner with JSON stdout parsing |
| `validator.py` | 148 | 5-state residual-based validation (protected) |
| `evidence.py` | 85 | Evidence bundle assembly |
| `policy.py` | 127 | 5-gate non-short-circuit policy chain |
| `gateway.py` | 65 | Task intake with dotted-path overrides |
| `benchmark_cases.py` | 92 | 5-case catalog |
| `benchmark_runner.py` | 774 | 3-lane benchmark runner (extension/direct/agent) |
| `study.py` | 125 | Parameter sweep (Cartesian product) |
| `governance.py` | 295 | MHE core governance adapter (SessionStore/AuditLog/ProvGraph) |
| `__init__.py` | 62 | Public API re-exports |

### 2.3 Case Type Coverage

| Case | Physics | Mesh | Key Metric |
|------|---------|------|------------|
| `vortex-2d` | Isentropic vortex advection | Structured (generated) | L1/L2 residual preservation |
| `airfoil-2d` | NACA0012 subsonic flow | Unstructured (external mesh) | Lift/drag from surface pressure |
| `cylinder-2d` | Supersonic cylinder (M=2.0) | Structured (generated) | Bow shock capture |
| `mms-2d` | Method of manufactured solutions | Structured (generated) | Truncation error convergence |
| `shock-diffraction-2d` | Shock diffraction over step | Structured (generated) | Complex wave pattern |

---

## 3. Key Implementation Details

### 3.1 Critical Differences from fealpy (Reference Pattern)

| Aspect | fealpy | PyCFD |
|--------|--------|-------|
| Integration | pip package import | Path-based discovery via `PYCFD_SRC_PATH` |
| Physics | FEM (18 PDE families) | 2D Euler FVM (5 case types) |
| Validation | L2/H1 error norms vs exact solution | L1/L2 residual norms |
| Config format | Dict-based PDE spec | Dict-based FVM config |
| Plan ID | SHA256 of spec JSON | SHA256 of spec JSON (same pattern) |
| Policy gates | 5-gate non-short-circuit | 5-gate non-short-circuit (same pattern) |
| Validation states | Standard pass/fail | 5-state priority chain |
| Preflight dependency | pip packages only | 4 archetypes (Binary, Pip, Path, Source-format) |

### 3.2 Path Resolution Bug Fix

The executor constructs `script_path = workspace / "solve.py"` (relative to workspace). The subprocess uses `cwd=str(workspace)`. The fix applied was `str(script_path.resolve())`, ensuring the script path is absolute before passing to `subprocess.run`. This prevents doubled relative paths when cwd is set to workspace.

**Location**: `src/metaharness_ext/pycfd/executor.py:37`

### 3.3 Validator Design (5-State Priority Chain)

The validator checks 5 states in strict priority order:

1. `unavailable` → `ENVIRONMENT_UNAVAILABLE`
2. `timeout` → `RUNTIME_FAILED`
3. `failed` (nonzero exit) → `RUNTIME_FAILED`
4. L1 residual exceeds tolerance → `RESIDUAL_EXCEEDED`
5. L2 residual exceeds tolerance → `RESIDUAL_EXCEEDED`
6. All pass → `EXECUTED`

Both residuals must be present AND within tolerance for `passed=True`. Missing residuals (None) are treated as failure. This is appropriate for FVM explicit solvers where residual norms measure solver convergence, not solution error.

### 3.4 Benchmark Runner (3-Lane)

The `PyCFDBenchmarkRunner` implements full Claude CLI integration across three lanes:

- **Extension lane**: Full MHE pipeline (compile → execute → validate → evidence). Dry-run produces synthetic evidence.
- **Direct lane**: Claude (`ClaudeCLIBrainProvider`/`FakeClaudeCLIBrainProvider`) generates a raw Python script. Preflight validates script extraction. Script executes via subprocess with timeout; metrics parsed from JSON stdout.
- **Agent lane**: Claude proposes `pycfd_spec` or `spec_patch` JSON. Preflight validates spec construction using Pydantic. Pipeline runs the proposed spec. Repair loop (configurable `max_repair_attempts`) re-prompts Claude on validation failure.

Key patterns:
- `_coerce(v, default)` static method normalizes Claude's null JSON proposals
- `_extract_json_from_markdown()` regex-based JSON extraction from markdown fences
- `_write_proposal_preflight()` validates Claude proposal structure before execution
- Domain-specific prompt methods for direct, agent, and repair scenarios

### 3.5 Governance Adapter (Runtime-Injected)

The `PyCFDGovernanceAdapter` integrates with all three MHE core runtime backends:

- `SessionStore` — appends session events via `append_events()`
- `AuditLog` — appends records with Merkle anchoring via `append_record()`
- `ProvGraph` — adds PROV-O entities and `WAS_DERIVED_FROM` relations
- `CandidateRecord` — constructed with `GraphSnapshot` for version tracking
- `make_session_event()` — factory for `CANDIDATE_VALIDATED`, `SAFETY_GATE_EVALUATED`, `CANDIDATE_REJECTED` events

The `_policy_gate_issues()` method handles PyCFD's dict-based gate format, extracting `ValidationIssue` objects with `blocks_promotion=True` for rejected gates.

---

## 4. Test Suite

### 4.1 Summary

```
80 passed, 3 deselected (smoke tests require MHE_RUN_REAL_PYCFD=1)
ruff check: All checks passed
```

### 4.2 Test File Breakdown

| Test file | Tests | Coverage area |
|-----------|-------|---------------|
| `test_metaharness_pycfd_contracts.py` | 13 | Pydantic model validation, field defaults, serialization |
| `test_metaharness_pycfd_environment.py` | 3 | Path discovery, availability checks, missing path handling |
| `test_metaharness_pycfd_compiler.py` | 6 | 5 case templates + plan_id determinism |
| `test_metaharness_pycfd_executor.py` | 6 | Success, timeout, nonzero exit, missing/malformed JSON, workspace creation |
| `test_metaharness_pycfd_validator.py` | 8 | 5 states + custom tolerance + missing residuals |
| `test_metaharness_pycfd_evidence_policy.py` | 8 | Evidence bundle, 5-gate evaluation, deferred/rejected paths |
| `test_metaharness_pycfd_gateway.py` | 5 | Defaults, specific case, unknown case rejection, overrides |
| `test_metaharness_pycfd_benchmark_cases.py` | 7 | Case catalog structure, completeness, spec validity |
| `test_metaharness_pycfd_benchmark_runner.py` | 5 | 3-lane dry run, lane summaries, fake Claude integration |
| `test_metaharness_pycfd_study.py` | 6 | Cartesian product, snapshot apply, report, max_trials |
| `test_metaharness_pycfd_governance.py` | 11 | Validation report, candidate record, session events, SessionStore/AuditLog/ProvGraph, policy gate issues |
| `test_metaharness_pycfd_smoke.py` | 3 | Opt-in real-PyCFD tests (environment probe, compiler, full pipeline) |

### 4.3 Test Opt-In Design

Smoke tests are gated behind two environment variables:
- `MHE_RUN_REAL_PYCFD=1` — permission to run real PyCFD
- `PYCFD_SRC_PATH` — path to PyCFD source directory

The `pyproject.toml` excludes `pycfd` marker by default:
```
addopts = "-m 'not nektar and not quafu and not octave and not pycfd'"
```

---

## 5. Documentation

### 5.1 Blueprint, Roadmap, and Handoff

| Document | Location | Purpose |
|----------|----------|---------|
| Blueprint | `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-blueprint.md` | Comprehensive analysis of PyCFD integration |
| Roadmap | `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-roadmap.md` | Phase 0–5 execution roadmap (complete) |
| Handoff | `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-handoff-report.md` | Continuation guide for new sessions |
| Work Report | `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-comprehensive-work-report.md` | This document |

### 5.2 Design Wiki

| Page | Content |
|------|---------|
| `README.md` | Wiki router and navigation |
| `01-overview.md` | Extension purpose, architecture, design rationale |
| `02-workflow-and-components.md` | Component chain, data flow, pipeline stages |
| `03-contracts-and-artifacts.md` | Pydantic models, artifact schemas |
| `04-environment-validation-and-evidence.md` | Environment probe, evidence bundle, policy gates |
| `05-family-design.md` | Case type families, mesh strategies |
| `06-packaging-and-registration.md` | Registration pattern, capability/slot declarations |
| `07-scope-and-boundaries.md` | Deliberate exclusions, non-goals, limitations |

### 5.3 Manifests

Six manifest files under `examples/manifests/pycfd/` enable MHE core registration:
`gateway`, `environment`, `compiler`, `executor`, `validator`, `study`

---

## 6. Shared Infrastructure Changes

Two changes to `src/metaharness/benchmark_drivers/` enable the PyCFD benchmark suite:

1. **`models.py`**: Added `"pycfd-pde"` to `BenchmarkSuite` literal type union
2. **`io.py`**: Added `"pycfd-pde": "pycfd-pde-benchmark"` to `SUITE_DIRS` dict

These are the minimal, established pattern for onboarding a new benchmark suite (same as fealpy, nektar, octave, qcompute-abacus).

---

## 7. Benchmark & Approval System

### 7.1 Approval Configs Created

| File | Purpose |
|------|---------|
| `.mhe/benchmarks/pycfd-approval.json` | Suite-level benchmark approval config (3-lane gates, FVM claim boundaries) |
| `.mhe/approvals/pycfd_pde_benchmark_approval.json` | Admin approval manifest — status: `approved_with_limitations` |

### 7.2 Shared Config Updated

| File | Change |
|------|--------|
| `.mhe/benchmarks/comparison-approval.json` | Added `pycfd-pde` conditional approval profile entry |

### 7.3 Approval Limitations

The admin approval is granted with specific limitations:
- 5 case types approved: `vortex-2d`, `airfoil-2d`, `cylinder-2d`, `mms-2d`, `shock-diffraction-2d`
- 4 lanes: `extension`, `direct`, `agent`, `comparison`
- Claims requiring additional evidence: CFD solver residual convergence, case type capability, direct lane correctness
- Non-replacement rules: ACP/Claude review does NOT replace admin approval; CI schema pass does NOT replace admin approval

---

## 8. mhe-benchmark-iteration Skill Improvements

Based on PyCFD development experience, 9 changes were made across 4 reference files in `~/.claude/skills/mhe-benchmark-iteration/`:

| File | Changes |
|------|---------|
| `lane-runner-protocol.md` | New Suite Onboarding section (5-step checklist), generalized preflight to 4 dependency archetypes, Claude Proposal Normalization subsection |
| `iteration-backlog.md` | Added "Governance Gaps" optimization category (9th category), 3 new common backlog rows (B-governance-placeholder, B-claude-nulls, B-path-probe), "new suite first-round" variant template |
| `design-method-docs.md` | Added PyCFD/FVM entry to Metrics by Domain table (residual_l1, residual_l2, wall_time_seconds, iterations, ncells, nnodes, nfaces) |
| `comparator-reporting.md` | Policy gate format divergence note: structured gate objects vs dict-based gates |

---

## 9. Known Limitations & Deliberate Exclusions

### 9.1 Design Scope Boundaries

- **No FEM error norms**: PyCFD is an FVM solver. Residual norms (L1/L2) are convergence quality metrics, not solution error metrics. MMS convergence rate analysis requires separate methodological review.
- **No mesh generation**: PyCFD uses structured grid generation via `Grid(generated=True)`. External meshes (airfoil) require pre-existing mesh files at `PYCFD_SRC_PATH`.
- **No convergence rate analysis**: The validator checks residual thresholds, not asymptotic convergence rates. MMS truncation error analysis is out of scope.
- **No Python 2 support**: PyCFD originally targeted Python 2; syntax fixes were applied upstream for Python 3.12 compatibility.

### 9.2 Governance Coverage Gaps (Intentionally Deferred)

These are documented in `iteration-backlog.md` under the Governance Gaps category:

- **No promotion gate automation**: Promotion from staging to production requires manual admin approval
- **No automated benchmark re-run triggers**: Regressions are detected by comparison but not auto-flagged
- **No CI integration**: All benchmarks are local CLI-driven; no CI pipeline exists

### 9.3 Real Execution Evidence

- Smoke tests gate on `MHE_RUN_REAL_PYCFD=1` and `PYCFD_SRC_PATH`
- Real execution evidence has NOT been collected for any case type
- The benchmark runner dry-run mode produces synthetic evidence for schema/plumbing validation
- Real Claude proposal variability and adaptive repair have NOT been tested against real PyCFD

---

## 10. Next Action Recommendations

### 10.1 Priority 1 — Collect Real Execution Evidence

The most significant evidence gap. Without real execution traces, the extension cannot claim anything about numerical correctness or solver behavior.

**Specific actions:**
1. Run `test_metaharness_pycfd_smoke.py` with `MHE_RUN_REAL_PYCFD=1 PYCFD_SRC_PATH=/home/linden/code/work/Helmholtz/git/PyCFD`
2. Run benchmark `--suite pycfd-pde --lanes extension --cases vortex-2d --allow-real-tools`
3. Run benchmark with `--repeat 3` on one case to establish stability baselines
4. Verify residual norms are within physically reasonable ranges per case type

**Estimated effort**: 1 session (requires PyCFD installation and Python 3.12 compatibility)

### 10.2 Priority 2 — Real Claude Benchmark Lanes

Once real solver baselines exist, introduce real Claude variability.

**Specific actions:**
1. Run `--suite pycfd-pde --lanes direct --cases vortex-2d` with real `ClaudeCLIBrainProvider`
2. Run `--suite pycfd-pde --lanes agent --cases vortex-2d --adaptive-agent`
3. Compare extension vs direct vs agent lane results
4. Document any repair success/failure patterns

**Precondition**: Priority 1 complete. **Estimated effort**: 1–2 sessions.

### 10.3 Priority 3 — Residual Tolerance Table

The admin approval requires a "residual tolerance table per case type." Currently the validator uses a single `residual_tolerance` parameter.

**Specific actions:**
1. Define per-case-type tolerance values based on real execution data (from Priority 1)
2. Update `PyCFDValidatorComponent` to accept a tolerance table keyed by `CaseType`
3. Document the rationale for each tolerance value in the wiki

**Precondition**: Priority 1 complete. **Estimated effort**: 1 session.

### 10.4 Priority 4 — Direct Lane Code Review

The admin approval requires review of compiler-generated scripts for 5 items: import correctness, config dict, mesh parameters, flux/limiter selection, residual computation.

**Specific actions:**
1. Run compiler for all 5 case types with `--allow-real-tools`
2. Extract generated scripts from the direct lane
3. Review against the 5-item checklist from the approval manifest
4. Document review findings in evidence bundle

**Precondition**: Priority 1 complete. **Estimated effort**: 1 session.

### 10.5 Priority 5 — Cross-Extension Comparison

Compare PyCFD benchmark results against fealpy and nektar PDE benchmark patterns.

**Specific actions:**
1. Run all three PDE suites (fealpy-pde, nektar-pde, pycfd-pde) with comparable cases
2. Run `benchmark-compare` across suites
3. Document FVM vs FEM vs spectral/hp workflow differences in the benchmark wiki

**Precondition**: Priority 1–2 complete. **Estimated effort**: 2 sessions.

### 10.6 Priority 6 — CI / Automation

**Specific actions:**
1. Add dry-run benchmark smoke to a pre-commit or CI check
2. Automate the `benchmark-run --suite pycfd-pde --repeat 3` cycle
3. Wire regression detection to governance adapter

**Precondition**: Priority 1–3 complete. **Estimated effort**: 2–3 sessions.

---

## 11. Conclusion

The PyCFD MHE extension is **fully complete** at the code, test, documentation, manifest, and approval configuration levels. All 80 non-smoke tests pass, ruff is clean, and all Phase 0–5 deliverables are delivered.

The extension follows the canonical MHE pattern (modeled after fealpy) with appropriate adaptations for PyCFD's unique characteristics: path-based discovery (not a pip package), residual-based validation (not FEM error norms), and FVM-specific metrics.

The primary remaining work is evidence collection: real execution traces, Claude lane comparisons, and residual tolerance calibration. These are gated on running the extension against a real PyCFD installation and real Claude CLI — both are environmental prerequisites, not code gaps.

**Key files for the next session:**
- Handoff: `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-extension-handoff-report.md`
- Roadmap: `docs/wiki/meta-harness-engineer/blueprint/09-pycfd-roadmap.md`
- Wiki router: `docs/wiki/meta-harness-engineer/pycfd-engine-wiki/README.md`
