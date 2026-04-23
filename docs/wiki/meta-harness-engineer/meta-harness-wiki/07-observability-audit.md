# 07. 可观测性与审计

本章把 Meta-Harness 的 Observability 从"记录日志"提升为一套面向**全链路追踪、重放、崩溃恢复、证据对象、审计不可篡改、溯源查询、反事实诊断、Memory 联动**的工程系统。目标不是多打一层埋点，而是让每一个 `graph version`、每一次 `mutation proposal`、每一轮 `rollback` 都留下可计算、可查询、可验证的证据。

在自我增长系统中，可观测性不仅是运维工具，更是 Optimizer 进行反事实诊断的数据基础，以及审计自我修改历史的证据来源。Meta-Harness 的研究已经证明：保留原始执行轨迹的诊断式搜索比抽象摘要更有效（proposer 每轮中位数读取 82 个文件，其中约 41% 是旧代码，40% 是执行轨迹）。

为与前文保持一致，本文统一使用：

- **active graph version / candidate graph / rollback target**
- **pending mutations**
- **evidence object**
- **full-chain trace**
- **observation window**
- **Policy / Governance**、**ConnectionEngine**、**Optimizer**、**Memory**

---

## 7.1 观测目标与边界

Meta-Harness 的可观测性不是辅助功能，而是整个自增长闭环的基础设施。它至少要支持五类能力：

| 目标 | 说明 | 对应机制 |
| --- | --- | --- |
| 看见运行路径 | 知道请求如何穿过组件图 | full-chain trace |
| 解释版本差异 | 知道哪个 `graph version` 带来了变化 | graph-tagged metrics + evidence object |
| 重放与复现 | 能复盘某次 proposal、切流、回滚 | replay + snapshot references |
| 崩溃后恢复 | 能恢复执行上下文和审计连续性 | crash recovery + checkpoint references |
| 形成可审计资产 | 让每次自修改都有不可篡改证据链 | PROV-based evidence + Merkle audit log |

可观测性的边界也需要明确：

- Observability 不直接决定是否提交变更，但为治理和回滚提供证据
- `ConnectionEngine` 负责路由，Observability 负责记录路由事实
- `Optimizer` 消费观测证据，但不能篡改原始审计链
- `Memory` 可以索引和解释证据，但不应覆盖不可变审计记录

---

## 7.2 三层观测数据模型

为了同时兼顾实时调试、版本审计和长期学习，Meta-Harness 建议把观测数据分成三层。

> **实现对齐说明（当前 MHE）**：当前代码已经实做了审计日志、Merkle 锚定、PROV 图、查询接口与反事实诊断模块；但统一的 runtime telemetry、完整 full-chain trace、crash recovery pipeline 与冷热分层存储仍主要停留在架构设计层。

### 7.2.1 L1：运行时遥测层

L1 记录最细粒度的运行事实：

- span / trace
- metrics
- logs
- resource counters
- tool call envelope
- policy decision event

这一层面向实时监控和短周期诊断，要求低延迟、可流式写入。

### 7.2.2 L2：版本与生命周期层

L2 记录系统在图级别发生了什么：

- candidate graph 组装
- shadow validation 结果
- graph cutover
- observation window 结果
- rollback 触发与恢复目标

这一层把大量碎片化运行事实压缩成"版本事件"。

### 7.2.3 L3：证据与谱系层

L3 负责形成长期可审计资产：

- evidence object
- provenance graph
- Merkle audit chain
- human approval records
- dead-end memory references

这一层不是给实时 dashboard 用的，而是给**治理、追责、回放、研究分析**用的。

### 7.2.4 三层数据总表

| 层级 | 关注对象 | 保留周期 | 典型消费者 |
| --- | --- | --- | --- |
| L1 遥测层 | span、metric、log | 短到中期 | runtime monitor、shadow validator |
| L2 生命周期层 | graph version event、rollback、commit | 中到长期 | governance、postmortem、optimizer |
| L3 证据层 | provenance、audit、approval、Merkle proof | 长期 | audit、memory、forensics |

### 7.2.5 数据模型代码

```python
@dataclass
class SystemMetrics:
    """系统层指标数据模型（L1）。"""
    timestamp: datetime
    cpu_usage_percent: float
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float
    ram_used_mb: float
    ram_total_mb: float
    network_rx_bytes: int
    network_tx_bytes: int
    disk_read_bytes: int
    disk_write_bytes: int
    container_count: int
    container_cpu_quota: float
    container_memory_limit_mb: float
    sample_interval_sec: float = 1.0


@dataclass
class ComponentMetrics:
    """组件层指标数据模型（L1）。"""
    component_id: str
    component_type: str
    timestamp: datetime
    invocation_count: int
    success_count: int
    failure_count: int
    timeout_count: int
    avg_latency_ms: float
    p50_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    input_data_bytes: int
    output_data_bytes: int
    token_consumed: int
    last_error: str | None
    error_rate: float


@dataclass
class TaskTrace:
    """任务层轨迹数据模型（L1/L2）。"""
    trace_id: str
    task_id: str
    config_version: str
    graph_version: int
    start_time: datetime
    end_time: datetime | None
    steps: list[TraceStep]
    final_status: str
    error_message: str | None


@dataclass
class TraceStep:
    """单步执行记录。"""
    step_id: int
    component_id: str
    action: str
    input_snapshot: dict
    output_snapshot: dict
    start_time: datetime
    end_time: datetime
    token_used: int
    tool_calls: list[ToolCallRecord]
```

---

## 7.3 Full-Chain Trace：全链路追踪

Meta-Harness 的 trace 不能只记录"函数调用"，而要记录"一个请求如何穿过组件图、图版本、治理决策和工具执行"。

### 7.3.1 Trace 最小链路

```
request ingress
  -> graph version selected
  -> component hops
  -> tool calls / policy guards
  -> evaluation outputs
  -> evidence emission
  -> final response / rollback signal
```

### 7.3.2 Trace 数据结构

```python
@dataclass
class FullChainTrace:
    """全链路追踪数据模型。"""
    trace_id: str
    parent_trace_id: str | None
    root_task_id: str
    entry_point: str
    entry_timestamp: datetime
    spans: list[Span]
    config_snapshot_id: str
    graph_version: int
    agent_id: str


@dataclass
class Span:
    """调用链中的单个节点。"""
    span_id: str
    parent_span_id: str | None
    component_id: str
    slot_binding: str
    operation: str
    start_time: datetime
    end_time: datetime
    status: str
    tags: dict[str, str]
    logs: list[dict]
```

### 7.3.3 Trace 关键字段

| 字段 | 说明 |
| --- | --- |
| `trace_id` | 单次请求或单轮优化的全局标识 |
| `span_id` / `parent_span_id` | 链路层级关系 |
| `graph_version` | 当前活动图版本 |
| `component_id` / `slot_binding` | 经过的组件与位点 |
| `contract` | 输入/输出 payload 的契约名 |
| `proposal_id` | 如果属于优化周期，则关联 mutation proposal |
| `policy_decision_id` | 若经过治理判断，则建立引用 |
| `checkpoint_ref` | 需要回放或恢复时指向快照 |

### 7.3.4 Trace 传播机制

```
Gateway (span_id=G1)
  |
  ├── Runtime (span_id=R1, parent=G1)
  |     |
  |     ├── Memory.retrieve (span_id=M1, parent=R1)
  |     |
  |     ├── Policy.check (span_id=P1, parent=R1)
  |     |
  |     └── Sandbox.execute (span_id=S1, parent=R1)
  |           |
  |           └── LLM.call (span_id=L1, parent=S1)
  |
  └── Gateway.respond (span_id=G2, parent=G1)
```

每个组件在处理请求时，从上下文中提取 `trace_id` 和 `parent_span_id`，创建新的 Span 并在完成后上报。这保证了完整的调用链可被重建。

### 7.3.5 Trace 视图建议

| 视图 | 作用 |
| --- | --- |
| 请求视图 | 从用户请求看完整路径 |
| 组件视图 | 看某个组件在不同版本下的表现 |
| graph version 视图 | 看特定版本引入了哪些新路径 |
| proposal 视图 | 看一次变更如何影响后续请求链路 |

---

## 7.4 Replay：重放与复现

可观测性若不能重放，很多 trace 最终只会变成"漂亮但无用的日志"。这仍然是正确方向。

> **实现对齐说明（当前 MHE）**：当前代码库已经有 `CounterFactualDiagnosis`、`ProvenanceQuery`、`AuditLog`、`MerkleTree` 等证据与诊断模块；但文中这种统一 replay runtime 仍未作为一个端到端子系统完全实现。

### 7.4.1 请求级重放

目标是复现某次请求在某个 `graph version` 下的执行路径。最少需要保存：

- 输入 envelope
- graph version 引用
- 组件配置快照引用
- 工具调用输入输出摘要
- 时间与随机种子信息

### 7.4.2 版本级重放

目标是复现某次 candidate graph 的验证过程。最少需要保存：

- `pending mutations`
- candidate graph snapshot
- shadow traffic 样本引用
- sandbox report
- policy decision records
- observation window 配置与结果

### 7.4.3 重放接口建议

| 接口 | 说明 |
| --- | --- |
| `replay_trace(trace_id)` | 重放单次请求链路 |
| `replay_graph_version(graph_version)` | 重放版本验证与切流过程 |
| `replay_proposal(proposal_id)` | 重放一次 mutation proposal 的全流程 |

### 7.4.4 执行回放实现

```python
class TraceReplayer:
    """执行轨迹回放器。"""

    async def replay_trace(
        self,
        execution_id: str,
        from_step: int = 0,
        override_config: str | None = None,
    ) -> ReplayResult:
        """从指定步骤开始重放历史执行。"""
        trace = await self.memory.load_trace(execution_id)
        if not trace:
            raise TraceNotFoundError(execution_id)

        config = override_config or trace.config_version
        sandbox = await self.sandbox.create_replay_env(
            config=config,
            snapshot=trace.state_snapshot_at(from_step)
        )

        results = []
        for step in trace.steps[from_step:]:
            replay_step = await sandbox.replay_step(
                step=step,
                inject_input=step.input_snapshot
            )
            results.append(ReplayStepResult(
                original=step,
                replay=replay_step,
                diverged=replay_step != step.output_snapshot
            ))
            if replay_step.status == "error":
                break

        return ReplayResult(
            execution_id=execution_id,
            steps_replayed=len(results),
            divergences=[r for r in results if r.diverged],
            final_status=results[-1].replay.status if results else "empty"
        )
```

### 7.4.5 Replay 使用场景

| 场景 | 说明 | 输入 |
|---|---|---|
| 复现 Bug | 在隔离环境中重现非确定性行为 | `execution_id` |
| 验证修复 | 用修复后的配置重放失败轨迹 | `execution_id` + `override_config` |
| A/B 对比 | 同一任务在两个配置下的执行差异 | `task_id` + `config_a` + `config_b` |
| 回归测试 | 候选配置在历史失败案例上的表现 | `candidate_config` + `failed_trace_ids` |

---

## 7.5 Crash Recovery：崩溃恢复

崩溃恢复的目标不是让系统"继续跑"，而是让系统在恢复后仍然保持：

- graph version 一致性
- 审计链连续性
- 回放能力
- 回滚目标可用

### 7.5.1 最小恢复单元

| 对象 | 恢复时必须可得 |
| --- | --- |
| active graph pointer | 当前活动图版本 |
| rollback target | 上一个稳定版本 |
| in-flight trace buffer | 尚未刷盘的链路片段 |
| checkpoint reference | 最近一次可恢复状态 |
| audit tail hash | 审计链当前尾部哈希 |

### 7.5.2 恢复流程建议

```
process crash
  -> restore active graph pointer
  -> restore latest committed checkpoint reference
  -> recover audit tail hash
  -> replay in-flight events if available
  -> mark trace as recovered / truncated
  -> reopen observation window if cutover was in progress
```

### 7.5.3 崩溃恢复实现

```python
class CrashRecovery:
    """崩溃恢复管理器。"""

    async def recover_from_crash(self, agent_id: str) -> RecoveryResult:
        """从崩溃中恢复执行。"""
        last_checkpoint = await self.memory.get_last_checkpoint(agent_id)
        if not last_checkpoint:
            return RecoveryResult(
                recovered=False,
                reason="无可用检查点，需从头开始"
            )

        state = await self.memory.load_state_snapshot(
            last_checkpoint.snapshot_id
        )
        pending_steps = await self.identify_pending_steps(
            agent_id, last_checkpoint.step_id
        )

        for step in pending_steps:
            try:
                result = await self.runtime.execute_step(
                    step=step,
                    initial_state=state
                )
                state = result.new_state
                await self.memory.save_checkpoint(
                    agent_id=agent_id,
                    step_id=step.step_id,
                    state=state
                )
            except Exception as e:
                return RecoveryResult(
                    recovered=False,
                    reason=f"恢复执行失败: {e}",
                    last_successful_step=step.step_id - 1
                )

        return RecoveryResult(
            recovered=True,
            resumed_from_step=last_checkpoint.step_id,
            steps_redone=len(pending_steps)
        )
```

### 7.5.4 崩溃中的特殊场景

| 场景 | 建议处理 |
| --- | --- |
| 刚完成 cutover 但未刷完 trace | 标记 graph version 为 `uncertain`，进入强制 observation |
| rollback 执行中崩溃 | 优先恢复到上一个稳定 `rollback target` |
| 审计链写入失败 | 禁止继续接收新的高风险 proposal |

### 7.5.5 检查点策略

| 策略 | 粒度 | 存储开销 | 恢复速度 | 适用场景 |
|---|---|---|---|---|
| 每步检查点 | 每个执行步骤 | 高 | 最快 | 关键任务、不可中断任务 |
| 周期检查点 | 每 N 步或每 T 秒 | 中 | 中 | 一般任务 |
| 关键事件检查点 | 仅在关键操作前后 | 低 | 较慢 | 低风险任务 |

---

## 7.6 Hot / Cold Storage：冷热分层存储

观测数据量会快速增长，必须从一开始就设计冷热分层。

### 7.6.1 存储分层

```
┌──────────────────────────────────────────────────────┐
│ 热数据 (Hot) — 最近 H 小时                            │
│   存储: Redis / 本地 SSD                              │
│   内容: 当前活跃轨迹、最近执行步骤、实时指标            │
│   访问延迟: < 10ms                                    │
│   消费者: Optimizer（快速检索）、Runtime（崩溃恢复）    │
├──────────────────────────────────────────────────────┤
│ 温数据 (Warm) — 最近 7-30 天                          │
│   存储: 时序数据库 (ClickHouse / TimescaleDB)         │
│   内容: 聚合指标、压缩轨迹摘要、配置版本历史            │
│   访问延迟: < 100ms                                   │
│   消费者: Evaluation（趋势分析）、Policy（审计查询）   │
├──────────────────────────────────────────────────────┤
│ 冷数据 (Cold) — 30 天以上                             │
│   存储: 对象存储 (S3 / MinIO)                         │
│   内容: 完整轨迹归档、审计日志、配置快照                │
│   访问延迟: 秒级                                      │
│   消费者: 人工审计、长期趋势分析、学术研究              │
└──────────────────────────────────────────────────────┘
```

### 7.6.2 数据生命周期管理

```python
class TraceLifecycleManager:
    """轨迹数据的生命周期管理。"""

    HOT_RETENTION_HOURS = 4
    WARM_RETENTION_DAYS = 30
    COLD_RETENTION_DAYS = 365 * 3
    MERKLE_LOG_PERMANENT = True

    async def transition(self, trace: TaskTrace) -> None:
        """根据时间将轨迹数据在不同存储层之间迁移。"""
        age = utcnow() - trace.start_time

        if age > timedelta(days=self.COLD_RETENTION_DAYS):
            await self.archive_to_merkle_summary(trace)
            await self.delete_full_trace(trace)
        elif age > timedelta(days=self.WARM_RETENTION_DAYS):
            compressed = await self.compress_trace(trace)
            await self.cold_storage.put(
                key=f"traces/{trace.trace_id}.zst",
                data=compressed
            )
            await self.warm_storage.delete(trace.trace_id)
        elif age > timedelta(hours=self.HOT_RETENTION_HOURS):
            summary = self._generate_summary(trace)
            await self.warm_storage.insert_summary(summary)
            await self.warm_storage.insert_aggregated_metrics(trace)
            await self.hot_storage.delete(trace.trace_id)
```

### 7.6.3 分层原则

| 数据类型 | 推荐层 |
| --- | --- |
| live trace spans | 热 |
| recent shadow metrics | 热 |
| rollback records | 热 + 冷 |
| evidence object | 冷为主，摘要进热 |
| Merkle audit nodes | 冷 |
| provenance graph snapshots | 冷 |

### 7.6.4 索引结构

为轨迹建立多维度索引，方便 Optimizer 和开发者进行反事实诊断：

```python
TRACE_INDEXES = {
    "by_task_type":     "task_type -> [trace_id]",
    "by_status":        "status -> [trace_id]",
    "by_component":     "component_id -> [trace_id]",
    "by_error_type":    "error_type -> [trace_id]",
    "by_config":        "config_version -> [trace_id]",
    "by_time_range":    "timestamp_range -> [trace_id]",
    "by_keyword":       "keyword -> [trace_id]",
    "by_token_cost":    "token_range -> [trace_id]",
    "by_graph_version": "graph_version -> [trace_id]",
}
```

---

## 7.7 PROV-based Evidence Object

Meta-Harness 应把每次关键变更沉淀为一个 **PROV-based evidence object**。这让"为什么改、怎么改、改后怎样"成为可查询的一等对象，而不是散落在日志里的字符串。

### 7.7.1 Evidence Object 的核心作用

| 作用 | 说明 |
| --- | --- |
| 统一证据载体 | 把 trace、评估、治理、回滚信息聚合在一起 |
| 建立因果关系 | 记录 proposal、component、graph version 之间的 lineage |
| 支持外部审计 | 输出可核验、可导出的证据 |
| 支持 Memory 学习 | 让优化器能读历史成功/失败谱系 |

### 7.7.2 PROV 映射建议

| PROV 概念 | Meta-Harness 对象 |
| --- | --- |
| `Entity` | graph snapshot、candidate patch、checkpoint、evaluation result |
| `Activity` | sandbox validation、shadow run、graph cutover、rollback |
| `Agent` | Optimizer、Policy、Human Reviewer、Component Runtime |

### 7.7.3 Evidence Object 最小字段

| 字段 | 说明 |
| --- | --- |
| `evidence_id` | 全局唯一 ID |
| `proposal_id` | 对应 mutation proposal |
| `graph_version_before` / `after` | 变更前后图版本 |
| `trigger_reason` | 为什么触发这次变更 |
| `validation_bundle` | sandbox / shadow / policy 结果引用 |
| `rollback_info` | 是否回滚及原因 |
| `prov_refs` | PROV Entity / Activity / Agent 链接 |
| `audit_leaf_hash` | 写入 Merkle 审计链后的叶子哈希 |

### 7.7.4 JSON Schema（基于 W3C PROV）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MetaHarnessModificationEvidence",
  "description": "基于 W3C PROV 标准的修改证据对象",
  "type": "object",
  "required": ["prov_id", "timestamp", "actor", "parent_config_id",
               "modification_diff", "eval_results", "merkle_root"],
  "properties": {
    "prov_id": {
      "type": "string",
      "description": "符合 W3C PROV 规范的全局唯一 ID (prov:id)"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "修改发生的时间戳 (prov:generatedAtTime)"
    },
    "actor": {
      "type": "object",
      "description": "执行修改的实体 (prov:wasAttributedTo)",
      "properties": {
        "agent_id": { "type": "string" },
        "optimizer_model": { "type": "string" },
        "optimizer_version": { "type": "string" }
      },
      "required": ["agent_id"]
    },
    "parent_config_id": {
      "type": "string",
      "description": "上一个稳定版本的哈希值 (prov:wasDerivedFrom)"
    },
    "modification_diff": {
      "type": "string",
      "description": "XML 配置的 Unified Diff"
    },
    "trigger_reason": {
      "type": "string",
      "description": "自修改的触发动机"
    },
    "affected_components": {
      "type": "array",
      "items": { "type": "string" },
      "description": "受影响的组件 ID 列表"
    },
    "eval_results": {
      "type": "object",
      "description": "评估结果",
      "properties": {
        "sandbox_status": {
          "type": "string",
          "enum": ["passed", "failed", "skipped"]
        },
        "sandbox_test_count": { "type": "integer" },
        "sandbox_failures": {
          "type": "array",
          "items": { "type": "string" }
        },
        "ab_test_metric_delta": { "type": "number" },
        "ab_test_p_value": { "type": "number" },
        "policy_veto": { "type": "boolean" },
        "policy_violations": {
          "type": "array",
          "items": { "type": "string" }
        },
        "pareto_metrics": {
          "type": "object",
          "properties": {
            "accuracy": { "type": "number" },
            "latency_ms": { "type": "number" },
            "resource_mb": { "type": "number" },
            "context_tokens": { "type": "number" }
          }
        }
      }
    },
    "approval": {
      "type": "object",
      "description": "审批状态",
      "properties": {
        "auto_approved": { "type": "boolean" },
        "human_reviewed": { "type": "boolean" },
        "reviewer": { "type": "string" },
        "approval_time": { "type": "string", "format": "date-time" }
      }
    },
    "rollback_info": {
      "type": "object",
      "description": "回滚信息",
      "properties": {
        "triggered": { "type": "boolean" },
        "reason": { "type": "string" },
        "rollback_time": { "type": "string", "format": "date-time" },
        "observation_window_tasks": { "type": "integer" },
        "observation_window_seconds": { "type": "number" }
      }
    },
    "merkle_root": {
      "type": "string",
      "description": "用于确保审计日志不可篡改的哈希根"
    }
  }
}
```

### 7.7.5 PROV 映射关系

| 证据对象字段 | W3C PROV 概念 | 说明 |
|---|---|---|
| `prov_id` | `prov:id` | 实体唯一标识符 |
| `parent_config_id` | `prov:wasDerivedFrom` | 新配置派生自旧配置 |
| `actor` | `prov:wasAttributedTo` | 修改归因于 Optimizer |
| `timestamp` | `prov:generatedAtTime` | 生成时间 |
| `modification_diff` | `prov:hadMember` | 具体变更内容 |
| `eval_results` | `prov:wasInformedBy` | 评估活动影响决策 |

---

## 7.8 Merkle Audit Log：不可篡改审计链

Observability 只要允许被任意覆盖，系统最终就无法证明任何事情。为此，Meta-Harness 建议把关键审计记录写入 **Merkle audit log**。

### 7.8.1 为什么需要 Merkle 结构

| 问题 | Merkle 的价值 |
| --- | --- |
| 日志可被事后修改 | 任何篡改都会改变路径哈希 |
| 单条记录难验证 | 可对单条记录提供 inclusion proof |
| 长期归档难核验 | 只需保留根哈希与路径证明 |

### 7.8.2 建议进入 Merkle 链的事件

- graph cutover
- rollback triggered
- protected component proposal
- policy escalate / deny
- human approval
- evidence object finalized

### 7.8.3 审计链写入流程

```
critical event occurs
  -> canonicalize audit payload
  -> hash payload as leaf
  -> append leaf to Merkle tree
  -> compute new root
  -> persist root reference
  -> link root/hash back to evidence object
```

### 7.8.4 Merkle 审计链结构

```python
class MerkleAuditChain:
    """基于 Merkle Tree 的不可变审计日志。"""

    def __init__(self, storage: ImmutableStorage):
        self.storage = storage
        self.tree = MerkleTree()

    def append(self, evidence: ModificationEvidence) -> str:
        """追加新的证据对象到审计链。"""
        entry_bytes = json.dumps(
            evidence.model_dump(), sort_keys=True
        ).encode()
        prev_hash = self.tree.get_latest_leaf_hash()
        chained_entry = {
            "evidence": evidence.model_dump(),
            "prev_hash": prev_hash,
        }
        entry_bytes = json.dumps(chained_entry, sort_keys=True).encode()
        leaf_hash = self.tree.add_leaf(entry_bytes)
        self.storage.write(
            key=f"audit/{evidence.prov_id}",
            value=chained_entry,
            immutable=True
        )
        return leaf_hash

    def verify_integrity(self) -> IntegrityReport:
        """验证整个审计链的完整性。"""
        leaves = self.tree.get_all_leaves()
        violations = []
        for i in range(1, len(leaves)):
            entry = json.loads(leaves[i])
            prev_entry = json.loads(leaves[i - 1])
            expected_prev = self.tree.hash_leaf(leaves[i - 1])
            actual_prev = entry.get("prev_hash")
            if actual_prev != expected_prev:
                violations.append({
                    "index": i,
                    "expected_prev": expected_prev,
                    "actual_prev": actual_prev,
                    "description": "审计链断裂：prev_hash 不匹配"
                })
        computed_root = self.tree.get_merkle_root()
        return IntegrityReport(
            total_entries=len(leaves),
            violations=violations,
            merkle_root=computed_root,
            is_valid=len(violations) == 0
        )
```

### 7.8.5 审计查询接口

```python
class AuditQuery:
    """审计日志查询接口。"""

    def get_evidence_chain(
        self, config_id: str
    ) -> list[ModificationEvidence]:
        """获取某个配置版本的完整演化谱系。"""
        chain = []
        current = self.storage.get(f"audit/{config_id}")
        while current:
            evidence = ModificationEvidence(**current["evidence"])
            chain.append(evidence)
            parent_id = evidence.parent_config_id
            if parent_id == "genesis":
                break
            current = self.storage.get(f"audit/{parent_id}")
        return list(reversed(chain))

    def find_modifications_by_component(
        self, component_id: str, time_range: tuple[datetime, datetime]
    ) -> list[ModificationEvidence]:
        """查找涉及指定组件的所有修改记录。"""
        results = []
        start, end = time_range
        for key in self.storage.scan(prefix="audit/"):
            entry = json.loads(self.storage.get(key))
            evidence = entry["evidence"]
            ts = datetime.fromisoformat(evidence["timestamp"])
            if start <= ts <= end:
                if component_id in evidence.get("affected_components", []):
                    results.append(ModificationEvidence(**evidence))
        return results
```

### 7.8.6 审计链与普通日志的关系

普通日志用于调试；Merkle audit log 用于证明。两者都要有，但用途不同。

---

## 7.9 Provenance Query Interfaces：溯源查询接口

有了 evidence object 和 provenance graph，还需要把它们变成可查询的系统接口。

### 7.9.1 核心查询问题

Meta-Harness 至少要能回答这些问题：

- 为什么当前 `graph version` 比前一个慢？
- 哪次 proposal 首次引入了某条连接路径？
- 哪个 component implementation 与回滚最相关？
- 哪些死路提案曾被 policy 拒绝过？
- 哪些实验结果依赖于某个不再可信的工具输出？

### 7.9.2 查询接口建议

| 接口 | 说明 |
| --- | --- |
| `query_lineage(graph_version)` | 查询版本谱系与父子关系 |
| `query_component_history(component_id)` | 查询组件在多个版本中的表现与替换历史 |
| `query_proposal_evidence(proposal_id)` | 查询某次 proposal 的完整证据包 |
| `query_audit_path(audit_leaf_hash)` | 获取 Merkle inclusion proof |
| `query_dependency_impact(entity_id)` | 查询某个实体影响了哪些版本与结果 |

### 7.9.3 标准查询接口

```python
class ProvenanceQuery:
    """来源追溯查询接口。"""

    def get_config_lineage(self, config_id: str) -> ConfigLineage:
        """获取配置的完整演化谱系（DAG）。"""
        ...

    def get_modifications_in_range(
        self, start: datetime, end: datetime
    ) -> list[ModificationEvidence]:
        """获取指定时间范围内的所有修改记录。"""
        ...

    def get_rollback_history(self, config_id: str) -> list[RollbackRecord]:
        """获取某个配置的回滚历史。"""
        ...

    def get_component_provenance(
        self, component_id: str
    ) -> ComponentProvenance:
        """获取组件的创建/修改/删除历史。"""
        ...
```

---

## 7.10 Counter-Factual Diagnosis Interfaces：反事实诊断

仅有 lineage 还不够。Meta-Harness 的 Optimizer 还需要做"如果当时不这样改，会怎样"的诊断，也就是 **counter-factual diagnosis**。

### 7.10.1 反事实诊断的最小输入

- 一个或多个对比 `graph version`
- 关联的 full-chain trace 集合
- 共同任务样本或 shadow 样本
- performance delta 与 rollback records
- proposal diff 与 policy annotations

### 7.10.2 推荐接口

| 接口 | 说明 |
| --- | --- |
| `compare_versions(v_old, v_new)` | 比较两个版本的拓扑、性能与治理差异 |
| `diagnose_regression(proposal_id)` | 解释某次 proposal 为何导致回归 |
| `explain_rollback(graph_version)` | 解释某次 rollback 的触发链 |
| `suggest_dead_end_features(path_id)` | 总结失败路径的共同特征 |

### 7.10.3 反事实诊断支持接口

```python
class CounterfactualDiagnosis:
    """反事实诊断接口。"""

    async def get_failed_traces(
        self,
        component: str,
        limit: int = 10,
        error_type: str | None = None,
    ) -> list[TaskTrace]:
        """获取组件 X 最近 N 条失败轨迹。"""
        ...

    async def compare_traces(
        self,
        config_a: str,
        config_b: str,
        task_id: str,
    ) -> TraceComparison:
        """对比同一任务在两个配置下的执行差异。"""
        trace_a = await self.memory.load_trace_by_config(config_a, task_id)
        trace_b = await self.memory.load_trace_by_config(config_b, task_id)
        return TraceComparison(
            trace_a=trace_a,
            trace_b=trace_b,
            divergent_steps=self._find_divergences(trace_a, trace_b),
            metric_delta=self._compute_metric_delta(trace_a, trace_b)
        )

    async def search_traces(
        self,
        keyword: str,
        time_range: tuple[datetime, datetime] | None = None,
        filters: dict | None = None,
    ) -> list[TaskTrace]:
        """基于关键词和时间范围检索相关轨迹片段。"""
        ...

    async def replay_trace(
        self,
        execution_id: str,
        from_step: int = 0,
        override_config: str | None = None,
    ) -> ReplayResult:
        """从第 k 步开始重放指定执行。"""
        ...
```

### 7.10.4 诊断使用示例

```python
# Optimizer 诊断场景：分析某个组件为何频繁失败
failed_traces = await diagnosis.get_failed_traces(
    component="Memory_1",
    limit=20,
    error_type="timeout"
)

# 对比分析：为什么同一个任务在两个配置下表现不同
comparison = await diagnosis.compare_traces(
    config_a="cfg_v5",
    config_b="cfg_v7",
    task_id="task_00123"
)

for step_diff in comparison.divergent_steps:
    print(f"步骤 {step_diff.step_id}:")
    print(f"  配置 A: {step_diff.action_a} (延迟 {step_diff.latency_a}ms)")
    print(f"  配置 B: {step_diff.action_b} (延迟 {step_diff.latency_b}ms)")
    print(f"  差异原因: {step_diff.divergence_reason}")
```

### 7.10.5 反事实诊断的价值

它能把"坏结果"转化为 Memory 可消费的结构化经验，而不是简单的失败计数。

---

## 7.11 与 Memory 的集成

Observability 和 Memory 的关系，不应该是"日志最终落到 Memory"，而应该是：

- 审计链保持不可变
- Memory 存索引、摘要、经验与死路特征
- 优化器从 Memory 读取的是"可解释摘要"，不是直接改写原始证据

### 7.11.1 建议的分工

| 子系统 | 负责内容 |
| --- | --- |
| Observability | 原始 trace、metrics、audit、evidence object |
| Memory | 经验摘要、dead-end memory、版本画像、查询缓存 |
| Governance | 定义哪些证据必须保留、哪些查询需要授权 |

### 7.11.2 Memory 应保存什么

| 内容 | 用途 |
| --- | --- |
| successful proposal patterns | 提高后续搜索效率 |
| rollback signatures | 降低重复踩坑 |
| component drift summaries | 发现某组件随版本退化 |
| human approval precedents | 辅助未来治理判断 |

### 7.11.3 集成架构

```
Observability 采集
    |
    ├── 实时指标 → 时序存储（热/温）
    |
    ├── 执行轨迹 → Memory（全量持久化）
    |     ├── 短期：热存储（Optimizer 快速检索）
    |     ├── 中期：温存储（Evaluation 趋势分析）
    |     └── 长期：冷存储（人工审计、学术研究）
    |
    └── 审计日志 → Merkle 审计链（不可变存储）
          └── 证据对象 → Memory 长期资产区
```

### 7.11.4 语义查询示例

当用户询问"为什么系统现在的检索速度变慢了？"时，Memory 模块可以回溯证据链：

```python
async def answer_performance_question(question: str) -> Answer:
    """基于可观测性数据回答性能问题。"""
    target_component = extract_component(question)
    target_metric = extract_metric(question)

    degradation = await metrics.find_degradation_point(
        component=target_component,
        metric=target_metric
    )

    modifications = await audit.find_modifications_in_range(
        start=degradation.detected_at - timedelta(hours=2),
        end=degradation.detected_at,
        component=target_component
    )

    return Answer(
        summary=f"检索延迟在 {degradation.detected_at} 开始上升 "
                f"（从 {degradation.before_ms}ms 到 {degradation.after_ms}ms）",
        root_cause=modifications[0] if modifications else None,
        evidence_chain=[m.prov_id for m in modifications]
    )
```

---

## 7.12 观测面接入 staged lifecycle

Observability 必须嵌入整个 staged lifecycle，而不是只覆盖运行态。

```
discover candidate
  -> static validation records
  -> sandbox trace
  -> shadow trace
  -> policy decision audit
  -> graph cutover event
  -> observation window metrics
  -> rollback / stabilize evidence
```

### 7.12.1 建议固定事件

| 事件 | 说明 |
| --- | --- |
| `CANDIDATE_DISCOVERED` | 发现候选组件或提案 |
| `STATIC_VALIDATION_COMPLETED` | 静态校验通过/失败 |
| `SANDBOX_VALIDATION_COMPLETED` | 沙箱执行结果 |
| `SHADOW_VALIDATION_COMPLETED` | 影子验证结果 |
| `POLICY_DECISION_EMITTED` | allow / deny / escalate |
| `GRAPH_COMMITTED` | graph version 切换完成 |
| `OBSERVATION_WINDOW_CLOSED` | 观察窗口结束 |
| `ROLLBACK_TRIGGERED` | 自动回滚被触发 |
| `EVIDENCE_FINALIZED` | 证据对象归档完成 |

---

## 7.13 小结

本章系统阐述了元 Harness 的可观测性与审计体系：

1. **三层观测数据模型**（L1 遥测 / L2 生命周期 / L3 证据）覆盖了从实时调试到长期审计的完整范围
2. **全链路 Trace** 支持请求级别的完整调用链追踪与重建
3. **执行回放（Replay）** 在隔离环境中精确重现历史执行，用于 Bug 复现和修复验证
4. **崩溃恢复** 通过检查点机制确保 Agent 进程崩溃后可从断点恢复
5. **冷热数据分层** 在存储成本与查询性能之间取得平衡
6. **修改证据对象** 基于 W3C PROV 标准记录完整的自修改谱系
7. **Merkle 审计链** 防止审计记录本身被篡改
8. **反事实诊断接口** 为 Optimizer 提供基于轨迹的精准归因能力
9. **与 Memory 的集成** 使修改谱系成为长期可解释性资产

一句话概括：**Meta-Harness 的可观测性不是日志系统，而是由全链路 trace、版本事件、PROV 证据对象、Merkle 审计链、可回放查询接口与 Memory 经验层共同组成的证据基础设施。**

---

## 7.14 落地建议

按实施顺序，Observability 最值得先做的是以下七件事：

| 优先级 | 建议 |
| --- | --- |
| P0 | 冻结三层观测数据模型 |
| P0 | 给所有 trace / metric / audit 加上 `graph_version` 标签 |
| P0 | 实现 evidence object 最小 schema |
| P1 | 实现 request / proposal / graph version 三类查询接口 |
| P1 | 引入冷热分层存储 |
| P1 | 为关键事件建立 Merkle audit log |
| P2 | 实现 replay 与 counter-factual diagnosis 接口 |

## 7.15 更长期的事件驱动观测方向

在当前 evidence / PROV / Merkle / replay 路线之上，CMA-inspired 方向提示另一层基础设施化目标：把 `SessionEvent` 进一步视为状态、观测与审计的共同基底。

- **追加型状态 + 观测统一**：`SessionStore` / `SessionEvent` 不仅服务恢复，也可成为 trace、治理事件、checkpoint 与 cutover 事实的统一载体
- **事件先于视图**：dashboard、query、replay 与审计对象更多从结构化事件流派生，而不是由多个独立子系统各自维护事实
- **事件驱动可观测性**：event bus、版本事件和治理信号更明确进入统一事件模型后，Observability 会更像控制面的可计算日志，而不只是被动埋点系统

这与当前强化工作互补：前者把证据体系做扎实，后者则说明长期可如何把证据体系进一步变成统一事件基础设施。
