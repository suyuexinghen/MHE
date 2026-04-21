# 03. 核心组件实现

本章说明 Meta-Harness 的 **9 core components + Optimizer** 应如何工程化实现。重点不是给出唯一实现，而是定义每个组件的**responsibilities、interfaces/ports、default implementations、combination rules、protected components、slot system、capability vocabulary、ConnectionEngine 通信模型、component directory layout**。

为避免术语漂移，本文统一使用：

- **9 core components**：九个运行期核心组件位点
- **Optimizer**：元层优化器，不属于 9 core components 内部数据平面
- **slot/capability system**：位点约束与能力匹配系统
- **staged lifecycle**：发现、校验、候选装配、激活、提交、回滚
- **contracts**：输入/输出/事件契约
- **pending mutations**：待提交变更
- **graph versions**：候选图、活动图、回滚图的版本体系

## 1. 组件全景

建议将 Meta-Harness 的 9 个核心位点固定为：

| # | 组件 | 主 slot | 核心作用 |
|---|---|---|---|
| 1 | Gateway | `gateway.primary` | 接入外部请求与上下文入口 |
| 2 | Runtime / Orchestrator | `runtime.primary` | 编排任务轮次、生命周期、调度 |
| 3 | Memory | `memory.primary` | 状态、历史、检索、快照 |
| 4 | ToolHub | `toolhub.primary` | 工具目录、权限、调用包装 |
| 5 | Planner / Reasoner | `planner.primary` | 规划、分解、推理路径生成 |
| 6 | Executor | `executor.primary` | 执行动作、调用工具/服务/子流程 |
| 7 | Evaluation | `evaluation.primary` | 质量、成本、延迟、多目标评估 |
| 8 | Observability | `observability.primary` | traces、metrics、audit、evidence |
| 9 | Policy / Governance | `policy.primary` | 安全、合规、veto、策略解释 |

`Optimizer` 是元层控制面：

| 组件 | slot | 说明 |
|---|---|---|
| Optimizer | `optimizer.meta` | 读取观测证据，生成 mutation proposal，不直接在数据面执行业务 |

### 身份、沙箱与浏览器

`Identity`、`Sandbox`、`Browser` 不作为独立核心组件，而是作为以下形式的扩展能力：

- **Identity**：作为 credential boundary 和 protected dependency，通常由 `Gateway` 或 `Runtime` 内部承载，或作为 `policy.primary` 的依赖能力。身份根实现必须标记为 protected。
- **Sandbox**：作为 `ToolHub` 或 `Executor` 的 execution environment extension。组件实现可以声明 `sandbox_level`（如 `standard`、`isolated`、`none`），但沙箱本身不是一个需要独立填充的 primary slot。
- **Browser**：作为 `ToolHub` 的 tool class 或 `Executor` 的外部调用目标。通过 `toolhub.execute` 或 `executor.tool_call` 调用，受 Policy 的速率/范围限制。

```text
┌─────────────────────────────────────────────────────────┐
│ 元层（Meta Layer）                                       │
│   Optimizer — 驱动自我重长循环，不参与任务执行             │
├─────────────────────────────────────────────────────────┤
│ 核心组件（Core Components）× 9                           │
│   Gateway / Runtime / Memory / ToolHub / Planner        │
│   Executor / Evaluation / Observability / Policy        │
│   每个组件可通过 Component SDK 独立实现和替换             │
├─────────────────────────────────────────────────────────┤
│ 扩展能力（Extension Capabilities）                       │
│   Identity — credential boundary (protected)            │
│   Sandbox  — execution environment (ToolHub/Executor)   │
│   Browser  — web access tool (ToolHub/Executor)         │
├─────────────────────────────────────────────────────────┤
│ 模板组件（Template Components）                          │
│   BM25Retriever / ContextPruner / ChainOfThoughtPlanner │
│   RetryWithBackoff / LoopGuard / SemanticValidator ...  │
│   由模板库提供，Optimizer 可按需实例化                    │
└─────────────────────────────────────────────────────────┘
```

## 2. 组合原则

### 2.1 默认组合

> **实现对齐说明（当前 MHE）**：当前仓库里的最小可运行拓扑更接近 `Gateway -> Runtime -> Executor -> Evaluation`，`Planner / Memory / Policy / Observability / ToolHub` 已有组件与契约骨架，但默认 demo 只覆盖其中一部分。`HarnessRuntime` 负责 discovery、static validation、dependency ordering、registry registration，随后再由 `ConnectionEngine` 对指定 `PendingConnectionSet` 做 stage/commit。

当前最小可运行系统通常是：

```text
Gateway -> Runtime -> Executor -> Evaluation
```

扩展示例拓扑可以再接入：

```text
Gateway -> Planner -> Runtime -> Executor -> Evaluation
                   |                    |
                   +--> Memory          +--> Observability
                                  \n                                   +--> Policy / ToolHub
```

### 2.2 组合规则

| 规则 | 说明 |
|---|---|
| 每个 primary slot 默认只允许 1 个 active binding | 避免控制面歧义 |
| 辅助 slot 可以多实例 | 如多个 memory index、多个 policy hook |
| 组件只通过 contracts 通信 | 禁止直接持有他组件实例引用 |
| 任何重绑定先生成 candidate graph | 禁止直接改 active graph |
| protected components 不能被 Optimizer 直接替换 | 需走人工审查或更高安全级流程 |
| 组件内聚约束 | 单个组件应保持清晰职责边界，不将 identity、governance、runtime、tool execution 混成单体 |

### 2.3 protected components

建议默认把以下组件或子能力标记为 `protected: true`：

| 组件/能力 | 原因 |
|---|---|
| `policy.primary` | 它决定哪些变更被允许 |
| 身份根实现（`gateway.primary` 或 `runtime.primary` 中的身份模块） | 它决定主体与授权语义 |
| `evaluation.primary` 的 loop guard 子能力 | 它决定系统何时回滚或停止优化 |

如果本版架构把身份能力并入 `gateway.primary` 或 `runtime.primary`，则相应的身份根实现也应进入 protected set。

## 3. 统一接口模式

所有核心组件都遵循同一模式：

```python
class HarnessComponent(ABC):
    def declare_interface(self, api: HarnessAPI) -> None: ...
    async def activate(self, runtime: ComponentRuntime) -> None: ...
    async def deactivate(self) -> None: ...
```

但每类组件会暴露不同的 ports 和 capabilities。

### 3.1 ports 约定

| 类型 | 作用 | 例子 |
|---|---|---|
| input port | 接收上游数据 | `task_request`, `plan_request` |
| output port | 向下游发送数据 | `plan_result`, `tool_result` |
| event port | 广播事件 | `on_policy_violation`, `on_converged` |

### 3.2 capability 命名约定

统一使用 `domain.verb[.qualifier]`：

- `memory.read`
- `memory.write`
- `planner.decompose`
- `executor.tool_call`
- `evaluation.score`
- `policy.veto`
- `observability.trace.write`

这样 capability 可以直接作为装配器的匹配键和值班表键。

## 4. Gateway

Gateway 负责把"外部世界"映射成 Meta-Harness 的标准任务对象。

### 4.1 职责

- 接收用户请求、系统事件、批任务触发
- 建立 request/session/context 根对象
- 做输入标准化与协议解码
- 触发 Runtime / Orchestrator 开始一轮执行
- 凭证挂载与剥离（身份边界由 Gateway 封装，底层凭证管理不对外暴露）

### 4.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `external_request: ExternalRequest@v1` |
| output | `task_request: TaskRequest@v1` |
| events | `on_session_started`, `on_session_closed` |
| provides | `gateway.ingest`, `gateway.session.open` |
| requires | `policy.pre_ingest`, `observability.trace.write` |

### 4.3 默认实现

| 实现 | 说明 |
|---|---|
| `DefaultGateway` | HTTP/CLI 统一入口，最小会话模型 |
| `InteractiveGateway` | 面向多轮交互，带 session keepalive |
| `BatchGateway` | 面向任务队列、回放和离线评测 |

### 4.4 接口代码示例

```python
class GatewayComponent(HarnessComponent):
    component_type = ComponentType.CORE
    protected = False

    def declare_interface(self, api: HarnessAPI) -> None:
        api.declare_input(
            "raw_request", "HTTPRequest", required=False,
            description="Incoming HTTP/WebSocket/CLI request",
        )
        api.declare_input(
            "agent_message", "AgentMessage", required=False,
            description="Inter-agent communication message",
        )
        api.declare_output(
            "command", "Command",
            description="Normalized internal command",
        )
        api.declare_output(
            "dispatched_response", "DispatchedResponse",
            description="Response after credential stripping",
        )
        api.declare_event("on_request_received", payload_type="RequestMeta")
        api.declare_event("on_protocol_error", payload_type="ErrorInfo")
```

### 4.5 凭证与身份边界

核心原则仍然成立：**身份根与凭证边界应位于 Gateway / Policy 外围，而不暴露给优化器或普通组件。**

但需要明确：**当前 MHE 代码尚未实现独立 Identity 组件或完整凭证剥离流水线**。这一段应视为后续实现目标，而不是已完成行为。当前代码层面，Gateway 组件主要承担输入归一化与任务载荷转发。`

## 5. Runtime / Orchestrator

Runtime / Orchestrator 是图执行的主调度器。

### 5.1 职责

当前实现需要区分两个层次：

- **`RuntimeComponent`**：最小运行时组件，只声明 `runtime.primary` slot、接收 `task`、输出 `result`
- **`HarnessRuntime`**：真正的启动编排器，负责 discovery、static validation、dependency resolution、registration、graph staging/commit

因此当前已实现的职责包括：
- 通过 `HarnessRuntime` 运行 discovery → validation → registration → commit pipeline
- 通过 `ConnectionEngine` 在已提交图上执行端口路由
- 通过最小 `RuntimeComponent` 参与 demo 主链

而超时/重试/并发窗口/完整任务轮次协调仍属于后续扩展目标。

### 5.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `task_request: TaskRequest@v1` |
| output | `execution_envelope: ExecutionEnvelope@v1` |
| events | `on_turn_started`, `on_turn_completed`, `on_turn_failed` |
| provides | `runtime.schedule`, `runtime.turn.execute`, `runtime.lifecycle.coordinate` |
| requires | `planner.decompose`, `executor.act`, `evaluation.score` |

### 5.3 默认实现

| 实现 | 说明 |
|---|---|
| `SingleTurnRuntime` | 单轮任务执行 |
| `IterativeRuntime` | 支持多步规划-执行-评估循环 |
| `CheckpointRuntime` | 增加 checkpoint 与恢复能力 |

### 5.4 接口代码示例

```python
class RuntimeComponent(HarnessComponent):
    component_type = ComponentType.CORE
    protected = False

    def declare_interface(self, api: HarnessAPI) -> None:
        api.declare_input("command", "Command", required=True,
                          description="Parsed LLM instruction to execute")
        api.declare_input("candidate_config", "CandidateConfig", required=False,
                          description="New configuration from Optimizer for hot-reload")
        api.declare_input("approved_config", "ApprovedConfig", required=False,
                          description="Configuration approved by Policy for commit")
        api.declare_input("execution_result", "ExecutionResult", required=False,
                          description="Result from sandbox or component execution")
        api.declare_output("action", "Action",
                           description="Executable action derived from command")
        api.declare_output("post_processed_result", "ProcessedResult",
                           description="Result after truncation, summarization, reformatting")
        api.declare_output("sandbox_request", "SandboxRequest",
                           description="Request to execute code in isolated sandbox")
        api.declare_output("hot_reload_signal", "HotReloadSignal",
                           description="Signal to trigger hot-reload of component graph")
        api.declare_event("on_config_reload", payload_type="ConfigSnapshot")
        api.declare_event("on_execution_timeout")
        api.declare_event("on_rollback", payload_type="RollbackInfo")
        api.declare_event("on_recovery", payload_type="RecoveryContext")
```

## 6. Memory

Memory 是状态与可恢复性的核心。

### 6.1 职责

- 保存短期状态、长期记忆、检索索引
- 提供 checkpoint 与 state snapshot
- 为 graph versions 和 rollback 提供状态支撑
- 为 Planner / Evaluation 提供历史依据
- 执行轨迹全量持久化

### 6.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `memory_query: MemoryQuery@v1`, `memory_write: MemoryWrite@v1` |
| output | `memory_result: MemoryResult@v1`, `state_snapshot: StateSnapshot@v1` |
| events | `on_snapshot_created`, `on_state_restored` |
| provides | `memory.read`, `memory.write`, `memory.snapshot`, `memory.restore` |
| requires | `observability.audit.write` |

### 6.3 默认实现

| 实现 | 说明 |
|---|---|
| `JsonlMemory` | 最小实现，适合原型和可审计场景 |
| `VectorMemory` | 面向语义检索 |
| `HybridMemory` | 结构化状态 + 向量检索混合 |

### 6.4 上下文管理策略

Memory 的上下文管理支持三种策略（可组合使用）：

```text
策略1: Sliding Window（滑动窗口）
  [新消息] [消息N-1] [消息N-2] ... [消息N-W]  ← 保留最近 W 条
  参数: window_size (默认: 10 轮)

策略2: Summarization（自动摘要）
  [摘要: 前 K 轮对话要点]
  [最近 W 轮完整消息]
  参数: summary_trigger_threshold (默认: 0.8 上下文占比)

策略3: Relevance Filtering（相关性过滤）
  [当前查询] -> 计算相似度 -> 保留 Top-K 相关
  [系统提示] (永久保留)
  [相关历史片段] (按相似度排序)
  参数: relevance_cutoff (默认: 0.5), top_k

组合模式: hybrid = sliding_window + summarization
         当窗口满时触发摘要，保留摘要+最近消息
```

### 6.5 执行轨迹存储

| 层级 | 存储 | 保留期 | 用途 |
|------|------|--------|------|
| 热数据 | Redis / 本地 SSD | 最近 H 小时 | Optimizer 快速检索 |
| 温数据 | PostgreSQL / SQLite | 最近 30 天 | 反事实诊断、趋势分析 |
| 冷数据 | S3 / MinIO | 永久 | 长期审计、Merkle 链 |

### 6.6 反事实诊断接口

```python
async def get_failed_traces(self, component: str, limit: int) -> list[Trace]:
    """获取指定组件最近 N 条失败轨迹。"""

async def compare_traces(self, config_a: str, config_b: str, task_id: str) -> TraceDiff:
    """对比同一任务在两个配置下的执行差异。"""

async def search_traces(self, keyword: str, time_range: TimeRange) -> list[Trace]:
    """基于关键词和时间范围检索轨迹片段。"""

async def replay_trace(self, execution_id: str, from_step: int = 0) -> ReplayResult:
    """从指定步骤开始重放执行。"""
```

## 7. ToolHub

ToolHub 是"工具平面"的统一门面。

### 7.1 职责

- 注册工具定义、schema、权限标签
- 包装同步/异步工具调用
- 对接 Policy 做 pre-call / post-call 检查
- 把工具调用转成标准 contract
- 封装 sandbox 执行环境（代码执行、浏览器访问均通过 ToolHub 统一入口）

### 7.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `tool_request: ToolRequest@v1` |
| output | `tool_result: ToolResult@v1` |
| events | `on_tool_called`, `on_tool_failed` |
| provides | `toolhub.catalog.read`, `toolhub.execute`, `toolhub.schema.resolve` |
| requires | `policy.tool.guard`, `observability.trace.write` |

### 7.3 默认实现

| 实现 | 说明 |
|---|---|
| `LocalToolHub` | 本地工具目录 + 直接调用 |
| `SandboxedToolHub` | 默认走 sandbox client |
| `RemoteToolHub` | 把工具执行代理到外部执行器 |

### 7.4 沙箱策略

ToolHub 封装 sandbox 执行时，应统一应用以下资源约束：

```xml
<Sandbox
    timeout_sec="60"
    max_memory_mb="512"
    max_cpu_percent="80"
    network_policy="isolated"
    allowed_languages="python,javascript"
    max_output_bytes="1048576"
    mount_readonly="true"
/>
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `timeout_sec` | 60 | 单次执行超时 |
| `max_memory_mb` | 512 | 内存上限 |
| `max_cpu_percent` | 80 | CPU 配额 |
| `network_policy` | `isolated` | 网络策略（isolated / whitelist / open） |
| `allowed_languages` | `python` | 允许的执行语言 |
| `max_output_bytes` | 1048576 (1MB) | 输出截断阈值 |
| `mount_readonly` | `true` | 候选配置挂载为只读 |

## 8. Planner / Reasoner

Planner / Reasoner 负责把任务转成可执行计划。

### 8.1 职责

- 任务分解、依赖分析、路径选择
- 生成 step graph / action list / search plan
- 声明需要的工具、知识、预算和风险标签

### 8.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `plan_request: PlanRequest@v1` |
| output | `plan_package: PlanPackage@v1` |
| events | `on_plan_generated`, `on_replan_requested` |
| provides | `planner.decompose`, `planner.replan`, `planner.estimate_risk` |
| requires | `memory.read`, `policy.plan.guard` |

### 8.3 默认实现

| 实现 | 说明 |
|---|---|
| `RulePlanner` | 基于规则与模板 |
| `LLMPlanner` | 依赖模型推理 |
| `HybridPlanner` | 规则先行，LLM 补全 |

### 8.4 组合规则

- `planner.primary` 只保留一个主决策器
- 可以叠加 `planner.critic.secondary` 做 plan review
- 如果开启 Optimizer，Planner 应暴露稳定的 `PlanPackage` contract，避免优化层直接耦合内部推理状态

## 9. Executor

Executor 负责把计划转成动作执行结果。

### 9.1 职责

- 解释 `PlanPackage`
- 调用 ToolHub、子流程、远程服务
- 汇聚执行结果与失败原因
- 在运行时支持 retry / fallback / cancellation

### 9.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `plan_package: PlanPackage@v1` |
| output | `execution_result: ExecutionResult@v1` |
| events | `on_action_started`, `on_action_completed`, `on_action_failed` |
| provides | `executor.act`, `executor.tool_call`, `executor.rollback_safe` |
| requires | `toolhub.execute`, `policy.action.guard`, `observability.trace.write` |

### 9.3 默认实现

| 实现 | 说明 |
|---|---|
| `DirectExecutor` | 顺序执行动作 |
| `DAGExecutor` | 支持可并行 step graph |
| `GuardedExecutor` | 强化策略检查和沙箱执行 |

## 10. Evaluation

Evaluation 是系统自我判断与收敛控制的核心。

### 10.1 职责

- 对执行结果输出质量向量
- 计算 latency / cost / safety / success 等指标
- 产出 loop guard signal 和 mutation feedback
- 为 rollback 和 Optimizer 提供证据

### 10.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `execution_result: ExecutionResult@v1` |
| output | `performance_vector: PerformanceVector@v1`, `loop_guard_signal: LoopGuardSignal@v1` |
| events | `on_bottleneck_detected`, `on_converged`, `on_degradation_detected` |
| provides | `evaluation.score`, `evaluation.compare`, `evaluation.loop_guard` |
| requires | `memory.read`, `observability.trace.read` |

### 10.3 默认实现

| 实现 | 说明 |
|---|---|
| `DefaultEvaluation` | 延迟/成本/成功率三目标 |
| `ResearchEvaluation` | 多维实验指标 |
| `SafeEvaluation` | 额外强化风险与合规指标 |

### 10.4 protected 规则

如果 `evaluation.loop_guard` 是系统停止条件的核心来源，则其默认实现或其 guard 子模块应被标记为 protected。

> **实现对齐说明（当前 MHE）**：`EvaluationComponent` 目前是最小组件，输出简单 `PerformanceVector` 风格载荷；真正的 loop/fitness/convergence 逻辑主要在 `optimizer/fitness.py` 与 `optimizer/convergence.py`，尚未完全并入 `evaluation.primary` 的单一运行时组件中。

### 10.5 性能向量计算

```python
@dataclass
class PerformanceVector:
    """多维性能向量。"""
    accuracy: float      # P_acc: 准确率 / F1 / BERTScore
    latency: float       # P_lat: 端到端响应时间（秒）
    resource: float      # P_res: GPU 显存峰值（MB）或 CPU 占用（%）
    context_cost: float  # P_ctx: 上下文 Token 总数

    def to_tuple(self) -> tuple[float, float, float, float]:
        return (self.accuracy, self.latency, self.resource, self.context_cost)
```

### 10.6 LoopGuard 子模块

```python
class LoopGuard:
    """死循环检测与无效策略终止。"""

    def __init__(self, config: LoopGuardConfig) -> None:
        self.max_steps = config.max_steps
        self.max_tokens = config.max_tokens
        self.max_runtime_seconds = config.max_runtime
        self.similarity_threshold = config.sim_threshold
        self.stagnation_window = config.stagnation_window

    async def check(self, execution: ExecutionTrace) -> QualityControlSignal | None:
        # 1. 步数上限检查
        if execution.step_count >= self.max_steps:
            return QualityControlSignal(
                type="hard_limit",
                message=f"Step limit exceeded: {execution.step_count} >= {self.max_steps}",
                action="abort",
            )
        # 2. Token 消耗上限检查
        if execution.total_tokens >= self.max_tokens:
            return QualityControlSignal(type="hard_limit", message="Token budget exhausted", action="abort")
        # 3. 重复输出检测
        if self._detect_repetition(execution.recent_outputs):
            return QualityControlSignal(type="loop", message="Repetitive outputs detected", action="abort")
        # 4. 停滞检测
        if self._detect_stagnation(execution.progress_history):
            return QualityControlSignal(type="stagnation", message="No progress in recent steps", action="escalate")
        return None
```

## 11. Observability

Observability 为系统提供可见性与审计证据。

### 11.1 职责

- 记录 traces、metrics、logs、artifacts
- 建立 evidence chain 与回放材料
- 为 graph versions 记录激活、切换、回滚证据
- 支撑 shadow validation 与 postmortem

### 11.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `trace_event: TraceEvent@v1`, `audit_record: AuditRecord@v1` |
| output | `evidence_record: EvidenceRecord@v1` |
| events | `on_trace_flushed`, `on_evidence_recorded` |
| provides | `observability.trace.write`, `observability.trace.read`, `observability.audit.write`, `observability.evidence.query` |
| requires | 无或仅依赖底层存储能力 |

### 11.3 默认实现

| 实现 | 说明 |
|---|---|
| `LocalObservability` | 本地文件/JSONL |
| `StructuredObservability` | 结构化 trace + metrics |
| `EvidenceChainObservability` | 面向审计与可追溯性 |

### 11.4 观测数据层次

```text
Layer 1: System Metrics (系统层)
  ├── CPU 使用率 (%)
  ├── GPU 显存占用 (MB)
  ├── 网络 I/O (bytes/sec)
  └── 容器资源限额使用率 (%)

Layer 2: Component Metrics (组件层)
  ├── 每组件调用次数 (count)
  ├── 每组件执行耗时 (ms, P50/P95/P99)
  ├── 输入/输出数据量 (bytes)
  └── 异常发生频率与类型分布

Layer 3: Task Trace (任务层)
  ├── 端到端执行时间线
  ├── 每步输入/输出快照
  ├── 工具调用记录与结果
  └── LLM 响应文本与 Token 统计

Layer 4: Data Flow (数据流层)
  ├── 组件间数据流转快照
  ├── Connection 吞吐量
  └── Event 分发延迟
```

## 12. Policy / Governance

Policy / Governance 是控制面中最关键的 protected 组件。

### 12.1 职责

- 对 plan、tool call、mutation proposal、graph commit 做 guard
- 提供 allow / deny / mutate / reduce 决策语义
- 维护权限模型、风险分级、安全策略

### 12.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `policy_query: PolicyQuery@v1`, `mutation_proposal: MutationProposal@v1` |
| output | `policy_decision: PolicyDecision@v1` |
| events | `on_policy_violation`, `on_veto`, `on_policy_reload` |
| provides | `policy.plan.guard`, `policy.tool.guard`, `policy.mutation.guard`, `policy.veto` |
| requires | `observability.audit.write`, `identity.attest` 或等价身份根能力 |

### 12.3 默认实现

| 实现 | 说明 |
|---|---|
| `RulePolicy` | 静态规则 + deny list |
| `ConstitutionalPolicy` | 宪法式多层约束 |
| `HumanReviewPolicy` | 关键路径需人工批准 |

### 12.4 protected 规则

- `policy.primary` 默认必须是 protected
- 替换 `policy.primary` 必须走人工审查或高信任签名流程
- `Optimizer` 不能直接提交覆盖 `policy.primary` 的自动变更

### 12.5 宪法层不变量

```python
CONSTITUTIONAL_INVARIANTS = [
    InvariantRule(
        id="identity_protection",
        description="Identity root capability must never be removed or disabled",
        check=lambda mutation: not (
            mutation.type == "remove_component"
            and mutation.target.startswith("metaharness.identity")
        ),
    ),
    InvariantRule(
        id="network_isolation",
        description="Unrestricted external network access is forbidden",
        check=lambda mutation: not (
            mutation.type == "modify_param"
            and mutation.param == "network_policy"
            and mutation.new_value == "open"
        ),
    ),
    InvariantRule(
        id="policy_self_protection",
        description="Policy component cannot modify its own configuration",
        check=lambda mutation: not (
            mutation.target.startswith("metaharness.policy")
            and mutation.source == "optimizer"
        ),
    ),
    InvariantRule(
        id="dangerous_code_filter",
        description="Code containing execve, fork bombs, or similar patterns is forbidden",
        check=lambda mutation: not (
            mutation.type == "code_generation"
            and contains_dangerous_pattern(mutation.generated_code)
        ),
    ),
    InvariantRule(
        id="complexity_cap",
        description="Total component count must not exceed N_max",
        check=lambda mutation: (
            mutation.type != "add_component"
            or get_total_component_count() + 1 <= COMPLEXITY_CAP
        ),
    ),
]
```

## 13. Optimizer

Optimizer 不在 9 core components 主数据面中，但必须作为一等组件定义清楚。

### 13.1 职责

- 读取 Evaluation、Observability、Memory 的证据
- 生成 `mutation proposal`
- 选择候选组件、slot rebinding、config patch、migration recipe
- 提交到 pending mutations，而不是直接写 active graph

### 13.2 ports 与 capabilities

| 项目 | 定义 |
|---|---|
| input | `optimization_signal: OptimizationSignal@v1`, `performance_vector: PerformanceVector@v1` |
| output | `mutation_proposal: MutationProposal@v1` |
| events | `on_candidate_selected`, `on_mutation_submitted`, `on_rollback_recommended` |
| provides | `optimizer.propose`, `optimizer.select`, `optimizer.rollback_recommend` |
| requires | `evaluation.compare`, `observability.evidence.query`, `policy.mutation.guard` |

### 13.3 约束

- 不直接调用 `ConnectionEngine.commit_graph()`
- 不直接修改 protected components
- 所有 proposal 必须进入 pending mutations
- 所有候选装配必须生成新的 candidate graph version

## 14. interfaces/ports 总表

| 组件 | 关键输入 | 关键输出 | 关键事件 |
|---|---|---|---|
| Gateway | `ExternalRequest@v1` | `TaskRequest@v1` | `on_session_started` |
| Runtime | `TaskRequest@v1` | `ExecutionEnvelope@v1` | `on_turn_completed` |
| Memory | `MemoryQuery@v1` | `MemoryResult@v1` | `on_snapshot_created` |
| ToolHub | `ToolRequest@v1` | `ToolResult@v1` | `on_tool_called` |
| Planner | `PlanRequest@v1` | `PlanPackage@v1` | `on_replan_requested` |
| Executor | `PlanPackage@v1` | `ExecutionResult@v1` | `on_action_failed` |
| Evaluation | `ExecutionResult@v1` | `PerformanceVector@v1` | `on_degradation_detected` |
| Observability | `TraceEvent@v1` | `EvidenceRecord@v1` | `on_evidence_recorded` |
| Policy | `PolicyQuery@v1` | `PolicyDecision@v1` | `on_veto` |
| Optimizer | `OptimizationSignal@v1` | `MutationProposal@v1` | `on_mutation_submitted` |

## 15. slot system

slot system 决定"什么组件可以装到什么位置"。

### 15.1 主位点定义

| slot | 含义 | 是否多实例 | 默认 protected |
|---|---|---|---|
| `gateway.primary` | 输入入口 | 否 | 否 |
| `runtime.primary` | 主调度器 | 否 | 视身份根实现而定 |
| `memory.primary` | 主状态存储 | 否 | 否 |
| `toolhub.primary` | 主工具门面 | 否 | 否 |
| `planner.primary` | 主规划器 | 否 | 否 |
| `executor.primary` | 主执行器 | 否 | 否 |
| `evaluation.primary` | 主评估器 | 否 | 部分能力 protected |
| `observability.primary` | 主观测器 | 否 | 否 |
| `policy.primary` | 主治理器 | 否 | 是 |
| `optimizer.meta` | 元层优化器 | 否 | 否 |

### 15.2 扩展位点示例

| slot | 用途 |
|---|---|
| `memory.retrieval.secondary` | 辅助检索索引 |
| `planner.critic.secondary` | 计划审查器 |
| `policy.shadow.secondary` | 影子策略校验 |
| `observability.exporter.secondary` | 外部导出器 |

## 16. capability vocabulary

建议先冻结一个最小 capability 词表，供 manifest 和装配器共用。

### 16.1 基础词表

| 域 | capabilities |
|---|---|
| gateway | `gateway.ingest`, `gateway.session.open` |
| runtime | `runtime.schedule`, `runtime.turn.execute`, `runtime.lifecycle.coordinate` |
| memory | `memory.read`, `memory.write`, `memory.snapshot`, `memory.restore` |
| toolhub | `toolhub.catalog.read`, `toolhub.execute`, `toolhub.schema.resolve` |
| planner | `planner.decompose`, `planner.replan`, `planner.estimate_risk` |
| executor | `executor.act`, `executor.tool_call`, `executor.rollback_safe` |
| evaluation | `evaluation.score`, `evaluation.compare`, `evaluation.loop_guard` |
| observability | `observability.trace.write`, `observability.trace.read`, `observability.audit.write`, `observability.evidence.query` |
| policy | `policy.plan.guard`, `policy.tool.guard`, `policy.mutation.guard`, `policy.veto` |
| optimizer | `optimizer.propose`, `optimizer.select`, `optimizer.rollback_recommend` |

### 16.2 capability 匹配规则

- slot 匹配先于 capability 匹配
- capability 是装配条件，不等于组件类型
- 一个组件可以提供多个 capability
- 如果一个 required capability 存在多个 provider，必须由装配器确定优先级或路由规则

## 17. ConnectionEngine：组件通信与图调度

ConnectionEngine 是主数据面的连接器，负责根据 contracts 和 graph bindings 进行通信。

### 17.1 职责

- 保存 active graph version 的连接表
- 将 output port 路由到一个或多个 input port
- 检查 contract compatibility
- 支持 event broadcast、direct send、request/reply 三种模式
- 在 graph cutover 时切换路由表

### 17.2 通信模式

| 模式 | 说明 | 例子 |
|---|---|---|
| direct port | 一对一或一对多路由 | `Planner.plan_package -> Executor.plan_package` |
| event broadcast | 发布到订阅方 | `Evaluation.on_degradation_detected` |
| guarded request | 发出前经 Policy 检查 | `Executor -> ToolHub.execute` |

### 17.3 文本图示

```text
[Gateway.task_request]
        |
        v
[Runtime.task_request] ----> [Planner.plan_request]
        |                           |
        |                           v
        |                     [Planner.plan_package]
        |                           |
        v                           v
[Executor.plan_package] ----> [ToolHub.tool_request]
        |
        v
[Evaluation.execution_result] ----> [Optimizer.optimization_signal]
        |
        +----> [Observability.trace_event]
        +----> [Policy.policy_query]
```

### 17.4 graph versions 与切换

ConnectionEngine 不直接修改现有路由，而是：

1. 读取 `candidate graph version`
2. 在隔离环境中建立新路由表
3. 等新组件进入可服务状态
4. 原子切换 `active graph version`
5. 保留旧路由表作为 rollback target

## 18. default implementations 与组合模板

为了让系统可落地，建议先提供一套默认组合模板。

### 18.1 baseline 模板

| slot | 默认实现 |
|---|---|
| `gateway.primary` | `DefaultGateway` |
| `runtime.primary` | `IterativeRuntime` |
| `memory.primary` | `JsonlMemory` |
| `toolhub.primary` | `SandboxedToolHub` |
| `planner.primary` | `HybridPlanner` |
| `executor.primary` | `GuardedExecutor` |
| `evaluation.primary` | `DefaultEvaluation` |
| `observability.primary` | `StructuredObservability` |
| `policy.primary` | `ConstitutionalPolicy` |
| `optimizer.meta` | `BaselineOptimizer` |

### 18.2 research 模板

- Planner、Evaluation、Optimizer 允许更快替换
- Policy 保持固定或仅允许影子模式
- Memory 保留兼容 snapshot contract

### 18.3 safe 模板

- ToolHub 强制 sandbox
- Policy 与 Evaluation guard 全部 protected
- graph cutover 只允许人工审批后执行

## 19. component directory layout

> **实现对齐说明（当前 MHE）**：当前仓库采用更扁平的实现：`components/*.py`、`optimizer/*`、`hotreload/*`、`provenance/*`、`safety/*`。下面的分层目录更接近目标演化方向，而非当前精确树形结构。

建议按"SDK / Core / Components / Governance / Templates"组织目录。

```text
metaharness/
├── sdk/
│   ├── base.py
│   ├── api.py
│   ├── runtime.py
│   ├── manifest.py
│   ├── registry.py
│   ├── discovery.py
│   ├── loader.py
│   └── contracts.py
├── core/
│   ├── harness_runtime.py
│   ├── connection_engine.py
│   ├── graph_versions.py
│   └── mutation_manager.py
├── components/
│   ├── gateway/
│   │   ├── default/
│   │   └── interactive/
│   ├── runtime/
│   ├── memory/
│   ├── toolhub/
│   ├── planner/
│   ├── executor/
│   ├── evaluation/
│   ├── observability/
│   └── policy/
├── optimizer/
│   ├── baseline/
│   ├── selector/
│   └── rollback/
└── manifests/
    ├── baseline/
    ├── research/
    └── safe/
```

### 19.1 单个组件包布局

```text
components/planner/hybrid/
├── metaharness.component.json
├── __init__.py
├── component.py
├── contracts.py
├── config.py
├── services.py
└── migrations/
```

其中：

| 文件 | 作用 |
|---|---|
| `metaharness.component.json` | 身份、slots、capabilities、contracts |
| `component.py` | `HarnessComponent` 实现 |
| `contracts.py` | payload schema 常量/适配器 |
| `config.py` | 组件配置 schema |
| `services.py` | 长生命周期后台任务 |
| `migrations/` | state schema 迁移器 |

## 20. 实施顺序建议

为了先把系统跑起来，建议按以下顺序做默认实现：

1. `Runtime / Orchestrator`、`Memory`、`Evaluation`
2. `Policy / Governance`、`Observability`
3. `Planner`、`Executor`、`ToolHub`
4. `Gateway`
5. `Optimizer`

原因是：

- Runtime 决定生命周期骨架
- Memory / Evaluation 决定 state 与回滚基础
- Policy / Observability 决定系统是否可控、可证据化
- Optimizer 应该最后接入，避免一开始就让系统改动自身结构

## 21. 设计约束总结

在实现和扩展 9 core components 时，必须遵守以下设计约束：

### 21.1 组件内聚约束

单个组件必须保持清晰职责边界。禁止将 identity 校验、governance 策略、runtime 调度、tool execution 混成单体叙事。Identity 能力应作为 Gateway/Runtime 的边界职责或 Policy 的依赖；Sandbox 和 Browser 作为 ToolHub/Executor 的扩展环境，不独立占据 primary slot。

### 21.2 可解释性预算

每章引入的新术语或新控制机制，必须控制在读者可追踪的范围内。新术语必须能映射到已有章节对象、流程或接口。 Capability 词表建议先冻结最小集合，再按需扩展。

### 21.3 连接健康与孤儿组件检查

任何 component taxonomy 或 extension guide 改写，不得削弱"组件存在但未被 graph 正确装配/路由"的风险表达。ConnectionEngine 必须持续检查 connection health，检测孤儿组件（声明了 ports 但未被任何 Connection 引用）。

### 21.4 Token / 资源预算底线

在 Optimizer、Planner、Evaluation、Observability 等章节中，预算不只是优化目标，也是硬约束。文档中需保留 token budget floor / hard ceiling 的控制面语义。LoopGuard 的 `max_tokens` 和 `max_runtime_seconds` 是底线，不是建议值。

### 21.5 Graph-version retirement / version rot 防护

Graph versions 不是无限累积资产。需要明确 retirement、archive、staleness、version rot prevention 的设计约束。建议：

- 保留最近 N 个 active versions（如 50）作为快速回滚目标
-  older versions 归档到冷存储，保留 Merkle 摘要
- 定期清理不可达版本，防止版本链无限增长
- 回滚目标（rollback target）应明确指向最近一个稳定版本，而非任意历史版本

## 22. 小结

9 core components 的本质不是"九个类"，而是**九个稳定 slot**。真正支撑可替换性的，是：

- 每个 slot 对应清晰的 responsibilities
- 统一的 ports/contracts/interfaces
- 冻结的 capability vocabulary
- ConnectionEngine 驱动的图级通信
- protected components、pending mutations、graph versions 共同构成的安全切换协议

在这个前提下，Optimizer 才能安全地对 Meta-Harness 做结构优化，而不会把系统退化成一堆难以回滚的临时拼装件。
