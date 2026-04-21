# 08. 热加载与状态迁移

本章把 Meta-Harness 的"运行中替换组件"落到一套可实现的动态切换协议上。目标不是简单的 reload 配置，而是构建一个围绕 **Suspend-Transform-Resume、state migration、component-level blue-green、checkpoint、observation window、自动回滚、熔断、Saga 补偿、migration adapter 注册** 的工程闭环。

当 Optimizer 生成的候选配置通过四级安全链路验证后，Runtime 需要在不中断当前任务执行的前提下，将旧组件替换为新组件——这要求一套严格的状态迁移协议。本章借鉴了 Erlang/OTP 的 `code_change` 机制和 Kubernetes 的声明式重构模式。

为与前文保持一致，本文统一使用：

- **candidate graph / active graph version / rollback target**
- **pending mutations**
- **staged lifecycle**
- **protected components**
- **observation window**
- **dead-end path**
- **ConnectionEngine**、**Policy / Governance**、**Observability**、**Memory**

---

## 8.1 热重载的目标与边界

Meta-Harness 的热重载要解决的不是"改完配置后自动生效"，而是三个更难的问题：

| 目标 | 说明 | 对应机制 |
| --- | --- | --- |
| 保持服务连续性 | 切换期间不丢失关键任务流 | Suspend-Transform-Resume |
| 保持状态一致性 | 旧状态能迁移到新实现 | state schema + migration adapter |
| 保持可回滚性 | 一旦退化可快速恢复 | checkpoint + rollback target + observation window |

热重载也有明确边界：

- 不是所有组件都应该支持无中断热切换
- `protected components` 默认不能走普通自动切换流程
- `Optimizer` 不能直接执行切换，只能提交 `mutation proposal`
- `ConnectionEngine` 只在候选图通过验证后原子切换 `active graph version`

---

## 8.2 Suspend-Transform-Resume 协议

Meta-Harness 推荐把热重载固定为 **Suspend-Transform-Resume（STR）** 三阶段协议，而不是让各组件自由发挥。

> **实现对齐说明（当前 MHE）**：当前这部分已经有可运行骨架：`HarnessComponent` 暴露 `suspend()` / `resume()` / `transform_state()`，`CheckpointManager` 负责内存态 checkpoint，`HotSwapOrchestrator` 用 saga 包装 `capture -> deactivate -> migrate -> resume`。但文中更重的蓝绿部署、消息缓冲器、观测窗口产品化、ARIES/WAL 等内容多数仍是目标设计而非现成功能。

```
old component serving
  -> suspend ingress and drain in-flight work
  -> export old state
  -> transform state to new schema
  -> activate new component
  -> import transformed state
  -> resume traffic
```

### 8.2.1 Suspend 阶段

`Suspend` 的目标是把系统推进到一个可迁移的 quiescent point：

- 暂停进入该 slot 的新流量
- 允许已开始的关键任务完成或进入 buffer
- 记录未完成任务与重放点
- 建立 checkpoint reference

```python
class SuspendPhase:
    """热加载第一阶段：挂起。"""

    async def execute(self, target_component_id: str) -> SuspendResult:
        """挂起目标组件并保存状态。"""
        component = self.registry.get(target_component_id)

        # 1. 停止向目标组件派发新消息
        self.message_router.pause(target_component_id)
        self.logger.info(f"已暂停向 {target_component_id} 派发消息")

        # 2. 等待当前正在执行的操作完成（带超时）
        await component.drain(timeout_sec=30)

        # 3. 创建全量状态检查点
        checkpoint = await self.checkpoint_manager.create(
            component_id=target_component_id,
            snapshot=component.export_state(),
            config_version=component.config_version
        )

        # 4. 缓存挂起期间到达的入站消息
        self.message_buffer = MessageBuffer(target_component_id)

        return SuspendResult(
            component_id=target_component_id,
            checkpoint_id=checkpoint.checkpoint_id,
            state_snapshot=checkpoint.snapshot,
            buffered_messages=0
        )
```

关键约束：
- 入站消息缓存但不丢弃
- 当前操作必须 drain 完成或超时后强制终止
- Checkpoint 必须在 Transform 之前创建完成

### 8.2.2 Transform 阶段

`Transform` 的目标是把旧组件状态映射为新组件可接受的状态结构。其核心数学表达是：

\[
\tau: S_{old} \times \Delta P \to S_{new}
\]

其中：

- `S_old`：旧组件的状态空间
- `ΔP`：本次变更引入的参数、拓扑或契约增量
- `S_new`：新组件的目标状态空间

`τ` 不一定是简单字段重命名；它可能包括：

- 状态 schema 升级
- 缓存结构重组
- 索引重建或降级回填
- 对旧状态做剪枝、补缺或归一化

```python
class TransformPhase:
    """热加载第二阶段：转换。"""

    async def execute(
        self,
        suspend_result: SuspendResult,
        new_config: XMLConfig,
    ) -> TransformResult:
        """执行状态迁移与组件替换。"""
        old_component = self.registry.get(suspend_result.component_id)
        old_state = suspend_result.state_snapshot

        # 1. 在沙箱中创建新组件实例
        new_component = await self.sandbox.instantiate(
            config=new_config,
            component_id=suspend_result.component_id
        )

        # 2. 执行状态迁移
        migration_adapter = self.get_migration_adapter(
            old_type=old_component.type,
            new_type=new_component.type,
            old_version=old_component.version,
            new_version=new_component.version,
        )
        new_state = await migration_adapter.migrate(
            old_state=old_state,
            delta_params=new_config.extract_delta_params()
        )

        # 3. 将迁移后的状态注入新组件
        new_component.import_state(new_state)

        # 4. 验证新组件的功能完整性
        validation_result = await self.validate_new_component(new_component)
        if not validation_result.passed:
            await self.rollback_to_checkpoint(suspend_result.checkpoint_id)
            return TransformResult(
                success=False,
                reason=f"验证失败: {validation_result.errors}"
            )

        # 5. 原子性指针切换
        self.registry.atomic_swap(
            component_id=suspend_result.component_id,
            old_instance=old_component,
            new_instance=new_component
        )

        return TransformResult(
            success=True,
            new_component=new_component,
            migration_adapter=migration_adapter.__class__.__name__
        )
```

### 8.2.3 Resume 阶段

`Resume` 的目标是让新组件接管流量，并在 `observation window` 中被持续验证：

- 恢复对新组件的入口路由
- 恢复 buffered messages 或重放队列
- 将旧组件保留为 rollback target 的一部分
- 进入 live observation

```python
class ResumePhase:
    """热加载第三阶段：恢复。"""

    async def execute(
        self,
        transform_result: TransformResult,
        suspend_result: SuspendResult,
    ) -> ResumeResult:
        """恢复组件服务并进入观察窗口。"""
        component_id = transform_result.new_component.component_id

        # 1. 重放缓存消息
        replay_count = 0
        while msg := self.message_buffer.pop():
            await self.message_router.dispatch(component_id, msg)
            replay_count += 1

        # 2. 恢复正常消息派发
        self.message_router.resume(component_id)

        # 3. 进入观察窗口
        observation_window = ObservationWindow(
            component_id=component_id,
            max_tasks=20,
            max_seconds=300,
            metrics=["latency_p99", "error_rate", "token_consumed"],
            baseline=transform_result.new_component.get_baseline_metrics()
        )
        self.watcher.register(observation_window)

        # 4. 归档旧组件
        await self.archive_old_component(
            suspend_result.component_id,
            transform_result.replaced_component
        )

        return ResumeResult(
            component_id=component_id,
            replayed_messages=replay_count,
            observation_window_id=observation_window.window_id,
            status="observing"
        )
```

---

## 8.3 借鉴 Erlang `code_change` 的状态迁移语义

Erlang/OTP 的价值不在于它的语法，而在于它对"在线升级时状态如何迁移"给出了稳定工程模式。Meta-Harness 可以借鉴其 `code_change` 语义：**新旧逻辑切换不是只换代码，还必须显式处理状态迁移。**

### 8.3.1 对 Meta-Harness 的启示

| Erlang 思想 | Meta-Harness 对应物 |
| --- | --- |
| `code_change(OldVsn, State, Extra)` | `transform_state(old_state, from_version, to_version, delta)` |
| 进程在切换点进入新代码 | slot 在 quiescent point 后切入新实现 |
| 状态转换是显式步骤 | migration adapter 是一等对象 |
| 失败可走监督与恢复 | rollback target + circuit breaker |

### 8.3.2 与 Erlang 的关键差异

| 维度 | Erlang/OTP | 元 Harness |
|---|---|---|
| 并发模型 | Actor 模型（轻量进程） | 组件模型（Python 对象） |
| 状态载体 | 进程字典 / gen_server state | 组件 `__dict__` / 显式状态对象 |
| 热加载粒度 | 模块级别 | 组件实例级别（含配置+代码） |
| 状态迁移 | 开发者手写 `code_change` | Optimizer 生成 + 人工审核 |
| 失败恢复 | Supervisor 重启策略 | Checkpoint + Saga 补偿 |

### 8.3.3 组件接口建议

| 方法 | 作用 |
| --- | --- |
| `prepare_swap()` | 评估是否可切换、是否需要 drain |
| `export_state()` | 导出旧状态 |
| `transform_state()` | 组件内迁移或调用 adapter |
| `import_state()` | 导入迁移后的新状态 |
| `resume()` | 恢复服务 |
| `abort_swap()` | 切换失败时清理候选状态 |

---

## 8.4 组件级蓝绿切换

Meta-Harness 建议把蓝绿部署从"整套服务"缩小到"component slot 级别"。

> **实现对齐说明（当前 MHE）**：当前仓库尚未形成完整的 component-level blue/green deployment runtime；已有的是 hot-swap / checkpoint / saga rollback 骨架，以及 `ConnectionEngine` 的 graph-level 原子切换与 rollback。蓝绿部分应视为后续增强方向。

### 8.4.1 组件级蓝绿流程

```
active slot binding = blue
  -> instantiate green candidate
  -> run shadow traffic on green
  -> if approved, switch pointer blue -> green
  -> keep blue as rollback target during observation window
```

### 8.4.2 Kubernetes 式蓝绿部署流程

借鉴 Kubernetes 的声明式配置管理模式，将热加载建模为一个有状态的迁移序列：

```
准备阶段 ──► 影子执行 ──► 切流阶段 ──► 清理阶段
  │              │            │            │
  ▼              ▼            ▼            ▼
创建新实例     并行运行      指针切换     归档旧实例
沙箱注入       指标对比      原子切换     状态归档
健康检查       收集证据      流量导入     资源释放
```

### 8.4.3 蓝绿部署实现

```python
class BlueGreenDeployer:
    """组件级蓝绿部署管理器。"""

    async def deploy(
        self,
        component_id: str,
        new_config: XMLConfig
    ) -> DeployResult:
        """执行蓝绿部署。"""
        blue = self.registry.get(component_id)
        green = await self.sandbox.instantiate(
            config=new_config,
            component_id=f"{component_id}__green"
        )

        shadow_result = await self.shadow_runner.run(
            primary=blue,
            shadow=green,
            task_source=self.memory.get_recent_tasks(limit=20),
            duration_sec=300,
        )

        if not shadow_result.green_superior:
            await green.destroy()
            return DeployResult(
                success=False,
                reason=f"影子执行未优于基线: {shadow_result.comparison}"
            )

        old_checkpoint = await self.checkpoint_manager.create(
            component_id=component_id,
            snapshot=blue.export_state()
        )

        migrated_state = await self.migrate_state(blue, green, new_config)
        green.import_state(migrated_state)

        self.registry.atomic_swap(
            component_id=component_id,
            old_instance=blue,
            new_instance=green
        )

        await self.archive_component(blue, old_checkpoint)

        return DeployResult(
            success=True,
            new_version=green.version,
            checkpoint_id=old_checkpoint.checkpoint_id
        )
```

### 8.4.4 蓝绿切换的优点

| 优点 | 说明 |
| --- | --- |
| 降低切换爆炸半径 | 只影响目标 slot 或局部 graph path |
| 保留快速回退能力 | blue 可在观察窗口内立即接管 |
| 易与 shadow 验证结合 | green 可先旁路接流量 |
| 适合 staged lifecycle | candidate graph 与 active graph 关系清晰 |

### 8.4.5 哪些组件适合组件级蓝绿

优先适合：

- `planner.primary`
- `executor.primary`
- `memory.retrieval.secondary`
- `observability.exporter.secondary`

谨慎处理：

- `memory.primary`
- `runtime.primary`
- `policy.primary`

---

## 8.5 Checkpoint 策略

热重载若没有 checkpoint，本质上就是一次高风险的现场改造。Meta-Harness 需要把 checkpoint 作为 graph cutover 前的强制步骤。

### 8.5.1 Checkpoint 类型

| 类型 | 说明 | 适用场景 |
| --- | --- | --- |
| 配置快照 | graph snapshot + component config | 所有切换 |
| 状态快照 | 组件导出的运行状态 | 有状态组件切换 |
| 队列快照 | 未完成消息、buffer、重放点 | runtime / executor / memory |
| 审计快照 | audit tail hash、evidence refs | 所有切换 |

### 8.5.2 推荐策略

| 组件类型 | Checkpoint 建议 |
| --- | --- |
| 无状态组件 | 至少保存配置快照与路由表版本 |
| 弱状态组件 | 保存配置快照 + 最小 state snapshot |
| 强状态组件 | 配置、状态、buffer、索引引用全部保存 |

### 8.5.3 Checkpoint 生命周期

```
before commit
  -> create checkpoint bundle
  -> bind checkpoint to candidate graph version
  -> commit graph
  -> keep checkpoint alive during observation window
  -> retire or archive after stabilization
```

### 8.5.4 全量快照 + ARIES 日志重放

借鉴数据库的 ARIES（Algorithm for Recovery and Isolation Exploiting Semantics）算法：

```python
class CheckpointManager:
    """检查点管理器：全量快照 + 增量日志重放。"""

    async def create(self, component_id: str, snapshot: dict) -> Checkpoint:
        """创建全量状态快照。"""
        checkpoint_id = f"cp_{component_id}_{utcnow().strftime('%Y%m%d%H%M%S')}"
        full_snapshot = {
            "checkpoint_id": checkpoint_id,
            "component_id": component_id,
            "timestamp": utcnow().isoformat(),
            "state": self._deep_copy(snapshot),
            "config_hash": self._hash_config(component_id),
            "merkle_proof": self._compute_merkle_proof(snapshot),
        }
        await self.storage.write(
            key=f"checkpoints/{checkpoint_id}",
            value=full_snapshot
        )
        self.wal.start_segment(checkpoint_id)
        return Checkpoint(
            checkpoint_id=checkpoint_id,
            timestamp=full_snapshot["timestamp"],
            snapshot_size_bytes=len(json.dumps(full_snapshot))
        )

    async def replay_wal(
        self, checkpoint_id: str, target_component_id: str
    ) -> int:
        """重放检查点之后的增量日志。"""
        entries = self.wal.read_segment(checkpoint_id)
        replayed = 0
        for entry in entries:
            component = self.registry.get(target_component_id)
            await component.apply_operation(entry.operation)
            replayed += 1
        return replayed
```

### 8.5.5 Checkpoint 保留策略

```python
CHECKPOINT_POLICY = {
    "max_checkpoints_per_component": 5,
    "retention_duration_days": 7,
    "genesis_checkpoint_permanent": True,
    "pre_rollback_checkpoint_permanent": True,
}
```

---

## 8.6 Observation Window：切换后的观察窗口

所有热重载都不应在切流后立刻判定"成功"。切换后必须进入 **observation window**。

### 8.6.1 观察窗口关注的指标

| 指标 | 说明 |
| --- | --- |
| 任务成功率 | 是否出现功能性回归 |
| 延迟分布 | 是否出现尾延迟放大 |
| 成本变化 | 是否性能提升但成本失控 |
| 错误率 | 是否出现新的异常模式 |
| 资源画像 | CPU / memory / I/O 是否异常尖峰 |
| policy violations | 是否新增治理异常 |

### 8.6.2 窗口时长建议

可采用统一经验式：

\[
\text{window} = \max(20 \text{ tasks}, 300 \text{ seconds})
\]

但对关键组件可拉长：

- `memory.primary`：覆盖至少两个完整读写周期
- `runtime.primary`：覆盖至少一个完整任务峰值窗口
- `planner.primary`：覆盖多个任务簇样本

### 8.6.3 观察窗口实现

```python
class ObservationWindow:
    """热加载后的观察窗口。"""

    def __init__(
        self,
        component_id: str,
        max_tasks: int = 20,
        max_seconds: int = 300,
    ):
        self.component_id = component_id
        self.max_tasks = max_tasks
        self.max_seconds = max_seconds
        self.baseline: dict | None = None

    def compute_z_score(self, metric: str, new_value: float) -> float:
        """计算新值的 Z-Score 异常分。"""
        if self.baseline is None:
            return 0.0
        mu = self.baseline[metric]["mean"]
        sigma = self.baseline[metric]["std"]
        if sigma == 0:
            return 0.0
        return (new_value - mu) / sigma

    def should_rollback(self, current_metrics: dict) -> RollbackDecision:
        """基于 Z-Score 判断是否应触发回滚。"""
        reasons = []
        latency_z = self.compute_z_score("latency_p99", current_metrics["latency_p99"])
        if latency_z > 3.0:
            reasons.append(f"延迟异常: Z-Score={latency_z:.2f} (> 3.0)")
        if current_metrics.get("error_rate", 0) > 0.1:
            reasons.append(f"错误率过高: {current_metrics['error_rate']:.2%}")
        if current_metrics.get("oom_count", 0) > 0:
            reasons.append("检测到 OOM 事件")
        if reasons:
            return RollbackDecision(should_rollback=True, reasons=reasons, severity="high")
        return RollbackDecision(should_rollback=False)
```

---

## 8.7 Z-score 回滚判据

观察窗口内是否回滚，建议使用 **Z-score** 作为最小异常判据之一。

### 8.7.1 基本公式

若某指标在旧版本上的均值与标准差为 `μ_old`、`σ_old`，新版本测得值为 `x_new`，则：

\[
Z = \frac{x_{new} - \mu_{old}}{\sigma_{old}}
\]

### 8.7.2 推荐解释

| 条件 | 建议动作 |
| --- | --- |
| `|Z| < 2` | 继续观察 |
| `2 <= |Z| < 3` | 标记异常，增强采样与治理观察 |
| `|Z| >= 3` | 触发回滚或强制人工复核 |

### 8.7.3 适合做 Z-score 的指标

- p95 / p99 latency
- 工具失败率
- OOM / crash 计数
- 关键质量分数
- 资源占用峰值

Z-score 不是唯一判据，但足够简单、可解释、适合 observation window 的第一道自动门槛。

---

## 8.8 熔断、Dead End 与路径冻结

一条切换路径如果连续失败，系统不应反复尝试相同模式。Meta-Harness 需要把 **circuit breaker** 与 **dead-end path** 建成标准机制。

### 8.8.1 熔断条件建议

| 条件 | 建议动作 |
| --- | --- |
| 同一 proposal family 连续 3 次回滚 | 标记为 dead-end |
| 同一 slot 在短时间内频繁切换 | 暂停自动热重载 |
| 审计链或 checkpoint 不完整 | 直接熔断高风险切换 |
| policy 连续 escalate/deny | 冻结该优化路径 |

### 8.8.2 Dead End 记录内容

| 字段 | 说明 |
| --- | --- |
| `path_id` | 失败路径标识 |
| `slot` | 涉及位点 |
| `proposal_family` | 同类提案分组 |
| `failure_signature` | 失败症状摘要 |
| `related_graph_versions` | 涉及版本 |
| `cooldown_until` | 冻结截止时间 |

### 8.8.3 与 Memory 的关系

Dead-end path 不只是黑名单，它还应进入 Memory，作为后续 proposer 的负样本经验。

### 8.8.4 熔断器实现

```python
class HotReloadCircuitBreaker:
    """热加载熔断器。"""

    CONSECUTIVE_FAILURE_THRESHOLD = 3
    HALF_OPEN_MAX_ATTEMPTS = 1
    OPEN_DURATION_SEC = 86400

    def __init__(self):
        self._state: dict[str, CircuitState] = {}

    def record_outcome(
        self, component_id: str, intent_hash: str, success: bool
    ) -> None:
        """记录热加载结果。"""
        key = f"{component_id}:{intent_hash}"
        state = self._state.setdefault(key, CircuitState(
            component_id=component_id,
            intent_hash=intent_hash
        ))

        if success:
            state.consecutive_failures = 0
            state.state = "closed"
        else:
            state.consecutive_failures += 1
            state.last_failure = utcnow()

            if state.consecutive_failures >= self.CONSECUTIVE_FAILURE_THRESHOLD:
                state.state = "open"
                state.open_until = utcnow() + timedelta(seconds=self.OPEN_DURATION_SEC)
                self.memory.record_dead_end(
                    component_id=component_id,
                    intent_hash=intent_hash,
                    reason=f"连续 {state.consecutive_failures} 次回滚"
                )

    def is_allowed(self, component_id: str, intent_hash: str) -> bool:
        """检查当前热加载意图是否被允许执行。"""
        key = f"{component_id}:{intent_hash}"
        state = self._state.get(key)
        if state is None:
            return True

        match state.state:
            case "closed":
                return True
            case "open":
                if utcnow() > state.open_until:
                    state.state = "half_open"
                    return True
                return False
            case "half_open":
                return False
```

### 8.8.5 熔断器状态机

```
                 成功                      失败次数 < 3
    ┌──────┐ ──────────► ┌────────┐ ◄──────────── ┌────────┐
    │ OPEN │             │ CLOSED │                │ CLOSED │
    └──┬───┘             └────────┘                └────────┘
       │                     │ 失败
       │ open_until 到期      │ 次数 >= 3
       ▼                     ▼
    ┌──────────┐        ┌──────┐
    │HALF_OPEN │        │ OPEN │ ←─── 标记为 Dead End
    └──────────┘        └──────┘     写入 Memory
       │
       │ 尝试成功 → CLOSED
       │ 尝试失败 → OPEN（重置定时器）
```

---

## 8.9 Saga 回滚与补偿事务

当一次热重载不只是替换单个组件，而是涉及多个组件联动时，简单"切回旧版本"可能不够，需要引入 **Saga rollback** 思想。

### 8.9.1 适用场景

- 同时替换 `planner.primary` 和 `executor.primary`
- `memory.primary` 迁移伴随索引结构变化
- 新旧组件共享部分外部资源或缓存

### 8.9.2 Saga 的核心思想

把一次大切换拆成若干局部步骤，每一步都有对应补偿动作：

| 步骤 | 正向动作 | 补偿动作 |
| --- | --- | --- |
| S1 | 部署 candidate component | 销毁 candidate component |
| S2 | 建立 shadow route | 关闭 shadow route |
| S3 | 执行 state migration | 恢复旧状态快照 |
| S4 | commit graph pointer | 切回旧 graph version |
| S5 | 清理旧实例 | 重新激活旧实例 |

### 8.9.3 Saga 的价值

它让多组件热重载不再是单点豪赌，而是一串可补偿的受控动作。

### 8.9.4 Saga 补偿逻辑实现

```python
class HotReloadSaga:
    """基于 Saga 模式的热加载回滚。"""

    def __init__(self):
        self.compensations: list[CompensatingAction] = []

    async def execute(self, plan: HotReloadPlan) -> SagaResult:
        """执行热加载 Saga，失败时自动补偿。"""
        try:
            checkpoint = await self.checkpoint_manager.create(
                component_id=plan.component_id,
                snapshot=self.get_current_state(plan.component_id)
            )
            self.compensations.append(
                CompensatingAction("delete_checkpoint", checkpoint.checkpoint_id)
            )

            await self.suspend(plan.component_id)
            self.compensations.append(
                CompensatingAction("resume_component", plan.component_id)
            )

            new_instance = await self.sandbox.instantiate(plan.new_config)
            self.compensations.append(
                CompensatingAction("destroy_instance", new_instance.instance_id)
            )

            migrated_state = await self.migrate_state(
                old_state=checkpoint.snapshot,
                new_instance=new_instance,
                adapter=plan.migration_adapter
            )

            self.registry.atomic_swap(
                component_id=plan.component_id,
                old_instance=self.registry.get(plan.component_id),
                new_instance=new_instance
            )
            self.compensations.append(
                CompensatingAction("swap_back", {
                    "component_id": plan.component_id,
                    "old_checkpoint": checkpoint.checkpoint_id,
                })
            )

            obs_result = await self.run_observation_window(
                component_id=plan.component_id,
                max_tasks=20,
                max_seconds=300
            )
            if not obs_result.passed:
                raise ObservationWindowFailure(obs_result.reasons)

            return SagaResult(success=True, checkpoint_id=checkpoint.checkpoint_id)

        except Exception as e:
            await self._compensate(e)
            return SagaResult(success=False, error=str(e))

    async def _compensate(self, original_error: Exception) -> None:
        """逆序执行所有补偿操作。"""
        for action in reversed(self.compensations):
            try:
                match action.name:
                    case "swap_back":
                        checkpoint = await self.checkpoint_manager.load(
                            action.params["old_checkpoint"]
                        )
                        old_component = await self.restore_from_checkpoint(
                            action.params["component_id"],
                            checkpoint
                        )
                        self.registry.atomic_swap(
                            component_id=action.params["component_id"],
                            old_instance=self.registry.get(action.params["component_id"]),
                            new_instance=old_component
                        )
                    case "destroy_instance":
                        await self.sandbox.destroy(action.params)
                    case "resume_component":
                        self.message_router.resume(action.params)
                    case "delete_checkpoint":
                        await self.checkpoint_manager.delete(action.params)
            except Exception as compensate_error:
                self.alert_critical(
                    f"补偿操作 '{action.name}' 失败: {compensate_error}. "
                    f"原始错误: {original_error}. 需要人工介入！"
                )
```

### 8.9.5 Saga 执行序列图

```
正常流程（全部成功）:
  Suspend → Checkpoint → Instantiate → Migrate → Swap → Observe → Done

异常流程（观察窗口失败）:
  Suspend → Checkpoint → Instantiate → Migrate → Swap → Observe(FAIL)
    │
    └── _compensate() 逆序执行：
        SwapBack(恢复旧组件) → DestroyInstance(销毁新实例)
        → ResumeComponent(恢复消息) → DeleteCheckpoint(清理检查点)
```

---

## 8.10 Migration Adapter 注册机制

状态迁移不能全靠组件作者在每次切换时"现场写转换函数"。Meta-Harness 需要一个 **migration adapter registry**。

### 8.10.1 Adapter 的作用

| 作用 | 说明 |
| --- | --- |
| 版本桥接 | 处理 `state_schema_version` 之间的转换 |
| 契约兼容 | 将旧 contract payload 转成新 contract |
| 风险隔离 | 把高风险迁移逻辑从主组件中拆开 |
| 可测试 | 独立验证 `v1 -> v2`、`v2 -> v3` 等路径 |

### 8.10.2 注册键建议

| 键 | 示例 |
| --- | --- |
| `component_kind` | `memory` |
| `impl_from` / `impl_to` | `jsonl -> hybrid` |
| `state_schema_from` / `to` | `1 -> 2` |
| `contract_from` / `to` | `MemoryResult@v1 -> MemoryResult@v2` |

### 8.10.3 迁移适配器接口

```python
class StateMigrationAdapter(ABC):
    """状态迁移适配器基类。"""

    source_type: str
    source_version: str
    target_type: str
    target_version: str

    @abstractmethod
    async def migrate(self, old_state: dict, delta_params: dict) -> dict:
        """将旧状态迁移到新结构。"""
        ...

    @abstractmethod
    def validate_migrated_state(self, new_state: dict) -> bool:
        """验证迁移后的状态是否有效。"""
        ...
```

### 8.10.4 适配器注册表

```python
class MigrationAdapterRegistry:
    """状态迁移适配器注册表。"""

    def __init__(self):
        self._adapters: dict[str, type[StateMigrationAdapter]] = {}

    def register(self, adapter_cls: type[StateMigrationAdapter]) -> None:
        """注册迁移适配器。"""
        key = self._make_key(
            adapter_cls.source_type, adapter_cls.source_version,
            adapter_cls.target_type, adapter_cls.target_version
        )
        self._adapters[key] = adapter_cls

    def get_adapter(
        self,
        source_type: str, source_version: str,
        target_type: str, target_version: str,
    ) -> StateMigrationAdapter:
        """获取匹配的迁移适配器。"""
        key = self._make_key(source_type, source_version,
                            target_type, target_version)
        if key in self._adapters:
            return self._adapters[key]()

        wildcard_key = self._make_key(source_type, "*", target_type, "*")
        if wildcard_key in self._adapters:
            return self._adapters[wildcard_key]()

        return DefaultMigrationAdapter()

    @staticmethod
    def _make_key(s_type: str, s_ver: str, t_type: str, t_ver: str) -> str:
        return f"{s_type}:{s_ver} → {t_type}:{t_ver}"
```

### 8.10.5 选择顺序建议

```
exact adapter match
  -> same impl, schema bridge
  -> generic kind-level adapter
  -> deny hot reload and require cold restart
```

### 8.10.6 迁移适配器示例

```python
class MemoryV1ToV2Adapter(StateMigrationAdapter):
    """Memory 组件从 v1 迁移到 v2 的适配器。

    v1: 滑动窗口 + 简单缓存
    v2: 滑动窗口 + 自动摘要 + 相关性过滤
    """
    source_type = "Memory"
    source_version = "1.0"
    target_type = "Memory"
    target_version = "2.0"

    async def migrate(self, old_state: dict, delta_params: dict) -> dict:
        new_state = {}
        new_state["conversation_history"] = old_state.get("conversation_history", [])
        new_state["config_version"] = self.target_version
        new_state["summary_cache"] = {}
        if len(new_state["conversation_history"]) > 10:
            recent = new_state["conversation_history"][-5:]
            older = new_state["conversation_history"][:-5]
            new_state["summary_cache"]["auto"] = await self._summarize(older)
            new_state["conversation_history"] = recent
        new_state["relevance_config"] = {
            "threshold": delta_params.get("relevance_threshold", 0.5),
            "model": delta_params.get("embedding_model", "default"),
        }
        return new_state

    def validate_migrated_state(self, new_state: dict) -> bool:
        required_keys = ["conversation_history", "summary_cache", "relevance_config"]
        return all(k in new_state for k in required_keys)
```

---

## 8.11 生命周期状态机

热重载本质上是一台状态机。把状态写清楚，能显著降低实现混乱。

### 8.11.1 完整状态机

```
                    ┌──────────────┐
                    │    IDLE      │ ← 初始状态
                    └──────┬───────┘
                           │ Optimizer 生成候选配置
                           ▼
                    ┌──────────────┐
              ┌────►│  VALIDATING  │ 静态兼容性校验 + 预编译检查
              │     └──────┬───────┘
              │            │ 校验通过
              │            ▼
              │     ┌──────────────┐
              │     │  SANDBOXING  │ 沙箱回归测试
              │     └──────┬───────┘
              │            │ 测试通过
              │            ▼
              │     ┌──────────────┐
              │     │  SHADOW_TEST │ A/B 影子测试
              │     └──────┬───────┘
              │            │ 指标优于基线
              │            ▼
              │     ┌──────────────┐
              │     │  POLICY_CHK  │ Policy 宪法审查
              │     └──────┬───────┘
              │            │ 未被否决
              │            ▼
              │     ┌──────────────┐
         校验/测试    │  SUSPENDING  │ 挂起旧组件
         失败        └──────┬───────┘
              │            │ 挂起完成
              │            ▼
              │     ┌──────────────┐
              │     │  TRANSFORMING│ 状态迁移 + 新组件初始化
              │     └──────┬───────┘
              │            │ 迁移成功
              │            ▼
              │     ┌──────────────┐
              │     │   RESUMING   │ 恢复消息派发 + 启动观察窗口
              │     └──────┬───────┘
              │            │ 消息恢复完成
              │            ▼
              │     ┌──────────────┐
              │     │  OBSERVING   │ 观察窗口监控
              │     └──────┬───────┘
              │            │
              │     ┌──────┴───────┐
              │     │              │
              │     ▼              ▼
              │  ┌────────┐  ┌──────────┐
              │  │COMMITTED│  │ROLLING_BACK│
              │  │ 已提交   │  │  回滚中     │
              │  └────┬───┘  └──────┬───┘
              │       │             │
              │       ▼             │
              │  ┌────────┐         │
              └──│REJECTED│ ◄───────┘
                 │ 已拒绝  │  回滚完成后
                 └────────┘  回到 IDLE
```

### 8.11.2 状态转换规则

| 当前状态 | 触发事件 | 目标状态 | 条件 |
|---|---|---|---|
| IDLE | 候选配置就绪 | VALIDATING | Optimizer 输出已就绪 |
| VALIDATING | 校验通过 | SANDBOXING | 全部兼容性规则通过 |
| VALIDATING | 校验失败 | REJECTED | 任一规则不通过 |
| SANDBOXING | 测试通过 | SHADOW_TEST | 回归测试 100% 通过 |
| SANDBOXING | 测试失败 | REJECTED | 任一回归测试失败 |
| SHADOW_TEST | 优于基线 | POLICY_CHK | 统计显著优于基线 |
| SHADOW_TEST | 不优于基线 | REJECTED | 未通过显著性检验 |
| POLICY_CHK | 未被否决 | SUSPENDING | 无不变量冲突 |
| POLICY_CHK | 被否决 | REJECTED | 违反治理不变量 |
| SUSPENDING | 挂起完成 | TRANSFORMING | Checkpoint 已创建 |
| TRANSFORMING | 迁移成功 | RESUMING | 新组件功能验证通过 |
| TRANSFORMING | 迁移失败 | ROLLING_BACK | 状态迁移异常 |
| RESUMING | 恢复完成 | OBSERVING | 消息已恢复派发 |
| OBSERVING | 观察通过 | COMMITTED | Z-Score < 3.0 且无异常 |
| OBSERVING | 观察失败 | ROLLING_BACK | 性能退化或异常 |
| ROLLING_BACK | 回滚完成 | IDLE | 补偿逻辑执行完毕 |
| REJECTED | - | IDLE | 反馈给 Optimizer 后回到待命 |

---

## 8.12 热重载与 ConnectionEngine 的关系

热重载不能让组件自己改路由。建议职责边界如下：

| 子系统 | 负责内容 |
| --- | --- |
| 组件自身 | `export_state` / `import_state` / `transform_state` |
| Migration Adapter | 跨版本/跨实现状态桥接 |
| ConnectionEngine | graph pointer 切换与路由表原子替换 |
| Observability | 记录切换、观察窗口、回滚证据 |
| Governance | 决定是否允许切换 |
| Memory | 保存 dead-end 与迁移经验 |

---

## 8.13 何时不应热重载

热重载是能力，不是义务。以下场景建议直接拒绝或降级为冷切换：

| 场景 | 建议 |
| --- | --- |
| 无可用 migration adapter | 拒绝热切换 |
| 组件是 `protected component` | 走人工审批或冷切换 |
| 无法建立 checkpoint | 拒绝切换 |
| 组件状态过大且迁移时间不可控 | 选择离线迁移或双写同步 |
| 影子验证样本不足 | 延后 commit |

---

## 8.14 小结

本章系统阐述了元 Harness 的热加载与状态迁移机制：

1. **Suspend-Transform-Resume 三阶段协议** 提供了严格有序的状态迁移流程，数学上表示为 \(\tau: S_{old} \times \Delta P \to S_{new}\)
2. **Erlang code_change 启示** 为状态连续性设计提供了成熟参考
3. **Kubernetes 式蓝绿部署** 在组件级别实现了零停机切换
4. **全量快照 + ARIES 日志重放** 保证了 Checkpoint 的原子性与可恢复性
5. **观察窗口设计** 通过 Z-Score 异常检测自动判断是否需要回滚
6. **Circuit Breaker** 对连续失败的优化路径标记为 Dead End
7. **Saga 模式** 为多组件联动回滚提供了补偿逻辑框架
8. **状态迁移适配器注册** 支持组件版本间的自动状态映射
9. **完整的状态机** 定义了热加载全生命周期的状态转换规则

一句话概括：**Meta-Harness 的热重载不是"替换代码后继续跑"，而是由 Suspend-Transform-Resume、显式状态迁移、组件级蓝绿、checkpoint、观察窗口、Z-score 回滚、熔断与 Saga 补偿共同组成的受控切换协议。**

---

## 8.15 落地建议

按实施顺序，热重载层最值得先做的是以下八件事：

| 优先级 | 建议 |
| --- | --- |
| P0 | 固定 Suspend-Transform-Resume 协议 |
| P0 | 为组件定义 `prepare_swap/export_state/import_state` 最小接口 |
| P0 | 在切换前强制生成 checkpoint bundle |
| P1 | 引入 component-level blue-green 与 shadow route |
| P1 | 实现 observation window 与 Z-score 判据 |
| P1 | 增加 circuit breaker / dead-end path 机制 |
| P2 | 建立 migration adapter registry |
| P2 | 对多组件联动切换引入 Saga rollback |
