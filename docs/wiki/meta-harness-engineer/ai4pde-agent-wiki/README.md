# AI4PDE Agent 技术手册 / 软件 Wiki

> 版本：v0.2 | 最后更新：2026-04-19

本目录是 `Aeloon` 中 `AI4PDE Agent` 子系统的独立中文技术手册，面向以下读者：

- 需要设计或实现 AI4PDE 科学智能体的研发人员
- 需要将 PDE 求解能力、团队运行时与元优化框架整合的架构师
- 需要维护 AI4PDE workflow、模板库、验证器与治理机制的工程师
- 需要部署、审计、排障长航时 PDE 科学任务的运维与平台人员

---

## 文档目录

| 文档 | 主题 | 状态 |
|---|---|---|
| [01-Architecture Spec](01-architecture-spec.md) | AI4PDE Team Runtime + Meta-Harness 的总体架构规范 | draft |
| [02-Runtime Flow](02-runtime-flow.md) | 从任务形式化到 team 协作、求解、验证、回滚与交付的生命周期 | draft |
| [03-Data Models](03-data-models.md) | Team、Task、Mailbox、Graph Version、Evidence、Template 等核心对象 | draft |
| [04-Governance and Observability](04-governance-and-observability.md) | 科学治理不变量、预算、风险、审计、回放与观测分层 | draft |
| [05-Template Library and Self-Growth](05-template-library-and-self-growth.md) | PDE 模板库、模板状态流转、自增长阶梯与失败记忆机制 | draft |
| [06-Implementation Blueprint](06-implementation-blueprint.md) | 基于 MHE 落地 AI4PDE 域软件的分层实现蓝图 | draft |
| [07-Scaffold Plan](07-scaffold-plan.md) | 面向仓库落地的文件级脚手架计划、职责划分与实现顺序 | draft |
| [08-Development Roadmap](08-development-roadmap.md) | 将脚手架方案拆解为 milestone 驱动的执行任务与完成标准 | draft |

---

## 定位

`AI4PDE Agent` 不是单纯的“PDE 求解工具代理”，而是一个结合了：

- **Team Runtime**：多 worker 协作执行
- **Meta-Harness**：受控自增长与工作流演化
- **PDE Capability Fabric**：PINN / DEM / Operator / PINO / Classical Hybrid 求解能力
- **Scientific Governance**：证据优先、预算控制、图版本回滚、可重放审计

的科学智能体子系统。

---

## 设计来源

本 wiki 的架构吸收并融合了以下设计思想：

- [science-agent-wiki](../science-agent-wiki/)：任务生命周期、能力层、验证闭环
- [agent-team-wiki](../AI4SE+SoulAnchor/agent-team-wiki/)：team runtime、task list、mailbox、approval、idle/recovery
- [meta-harness-wiki](../meta-harness-wiki/)：candidate graph、template library、policy engine、observability、hot reload、rollback

---

## 与 science-agent-wiki 的关系

本文档目录是 [science-agent-wiki/07-ai4pde-team-runtime-meta-harness.md](../science-agent-wiki/07-ai4pde-team-runtime-meta-harness.md) 的展开版：

- 07 是综合架构概览，涵盖三层架构、Team Runtime、Meta-Harness、治理与演化路线
- 本 wiki 将 07 的内容拆分为 5 个独立章节，各自深入展开
- 两份文档应保持核心概念（不变量、槽位定义、模板目录、状态枚举）的一致性

---

## 阅读建议

### 如果你想快速理解 AI4PDE Agent 是什么

先看：[01-Architecture Spec](01-architecture-spec.md)

### 如果你关心多 worker 协作

先看：[02-Runtime Flow](02-runtime-flow.md)

### 如果你关心核心对象与持久化

先看：[03-Data Models](03-data-models.md)

### 如果你关心治理、审计与回放

先看：[04-Governance and Observability](04-governance-and-observability.md)

### 如果你关心工作流如何安全进化

先看：[05-Template Library and Self-Growth](05-template-library-and-self-growth.md)

---

## 术语表

| 术语 | 定义 |
|---|---|
| **PDE Capability Fabric** | 运行期求解能力层，由 11 个可替换 slot 组成 |
| **Meta-Harness** | 系统演化运行时，负责图版本管理、策略审查与受控自增长 |
| **Team Runtime** | 执行协作运行时，负责多 worker 团队的任务分配、消息与审批 |
| **Evidence-First Delivery** | 证据先于结论的交付范式，所有结论必须绑定溯源与验证证据 |
| **Slot** | 运行期可替换组件的稳定抽象槽位，通过契约（contract）定义输入输出 |
| **Candidate Graph** | 待验证的工作流图版本，通过沙盒/影子验证后才能激活 |
| **Observation Window** | 图版本切换后的监控期，用于检测退化并决定 stabilize 或 rollback |
| **Protected Slot** | 受治理保护的槽位（PolicyGuard、EvidenceManager 等），普通优化器不可修改 |
