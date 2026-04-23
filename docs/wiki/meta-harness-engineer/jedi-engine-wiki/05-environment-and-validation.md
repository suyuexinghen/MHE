# 05. 环境与验证

## 5.1 为什么 environment probe 是正式组件

本文档定义 canonical failure taxonomy、validation report 语义与 `evidence_files` 口径；run artifact contract 本身以 [03-contracts 设计](03-contracts.md) 为准。

JEDI workflow 的早期失败，很多并不是 YAML 逻辑错误，而是环境前提没有满足：

- binary 不存在
- launcher 不可用
- shared library 解析失败
- testinput / data path 缺失
- Git LFS 或 `ctest -R get_` 一类数据准备未完成

如果没有独立的 environment probe，这些问题就会在 validate-only 或 real-run 阶段表现成模糊 stderr，导致 failure taxonomy 失真。

---

## 5.2 Phase 0 的环境检查项

首版至少检查：

- binary 是否在 PATH 中
- launcher 是否可调用（`direct` / `mpiexec` / `mpirun` / `srun`）
- `ldd` 是否显示 unresolved libraries
- 必需 YAML / testinput / data path 是否存在
- 数据准备前提是否可能缺失

这里的目标不是自动修复，而是返回稳定、可审计的 `JediEnvironmentReport`。

需要特别强调的是：`required paths` 不是统一的一组静态路径，而是 **family-aware 的引用面**。例如：

- `variational` 往往需要 background、background error、observations 等块引用的外部文件
- `hofx` 往往需要 observation-side 输入与相关配置路径
- `forecast` 更可能依赖 initial condition、model 与输出路径

因此 environment probe 不应只检查“某个目录是否存在”，而应与 compiler / contracts 对齐，按当前 `application_family` 解析并核对该 family 真正依赖的路径集合。关于 family 边界，见 [07-family 设计](07-family-design.md)。

---

## 5.3 failure taxonomy

当前 validator 至少应输出以下状态：

- `environment_invalid`
- `validated`
- `executed`
- `validation_failed`
- `runtime_failed`

这四类状态的价值在于：

- `environment_invalid` 表示 extension 不应继续把错误归给配置
- `validated` 表示 schema / validate-only 路径已经通过各自的基础判定
- `executed` 表示 real run 已完成且存在最小 runtime evidence
- `validation_failed` 表示配置或引用关系未通过 executable 校验，或 runtime evidence 未达到当前最小判定面
- `runtime_failed` 表示 runtime 调用失败、超时或缺少必要退出信息

这组 taxonomy 对当前 Phase 0 是足够且刻意收敛的；进入 Phase 1+ 后，通常还需要扩展为更细的 runtime/result interpretation，例如：

- run 完成但需要 richer diagnostics interpretation
- run 完成但 scientific evidence 不满足更高层判据
- MPI 部分失败或仅产生部分 artifact

也就是说，当前 Phase 0 的五状态模型是 **当前 canonical taxonomy**，不是永久终态。

---

## 5.4 evidence-first report

一个可用的 `JediValidationReport` 至少应包含：

- `messages`
- `summary_metrics`
- `evidence_files`

`evidence_files` 至少能指向：

- `config.yaml`
- `stdout.log`
- `stderr.log`
- `schema.json`（当存在时）
- `prepared_inputs`
- `output_files`
- `diagnostic_files`

这样做的原因是：agent、CLI、reviewer 都不应该被迫重新猜测“刚才到底跑了什么”。

---

## 5.5 diagnostics 在首版中的位置

Phase 0 不要求复杂 diagnostics interpretation，但这不意味着要把当前输出假设成“纯文本日志”。

更稳妥的做法是：

- 当前已把 diagnostics 纳入 artifact / evidence surface
- 在 contract / artifact layout 中保留 diagnostics files 的稳定位置
- 文档中明确后续目标是 IODA/HDF5/ODB 组级证据提取，而不是单一 NetCDF 日志假设

---

## 5.6 数据准备策略

对于 testinput / observations / reference data 缺失，首版 wiki 采用明确而保守的策略：

- Phase 0：environment probe 只负责 **报告缺失**，并将其归入 `environment_invalid`
- Phase 0：extension 不自动触发 `ctest -R get_`、`qg_get_data`、`l95_get_data` 或等价数据准备步骤
- 当前 Phase 0：preprocessor 只负责 materialize config、验证 `required_runtime_paths`、记录 `prepared_inputs`
- Phase 1+：如确有需要，再把数据准备扩展为更完整的 data-preparation step，而不是隐藏在 executor 内部

这样做的原因是：

- 数据准备是环境前提，不是 validate-only 的副作用
- 自动触发下载/准备会模糊失败边界，也增加不可审计副作用
- reviewer 与 agent 更容易理解“当前失败是环境未就位”，而不是把问题误判成 YAML 逻辑错误

## 5.7 测试重点

围绕环境与验证的单测，优先覆盖：

- binary 缺失
- launcher 缺失
- unresolved libraries
- required path 缺失
- validate-only 命令构造
- schema 命令构造
- real-run 命令构造与 evidence 映射
- environment failure 与 validation failure 的语义分离
- `executed` 与 scientific success 的语义分离

如果这些点不稳，后面再补 smoke policy 与 richer diagnostics interpretation 只会放大不确定性。