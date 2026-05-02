# 06. Packaging and Registration

## 1. Package Layout

```text
MHE/src/metaharness_ext/pycfd/
├── __init__.py              # 30+-name public re-export surface
├── types.py                 # 6 type aliases + 1 enum
├── contracts.py             # 14 Pydantic models
├── slots.py                 # 7 slot constants + PROTECTED_SLOTS
├── capabilities.py          # 9 capability constants + CANONICAL_CAPABILITIES
├── gateway.py               # PyCFDGatewayComponent
├── environment.py           # PyCFDEnvironmentProbeComponent
├── compiler.py              # PyCFDCompilerComponent (5 case templates)
├── executor.py              # PyCFDExecutorComponent
├── validator.py             # PyCFDValidatorComponent (protected)
├── evidence.py              # build_evidence_bundle()
├── policy.py                # PyCFDEvidencePolicy
├── study.py                 # PyCFDStudyComponent
├── governance.py            # PyCFDGovernanceAdapter
├── benchmark_cases.py       # pycfd_case_catalog() — 5 cases
└── benchmark_runner.py      # PyCFDBenchmarkRunner (3-lane)

MHE/examples/manifests/pycfd/
├── pycfd_gateway.json
├── pycfd_environment.json
├── pycfd_compiler.json
├── pycfd_executor.json
├── pycfd_validator.json
└── pycfd_study.json

MHE/tests/
├── test_metaharness_pycfd_contracts.py
├── test_metaharness_pycfd_environment.py
├── test_metaharness_pycfd_compiler.py
├── test_metaharness_pycfd_executor.py
├── test_metaharness_pycfd_validator.py
├── test_metaharness_pycfd_evidence_policy.py
├── test_metaharness_pycfd_gateway.py
├── test_metaharness_pycfd_benchmark_cases.py
├── test_metaharness_pycfd_benchmark_runner.py
├── test_metaharness_pycfd_study.py
├── test_metaharness_pycfd_governance.py
└── test_metaharness_pycfd_smoke.py
```

## 2. Public Exports (`__all__`)

30+ names total, organized by category:

**Capabilities** (10): `CANONICAL_CAPABILITIES` + 9 individual `CAP_PYCFD_*`

**Slots** (8): 7 individual `PYCFD_*_SLOT` + `PROTECTED_SLOTS`

**Components** (6): `PyCFDGatewayComponent`, `PyCFDEnvironmentProbeComponent`, `PyCFDCompilerComponent`, `PyCFDExecutorComponent`, `PyCFDValidatorComponent`, `PyCFDStudyComponent`

**Models** (14): `PyCFDMeshSpec`, `PyCFDFlowSpec`, `PyCFDSolverSpec`, `PyCFDProblemSpec`, `PyCFDEnvironmentReport`, `PyCFDRunPlan`, `PyCFDRunArtifact`, `PyCFDValidationReport`, `PyCFDEvidenceWarning`, `PyCFDEvidenceBundle`, `PyCFDPolicyReport`, `PyCFDStudyAxis`, `PyCFDStudySpec`, `PyCFDStudyTrial`, `PyCFDStudyReport`

**Type aliases** (6): `PyCFDCaseType`, `PyCFDMeshType`, `PyCFDFluxType`, `PyCFDLimiterType`, `PyCFDRunArtifactStatus`, `PyCFDSolverType`, `PyCFDFlowType`

**Enums** (1): `PyCFDValidationStatus`

**Non-component classes** (3): `PyCFDBenchmarkRunner`, `PyCFDGovernanceAdapter`, `PyCFDEvidencePolicy`

**Functions** (3): `build_evidence_bundle`, `pycfd_case_catalog`, `get_pycfd_cases`

## 3. Capabilities

| Constant | Value | Provider |
|---|---|---|
| `CAP_PYCFD_TASK_ISSUE` | `pycfd.task.issue` | `PyCFDGatewayComponent` |
| `CAP_PYCFD_ENV_PROBE` | `pycfd.environment.probe` | `PyCFDEnvironmentProbeComponent` |
| `CAP_PYCFD_COMPILE` | `pycfd.compile` | `PyCFDCompilerComponent` |
| `CAP_PYCFD_EXECUTE_RUN` | `pycfd.execute.run` | `PyCFDExecutorComponent` |
| `CAP_PYCFD_VALIDATE_REPORT` | `pycfd.validate.report` | `PyCFDValidatorComponent` |
| `CAP_PYCFD_STUDY_RUN` | `pycfd.study.run` | `PyCFDStudyComponent` |
| `CAP_PYCFD_BENCHMARK_RUN` | `pycfd.benchmark.run` | `PyCFDBenchmarkRunner` |
| `CAP_PYCFD_GOVERNANCE_EMIT` | `pycfd.governance.emit` | `PyCFDGovernanceAdapter` |
| `CAP_PYCFD_POLICY_EVALUATE` | `pycfd.policy.evaluate` | `PyCFDEvidencePolicy` |

All 9 are in `CANONICAL_CAPABILITIES` frozenset.

## 4. Slots and Protected Boundary

| Slot | Bound Component | Manifest |
|---|---|---|
| `pycfd_gateway.primary` | `PyCFDGatewayComponent` | pycfd_gateway.json |
| `pycfd_environment.primary` | `PyCFDEnvironmentProbeComponent` | pycfd_environment.json |
| `pycfd_compiler.primary` | `PyCFDCompilerComponent` | pycfd_compiler.json |
| `pycfd_executor.primary` | `PyCFDExecutorComponent` | pycfd_executor.json |
| `pycfd_validator.primary` | `PyCFDValidatorComponent` | pycfd_validator.json |
| `pycfd_study.primary` | `PyCFDStudyComponent` | pycfd_study.json |
| `pycfd_benchmark.primary` | `PyCFDBenchmarkRunner` | (no manifest) |

`PROTECTED_SLOTS = frozenset({PYCFD_VALIDATOR_SLOT})` — validator cannot be replaced without platform authorization.

## 5. Manifest Surface

All 6 manifests follow the same structure with extension-specific values:

| Manifest | Sandbox Tier | Protected | Entry Class |
|---|---|---|---|
| `pycfd_gateway.json` | `workspace-write` | false | `PyCFDGatewayComponent` |
| `pycfd_environment.json` | `read-only` | false | `PyCFDEnvironmentProbeComponent` |
| `pycfd_compiler.json` | `read-only` | false | `PyCFDCompilerComponent` |
| `pycfd_executor.json` | `workspace-write` | false | `PyCFDExecutorComponent` |
| `pycfd_validator.json` | `read-only` | **true** | `PyCFDValidatorComponent` |
| `pycfd_study.json` | `workspace-write` | false | `PyCFDStudyComponent` |

Manifests use `harness_version: ">=0.1.0"` and `state_schema_version: 1`.

## 6. Registration and Discovery

The extension is auto-discoverable through MHE's manifest discovery (`discover_manifest_paths()`). The extension directory `src/metaharness_ext/pycfd/` is a standard Python package — no plugin entry points needed. MHE core's `HarnessRuntime` handles component discovery, dependency ordering, activation, and slot registration during boot.

Components are registered with their slots and capabilities via `declare_interface()`. The validator is the only protected component and cannot be replaced through graph mutation.
