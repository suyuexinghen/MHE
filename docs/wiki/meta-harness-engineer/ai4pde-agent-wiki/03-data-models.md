# 03. 数据模型与持久化

## 3.1 为什么数据模型是核心

`AI4PDE Agent` 的关键不只是“能不能调用求解器”，而是是否能把以下对象结构化：

- PDE 任务
- team runtime 状态
- worker task
- mailbox 协议消息
- workflow graph version
- mutation proposal
- validation result
- scientific evidence bundle
- asset / template / failure memory

只有这些对象成为正式模型，系统才真正具备：

- 可协作
- 可追溯
- 可回放
- 可回滚
- 可演化

---

## 3.2 数据模型分层

建议将 AI4PDE 数据模型分成五层：

```text
L1 任务层
  - PDETask
  - PDEWorkerTask

L2 协作层
  - PDETeamFile
  - PDEMailboxMessage

L3 工作流层
  - WorkflowGraphVersion
  - WorkflowNode
  - MutationProposal

L4 验证证据层
  - ValidationResult
  - ScientificEvidenceBundle
  - ProvenanceRecord

L5 资产层
  - PDETemplate
  - FailurePattern
  - DeadEndRecord
  - EvaluationSnapshot
```

---

## 3.3 任务层

## 3.3.1 `PDETask`

表示一次完整的 AI4PDE 科学任务。

建议字段：

```text
PDETask
  - task_id
  - goal
  - problem_type: Literal["forward", "inverse", "design", "surrogate"]
  - physics_spec
  - geometry_spec
  - data_spec
  - deliverables
  - budget
  - risk_level
  - required_evidence
  - graph_version_id
  - status
  - created_at
  - updated_at
```

### 关键子结构

#### `physics_spec`

保存：

- PDE type
- constitutive law
- coefficients
- BC / IC
- conservation constraints
- dimensionality
- stationary / transient

#### `geometry_spec`

保存：

- representation type
- source path
- preprocessing hints
- mesh / point-cloud / SDF metadata

#### `data_spec`

保存：

- simulation data refs
- experiment data refs
- sparse observation refs
- noise level
- supervision mode

> 任务生命周期的完整流程见 [02-runtime-flow.md](02-runtime-flow.md) 第 2.4 节。

---

## 3.3.2 `PDEWorkerTask`

表示 team runtime 中一个可分配给具体 worker 的子任务。

建议字段：

```text
PDEWorkerTask
  - task_id
  - parent_task_id
  - subject
  - description
  - role_hint
  - status
  - owner
  - blocked_by
  - blocks
  - priority
  - physics_domain
  - cost_level
  - required_validators
  - required_evidence
  - candidate_capabilities
  - retry_policy
  - artifact_refs
```

### 与普通任务的区别

增加了：

- `role_hint`
- `physics_domain`
- `required_validators`
- `required_evidence`
- `candidate_capabilities`

这些字段使 task list 不只是工作队列，也是 PDE 协作语义载体。

---

## 3.4 协作层

## 3.4.1 `PDETeamFile`

表示一次团队运行的状态镜像。

建议字段：

```text
PDETeamFile
  - team_name
  - lead_worker_id
  - backend
  - is_active
  - graph_version_id
  - worktree_path
  - allowed_paths
  - members[]
  - created_at
  - updated_at
```

### `members[]`

每个成员建议包含：

- `worker_id`
- `worker_name`
- `role`
- `backend_ref`
- `is_active`
- `is_idle`
- `current_task_id`
- `last_heartbeat_at`
- `color`（若需要 UI）

---

## 3.4.2 `PDEMailboxMessage`

表示跨 worker / coordinator / meta layer 的异步消息。

建议字段：

```text
PDEMailboxMessage
  - message_id
  - team_name
  - sender_id
  - recipient
  - message_type
  - priority: Literal["low", "normal", "high", "critical"] = "normal"    # 消息处理优先级，failure_report 和 shutdown_request 默认 critical
  - summary
  - payload
  - read_state
  - created_at
```

### `message_type` 建议枚举

- `task_assignment`
- `idle_notification`
- `failure_report`
- `approval_request`
- `approval_response`
- `shutdown_request`
- `shutdown_response`
- `candidate_graph_request`
- `candidate_graph_result`
- `candidate_change_notice`

### `payload` 特点

- 普通消息可自由文本
- 控制消息必须结构化
- 与 backend 无关

---

## 3.5 工作流层

## 3.5.1 `WorkflowNode`

表示工作流图中的单个执行节点。

建议字段：

```text
WorkflowNode
  - node_id
  - objective
  - role_binding
  - dependencies
  - inputs
  - expected_outputs
  - candidate_capabilities
  - retry_policy
  - cost_hint
  - validator_hooks
```

这与普通 task 的区别是：

- 更接近执行图节点
- 对 solver / validator / reference capability 绑定更强

---

## 3.5.2 `WorkflowGraphVersion`

这是 AI4PDE 最重要的结构化对象之一。

建议字段：

```text
WorkflowGraphVersion
  - graph_version_id
  - parent_version_id
  - task_family
  - template_id
  - nodes[]
  - contracts
  - active_slots
  - mutation_summary
  - status
  - rollback_target
  - created_at
```

### 关键意义

它回答：

- 当前任务是在哪个图版本上运行的？
- 它从哪个版本演化而来？
- 若失败，应回到哪个版本？

### `nodes[]` 说明

`nodes[]` 是 `WorkflowNode` 引用数组，通过 `node_id` 关联，而非内联对象。

### `contracts` 子结构

| 字段 | 类型 | 说明 |
|---|---|---|
| `input_schema` | `JSON Schema` | 输入端口契约 |
| `output_schema` | `JSON Schema` | 输出端口契约 |
| `event_schema` | `JSON Schema \| None` | 事件端口契约（可选） |
| `side_effects` | `list[str]` | 声明的副作用列表 |

### `status` 建议值

- `active`
- `candidate`
- `shadow`
- `stable`
- `rolled_back`
- `retired`

> 图版本化原则与观察窗口语义见 [04-governance-and-observability.md](04-governance-and-observability.md) 第 4.6 节。

---

## 3.5.3 `MutationProposal`

表示一次元优化层提出的变更建议。

建议字段：

```text
MutationProposal
  - proposal_id
  - proposal_type
  - target_slots
  - source_graph_version
  - candidate_graph_version
  - expected_gain
  - risk_level
  - evidence_basis
  - policy_status
  - evaluation_status
  - created_at
```

### `proposal_type` 建议枚举

- `parameter_tuning`
- `graph_rewire`
- `template_instantiation`
- `bounded_synthesis`
- `hot_reload`

### `policy_status`

- `pending`
- `allowed`
- `allowed_with_constraints`
- `denied`
- `escalated`

---

## 3.6 验证与证据层

## 3.6.1 `ValidationResult`

表示一次验证链的输出。

建议字段：

```text
ValidationResult
  - validation_id
  - task_id
  - graph_version_id
  - status
  - confidence
  - structural_checks
  - physics_checks
  - reference_checks
  - violations
  - next_action
  - evidence_refs
  - created_at
```

### `next_action`

- `DELIVER`
- `RETRY`
- `SUBSTITUTE`
- `REPLAN`
- `HOT_RELOAD`
- `ESCALATE`

---

## 3.6.2 `ScientificEvidenceBundle`

表示最小科学证据包。

建议字段：

```text
ScientificEvidenceBundle
  - bundle_id
  - task_id
  - graph_version_id
  - template_id
  - solver_config
  - residual_refs
  - bc_ic_refs
  - conservation_refs
  - reference_comparison_refs
  - telemetry_refs
  - checkpoint_refs
  - provenance_refs
  - validation_summary
```

### 为什么单独建模

因为 AI4PDE 的交付对象不应只是文本，而应是：

- 结果
- 证据
- 溯源
- 图版本

的组合包。

> 验证闭环与回退策略见 [02-runtime-flow.md](02-runtime-flow.md) 第 2.9–2.10 节。

---

## 3.6.3 `ProvenanceRecord`

表示某个关键产物的来源。

建议字段：

```text
ProvenanceRecord
  - provenance_id
  - entity_id
  - generated_by
  - used_entities
  - graph_version_id
  - template_id
  - capability_id
  - tool_version
  - input_hash
  - output_hash
  - started_at
  - ended_at
```

这使结果具备”谁、何时、在何图版本、用何能力生成”的完整追踪能力。

> `capability_id` 对应 Capability Registry 中的注册能力 ID，或运行时 slot 名称（如 `PINNStrongExecutor`、`PhysicsValidator`）。

---

## 3.7 资产层

## 3.7.1 `PDETemplate`

表示一个可实例化的 PDE workflow skeleton。

建议字段：

```text
PDETemplate
  - template_id
  - name
  - task_family
  - supported_slots
  - fixed_contracts
  - variable_params
  - required_validators
  - risk_level
  - reproducibility_requirements
  - migration_hooks
  - version
  - status
  - benchmark_profile: BenchmarkProfile | None = None    # 模板性能基准配置，用于评估实例化后的效果是否达到预期
```

### `status`

- `draft`
- `candidate`
- `stable`
- `degraded`
- `retired`

> 模板库的完整目录与状态流转见 [05-template-library-and-self-growth.md](05-template-library-and-self-growth.md)。

---

## 3.7.2 `FailurePattern`

记录可复用的失败模式。

建议字段：

```text
FailurePattern
  - failure_id
  - task_family
  - graph_signature
  - symptoms
  - likely_causes
  - recommended_patches
  - evidence_refs
  - first_seen_at
  - last_seen_at
  - hit_count
```

作用：

- 给 Planner / Optimizer 提前预警
- 避免重复进入高成本错误路径

---

## 3.7.3 `DeadEndRecord`

专门记录“已知不该继续探索”的 proposal family 或 graph family。

建议字段：

```text
DeadEndRecord
  - dead_end_id
  - proposal_family
  - graph_signature
  - denial_reason
  - evidence_basis
  - policy_ref
  - created_at
```

它与 `FailurePattern` 的区别是：

- `FailurePattern` 侧重运行失败
- `DeadEndRecord` 侧重演化层拒绝或回滚的坏变更路径

---

## 3.7.4 `EvaluationSnapshot`

表示某个 graph / template / proposal 的多目标评估结果。

建议字段：

```text
EvaluationSnapshot
  - snapshot_id
  - graph_version_id
  - template_id
  - metrics
  - pareto_rank
  - benchmark_refs
  - created_at
```

### `metrics`

可包含：

- accuracy
- residual quality
- latency
- cost
- reproducibility
- robustness

---

## 3.8 运行时支撑模型

以下模型支撑热加载、预算管理与审批流程等运行时机制。

---

### `CheckpointSnapshot`

保存热加载和图版本切换时的状态快照。

| 字段 | 类型 | 说明 |
|---|---|---|
| `checkpoint_id` | `str` | 唯一标识 |
| `graph_version_id` | `str` | 所属图版本 |
| `task_id` | `str \| None` | 关联任务（如适用） |
| `snapshot_type` | `Literal["pre_cutover", "pre_hot_reload", "periodic", "manual"]` | 快照类型 |
| `component_states` | `dict[str, bytes]` | slot_name → 序列化状态 |
| `solver_checkpoints` | `list[str]` | solver checkpoint URI 列表 |
| `evidence_refs` | `list[str]` | 关联证据 ID 列表 |
| `created_at` | `datetime` | 创建时间 |

---

### `BudgetRecord`

保存预算分配与消耗记录。

| 字段 | 类型 | 说明 |
|---|---|---|
| `budget_id` | `str` | 唯一标识 |
| `owner_type` | `Literal["task", "team", "session"]` | 预算归属层级 |
| `owner_id` | `str` | 归属对象 ID |
| `dimensions` | `BudgetDimensions` | 各维度配额（见下） |
| `spent` | `BudgetDimensions` | 各维度已消耗 |
| `status` | `Literal["active", "exhausted", "revoked"]` | 预算状态 |

`BudgetDimensions` 子结构：

| 字段 | 类型 | 说明 |
|---|---|---|
| `gpu_hours` | `float` | GPU 时间配额 |
| `token_count` | `int` | LLM token 数配额 |
| `walltime_seconds` | `int` | 总运行时长配额 |
| `hpc_core_hours` | `float` | HPC 核心时间配额 |
| `batch_count` | `int` | 最大批次数 |

---

### `ApprovalRecord`

保存审批流程记录。

| 字段 | 类型 | 说明 |
|---|---|---|
| `approval_id` | `str` | 唯一标识 |
| `request_type` | `Literal["tool_access", "budget_extension", "hpc_submit", "graph_cutover", "template_instantiate", "validator_change", "hot_reload"]` | 审批类型 |
| `risk_level` | `Literal["green", "yellow", "red"]` | 风险等级 |
| `requester_id` | `str` | 发起者 worker_id |
| `target_description` | `str` | 审批对象描述 |
| `status` | `Literal["pending", "approved", "denied", "escalated"]` | 审批状态 |
| `decider` | `str \| None` | 决策者（coordinator / policy_engine / human） |
| `decision_reason` | `str \| None` | 决策理由 |
| `created_at` | `datetime` | 创建时间 |
| `decided_at` | `datetime \| None` | 决策时间 |

---

## 3.9 持久化建议

## 3.9.1 文件层次

建议以目录分层持久化：

```text
ai4pde/
├── teams/
│   └── <team>.json
├── tasks/
│   └── <task>.json
├── inboxes/
│   └── <worker>.jsonl
├── graphs/
│   └── <graph_version>.json
├── proposals/
│   └── <proposal>.json
├── evidence/
│   └── <bundle>.json
├── provenance/
│   └── <prov>.json
├── templates/
│   └── <template>.json
├── failures/
│   └── <failure>.json
└── checkpoints/
    └── ...
```

### 3.9.2 初期实现建议

v0.x 可以先采用：

- JSON / JSONL 文件存储
- 文件锁
- 可人工 inspect 的目录结构

这样与现有本地 CLI 场景一致，便于调试。

后续再逐步演化到：

- SQLite
- embedded KV
- remote event store

---

## 3.10 模型间关系

可概括为：

```text
PDETask
  ├─ owns PDEWorkerTask[]
  ├─ runs on WorkflowGraphVersion
  ├─ produces ValidationResult
  ├─ produces ScientificEvidenceBundle
  └─ materializes ProvenanceRecord[]

WorkflowGraphVersion
  ├─ may come from PDETemplate
  ├─ may be produced by MutationProposal
  └─ may be compared by EvaluationSnapshot

FailurePattern / DeadEndRecord
  └─ feed back into Planner / Optimizer
```

---

## 3.11 为什么这些模型重要

这些模型让 AI4PDE 不再只是“会启动求解器的对话系统”，而成为：

- 有 team 语义的协作系统
- 有 graph version 语义的演化系统
- 有 evidence bundle 语义的科学交付系统
- 有 failure / dead-end 语义的长期学习系统

这正是其区别于普通 agent 的根本所在。
