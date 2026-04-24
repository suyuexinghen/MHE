# AI4PDE Agent 技术手册 / 软件 Wiki

> 版本：v1.0 | 最后更新：2026-04-24

本目录只讨论 **如何在 `MHE` 中设计 `AI4PDE Agent` 的 team runtime、scientific workflow 与受控演化边界**。

它关注的是子系统级设计边界：runtime lifecycle、typed data models、scientific governance、template library 与 self-growth semantics。

本目录**不再承载**以下内容作为主线：

- 分阶段实施细节
- 文件级脚手架清单
- 当前实现状态盘点
- roadmap / milestone 推进说明
- 混合在设计文档中的 implementation plan 叙述

这些内容统一下沉到 `blueprint/` 目录中的正式文档。

---

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-架构规范](01-architecture-spec.md) | AI4PDE = Team Runtime + Meta-Harness + PDE Capability Fabric 的总体设计 | 所有人 |
| [02-运行流程](02-runtime-flow.md) | 从任务形式化到 team 协作、求解、验证、交付与图版本演化的生命周期 | 架构师 / 运行时开发 |
| [03-数据模型](03-data-models.md) | task、team、mailbox、graph version、evidence、template 等 typed object 边界 | 核心开发 / 存储维护者 |
| [04-治理与可观测性](04-governance-and-observability.md) | 科学治理不变量、预算、风险分级、观察窗口、审计与回放 | 平台 / 治理 / reviewer |
| [05-模板库与自增长](05-template-library-and-self-growth.md) | workflow template、状态流转、受控变体空间与失败记忆 | 架构师 / optimizer 维护者 |

---

## 术语约定

- prose 中使用 **Team Runtime**；对象命名写作 `PDETeamFile`、`PDEWorkerTask`、`PDEMailboxMessage`
- prose 中使用 **Meta-Harness**；图对象字段写作 `graph_version_id`、`template_id`、`instantiation_id`
- prose 中使用 **scientific governance**；规则对象使用 invariant、risk level、budget gate 等术语
- **candidate graph** 表示待验证的工作流图版本；**active graph** 表示当前承载生产任务的稳定图版本
- **evidence bundle** 指一次科学任务交付所需的结构化证据集合；**provenance** 指结果的可追溯来源链

---

## 设计原则

`AI4PDE Agent` 的首版应被理解为：

- **team-scoped** 的科学协作运行时
- 以 **typed workflow + typed evidence** 为稳定控制面
- 以 **planner / router / solver / validator** 为执行面
- 以 **policy / budget / rollback** 为治理面
- 以 **template library + controlled self-growth** 为演化面

因此本目录的写作重点是 **设计边界与职责分层**，而不是交付顺序或实现脚手架。

---

## 与 `blueprint/` 的分工

AI4PDE 的正式实施材料位于 `MHE/docs/wiki/meta-harness-engineer/blueprint/`：

- `03-ai4pde-implementation-blueprint.md`：正式设计蓝图
- `03-ai4pde-development-roadmap.md`：阶段路线与里程碑
- `03-ai4pde-scaffold-plan.md`：实施计划、文件脚手架与验收面

分工原则如下：

- **本 wiki**：回答“这个子系统应如何被设计”
- **blueprint**：回答“正式设计主张是什么”
- **roadmap**：回答“按什么顺序推进”
- **scaffold plan**：回答“当前阶段具体怎么做、改哪些文件、怎么验收”

---

## 设计来源

本 wiki 的架构吸收并融合了以下设计思想：

- [science-agent-wiki](../science-agent-wiki/)：任务生命周期、能力层、验证闭环
- [agent-team-wiki](../AI4SE+SoulAnchor/agent-team-wiki/)：team runtime、task list、mailbox、approval、idle/recovery
- [meta-harness-wiki](../meta-harness-wiki/)：candidate graph、template library、policy engine、observability、hot reload、rollback

---

## 与 `science-agent-wiki` 的关系

本文档目录是 `science-agent-wiki/07-ai4pde-team-runtime-meta-harness.md` 的展开版：

- `07` 提供三层架构、Team Runtime、Meta-Harness 与治理的综合视图
- 本 wiki 将其拆分为 5 个设计章节，分别讨论运行时、对象模型、治理与演化边界
- 两份文档应保持核心概念（不变量、slot 定义、模板目录、状态枚举）的一致性

---

## 推荐阅读顺序

### 想先理解子系统边界

先看：[01-架构规范](01-architecture-spec.md) → [02-运行流程](02-runtime-flow.md) → [03-数据模型](03-data-models.md)

### 想理解治理与交付可信度

先看：[04-治理与可观测性](04-governance-and-observability.md)

### 想理解模板化演化与受控改进

先看：[05-模板库与自增长](05-template-library-and-self-growth.md)

### 想看实施材料

转到：`blueprint/03-ai4pde-implementation-blueprint.md`、`blueprint/03-ai4pde-development-roadmap.md`、`blueprint/03-ai4pde-scaffold-plan.md`

---

## 不在本目录展开的内容

以下内容不再作为本目录主线：

- PDE 方法学教材式综述
- PINN / DEM / Operator / PINO 的算法百科
- 构建教程与环境兼容性细节
- 文件级落地计划与当前实现盘点
- 分阶段执行清单与 milestone 跟踪

本目录只保留 **设计 `AI4PDE Agent` 所必需** 的内容。
