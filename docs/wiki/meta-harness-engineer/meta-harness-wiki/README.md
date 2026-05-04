# Meta-Harness 技术手册 / 软件 Wiki

本目录是 Meta-Harness 自我重长框架的中文技术手册，面向以下读者：

- 需要理解元Harness整体设计与组件化架构的研发人员
- 需要实现或替换某个核心组件（Runtime / Memory / Evaluation 等）的工程师
- 需要扩展新组件模板、新搜索策略、新安全规则的平台贡献者
- 需要部署、审计、排障自我重长循环的运维人员
- 需要把科学计算 extension 接入 assembly / instantiation / selection / metrics 治理边界的维护者

---

## 文档目录

| 文档 | 主题 |
|---|---|
| [01-概述与设计理念](01-overview.md) | 核心问题、PDE类比、9组件分类、统一术语基线、与 Aeloon Plugin SDK 的关系 |
| [02-组件 SDK 架构](02-component-sdk.md) | HarnessComponent、HarnessAPI、ComponentRuntime、Manifest、staged lifecycle、pending mutations |
| [03-核心组件实现](03-core-components.md) | 9大核心组件的接口定义、默认实现、slot system、capability vocabulary、protected components |
| [04-连接引擎与配置](04-connection-engine.md) | XML/XSD 配置规范、ConnectionEngine、5条兼容规则、PendingConnection、graph versioning、契约驱动剪枝 |
| [05-自我重长与 Optimizer](05-self-growth.md) | 3-phase搜索（参数/拓扑/受限合成）、进化/BO/RL策略、GIN状态编码、4层动作漏斗、三重收敛判据 |
| [06-安全控制与治理](06-safety-governance.md) | 4级安全链路、3级沙箱、Policy宪法层、invariant库、治理hooks、间接攻击防护 |
| [07-可观测性与审计](07-observability-audit.md) | 3层可观测模型、Trace/Replay、evidence对象、Merkle审计链、Provenance查询、反事实诊断 |
| [08-热加载与状态迁移](08-hot-reload.md) | STR协议、Checkpoint策略、组件级蓝绿部署、观察窗口、Saga回滚、迁移适配器 |
| [09-模板库与代码生成](09-template-library.md) | 模板设计原则、slot filling vs 自由生成、6步代码生成管线、MVP Proposer、反事实诊断提示 |
| [10-开发与扩展指南](10-extension-guide.md) | 候选图优先的扩展流程、新建组件、替换核心组件、创建模板、扩展搜索策略、添加安全规则与hooks、5阶段实施路线图 |
| [11-MHE Core 升级框架与 Extension 改进指南](11-upgraded-core-framework-and-extension-improvement.md) | assembly、instantiation、selection、metrics 升级后的 core 框架能力与 extension 改进路线 |

---

## 快速导航

### 如果你只想知道"Meta-Harness 是什么"

先看：[01-概述与设计理念](01-overview.md)

### 如果你要实现或替换某个组件

先看：[02-组件 SDK 架构](02-component-sdk.md) 与 [03-核心组件实现](03-core-components.md)

### 如果你要理解组件间如何连接

先看：[04-连接引擎与配置](04-connection-engine.md)

### 如果你要理解"自我重长"怎么工作

先看：[05-自我重长与 Optimizer](05-self-growth.md)

### 如果你要理解安全机制

先看：[06-安全控制与治理](06-safety-governance.md)

### 如果你要部署、排障、审计

先看：[07-可观测性与审计](07-observability-audit.md) 与 [08-热加载与状态迁移](08-hot-reload.md)

### 如果你要扩展新能力

先看：[10-开发与扩展指南](10-extension-guide.md)

### 如果你要理解升级后的 core 能力如何反哺 extension

先看：[11-MHE Core 升级框架与 Extension 改进指南](11-upgraded-core-framework-and-extension-improvement.md)

该页对应当前已实现的 core upgrade docs，覆盖：

- assembly ledger、copy-count index、dependency DAG snapshot 与 assembly-health summary
- `ExecutionMode`、`InstantiationRecord` 与 external evidence refs
- selection lifecycle（promoted / deprecated / suspended / graveyard）
- `AssemblyMetricsService` 与 `metrics assembly` report 边界
- extension portfolio 从 dry-run / simulation 到 gated real-tool / external verification 的升级路线

---

## 与 meta-harness-book 的关系

`docs/meta-harness-book/meta-harness-book.md` 是面向学术/架构读者的设计手册，阐述"为什么这样设计"。

本 Wiki 是面向工程落地读者的技术手册，阐述"怎么实现"——包含接口定义、代码骨架、配置格式、数据模型、CLI surfaces、claim boundary 和扩展方式。

---

## 适用版本

- 设计版本：`metaharness v0.1.0`（开发中）
- 参考实现语言：Python `>=3.11`
- 推荐开发环境：Python 3.13（当前 Ruff target 为 `py313`）
- 核心依赖：Pydantic `>=2.12,<3`
- 开发工具：pytest `>=9,<10`、ruff `==0.15.6`
- 配置格式：XML + XSD
- 清单格式：JSON（`harness.component.json`）
- CLI surfaces：`demo`、`validate`、`benchmark-run`、`benchmark-compare`、`benchmark-approval-check`、`research-run`，以及 core upgrade docs 中描述的 `metrics assembly`

---

## 架构方向说明

为避免把不同层次的工作混在一起，阅读本 Wiki 时可区分三类内容：

- **当前 MHE**：仓库中已实现或已有骨架支撑的能力，包括 runtime graph authority、manifest discovery、semantic validation、safety/provenance/hot-reload、extension packages、benchmark/research CLI surfaces，以及 assembly / instantiation / selection / metrics governance docs
- **强化路线图**：当前正在推进的工程补强，用于把现有图模型、治理、证据、热切换、benchmark approval 和 extension portfolio 改进路径做稳
- **更长期的 CMA-inspired 基础设施方向**：在上述工作之外，未来可能继续演进的控制面/执行面解耦方向

后者主要包括：以 `SessionStore` / `SessionEvent` 为追加型状态与观测基底、逐步推动 `HarnessRuntime` 无状态化与 `wake(session_id)` 恢复、以惰性沙箱形成更强执行边界、以 `Credential Vault` 提供强于当前 `InMemoryIdentityBoundary` 的凭证隔离，以及把 `BrainProvider` 抽象和事件驱动可观测性纳入统一基础设施视角。这些方向用于帮助理解 MHE 的长期演进，不等同于当前版本已全部实现。

---

## Claim Boundaries

- assembly metrics、copy-count、lineage completeness、benchmark reports 和 research-loop traces 只能说明治理、复用、证据完整性与 workflow 可审计性；它们不单独证明科学有效性、数值正确性或性能优越性。
- simulation / dry-run evidence 不等价于真实 solver、真实硬件或真实外部 execution。
- externally verified execution 需要 explicit external evidence refs，例如 solver logs、hardware/backend receipts、artifact hashes、reviewed tolerances 或第三方验证材料。
- optional real-tool / hardware paths 必须保持 explicit gate，不应被默认 CI、默认 demo 或文档示例暗示为已自动运行。
