# 09. 核心对象与 I/O 模型

## 9.1 为什么需要对象与 I/O 模型页

ABACUS extension 的设计，不只是“怎么运行一次命令”，还包括：

- 哪些对象是稳定控制面
- 哪些对象是运行期资产
- 哪些对象构成输出与证据面
- 哪些对象可以被 runtime governance 消费

外部 ABACUS wiki 的一个优势，就是它把输入、模块和输出讲成稳定对象模型。对 `metaharness_ext.abacus` 来说，也需要同样的视角。

---

## 9.2 输入侧核心对象

### `INPUT`

`INPUT` 是 ABACUS 的主控制文件，负责表达：

- calculation family 相关参数
- basis / cutoff / mixing 等数值控制项
- `esolver_type`
- 与运行模式相关的关键选项

对扩展层来说，`INPUT` 的意义不是“任意文本”，而是 compiler 输出的 canonical control plane。

### `STRU`

`STRU` 负责表达体系对象：

- 晶胞 / 原子结构
- 赝势引用
- 轨道或其它结构相关资源引用

对扩展层来说，`STRU` 是 structure object 的 materialized form，而不是普通附件。

### `KPT`

`KPT` 是按需要出现的输入对象：

- 它可能是必需的
- 也可能由 family / 参数组合决定是否显式出现

因此 `KPT` 在对象模型里应被理解为 **optional but first-class** 的输入文件，而不是可有可无的附录文本。

---

## 9.3 运行资产对象

除了三份核心输入文件，ABACUS 运行还依赖一组资产对象：

- pseudo files
- orbital files
- `pot_file`
- charge density / restart inputs
- 其它 required runtime paths

这些对象的设计意义是：

- 它们不是普通说明字段，而是 execution prerequisite
- 它们应在 contracts 和 environment probe 中被显式建模
- 它们决定不同 family / mode 的真实前提

例如：

- `basis_type=lcao` 时，orbital files 是正式资产对象
- `nscf` 时，charge density / restart file 是正式前置对象
- `md + dp` 时，`pot_file` 是正式模型对象

---

## 9.4 workspace 对象

ABACUS 的 workspace 本身也是第一类对象：

```text
working_directory/
  |- INPUT
  |- STRU
  |- KPT                (optional)
  |- pseudo/orbital/model assets
  |- stdout / stderr
  |- OUT.<suffix>/
```

这意味着：

- `working_directory` 不是环境细节，而是运行对象的一部分
- 输入、资产与输出之间的空间关系是可审计语义
- validator 与后续 evidence flow 都依赖这个对象模型稳定存在

---

## 9.5 输出侧核心对象

### `OUT.<suffix>/`

对 ABACUS 扩展来说，`OUT.<suffix>/` 是当前最重要的 output root 对象。

它的设计地位高于单个 log 文件，因为：

- 它是 family-aware output discovery 的主容器
- 它通常包含 effective input snapshot
- 它承接结果文件、结构文件、诊断文件与 family-specific evidence

### logs

- `stdout`
- `stderr`
- family-specific runtime logs

这些对象是辅证，而不是唯一成功依据。

### structure / restart artifacts

某些 family 的成功面天然依赖结构或 restart 产物：

- `relax` 依赖 final structure evidence
- `md` 依赖 `MD_dump`、`Restart_md.dat`、`STRU_MD_*`

因此 output objects 不能只按“普通文件列表”理解，而要按 family-aware artifact model 理解。

---

## 9.6 contracts 中的对象映射

当前对象模型在 contracts 中大致映射为：

### spec side

- `AbacusExperimentSpec`
- family-specific task specs
- `AbacusExecutableSpec`

### plan side

- `AbacusRunPlan`
- `input_content`
- `structure_content`
- `kpoints_content`
- `required_runtime_paths`
- `output_root`

### artifact side

- `AbacusRunArtifact`
- `prepared_inputs`
- `output_files`
- `diagnostic_files`
- `structure_files`
- `evidence_refs`

### validation side

- `AbacusValidationReport`
- `evidence_files`
- `missing_evidence`
- `issues`
- `blocks_promotion`
- `scored_evidence`

因此 ABACUS extension 已经不是“字符串进、字符串出”的接口，而是一个对象逐层 materialize / validate 的模型。

---

## 9.7 与外部 ABACUS 软件对象模型的关系

外部 ABACUS wiki会讨论更底层的软件对象，例如：

- Hamiltonian
- electron state
- basis modules
- IO modules
- ESolver hierarchy

而 `abacus-engine-wiki` 关心的不是重述这些内部实现，而是把它们在扩展层投影成可治理的对象模型：

- 输入文件对象
- 运行资产对象
- output root 对象
- family-aware artifacts
- validation / evidence objects

也就是说，本 wiki 关心的是 **ABACUS 作为 external scientific backend 被 MHE 接入时，哪些对象需要成为稳定 contract**。

---

## 9.8 为什么 I/O 模型能改进设计质量

把 I/O 模型写清楚，有三个直接收益：

1. compiler 不会退化成普通文本模板器
2. validator 不会退化成只看 return code 的薄层
3. family 扩展时更容易判断哪些对象真正需要提升为 contract 字段

这也是为什么外部 ABACUS wiki 的“数据模型 / 输入输出”视角，对 engine wiki 是有价值的。

---

## 9.9 结论

ABACUS extension 的核心对象与 I/O 模型应被理解为：

- `INPUT` / `STRU` / `KPT` 是控制对象
- pseudo / orbital / `pot_file` / restart inputs 是运行资产对象
- `working_directory` 与 `OUT.<suffix>/` 是空间与输出对象
- family-specific artifacts 是成功判据对象
- validation / evidence / scored evidence 是治理 handoff 对象

只有把这些对象看成正式边界，ABACUS 扩展才能保持 file-driven scientific backend 的真实语义。
