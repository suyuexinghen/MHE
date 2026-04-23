# 06. ABACUS 实现前补严清单

## 6.1 目的

本清单的目标，不是重复 `04-extension-blueprint.md` 与 `05-roadmap.md` 的设计结论，而是把其中仍偏“架构陈述”的部分压缩成更接近代码实现的规则。

它服务于三个直接目标：

- 在真正创建 `MHE/src/metaharness_ext/abacus/` 之前，先把边界离散化
- 在开始写 `contracts / input_compiler / executor / validator` 之前，先明确哪些规则必须机械化编码
- 避免实现时退化成“能跑就行”的 shell wrapper 或“return code + 目录存在”的假阳性 validator

---

## 6.2 总体原则

实现前应坚持以下四条规则：

1. **先缩边界，再写代码**
   - 首版只支持少量可验证组合
   - 对未明确建模的 family / mode / asset 组合直接拒绝

2. **先 probe 事实，再决定执行**
   - environment 组件只能报告“探测到的事实”
   - 不应把构建 feature、launcher 可用性、runtime path 完整性写成默认假设

3. **先编译受控输入，再执行**
   - compiler 只渲染受支持字段
   - 不提供任意 `INPUT` 文本 passthrough 作为首版默认能力

4. **先看证据，再给成功判定**
   - validator 不得只依赖 return code
   - validator 也不得只依赖 `OUT.<suffix>/` 是否存在

---

## 6.3 `environment probe` 必须补严的规则

### 6.3.1 不要把 probe 写成“理想 ABACUS 安装”假设

文档里提到的 `abacus --version`、`abacus --info`、`abacus --check-input` 是合理 probe 面，但实现时必须允许不同构建版本的支持度不一致。

因此环境报告不应只返回简单布尔值，而应把每类 probe 拆成独立事实，例如：

- `abacus_available`
- `abacus_path`
- `version_probe_supported`
- `version_probe_succeeded`
- `info_probe_supported`
- `info_probe_succeeded`
- `check_input_probe_supported`
- `check_input_probe_succeeded`
- `requested_launcher`
- `launcher_available`
- `deeppmd_support_detected`
- `gpu_support_detected`
- `required_paths_present`
- `messages`

关键约束：

- **unsupported** 与 **failed** 必须区分
- 缺少某个 probe 子命令，不自动等于环境非法
- 但若某个 family/mode 明确依赖某探针能力，则缺失应升级为 environment prerequisite failure

### 6.3.2 launcher 检查必须和 `abacus` binary 检查分离

实现时必须把以下失败分开：

- `abacus` 本体缺失
- 请求了 `mpirun/mpiexec/srun` 但 launcher 缺失
- launcher 存在但参数组合不被首版支持

不要把三者折叠成一个“环境不可用”。

### 6.3.3 required paths 必须按 family/mode 检查，而不是全局平铺

`required_paths_present` 不能只做“所有路径都存在”的粗检查，而要按组合判断：

- `scf / nscf / relax / md` 对 `STRU`、`KPT`、伪势、轨道、模型文件的要求不同
- `basis_type=pw` 与 `basis_type=lcao` 的资产要求不同
- `md + esolver_type=dp` 与普通 `md` 的依赖闭包不同

因此环境层至少要支持：

- 基于 family 的 required path 计算
- 基于 basis_type 的 asset requirement 计算
- 基于 `esolver_type=dp` 的 model-file requirement 计算

### 6.3.4 probe 结果要保留“不确定”状态

对于 DeePMD support、GPU support 这类构建期 feature：

- 首版不要假定一定能可靠探测
- 若无法稳定从 `--info` 提取，应保留 `unknown`
- `md + dp` 模式只有在 `supported=true` 时才允许执行；`unknown` 应按保守策略处理为前提不足，而不是默认放行

---

## 6.4 `contracts` 必须补严的规则

### 6.4.1 首版 contracts 必须表达“允许的离散组合”

不要只定义大而全的数据模型；必须同时定义允许组合的规则。

最低限度要把这些维度离散化：

- `application_family`: `scf | nscf | relax | md`
- `basis_type`: `pw | lcao`
- `launcher`: `direct | mpirun | mpiexec | srun`
- `esolver_type`: `ksdft | dp`

并把“哪些组合在首版合法”编码成校验逻辑，而不是留给 compiler 内部默默兜底。

### 6.4.2 family-specific spec 必须比通用 run spec 更强

建议实现时不要只依赖一个 `AbacusRunSpec`。至少需要：

- `AbacusScfSpec`
- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- `AbacusMdSpec`

原因：

- 不同 family 的成功证据不同
- 不同 family 的输入前提不同
- 不同 family 的 artifact 发现逻辑不同

如果 family-specific 规则都堆到 compiler/validator 中，后续会很快退化成大量条件分支。

### 6.4.3 资产要求要变成显式字段，不要留在说明文字里

实现前应明确哪些资产需要独立 schema 表达，例如：

- `structure`
- `kpoints`
- `pseudo_files`
- `orbital_files`
- `pot_file`
- `working_directory`
- `suffix`

首版允许资产字段不覆盖全部 ABACUS 世界，但**已经决定支持的字段必须进入 typed boundary**。

### 6.4.4 对不支持的组合要显式报错，不要自动降级

例如：

- 未建模的 `basis_type`
- 未建模的 `esolver_type`
- 需要额外资产但未声明的组合
- 首版未承诺的 family-specific 高阶参数

这些都应返回 `input_invalid` 或 `unsupported_combination` 风格错误，而不是：

- 静默忽略字段
- 自动回退到默认参数
- 继续执行然后把问题推迟到 runtime

---

## 6.5 `input compiler` 必须补严的规则

### 6.5.1 compiler 只渲染“已支持字段”

编译器的职责不是转储任意配置，而是把受控 spec 渲染成稳定的 `INPUT / STRU / KPT`。

因此必须满足：

- 固定字段顺序或稳定排序
- 只渲染首版明确支持的 key
- 不把未知字段无声透传进 `INPUT`
- 同一 spec 重复编译得到字节级稳定输出

### 6.5.2 compiler 必须区分三类失败

实现时要分清：

1. **schema/contract failure**
   - typed spec 自身不合法
2. **unsupported combination**
   - spec 合法，但组合超出首版边界
3. **rendering/preparation failure**
   - 需要的资产缺失、路径无效、输出目录不可准备

不要把它们统一压成“输入错误”。

### 6.5.3 `suffix` 规则必须稳定且可审计

`OUT.<suffix>/` 是首版 evidence surface 的中心，因此 `suffix` 规则必须明确：

- 允许用户显式给定，或由系统稳定生成
- 不允许包含破坏目录语义的字符
- 必须能从 `run_id/task_id` 追溯
- 在 artifact 收集阶段不能再依赖模糊猜测

### 6.5.4 family-specific compiler 约束必须机械化

以下规则不能只停留在文档里，必须变成可执行检查：

- `basis_type=lcao` 时，哪些 asset 是强制项
- `basis_type=pw` 时，哪些 asset 不应再被要求
- `md + esolver_type=dp` 时，`pot_file` 是强制项
- 文档已声明可省略的文件，在该 mode 下不得再被错误要求
- `nscf` 若依赖前置 charge / read-file 语义，必须有明确字段与前提检查，而不是靠自由文本约定

建议做法：

- 先定义首版最小合法组合表
- 再让 compiler 仅支持表中组合
- 对表外情况直接拒绝

### 6.5.5 workspace 准备语义必须先定清楚

实现前必须决定：

- 输入文件是 copy、symlink 还是 render 到新目录
- 外部资产是否允许引用原路径
- 相对路径是否在编译阶段归一化
- `OUT.<suffix>/` 的父目录是谁负责准备

这些规则若不先定，后续 executor 和 validator 都会变得不稳定。

---

## 6.6 `executor` 必须补严的规则

### 6.6.1 command 构造必须是结构化的

不要让 executor 接收任意 shell command。首版应只接受结构化 command parts：

- launcher 段
- launcher args 段
- `abacus` binary 段
- 工作目录段
- timeout / process_count 等运行控制字段

### 6.6.2 direct 与 launcher 模式要共享统一 artifact 语义

不能因为执行路径不同，就让后续 artifact 搜集逻辑分裂成两套结果模型。

无论 `direct`、`mpirun`、`mpiexec` 还是 `srun`，最终都应归一到统一的：

- `command`
- `stdout_path`
- `stderr_path`
- `working_directory`
- `output_root`
- `prepared_inputs`
- `discovered_artifacts`

### 6.6.3 `OUT.<suffix>/` 发现逻辑必须可解释

实现时不要写成“搜到一个像输出目录的目录就算”。至少应保证：

- 发现逻辑与 compiler 的 `suffix` 规则一致
- 优先使用预期输出目录
- fallback 扫描仅作为诊断，不作为主要成功判据

---

## 6.7 `validator` 必须补严的规则

### 6.7.1 首版严禁使用弱成功条件

以下判据单独使用都不够：

- return code == 0
- `stdout.log` 存在
- `OUT.<suffix>/` 存在
- 某个目录非空

validator 必须采用 **多证据联合判定**。

### 6.7.2 family-specific success rule 必须最小但不可空泛

建议首版至少把成功条件编码成如下形态：

- `scf`
  - 预期 `OUT.<suffix>/` 存在
  - 有有效输入快照或关键日志证据
  - 有能表明进入并完成 SCF 主流程的证据
- `nscf`
  - 满足 `scf` 的基础输出要求
  - 额外满足 `nscf` family 的输入前提或特定输出证据
- `relax`
  - 除基础输出外，必须存在 final structure evidence
- `md`
  - 除基础输出外，必须存在 `MD_dump`、`Restart_md.dat`、`STRU_MD_*` 等至少一类 MD 特征证据
- `md + dp`
  - 满足 `md` 证据要求
  - 同时满足 `pot_file` / DeePMD support 等 mode prerequisite

关键点：

- 每个 family 都要有“基础证据 + family 专属证据”两层结构
- 不能为了统一实现而退化成最弱共同分母

### 6.7.3 validator 必须区分“没跑起来”和“跑了但证据不够”

至少要保留：

- `environment_invalid`
- `input_invalid`
- `runtime_failed`
- `validation_failed`
- `executed`

其中：

- return code 非零、timeout、launcher 崩溃，应落到 `runtime_failed`
- return code 为零但 family 证据不充分，应落到 `validation_failed`
- 缺 DeePMD support 却请求 `md + dp`，应优先视作前提不足，而不是 runtime failure

### 6.7.4 validator 输出必须便于审计

`ValidationReport` 至少应携带：

- `status`
- `passed`
- `messages`
- `summary_metrics`
- `evidence_files`
- `missing_evidence`

这样后续测试与人工审阅才能知道“为什么没通过”，而不是只看到 `passed=false`。

---

## 6.8 首版最值得先离散化的 family/mode 规则

如果现在就开始编码，建议先把以下规则写成最小合法组合表。

### 6.8.1 Phase 0 建议只支持的组合

- `scf + basis_type=pw + esolver_type=ksdft + launcher=direct`
- `scf + basis_type=pw + esolver_type=ksdft + launcher in {mpirun, mpiexec, srun}`

在这个阶段：

- 先把 `INPUT / STRU / KPT` 渲染、workspace 准备、输出目录发现、validator taxonomy 打稳
- 暂不追求 `lcao`、`md`、`dp` 的完整闭环

### 6.8.2 只有当规则被写成表，才适合继续扩张

推荐在实现中显式维护类似语义：

```text
supported_combinations = {
  ("scf", "pw", "ksdft"),
  ("nscf", "pw", "ksdft"),
  ("relax", "pw", "ksdft"),
  ("md", "pw", "ksdft"),
  ("md", "pw", "dp"),
}
```

真实代码结构不必长这样，但必须有同等约束强度。

---

## 6.9 测试先行清单

在开始写真实实现前，建议先把下面这些测试目标写出来。

### 6.9.1 environment tests

- 缺 `abacus` binary
- 请求 launcher 但 launcher 缺失
- `--version` 支持但 `--info` 不支持
- `md + dp` 请求时 DeePMD support 为 `false`
- `md + dp` 请求时 DeePMD support 为 `unknown`

### 6.9.2 compiler tests

- 相同 spec 重复编译输出稳定
- `suffix` 非法字符被拒绝
- `basis_type=lcao` 缺少必需资产被拒绝
- `md + dp` 缺 `pot_file` 被拒绝
- 未支持的 family/basis/mode 组合被拒绝

### 6.9.3 executor tests

- `direct` 模式命令构造正确
- launcher 模式命令构造正确
- workspace 输入落盘位置稳定
- 预期 `OUT.<suffix>/` 发现逻辑正确

### 6.9.4 validator tests

- return code 为零但无关键 evidence -> `validation_failed`
- output root 存在但 family-specific evidence 缺失 -> `validation_failed`
- `relax` 缺 final structure -> 失败
- `md` 缺 MD 特征产物 -> 失败
- `md + dp` 缺 prerequisite -> 不应误报 `executed`

---

## 6.10 可以直接作为实现 gate 的完成标准

在真正创建 `MHE/src/metaharness_ext/abacus/` 前，建议把以下问题都回答清楚：

- 首版到底支持哪些 family/basis/mode 组合
- 每个组合各自需要哪些资产
- 哪些 probe 是 required，哪些 probe 只是 best-effort
- `suffix` 如何稳定生成与验证
- workspace 是如何准备与归档的
- 每个 family 的最小成功证据到底是什么
- 哪些失败属于 environment，哪些属于 input，哪些属于 runtime，哪些属于 validation

如果这些问题仍然只能用自然语言解释，而不能被翻译成 schema、表格或测试断言，就说明实现前的 rigor 还不够。

---

## 6.11 与当前文档的关系

本清单不是替代现有文档，而是把现有文档向“可编码规则”再推进一步：

- [03-Contracts 与产物](03-contracts-and-artifacts.md) 给出模型轮廓
- [04-扩展蓝图](04-extension-blueprint.md) 给出架构边界
- [05-路线图](05-roadmap.md) 给出 phase 顺序
- 本文档则补足“在写代码前必须先机械化的约束项”

如果后续要进入真实实现，建议先把本清单中的组合表、failure taxonomy 和 success evidence 细化成测试，再开始写 `contracts.py`、`environment.py`、`input_compiler.py` 与 `validator.py`。
