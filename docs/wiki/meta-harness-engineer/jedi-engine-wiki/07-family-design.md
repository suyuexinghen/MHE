# 07. Family 设计

## 7.1 为什么 family 是一等设计对象

如果 `metaharness_ext.jedi` 不把 `application_family` 当成一等对象，后续几乎所有能力都会退化：

- compiler 会变成条件分支堆积
- validator 会失去稳定 failure taxonomy
- study / mutation 会绕过 typed boundary
- 文档与测试会不断混淆 family 与具体 baseline

因此，`application_family` 必须成为 gateway、contracts、compiler、executor 与测试命名的共同主轴。

---

## 7.2 首版 family 划分

首版推荐固定为四类：

- `variational`
- `local_ensemble_da`
- `hofx`
- `forecast`

它们不是 JEDI 全部应用的完整分类，而是 **MHE 对 JEDI extension 的首版正式支持边界**。

---

## 7.3 `variational` family

### 设计定位

`variational` 是一个独立 family，用来承载 3D-Var / 4D-Var / 4DEnsVar / 4D-Weak 这一组具有共同结构的应用。

### 首版需要承载的差异

- `cost_type`：`3D-Var` / `4D-Var` / `4DEnsVar` / `4D-Weak`
- `window begin` / `window length`
- `background` / `background error`
- `observations`
- `variational`
- `output` / `final` / `test`

### 需要刻意避免的错误

- 把 `3DFGAT` 当成独立 `cost_type`
- 把 `variational` family 与某个 toy YAML 样例绑定死
- 把 minimizer 细节下沉到 executor

---

## 7.4 `local_ensemble_da` family

### 设计定位

`local_ensemble_da` 是与 `variational` 并列的独立 family，而不是后者的可选模式。

### 首版需要承载的差异

- `driver`
- `local ensemble DA`
- `window begin` / `window length`
- `geometry` / `background` / `observations`
- ensemble-specific output evidence

### 设计提醒

如果 contracts 过于 variational-centric，这个 family 会立即暴露设计问题。因此 family 划分不仅是命名问题，也是 contract 形状与 compiler 结构的约束条件。

---

## 7.5 `hofx` family

### 设计定位

`hofx` 是一个独立 family，用于表达 observation-oriented 的运行路径。

### 结构特征

相较于 `variational` 与 `local_ensemble_da`，`hofx` 的结构重点更集中在：

- geometry / state
- time window
- observations
- model（若 workflow 需要）
- observation-side outputs / diagnostics

### 设计意义

把 `hofx` 作为独立 family，而不是把它折叠进其他 family，有助于：

- 保持 contracts 的边界清晰
- 让 compiler 明确生成不同顶层块
- 让 validator 与 diagnostics surface 更自然地表达 observation-side evidence

是否把某个 `hofx` 样例选为 smoke baseline，属于 roadmap / implementation plan 的问题，而不是 family 定义本身。

---

## 7.6 `forecast` family

### 设计定位

`forecast` 在首版中优先级较低，但仍值得先纳入 contract 边界。

### 原因

- 它代表另一类非 observation-centric 应用面
- 提前纳入 family 集合，可以避免未来破坏 discriminated union
- 它有助于保持扩展模型的完整性，即使不是首批 baseline

---

## 7.7 family 与 baseline 的关系

必须严格区分：

- **family**：扩展层支持的应用族边界
- **baseline**：某个 family 下被选中的具体运行样例

例如：

- `hofx` 是 family
- `qgHofX4D.x` 是某个可能的 baseline
- `variational` 是 family
- `qg4DVar.x + 4dvar_rpcg.yaml` 是某个可能的 baseline

如果这两个概念混掉，contracts、roadmap、tests 与 validator 语义都会失真。

---

## 7.8 family 扩展规则

新增 family 之前，至少要回答以下问题：

- 顶层 YAML 结构是否独立到足以形成新 family
- execution mode 是否有新的语义差异
- diagnostics / evidence 是否需要新的 validator 逻辑
- 是否需要新的 baseline 与测试层次

只有这些问题有了明确答案，才值得把它提升为新的一级 family。