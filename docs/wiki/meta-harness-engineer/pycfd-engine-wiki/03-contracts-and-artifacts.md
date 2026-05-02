# 03. Contracts and Artifacts

## 1. Typed Input / Task Contracts

### PyCFDProblemSpec

The primary task specification. All CFD parameters flow through this model.

```python
class PyCFDProblemSpec(BaseModel):
    task_id: str                    # Unique task identifier
    case_type: PyCFDCaseType        # One of 5 case IDs
    mesh: PyCFDMeshSpec             # Grid dimensions (nx, ny)
    flow: PyCFDFlowSpec             # Flow conditions (Mach, AoA, gamma)
    solver: PyCFDSolverSpec         # Solver settings (CFL, max_iter, tolerance)
    timeout_seconds: int = 300      # Subprocess timeout
    tfinal: float | None = None     # End time (auto-inferred)
    dt: float | None = None         # Time step (auto-inferred)
    flow_type: PyCFDFlowType | None = None  # Auto-inferred from case_type
    solver_type: PyCFDSolverType | None = None  # Auto-inferred from case_type
    flux_type: PyCFDFluxType = "roe"
    limiter_type: PyCFDLimiterType = "barth"
```

`flow_type` and `solver_type` are computed fields auto-inferred from `case_type`:
- vortex-2d/cylinder-2d/mms-2d → subsonic, explicit-rk
- airfoil-2d → transonic, implicit-lu
- shock-diffraction-2d → supersonic, explicit-rk

### PyCFDMeshSpec

```python
class PyCFDMeshSpec(BaseModel):
    nx: int = 101                   # Grid points in x (≥ 10)
    ny: int = 101                   # Grid points in y (≥ 10)
    mesh_type: PyCFDMeshType = "structured"
    mesh_file: str | None = None    # External mesh file (airfoil case)
```

### PyCFDFlowSpec

```python
class PyCFDFlowSpec(BaseModel):
    mach: float = 0.5               # Mach number (> 0)
    aoa: float = 0.0                # Angle of attack (degrees)
    gamma: float = 1.4              # Specific heat ratio (≥ 1.0)
```

### PyCFDSolverSpec

```python
class PyCFDSolverSpec(BaseModel):
    cfl: float = 0.5                # CFL number (> 0, ≤ 1.0)
    max_iter: int = 10000           # Maximum iterations
    convergence_tol: float = 1e-10  # Convergence tolerance
```

## 2. Environment Report

### PyCFDEnvironmentReport

```python
class PyCFDEnvironmentReport(BaseModel):
    task_id: str
    available: bool                 # Whether PyCFD environment is ready
    pycfd_src_path: str             # Resolved absolute path
    python_version: str             # Python version string
    status: str                     # ready, source_not_found, partial, not_found
    errors: list[str]               # Error messages
    blocks_promotion: bool          # True when unavailable
```

## 3. Run Plan

### PyCFDRunPlan

```python
class PyCFDRunPlan(BaseModel):
    plan_id: str                    # SHA256 deterministic plan ID
    task_id: str
    run_id: str                     # Unique run identifier
    spec: PyCFDProblemSpec          # The spec that produced this plan
    script_source: str              # Generated solve.py content
    workspace_dir: str              # Working directory for execution
    created_at: str                 # ISO timestamp
```

`plan_id` is deterministically computed as `SHA256(json.dumps(spec, sort_keys=True))`, ensuring identical specs produce identical plan IDs.

## 4. Run Artifact

### PyCFDRunArtifact

```python
class PyCFDRunArtifact(BaseModel):
    artifact_id: str                # Unique artifact identifier
    run_id: str
    task_id: str
    plan_ref: str                   # Reference to parent plan
    status: PyCFDRunArtifactStatus  # completed, failed, timeout, unavailable
    return_code: int | None         # Subprocess exit code
    error_message: str | None       # Error details if failed
    residual_l1: float | None       # L1 residual norm
    residual_l2: float | None       # L2 residual norm
    wall_time_seconds: float | None # Execution wall time
    iterations: int | None          # Iteration count
    ncells: int | None              # Number of computational cells
    nnodes: int | None              # Number of mesh nodes
    nfaces: int | None              # Number of mesh faces
    summary_metrics: dict[str, object] | None  # Full metrics from solver JSON
```

## 5. Validation Surface

### PyCFDValidationReport

```python
class PyCFDValidationReport(BaseModel):
    task_id: str
    plan_ref: str
    artifact_ref: str
    passed: bool                    # All tolerance checks passed
    status: PyCFDValidationStatus   # ENVIRONMENT_UNAVAILABLE | RUNTIME_FAILED | RESIDUAL_EXCEEDED | EXECUTED
    messages: list[str]             # Human-readable validation messages
    residual_tolerance: float       # Tolerance used for checks
    residual_l1_passed: bool        # L1 residual within tolerance
    residual_l2_passed: bool        # L2 residual within tolerance
    summary_metrics: dict[str, object]  # Filtered key metrics
    issues: list[ValidationIssue]   # Structured issue list with blocks_promotion flags
```

#### PyCFDValidationStatus Enum

| Status | Meaning |
|---|---|
| `ENVIRONMENT_UNAVAILABLE` | PyCFD path not found or not importable |
| `RUNTIME_FAILED` | Execution timed out or subprocess returned non-zero |
| `RESIDUAL_EXCEEDED` | Execution succeeded but residuals exceed tolerance |
| `EXECUTED` | Execution succeeded and all residuals within tolerance |

## 6. Evidence / Policy Surface

### PyCFDEvidenceBundle

```python
class PyCFDEvidenceBundle(BaseModel):
    bundle_id: str                  # pycfd-evidence-{uuid}
    task_id: str
    environment: PyCFDEnvironmentReport | None
    plan: PyCFDRunPlan | None
    artifact: PyCFDRunArtifact | None
    validation: PyCFDValidationReport | None
    evidence_refs: list[str]        # pycfd:// references
    evidence_files: list[str]       # Local file paths
    warnings: list[PyCFDEvidenceWarning]  # Non-blocking warnings
```

### PyCFDPolicyReport

```python
class PyCFDPolicyReport(BaseModel):
    passed: bool
    decision: str                   # allow, defer, reject
    reason: str
    gates: list[dict]               # Per-gate results (5 gates)
```

## 7. Study Contracts

### PyCFDStudySpec

```python
class PyCFDStudySpec(BaseModel):
    study_id: str
    task_template: PyCFDProblemSpec # Base spec to vary
    axes: list[PyCFDStudyAxis]      # Parameter axes to sweep
    max_trials: int = 100           # Trial limit
```

### PyCFDStudyAxis

```python
class PyCFDStudyAxis(BaseModel):
    name: str                       # Dotted path to parameter
    values: list[Any]               # Discrete values
    range: tuple[float, float, float] | None  # (start, stop, step)
```

### PyCFDStudyTrial

```python
class PyCFDStudyTrial(BaseModel):
    trial_id: str
    snapshot: dict[str, Any]        # Parameter values for this trial
    spec: PyCFDProblemSpec          # Mutated spec
    result: dict[str, Any] | None   # Trial result
    status: str                     # pending, running, completed, failed
```

### PyCFDStudyReport

```python
class PyCFDStudyReport(BaseModel):
    study_id: str
    task_id: str
    trials: list[PyCFDStudyTrial]
    best_trial_id: str | None
    summary: dict[str, Any]
```

## 8. Key Naming Constraints

- `task_id` is sanitized to `[a-z0-9_-]` with replacements for common separators
- `plan_id` uses hex digest of SHA256 for determinism
- `bundle_id` uses `pycfd-evidence-` prefix + UUID
- `artifact_id` uses `pycfd-artifact-` prefix + UUID
- Evidence refs use `pycfd://` URI scheme prefix
