# 09. 测试与评审

## 9.1 测试目标

本文档中的测试与 review 规则默认建立在 [03-contracts 设计](03-contracts.md)、[04-执行链设计](04-execution-pipeline.md)、[05-环境与验证](05-environment-and-validation.md)、[08-封装与注册](08-packaging-and-registration.md) 已定义的 canonical 边界之上。

JEDI extension 的测试不只是证明“代码能 import”，还要证明以下边界稳定：

- package / manifest 结构稳定
- contracts 的 family 边界稳定
- environment failure 与 validation failure 区分稳定
- command construction 稳定
- executable name 与 CTest test name 不混淆

首版如果先把这些点测稳，后续再进入 real-run 与 diagnostics 时会轻松很多。

---

## 9.2 推荐测试层次

### 第一层：packaging / import tests

优先覆盖：

- manifest set 是否完整
- manifest entries 是否可导入
- `metaharness_ext.jedi` public API 是否可导入

### 第二层：contracts / compiler tests

优先覆盖：

- discriminated union 是否按 `application_family` 工作
- `variational.cost_type` 是否限制正确
- YAML 输出是否稳定
- compiler 是否拒绝退化成任意 YAML passthrough

### 第三层：environment / executor / validator tests

优先覆盖：

- binary 缺失
- launcher 缺失
- unresolved libraries
- required path 缺失
- schema 命令构造
- validate-only 命令构造
- validation report 状态映射

### 第四层：smoke / e2e tests

Phase 1 之后再覆盖：

- `hofx` smoke baseline
- toy variational baseline
- toy local ensemble DA baseline

---

## 9.3 首版测试文件建议

Phase 0 至少包括：

- `test_metaharness_jedi_manifest.py`
- `test_metaharness_jedi_imports.py`
- `test_metaharness_jedi_environment.py`
- `test_metaharness_jedi_compiler.py`
- `test_metaharness_jedi_validate_only.py`

这组测试的价值在于：它们正好覆盖 package、contract、环境和命令构造四条主线。

---

## 9.4 reviewer checklist

评审 `metaharness_ext.jedi` 时，优先检查：

- 是否仍然坚持 MHE extension 视角，而不是软件综述视角
- contracts 是否清晰区分 family
- compiler 是否只从 typed spec 生成受控 YAML
- environment probe 是否发生在 compiler/executor 之前
- executor 是否只知道 execution mode，而不理解业务 YAML 结构
- validator 是否只负责判定，而不承担运行或编译职责
- tests 是否真正覆盖 failure taxonomy，而不是只测 happy path

---

## 9.5 最值得早期卡住的 review 问题

如果在评审中看到以下迹象，应尽早要求返工：

- `contracts.py` 开始堆大量 `dict[str, object]` 弱类型逃逸
- `config_compiler.py` 接受任意外部 YAML 透传
- `executor.py` 里出现 family-specific YAML 结构逻辑
- `validator.py` 里偷偷补环境探测
- 测试直接把 CTest test name 当 executable name 用

这些问题越早纠正，代价越低。

---

## 9.6 Phase 演进时的测试策略

随着 phase 推进，测试重点应同步前移：

- Phase 0：package / contract / env / validate-only
- Phase 1：smoke / artifact layout / runtime success-failure split
- Phase 2：variational baseline + minimum scientific evidence
- Phase 3：ensemble baseline
- Phase 4+：diagnostics summary / study / mutation

这比一开始就追求“大而全 e2e”更稳健，也更符合 extension-first 的演进节奏。

---

## 9.7 文档评审同样重要

JEDI extension 的 wiki 与 blueprint/roadmap 不是附属品，而是正式设计资产。

因此评审时也应检查：

- 术语是否统一（family、baseline、smoke、diagnostics）
- 技术事实是否与当前修正后的 JEDI wiki 一致
- 文档是否持续强调 executable name 与 CTest test name 的区别
- 文档是否没有重新膨胀回 JEDI 软件百科

只有代码与文档同时守住边界，`metaharness_ext.jedi` 才会稳定。