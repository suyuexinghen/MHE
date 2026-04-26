# MHE Core 架构增强总报告

> 版本：v0.2 | 日期：2026-04-25 | 状态：修订草案

## 1. 背景与方法

### 1.1 为什么需要这份报告

MHE 当前有 6 个 extension 处于不同设计/实现阶段：ABACUS（DFT）、DeepMD（分子动力学）、
JEDI（数据同化）、AI4PDE（PDE 求解）、Nektar（CFD）、QCompute（量子计算）。
每个 extension 独立分析了 MHE core 的架构 gap，记录在 `docs/wiki/MHE-core-improvement.md`
和 `docs/wiki/Qcompute.md` 中。

两条独立分析路径收敛到相同的结论：**MHE core 当前更接近"图治理框架"，
还不是"运行治理框架"**。但各 extension 的具体需求、优先级和风险容忍度不同，
尚未统一排序或形成可执行的改进路线图。

### 1.2 分析方法

1. **代码审查**：逐模块阅读 MHE core 源码（models.py、boot.py、mutation.py、
   optimizer.py、fitness.py、convergence.py、pipeline.py、event_bus.py、
   checkpoint.py、observation.py、gates.py、manifest.py、events.py、brain.py）
2. **Extension 反推**：从 6 份 extension gap 报告中提取对 core 的共同要求
3. **交叉验证**：用 QCompute 的 7 维度分析（`docs/wiki/Qcompute.md`）独立验证
   其他 5 个 extension 的共性结论

### 1.3 一句话结论

MHE core 的下一阶段改进不是"再加几个组件"，而是把 core 从**图治理框架**
推进为**运行治理框架**。v0.2 将优先级重新收敛为 3 条主线：

1. run-oriented contracts + execution service
2. run-level governance + evidence protocol
3. durable session/evidence/artifact store

其余需求（如 `domain_payload`、Pareto、多目标优化、provider-specific quota）
在本版中下调为 **extension-first validation**：先由 extension 层验证价值，
再决定是否进入 core。  

---

## 2. 现状评估

### 2.1 已具备的能力

为避免误导，本节将现状拆成 **图治理成熟度** 与 **运行治理成熟度** 两列。
当前 MHE 在图治理上明显更成熟，在运行治理上仍以骨架为主。

| 能力维度 | 实现位置 | 图治理成熟度 | 运行治理成熟度 |
|---------|---------|-------------|---------------|
| 图级 candidate/commit/rollback | `connection_engine.py` stage/commit/discard | 成熟 | 缺失 |
| 受保护组件声明 | `models.py` ComponentNode.protected + validators.py 检查 | 成熟 | 基础可用 |
| PromotionContext 统一记录 | `models.py` PromotionContext dataclass | 成熟 | 基础可用 |
| 安全门 pipeline | `safety/pipeline.py` 四级 gate chain | 基础可用 | 缺失 |
| SessionEvent/SessionStore 协议 | `models.py` + `observability/events.py` InMemorySessionStore | 基础可用 | 基础可用 |
| ScoredEvidence 统一评分协议 | `models.py` ScoredEvidence + BudgetState + ConvergenceState | 成熟 | 基础可用 |
| BrainProvider proposal-only 边界 | `brain.py` Protocol + `optimizer.py` proposal-only 设计 | 成熟 | 基础可用 |
| Checkpoint capture/restore | `hotreload/checkpoint.py` CheckpointManager + saga | 基础可用 | 缺失 |
| Hot-swap saga orchestration | `hotreload/swap.py` HotSwapOrchestrator | 基础可用 | 缺失 |
| Observation window probes | `hotreload/observation.py` ObservationWindowEvaluator | 基础可用 | 缺失 |
| Optimizer observe/propose/evaluate/commit | `components/optimizer.py` OptimizerComponent | 成熟 | 基础可用 |
| FitnessEvaluator + TripleConvergence | `optimizer/fitness.py` + `convergence.py` | 成熟 | 基础可用 |
| AuditLog (JSONL + Merkle) | `provenance/audit_log.py` | 成熟 | 基础可用 |
| ProvGraph (PROV 模型) | `provenance/evidence.py` | 基础可用 | 基础可用 |
| EventBus (pub/sub + trace) | `core/event_bus.py` | 成熟 | 基础可用 |
| ValidationIssue 分类 + blocks_promotion | `models.py` ValidationIssueCategory enum | 成熟 | 基础可用 |
| ComponentManifest 完整 schema | `sdk/manifest.py` ComponentManifest + DependencySpec | 成熟 | 基础可用 |

### 2.2 不足的能力

| 能力维度 | Gap | 影响 |
|---------|-----|------|
| 执行模型 | 无 run/job abstraction，无异步轮询/重试/取消 | 所有有外部执行的 extension |
| Run contracts | 无 core 级 RunPlan/RunArtifact/EnvironmentReport 协议 | 所有 extension |
| 领域验证→governance | `evaluate_graph_promotion()` 绕过 gate chain，run-level evidence 不进入正规 gate 路径 | 所有需要领域验证的 extension |
| Policy tri-state | 只有 allow/reject，无 defer，也无 deferred candidate 生命周期 | DeepMD、QCompute、AI4PDE |
| Run validation 协议 | 无统一的 ValidationOutcome / EvidenceBundle 输入给 governance | 所有 extension |
| 多目标优化 | FitnessEvaluator 只有单标量 fitness，无 Pareto | QCompute |
| Optimizer 粒度 | MutationProposal 只表达 graph topology，不表达领域候选 | QCompute、Nektar |
| Manifest optional deps | DependencySpec 无 optional 分支 | QCompute（QSteed/Mitiq） |
| 执行生命周期事件 | SessionEventType 只有图事件，无执行事件 | 所有 extension |
| Durable store | SessionStore 只有 InMemory 实现 | 所有 extension |
| Checkpoint 范围 | 只保存 component state，不保存 run artifact；artifact snapshot 与 state checkpoint 未分离 | Nektar、QCompute |
| Scientific provenance | ProvGraph 泛化，缺科学产物 lineage schema | 所有 extension |
| ResourceQuota | 无外部资源配额抽象 | QCompute（真机配额）、Nektar（HPC） |
| Control-plane objects | 无 team/approval/budget/template 一等对象 | AI4PDE |

---

## 3. 统一需求矩阵

共识度排序：★★★ 所有 extension 必须 → ★★ 多数 extension 增强 → ★ 个别 extension 需要

| Core 改进项 | ABACUS | DeepMD | JEDI | AI4PDE | Nektar | QCompute | 共识度 |
|------------|--------|--------|------|--------|--------|----------|--------|
| RunPlan/RunArtifact 协议 | 必须 | 增强 | 必须 | 必须 | 必须 | 必须 | ★★★ |
| 异步执行 (submit/poll/cancel) | 必须 | — | 增强 | 增强 | 必须 | 必须 | ★★★ |
| 执行生命周期事件 | 必须 | — | 增强 | 增强 | 必须 | 必须 | ★★★ |
| Run-level governance gate | 必须 | 必须 | 必须 | 必须 | 必须 | 必须 | ★★★ |
| Durable session store | 增强 | 增强 | 必须 | 必须 | 必须 | 增强 | ★★ |
| Artifact evidence bundle API | 必须 | 必须 | 必须 | 增强 | 必须 | 必须 | ★★ |
| Policy allow/defer/reject | — | 必须 | 增强 | 必须 | 增强 | 必须 | ★★ |
| domain_payload on MutationProposal | — | — | — | — | 增强 | 必须 | ★ |
| 多目标 Pareto fitness | — | — | — | — | — | 必须 | ★ |
| optional_deps manifest | — | — | — | — | — | 必须 | ★ |
| ResourceQuota 协议 | — | — | — | — | 增强 | 必须 | ★ |
| Template 一等生命周期 | — | — | — | 必须 | — | — | ★ |
| Team/approval/budget | — | — | — | 必须 | — | — | ★ |
| Invariant engine | — | — | — | 必须 | — | — | ★ |

---

## 4. 架构增强方案

### 4.1 Run-oriented core contracts

**Gap**：当前 core 没有 RunPlan/RunArtifact/EnvironmentReport/ValidationOutcome/EvidenceBundle
的一等抽象。每个 extension 各自定义自己的模型（如 nektar 的 NektarSessionPlan/NektarRunArtifact），
但 core 不知道这些概念，无法提供统一的执行治理。

**方案**：在 `sdk/run_contracts.py`（或 `sdk/execution.py`）中定义 Protocol 级协议
（不是具体实现，也不放在 `core/models.py`，避免数据模型层和运行协议层耦合）：

```python
class RunPlanProtocol(Protocol):
    plan_id: str
    experiment_ref: str
    target_backend: str
    execution_params: dict[str, Any]

class RunArtifactProtocol(Protocol):
    artifact_id: str
    plan_ref: str
    status: str
    raw_output_path: str | None

class EnvironmentReportProtocol(Protocol):
    task_id: str
    available: bool
    blocks_promotion: bool

class ValidationOutcomeProtocol(Protocol):
    subject_ref: str
    status: str
    blocks_promotion: bool
    evidence_refs: list[str]

class EvidenceBundleProtocol(Protocol):
    bundle_id: str
    evidence_refs: list[str]
```

Extension 的具体类型（如 `QComputeRunPlan`、`NektarSessionPlan`）只需满足 Protocol
即可被 core 的执行治理路径消费，不需要继承 core 基类。

**受益 extension**：全部 6 个（★★★ 共识）

### 4.2 Job execution layer

**Gap**：`HarnessComponent` 只有 `activate/deactivate` 钩子，没有任务执行抽象。
`ExecutorComponent`（`components/executor.py`）仍是 stub。

**方案**：在 `sdk/execution.py` 中定义：

```python
from enum import Enum
from typing import Protocol

class ExecutionStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class JobHandle(BaseModel):
    job_id: str
    backend: str
    status: ExecutionStatus
    submitted_at: datetime
    completed_at: datetime | None = None

class PollingStrategy(Protocol):
    async def next_delay(self, attempt: int) -> float: ...
    @property
    def max_total_wait(self) -> float: ...

class AsyncExecutorProtocol(Protocol):
    async def submit(self, plan: Any) -> JobHandle: ...
    async def poll(self, job_id: str) -> ExecutionStatus: ...
    async def cancel(self, job_id: str) -> None: ...
    async def await_result(self, job_id: str, timeout: float) -> Any: ...
```

提供内置的 `FibonacciPollingStrategy` 和 `ExponentialBackoffStrategy`。
Extension 的 executor 实现 `AsyncExecutorProtocol`，core 提供轮询/重试/取消的
编排逻辑，避免每个 extension 重复实现。

**受益 extension**：ABACUS、Nektar、QCompute 必须；JEDI、AI4PDE 增强

### 4.3 Run-level governance

**Gap**：`SafetyPipeline.evaluate_graph_promotion()` 只调用可选的 `reviewer`，
完全跳过 gate chain。domain validation results 永远不经过安全门。

**方案**：

1. **扩展 evaluate_graph_promotion 经过 gates**：

```python
# safety/gates.py
class SafetyGate(ABC):
    name: str

    @abstractmethod
    def evaluate(self, proposal, context) -> GateResult: ...

    def evaluate_promotion(self, promotion: PromotionContext) -> GateResult:
        return GateResult.allow(self.name)
```

这里使用 `ABC` 或默认 mixin，而不是 `Protocol` 默认实现。`evaluate_graph_promotion`
在 reviewer 检查后，若 gate 实现了 `evaluate_promotion`，则继续遍历。

2. **Policy tri-state + deferred candidate lifecycle**：

```python
class PolicyDecision(str, Enum):
    ALLOW = "allow"
    DEFER = "defer"
    REJECT = "reject"
```

`DEFER` 不等于 `REJECT`。v0.2 明确要求补齐 deferred candidate 语义：
- deferred candidate 保留 candidate record，不进入 active graph
- deferred candidate 不触发 committed，也不视为 failed/rejected
- 必须有再审查入口（人工审批、补充 evidence、延后自动重试）
- SessionEvent 需能记录 `candidate_deferred`

3. **ResourceQuota 协议**（保留为增强项，不作为 core 初期主线）：

```python
class ResourceQuota(BaseModel):
    resource_type: str
    provider: str
    daily_limit: int | None
    daily_used: int
    blocks_execution: bool = False
```

**受益 extension**：全部 6 个需要 run-level gate（★★★）；
defer 是 DeepMD/QCompute/AI4PDE 的重要增强；ResourceQuota 仍建议先由 extension 验证

### 4.4 Durable evidence & provenance

**Gap**：SessionStore 只有 InMemory 实现。AuditLog 有 JSONL 但 session store 没有。
同时，当前 system checkpoint 只保存 component state，不保存 run artifact；
而 run artifact 的持久化需求与 hot-reload checkpoint 并不是同一个概念。

**方案**：

1. **FileSessionStore**：在 `observability/events.py` 中增加基于 JSONL 的
   持久化实现，支持 `wake(session_id)` 恢复。

2. **拆分 artifact snapshot 与 component checkpoint**：
   - `CheckpointManager` 继续负责 component state（hot reload / rollback / migration）
   - 新增 `ArtifactSnapshotStore` 或等价接口，专门保存 RunArtifact / ValidationOutcome /
     EvidenceBundle 的持久化快照
   - 不把 scientific artifact 混入 component state checkpoint，避免语义污染

3. **Scientific artifact lineage**：在 `provenance/` 中定义标准 relation types：
   - `EXPERIMENT_SPEC → RUN_PLAN → RUN_ARTIFACT → VALIDATION_REPORT → EVIDENCE_BUNDLE`
   - 统一 extension 的 provenance chain 表达

**受益 extension**：JEDI、AI4PDE、Nektar 必须；其余增强

### 4.5 Optimizer dual-layer architecture

**Gap**：`MutationProposal` 只携带 `PendingConnectionSet`（graph topology），
不携带领域候选。`FitnessEvaluator` 只有单标量 fitness，不支持多目标/Pareto。

**方案**：

1. **core 先只做最小增强**：
   `MutationProposal` 增加 `domain_payload: dict[str, Any] | None = None`，
   作为 graph optimizer 与 domain/study optimizer 之间的桥接通道。

2. **Pareto / MultiObjectiveScore 暂不直接 core 化**：
   这些能力当前主要由 QCompute 明确需要，建议先在 extension 层验证：
   - QCompute 先在自身 Study/optimizer 中实现 `MultiObjectiveScore`
   - 若未来 2+ extension 独立出现多目标前沿需求，再提升为 core 能力

3. **core 侧保留 evidence plumbing**：
   core 只保证 `ScoredEvidence.metrics`、`domain_payload`、`ProposalEvaluation`
   可以承载多目标信息，而不在本阶段规定统一 Pareto API。

**受益 extension**：QCompute 立即受益；其余 extension 暂不受影响

### 4.6 Control-plane enhancements

本主题在 v0.2 中继续保留为远期主题，不进入核心主线。原因是它主要由 AI4PDE 强驱动，
尚未形成跨 extension 的稳定共识。

**Gap**：MHE core 没有 team/approval/budget/template 等控制面对象。
当前只有 graph lifecycle + component lifecycle。

**方案**（远期，Phase 5 细化）：

- **Template lifecycle**：将 AI4PDE 的模板匹配机制抽象为 core 一等对象
- **Approval routing**：将人工审批从 ad-hoc 提升为 core protocol
- **Budget ledger**：将 `BudgetState` 从 ScoredEvidence 附属提升为
  authoritative service
- **Invariant engine**：将硬编码的 `blocks_promotion` 检查替换为声明式不变量

**受益 extension**：主要是 AI4PDE（★★）；其余 extension 远期可能受益

---

## 5. 分 phase 路线图

### Phase 0：模型增量扩展

**目标**：为后续 phase 做数据模型准备。纯增量，所有新字段有默认值，零破坏。

**改动点**：

| 文件 | 改动 |
|------|------|
| `src/metaharness/core/models.py` | SessionEventType 增加 5 个执行事件枚举值 + `CANDIDATE_DEFERRED` |
| `src/metaharness/core/mutation.py` | MutationProposal 增加 `domain_payload` 可选字段 |
| `src/metaharness/sdk/manifest.py` | DependencySpec 增加 `optional_components`、`optional_capabilities` 可选字段 |

**说明**：
- `optional_deps` 属于低风险 schema hygiene，本 phase 一并处理，但不视为主线改进
- 执行事件只在模型中预留，不在本 phase 绑定到 `commit_graph()`

**依赖**：无

**验证**：
- 现有 pytest 子集全部通过（新字段有默认值）
- 新增测试：确认新字段可序列化/反序列化
- 新增测试：确认不含 domain_payload 的旧 MutationProposal 仍可正常使用

**预计影响**：3 个文件，约 30 行新增代码

---

### Phase 1：Run contracts & execution protocol

**目标**：引入 core 级运行协议和异步执行抽象。

**改动点**：

| 文件 | 改动 |
|------|------|
| `src/metaharness/sdk/run_contracts.py` 或 `src/metaharness/sdk/execution.py` | 新增 RunPlanProtocol、RunArtifactProtocol、EnvironmentReportProtocol、ValidationOutcomeProtocol、EvidenceBundleProtocol |
| `src/metaharness/sdk/execution.py` | 新增文件：ExecutionStatus enum、JobHandle、PollingStrategy、AsyncExecutorProtocol、FibonacciPollingStrategy |
| `src/metaharness/sdk/runtime.py` | 为未来 execution service 预留正式注入面（如 job runner / evidence emitter） |

**依赖**：Phase 0

**验证**：
- Extension 的具体 RunPlan/RunArtifact/ValidationOutcome 类型满足 Protocol（structural subtyping 测试）
- FibonacciPollingStrategy 单元测试（验证延迟序列正确、上限 60s、总超时 600s）
- 执行事件由 execution service / job layer 发布，而不是由 `commit_graph()` 发布
- 现有测试不受影响（Protocol 不要求继承）

**预计影响**：新增 1-2 个文件，修改 1 个文件，约 150 行

---

### Phase 2：Run-level governance

**目标**：让 domain validation evidence 进入 safety pipeline 的正规评估路径。

**改动点**：

| 文件 | 改动 |
|------|------|
| `src/metaharness/safety/gates.py` | SafetyGate 基类增加 `evaluate_promotion(promotion) -> GateResult` 默认实现 |
| `src/metaharness/safety/pipeline.py` | evaluate_graph_promotion 在 reviewer 后遍历 gates 的 evaluate_promotion |
| `src/metaharness/components/policy.py` | PolicyDecision 扩展为 allow/defer/reject tri-state |
| `src/metaharness/core/models.py` | 新增 ResourceQuota 类型 + deferred candidate 状态所需事件/记录 |

**依赖**：Phase 1

**验证**：
- 新增测试：evaluate_graph_promotion 经过 gate chain（不只是 reviewer）
- 新增测试：DomainValidationGate 能拒绝 promotion
- 新增测试：defer 决策不 commit、不 rejected、会产出 `CANDIDATE_DEFERRED` 事件
- 新增测试：deferred candidate 可被再次审查并最终 allow/reject
- 现有测试不受影响（gate 默认 evaluate_promotion 返回 ALLOW）

**预计影响**：修改 4 个文件，约 140 行

---

### Phase 3：Durable evidence & provenance

**目标**：让 session/audit/checkpoint 数据可持久化和可恢复。

**改动点**：

| 文件 | 改动 |
|------|------|
| `src/metaharness/observability/events.py` | 新增 FileSessionStore（JSONL 后端） |
| `src/metaharness/provenance/artifacts.py` | 新增文件：scientific artifact lineage schema 和标准 relation types |
| `src/metaharness/provenance/artifact_store.py`（或等价位置） | 新增 ArtifactSnapshotStore，保存 RunArtifact / ValidationOutcome / EvidenceBundle 快照 |
| `src/metaharness/hotreload/checkpoint.py` | 仅在需要时与 ArtifactSnapshotStore 建立引用，不直接混存 artifact payload |

**依赖**：Phase 0（SessionEventType 执行事件）

**验证**：
- FileSessionStore 读写一致（append → get_events → latest_checkpoint_index）
- ArtifactSnapshotStore 能独立保存/读取 run artifacts
- hot-reload checkpoint 与 artifact snapshot 边界清晰：前者恢复 component state，后者恢复运行证据引用
- Scientific artifact lineage 表达完整的 provenance chain
- 现有 InMemorySessionStore 测试不受影响

**预计影响**：新增 2 个文件，修改 2 个文件，约 220 行

---

### Phase 4：Optimizer & study support

**目标**：先让 optimizer 支持领域级 payload 传递；多目标优化是否进入 core，留待 extension 验证后再决定。

**改动点**：

| 文件 | 改动 |
|------|------|
| `src/metaharness/components/optimizer.py` | 利用 `MutationProposal.domain_payload` 打通 graph proposal 与 domain proposal 的桥接 |
| `src/metaharness/core/mutation.py` | 确认 `domain_payload` 在 submit / serialize / replay 路径中保持稳定 |
| `src/metaharness/core/models.py` / `ProposalEvaluation` 相关位置 | 确保 evidence metrics 可承载多目标信息 |

**依赖**：Phase 0（domain_payload）

**验证**：
- `domain_payload` 在 optimizer → mutation submitter → replay 路径中保持不丢失
- Extension 可在不修改 core Pareto API 的前提下，自行实现多目标评分
- 现有 optimizer 测试不受影响

**预计影响**：修改 2-3 个文件，约 80-120 行

**备注**：
- `MultiObjectiveScore`、`optimizer/pareto.py`、`propose_domain()` 不再作为 v0.2 的确定性 core 交付项
- 若未来 2+ extension 独立需要 Pareto/frontier，再进入 core roadmap

---

### Phase 5：Control-plane enhancements（远期）

**目标**：根据 extension 实际需求引入控制面对象。

**候选改动**：
- Template lifecycle（如果 AI4PDE 验证了通用性）
- Invariant engine（如果多个 extension 有声明式不变量需求）
- Approval routing（如果有跨 extension 的审批流需求）
- Budget ledger authority（如果 BudgetState 需要从附属变权威）

**依赖**：Phase 2-4 完成后评估
**预计影响**：待定

---

### Phase 依赖图

```
Phase 0 (模型增量)
  ├──→ Phase 1 (Run contracts & execution)
  │       └──→ Phase 2 (Run-level governance)
  │               └──→ Phase 5 (Control-plane, 远期)
  ├──→ Phase 3 (Durable evidence)  ←── 也可与 Phase 1 并行
  └──→ Phase 4 (Optimizer)         ←── 只依赖 Phase 0
```

Phase 1 和 Phase 3 可并行推进。Phase 4 独立于 Phase 1-3，可先行。
Phase 2 依赖 Phase 1。Phase 5 在 Phase 2-4 完成后再评估。

### 与现有 strengthening plan 的对齐

本路线图不是替代现有 strengthening plan，而是对其做 **run-oriented 能力收敛**。
两者关注点不同：

- **strengthening plan**：以当前 core strengthening 和 `nektar` / `ai4pde` 迁移为主线，
  强调 graph lifecycle、promotion authority、evidence flow、protected semantics、hot reload 治理
- **本路线图**：以 6 个 extension + QCompute 的共性需求为主线，强调 run-oriented contracts、
  execution service、run-level governance、durable evidence、optimizer dual-layer

两者的 phase 可做如下对应：

| 本路线图 | strengthening plan | 对齐关系 |
|---------|--------------------|---------|
| Phase 0 | Phase 1a | 都是纯增量的数据模型扩展，为后续行为变更做准备 |
| Phase 1 | Phase 1b + Phase 2（前半） | 都在把 core 从静态 graph 语义推进到可执行的运行/治理语义 |
| Phase 2 | Phase 2（后半） | 都在强化 safety/policy 作为 authority point |
| Phase 3 | Phase 3 | 都聚焦 evidence / provenance / session flow 的持久化与统一 |
| Phase 4 | （新增） | 本路线图新增的 optimizer/domain-study 支持，现有 strengthening plan 未显式覆盖 |
| Phase 5 | Phase 5 + Phase 6（远期） | 都属于 control-plane / hot reload / control object 的远期增强 |

为避免两份文档产生冲突，应采用以下解释原则：

1. **若涉及 graph promotion / protected components / hot reload 基础设施**，以 strengthening plan 为主
2. **若涉及 run-oriented contracts / execution lifecycle / domain evidence governance**，以本路线图为主
3. **若某一改进同时出现在两份文档中**，优先采用 strengthening plan 的已有实现顺序，
   再用本路线图补充其 run-oriented 语义边界
4. **Phase 4（optimizer dual-layer）是本路线图新增项**，可在 strengthening plan 的
   Phase 3 完成后独立推进，不要求等待其远期 control-plane 主题落地

因此，建议将本路线图视为：**对 strengthening plan 的专题补充文档**，
而不是新的替代性总计划。

---

## 6. 风险评估

| Phase | 主要风险 | 缓解策略 |
|-------|---------|---------|
| 0 | 无（纯增量） | 所有新字段有默认值 |
| 1 | Run contracts 设计过早过重，束缚 extension | 用 Protocol（structural typing）而非基类；extension 自由定义具体类型 |
| 1 | AsyncExecutorProtocol 过于贴近量子/HPC | 保持接口最小（submit/poll/cancel/await），不含领域语义 |
| 2 | Gate chain 扩展导致 evaluate_graph_promotion 变慢 | 默认 gate 的 evaluate_promotion 直接返回 ALLOW，开销接近零 |
| 2 | Tri-state policy 增加治理复杂度 | `defer` 只在显式配置时生效，并补齐 deferred candidate 生命周期 |
| 3 | FileSessionStore 的 schema 演进问题 | JSONL 是 append-only，schema 变更只需新加字段 |
| 3 | artifact snapshot 与 component checkpoint 混淆 | 明确拆分两套机制：state rollback vs evidence persistence |
| 4 | 过早把 Pareto / 多目标优化 core 化 | v0.2 不直接 core 化，先由 extension 验证 |
| 5 | 控制面对象与外部 agent 编排系统重叠 | 只在 2+ extension 独立验证需求后才实施 |

### 向后兼容策略

每个 phase 遵循：
1. 新增字段有默认值——旧代码不需要改动
2. 新增 Protocol 不要求继承——旧组件不需要实现新接口
3. 新增方法有默认实现——旧 gate/reviewer 不需要改动
4. 每个 phase 完成后，运行现有 nektar/ai4pde/abacus 测试确认无破坏

---

## 7. 验证方案

### 7.1 Core 验证

每个 phase 完成后运行：
- `pytest tests/` 全量测试
- 新增 invariant 测试：确认新的 core 抽象不破坏现有行为
- Property-based 测试（hypothesis）：对新的状态机/协议做随机输入验证

### 7.2 Extension 验证

每个 phase 完成后，确认以下 extension 测试不受影响：
- `pytest tests/test_metaharness_nektar_*.py`
- `pytest tests/test_metaharness_ai4pde_*.py`
- `pytest tests/test_metaharness_abacus_*.py`

### 7.3 端到端验证

Phase 1-2 完成后，用一个最小 extension 做 smoke path：
1. boot → 注册带 AsyncExecutorProtocol 的组件
2. execution service submit → poll → collect result → 验证 TASK_* 事件发布
3. validation outcome → evaluate_graph_promotion → gate reject → 验证 promotion 失败
4. validation outcome → defer → 验证 `CANDIDATE_DEFERRED` 与再审查路径
5. validation outcome → gate allow → commit → 验证 durable evidence 可查询

### 7.4 交叉验证

报告完成后，核对：
- 6 extension 的 gap 是否都被覆盖（逐条对照 `MHE-core-improvement.md`）
- QCompute 的 7 维度分析是否都有对应改进方案
- 每个 phase 的改动点是否与实际代码路径匹配
