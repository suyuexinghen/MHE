# 06. 封装与注册

## 6.1 扩展目录结构

```
metaharness_ext/qcompute/
  __init__.py              # 公共 API re-export
  manifest.json            # 入口清单
  contracts.py             # Pydantic 模型（Spec, Report, Artifact, Bundle）
  capabilities.py          # CAP_QCOMPUTE_* 常量 + CANONICAL_CAPABILITIES
  slots.py                 # QCOMPUTE_*_SLOT 常量 + PROTECTED_SLOTS
  gateway.py               # QComputeGatewayComponent
  environment.py           # QComputeEnvironmentComponent
  config_compiler.py       # QComputeConfigCompilerComponent
  executor.py              # QComputeExecutorComponent
  validator.py             # QComputeValidatorComponent
  evidence.py              # QComputeEvidenceBuilder
  policy.py                # QComputePolicyEngine
  governance.py            # QComputeGovernanceAdapter
  study.py                 # QComputeStudyComponent
  types.py                 # 共享字面量/枚举
```

## 6.2 Slot 声明

```python
# slots.py
QCOMPUTE_GATEWAY_SLOT = "qcompute_gateway.primary"
QCOMPUTE_ENVIRONMENT_SLOT = "qcompute_environment.primary"
QCOMPUTE_CONFIG_COMPILER_SLOT = "qcompute_config_compiler.primary"
QCOMPUTE_EXECUTOR_SLOT = "qcompute_executor.primary"
QCOMPUTE_VALIDATOR_SLOT = "qcompute_validator.primary"
QCOMPUTE_STUDY_SLOT = "qcompute_study.primary"

PROTECTED_SLOTS = frozenset({QCOMPUTE_VALIDATOR_SLOT})
```

`QCOMPUTE_VALIDATOR_SLOT` 是 protected slot——validator 的输出直接参与
runtime-level promotion decision，不允许未经治理审批的热替换。

## 6.3 Capability 声明

```python
# capabilities.py
CAP_QCOMPUTE_CASE_COMPILE = "qcompute.compile.case"
CAP_QCOMPUTE_ENV_PROBE = "qcompute.environment.probe"
CAP_QCOMPUTE_CIRCUIT_COMPILE = "qcompute.circuit.compile"
CAP_QCOMPUTE_CIRCUIT_RUN = "qcompute.circuit.run"
CAP_QCOMPUTE_RESULT_VALIDATE = "qcompute.result.validate"
CAP_QCOMPUTE_EVIDENCE_BUILD = "qcompute.evidence.build"
CAP_QCOMPUTE_POLICY_EVALUATE = "qcompute.policy.evaluate"
CAP_QCOMPUTE_GOVERNANCE_REVIEW = "qcompute.governance.review"
CAP_QCOMPUTE_STUDY_RUN = "qcompute.study.run"

CANONICAL_CAPABILITIES = frozenset({
    CAP_QCOMPUTE_CASE_COMPILE,
    CAP_QCOMPUTE_ENV_PROBE,
    CAP_QCOMPUTE_CIRCUIT_COMPILE,
    CAP_QCOMPUTE_CIRCUIT_RUN,
    CAP_QCOMPUTE_RESULT_VALIDATE,
    CAP_QCOMPUTE_EVIDENCE_BUILD,
    CAP_QCOMPUTE_POLICY_EVALUATE,
    CAP_QCOMPUTE_GOVERNANCE_REVIEW,
    CAP_QCOMPUTE_STUDY_RUN,
})
```

## 6.4 Manifest 注册

### 6.4.1 入口清单 (`manifest.json`)

```json
{
  "name": "qcompute_gateway",
  "version": "0.1.0",
  "kind": "core",
  "entry": "metaharness_ext.qcompute.gateway:QComputeGatewayComponent",
  "harness_version": ">=0.1.0",
  "contracts": {
    "inputs": [
      {"name": "experiment_spec", "type": "QComputeExperimentSpec", "required": true}
    ],
    "outputs": [
      {"name": "evidence_bundle", "type": "QComputeEvidenceBundle", "mode": "sync"}
    ],
    "events": [],
    "provides": [
      {"name": "qcompute.compile.case", "description": "Compile quantum experiment spec into run plan"}
    ],
    "requires": [
      {"name": "qcompute.environment.probe", "description": "Probe backend availability and noise"},
      {"name": "qcompute.circuit.compile", "description": "Compile circuit with transpilation"},
      {"name": "qcompute.circuit.run", "description": "Execute circuit on quantum backend"},
      {"name": "qcompute.result.validate", "description": "Validate quantum execution results"}
    ],
    "slots": [
      {"slot": "qcompute_gateway.primary", "binding": "primary", "required": true}
    ]
  },
  "safety": {
    "protected": false,
    "mutability": "mutable",
    "sandbox_profile": "workspace-read",
    "hot_swap": true
  },
  "policy": {
    "sandbox": {"tier": "workspace-read"},
    "credentials": {
      "requires_subject": false,
      "allow_inline_credentials": true,
      "required_claims": []
    }
  },
  "state_schema_version": 1,
  "deps": {
    "components": [
      "qcompute_environment",
      "qcompute_config_compiler",
      "qcompute_executor",
      "qcompute_validator"
    ],
    "capabilities": []
  },
  "optional_deps": {
    "components": ["qsteed_compiler"],
    "capabilities": ["error_mitigation.zne", "error_mitigation.mem"]
  },
  "bins": ["qsteed (optional)"],
  "env": [],
  "provides": [
    "qcompute.compile.case"
  ],
  "requires": [
    "qcompute.environment.probe",
    "qcompute.circuit.compile",
    "qcompute.circuit.run",
    "qcompute.result.validate"
  ],
  "enabled": true
}
```

### 6.4.2 Validator 清单（protected component）

```json
{
  "name": "qcompute_validator",
  "version": "0.1.0",
  "kind": "governance",
  "entry": "metaharness_ext.qcompute.validator:QComputeValidatorComponent",
  "harness_version": ">=0.1.0",
  "contracts": {
    "inputs": [
      {"name": "artifact", "type": "QComputeRunArtifact", "required": true},
      {"name": "plan", "type": "QComputeRunPlan", "required": true},
      {"name": "environment_report", "type": "QComputeEnvironmentReport", "required": true}
    ],
    "outputs": [
      {"name": "validation_report", "type": "QComputeValidationReport", "mode": "sync"}
    ],
    "provides": [
      {"name": "qcompute.result.validate", "description": "Validate quantum execution results"}
    ],
    "slots": [
      {"slot": "qcompute_validator.primary", "binding": "primary", "required": true}
    ]
  },
  "safety": {
    "protected": true,
    "mutability": "mutable",
    "sandbox_profile": "workspace-read",
    "hot_swap": false
  },
  "policy": {
    "sandbox": {"tier": "workspace-read"},
    "credentials": {
      "requires_subject": false,
      "allow_inline_credentials": true,
      "required_claims": []
    }
  },
  "state_schema_version": 1,
  "provides": ["qcompute.result.validate"],
  "enabled": true
}
```

## 6.5 Manifest 治理语义

当前 strengthened MHE 语义下，manifest 承担明确的治理声明责任。QCompute 文档层应清晰表达以下字段语义：

| 字段 | QCompute 语义 |
|------|-------------|
| `kind` | Gateway/Environment/ConfigCompiler/Executor 为 `"core"`；Validator 为 `"governance"`；Study 为 `"core"` |
| `safety.protected` | Validator 为 `true`（protected governance component），其余为 `false` |
| `policy.credentials` | `requires_subject=False`：量子 API token 通过环境变量注入，不在 manifest 中声明 |
| `policy.sandbox` | Executor 需要 `workspace-write`（保存 raw_output）；其余使用 `workspace-read` |
| `bins` | 不依赖外部二进制文件（通过 Python SDK 交互）；可选 `qsteed` |
| `optional_deps` | 可选集成：QSteed（编译加速）、Mitiq（错误缓解）、TensorCircuit（模拟器） |
| `env` | 运行时需注入：`QUAFU_API_TOKEN`（真机必需）、`QISKIT_CACHE_DIR`（可选）；MCP 通道需 `ALIBABA_API_KEY` |

## 6.6 依赖关系图

```
qcompute_gateway
  ├─ requires → qcompute_environment
  ├─ requires → qcompute_config_compiler
  ├─ requires → qcompute_executor
  └─ requires → qcompute_validator

qcompute_config_compiler
  └─ optional → qsteed_compiler (VQPU selection for Quafu)

qcompute_executor
  └─ optional → mitiq (error mitigation via execute_with_zne)

qcompute_study
  ├─ requires → qcompute_gateway
  └─ requires → qcompute_validator

qcompute_validator [PROTECTED]
  └─ (被 gateway 和 study 依赖)
```

## 6.7 扩展注册到 pyproject.toml

`metaharness_ext` 是命名空间包，已由现有 `pyproject.toml` 覆盖：

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/metaharness_ext"]
```

QCompute 不需要修改构建配置。只需将文件放入 `src/metaharness_ext/qcompute/`，
MHE 的 `ComponentDiscovery` 会自动扫描 `*.json` 并注册组件。

## 6.8 运行时初始化

```python
# __init__.py
from metaharness_ext.qcompute.contracts import (
    QComputeExperimentSpec,
    QComputeBackendSpec,
    QComputeCircuitSpec,
    QComputeNoiseSpec,
    QComputeRunPlan,
    QComputeRunArtifact,
    QComputeEnvironmentReport,
    QComputeValidationReport,
    QComputeValidationMetrics,
    QComputeEvidenceBundle,
    QComputeStudySpec,
    QComputeStudyReport,
    QComputeExecutionMode,
    QComputeValidationStatus,
)
from metaharness_ext.qcompute.capabilities import (
    CAP_QCOMPUTE_CASE_COMPILE,
    CAP_QCOMPUTE_ENV_PROBE,
    CAP_QCOMPUTE_CIRCUIT_COMPILE,
    CAP_QCOMPUTE_CIRCUIT_RUN,
    CAP_QCOMPUTE_RESULT_VALIDATE,
    CANONICAL_CAPABILITIES,
)
from metaharness_ext.qcompute.slots import (
    QCOMPUTE_GATEWAY_SLOT,
    QCOMPUTE_VALIDATOR_SLOT,
    PROTECTED_SLOTS,
)
```

## 6.9 错误缓解实现路径

QCompute 不自行实现错误缓解算法。首版通过 Mitiq 标准库集成：

```python
# metaharness_ext/qcompute/executor.py
from mitiq import zne
from mitiq.zne.scaling import fold_global

async def _apply_error_mitigation(self, circuit, mitigation_strategies, executor_func):
    if "zne" in mitigation_strategies:
        result = zne.execute_with_zne(
            circuit,
            executor_func,
            factory=zne.inference.AdaExpFactory(scale_factor=2.0, steps=5),
            scale_noise=fold_global,
        )
    return result
```

Mitiq 的优势：
- 跨后端兼容（Qiskit, Cirq, pyQuafu）
- 活跃维护（Unitary Foundation 开源项目）
- 支持 ZNE, PEC, Dynamical Decoupling 等多种技术
- `AdaExpFactory` 自适应选择噪声缩放因子，减少人工调参
