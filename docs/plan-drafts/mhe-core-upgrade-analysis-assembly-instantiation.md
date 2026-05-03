# MHE Core 升级分析报告：从图运行时到带物理记忆的选择环境

## 摘要

本文合并两份关于 `Harness设计原则-组装理论和抽象谬误-优化版.md` 的分析，并对照 MHE core 当前实现，提出一套面向框架升级的设计建议。

核心判断是：MHE core 已经具备候选图、组件注册、生命周期、图验证、安全门、执行证据、审计日志和会话事件等重要基础，其中部分服务支持 append-only 或文件持久化，因此并不需要推倒重写。真正的升级方向，是把当前“可验证的图运行时”进一步提升为“带物理记忆、谱系治理、选择压力和实例化边界的 harness framework”。

换言之，MHE 已经能记录许多“发生了什么”的事件和证据，也已有通用 provenance 与 artifact parent chain；但还没有形成统一的 assembly-governance 层来回答“复杂能力如何被组装出来”“它被复用了多少次”“它是否经过真实世界实例化验证”。这正对应设计原则文档中的两条主线：

- 组装理论要求复杂能力必须有历史、谱系、拷贝数和选择压力。
- 抽象谬误要求 agent 的计划、声明、模拟和真实执行之间必须有清晰边界。

本文建议优先新增 Assembly Ledger、Copy Count Index、持久化依赖 DAG、Simulation/Instantiation 执行模式、Instantiation Gateway、Selection Pressure Gates 和 Assembly Metrics Dashboard。这样可以在不破坏现有 core 架构的前提下，为 MHE 增加长期演化能力和更强的工程诚实性。

## 分析依据

本报告参考以下设计与实现证据：

- 设计原则文档：`docs/plan-drafts/Harness设计原则-组装理论和抽象谬误-优化版.md`
- 图快照模型：`src/metaharness/core/models.py:126`
- 组件注册器：`src/metaharness/sdk/registry.py:29`
- boot 依赖排序：`src/metaharness/sdk/dependency.py:38`
- 图提交流程：`src/metaharness/core/boot.py:927`
- 图版本存储：`src/metaharness/core/graph_versions.py:39`
- 图语义验证：`src/metaharness/core/validators.py:87`
- 生命周期跟踪：`src/metaharness/core/lifecycle_tracker.py:27`
- 执行证据记录：`src/metaharness/core/execution.py:273`
- 审计日志：`src/metaharness/provenance/audit_log.py:40`
- PROV 风格证据图：`src/metaharness/provenance/evidence.py:65`
- provenance 查询辅助：`src/metaharness/provenance/query.py:12`
- scientific artifact lineage helper：`src/metaharness/provenance/artifacts.py:8`
- artifact snapshot store：`src/metaharness/provenance/artifact_store.py:25`
- session event store：`src/metaharness/observability/events.py:19`
- metrics registry：`src/metaharness/observability/metrics.py:117`
- histogram summary：`src/metaharness/observability/metrics.py:71`
- extension 局部执行模式示例：`src/metaharness_ext/qcompute/types.py:6`
- safety pipeline：`src/metaharness/safety/pipeline.py:96`
- post-commit auto rollback：`src/metaharness/safety/auto_rollback.py:38`

## 总体结论

MHE core 当前最接近的是一个“可审计、可回滚、可验证的 graph/runtime orchestrator”。它已经有很多成为成熟 harness 的底座：

- 候选图和活跃图的快照模型。
- 组件注册、slot/capability 索引和 pending zone。
- boot 阶段的拓扑排序和依赖检查。
- graph promotion 过程中的语义验证、安全门和回滚目标。
- append-only session events、artifact snapshots、PROV graph 和 Merkle-anchored audit log；`AuditLog` 和 artifact/session stores 都已有文件持久化实现或接口，但部分默认实例仍是内存态。
- `SafetyPipeline` 相关基础包括沙箱验证、AB 影子测试、策略否决门，以及独立的提交后健康检查/自动回滚机制。
- 组件 runtime phase 的显式转移检查，当前 `LifecycleTracker` 覆盖 8 个 runtime 状态。

但从设计原则文档的角度看，MHE core 还缺少三个跨 core 的一等治理概念：

- **统一组装历史**：复杂图、组件、模板或策略从哪些基础构件递归组合而来；这不同于现有 artifact/event provenance。
- **复用强度**：组件、图、模板、策略被实例化、调用、依赖和跨版本复用的次数。
- **统一实例化边界**：agent 的计划、模拟、dry-run、声明和真实外部副作用之间的可审计边界；这不同于各 extension 局部 execution mode。

因此，MHE 的升级目标不应是“让单个 agent 更聪明”，而是让 core 成为一个可持续选择、复制、晋升、降级和审计复杂能力的环境。

后续设计应明确三层边界：`GraphSnapshot` 负责 runtime connection graph，现有 provenance 负责通用证据派生与 artifact lineage，新增 `AssemblyLedger` 负责组装治理、复用统计和选择压力。

## 当前 MHE 与设计原则的对齐情况

| 设计原则方向 | MHE 已有基础 | 当前成熟度 | 说明 |
| --- | --- | --- | --- |
| 物理记忆 | `SessionStore`、`AuditLog`、`ArtifactSnapshotStore`、`ProvGraph` | 中等到较强 | 已有事件、证据和 artifact 记录基础，`AuditLog` 可持久化为 JSONL，artifact/session stores 也有文件实现或接口；但默认实例不少仍是内存态，且还没有专门的 assembly lineage store。 |
| 依赖 DAG | `resolve_boot_order()`、`GraphSnapshot`、`GraphVersionStore` | 中等 | graph snapshot 保存 runtime connection graph，`GraphVersionStore` 保存 candidate/active/rollback/archived graph；但 boot/component dependency DAG 主要用于排序，未成为可查询的一等历史对象。 |
| 组件注册 | `ComponentRegistry` | 较强 | 支持 staged registration、slot/capability 索引和 pending commit，但没有 copy count 或 selection lifecycle。 |
| 生命周期 | `LifecycleTracker` | 中等 | 能约束 8 个 runtime phase，但不是持久化的组件生态生命周期，也不记录 exploratory/infrastructure/deprecated/graveyard 等长期选择状态。 |
| 图验证 | `validate_graph()` | 较强 | 能检查未知组件、端口、payload、必需输入、环、orphan、protected boundary 等结构语义问题。 |
| 安全门 | `SafetyPipeline`、`AutoRollback` | 较强 | graph promotion 可进入 gate/reviewer 流程，另有提交后健康检查触发的 auto rollback；但还没有 assembly-health gate。 |
| 执行证据 | `ExecutionEvidenceRecorder` | 较强 | 能保存 run artifact、validation outcome、evidence bundle，并关联 candidate/graph version。 |
| 审计完整性 | `AuditLog` | 较强 | append-only 且 Merkle anchored，适合作为不可变证据层。 |
| 模拟/实例化隔离 | 分散存在 | 较弱 | candidate/active、dry-run/validation 的语义存在于流程中，部分 extension 也有局部执行模式；但 core 缺少贯穿 session/audit/artifact/safety 的统一 execution mode。 |
| 转导透明度 | 基础不足 | 较弱 | 没有系统记录 raw input 如何变成符号、符号如何变成动作。 |
| 选择压力 | 基础不足 | 较弱 | 没有基于复用、验证、成本、失败率的晋升/降级/淘汰机制。 |
| 量化 dashboard | `MetricsRegistry`、`Histogram.summary()` | 较弱 | 已有 counter/gauge/histogram 和 mean/min/max/p50/p95 基础统计；但设计文档中的 assembly/instantiation 指标尚未成为 core metrics。 |

## 核心差距

### 组装层差距

设计原则文档要求 harness 能回答：“这个复杂能力是如何被制造出来的？”当前 MHE 只能部分回答这个问题。

主要差距包括：

- **缺少统一 Assembly Ledger**：当前 MHE 已有 `wasDerivedFrom`、artifact parent snapshot 和 scientific artifact lineage 等局部谱系能力，但它们更偏 artifact/event evidence；尚未形成覆盖 graph/component/template/strategy 的组装治理账本。
- **缺少 copy count**：registry 知道有哪些组件，但不知道组件被实例化、调用、依赖、复用、验证了多少次。
- **缺少 assembly index**：系统没有计算组件或图从基础原子到复杂产物的依赖路径深度。
- **缺少持久化 boot dependency DAG**：`resolve_boot_order()` 能构建依赖关系并排序；`GraphVersionStore` 已有 candidate/active/rollback/archived graph 管理基础，但不保存组件依赖 DAG 结构本身，因此无法查询组件间依赖拓扑或做跨版本依赖比较。
- **缺少 selection lifecycle**：`LifecycleTracker` 记录 DISCOVERED、VALIDATED_STATIC、ASSEMBLED、VALIDATED_DYNAMIC、ACTIVATED、COMMITTED、SUSPENDED、FAILED 这 8 个 runtime phase，不记录组件生态位状态，例如 exploratory、active、infrastructure、deprecated、graveyard。
- **缺少 Boltzmann-brain 检测**：高复杂度、低复用、无谱系的产物不会自动触发隔离或人工审查。

### 实例化层差距

设计原则文档要求 harness 能回答：“agent 说它做了某事，真实世界是否真的发生了对应变化？”当前 MHE 也只能部分回答这个问题。

主要差距包括：

- **缺少 core 统一执行模式**：部分 extension 已有局部模式，例如 QCompute 的 `simulate/run/hybrid`；但 core 没有统一字段区分 simulation、dry-run、staged、instantiated、externally verified，并传播到 session/audit/artifact/safety 层。
- **缺少声明-行动对账机制**：无法系统查询“agent 声称完成 X”是否有外部日志、文件变更、API 回执或验证器证据。
- **缺少转导记录**：没有系统记录原始输入如何被解释为符号，符号输出如何被解释为动作。
- **缺少制图者归因**：没有显式记录是人类、业务规则、传感器、外部验证器还是环境反馈赋予了某个符号映射的意义。
- **缺少因果闭环追踪**：执行结果能保存为 evidence，但没有系统反向链接到 originating decision、plan、claim 或 assembly record。

### 量化框架差距

设计原则文档列出的指标目前尚未成为 MHE core 的可计算指标：

- 组件复用率。
- 组装指数。
- 谱系完整率。
- 历史折叠度。
- 生成不可能性指数。
- 选择压强度。
- 跨环境组装一致性。
- 制图者显式度。
- 实例化隔离健全度。
- 因果闭环率。
- 转导透明度。
- 语义漂移指数。
- 物理主义通过率。

这意味着 MHE 目前的观测能力更偏运行时事件、基础统计和证据保存，还没有形成“复杂能力生态系统”的健康度评价。现有 `MetricsRegistry` 与 `Histogram.summary()` 可作为输出底座，但缺少面向组装理论和实例化边界的计算逻辑。

## 合并后的升级框架

### Assembly Ledger

新增一个专门的组装账本，而不是把所有字段直接塞进 `RegisteredComponent`。推荐引入 companion model：

```python
class AssemblyRecord(BaseModel):
    artifact_id: str
    artifact_kind: str
    version: str | None = None
    parent_refs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    assembly_context: dict[str, Any] = Field(default_factory=dict)
    validation_refs: list[str] = Field(default_factory=list)
    graph_version: int | None = None
    candidate_id: str | None = None
```

`artifact_kind` 可覆盖：

- component
- graph
- template
- strategy
- workflow
- evaluator
- execution_plan
- evidence_bundle

这个账本应能回答：

- 当前图从哪些父图、模板或组件变异而来。
- 某个组件是否源自已有组件的组合、复制、参数化或人工新增。
- 某个高阶工作流是否复用了高 copy count 的低阶组件。
- 某个产物是否缺少父组件、验证记录或生成上下文。

设计理由：

- `ComponentRegistry` 应继续负责当前可用组件索引。
- `ProvGraph` 应继续负责通用 evidence/provenance relation。
- `AssemblyLedger` 应专门负责组装理论意义上的谱系、复用和复杂度指标。

### Copy Count Index

新增一个独立的 copy/reuse 指标索引，不建议只用单个 `copy_count` 字段。至少应拆成：

```python
class CopyCountRecord(BaseModel):
    artifact_ref: str
    registered_count: int = 0
    instantiated_count: int = 0
    invoked_count: int = 0
    dependency_count: int = 0
    graph_reuse_count: int = 0
    external_verified_count: int = 0
```

推荐计数事件：

- 组件被注册。
- 组件进入候选图。
- 组件进入 committed graph。
- 组件被其他组件依赖。
- 组件被 executor 调用。
- 组件出现在多个 graph version 中。
- 组件参与的执行被外部证据确认。

这样可以避免把“声明存在一次”和“真实执行一百次”混为一谈。

### 持久化依赖 DAG

当前 `GraphSnapshot` 主要保存 runtime connection graph：nodes 与 edges。建议新增 dependency graph 快照，保存 boot/component dependency DAG。

推荐结构：

```python
class DependencyGraphSnapshot(BaseModel):
    graph_version: int | None = None
    candidate_id: str | None = None
    dependencies: dict[str, list[str]] = Field(default_factory=dict)
    capability_dependencies: dict[str, list[str]] = Field(default_factory=dict)
    produced_by: str = "resolve_boot_order"
```

它与 `GraphSnapshot` 的关系应保持清晰：

- `GraphSnapshot`：运行时连接图，回答组件如何传递 payload。
- `DependencyGraphSnapshot`：组装/激活依赖图，回答组件为什么必须依赖某些父组件。
- `AssemblyRecord`：跨图、跨版本、跨模板的谱系图，回答复杂产物如何演化而来。

这样可以支持 assembly index、跨环境组装一致性、低拷贝关键依赖检测等指标。

### Assembly Index 计算

组装指数不应手动填写，而应由 `AssemblyLedger` 和 dependency DAG 计算。

建议初始定义：

```text
assembly_index(component) = max_depth_from_primitives(component)
assembly_index(graph) = max(assembly_index(node) for node in graph.nodes) + graph_composition_depth
```

其中 primitive 可包括：

- 无父组件的原子工具。
- 外部 API adapter。
- 基础 evaluator。
- 基础 executor。
- 人工标记为 primitive 的 manifest。

需要注意：设计原则文档说“最少递归组合步数”，而工程实现可先用 DAG 最长有效路径近似。后续如果要更严格，可以把 assembly operation 明确建模为 combine、specialize、instantiate、wrap、validate、promote 等操作。

### Simulation 与 Instantiation 边界

这是最重要的升级点。这里的目标不是否认 extension 内已有局部执行模式，而是提供一个 core-wide 标准枚举，让不同 extension 的局部语义能映射到同一套 session、audit、artifact 和 safety 语义上。建议新增统一枚举：

```python
class ExecutionMode(str, Enum):
    SIMULATION = "simulation"
    DRY_RUN = "dry_run"
    STAGED = "staged"
    INSTANTIATED = "instantiated"
    EXTERNALLY_VERIFIED = "externally_verified"
```

这里采用名词形 `SIMULATION` 作为 core 标准名；extension 或旧草案中的 `simulate` / `simulated` 语义可映射到该枚举值。

推荐语义：

- `SIMULATION`：内部推理、计划、预测、草稿、世界模型。
- `DRY_RUN`：执行路径被检查，但不产生真实外部副作用。
- `STAGED`：准备提交或等待审批，尚未确认外部状态变化。
- `INSTANTIATED`：已通过执行网关产生真实副作用。
- `EXTERNALLY_VERIFIED`：真实副作用已被外部日志、文件状态、API 回执、用户确认或验证器确认。

该字段应传播到：

- execution lifecycle event。
- audit payload。
- artifact snapshot metadata。
- graph promotion context。
- safety gate context。
- report/dashboard 查询层。

关键设计修正：`AuditLog` 不应负责拒绝无证据的实例化声明。`AuditLog` 是 append-only evidence layer，应保持不可变记录能力。拒绝、defer 或要求补证据，应发生在 execution gateway、safety gate 或 promotion gate。审计日志可以记录拒绝事件本身，但不应承担业务策略判断。

### Instantiation Gateway

新增统一真实动作网关，用于集中管理所有可能产生外部副作用的动作。

网关职责：

- 接收 action request。
- 记录 originating claim、plan、decision、component、graph version。
- 标记 execution mode。
- 要求真实动作提供 external evidence contract。
- 执行动作或委托 executor。
- 收集外部日志、回执、artifact、状态检查。
- 将结果回写到 session store、artifact store、audit log、assembly ledger。

推荐抽象：

```python
class InstantiationRecord(BaseModel):
    action_id: str
    originating_ref: str | None = None
    execution_mode: ExecutionMode
    target_system: str | None = None
    external_evidence_refs: list[str] = Field(default_factory=list)
    result_ref: str | None = None
    verified: bool = False
```

这样可以支持“声明-行动对账”：

```text
agent_claim -> action_request -> gateway_execution -> external_evidence -> verification_result
```

### 转导与制图者归因

为了落实抽象谬误部分，建议新增 transduction records。

```python
class TransductionRecord(BaseModel):
    record_id: str
    direction: Literal["input", "output"]
    raw_ref: str | None = None
    symbolic_ref: str | None = None
    mapper_ref: str
    cartographer_kind: str
    cartographer_ref: str | None = None
    reversible: bool = False
    confidence: float | None = None
```

`cartographer_kind` 可包括：

- human
- business_rule
- sensor_calibration
- external_validator
- environment_feedback
- tool_schema
- manifest_contract

这个机制的目标不是增加复杂性，而是让 MHE 能回答：

- 输入语义是谁赋予的。
- 输出动作是谁解释并执行的。
- 某个符号是否只是 agent 内部自我赋义。
- 同一物理输入在不同上下文中是否出现语义漂移。

### Selection Pressure Gates

在 `SafetyPipeline` 中增加 assembly-health gate，而不是单独做离线报告。

推荐 gate：

```text
AssemblyHealthGate
- reject: graph has high assembly index, low average copy count, and missing lineage
- defer: critical path includes low-copy unverified component
- warn: graph introduces many new unique components without reuse
- allow: high lineage completeness and sufficient verified reuse
```

关键指标：

- high_ai_low_copy_count
- lineage_completeness
- low_copy_critical_dependencies
- external_verified_ratio
- graph_reuse_score
- impossible_generation_score

它应接入 promotion 流程，而不是只显示在 dashboard 中。这样 selection pressure 才会真正影响系统演化。

### Component Selection Lifecycle

不要直接复用当前 `LifecycleTracker` 来承担选择压力。当前 tracker 适合 runtime phase：discovered、validated、assembled、activated、committed 等。

建议新增持久化生态生命周期：

```python
class SelectionState(str, Enum):
    EXPLORATORY = "exploratory"
    ACTIVE = "active"
    INFRASTRUCTURE = "infrastructure"
    DEPRECATED = "deprecated"
    GRAVEYARD = "graveyard"
```

状态转移依据：

- copy count。
- external verified count。
- failure rate。
- cost/benefit。
- reuse across graph versions。
- human approval。
- replacement availability。

示例规则：

- 新组件默认进入 `EXPLORATORY`。
- 多次验证通过且跨图复用后进入 `ACTIVE`。
- 高复用、低失败率、关键路径稳定后进入 `INFRASTRUCTURE`。
- 长期低复用或存在替代方案进入 `DEPRECATED`。
- 明确不可用、过时或不安全后进入 `GRAVEYARD`。

### Metrics Dashboard

等 Assembly Ledger、Copy Count Index 和 ExecutionMode 落地后，再实现 dashboard。否则 dashboard 只能是估算。

建议首批指标：

| 指标 | 来源 | 用途 |
| --- | --- | --- |
| copy count | Copy Count Index | 判断组件复用强度。 |
| assembly index | Assembly Ledger + Dependency DAG | 判断复杂度历史深度。 |
| lineage completeness | Assembly Ledger | 判断谱系是否完整。 |
| history folding ratio | Assembly Ledger | 判断是否复用已有构件。 |
| low-copy critical dependency count | Dependency DAG + Copy Count Index | 识别关键路径风险。 |
| external verified ratio | Instantiation Gateway | 判断真实执行验证比例。 |
| declaration-action reconciliation rate | Claim/action/evidence chain | 判断行动声明是否可对账。 |
| transduction transparency | Transduction Records | 判断 I/O 映射是否可审计。 |
| selection pressure intensity | Selection Lifecycle | 判断系统是否在筛选而非堆积。 |

建议暴露形式：

- Python service：`AssemblyMetricsService`。
- CLI：`python -m metaharness.cli metrics assembly`。
- JSON 输出：便于 CI、benchmark、报告生成使用。
- Markdown/ASCII 输出：便于人工审阅。

## 分阶段实施路线

本路线吸收较短报告中的 Phase 1–5 结构，同时保留本文对现有 provenance、持久化边界和 core-wide execution mode 的修正。

| 阶段 | 主题 | 核心交付 | 主要收益 |
| --- | --- | --- | --- |
| Phase 1 | 组装账本 + 拷贝计数 | `AssemblyLedger`、`CopyCountIndex`、graph promotion 埋点、`AssemblyHealthGate` WARN 模式 | 建立最小可观测底座。 |
| Phase 2 | 持久化 DAG + 组装指数 | `DependencyGraphSnapshot`、assembly index、lineage completeness | 识别高复杂度低复用风险。 |
| Phase 3 | 模拟/实例化边界 + 执行对账 | core-wide `ExecutionMode`、`InstantiationRecord`、external evidence contract | 防止计划或 dry-run 被误报为真实执行。 |
| Phase 4 | 选择压门 + 组件生命周期 | `AssemblyHealthGate`、`SelectionState`、晋升/降级策略 | 让指标真正影响 graph promotion。 |
| Phase 5 | Metrics Dashboard + 框架化输出 | `AssemblyMetricsService`、metrics CLI、JSON/Markdown 输出 | 支撑 benchmark、报告和运维观测。 |

### Phase 1：组装账本 + 拷贝计数

目标：让 MHE 开始保存组装历史与复用信息。

建议任务：

- 新增 `AssemblyRecord` 和 `AssemblyLedger`。
- 新增 `CopyCountRecord` 和 copy count service。
- 在 component registration、graph candidate creation、graph commit、execution record 中记录基础事件。
- 为 `GraphSnapshot` 或 graph version store 增加 assembly/provenance refs，而不是一次性大改所有模型。
- 以 WARN 模式接入 `AssemblyHealthGate`，只输出风险摘要，不阻塞现有 promotion。
- 添加最小单元测试，验证 graph commit 后能查询组件复用和父组件关系。

交付标准：

- 能查询某个 graph version 使用了哪些组件。
- 能查询某个组件被多少 graph version 复用。
- 能查询某个 candidate graph 的 parent graph/template/component refs。
- 不影响现有 graph validation 和 boot tests。

### Phase 2：持久化 DAG + 组装指数

目标：让 MHE 能识别“高复杂度、低复用、无谱系”的风险产物。

建议任务：

- 持久化 boot dependency DAG。
- 实现 assembly index 近似计算。
- 实现 lineage completeness 和 history folding ratio。
- 实现 impossible generation score 或 high-ai-low-copy detector。
- 在 dashboard service 中输出首批 assembly metrics。

交付标准：

- 给定一个 graph snapshot，能计算 assembly index。
- 给定一个组件，能计算 copy count 分解项。
- 给定一个 graph promotion，能输出 assembly health summary。
- 高 AI、低 C、无 lineage 的 candidate 能被标记为风险。

### Phase 3：模拟/实例化边界 + 执行对账

目标：让 MHE 明确区分计划、模拟、dry-run 和真实执行。

建议任务：

- 新增 `ExecutionMode`。
- 将 execution mode 接入 execution lifecycle、artifact snapshot、audit payload 和 safety context。
- 新增 `InstantiationRecord`。
- 定义 external evidence contract。
- 建立 claim/action/evidence reconciliation 查询。

交付标准：

- 任何真实副作用动作都必须经过 instantiation gateway 或等价封装。
- `INSTANTIATED` 和 `EXTERNALLY_VERIFIED` 事件必须包含 external evidence refs。
- 能查询某个 agent/action claim 是否被外部证据确认。
- 未确认的执行声明不会被 dashboard 计入 verified execution。

### Phase 4：选择压门 + 组件生命周期

目标：让 MHE 不只是堆积组件，而是形成可演化的组件生态。

建议任务：

- 新增 persistent `SelectionState`。
- 新增 `ComponentSelectionLifecycle` service。
- 新增 `AssemblyHealthGate` 接入 `SafetyPipeline`。
- 定义 promotion/deprecation/graveyard 策略。
- 将 selection decisions 写入 audit/session events。

交付标准：

- 高复用、高验证组件可晋升为 infrastructure。
- 长期低复用或高失败率组件可进入 deprecated/graveyard。
- graph promotion 会受到 low-copy critical dependency 的 gate 影响。
- selection decision 可审计、可解释、可回滚。

### Phase 5：Metrics Dashboard + 框架化输出

目标：让 MHE 的“组装健康度”和“实例化诚实度”成为可见框架能力。

建议任务：

- 实现 `AssemblyMetricsService`。
- 增加 metrics CLI。
- 输出 JSON 与 Markdown/ASCII 两种格式。
- 在 benchmark/report workflow 中引用这些指标。
- 将关键指标纳入 docs/wiki 的架构说明。

交付标准：

- 能生成当前 MHE runtime 的 assembly/instantiation dashboard。
- 指标来源可追溯到 ledger、copy count、gateway、audit 和 session events。
- benchmark 报告能引用真实指标，而不是手工判断。

## 原则到 Phase 的追踪矩阵

| 设计原则 | 覆盖阶段 | 实现抓手 |
| --- | --- | --- |
| 物理记忆 | Phase 1, Phase 2 | `AssemblyLedger`、dependency graph snapshot、artifact/session/audit refs。 |
| 递归复用 | Phase 1, Phase 2 | `CopyCountIndex`、assembly index、history folding ratio。 |
| 拷贝数信任 | Phase 1 | copy count 分解项、verified reuse count、low-copy critical dependency 检测。 |
| 选择压 | Phase 4 | `AssemblyHealthGate`、`SelectionState`、promotion/deprecation/graveyard 策略。 |
| 反随机涌现 | Phase 2, Phase 4 | high-AI/low-copy detector、impossible generation score、gate escalation。 |
| 显式制图者 | Phase 3, Phase 5 | `TransductionRecord`、cartographer attribution、dashboard 指标。 |
| 模拟/实例化隔离 | Phase 3 | core-wide `ExecutionMode`、`InstantiationRecord`。 |
| 因果闭环 | Phase 3 | originating claim/decision 到 action/evidence/result 的链路。 |
| 转导透明 | Phase 3, Phase 5 | input/output transduction records、语义漂移指标。 |
| 机制确定性 | Phase 2 | 持久化 dependency DAG、跨版本/跨环境 assembly index 比较。 |
| 反涌现谦逊 | Phase 4 | 对无谱系复杂产物 warn/defer/reject。 |
| 物理主义检验门 | Phase 3 | claim/action/evidence reconciliation、external evidence contract。 |

## 推荐启动顺序

较短报告中的启动顺序适合保留为执行视角，但需要按本文的边界修正为“先观测、再 gate、最后自动化”。

**第一优先级：1–2 周，不破坏现有合约**

- `AssemblyLedger`：新增服务，记录 graph/component/template 的父引用、版本、生成上下文和验证引用。
- `CopyCountIndex`：先在 graph candidate、graph commit、dependency resolution 和 execution evidence 附近做轻量埋点。
- `AssemblyHealthGate`：以 WARN 模式接入 `SafetyPipeline`，只产出 assembly health summary，不阻塞现有推广流程。

**第二优先级：2–4 周，形成 core 语义闭环**

- 持久化 boot/component dependency DAG，并计算 assembly index、lineage completeness 和 high-ai-low-copy 风险。
- 引入 core-wide `ExecutionMode`，把 extension 局部执行模式映射到统一 session/audit/artifact/safety 语义。
- 建立 `InstantiationRecord` 与 claim/action/evidence reconciliation 查询。

**第三优先级：4–6 周，接入治理和报告能力**

- 将 `AssemblyHealthGate` 从 WARN 逐步升级到 DEFER/REJECT，仅用于明确高风险关键路径。
- 新增 `SelectionState` 与 `ComponentSelectionLifecycle`，支持 infrastructure/deprecated/graveyard 治理。
- 实现 `AssemblyMetricsService`、metrics CLI 和 JSON/Markdown dashboard，供 benchmark/report workflow 使用。

## 架构变更摘要

```text
当前 MHE Core                      升级后 MHE Core
─────────────────────────────      ────────────────────────────────
ComponentRegistry                  ComponentRegistry
  (components + indexes)             + CopyCountIndex
                                      + AssemblyLedger refs

GraphSnapshot / GraphVersionStore  GraphSnapshot / GraphVersionStore
  (runtime graph versions)            + DependencyGraphSnapshot refs
                                      + assembly health summary

HarnessRuntime.commit_graph()       HarnessRuntime.commit_graph()
  stage → validate → gates → commit    + AssemblyLedger.record()
                                        + AssemblyHealthGate.warn/defer/reject()

LifecycleTracker                   LifecycleTracker
  (8 runtime phases)                  + ComponentSelectionLifecycle
                                      + SelectionState governance

SafetyPipeline / AutoRollback       SafetyPipeline / AutoRollback
  sandbox, AB shadow, policy veto      + AssemblyHealthGate
  post-commit health rollback          + high-AI/low-copy risk checks

ExecutionEvidenceRecorder           ExecutionEvidenceRecorder
  run/validation/evidence snapshots    + core-wide ExecutionMode
                                      + InstantiationRecord
                                      + claim/action/evidence reconciliation

MetricsRegistry                     MetricsRegistry
  counters/gauges/histograms           + AssemblyMetricsService
                                      + metrics CLI / dashboard
```

这个摘要只描述职责增量，不要求一次性重构所有模块。优先做 companion service 和 refs，可以避免把 registry、audit 或 graph model 变成上帝对象。

## 迁移兼容性

推荐的首批变更应对现有 `metaharness_ext/*` 保持渐进兼容：

- `AssemblyLedger`、`CopyCountIndex` 和 `ComponentSelectionLifecycle` 作为新增服务，不改变现有 executor 合约。
- copy/reuse 计数优先在 core 调度、graph promotion、dependency resolution 和 execution evidence 附近埋点。
- core-wide `ExecutionMode` 初期可由 wrapper 或 adapter 从 extension 局部模式映射，不要求 extension 立即改字段。
- `AssemblyHealthGate` 初期只用 WARN 模式，不阻塞现有 promotion；DEFER/REJECT 需要指标校准后再启用。
- legacy graph/component 可标记为 `lineage_status = legacy_unknown`，不伪造历史谱系。

## 架构边界建议

### 保持 AuditLog 简单不可变

`AuditLog` 应继续作为 append-only evidence infrastructure。不要让它承担策略拒绝、权限判断或业务验证。

推荐分工：

- `AuditLog`：记录发生过的 claim、decision、action、rejection、verification。
- `SafetyPipeline`：判断 graph promotion 是否允许。
- `InstantiationGateway`：判断真实动作是否满足 external evidence contract。
- `AssemblyHealthGate`：判断复杂产物是否具备足够谱系和复用基础。

### 不要把 Registry 变成上帝对象

`ComponentRegistry` 当前职责清晰：注册组件、维护 pending zone、维护 slot/capability 索引、指向 candidate/active graph。升级时不应把所有 assembly metrics、copy counts、selection states 都塞进去。

推荐拆分：

- `ComponentRegistry`：当前组件集合与索引。
- `ProvGraph` / artifact stores：通用证据派生、artifact parent chain 和审计可追溯性。
- `AssemblyLedger`：graph/component/template/strategy 层面的组装治理谱系。
- `CopyCountIndex`：复用统计。
- `ComponentSelectionLifecycle`：组件生态状态。
- `AssemblyMetricsService`：指标计算与聚合。

### 区分运行时生命周期与选择生命周期

当前 lifecycle phase 是 runtime correctness 机制，不应直接承担 evolutionary selection。

推荐区分：

- runtime lifecycle：组件是否完成发现、验证、组装、激活、提交。
- selection lifecycle：组件是否处于探索、活跃、基础设施、弃用、graveyard。

前者服务于执行正确性，后者服务于长期演化与组件治理。

### 先记录，再 gate，最后自动淘汰

选择压力不要一开始就做强自动删除。建议三步走：

- 先记录 assembly/copy/verification 数据。
- 再在 promotion 中 warn/defer/reject。
- 最后才引入自动 deprecated/graveyard 策略。

这样能避免早期指标定义不稳定时误伤有效组件。

## 与另一份分析的吸收与修正

另一份分析非常有价值，尤其补充了以下方向：

- 持久化 boot dependency DAG。
- 组件生态生命周期与 selection pressure。
- `ExecutionMode` 作为 simulation/instantiation 边界。
- declaration-action reconciliation。
- transduction transparency 与 cartographer attribution。
- metrics dashboard。

本报告采纳这些方向，同时做出以下架构修正：

- 不建议让 `AuditLog` 拒绝无证据的 instantiation claim；拒绝应由 gateway 或 gate 完成，audit 负责记录。
- 不建议只在 `RegisteredComponent` 上添加 `copy_count`、`assembly_index`、`lineage_parents`；更稳妥的是 companion ledger/index，避免 registry 职责膨胀。
- 不建议只在 `commit_pending()` 增加 copy count；copy count 应拆分为注册、实例化、调用、依赖、跨图复用和外部验证等多个维度。
- 不建议复用 runtime `LifecycleTracker` 做组件淘汰；应新增 persistent selection lifecycle。
- “无 persistent DAG”需要精确表述：MHE 已有 graph snapshot，但缺少持久化的 boot/component dependency DAG。

## 风险与权衡

### 数据模型复杂度增加

Assembly Ledger、Copy Count Index、Transduction Records 会增加 core model 数量。为避免过度设计，应从最小字段开始，并优先通过 refs 连接现有 artifact/session/audit 数据。

### 指标误用风险

copy count 是可靠性的 proxy，不是可靠性本身。高复用组件也可能有系统性缺陷，低复用组件也可能是新但关键的创新组件。因此 selection gate 初期应以 warn/defer 为主，reject 只用于明显无谱系且影响关键路径的高风险情况。

### 执行边界接入成本

统一 Instantiation Gateway 可能要求各 extension executor 调整调用路径。建议先在 core execution evidence 层引入 execution mode 和 evidence contract，再逐步要求高风险 executor 迁移。

### 历史数据缺失

已有组件和 graph version 没有完整 assembly lineage。可以通过 migration/backfill 标记：

```text
lineage_status = legacy_unknown
```

不要伪造历史。缺失历史本身就是重要事实。

### Dashboard 真实性风险

dashboard 应只展示可由 ledger/index/gateway/audit 计算出的指标。不能用 agent 自我总结替代真实指标，否则会重新落入“地图冒充疆域”的问题。

## 推荐优先级

| 优先级 | 升级项 | 原因 | 预期收益 |
| --- | --- | --- | --- |
| P0 | `ExecutionMode` + external evidence refs | 修复 simulation/instantiation 核心边界 | 防止计划、dry-run、声明被误报为真实执行。 |
| P0 | `AssemblyLedger` 最小模型 | 建立复杂能力历史 | 让 graph/component/workflow 可追溯。 |
| P1 | `CopyCountIndex` | 建立复用强度指标 | 支撑 copy number trust 和 selection pressure。 |
| P1 | 持久化 dependency DAG | 支撑 assembly index | 让复杂度历史可计算。 |
| P1 | claim/action/evidence reconciliation | 建立行动对账 | 支撑物理主义检验和执行诚实性。 |
| P0 | `AssemblyHealthGate` WARN 模式 | 先将 assembly health 接入 promotion 观测链路 | 不阻塞现有流程，同时积累 gate 校准数据。 |
| P2 | `AssemblyHealthGate` DEFER/REJECT 模式 | 将成熟指标用于 promotion 决策 | 让选择压力真正影响系统演化。 |
| P2 | Selection lifecycle | 组件晋升/降级/归档 | 避免组件无限堆积。 |
| P3 | Metrics dashboard + CLI | 可视化框架健康度 | 支撑 benchmark、报告和运维。 |
| P3 | Transduction/cartographer records | 提升语义边界透明度 | 支撑高可信 I/O 映射审计。 |

## 建议的首个实现切片

最小切片应避免一次性改动所有 executor 和 extension。推荐从 graph promotion 路径开始：

- 新增 `AssemblyRecord`、`AssemblyLedger` 和内存实现。
- 在 `HarnessRuntime.commit_graph()` 创建 candidate 时写入 graph assembly record。
- 在 graph commit 成功后更新组件 `graph_reuse_count`。
- 为 graph promotion 生成 assembly health summary。
- 添加 focused tests 覆盖 candidate、commit、rollback 或 validation failure 情况下的 ledger 行为。

这个切片价值高、边界清晰，能马上让 MHE 记录“图从哪里来、用了哪些组件、这些组件被复用了多少次”。后续再接入 execution mode 和 instantiation gateway。

## 成功标准

MHE core 升级完成后，应能回答以下问题：

- 一个 graph version 是从哪些父图、模板、组件或策略组装而来的？
- 一个组件在多少个 graph version、workflow 或 execution 中被复用？
- 一个复杂 graph 的 assembly index 是多少？
- 一个高 assembly index graph 是否依赖足够高 copy count 的基础组件？
- 某个 agent 声称执行的动作是否有外部证据？
- 某个执行结果是否来自真实环境，而不是内部模拟？
- 某个符号输入/输出的制图者是谁？
- 某个组件应继续探索、晋升为基础设施，还是进入弃用/墓地？
- dashboard 上的指标是否都能追溯到 ledger、gateway、audit 或 session events？

如果这些问题能被系统性回答，MHE 就完成了从“well-instrumented orchestrator”到“selection environment with physical memory and cartographic honesty”的关键升级。

## 结论

MHE core 的基础架构已经足够支撑这次升级。当前不需要重写核心运行时，而应沿着现有 registry、graph promotion、execution evidence、audit、session store 和 safety pipeline 进行增量扩展。

最重要的框架升级不是新增更多 agent 能力，而是新增三个系统性能力：

- **组装记忆**：复杂能力必须有可追溯的父组件、版本、验证和复用记录。
- **选择压力**：高复用、高验证组件被晋升，低复用、高风险、无谱系组件被降级或隔离。
- **实例化诚实性**：计划、模拟、dry-run、真实执行和外部验证必须被明确区分。

按这个方向推进后，MHE 将不只是一个能够运行科学工作流的 harness，而是一个能够长期演化、审计和复用复杂科学 agent 能力的框架底座。