# 06. 实施路径

## 6.1 三份正式文档如何分工

`metaharness_ext.jedi` 当前已经有三份正式设计文档：

- `blueprint/01-jedi-extension-blueprint.md`
- `blueprint/01-jedi-extension-roadmap.md`
- `blueprint/01-jedi-extension-implementation-plan.md`

它们的职责分别是：

- **blueprint**：定义正式设计立场、组件链和边界
- **roadmap**：定义 Phase 0 → Phase 6 的推进顺序和里程碑
- **implementation plan**：把当前要做的 phase 拆成可直接执行的文件、步骤、测试与验收标准

本 wiki 的作用，是把这些正式文档转成更利于实现与维护的工程说明。

---

## 6.2 当前推荐推进顺序

本文档中的 baseline 术语统一采用：**smoke baseline** 表示优先验证执行链的轻量 baseline，**scientific baseline** 表示带最小科学证据的正式 baseline，**toy baseline** 表示刻意缩小规模的 baseline。family 边界以 [07-family 设计](07-family-design.md) 为准，测试策略以 [09-测试与评审](09-testing-and-review.md) 为准。

### Phase 0

目标：

- environment probe
- family-aware contracts
- controlled YAML compiler
- schema / validate-only executor
- validation report

验收重点：

- 稳定区分 environment failure 与 validation failure
- 能生成稳定 YAML
- 能构造正确 executable 命令

### Phase 1

目标：

- preprocessor
- real run
- toy smoke baseline
- 最小 diagnostics 线索

验收重点：

- 至少一个 toy executable 能稳定跑通
- artifact 布局稳定
- validator 可区分 runtime success / failure

需要额外强调的是：Phase 1 的 smoke baseline 不能预先硬编码为“必然是 `hofx`”。更稳妥的设计约束应是：

- 若 observation stack（如 IODA/UFO 相关 runtime 前提）与 test data 已就位，则优先选择 `hofx` 作为首个 smoke baseline
- 若 observation stack 的可用性尚未被当前环境确认，则应由 environment probe 先给出结论，再决定是进入 `hofx` smoke，还是切换到更少依赖 observation stack 的候选 baseline
- 若缺少可用的 real-run baseline，则应明确把 Phase 1 判定为环境阻塞，而不是强行假定 smoke 一定能跑通

这条约束的目的是把 smoke baseline 选择从“文档假设”收敛为“环境先验 + phase gate”。

### Phase 2+

后续再进入：

- real variational baseline
- local ensemble DA baseline
- diagnostics strengthening
- study / mutation layer
- environment / HPC hardening

---

## 6.3 为什么先做 Phase 0

Phase 0 的收益最高，因为它最早把以下边界固定下来：

- 输入 contract 边界
- environment failure 边界
- executable invocation 边界
- report / evidence 边界

这些边界一旦稳定，后续 phase 只是在同一骨架上增加 preprocessor、diagnostics、study，而不是反复重写基础接口。

---

## 6.4 实现时的代码组织建议

建议直接对齐现有扩展模式，先建立：

- `__init__.py`
- `types.py`
- `contracts.py`
- `capabilities.py`
- `slots.py`
- `gateway.py`
- `environment.py`
- `config_compiler.py`
- `executor.py`
- `validator.py`
- 对应 manifest JSON
- 对应测试文件

这套骨架的目标不是“把所有逻辑写满”，而是先建立后续可复用的扩展边界。

---

## 6.5 reviewer 关注点

在评审 `metaharness_ext.jedi` 代码时，优先看以下问题：

- contract 是否真的 family-aware
- compiler 是否退化成 YAML passthrough
- executor 是否错误理解了 family-specific YAML
- validator 是否稳定区分 environment / validation / runtime
- 测试是否覆盖 executable name 与 CTest name 的分离
- 文档是否仍然坚持“设计 MHE extension”，而不是回到软件综述

---

## 6.6 本 wiki 的维护策略

随着实现推进，本目录应优先更新：

- 组件边界
- contract 设计
- failure taxonomy
- phase mapping
- reviewer checklist

而不是重新长篇补写 JEDI 软件背景。这个取舍能让 wiki 始终服务于 `metaharness_ext.jedi` 的工程落地。