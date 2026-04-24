# 05. family 设计

## 5.1 为什么 family 是一等设计对象

如果 `metaharness_ext.deepmd` 不把 `application_family` 当成一等对象，后续几乎所有能力都会退化：

- compiler 会变成条件分支堆积
- validator 会失去稳定 status taxonomy
- evidence / policy 会混淆 DeePMD 与 DP-GEN 的证据面
- study 会绕过 typed boundary
- 文档与测试会混淆 family、mode 与 baseline

因此 `application_family` 必须成为 contracts、compiler、environment、validator、study 与测试命名的共同主轴。

---

## 5.2 当前 family 集合

当前正式支持的 family 固定为四类：

- `deepmd_train`
- `dpgen_run`
- `dpgen_simplify`
- `dpgen_autotest`

它们不是整个 DeepModeling 生态的完整分类，而是 **MHE 对 DeepMD extension 在包与 contracts 层的当前正式支持边界**。

---

## 5.3 `deepmd_train` family

### 设计定位

`deepmd_train` 承载 DeePMD 单体训练链的 typed 入口。

### 当前需要承载的差异

同一 family 下已经包含多个 execution mode：

- `train`
- `freeze`
- `test`
- `compress`
- `model_devi`
- `neighbor_stat`

这些 mode 共享 `DeepMDTrainSpec`，但通过 `executable.execution_mode` 与 `mode_inputs` 区分运行语义。

### 设计提醒

- 不要把每个 DeePMD CLI 子命令都提升成新的 task family
- 不要把 `mode_inputs` 误写成任意参数透传层
- 不要让 executor 承担 descriptor / dataset compiler 职责

---

## 5.4 `dpgen_run` family

### 设计定位

`dpgen_run` 表达 concurrent learning 的主迭代路径。

### 结构重点

它的核心不是单次命令，而是：

- `param.json`
- `machine.json`
- workspace 准备
- `record.dpgen`
- `iter.*`
- candidate / accurate / failed 统计

### 设计意义

把 `dpgen_run` 当作独立 family，而不是 DeePMD train 的一个 mode，有助于：

- 保持 contracts 清晰
- 让 environment prerequisite 与 machine 语义自然落位
- 让 validator / evidence surface 更自然地表达 iteration evidence

---

## 5.5 `dpgen_simplify` family

### 设计定位

`dpgen_simplify` 是与 `dpgen_run` 并列的独立 family，用来承载 relabeling / transfer-learning 风格的迭代。

### 当前需要承载的差异

- `training_init_model`
- `trainable_mask`
- `relabeling`
- simplify-specific convergence clues

### 设计提醒

`simplify` 的成功态与“已经收敛”不是同一个概念：

- validator 可返回 `simplify_success`
- evidence 足够时才可能升级为 `converged`
- policy 仍可对不完整证据给出 `defer`

---

## 5.6 `dpgen_autotest` family

### 设计定位

`dpgen_autotest` 表达性质验证路径，而不是训练路径的附属步骤。

### 结构重点

它更关注：

- `properties`
- autotest workspace
- 结构化 property results
- property evidence completeness

### 设计意义

把 autotest 作为独立 family，而不是把它折叠到 `dpgen_run`，有助于：

- 保持 contracts 与 evidence surface 清晰
- 让 validator / policy 更自然地表达“性质证据是否完整”
- 避免把 property validation 混成迭代训练状态

---

## 5.7 family、mode 与 baseline 的关系

必须严格区分：

- **family**：扩展层支持的工作流族边界
- **mode**：某个 family 下的具体执行模式
- **baseline**：被选中的具体运行样例

例如：

- `deepmd_train` 是 family
- `compress` 是 `deepmd_train` family 下的 mode
- `dpgen_simplify` 是 family
- 某个带 `relabeling.pick_number` 的最小 demo 是 baseline

如果这几个概念混掉，compiler、validator、study 与测试语义都会失真。

---

## 5.8 family 与 study 的关系

study 的 boundary 也必须 family-aware：

- `numb_steps`、`rcut`、`rcut_smth`、`sel` 属于 `deepmd_train`
- `model_devi_f_trust_lo`、`model_devi_f_trust_hi` 属于 `dpgen_run`
- `relabeling.pick_number` 属于 `dpgen_simplify`

这也是为什么 `DeepMDStudySpec.base_task` 当前只接受：

- `DeepMDTrainSpec`
- `DPGenRunSpec`
- `DPGenSimplifySpec`

而不是一切 experiment family 都默认进入 study surface。

---

## 5.9 family 扩展规则

新增 family 之前，至少要回答：

- 顶层 contracts 是否已经独立到值得形成新 spec
- environment prerequisite 是否明显不同
- validator / evidence 是否需要新的语义分支
- study / baseline / tests 是否需要新的层次

只有这些问题有了明确答案，才值得把它提升为新的一级 family。
