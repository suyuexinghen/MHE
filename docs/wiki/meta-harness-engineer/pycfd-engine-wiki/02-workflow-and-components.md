# 02. Workflow and Component Chain

## 1. Canonical Component Chain

```text
PyCFDGateway (task intake + case type validation)
  → PyCFDEnvironmentProbe (PYCFD_SRC_PATH, numpy, Solvers.py)
    → PyCFDCompiler (Python solver script generation, 5 case templates)
      → PyCFDExecutor (subprocess execution, JSON stdout parsing)
        → PyCFDValidator (L1/L2 residual tolerance checks) [protected]
          → build_evidence_bundle() (structured evidence assembly)
            → PyCFDEvidencePolicy (5-gate promotion evaluation)

Optional extensions:
  → PyCFDStudyComponent (parameter sweep via Cartesian product)
  → PyCFDGovernanceAdapter (MHE core governance integration)
  → PyCFDBenchmarkRunner (3-lane benchmark comparison)
```

## 2. Component Responsibilities

### Gateway (`pycfd_gateway.primary`)

- Accepts `PyCFDProblemSpec`, validates case type against 5 known case IDs
- Provides `issue_task(spec)` — validates spec, sets defaults from case catalog
- Provides `issue_task_with_overrides(spec, overrides)` — dotted-path parameter overrides
- Provides `compile_and_run(spec)` — convenience shorthand for full pipeline
- Rejects unknown case types with clear error messages
- Provides capability `pycfd.task.issue`

### Environment Probe (`pycfd_environment.primary`)

- Checks `PYCFD_SRC_PATH` existence (env var or constructor arg)
- Validates `Solvers.py` file presence and Python importability
- Probes numpy availability
- Reports Python version
- Returns `PyCFDEnvironmentReport`: `available`, `pycfd_src_path`, `python_version`, `errors`
- Provides capability `pycfd.environment.probe`

### Compiler (`pycfd_compiler.primary`)

- Compiles `PyCFDProblemSpec` into `PyCFDRunPlan` with self-contained `solve.py` script source
- Generates deterministic `plan_id` via SHA256 of serialized spec
- 5 case-specific template methods via `_CASE_DEFAULTS` dispatch dict
- Template header injects `pycfd_src` path and config JSON for `run_pycfd_case()`
- Maps case types to flow types and solver types automatically
- Provides capability `pycfd.compile`

### Executor (`pycfd_executor.primary`)

- Writes `solve.py` into workspace directory
- Executes via `subprocess.run([sys.executable, script_path])` in subprocess
- Enforces timeout from `plan.spec.timeout_seconds`
- Captures stdout and parses JSON (residual_l1, residual_l2, wall_time_seconds, iterations, ncells, nnodes, nfaces)
- Produces `PyCFDRunArtifact` with 4 statuses: `completed`, `failed`, `timeout`, `unavailable`
- Parses JSON from last stdout line (robust to debug print noise)
- Provides capability `pycfd.execute.run`

### Validator (`pycfd_validator.primary`) — protected

- Distinguishes 5 `PyCFDValidationStatus` states: `ENVIRONMENT_UNAVAILABLE`, `RUNTIME_FAILED`, `RESIDUAL_EXCEEDED`, `EXECUTED`
- Checks artifact status for `unavailable`, `timeout`, `failed` → generates appropriate `ValidationIssue`
- Applies L1/L2 residual tolerance checks (configurable, default `1e-5`)
- Both residuals missing → fail; one missing + one passing → fail
- `protected = True` — cannot be replaced via graph mutation
- Provides capability `pycfd.validate.report`

### Evidence (`build_evidence_bundle()`)

- Free function assembling `PyCFDEvidenceBundle` from env + plan + artifact + validation
- Collects evidence refs with `pycfd://` prefix
- Generates warnings for missing validation, unavailable environment
- Includes provenance metadata (task_id, plan_ref, artifact_ref)

### Policy (`PyCFDEvidencePolicy`)

- 5-gate non-short-circuit chain:
  1. `pycfd_environment_readiness` — environment must be available
  2. `pycfd_validation_presence` — validation report must exist
  3. `pycfd_validation_status` — validation must pass
  4. `pycfd_evidence_files` — at least one evidence ref or file
  5. `pycfd_evidence_ready` — bundle-level readiness check
- Each gate produces ALLOW / DEFER / REJECT
- Final decision: ALLOW (all pass), DEFER (no explicit rejection but incomplete), REJECT (any gate rejects)

### Study (`pycfd_study.primary`)

- Accepts `PyCFDStudySpec` (task_template + axes), generates parameter combinations via Cartesian product
- For each snapshot: apply mutation → produces mutated spec
- Extracts target metrics from trial results
- Configurable `max_trials` limit
- Provides capability `pycfd.study.run`

### Governance (`PyCFDGovernanceAdapter`)

- Bridges to MHE core: builds `ValidationReport` from `PyCFDValidationReport`
- Emits `SessionEvent` records (3 types): `CANDIDATE_VALIDATED`, `SAFETY_GATE_EVALUATED`, `CANDIDATE_REJECTED`
- `emit_runtime_evidence()` — placeholder for SessionStore/AuditLog/ProvGraph injection
- Non-HarnessComponent (adapter pattern integration)

### Benchmark Runner (`PyCFDBenchmarkRunner`)

- 3-lane comparison: extension (full MHE pipeline), direct (Claude-generated raw script), agent (Claude spec proposal)
- `run_all_cases()` orchestrates all case/lane combinations
- `run_case()` dispatches to lane-specific handlers
- Dry-run mode for testing without real PyCFD execution
- Direct and agent lanes are placeholder (require Claude CLI integration)

## 3. Data Flow Between Components

```
PyCFDProblemSpec (typed task input)
  │
  ├─→ PyCFDEnvironmentProbe.probe(spec) → PyCFDEnvironmentReport
  │
  ├─→ PyCFDCompiler.compile(spec, environment) → PyCFDRunPlan
  │     └─ .script_source (self-contained solve.py)
  │     └─ .workspace_dir
  │     └─ .plan_id (SHA256 deterministic)
  │
  ├─→ PyCFDExecutor.execute(plan) → PyCFDRunArtifact
  │     └─ .residual_l1, .residual_l2
  │     └─ .wall_time_seconds, .iterations
  │     └─ .ncells, .nnodes, .nfaces
  │     └─ .status (completed/failed/timeout/unavailable)
  │
  ├─→ PyCFDValidator.validate(artifact, plan) → PyCFDValidationReport
  │     └─ .passed (all tolerance checks)
  │     └─ .status (PyCFDValidationStatus enum)
  │     └─ .residual_l1_passed, .residual_l2_passed
  │     └─ .issues (with blocks_promotion flags)
  │
  └─→ build_evidence_bundle(artifact, validation, plan, environment)
       → PyCFDEvidenceBundle
         └─ PyCFDEvidencePolicy.evaluate(bundle) → PyCFDPolicyReport
```

Each downstream component assumes upstream outputs are type-validated Pydantic models. Components do not bypass previous stages.
