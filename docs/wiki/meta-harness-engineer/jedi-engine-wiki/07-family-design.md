# 07. Family 设计

## 7.1 为什么 family 是一等设计对象

本文档中的概念层术语统一使用 **application family**；代码字段继续使用 `application_family`。phase mapping 以 [06-实施路径](06-implementation-phases.md) 为准，contract 形状以 [03-contracts 设计](03-contracts.md) 为准。

`metaharness_ext.jedi` 的首版如果不把 `application_family` 当成一等对象，后续几乎所有能力都会退化：

- compiler 会变成条件分支堆积
- validator 会失去稳定 failure taxonomy
- study/mutation 会绕过 typed boundary
- 文档与测试会不断混淆“family”与“具体 YAML 样例”

因此，`application_family` 必须成为 gateway、contracts、compiler、executor 和测试命名的共同主轴。

---

## 7.2 首版 family 划分

首版推荐固定为四类：

- `variational`
- `local_ensemble_da`
- `hofx`
- `forecast`

它们不是“JEDI 全宇宙应用的完整分类”，而是 **MHE 首版正式支持边界**。

---

## 7.3 `variational` family

### 设计定位

`variational` 是首个正式 scientific baseline 的核心 family，也是最容易暴露 compiler/validator 边界是否合理的 family。

### 首版需要承载的差异

- `cost_type` 差异：`3D-Var` / `4D-Var` / `4DEnsVar` / `4D-Weak`
- `window begin` / `window length`
- `background` / `background error`
- `observations`
- `variational`
- `output` / `final` / `test`

### 需要刻意避免的错误

- 把 `3DFGAT` 当成独立 `cost_type`
- 把 `variational` family 和某个单一 toy YAML 样例绑定死
- 把 minimizer 细节下沉到 executor

---

## 7.4 `local_ensemble_da` family

### 设计定位

这是第二类正式 family，不应被视作“variational 的可选模式”。

### 首版需要承载的差异

- `driver`
- `local ensemble DA`
- `window begin` / `window length`
- `geometry` / `background` / `observations`
- ensemble-specific output evidence

### 设计提醒

当 `local_ensemble_da` 进入同一 extension 时，contracts 的优劣会立刻暴露：如果当前 contract 过于 variational-centric，这个 family 会变得异常别扭。

---

## 7.5 `hofx` family

### 设计定位

`hofx` 不只是辅助功能，而是最适合作为 smoke baseline 的 family。

### 作为首个 smoke baseline 的原因

- 比完整 variational / ensemble DA 更轻
- 能更快暴露 observations/input/diagnostics 路径问题
- 仍然覆盖 YAML -> executable -> outputs/diagnostics 主链

### 依赖前提

`hofx` 作为首个 smoke baseline 的成立前提，不是“它逻辑上更轻”这一点本身，而是 **observation stack 与对应 test data 在当前环境中确实可用**。如果这些前提未被 environment probe 证实，则 `hofx` 只能是优先候选，而不能是硬编码的 Phase 1 必经路径。

### 工程意义

因此更准确的表达是：`hofx` 应被设计为 **首选 smoke baseline candidate**，并由 environment probe + data readiness 决定是否成为当前环境下的首批真实运行路径。

---

## 7.6 `forecast` family

### 设计定位

`forecast` 在首版中优先级低于 `hofx` / `variational` / `local_ensemble_da`，但仍值得先纳入 contract 边界。

### 原因

- 它提供另一类非 observation-centric 的应用面
- 提前纳入 family 列表，可以避免未来再破坏 discriminated union
- 它是扩展完整性的一部分，即使不作为首批 baseline

---

## 7.7 family 与 baseline 的关系

必须区分：

- **family**：扩展层支持的应用族边界
- **baseline**：当前 phase 选择来跑通或验证的具体样例路径

例如：

- `hofx` 是 family
- `qgHofX4D.x` smoke 是 baseline
- `variational` 是 family
- `qg4DVar.x + 4dvar_rpcg.yaml` 是 baseline

如果这两个概念混掉，roadmap、tests 和 validator 语义都会失真。

---

## 7.8 family 扩展规则

新增 family 之前，至少回答以下问题：

- 顶层 YAML 结构是否独立到足以形成新 family
- execution mode 是否有新差异
- diagnostics / evidence 是否需要新 validator 逻辑
- 是否需要新 baseline 与新测试层次

只有在这些问题答案明确时，才值得把它提升为新的一等 family。