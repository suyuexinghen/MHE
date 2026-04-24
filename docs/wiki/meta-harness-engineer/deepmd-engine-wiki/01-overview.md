# 01. 概述与定位

## 1.1 DeepMD 解决什么问题

DeepModeling 生态的核心目标，是在量子力学精度与经典分子动力学效率之间建立可工程化的折中：

1. **DeePMD-kit**：从第一性原理或高保真标注数据训练 Deep Potential 模型
2. **DP-GEN**：通过 concurrent learning 扩充数据集并提高模型质量
3. **simplify / transfer learning / autotest**：复用已有模型、控制 relabeling 成本，并对性质结果做结构化验证

从工程视角看，DeepMD 不是一个单步训练器，而是一个跨越数据准备、训练、模型导出、偏差分析、迭代收集与性质验证的工作流族。

---

## 1.2 MHE 接哪一层

DeepModeling 生态可粗分为四层：

- **Level 1：物理与数据源层**
  - VASP / QE / ABACUS / Gaussian / AIMD / DFT 数据来源
- **Level 2：模型训练层**
  - descriptor、fitting net、loss、checkpoint、model export
- **Level 3：并发学习与自动化层**
  - `dpgen run` / `simplify` / `autotest`
- **Level 4：外部封装与工作流层**
  - `input.json` / `param.json` / `machine.json`、workspace、命令调用、结果收集

对 `metaharness_ext.deepmd` 来说，正确落点是：

- **以 Level 4 为主**：gateway、compiler、workspace、executor、validator、evidence、policy
- **以 Level 3 为辅**：包装 `dpgen_run`、`dpgen_simplify`、`dpgen_autotest` 的稳定控制面
- **对 Level 2 只做受控参数化**：通过 typed spec 改 descriptor / fitting / training，不直接接管训练内核
- **不进入 Level 1**：不把扩展做成任意 first-principles backend 适配平台

---

## 1.3 为什么 DeepMD 适合接入 MHE

### 1.3.1 控制面天然是声明式的

DeepMD 的稳定入口主要是 JSON：

- DeePMD-kit：`input.json`
- DP-GEN：`param.json`、`machine.json`

这意味着扩展层最适合走 **typed spec -> controlled JSON -> workspace -> executable** 的路线。

### 1.3.2 执行过程天然是 staged lifecycle

典型路径并不是单命令黑盒，而是：

```text
deepmd_train:
  train -> freeze -> compress -> test / model_devi / neighbor_stat

dpgen_run:
  00.train -> 01.model_devi -> 02.fp

dpgen_simplify:
  relabeling / transfer-learning oriented iteration

dpgen_autotest:
  make / run / post oriented property validation
```

这与 MHE 的 contract-first、evidence-first 扩展模式天然同构。

### 1.3.3 证据面足够丰富

当前扩展可围绕以下证据建立稳定 typed surface：

- `lcurve.out`
- checkpoint / frozen / compressed model
- `model_devi.out`
- `neighbor_stat.out`
- `record.dpgen` 与 `iter.*`
- autotest property summary
- stdout / stderr / working directory / command provenance

因此 DeepMD 很适合作为 evidence-bearing scientific extension 接入，而不是只做命令包装层。

---

## 1.4 关键现实约束

### 1.4.1 DeepMD 是多工具链组合，不是单一 binary

最常见失败往往不是模型本身，而是：

- `dp` / `dpgen` 不可用
- `python` 或指定 `machine.python_path` 不可用
- dataset / workspace 输入缺失
- `machine.local_root`、`machine.remote_root`、scheduler command 配置不完整
- autotest 或 FP 所需外部环境不齐

因此 environment probe 必须是正式组件，而不是 executor 内部的附带检查。

### 1.4.2 workspace-driven workflow 是正式边界

DeepMD / DP-GEN 的真实语义依赖目录布局和中间产物，而不只是返回码：

- 哪些配置文件被 materialize
- 哪些输入被复制或引用到 workspace
- `record.dpgen` 与 `iter.*` 是否存在
- 模型、checkpoint、diagnostics 是否被稳定识别

因此工作目录、产物布局和 evidence bundle 都属于正式 contract 边界。

### 1.4.3 科学通过与治理可晋升不是一回事

一次运行成功，只能说明 extension-local 路径跑通；它不自动等价于 promotion-ready。

DeepMD 扩展当前需要显式区分：

- 工程上是否运行完成
- 是否有最小科学证据
- evidence 是否完整到足以进入下游 review
- policy 是否给出 `allow` / `defer` / `reject`

---

## 1.5 正式支持边界

当前在包与 contracts 层正式支持的 application family 为：

- `deepmd_train`
- `dpgen_run`
- `dpgen_simplify`
- `dpgen_autotest`

当前正式支持的 execution mode 为：

- `train`
- `freeze`
- `test`
- `compress`
- `model_devi`
- `neighbor_stat`
- `dpgen_run`
- `dpgen_simplify`
- `dpgen_autotest`

当前明确不支持的方向：

- 任意 first-principles backend 自动适配平台
- 无约束 JSON 透传与自由 patch
- 把 DP-GEN 当成通用 shell workflow 平台
- extension 内自带完整 session / audit / provenance 子系统
- 直接把 runtime-level promotion authority 下沉到 DeepMD 扩展内

---

## 1.6 结论

`metaharness_ext.deepmd` 最合理的定位，不是把 DeepModeling 视为 Python SDK，而是把它视为一个：

- **JSON-configured**
- **workspace-driven**
- **artifact-rich**
- **environment-sensitive**
- **policy-bearing**

的训练与并发学习应用族。

因此扩展层的长期主轴应是：family-aware contracts、environment probe、controlled compiler、mode-aware executor、validator boundary、evidence / policy seam 与 typed study entry。
