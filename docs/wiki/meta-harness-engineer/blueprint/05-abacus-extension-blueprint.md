# 05. ABACUS Extension Blueprint

> 状态：proposed | 面向 `MHE/src/metaharness_ext/abacus` 的正式实现蓝图

## 5.1 目标

`metaharness_ext.abacus` 的目标，是把 ABACUS 的稳定控制面以 **受控、可声明、可验证、可审计** 的方式接入 MHE，而不是把它包装成任意 shell 运行器。

ABACUS 的正式运行模型可以概括为：

```text
typed spec
  -> INPUT / STRU / KPT + assets
  -> launcher + abacus
  -> OUT.<suffix>/ + logs + structures + restart artifacts
  -> structured validation
```

因此首版扩展的核心职责是：

1. 用 typed contracts 表达 ABACUS 的受控输入边界
2. 将 spec 编译成稳定输入文件集，而不是允许任意自由文本透传
3. 用可审计的 workspace + launcher 运行 ABACUS
4. 收集 family-aware artifacts 与 evidence
5. 生成 environment-aware、artifact-aware 的 validator/report

---

## 5.2 设计立场

ABACUS 的控制面与 DeepMD、JEDI、Nektar 都不同：

- 与 DeepMD 相比：不是 `JSON + workspace`，而是 `INPUT/STRU/KPT + workspace`
- 与 JEDI 相比：不是 YAML-first，而是固定文件名工作目录模型
- 与 Nektar 相比：不是 XML/session plan，而是多文件输入目录语义

因此 ABACUS extension 的首版应明确选择：

- **compiler-first** 设计
- **environment probe 先于执行**
- **artifact/evidence 先于 return code**
- **family-aware** contracts，而不是单一 giant config dict

---

## 5.3 首版 family 与 mode

推荐首版 family：

- `scf`
- `nscf`
- `relax`
- `md`

推荐首版关键 mode 维度：

- `basis_type`: `pw`, `lcao`
- `launcher`: `direct`, `mpirun`, `mpiexec`, `srun`
- `esolver_type`: `ksdft`, `dp`

其中 `esolver_type=dp` 应被视为 ABACUS extension 内部的一个 mode，而不是另一套扩展边界。

---

## 5.4 首版组件链

```text
AbacusGateway
  -> AbacusEnvironmentProbe
    -> AbacusInputCompiler
      -> AbacusExecutor
        -> AbacusValidator
```

### Gateway
- 规范化 request
- 选择 family
- 拒绝超出首版边界的组合

### Environment Probe
- `abacus --version`
- `abacus --info`
- `abacus --check-input`
- launcher availability
- required runtime paths
- DeePMD / GPU / optional feature availability

### Input Compiler
- 生成 `INPUT`
- 生成 `STRU`
- 需要时生成 `KPT`
- 规范 `suffix`
- 输出 `AbacusRunPlan`

### Executor
- 准备 workspace
- 落盘输入文件
- 调用 launcher + `abacus`
- 收集 stdout/stderr
- 发现 `OUT.<suffix>/` 与关键产物

### Validator
- 区分 environment / input / runtime / validation failure
- 按 family 进行最小成功判定
- 输出 evidence-oriented report

---

## 5.5 推荐未来包结构

```text
MHE/src/metaharness_ext/abacus/
├── __init__.py
├── capabilities.py
├── slots.py
├── contracts.py
├── gateway.py
├── environment.py
├── input_compiler.py
├── executor.py
├── validator.py
├── manifest.json
├── environment.json
├── input_compiler.json
├── executor.json
└── validator.json
```

同时建议配套：

```text
MHE/examples/manifests/abacus/
MHE/examples/graphs/abacus-minimal.xml
MHE/tests/test_metaharness_abacus_manifest.py
MHE/tests/test_metaharness_abacus_executor.py
MHE/tests/test_metaharness_abacus_minimal_demo.py
```

---

## 5.6 contracts 设计原则

首版 contracts 应满足：

- family-aware
- file-aware
- artifact-aware
- environment-aware

推荐核心 contracts：

- `AbacusExecutableSpec`
- `AbacusStructureSpec`
- `AbacusKPointSpec`
- `AbacusRunSpec`
- `AbacusScfSpec`
- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- `AbacusMdSpec`
- `AbacusEnvironmentReport`
- `AbacusRunPlan`
- `AbacusRunArtifact`
- `AbacusValidationReport`

边界原则：

- 不做任意 `INPUT` 文本 passthrough 的首版默认能力
- 不承诺所有 ABACUS 字段在首版都进入强类型 schema
- 先覆盖首版 family 需要的稳定字段

---

## 5.7 artifact 与 validator 设计

ABACUS extension 的 evidence surface 应围绕 `OUT.<suffix>/` 组织。

推荐 artifact 类别：

- rendered input files
- stdout/stderr
- output root
- effective input snapshot
- log files
- structure files
- restart files
- diagnostic files

推荐 validator 状态：

- `environment_invalid`
- `input_invalid`
- `runtime_failed`
- `validation_failed`
- `executed`

family-aware success 规则：

- `scf`: `OUT.<suffix>/` 存在且关键日志/输出存在
- `nscf`: 输出存在且相关前提满足
- `relax`: final structure evidence 存在
- `md`: `MD_dump` / `Restart_md.dat` / `STRU_MD_*` 等证据存在
- `md + dp`: 额外要求 DPMD mode 前提成立

---

## 5.8 DPMD-in-ABACUS 边界

ABACUS 文档中，DPMD 的接入路径是：

```text
calculation = md
esolver_type = dp
pot_file = model.pb
```

所以 blueprint 必须明确：

- 这是 `AbacusMdSpec` 的一种 mode-aware variant
- 它属于 `metaharness_ext.abacus`
- environment probe 必须判断 DeePMD support
- compiler 必须把 `pot_file` 作为 typed asset 处理
- validator 必须把该模式的前提与产物纳入成功标准

---

## 5.9 首版非目标

- 任意自由文本 `INPUT` 透传
- 任意 ABACUS feature 的全量强类型覆盖
- 完整 HPC 作业调度平台
- 任意外部后处理链自动集成
- 将 DeePMD native train/test/freeze/compress workflow 合并进本扩展

---

## 5.10 结论

ABACUS extension 最适合在 MHE 中被设计成一个 **file-driven, launcher-aware, evidence-first** 的 solver extension。

它与 DeepMD extension 的结构同构之处在于：

```text
gateway -> environment -> compiler -> executor -> validator
```

不同之处在于：

- DeepMD 的控制面是 `JSON + workspace`
- ABACUS 的控制面是 `INPUT/STRU/KPT + workspace + launcher`

因此首版的关键，不是追求功能大而全，而是先建立一套正确的 typed boundary、workspace 语义与 artifact-aware validator。