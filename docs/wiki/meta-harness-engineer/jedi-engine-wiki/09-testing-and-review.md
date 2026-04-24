# 09. 测试与评审

## 9.1 测试目标

JEDI extension 的测试不只是证明“代码能 import”，还要证明以下设计边界稳定：

- package / manifest 结构稳定
- contracts 的 family 边界稳定
- environment failure 与 validation failure 区分稳定
- command construction 稳定
- executable name 与 CTest test name 不混淆

如果这些边界先被测稳，后续扩展 smoke、diagnostics 或 study 能力时，整体架构会更可控。

---

## 9.2 推荐测试层次

### 第一层：packaging / import

优先覆盖：

- manifest set 是否完整
- manifest entries 是否可导入
- `metaharness_ext.jedi` public API 是否可导入

### 第二层：contracts / compiler

优先覆盖：

- discriminated union 是否按 `application_family` 工作
- `variational.cost_type` 是否限制正确
- YAML 输出是否稳定
- compiler 是否拒绝退化成任意 YAML passthrough

### 第三层：environment / executor / validator

优先覆盖：

- binary 缺失
- launcher 缺失
- unresolved libraries
- required path 缺失
- schema / validate-only / real-run 的命令构造是否稳定
- validation report 状态映射是否稳定

### 第四层：execution demo / e2e

这一级测试的目标，是验证设计边界在真实执行链上仍然成立，而不是把所有实现细节都堆进单个大而全 e2e。

---

## 9.3 reviewer checklist

评审 `metaharness_ext.jedi` 时，优先检查：

- 是否仍然坚持 MHE extension 视角，而不是软件综述视角
- contracts 是否清晰区分 family
- compiler 是否只从 typed spec 生成受控 YAML
- environment probe 是否发生在 compiler / executor 之前
- executor 是否只知道 execution mode，而不理解业务 YAML 结构
- validator 是否只负责判定，而不承担运行或编译职责
- tests 是否真正覆盖 failure taxonomy，而不是只测 happy path
- 文档是否仍然保持设计导向，而不是混入实施计划

---

## 9.4 最值得早期卡住的 review 问题

如果在评审中看到以下迹象，应尽早要求返工：

- `contracts.py` 开始堆大量 `dict[str, object]` 弱类型逃逸
- `config_compiler.py` 接受任意外部 YAML 透传
- `executor.py` 中出现 family-specific YAML 结构逻辑
- `validator.py` 中偷偷补环境探测
- 测试把 CTest test name 当 executable name 使用

这些问题越早纠正，代价越低。

---

## 9.5 测试与文档必须共同守边界

JEDI extension 的稳定性不仅来自代码，也来自文档是否持续表达正确边界。

因此评审时也应检查：

- 术语是否统一（family、baseline、execution mode、evidence）
- 技术事实是否与当前修正后的 JEDI wiki / blueprint 一致
- 文档是否持续强调 executable name 与 CTest test name 的区别
- 文档是否没有重新膨胀回 JEDI 软件百科

只有代码与文档同时守住边界，`metaharness_ext.jedi` 才会稳定。