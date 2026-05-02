# Research Loop MVP Wiki

本 wiki 记录 MHE Research Loop MVP 的架构演进、模型设计、实现历史、CLI 入口与验收边界。

## 目录

- [01-overview.md](01-overview.md) — MVP 概述：研究闭环概念、MVP 与 Science Discovery Vision 分层
- [02-architecture-evolution.md](02-architecture-evolution.md) — 架构演进：plan-v1 → plan-v2 → plan-v3 → plan-v4 的修正链
- [03-models-and-data-flow.md](03-models-and-data-flow.md) — 模型与数据流：Research Lifecycle 模型、DAG 设计、store 策略
- [04-implementation-history.md](04-implementation-history.md) — 实现历史：P0a–P4 + v4 CLI 的按阶段交付记录与 git commit 映射
- [05-cli-and-user-entry.md](05-cli-and-user-entry.md) — CLI 与用户入口：research-run 子命令、示例输入、fixture、产物
- [06-verification-and-boundaries.md](06-verification-and-boundaries.md) — 验证与边界：测试覆盖、非声明、已延后能力

## 推荐阅读路径

- 新读者：按 01 → 03 → 05 顺序了解 MVP 是什么、数据结构如何、怎么运行
- 需要理解设计决策：按 01 → 02 → 04 顺序追踪架构如何从 v1 演进到 v4 并落地
- 需要判断剩余工作：从 06 开始，确认哪些是已延后而非未完成
