# QCompute Extension for MHE Wiki

> 版本：v0.1 | 最后更新：2026-04-25

本目录只讨论 **如何在 `MHE` 中设计 `metaharness_ext.qcompute`**——即 Meta-Harness Engine
的量子计算（Quantum Computing）扩展包。所有涉及跨扩展协调、蓝图规划、实现阶段拆解、
历史版本归档的内容，均不在本目录展开。

## 排除项

- **不** 包含实现阶段分解（转至 `blueprint/`）
- **不** 包含进度跟踪或 checklist（转至 `blueprint/`）
- **不** 包含历史版本或已废弃方案（转至 `.trash/`）
- **不** 包含跨扩展协调文档（转至 `blueprint/` 或上级 `README.md`）

## 导航

| 文档 | 主题 | 读者 |
|------|------|------|
| [01-overview.md](01-overview.md) | 概述与定位：量子计算在 MHE 中的角色 | 所有人 |
| [02-workflow-and-components.md](02-workflow-and-components.md) | 工作流与组件链：Gateway → Environment → ConfigCompiler → Executor → Validator | 开发者、架构师 |
| [03-contracts-and-artifacts.md](03-contracts-and-artifacts.md) | Contracts 与产物：Pydantic 模型体系 | 开发者 |
| [04-environment-validation-and-evidence.md](04-environment-validation-and-evidence.md) | 环境探测、验证与证据：噪声感知评分与 promotion-readiness | 开发者、评审者 |
| [05-family-design.md](05-family-design.md) | Family 设计：ansatz 族、backend 族、error-mitigation 策略族 | 架构师 |
| [06-packaging-and-registration.md](06-packaging-and-registration.md) | 封装与注册：manifest、slot、capability 声明 | 开发者 |
| [07-scope-and-boundaries.md](07-scope-and-boundaries.md) | 范围与分工：QCompute 的职责边界与 MHE 核心的集成面 | 架构师、评审者 |
| [08-testing-and-review.md](08-testing-and-review.md) | 测试与评审：模拟器测试、mock backend、promotion-readiness 覆盖 | 开发者、QA |

## 当前状态

QCompute 扩展处于 **设计阶段**。本文档描述的是目标架构和设计决策，而非已实现功能。
核心设计围绕以下主线展开：

- **量子-经典混合 Agent 编排**：Agent 作为控制中枢，调度经典预处理 → 量子执行 → 经典后处理的闭环
- **评估驱动的电路编译优化**：基于 SimpleTES 的 C×L×K 范式，实现"生成-编译-评估-再生成"动态优化
- **多后端抽象**：统一 Quafu 真机、Qiskit Aer 模拟器及其他量子云平台的访问接口
- **与 ABACUS/DeepMD 的协同**：经典 DFT + 量子 NISQ 混合工作流的编排能力

## 阅读路径

- **快速了解**：从 [01-overview.md](01-overview.md) 开始
- **理解组件设计**：顺序阅读 02 → 03 → 04
- **着手实现**：阅读 05（family 设计）和 06（注册），然后参考 08（测试）
- **评审架构决策**：阅读 01、02、07

## 研究辅助

以下提示文件供外部研究 Agent（Gemini、GLM 等）使用，收集 QCompute 设计所需的精确技术信息：

| 文档 | 主题 | 目标模型 | 用途 |
|------|------|---------|------|
| [research-prompt-01-quantum-agent-landscape.md](research-prompt-01-quantum-agent-landscape.md) | 量子计算 × Agent 集成全景 | Gemini / 通用 | 全球量子云平台、QUASAR/QAgent/SimpleTES 架构、VQE hybrid workflows、error mitigation landscape、transpilation pipeline、Agent 框架对比 |
| [research-prompt-01-quantum-agent-landscape-glm.md](research-prompt-01-quantum-agent-landscape-glm.md) | 量子计算 × Agent 集成全景（中国生态版） | GLM / 中文模型 | 中国量子生态专项：pyQuafu SDK 精确 API、QuafuCloud MCP schema、QSteed 嵌入方案、中国量子软件评估矩阵、ABACUS↔QCompute 数据交接合约、Quafu 芯片噪声特征 |
| [research-prompt-02-qcompute-extension-design.md](research-prompt-02-qcompute-extension-design.md) | QCompute 扩展工程设计细化 | 通用 | 组件接口细化、合约 schema 验证、测试策略、MCP 深度集成 |
