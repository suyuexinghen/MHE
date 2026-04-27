# 06. 封装与注册

## 6.1 包结构

```text
MHE/src/metaharness_ext/octave/
├── __init__.py
├── capabilities.py          # capability 常量定义
├── slots.py                 # slot 常量定义
├── types.py                 # 基础类型
├── contracts.py             # 所有 typed contracts (Pydantic models)
├── gateway.py               # OctaveGateway
├── environment.py           # OctaveEnvironmentProbe
├── script_compiler.py       # OctaveScriptCompiler
├── executor.py              # OctaveExecutor
├── validator.py             # OctaveValidator
├── evidence.py              # OctaveEvidenceBundle / OctaveEvidencePolicy
├── policy.py                # governance_state 判定
├── study.py                 # OctaveStudyComponent (Phase 5)
├── workspace.py             # workspace staging 工具
├── manifest.json            # extension manifest
├── gateway.json             # component manifests
├── environment.json
├── script_compiler.json
├── executor.json
└── validator.json
```

配套资产：

```text
MHE/examples/manifests/octave/
MHE/examples/graphs/octave-minimal.xml
MHE/examples/octave/
MHE/tests/test_metaharness_octave_contracts.py
MHE/tests/test_metaharness_octave_manifest.py
MHE/tests/test_metaharness_octave_environment.py
MHE/tests/test_metaharness_octave_compiler.py
MHE/tests/test_metaharness_octave_executor.py
MHE/tests/test_metaharness_octave_validator.py
MHE/tests/test_metaharness_octave_gateway.py
MHE/tests/test_metaharness_octave_minimal_demo.py
MHE/docs/wiki/meta-harness-engineer/octave-engine-wiki/
```

## 6.2 Gateway Manifest 示例

```json
{
  "name": "octave_gateway",
  "version": "0.1.0",
  "kind": "custom",
  "entry": "metaharness_ext.octave.gateway:OctaveGatewayComponent",
  "harness_version": ">=0.1.0",
  "contracts": {
    "inputs": [
      {"name": "experiment_spec", "type": "OctaveExperimentSpec", "required": true}
    ],
    "outputs": [
      {"name": "task", "type": "OctaveExperimentSpec", "mode": "sync"}
    ],
    "events": [],
    "provides": [
      {"name": "octave.task.issue"}
    ],
    "requires": [
      {"name": "octave.environment.probe"},
      {"name": "octave.script.compile"}
    ],
    "slots": [
      {"slot": "octave_gateway.primary"}
    ]
  },
  "safety": {
    "protected": false,
    "mutability": "mutable",
    "hot_swap": true
  },
  "policy": {
    "sandbox": {
      "tier": "standard"
    }
  },
  "provides": ["octave.task.issue"],
  "requires": ["octave.environment.probe", "octave.script.compile"],
  "deps": {
    "components": [],
    "capabilities": ["octave.environment.probe", "octave.script.compile"]
  },
  "bins": ["octave-cli"],
  "state_schema_version": 1
}
```

注：`kind` 使用 `"custom"`（`ComponentType` enum = `CORE | TEMPLATE | META | GOVERNANCE | CUSTOM`）。`safety.hot_swap` 为 `bool`。Sandbox tier 位于 `policy.sandbox.tier`。

## 6.3 Manifest 字段对照

| Manifest 字段 | 对应 SDK 类型 | 说明 |
|---------------|--------------|------|
| `name` | `ComponentManifest.name` | 组件名，全局唯一 |
| `kind` | `ComponentType` | CORE / TEMPLATE / META / GOVERNANCE / CUSTOM |
| `entry` | `ComponentManifest.entry` | Python 类路径 |
| `contracts.inputs` | `ContractSpec.inputs` | 输入 contract |
| `contracts.outputs` | `ContractSpec.outputs` | 输出 contract |
| `contracts.provides` | `ContractSpec.provides` | 提供的 capability |
| `contracts.requires` | `ContractSpec.requires` | 依赖的 capability |
| `contracts.slots` | `ContractSpec.slots` | 绑定的 slot |
| `safety.protected` | `SafetySpec.protected` | 是否受保护组件 |
| `safety.hot_swap` | `SafetySpec.hot_swap` | 是否支持热替换 |
| `policy.sandbox.tier` | `PolicySpec.sandbox.tier` | 沙箱层级 |

## 6.4 Validator Manifest

Validator 的 manifest 与 gateway 结构相同，差异在于：

```json
{
  "name": "octave_validator",
  "kind": "custom",
  "entry": "metaharness_ext.octave.validator:OctaveValidatorComponent",
  "safety": {
    "protected": true,
    "mutability": "mutable",
    "hot_swap": false
  },
  "contracts": {
    "slots": [{"slot": "octave_validator.primary"}]
  }
}
```

Validator 作为 protected component，`safety.protected = true`，`hot_swap = false`。

## 6.5 Slot 与 Capability 注册

```text
Slot bindings:
  octave_gateway.primary           -> OctaveGateway
  octave_environment.primary       -> OctaveEnvironmentProbe
  octave_script_compiler.primary   -> OctaveScriptCompiler
  octave_executor.primary          -> OctaveExecutor
  octave_validator.primary         -> OctaveValidator (protected)

Capabilities:
  octave.task.issue                # gateway 提供
  octave.environment.probe         # environment probe 提供
  octave.script.compile            # script compiler 提供
  octave.execute.run               # executor 提供
  octave.validate.report           # validator 提供
  octave.evidence.bundle           # evidence policy 提供
  octave.study.run                 # study component 提供 (Phase 5)
```

## 6.6 注册流程

1. 各组件 `.json` manifest 文件放在 `metaharness_ext/octave/` 下
2. `manifest.json` 作为 extension-level manifest，声明 extension 元信息
3. MHE 的 `ComponentRegistry` 在 discovery 阶段扫描 manifest 文件
4. 通过 `HarnessRuntime` 的 boot path 加载组件、验证依赖、激活组件
5. ConnectionEngine 基于 contracts 的 provides/requires 连通组件图

## 6.7 依赖声明

`deps.capabilities` 声明组件依赖的 capability，在 graph 装配时由 ConnectionEngine 验证可满足性。`bins` 声明运行时二进制依赖，由 Environment Probe 在运行时验证。
