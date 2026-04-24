# 08. 封装与注册

## 8.1 为什么 JEDI extension 需要明确的 packaging 约定

本文档定义 canonical packaging、manifest、capability 与 slot 约定；相关 importability 与 review 要求见 [09-测试与评审](09-testing-and-review.md)。

`metaharness_ext.jedi` 不是一组松散脚本，而是需要被 MHE runtime、manifest loader、测试和 reviewer 共同识别的正式扩展包。

因此，目录结构、exports、manifest 命名和 slot/capability 语义都应尽早固定。

---

## 8.2 推荐目录结构

首版推荐结构：

```text
MHE/src/metaharness_ext/jedi/
  |- __init__.py
  |- types.py
  |- contracts.py
  |- capabilities.py
  |- slots.py
  |- gateway.py
  |- environment.py
  |- config_compiler.py
  |- executor.py
  |- validator.py
  |- manifest.json
  |- environment.json
  |- compiler.json
  |- executor.json
  |- validator.json
```

这个结构的重点不是“模块数尽量多”，而是把正式组件边界写进包结构本身。

---

## 8.3 `__init__.py` 的职责

`__init__.py` 应只承担三类职责：

- 导出 public contracts / types
- 导出 canonical component classes
- 提供稳定的 `__all__`

不应承担：

- 运行时副作用
- 自动发现本地 JEDI workspace
- 隐式读取环境变量

---

## 8.4 capabilities 与 slots

### capabilities

`capabilities.py` 应回答的问题是：

- 这个 extension 对外宣称自己能做什么
- 哪些能力是 canonical capabilities
- 后续 gateway/agent 如何稳定引用这些能力

JEDI extension 的 capability 命名应围绕：

- environment probe
- config compile
- schema generation
- validate-only execution
- real run
- validation

### slots

`slots.py` 应回答的问题是：

- gateway 挂在哪个 slot
- environment/compiler/executor/validator 分别用什么稳定名字注册
- 哪些 slot 承担 protected / governance responsibility

slot 的价值在于：让 wiring、manifest 和 reviewer 讨论的是同一组固定名称，而不是隐式约定。

对 JEDI 而言，尤其要避免把 validator、smoke policy 或后续 policy-bearing 组件误写成“普通 helper slot”。其中 validator 所在 slot 应被理解为 governance slot：其产出会进入更高层 promotion / policy 路径，不能被 wiring 侧随意替换成弱语义实现。

---

## 8.5 manifest 设计

建议最少包含：

- `manifest.json`
- `environment.json`
- `compiler.json`
- `executor.json`
- `validator.json`

其中：

- `manifest.json` 负责整体 extension entry
- 其余 manifest 负责组件级 entry 与 class 对齐

manifest 的主要目标不是“方便动态魔法”，而是：

- 让 importability 可测
- 让组件边界可审计
- 让注册关系不依赖读者猜测

当前 strengthened MHE 语义下，manifest 还应承担明确的治理声明责任。JEDI 文档层至少应把以下字段语义写清：

- `kind`：区分 `core` 与 `governance` 组件；当前 validator manifest 已属于 `governance`
- `safety.protected`：标识 protected boundary；当前 validator 已是 protected component
- `policy.credentials`：描述凭证/主体边界的预留 policy surface
- `policy.sandbox`：描述 launcher / binary / sandbox 约束的 policy surface
- legacy `safety.sandbox_profile`：作为兼容字段保留，但不应再被误解为完整 policy 模型

---

## 8.6 importability 是正式验收点

一个新 extension 即使逻辑还未写满，只要 packaging 没稳，后续测试就会持续脆弱。

因此首版就应加入：

- manifest set completeness tests
- manifest entry importability tests
- top-level imports tests

这类测试的价值很高，因为它们最便宜地锁定了包结构回归。

---

## 8.7 与现有扩展的一致性

JEDI extension 应尽量对齐现有扩展模式，尤其是：

- `metaharness_ext.nektar`
- `metaharness_ext.ai4pde`

对齐的重点不是复制文件名本身，而是复用以下工程习惯：

- public exports 清晰
- manifest 与类名一一对齐
- tests 以 `test_metaharness_<extension>_<topic>.py` 命名
- capability / slot / component 边界一致可读

同时还应与 ABACUS / DeepMD / Nektar 等扩展共享一致的治理基线：manifest 不只是注册元数据，还要能表达 protected boundary、component kind、以及后续 policy/evidence integration 的宿主语义。

---

## 8.8 packaging 层最常见的退化

需要避免：

- 所有类都堆进单文件
- manifest 只写一个总入口，组件无单独 entry
- `__init__.py` 里做隐式环境探测
- 把 capability/slot 名称写死在测试或实现内部而不抽出常量

这些做法短期看省事，长期会直接拖慢 phase 演进和代码评审。