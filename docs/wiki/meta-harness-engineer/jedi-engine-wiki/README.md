# JEDI Extension for MHE Wiki

> 版本：v1.1 | 最后更新：2026-04-24

本目录只讨论 **如何在 `MHE` 中设计 `metaharness_ext.jedi`**。

它关注的是扩展层的设计边界：contracts、execution semantics、environment/validation surface、family model、packaging 与 review invariants。

本目录**不再承载**以下内容作为主线：

- 分阶段实施细节
- 文件级脚手架清单
- 当前实现状态盘点
- roadmap / milestone 推进说明
- 混合在设计文档中的 implementation plan 叙述

这些内容统一下沉到 `blueprint/` 目录中的正式文档；本 wiki 不保留它们的主阅读路径版本。

---

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-扩展定位](01-extension-positioning.md) | 为什么 MHE 需要 JEDI extension、接口层级选择、范围边界 | 所有人 |
| [02-架构总览](02-architecture.md) | gateway / environment / compiler / executor / validator 的组件链 | 架构师 / 核心开发 |
| [03-contracts 设计](03-contracts.md) | family-aware typed contracts、运行/验证报告、typed boundary | 核心开发 |
| [04-执行链设计](04-execution-pipeline.md) | schema / validate-only / real-run 的分层执行语义 | 运行时工程师 |
| [05-环境与验证](05-environment-and-validation.md) | environment probe、failure taxonomy、evidence/report semantics | 运行时 / 平台工程师 |
| [06-设计文档分工](06-implementation-phases.md) | wiki 与 blueprint / roadmap / implementation plan 的职责分工与边界 | 文档维护者 / reviewer |
| [07-family 设计](07-family-design.md) | variational / local_ensemble_da / hofx / forecast 的 family 边界 | 架构师 / compiler 维护者 |
| [08-封装与注册](08-packaging-and-registration.md) | 包结构、exports、capabilities、slots、manifest 设计 | 核心开发 / reviewer |
| [09-测试与评审](09-testing-and-review.md) | 测试边界、review checklist、设计不变量 | reviewer / 测试维护者 |

---

## 术语约定

- prose 中使用 **application family**；代码字段写作 `application_family`
- prose 中使用 **execution mode**；代码字面量写作 `schema`、`validate_only`、`real_run`
- prose 中使用 **validate-only**、**real run** 作为自然语言写法
- **family** 表示扩展层支持的应用族边界；**baseline** 表示某个 family 下被选中的具体运行样例
- **run artifact** 指一次运行产出的结构化证据集合；`evidence_files` 指 report 或 evidence bundle 对外暴露的关键证据文件

---

## 设计原则

`metaharness_ext.jedi` 的首版应被理解为：

- **family-aware** 的 typed extension
- 以 **YAML** 为稳定控制面
- 以 **launcher + executable** 为执行面
- 以 **environment probe + validation report** 为失败边界
- 以 **artifact / diagnostics / report** 为证据面

因此本目录的写作重点是 **设计边界**，而不是交付顺序或实现脚手架。

---

## 与 `blueprint/` 的分工

JEDI 扩展的正式实施材料位于 `MHE/docs/wiki/meta-harness-engineer/blueprint/`：

- `01-jedi-extension-blueprint.md`：正式设计蓝图
- `01-jedi-extension-roadmap.md`：阶段路线与里程碑
- `01-jedi-extension-implementation-plan.md`：实施计划与验收面
- `01-jedi-extension-wiki-refocus-report.md`：本次 wiki 重构后的内容分流说明

分工原则如下：

- **本 wiki**：回答“这个扩展应如何被设计”
- **blueprint**：回答“正式设计主张是什么”
- **roadmap**：回答“按什么顺序推进”
- **implementation plan**：回答“当前阶段具体怎么做、改哪些文件、怎么验收”

---

## 推荐阅读顺序

### 想先理解扩展边界

先看：[01-扩展定位](01-extension-positioning.md) → [02-架构总览](02-architecture.md) → [03-contracts 设计](03-contracts.md)

### 想理解运行与失败语义

先看：[04-执行链设计](04-execution-pipeline.md) → [05-环境与验证](05-environment-and-validation.md)

### 想设计 family 与注册面

先看：[07-family 设计](07-family-design.md) → [08-封装与注册](08-packaging-and-registration.md)

### 想看实施材料

转到：`blueprint/01-jedi-extension-blueprint.md`、`blueprint/01-jedi-extension-roadmap.md`、`blueprint/01-jedi-extension-implementation-plan.md`

---

## 不在本目录展开的内容

以下内容不再作为本目录主线：

- JEDI 软件本体的通用背景综述
- OOPS / IODA / UFO / SABER 的完整软件架构说明
- 构建教程与环境兼容性细节
- 极小化器算法百科
- 分阶段执行清单与当前实现盘点

本目录只保留 **设计 `metaharness_ext.jedi` 所必需** 的内容。