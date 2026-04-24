# 03. Contracts 设计

## 3.1 为什么必须使用 family-aware contracts

本文档中，概念层统一使用 **application family**；代码字段统一使用 `application_family`。family 边界与 baseline 关系以 [07-family 设计](07-family-design.md) 为补充说明。

JEDI application family 在顶层 YAML 结构上并不统一：

- `variational` 有 `cost function` / `variational` / `final` / `test`
- `local_ensemble_da` 有 `driver` / `local ensemble DA`
- `hofx` 更接近 observation-path / state evaluation 工作流
- `forecast` 则偏向 model integration

因此，`JediExperimentSpec` 不能设计成一个只靠可选字段堆起来的松散对象，而应该是 **discriminated union**。

---

## 3.2 基础类型

推荐的基础类型：

```python
JediApplicationFamily = Literal[
    "variational",
    "local_ensemble_da",
    "hofx",
    "forecast",
]

JediExecutionMode = Literal["schema", "validate_only", "real_run"]

JediLauncher = Literal["direct", "mpiexec", "mpirun", "srun", "jsrun"]
```

这些类型的意义不只是 IDE 补全，而是把 MHE 对 JEDI 的支持边界写进 contract 本身。
当前 Phase 6 launcher contract 还需要显式写清 process-count 规则：

- `direct`：不注入 launcher，也不接受 process-count flag
- `mpiexec`：canonical process-count flag 为 `-n`
- `mpirun`：canonical process-count flag 为 `-n`
- `srun`：canonical process-count flag 为 `-n`
- `jsrun`：canonical process-count flag 为 `-n`

实现层要求 `process_count` 与 `launcher_args` 分层：当需要设置进程数时，必须使用 `executable.process_count`，而不是把 `-n` / `-np` / `--ntasks` 等 process-count 语义混入 `launcher_args`。advanced scheduler/resource semantics（例如 `srun`/`jsrun` 的 richer resource-set placement、binding、allocation 语义）当前仍明确不在首版 contract 内。

---

## 3.3 executable contract

推荐独立建模 executable 相关配置：

```python
class JediExecutableSpec(BaseModel):
    binary_name: str
    launcher: JediLauncher = "direct"
    execution_mode: JediExecutionMode = "validate_only"
    timeout_seconds: int | None = None
    process_count: int | None = None
    launcher_args: list[str] = Field(default_factory=list)
```

这样做的原因：

- execution mode 是执行面语义，不应散落在 family spec 顶层
- launcher / np 属于运行参数，而不是 scientific config
- schema path 只对 `schema` mode 有意义，放在 executable spec 更清晰

同时，`binary_name` 不应保持“任意字符串均可”的弱约束。实现时至少应满足以下规则之一：

- 基础约束：以 `.x` 结尾，并拒绝明显像 CTest test name 的值
- family-aware 约束：由 `application_family -> allowed binary names / binary patterns` 做白名单或模式校验
- baseline-aware 约束：在正式 baseline 中使用固定 binary mapping，而不是自由输入

这样可以把 **executable name 与 CTest test name 的混淆** 尽量前移到 contract 或 gateway 级别，而不是拖到 runtime 才暴露。

---

## 3.4 family specs

首版至少需要以下 family：

- `JediVariationalSpec`
- `JediLocalEnsembleDASpec`
- `JediHofXSpec`
- `JediForecastSpec`

其中 `variational` family 需要明确区分：

- family 是 `variational`
- `cost_type` 才是 `3D-Var` / `4D-Var` / `4DEnsVar` / `4D-Weak`
- FGAT 只能作为 `3D-Var` / `4D-Var` 内的运行语义，而不是新增独立 `cost_type`

---

## 3.5 environment / run / validation contracts

除了输入 spec，还必须显式定义输出 contract。这些 contract 的用途也不只停留在 local execution；它们还需要为 runtime-level promotion gating 提供稳定、可审计、可引用的上游输入，因此字段设计应能兼容 protected validator、policy review 与 provenance evidence 的消费路径。

### JediEnvironmentReport

记录：

- binary 是否存在
- launcher 是否可用
- libraries 是否已解析
- required paths 是否存在
- 哪些 environment/data-prep prerequisites 已就绪
- 哪些 prerequisites 缺失
- 各 ready prerequisite 对应的 evidence paths
- 详细消息列表

### JediRunPlan

记录：

- 当前 run 的 task/run identity
- command
- config path / config text
- working directory
- expected outputs / diagnostics / references
- required runtime paths
- executable spec

### JediRunArtifact

记录：

- return code
- stdout/stderr path
- schema path
- prepared inputs
- output / diagnostics / reference files
- run status

### JediValidationReport

记录：

- passed 与 status
- status taxonomy
- summary metrics
- evidence files

当前实现里，`JediValidationReport` 仍保持轻量字段面，但其语义已经不只是“本地报告是否好看”。更准确的定位是：

- validator 结果要能为 promotion-readiness 提供信号，而不只是给 extension 内部自用
- diagnostics、reference files、prerequisite evidence 要能升级成 governance-grade evidence
- validator 作为 protected governance component，其结论应可被上游 policy / promotion authority 消费，而不是被 executor 或调用侧隐式绕开
- report 侧至少应预留稳定的 candidate / graph version / session-event / audit / provenance handoff 面，避免文档继续把 `JediValidationReport` 理解成一次性终端输出

当前 taxonomy 至少包括：

- `environment_invalid`
- `validated`
- `executed`
- `validation_failed`
- `runtime_failed`

其中可以进一步按治理语义理解：

- `environment_invalid` 常对应 prerequisite missing，通常可直接进入 defer / block promotion 的候选集合
- `validation_failed` 常对应 evidence 不完整、输入约束未满足或 diagnostics 未达到当前最小 acceptance surface
- `executed` 只表示 runtime completed with evidence，不天然等于 promotion-ready，更不等于 scientific success
- 当 validator 发现关键 diagnostics/reference evidence 缺失时，这类结果应能被上游映射为 `blocks_promotion` 候选，而不是退化成普通告警

---

## 3.6 contract 设计约束

### 不透传任意 YAML

contract-first 的核心约束是：compiler 只能消费 typed spec，不能接受“随便给一段 YAML 然后顺手跑”。

### 不把 family 差异藏进 overrides

`overrides` 可以存在，但不能反过来替代 family-specific fields。否则 contract 会退化成“看上去 typed，实际还是弱类型字典”。

### 输出 contract 优先稳定性

validator/report 的首要目标是 **稳定可消费**，而不是第一天就塞满所有 scientific metrics。

先把失败分类和 evidence files 做稳，再逐步增加更强的 diagnostics summary。

---

## 3.7 一个最小的 family-to-YAML 编译示意

为了避免 `config_compiler.py` 的设计停留在抽象口号，至少应先固定一个最小编译示意。以 `JediVariationalSpec` 为例：

```text
JediVariationalSpec
  task_id
  executable.binary_name = qg4DVar.x
  cost_type = 4D-Var
  window_begin / window_length
  geometry
  background
  background_error
  observations
  variational
  output
  final
  test
    ↓
config.yaml
  cost function:
    cost type: 4D-Var
    window begin: ...
    window length: ...
    geometry: ...
    background: ...
    background error: ...
    observations: ...
  variational: ...
  output: ...
  final: ...
  test: ...
```

这个示意的意义不在于提前锁死所有键名，而在于明确：

- family-specific YAML 结构由 compiler 负责
- executable 选择与 YAML 顶层块生成是相关但分层的两个动作
- `observations`、`background`、`background error` 等块往往携带外部文件路径，因此 compiler 与 environment probe 必须通过 contract 对齐这些引用面

关于 execution mode 与 artifact layout 的配合，见 [04-执行链设计](04-execution-pipeline.md)；关于 required paths 的检查责任，见 [05-环境与验证](05-environment-and-validation.md)。

---

## 3.8 面向后续 phase 的可扩展性

好的 contract 设计应允许后续 phase 在不打破当前调用方式的前提下增加：

- preprocessor input contracts
- diagnostics summary contracts
- study / mutation contracts
- family-specific recommendation/report fields
- `ScoredEvidence` 兼容字段
- session / audit / provenance refs
- 面向 `BrainProvider` seam 的推荐与解释接口

扩展的前提是：首版边界足够清晰，而不是一开始就把所有未来字段预埋成一大堆模糊 optional。

这里还应明确一条方向性约束：JEDI 后续扩展点不只是在 compiler family 上继续加分支，也要考虑如何把 diagnostics、study outcome、validator conclusion 映射到统一 runtime evidence flow，而不与 strengthened MHE 的 session/provenance 模型冲突。