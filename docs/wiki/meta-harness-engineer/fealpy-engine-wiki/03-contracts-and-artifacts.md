# 03. Contracts and Artifacts

## 1. Typed Input / Task Contracts

### FealpyMeshSpec

```text
meshtype: Literal["interval", "tri", "quad", "tet", "hex", "uniform"]
nx: int (≥2)    # number of cells in x
ny: int (≥1)    # number of cells in y (default 1)
nz: int | None  # number of cells in z (3D only)
h: float | None # uniform mesh spacing override
```

### FealpySolverSpec

```text
method: Literal["direct", "cg", "gmres", "minres", "bicgstab", "amg"] = "direct"
max_iterations: int (≥1) = 1000
atol: float = 1e-10
rtol: float = 1e-8
```

### FealpyProblemSpec

The central task input model:

| Field | Type | Default | Notes |
|---|---|---|---|
| `task_id` | `str` | required | Sanitized (whitespace stripped) |
| `pde_family` | `FealpyPdeFamily` | `"poisson"` | One of 32 recognized families |
| `example_key` | `int` | `1` | fealpy PDEModelManager example key |
| `backend` | `FealpyBackend` | `"numpy"` | `numpy` / `pytorch` / `jax` |
| `mesh` | `FealpyMeshSpec` | P1 triangle 8×8 | Grid parameters |
| `fe_degree` | `int` | `1` | FE polynomial degree (≥1) |
| `fe_space_type` | `FealpyFeSpaceType` | `"Lagrange"` | FE space dispatch |
| `solver` | `FealpySolverSpec` | direct, 1000 iter | Linear solver config |
| `dt` | `float` | `0.01` | Time step size (>0) |
| `num_time_steps` | `int` | `100` | Time integration steps (≥0) |
| `time_integrator` | `str` | `"implicit_euler"` | Time scheme for transient PDEs |
| `adaptive_refinement` | `int` | `0` | Refinement steps (field declared, not enforced) |
| `timeout_seconds` | `int` | `300` | Subprocess timeout (>0) |
| `promotion_metadata` | `dict` | `{}` | MHE promotion context |
| `graph_metadata` | `dict` | `{}` | MHE graph context |
| `evidence_refs` | `list[str]` | `[]` | Evidence references |

## 2. Run Plan

### FealpyRunPlan

| Field | Type | Notes |
|---|---|---|
| `plan_id` | `str` | SHA256 deterministic ID |
| `task_id` | `str` | From spec |
| `run_id` | `str` | One per invocation |
| `spec` | `FealpyProblemSpec` | Reference copy of input |
| `workspace_dir` | `str` | Execution directory |
| `script_source` | `str` | Generated solve.py source |
| `experiment_ref` | `str` (computed) | = `self.task_id` |

`plan_id` ensures different spec parameters → different plan. Two identical specs produce identical plan_id, enabling caching.

## 3. Run Artifact

### FealpyRunArtifact

| Field | Type | Notes |
|---|---|---|
| `artifact_id` | `str` | Unique per execution |
| `run_id` | `str` | From plan |
| `task_id` | `str` | From spec |
| `plan_ref` | `str` | Links to plan_id |
| `status` | `FealpyRunArtifactStatus` | `completed` / `failed` / `timeout` / `unavailable` |
| `return_code` | `int` | Subprocess exit code |
| `error_message` | `str | None` | Failure description |
| `l2_error` | `float | None` | L2 norm error |
| `h1_error` | `float | None` | H1 seminorm error |
| `linf_error` | `float | None` | Linf norm error |
| `dof_count` | `int | None` | Degrees of freedom |
| `solver_iterations` | `int | None` | Linear solver iterations |
| `wall_time_seconds` | `float | None` | Wall clock time |
| `mesh_info` | `dict` | `nc` (cells), `nn` (nodes) |
| `summary_metrics` | `dict` | Aggregated for benchmark |
| `evidence_refs` | `list[str]` | Evidence pointers |
| `warnings` | `list[str]` | Non-fatal issues |

## 4. Validation Surface

### FealpyValidationReport

| Field | Type | Notes |
|---|---|---|
| `task_id` | `str` | From spec |
| `plan_ref` | `str` | Links to plan |
| `artifact_ref` | `str` | Links to artifact |
| `passed` | `bool` | All tolerance checks passed |
| `status` | `FealpyValidationStatus` | 6-state enum |
| `messages` | `list[str]` | Human-readable messages |
| `l2_tolerance` | `float` | Default 1e-6 |
| `h1_tolerance` | `float` | Default 1e-4 |
| `l2_passed` | `bool | None` | L2 check result |
| `h1_passed` | `bool | None` | H1 check result |
| `linf_passed` | `bool | None` | Linf check result |
| `summary_metrics` | `dict` | Aggregated metrics |
| `issues` | `list[ValidationIssue]` | Issue list |
| `run_id` | `str` (computed) | = `self.artifact_ref` |
| `blocks_promotion` | `bool` (computed) | Any issue blocks? |

## 5. Evidence / Policy Surface

### FealpyEvidenceWarning

```text
code: str, message: str, severity: str, evidence: dict
```

### FealpyEvidenceBundle

| Field | Notes |
|---|---|
| `bundle_id` | Unique bundle identifier |
| `task_id`, `run_id` | Execution context |
| `plan_ref`, `artifact_ref`, `validation_ref` | Component links |
| `environment` | `FealpyEnvironmentReport` (optional) |
| `plan`, `artifact`, `validation` | Component outputs (optional) |
| `evidence_files`, `evidence_refs` | File paths and refs |
| `warnings` | `list[FealpyEvidenceWarning]` |
| `provenance` | `dict` — metadata for audit |
| `metadata` | `dict` — extension-specific metadata |

### FealpyPolicyReport

```text
passed: bool
decision: str  # "allow" | "defer" | "reject"
reason: str    # Human-readable reasoning
warnings: list[FealpyEvidenceWarning]
gates: dict[str, GateResult]  # Per-gate results
evidence: dict  # Supporting data
```

## 6. Study Surface

### FealpyStudyAxis

```text
parameter_path: str  # dotted path in FealpyProblemSpec (e.g. "mesh.nx")
values: list[Any] | None  # explicit value list
range: list[float] | None  # [start, end] inclusive
step: float | None  # step between values
```

### FealpyStudySpec

```text
task_template: FealpyProblemSpec
axes: list[FealpyStudyAxis]
objective: str = "minimize_l2_error"
goal: str = "minimize"
max_trials: int = 100
convergence_rule: str | None = None
target_tolerance: float | None = None
```

### FealpyStudyTrial / FealpyStudyReport

`FealpyStudyTrial` captures single trial: `trial_id`, `parameters`, `plan_ref`, `artifact_ref`, `validation_ref`, `metric_value`, `passed`, `messages`.

`FealpyStudyReport` aggregates: `study_id`, `task_id`, `trials`, `best_trial_id`, `recommended_parameters`, `convergence_analysis` (list of `dict` with convergence metrics), `summary_metrics`.

## 7. Scheduler Models

### FealpySlurmSubmission

```text
job_name: str, script: str, command: str
```

### FealpyK8sJobSpec

```text
job_name: str, yaml_spec: str
```

## 8. Backend Comparison Models

### BackendMetrics

```text
backend: str, wall_time: float | None, l2_error: float | None
h1_error: float | None, dof: int | None, status: str, error_message: str | None
```

### FealpyBackendComparisonResult

```text
case_id: str, backends: list[BackendMetrics], comparison_matrix: dict[str, dict]
```
