# 04. Environment, Validation, and Evidence

## 1. Environment Probe Surface

`FealpyEnvironmentProbeComponent.probe(spec) → FealpyEnvironmentReport`

### Detection Strategy

| Check | Method | Failure Impact |
|---|---|---|
| fealpy import | `import fealpy; fealpy.__version__` | `available=False`, `blocks_promotion=True` |
| numpy backend | `import numpy` | `available=False`, `blocks_promotion=True` |
| pytorch backend | `import torch` | Warning only, does not block |
| jax backend | `import jax` | Warning only, does not block |
| PDE families | static list from `_FEALPY_PDE_FAMILIES` | Informational |

### Backend Import Paths

```python
_BACKEND_IMPORT_PATHS = {"numpy": "numpy", "pytorch": "torch", "jax": "jax"}
```

`available` is true iff both fealpy and numpy are importable. `backend_status` maps each backend to detailed status messages.

### PDE Families List

Environment probe reports 22 PDE families: poisson, stokes, navier_stokes, parabolic, hyperbolic, helmholtz, curlcurl, diffusion_convection_reaction, diffusion_reaction, interface_poisson, surface_poisson, wave, allen_cahn, nonlinear, polyharmonic, quasilinear_elliptic, optimal_control, linear_elasticity, diffuse_interface, ion_flow, dld_microfluidic_chip, mgtensor_possion.

## 2. Failure Taxonomy

| Stage | Detectable By | Artifact Status | Promotion Decision |
|---|---|---|---|
| Environment unavailable | Probe | `unavailable` | REJECT (component unavailable) |
| Compile error | Compiler | `failed` | REJECT (no plan) |
| Subprocess timeout | Executor | `timeout` | REJECT (incomplete) |
| Non-zero exit | Executor | `failed` | REJECT (runtime error) |
| JSON parse failure | Executor | `failed` (with error message) | REJECT (unparseable output) |
| Missing metrics | Validator | N/A | REJECT (insufficient output) |
| L2/H1 tolerance fail | Validator | N/A | DEFER (numeric quality concern) |
| All checks pass | Validator | `completed` | ALLOW |

## 3. Validation States

`FealpyValidationStatus` is a `(str, Enum)` with 6 members:

| Status | Meaning | `blocks_promotion` |
|---|---|---|
| `ENVIRONMENT_INVALID` | fealpy unavailable | Yes |
| `COMPILE_FAILED` | Compiler could not generate script | Yes |
| `RUNTIME_FAILED` | Subprocess error or non-zero exit | Yes |
| `OUTPUT_MISSING` | JSON stdout parse failed | Yes |
| `NUMERIC_VALIDATION_FAILED` | L2/H1 error exceeds tolerance | Yes (tunable) |
| `EXECUTED` | All checks passed | No |

`FealpyValidatorComponent` is `protected = True`. It cannot be replaced via graph mutation without platform authorization.

### Tolerance Defaults

- `l2_tolerance = 1e-6`
- `h1_tolerance = 1e-4`

Both are per-validator-invocation tunable via method parameters.

## 4. Evidence / Governance Seam

### Evidence Assembly

`build_evidence_bundle(artifact, validation, plan, environment) → FealpyEvidenceBundle`

The bundle:
1. Validates input completeness (warning if any of run/validation/environment/plan is missing)
2. Collects `evidence_refs` from all inputs
3. Generates warnings for: missing validation, environment issues, artifact anomalies
4. Creates `provenance` dict with `task_id`, `plan_ref`, `artifact_ref`, `validation_ref`
5. All evidence refs use `fealpy://` URI prefix

### Policy Gate Chain

`FealpyEvidencePolicy.evaluate(bundle) → FealpyPolicyReport`

| Gate | Check | ALLOW condition | DEFER / REJECT |
|---|---|---|---|
| `fealpy_environment_readiness` | Environment probe result | fealpy + numpy available | REJECT if missing |
| `fealpy_validation_presence` | Validation in bundle | Non-null validation | DEFER if missing |
| `fealpy_validation_status` | Validation status | `EXECUTED` | REJECT if non-executed |
| `fealpy_evidence_files` | Evidence refs completeness | Non-empty evidence list | DEFER if empty |
| `fealpy_evidence_ready` | Overall readiness | All gates allow | DEFER/REJECT based on severity |

### Decision Logic

- **ALLOW**: All 5 gates ALLOW → `decision="allow"`, `passed=True`
- **DEFER**: One or more gates DEFER, none REJECT → `decision="defer"`, `passed=False`
- **REJECT**: One or more gates REJECT → `decision="reject"`, `passed=False`

## 5. Non-short-circuit vs Short-circuit

- **Non-short-circuit**: All 5 gates are always evaluated, even if an early gate REJECTs. The full gate picture is always available in `report.gates`.
- **Short-circuit at executor**: If `runtime.resolved_resource_quota().exhausted`, executor returns failed artifact immediately — no subprocess launched.
- **Short-circuit at scheduler**: If `quota.exhausted` and `quota` passed to `SchedulerAdapter.submit()`, raises `ValueError` — no job submitted.

## 6. What Counts as Executed vs Scientifically Accepted

| Condition | Executed? | Scientifically Accepted? |
|---|---|---|
| Subprocess exit 0, JSON valid, all tolerances pass | Yes | Yes |
| Subprocess exit 0, JSON valid, L2 fails | Yes | No (NUMERIC_VALIDATION_FAILED) |
| Subprocess timeout | No (incomplete) | No |
| Non-zero exit | No (failed) | No |
| JSON parse failure | Technically yes, but output invalid | No |
| fealpy unavailable | No (never launched) | No |
