# 06. Packaging and Registration

## 1. Package Layout

```text
MHE/src/metaharness_ext/fealpy/
├── __init__.py              # 69-name public re-export surface
├── types.py                 # 6 type aliases + 1 enum
├── contracts.py             # 12 Pydantic models
├── slots.py                 # 7 slot constants + PROTECTED_SLOTS
├── capabilities.py          # 9 capability constants + CANONICAL_CAPABILITIES
├── gateway.py               # FealpyGatewayComponent
├── environment.py           # FealpyEnvironmentProbeComponent
├── compiler.py              # FealpyCompilerComponent (7 templates)
├── executor.py              # FealpyExecutorComponent (quota-gated)
├── validator.py             # FealpyValidatorComponent (protected)
├── evidence.py              # build_evidence_bundle()
├── policy.py                # FealpyEvidencePolicy
├── study.py                 # FealpyStudyComponent + convergence helpers
├── governance.py            # FealpyGovernanceAdapter
├── async_executor.py        # FealpyAsyncExecutor
├── optimizer.py             # FealpyDomainBrainProvider + 3 models
├── scheduler.py             # FealpySchedulerAdapter + Slurm + K8s backends
├── quota.py                 # FealpyResourceQuotaProvider + DOF estimators
├── benchmark_runner.py      # FealpyBenchmarkRunner (3-lane)
├── benchmark_cases.py       # fealpy_case_catalog() — 8 cases
└── backend_comparison.py    # FealpyBackendComparisonRunner + 2 models

MHE/examples/manifests/fealpy/
├── fealpy_gateway.json
├── fealpy_environment.json
├── fealpy_compiler.json
├── fealpy_executor.json
├── fealpy_validator.json
└── fealpy_study.json

MHE/tests/
├── test_metaharness_fealpy_contracts.py
├── test_metaharness_fealpy_environment.py
├── test_metaharness_fealpy_compiler.py
├── test_metaharness_fealpy_manifest.py
├── test_metaharness_fealpy_executor.py
├── test_metaharness_fealpy_validator.py
├── test_metaharness_fealpy_evidence_policy.py
├── test_metaharness_fealpy_study.py
├── test_metaharness_fealpy_smoke.py
├── test_metaharness_fealpy_backends.py
├── test_metaharness_fealpy_governance.py
├── test_metaharness_fealpy_async_executor.py
├── test_metaharness_fealpy_optimizer.py
├── test_metaharness_fealpy_scheduler.py
├── test_metaharness_fealpy_quota.py
├── test_metaharness_fealpy_benchmark_cases.py
└── test_metaharness_fealpy_backend_comparison.py
```

## 2. Public Exports (`__all__`)

69 names total, organized by category:

**Capabilities** (10): `CANONICAL_CAPABILITIES` + 9 individual `CAP_FEALPY_*`

**Slots** (8): 7 individual `FEALPY_*_SLOT` + `PROTECTED_SLOTS`

**Components** (12): `FealpyGatewayComponent`, `FealpyEnvironmentProbeComponent`, `FealpyCompilerComponent`, `FealpyExecutorComponent`, `FealpyValidatorComponent`, `FealpyStudyComponent`, `FealpyResourceQuotaProvider`

**Models** (26): `FealpyMeshSpec`, `FealpySolverSpec`, `FealpyProblemSpec`, `FealpyEnvironmentReport`, `FealpyRunPlan`, `FealpyRunArtifact`, `FealpyValidationReport`, `FealpyEvidenceBundle`, `FealpyEvidenceWarning`, `FealpyPolicyReport`, `FealpyStudyAxis`, `FealpyStudySpec`, `FealpyStudyTrial`, `FealpyStudyReport`, `FealpySlurmSubmission`, `FealpyK8sJobSpec`, `BackendMetrics`, `FealpyBackendComparisonResult`, `FealpyProposalEvaluation`, `FealpyStudyObservation` + 6 type aliases

**Non-component classes** (8): `FealpyBenchmarkRunner`, `FealpyBackendComparisonRunner`, `FealpyAsyncExecutor`, `FealpyGovernanceAdapter`, `FealpyEvidencePolicy`, `FealpyDomainBrainProvider`, `FealpyOptimizerStrategy`, `FealpySchedulerAdapter`, `FealpySlurmBackend`, `FealpyK8sBackend`

**Functions** (5): `build_evidence_bundle`, `estimate_dofs`, `estimate_memory_mb`, `estimate_taylor_hood_dofs`, `fealpy_case_catalog`, `get_fealpy_cases`

## 3. Capabilities

| Constant | Value | Provider |
|---|---|---|
| `CAP_FEALPY_TASK_ISSUE` | `fealpy.task.issue` | `FealpyGatewayComponent` |
| `CAP_FEALPY_ENV_PROBE` | `fealpy.environment.probe` | `FealpyEnvironmentProbeComponent` |
| `CAP_FEALPY_COMPILE` | `fealpy.compile` | `FealpyCompilerComponent` |
| `CAP_FEALPY_EXECUTE_RUN` | `fealpy.execute.run` | `FealpyExecutorComponent` |
| `CAP_FEALPY_VALIDATE_REPORT` | `fealpy.validate.report` | `FealpyValidatorComponent` |
| `CAP_FEALPY_STUDY_RUN` | `fealpy.study.run` | `FealpyStudyComponent` |
| `CAP_FEALPY_OPTIMIZER_PROPOSE` | `fealpy.optimizer.propose` | `FealpyDomainBrainProvider` |
| `CAP_FEALPY_SCHEDULER_DRYRUN` | `fealpy.scheduler.dryrun` | `FealpySchedulerAdapter` |
| `CAP_FEALPY_QUOTA_PROVIDE` | `fealpy.quota.provide` | `FealpyResourceQuotaProvider` |

All 9 are in `CANONICAL_CAPABILITIES` frozenset.

## 4. Slots and Protected Boundary

| Slot | Bound Component | Manifest |
|---|---|---|
| `fealpy_gateway.primary` | `FealpyGatewayComponent` | fealpy_gateway.json |
| `fealpy_environment.primary` | `FealpyEnvironmentProbeComponent` | fealpy_environment.json |
| `fealpy_compiler.primary` | `FealpyCompilerComponent` | fealpy_compiler.json |
| `fealpy_executor.primary` | `FealpyExecutorComponent` | fealpy_executor.json |
| `fealpy_validator.primary` | `FealpyValidatorComponent` | fealpy_validator.json |
| `fealpy_study.primary` | `FealpyStudyComponent` | fealpy_study.json |
| `fealpy_quota_provider.primary` | `FealpyResourceQuotaProvider` | (no manifest) |

`PROTECTED_SLOTS = frozenset({FEALPY_VALIDATOR_SLOT})` — validator cannot be replaced without platform authorization.

## 5. Manifest Surface

All 6 manifests follow the same structure:

```json
{
  "manifest_version": "1.0",
  "harness_version": ">=0.1.0",
  "kind": "core",
  "name": "fealpy_<name>",
  "version": "0.1.0",
  "entry": {
    "module": "metaharness_ext.fealpy.<module>",
    "class": "<ClassName>"
  },
  "slots": {"primary": "<slot>"},
  "capabilities": {"primary": "<capability>"},
  "sandbox": "<tier>",
  "protected": true/false,
  "credentials": {}
}
```

| Manifest | Sandbox Tier | Protected |
|---|---|---|
| `fealpy_gateway.json` | `workspace-write` | false |
| `fealpy_environment.json` | `read-only` | false |
| `fealpy_compiler.json` | `read-only` | false |
| `fealpy_executor.json` | `workspace-write` | false |
| `fealpy_validator.json` | `read-only` | **true** |
| `fealpy_study.json` | `workspace-write` | false |

## 6. Registration and Discovery

Extension is auto-discoverable through MHE's manifest discovery (`discover_manifest_paths()`). The extension directory `src/metaharness_ext/fealpy/` is a standard Python package — no plugin entry points needed. MHE core's `HarnessRuntime` handles component discovery, dependency ordering, activation, and slot registration during boot.
