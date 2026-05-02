# 04. Environment, Validation, and Evidence

## 1. Environment Probe Surface

`PyCFDEnvironmentProbeComponent` performs path-based discovery of PyCFD:

1. **Resolve `PYCFD_SRC_PATH`**: env var `PYCFD_SRC_PATH` or constructor argument
2. **Check path existence**: `os.path.isdir(pycfd_src_path)`
3. **Check `Solvers.py`**: file existence in the resolved path
4. **Check numpy availability**: `import numpy`
5. **Attempt import**: `importlib.import_module("Solvers")` with path injection
6. **Report**: Python version, resolved path, error list, availability boolean

```python
report = probe.probe(task_id="test")
# PyCFDEnvironmentReport(
#     task_id="test",
#     available=True/False,
#     pycfd_src_path="/abs/path/to/PyCFD",
#     python_version="3.13.11",
#     status="ready" | "source_not_found" | "partial" | "not_found",
#     errors=[],
#     blocks_promotion=True when unavailable
# )
```

## 2. Failure Taxonomy

### Environment-Level Failures

| Status | Cause | Blocks Promotion |
|---|---|---|
| `source_not_found` | `PYCFD_SRC_PATH` does not exist or has no `Solvers.py` | Yes |
| `partial` | Path exists but import or numpy check failed | Yes |
| `not_found` | Neither env var nor constructor path provided | Yes |

### Run-Level Failures

| Artifact Status | Meaning | Validator Response |
|---|---|---|
| `unavailable` | Environment not ready | `ENVIRONMENT_UNAVAILABLE` |
| `timeout` | Execution exceeded timeout | `RUNTIME_FAILED` |
| `failed` | Non-zero exit or parsing failure | `RUNTIME_FAILED` |

### Validation-Level Failures

| Condition | Validation Status | Blocks Promotion |
|---|---|---|
| L1 residual > tolerance | `RESIDUAL_EXCEEDED` | Yes |
| L2 residual > tolerance | `RESIDUAL_EXCEEDED` | Yes |
| Residuals missing | `RESIDUAL_EXCEEDED` | Yes (implicit) |
| All checks pass | `EXECUTED` | No |

## 3. Validation States

The validator processes artifacts in priority order:

```
1. status == "unavailable" → ENVIRONMENT_UNAVAILABLE (fail)
2. status == "timeout"     → RUNTIME_FAILED (fail)
3. status == "failed"      → RUNTIME_FAILED (fail)
4. Check residual_l1 > tol → RESIDUAL_EXCEEDED if exceeded
5. Check residual_l2 > tol → RESIDUAL_EXCEEDED if exceeded
6. All pass                → EXECUTED (pass)
```

Missing residuals (None) are treated as failure: if either residual is missing, that check fails. Both must be present and within tolerance for `passed=True`.

## 4. Evidence Assembly

`build_evidence_bundle()` collects four evidence layers:

1. **Environment**: `PyCFDEnvironmentReport` (readiness proof)
2. **Plan**: `PyCFDRunPlan` (deterministic spec→script trace)
3. **Artifact**: `PyCFDRunArtifact` (execution outputs)
4. **Validation**: `PyCFDValidationReport` (numeric quality proof)

Evidence refs use the `pycfd://` URI scheme:
```python
evidence_refs = [
    "pycfd://artifacts/pycfd-artifact-abc123",
    "pycfd://plans/p1",
    "pycfd://validations/p1",
    "pycfd://environments/env-test",
]
```

Warnings are generated for:
- `pycfd_environment_unavailable` — environment not ready
- `pycfd_validation_missing` — validation report not provided

## 5. 5-Gate Non-Short-Circuit Policy Chain

`PyCFDEvidencePolicy.evaluate()` runs all 5 gates regardless of individual outcomes. Each gate evaluates independently; the final decision aggregates all results.

| # | Gate | Checks | Decision |
|---|---|---|---|
| 1 | `pycfd_environment_readiness` | Environment available, not blocking | ALLOW / REJECT |
| 2 | `pycfd_validation_presence` | Validation report exists | ALLOW / REJECT |
| 3 | `pycfd_validation_status` | Validation passed | ALLOW / DEFER |
| 4 | `pycfd_evidence_files` | Evidence refs or files present | ALLOW / DEFER |
| 5 | `pycfd_evidence_ready` | Bundle complete and coherent | ALLOW / DEFER |

**Final decision logic**:
- Any gate REJECT → final `reject`
- No REJECT, but some gates DEFER → final `defer`
- All gates ALLOW → final `allow`

## 6. Non-Short-Circuit Decision Rationale

Unlike short-circuit evaluation (stop at first failure), the non-short-circuit design ensures:

- All gates are always evaluated, providing complete diagnostic information
- Users see ALL reasons for rejection, not just the first one
- Gate results can be trended over time for reliability analysis
- Policy reports contain the full 5-gate trace for audit purposes

## 7. What Counts as Executed vs. Scientifically Accepted

| State | Meaning |
|---|---|
| **Executed** | Solver ran to completion, residuals computed and within tolerance |
| **Scientifically Accepted** | Executed + all policy gates ALLOW + evidence bundle complete |

The validator certifies execution quality; the policy certifies evidence completeness. Both must pass for promotion readiness.
