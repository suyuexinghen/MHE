# 05. ABACUS Extension Blueprint

> 状态：merged current baseline | 以 `MHE/src/metaharness_ext/abacus` 与 `abacus-engine-wiki` 为准整理的实现蓝图

## 5.1 目标

`metaharness_ext.abacus` 的目标，是把 ABACUS 的稳定控制面以 **受控、可声明、可验证、可审计** 的方式接入 MHE，而不是把它包装成任意 shell 运行器，也不是在扩展内部重复实现一套独立 runtime / promotion 系统。

当前更可靠的实现基线来自：

- `MHE/src/metaharness_ext/abacus/`
- `MHE/tests/test_metaharness_abacus_*.py`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/.trash/abacus-engine-wiki/04-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/.trash/abacus-engine-wiki/05-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/.trash/abacus-engine-wiki/06-implementation-hardening-checklist.md`

ABACUS 的运行模型可以概括为：

```text
typed spec
  -> INPUT / STRU / KPT + assets
  -> launcher + abacus
  -> OUT.<suffix>/ + logs + structures + restart artifacts
  -> evidence-first validation
```

因此当前实现蓝图的核心职责是：

1. 用 typed contracts 表达 ABACUS 的受控输入边界
2. 将 spec 编译成稳定输入文件集，而不是允许任意自由文本透传
3. 用可审计的 workspace + launcher 运行 ABACUS
4. 收集 family-aware artifacts 与 evidence
5. 生成 environment-aware、artifact-aware、governance-aware 的 validator/report
6. 让本地 evidence 结构能被 MHE 的 promotion / policy / session / audit / provenance 主路径稳定消费

---

## 5.2 设计立场

ABACUS 的控制面与 DeepMD、JEDI、Nektar 都不同：

- 与 DeepMD 相比：不是 `JSON + workspace`，而是 `INPUT/STRU/KPT + workspace`
- 与 JEDI 相比：不是 YAML-first，而是固定文件名工作目录模型
- 与 Nektar 相比：不是 XML/session plan，而是多文件输入目录语义

因此 ABACUS extension 的当前设计立场应保持：

- **compiler-first** 设计
- **environment probe 先于执行**
- **artifact/evidence 先于 return code**
- **family-aware** contracts，而不是单一 giant config dict
- **validator 产出 promotion-ready validation semantics，但不直接等同于 graph promotion**

ABACUS 是运行在 strengthened MHE 宿主中的 extension。它的 gateway / environment / compiler / executor / validator 输出，最终应能进入统一的：

- `PromotionContext`
- `ValidationIssue.blocks_promotion`
- manifest `policy.credentials` / `policy.sandbox`
- session / audit / provenance evidence flow
- `ScoredEvidence`

但这些治理能力仍由宿主 runtime 承担，而不是由 ABACUS 自己重建。

---

## 5.3 当前 family 与 mode

当前已落地并进入同一套 typed workflow 的 family：

- `scf`
- `nscf`
- `relax`
- `md`

关键 mode 维度：

- `basis_type`: `pw`, `lcao`
- `launcher`: `direct`, `mpirun`, `mpiexec`, `srun`
- `esolver_type`: `ksdft`, `dp`

其中：

- `esolver_type=dp` 被视为 ABACUS 内部的一个 mode，而不是第二套扩展
- `md + esolver_type=dp + pot_file` 已按 typed baseline 建模
- 当 `abacus --info` 无法明确确认 DeePMD support 时，当前实现按保守策略阻断该 mode

---

## 5.4 当前组件链

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
- 拒绝超出当前支持边界的组合
- 后续需要把 manifest credential / subject / claim 边界写得更明确

### Environment Probe
- `abacus --version`
- `abacus --info`
- `abacus --check-input`
- launcher availability
- required runtime paths
- DeePMD / GPU / optional feature availability
- 输出结构化 prerequisite / missing prerequisite 事实，而不是只给本地日志
- 产出 lifecycle-aware 的环境对象：prerequisite 状态、消息与 environment-scoped `evidence_refs`

### Input Compiler
- 生成 `INPUT`
- 生成 `STRU`
- 需要时生成 `KPT`
- 规范 `suffix`
- 输出 `AbacusRunPlan`
- 将控制文件、运行资产、workspace 布局与期望输出组织成稳定的 lifecycle plan 对象

### Executor
- 准备 workspace
- 落盘输入文件
- 调用 launcher + `abacus`
- 收集 stdout/stderr
- 发现 `OUT.<suffix>/` 与关键产物
- 将 prepared inputs、workspace 布局、output root 与 family-aware artifact groups 汇总成稳定 run artifact 对象
- 后续需要更显式对齐 manifest `policy.sandbox` 与稳定 evidence anchors

### Validator
- 区分 `environment_invalid` / `input_invalid` / `runtime_failed` / `validation_failed` / `executed`
- 按 family 进行最小成功判定
- 当前已是 protected governance component
- 当前已输出 `issues`、`blocks_promotion`、`ScoredEvidence` 与 canonical `evidence_refs`
- 成功校验当前表示可进入后续 review 的 governance-shaped baseline，而不等于直接 graph promotion

---

## 5.5 当前包结构与配套资产

当前仓库已落地：

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
├── gateway.json
├── environment.json
├── input_compiler.json
├── executor.json
└── validator.json
```

当前已配套：

```text
MHE/examples/manifests/abacus/
MHE/examples/graphs/abacus-minimal.xml
MHE/tests/test_metaharness_abacus_manifest.py
MHE/tests/test_metaharness_abacus_executor.py
MHE/tests/test_metaharness_abacus_gateway.py
MHE/tests/test_metaharness_abacus_minimal_demo.py
MHE/tests/test_metaharness_abacus_environment.py
MHE/tests/test_metaharness_abacus_validator.py
```

因此后续重点已经不是“创建骨架”，而是：

- 补齐 governance-facing contract/report/evidence surface
- 把 manifest policy 从隐含语义变成显式声明
- 让 blueprint / roadmap / checklist 与当前代码现实重新对齐

---

## 5.6 contracts 设计原则

ABACUS contracts 当前应满足：

- family-aware
- file-aware
- artifact-aware
- environment-aware
- governance-alignment-aware

核心 contracts：

- `AbacusExecutableSpec`
- `AbacusStructureSpec`
- `AbacusKPointSpec`
- `AbacusScfSpec`
- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- `AbacusMdSpec`
- `AbacusEnvironmentReport`
- `AbacusRunPlan`
- `AbacusRunArtifact`
- `AbacusValidationReport`

这些类型当前应被理解为一组嵌套 lifecycle 对象，而不是彼此独立的扁平记录：

- control-file objects：`INPUT` / `STRU` / `KPT` 的 canonical 内容与相关 spec
- runtime-asset objects：pseudo、orbital、`pot_file`、restart / charge density 等执行前置资产
- workspace-layout objects：`working_directory`、prepared inputs、`OUT.<suffix>/` 与输出空间关系
- artifact-group objects：logs、diagnostics、structure / restart / family-specific outputs
- lifecycle-state objects：environment、run、validation 三段状态与对应 evidence handoff

当前边界原则：

- 不做任意 `INPUT` 文本 passthrough 的默认能力
- 不承诺所有 ABACUS 字段都进入强类型 schema
- 先覆盖已落地 family/mode 的稳定字段
- 后续治理对齐优先采用共享 MHE 类型，而不是发明 ABACUS 私有治理模型

后续本轮实现应把 `AbacusValidationReport` / `AbacusRunArtifact` 补齐为可承载：

- `ValidationIssue`
- `blocks_promotion`
- `ScoredEvidence`
- canonical `evidence_refs`

---

## 5.7 artifact、validator 与 runtime evidence

ABACUS extension 的 evidence surface 仍然应围绕 `OUT.<suffix>/` 组织。

当前 artifact 类别包括：

- rendered input files
- stdout/stderr
- output root
- log files
- structure files
- diagnostic files
- family-specific output files

当前 validator 状态：

- `environment_invalid`
- `input_invalid`
- `runtime_failed`
- `validation_failed`
- `executed`

family-aware success 规则：

- `scf`: `OUT.<suffix>/` 存在且关键日志/输出存在
- `nscf`: 输出存在且相关前提满足
- `relax`: final structure evidence 存在
- `md`: `MD_dump` / `Restart_md*` / `STRU_MD*` 等证据存在
- `md + dp`: 额外要求 DeePMD prerequisite 满足

但当前蓝图要求进一步补齐：

- validator 结果要能表达 `blocks_promotion`
- evidence 不只保留文件路径，还要能导出 canonical `evidence_refs`
- 成功执行不自动等于 graph promotion；它只代表当前 evidence baseline 成立
- 本地 artifact/report 结构需要能被 session / audit / provenance 稳定消费

推荐运行时对接形状：

- 文件路径继续保留，供本地审阅和测试使用
- 并行生成 run-scoped / validation-scoped evidence refs
- `ScoredEvidence` 汇总 metrics、reasons、evidence refs、status attributes
- validator 作为 protected governance component 提供 promotion-ready validation semantics

---

## 5.8 DPMD-in-ABACUS 边界

ABACUS 中的 DPMD 接入路径仍然是：

```text
calculation = md
esolver_type = dp
pot_file = model.pb
```

因此 blueprint 必须明确：

- 这是 `AbacusMdSpec` 的一个 mode-aware variant
- 它属于 `metaharness_ext.abacus`
- environment probe 必须判断 DeePMD support
- compiler 必须把 `pot_file` 作为 typed asset 处理
- validator 必须把该模式的前提与产物纳入成功标准
- 当 DeePMD support 无法确认时，当前实现按 environment prerequisite missing 保守阻断

---

## 5.9 当前非目标

当前仍不做：

- 任意自由文本 `INPUT` 透传
- 任意 ABACUS feature 的全量强类型覆盖
- 完整 HPC 作业调度平台
- 任意外部后处理链自动集成
- 将 DeePMD native train/test/freeze/compress workflow 合并进本扩展
- 在 ABACUS extension 内部复制一套独立的 graph promotion / session runtime

当前同样不要求 ABACUS 自己实现：

- `SessionStore`
- runtime audit layer
- hot-swap orchestration
- graph commit authority

但要求它的 contracts / manifests / validator / evidence 组织方式能和这些宿主能力兼容。

---

## 5.10 结论

ABACUS extension 仍最适合在 MHE 中被设计成一个 **file-driven, launcher-aware, evidence-first** 的 solver extension。

当前下一步不是再扩一轮基础 workflow，而是把已有 family/mode 基线对齐到 strengthened MHE 的治理语义：

- manifest `policy.credentials` / `policy.sandbox`
- validator `issues` / `blocks_promotion`
- `ScoredEvidence`
- canonical `evidence_refs`
- promotion-ready validation does not equal graph promotion

因此这份 merged blueprint 的用途，是作为后续 ABACUS 代码与 wiki 同步更新的统一架构底稿。