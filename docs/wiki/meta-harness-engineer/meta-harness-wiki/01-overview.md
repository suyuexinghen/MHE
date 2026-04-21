# 01. 概述与设计理念

## 1.1 Meta-Harness 解决什么问题

当前大多数 Agent 框架采用"固定配置"范式：开发者手工编排 Prompt、工具链、记忆模块与控制流，部署后结构基本不变。当面对任务分布漂移、性能瓶颈或资源约束时，这种范式缺乏弹性。

Meta-Harness 的核心主张：**Agent 系统的外层结构（Harness）应当成为可自动优化的对象**。不仅优化模型权重，更要优化包裹模型外部的运行框架——组件组合、连接关系、配置参数。

## 1.2 设计理念：PDE 迭代收敛类比

借鉴数值偏微分方程（PDE）求解器的思想：

| PDE 求解器 | Meta-Harness |
|---|---|
| 初始猜测 | 开发者提供的基础 XML 配置 |
| 残差（Residual） | 性能向量与目标之间的差距 |
| 更新操作 | Optimizer 生成新组件组合或调整参数 |
| 收敛准则 | Hypervolume 稳定 + 统计检验 + 复杂度上限 |

> **类比边界**：这是直觉层面的类比，而非严格的形式等价。Agent 系统的搜索空间是非凸、非连续、部分可观测的，不存在 Banach 不动点定理的收敛保证。PDE 类比的价值在于提供"迭代改进直至停止"的工程框架。

## 1.3 组件分类

Meta-Harness 将系统分为三类构建块：

```
┌─────────────────────────────────────────────────────────┐
│ 元层（Meta Layer）                                       │
│   Optimizer — 驱动自我重长循环，不参与任务执行             │
├─────────────────────────────────────────────────────────┤
│ 核心组件（Core Components）× 9                           │
│   Gateway / Runtime / Memory / ToolHub                   │
│   Planner / Executor / Evaluation                        │
│   Observability / Policy / Governance                    │
│   每个组件可通过 Component SDK 独立实现和替换             │
├─────────────────────────────────────────────────────────┤
│ 模板组件（Template Components）                          │
│   BM25Retriever / ContextPruner / ChainOfThoughtPlanner  │
│   RetryWithBackoff / LoopGuard / SemanticValidator ...   │
│   由模板库提供，Optimizer 可按需实例化                    │
└─────────────────────────────────────────────────────────┘
```

### 核心组件职责速查

> **实现对齐说明（当前 MHE）**：下面的表格表示目标职责边界；当前 `MHE/src/metaharness/components/` 已实现对应组件与 slot，但多数默认组件仍是最小可运行实现，重点在 contracts、graph staging、validation、proposal-only mutation flow 与 demo wiring，而不是完整生产级能力。

| 组件 | 当前实现对齐 |
|---|---|
| **Gateway** | 已实现最小入口组件与 `gateway.primary` slot；负责把外部输入归一为内部任务载荷，尚未实现完整凭证边界/身份根 |
| **Runtime / Orchestrator** | 已实现最小 `runtime.primary` 组件；真正的装配/启动编排由 `HarnessRuntime` 承担，而非组件本身承担完整调度职责 |
| **Memory** | 已实现组件、状态导出/导入接口与 checkpoint 支撑；尚非完整上下文管理与长期存储系统 |
| **ToolHub** | 已实现组件与基础工具平面骨架；尚非完整工具目录、沙箱代理与远程执行系统 |
| **Planner / Reasoner** | 已实现最小 planner 组件与 demo 规划输出；尚非完整多策略规划器 |
| **Executor** | 已实现最小 executor 组件与 demo 执行输出；复杂动作执行/回退仍待扩展 |
| **Evaluation** | 已实现最小评分输出组件；优化器中的 `fitness` / `convergence` 已独立实现，但 Pareto/frontier 仍主要停留在概念层 |
| **Observability** | 已实现审计、Merkle、PROV 图、查询与反事实诊断模块；完整全链路 trace / crash recovery / 分层存储仍未做成统一运行时产品面 |
| **Policy / Governance** | 已实现 proposal reviewer、四级 safety pipeline、guard/mutate/reduce hooks 与 veto 边界；独立进程级宪法层仍属后续增强 |

### 扩展能力（非核心 taxonomy）

以下能力作为**受保护的根能力或扩展依赖边界**存在，不单独列为独立核心组件；其中只有部分机制已在当前 MHE 中落地：

| 能力 | 当前实现状态 | 融入位置 |
|---|---|---|
| **Identity** | **未作为独立实现落地**；当前仅保留文档中的边界概念 | 未来宜内嵌于 Gateway / Policy，而非新增 primary slot |
| **Sandbox** | **已部分落地**：存在 `safety/sandbox_validator.py` 与 `sandbox_tiers.py` 的分层/门控抽象，但尚非完整容器/微虚机执行平台 | 作为 Executor / ToolHub 的运行时依赖边界 |
| **Browser** | **未作为独立实现落地** | 未来宜作为 ToolHub 的工具类别或 Executor 的外部调用目标 |

### 元层组件

| 组件 | 职责 |
|---|---|
| **Optimizer** | 位于九大核心组件之上，驱动自我重长循环；集成搜索与优化模块；自身不参与任务执行 |

## 1.4 统一术语基线

为与后续章节保持一致，本书使用以下术语：

| 术语 | 含义 |
|---|---|
| **slots** | 组件位点，如 `planner.primary`、`memory.primary`，定义组件在图中的可绑定位置 |
| **contracts** | 输入/输出/Event 的显式契约，静态校验与动态路由的基础 |
| **capabilities** | 组件提供或依赖的能力词汇，用于剪枝与兼容性判定 |
| **pending mutations** | 待提交的变更草案，Optimizer 的提议先进入此状态 |
| **candidate graph** | 经校验但未提交的组件图，是优化搜索的中间产物 |
| **active graph version** | 当前正在运行的组件图版本号，单调递增 |
| **rollback target** | 回滚时恢复的目标版本，保留窗口内的最近稳定版本 |
| **staged lifecycle** | 组件从发现到激活的多阶段生命周期：`DISCOVERED` → `VALIDATED_STATIC` → `ASSEMBLED` → `VALIDATED_DYNAMIC` → `ACTIVATED` → `COMMITTED` / `FAILED` / `SUSPENDED` |
| **protected components** | 不可被 Optimizer 直接替换的组件位点，如 `policy.primary`、关键收敛判据组件 |

## 1.5 与 Aeloon Plugin SDK 的关系

Meta-Harness Component SDK 借鉴了 Aeloon Plugin SDK 的成熟模式，但面向组件图而非命令/工具：

| Aeloon Plugin SDK | Meta-Harness Component SDK |
|---|---|
| `Plugin` 基类 | `HarnessComponent` 基类 |
| `aeloon.plugin.json` | `harness.component.json` |
| `PluginAPI.register_command()` | `HarnessAPI.declare_input/output/event()` |
| `PluginRegistry` | `ComponentRegistry`（含兼容性校验） |
| `PluginManager.boot()` | `HarnessRuntime.boot()` |
| `PluginRuntime` | `ComponentRuntime` |
| `HookDispatcher` (GUARD) | `PolicyLayer`（宪法否决） |
| `ServiceSupervisor` | `SandboxOrchestrator` |
| `PluginDiscovery`（4源） | `ComponentDiscovery`（bundled/template/market） |

关键差异：
- **注册粒度**：Aeloon 注册命令/工具/服务；Meta-Harness 注册 Input/Output/Event 端口
- **组件通信**：Aeloon 通过 AgentLoop 间接；Meta-Harness 通过 ConnectionEngine 直连
- **生命周期**：Aeloon 加载即激活；Meta-Harness 走 staged lifecycle（发现 → 校验 → 候选装配 → 动态验证 → 激活 → 提交）
- **热加载**：Aeloon 不支持；Meta-Harness 有 Suspend-Transform-Resume 协议
- **安全模型**：Aeloon 用 GUARD hooks 拦截工具调用；Meta-Harness 用四级安全链路拦截组件配置变更
- **图版本**：Aeloon 无图版本概念；Meta-Harness 所有改动进入 `candidate graph`，提交后生成新的 `graph version`

## 1.6 设计原则

1. **接口先行**：每个组件必须通过 `declare_interface()` 显式声明端口，由兼容性校验器静态检查
2. **契约优先**：组件间只通过声明过的 contracts 通信，ConnectionEngine 负责验证连接合法性
3. **受保护组件**：Policy / Governance 的关键位点、收敛判据组件不可被 Optimizer 独立修改
4. **候选图优先**：一切改动先进入 `pending mutations`，经校验后再切换 `active graph version`
5. **进化搜索优先**：Optimizer 以进化搜索和贝叶斯优化为主，RL 为可选增强
6. **安全前置**：沙箱与 A/B 测试基础设施是所有优化工作的前提
7. **轨迹即证据**：审计记录、Merkle 锚定与 PROV 谱系已落地；更完整的统一 trace / replay / crash recovery 产品面仍在持续实现
