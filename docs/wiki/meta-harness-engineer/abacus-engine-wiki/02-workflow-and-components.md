# 02. 工作流与组件链

## 2.1 canonical 组件链

`metaharness_ext.abacus` 的当前设计主轴是：

```text
AbacusGatewayComponent
  -> AbacusEnvironmentProbeComponent
    -> AbacusInputCompilerComponent
      -> AbacusExecutorComponent
        -> AbacusValidatorComponent
```

这条链的目标，是把 ABACUS 的固定工作目录模型纳入 MHE，而不是把它抽象成任意命令执行器。

---

## 2.2 组件职责

### `gateway.py`

`AbacusGatewayComponent` 当前负责 task shaping：

- 输出 `AbacusExperimentSpec`
- 选择 `scf` / `nscf` / `relax` / `md` family
- 为最小 family-aware entry 提供受控任务入口

它不是 policy engine，也不直接承担更宽泛的治理职责。

### `environment.py`

`AbacusEnvironmentProbeComponent` 负责 environment probe：

- 检查 `abacus` binary
- best-effort 运行 `--version` / `--info` / `--check-input`
- 检查 launcher availability
- 检查 required runtime paths
- 对 `md + dp` 相关 DeePMD support 采用保守 prerequisite 语义

它的职责是把环境事实前置暴露，而不是自动修复环境。

### `input_compiler.py`

`AbacusInputCompilerComponent` 负责：

- 渲染稳定 `INPUT`
- 渲染 `STRU`
- 在需要时渲染 `KPT`
- 固化 `suffix` 与 output root 预期
- 输出 `AbacusRunPlan`

它不应退化成任意 `INPUT` 文本 passthrough。

### `executor.py`

`AbacusExecutorComponent` 负责：

- 准备 workspace
- 落盘输入文件
- 构造 launcher + `abacus` 命令
- 收集 stdout / stderr / return code
- 发现 `OUT.<suffix>/` 与 family-aware artifacts

executor 的职责是产生 run artifact，而不是决定最终治理判据。

### `validator.py`

`AbacusValidatorComponent` 是当前 extension-local 的 protected governance boundary：

- 解释 environment、artifact 与运行结果
- 区分 `environment_invalid` / `input_invalid` / `runtime_failed` / `validation_failed` / `executed`
- 产出 `AbacusValidationReport`
- 承载 `issues`、`blocks_promotion`、`governance_state` 与 `ScoredEvidence` 接缝

当前真正受保护的是 validator 所在边界，而不是整个扩展包中的所有组件。

---

## 2.3 ABACUS 的 file-driven workflow

ABACUS 的核心运行语义是：

```text
workspace
  |- INPUT
  |- STRU
  |- KPT        (optional by mode)
  |- pseudo/orbital/model assets
  -> launcher + abacus
  -> OUT.<suffix>/...
```

这对扩展设计有三个直接影响：

1. compiler 是正式主组件，而不是辅助工具
2. workspace 布局是执行语义的一部分
3. validator 需要围绕 `OUT.<suffix>/` 组织证据收集

---

## 2.4 family-aware workflow

### `scf`

最小链：

```text
AbacusScfSpec
  -> INPUT/STRU/KPT
  -> abacus run
  -> OUT.<suffix>/INPUT + SCF logs + result evidence
  -> validator
```

### `nscf`

相较于 `scf`，需要更强调前置 charge / restart 依赖的显式表达。

### `relax`

除了普通输出外，validator 还要关注 final structure evidence。

### `md`

需要把下列内容纳入正式 artifact surface：

- `MD_dump`
- `Restart_md.dat`
- `STRU_MD_*`

### `md + esolver_type=dp`

在 ABACUS 里，DeePMD 不是第二个扩展，而是 ABACUS 的受控 mode：

```text
calculation = md
esolver_type = dp
pot_file = <model.pb>
```

因此它属于 `AbacusMdSpec` 的一个 variant，而不是独立 family。

---

## 2.5 与 runtime authority 的关系

ABACUS 组件链的本地输出并不直接等价于 graph promotion。更准确的关系是：

- environment probe 暴露 prerequisites
- compiler 与 executor 产生 run plan / run artifact
- validator 给出 governance-aware validation result
- runtime 再基于更高层 promotion / audit / provenance authority 决定是否允许 graph promotion

因此 extension-local 的 `executed` 或 `passed=true`，只表示当前结果具备进入下游治理路径的资格，不表示 graph 已自动晋升。

---

## 2.6 结论

ABACUS 扩展的组件链重点不在“再造求解器”，而在：

- 固化输入文件边界
- 固化 workspace 与 launcher 语义
- 固化 validator 的 protected boundary
- 固化 evidence / governance handoff 面

这也是为什么它可以一边继续开发，一边保持设计边界清晰。
