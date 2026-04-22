# JEDI Extension for MHE Wiki

> 版本：v1.0 | 最后更新：2026-04-22

本目录只讨论 **如何在 `MHE` 中设计、实现和演进 `metaharness_ext.jedi`**，不再承担 JEDI 软件本体（如 OOPS / IODA / UFO / SABER 架构综述、构建细节、算法百科）的通用软件 wiki 职责。

适合以下读者：

- 需要设计 `MHE/src/metaharness_ext/jedi/` 的工程师
- 需要评审 `contracts / compiler / executor / validator` 边界的架构师
- 需要把 JEDI workflow 以受控方式接入 MHE runtime 的扩展开发者
- 需要基于 JEDI extension 做 smoke baseline、study 或 agent orchestration 的维护者

---

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-扩展定位](01-extension-positioning.md) | 为什么 MHE 需要 JEDI extension、接口层级选择、范围边界 | 所有人 |
| [02-架构总览](02-architecture.md) | gateway / environment / compiler / executor / validator 的组件链 | 架构师 / 核心开发 |
| [03-contracts 设计](03-contracts.md) | family-aware typed contracts、运行/验证报告、typed boundary | 核心开发 |
| [04-执行链设计](04-execution-pipeline.md) | schema / validate-only / real-run 的分层执行语义 | 运行时工程师 |
| [05-环境与验证](05-environment-and-validation.md) | environment probe、artifact 归档、failure taxonomy、evidence | 运行时 / 平台工程师 |
| [06-实施路径](06-implementation-phases.md) | blueprint / roadmap / implementation plan 的映射与 Phase 拆分 | 实现负责人 / reviewer |
| [07-family 设计](07-family-design.md) | variational / local_ensemble_da / hofx / forecast 的 family 边界 | 架构师 / compiler 维护者 |
| [08-封装与注册](08-packaging-and-registration.md) | 包结构、exports、capabilities、slots、manifest 设计 | 核心开发 / reviewer |
| [09-测试与评审](09-testing-and-review.md) | 测试层次、review checklist、phase-aware 验证策略 | reviewer / 测试维护者 |

---

## 术语与交叉引用约定

为保持整套 wiki 的 PR-ready 风格，本文档集统一采用以下约定：

- prose 中使用 **application family** 表示概念层；代码字段一律写作 `application_family`
- prose 中使用 **execution mode** 表示概念层；代码字面量一律写作 `schema`、`validate_only`、`real_run`
- prose 中使用 **validate-only**、**real run** 作为自然语言写法，不把 snake_case 代码字面量直接混入叙述句
- **smoke baseline** 指轻量、低成本、优先验证执行链的 baseline；**scientific baseline** 指带最小科学证据或正式科学判据的 baseline；**toy baseline** 指刻意缩小问题规模的 baseline
- **run artifact** 指一次执行产生的结构化运行产物集合；`evidence_files` 指 validator/report 对外暴露的关键证据文件列表
- Phase 0 中 **diagnostics** 只作为未来 evidence surface 与 artifact layout 预留项，不要求结构化解析或 scientific 判定

交叉引用规则：

- 组件职责以 [02-架构总览](02-architecture.md) 为主
- contract 定义以 [03-contracts 设计](03-contracts.md) 为主
- execution mode 语义以 [04-执行链设计](04-execution-pipeline.md) 为主
- failure taxonomy 与 evidence 语义以 [05-环境与验证](05-environment-and-validation.md) 为主
- phase mapping 与 baseline 节奏以 [06-实施路径](06-implementation-phases.md) 为主
- application family 边界以 [07-family 设计](07-family-design.md) 为主
- packaging / manifest / capability / slot 约定以 [08-封装与注册](08-packaging-and-registration.md) 为主
- tests 与 reviewer checklist 以 [09-测试与评审](09-testing-and-review.md) 为主

---

## 本目录的设计原则

`metaharness_ext.jedi` 的首版不是：

- JEDI C++ API 的 Python binding
- 任意 YAML 透传器
- 任意 executable 的黑盒 launcher 包装层
- JEDI 软件百科或构建教程的替代品

`metaharness_ext.jedi` 的首版是：

- **family-aware** 的 typed extension
- 以 **YAML** 为稳定控制面
- 以 **launcher + executable** 为执行面
- 以 **environment probe + validator** 为失败边界
- 以 **artifact / diagnostics / report** 为证据面

---

## 与 blueprint / roadmap 的关系

本目录服务于 `metaharness_ext.jedi` 的工程实现，和 blueprint 文档形成如下分工：

- `blueprint/01-jedi-extension-blueprint.md`：正式设计蓝图
- `blueprint/01-jedi-extension-roadmap.md`：分阶段路线图
- `blueprint/01-jedi-extension-implementation-plan.md`：当前可执行实施计划（Phase 0）
- 本目录：把上述正式文档拆解成便于实现、维护和代码评审的工程设计 wiki

如果 blueprint / roadmap 与当前环境事实存在未决差异，本目录的策略是：

- Phase 0 只承诺 environment probe + validate-only 的最小闭环
- Phase 1 的 smoke baseline 与 observation-path 选择，必须由 environment probe 和 data readiness 结果来 gate
- 不把尚未验证的外部构建/安装状态直接写死成实现前提

---

## 当前推荐阅读顺序

### 如果你要先理解扩展做什么

先看：[01-扩展定位](01-extension-positioning.md)

### 如果你要开始写代码

先看：[02-架构总览](02-architecture.md) → [03-contracts 设计](03-contracts.md) → [04-执行链设计](04-execution-pipeline.md) → [08-封装与注册](08-packaging-and-registration.md)

### 如果你要设计 family 边界与 baseline

先看：[07-family 设计](07-family-design.md) → [06-实施路径](06-implementation-phases.md)

### 如果你要评审失败语义与测试策略

先看：[05-环境与验证](05-environment-and-validation.md) → [09-测试与评审](09-testing-and-review.md)

---

## 不在本目录展开的内容

以下内容已不再作为本目录主线：

- JEDI 软件本体的通用背景介绍
- OOPS / IODA / UFO / SABER 的完整架构综述
- JEDI bundle 的构建教程与 GCC 兼容性细节
- 极小化器算法百科
- 观测系统的领域知识型长篇说明

这些内容应保留在外部 JEDI 文档或单独的软件 wiki 中；本目录只在 **设计 `metaharness_ext.jedi` 所必需** 的地方引用它们。