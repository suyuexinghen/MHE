# 05. family 设计

## 5.1 为什么 family 是一等设计对象

如果 `metaharness_ext.abacus` 不把 `application_family` 当成一等对象，后续几乎所有能力都会退化：

- compiler 会变成条件分支堆积
- validator 会失去稳定证据判据
- 文档与测试会混淆 family、mode 与 baseline
- `md + dp` 会被误写成第二套扩展，而不是 ABACUS mode

因此 `application_family` 必须成为 contracts、compiler、validator 与测试命名的共同主轴。

---

## 5.2 当前 family 集合

当前在包与 contracts 层支持的 family 为：

- `scf`
- `nscf`
- `relax`
- `md`

它们不是整个 ABACUS 世界的完整分类，而是当前扩展的正式支持边界。

---

## 5.3 `scf` family

### 设计定位

`scf` 是最小稳定闭环的基础 family。

### 结构重点

- `INPUT`
- `STRU`
- 常见情况下的 `KPT`
- `OUT.<suffix>/`
- 最小 SCF 结果证据

### 设计意义

它是 ABACUS 扩展最自然的最小 baseline，因为最容易验证输入文件链、launcher 语义与输出目录证据面。

---

## 5.4 `nscf` family

### 设计定位

`nscf` 不是 `scf` 的一个小 flag，而是需要显式前提的独立 family。

### 当前关键约束

- 需要 `charge_density_path` 或 `restart_file_path`
- 需要更明确的前置 charge / restart 语义

### 设计意义

把这些前提写成 family-specific 规则，有助于避免把隐式目录依赖留给 executor 猜测。

---

## 5.5 `relax` family

### 设计定位

`relax` 是与 `scf` 并列的独立 family，而不是“多跑几步的 scf”。

### 结构重点

- final structure evidence
- relax-specific result interpretation

### 设计提醒

`relax` 的成功判定不应只看 `OUT.<suffix>/` 是否存在，还应关注最终结构产物是否出现。

---

## 5.6 `md` family

### 设计定位

`md` family 用来表达轨迹、restart 与 step-wise structure 证据面。

### 结构重点

- `MD_dump`
- `Restart_md.dat`
- `STRU_MD_*`

### 当前约束

- 当前代码不支持 `basis_type=lcao` 用于 `md`

因此 `md` 已经不仅是“另一种 calculation 值”，而是有独立 artifact / validation surface 的 family。

---

## 5.7 `md + dp` 是 mode，不是新 family

在当前设计里：

- `md` 是 family
- `esolver_type=dp` 是该 family 下的 mode 变体
- `pot_file` 是该 mode 的强制前提

这样可以避免把 ABACUS-native workflow 与 DeepMD-native workflow 混成两套并行体系。

---

## 5.8 family、mode 与 baseline 的关系

必须严格区分：

- **family**：扩展层支持的工作流族边界
- **mode**：某个 family 下的关键执行维度
- **baseline**：某个 family 下被选中的具体样例

例如：

- `md` 是 family
- `esolver_type=dp` 是 `md` 下的 mode 维度
- 某个 `md + dp + pot_file` demo 是 baseline

---

## 5.9 family 扩展规则

新增 family 前，至少要回答：

- 输入文件与 artifact 语义是否足够独立
- validator 是否需要新的最小成功判据
- 现有 family + mode 组合是否已经无法自然表达

只有这些问题有明确答案，才值得把它提升为新的一级 family。
