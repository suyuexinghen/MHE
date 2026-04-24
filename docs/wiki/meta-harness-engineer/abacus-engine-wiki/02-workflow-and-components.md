# 02. ABACUS 工作流与组件链

## 2.1 组件链总览

首版 `metaharness_ext.abacus` 建议采用如下最小组件链：

```text
AbacusGateway
  -> AbacusEnvironmentProbe
    -> AbacusInputCompiler
      -> AbacusExecutor
        -> AbacusValidator
```

这条链的目标是把 ABACUS 的固定工作目录模型纳入 MHE，而不是把它抽象成任意命令执行器。

### 与 MHE promotion path 的关系

这条组件链的输出，首先服务于 ABACUS extension 内部的 environment / execution / validation 语义，但最终并不自行决定 graph promotion。按照当前 strengthened MHE 语义，ABACUS 组件链产出的 artifact、validation report 与 evidence refs，应作为 `HarnessRuntime.commit_graph()` 之后统一 candidate promotion path 的上游输入；是否进入 active graph，仍由 runtime-level promotion authority、policy review 与 protected governance boundary 共同决定。

---

## 2.2 组件职责

### `AbacusGateway`

职责：

- 接收高层 request
- 规范化 `AbacusRunSpec` 及 family-aware variants
- 决定执行 family：`scf` / `nscf` / `relax` / `md`
- 约束 `basis_type`、`launcher`、`esolver_type` 的首版合法组合
- 在进入 compiler / executor 前收紧 manifest 声明输入边界，尤其是 credential subject / claim、required paths 与 launcher / binary 请求不能越过 manifest policy surface

### `AbacusEnvironmentProbe`

职责：

- 检查 `abacus` 是否存在
- 读取 `abacus --version`
- 读取 `abacus --info` 并识别构建特性
- 检查 `abacus --check-input` 是否可用
- 检查 launcher：`mpirun` / `mpiexec` / `srun`
- 检查 required runtime paths：
  - `STRU`
  - `KPT`（按模式可选）
  - 伪势 / 轨道文件（按 basis / mode 可选）
  - DPMD `pot_file`
- 将环境探测结果保留为 prerequisites evidence：它不仅决定“能不能跑”，也为后续 validator / policy review 提供前提满足、缺失项与保守阻断的证据基础

### `AbacusInputCompiler`

职责：

- 把 typed spec 编译成稳定的 `INPUT`
- 编译 `STRU`
- 在需要时编译 `KPT`
- 控制 `suffix` 与输出目录命名
- 不允许无约束 `INPUT` 文本透传成为默认路径

### `AbacusExecutor`

职责：

- 准备运行目录
- 落盘 `INPUT` / `STRU` / `KPT`
- 按 launcher 语义运行 `abacus`
- 收集 stdout / stderr / return code
- 发现 `OUT.<suffix>/` 与关键输出文件
- 在 MD 模式下收集 restart / trajectory / 结构演化证据
- 执行时遵守 manifest / runtime policy surface 中已经声明的 launcher、binary、sandbox tier 与 workspace 边界，而不是在 executor 内部额外扩权

### `AbacusValidator`

职责：

- 将 environment、运行结果与 artifact 统一映射为稳定判定
- 区分 `environment_invalid`、`input_invalid`、`runtime_failed`、`validation_failed`、`executed`
- 按 family 判断最小成功条件
- 对 DPMD mode 做额外条件检查
- 作为 governance component 处于 protected boundary，不能被隐式绕过或退化成可选 helper
- 把关键失败提升为 promotion-blocking evidence 候选，并与 policy review 协作区分“没跑起来”“跑了但证据不足”“工程上通过但仍需治理审核”

---

## 2.3 ABACUS 的 file-driven workflow

ABACUS 的核心运行语义不是“传一堆 CLI 参数”，而是：

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

## 2.4 launcher 与执行语义

ABACUS 并行模式通常依赖外部 launcher：

- `direct`
- `mpirun`
- `mpiexec`
- `srun`

因此执行计划中至少要显式表达：

- `binary_name`
- `launcher`
- `num_ranks` / `omp_threads` 等未来可能字段
- working directory
- environment variables

建议首版把 launcher 语义写进 `AbacusExecutableSpec`，而不是在 executor 里隐式猜测。

---

## 2.5 family-aware workflow

### `scf`

最小链：

```text
typed scf spec
  -> INPUT/STRU/KPT
  -> abacus run
  -> OUT.<suffix>/INPUT + SCF log + result files
  -> validator
```

### `nscf`

相较于 `scf`，需要更强调前置 charge / read-file 依赖的显式表达。

### `relax`

除了普通输出外，validator 还要关注最终结构证据，如：

- `STRU.cif`
- relaxed structure outputs

### `md`

需要把下列内容纳入正式 artifact surface：

- `MD_dump`
- `Restart_md.dat`
- `STRU/STRU_MD_<step>`

---

## 2.6 ABACUS+DeePMD mode

在 ABACUS 文档里，DeePMD 不是单独 CLI 工作流，而是 ABACUS 的一种运行配置：

```text
calculation = md
esolver_type = dp
pot_file = <model.pb>
```

这意味着在组件链里它属于：

- `AbacusMdSpec` 的一个受控 variant
- `AbacusEnvironmentProbe` 需要检查 DeePMD support
- `AbacusInputCompiler` 需要加入 `pot_file`
- `AbacusValidator` 需要识别 DPMD mode 的额外前提与证据

---

## 2.7 推荐输出目录与 artifact 视图

建议 `AbacusRunArtifact` 至少组织为以下类别：

- `input_files`
- `stdout_path`
- `stderr_path`
- `output_root`（即 `OUT.<suffix>/`）
- `effective_input_path`
- `log_files`
- `structure_files`
- `restart_files`
- `diagnostic_files`

这样可以让 validator 与后续 evidence manager 在不重新扫描目录的情况下消费稳定产物。

这些 artifact 目录视图还应被理解为 runtime evidence handoff 面：ABACUS extension 负责把关键输入、输出、diagnostics 与 prerequisite evidence 稳定组织出来，后续 session event、audit record、provenance link 与 candidate/graph version 锚点则由 strengthened MHE 的统一治理路径继续承接。

---

## 2.8 首版最小 happy path

首版最小 happy path 应优先选择：

```text
SCF (direct or launcher-driven) 
  -> typed spec
  -> compiler emits INPUT/STRU/KPT
  -> executor runs abacus
  -> validator confirms OUT.<suffix>/ and key outputs
```

原因：

- SCF 是最小且最通用的基础路径
- 它能验证 file-driven compiler、launcher 语义和 `OUT.<suffix>/` artifact surface
- 为后续 `nscf` / `relax` / `md` 提供最稳定的基线

但从 workspace / artifact 成功到 active graph promotion 之间，仍有统一治理门。也就是说，happy path 的终点应理解为 promotion-ready candidate outcome：ABACUS 已产出足够工程证据与最小验证结论，但是否晋升到 active graph，仍要经过 runtime-level promotion authority、policy 审核与 protected governance boundary 的共同裁决。
