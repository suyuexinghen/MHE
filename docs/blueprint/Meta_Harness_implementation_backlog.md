# Meta-Harness Implementation Backlog (17 Apr 2026)

本文档把 `docs/roadmap/Meta_Harness_master_roadmap.md` 压缩成一个 implementation-ready backlog。

目标：
- 把 Meta-Harness 从 roadmap 落成可执行 backlog
- 明确 Epic / Story / Depends On / Exit Criteria
- 明确 priority 与 wave
- 明确第一批 sprint 应该先做什么

Meta-Harness 的核心不是堆更多组件，而是围绕 **candidate graph / staged lifecycle / constitutional governance** 建立一个可安全自修改的 agent 运行时。

---

## 1. Backlog 使用规则

### 优先级定义
- `P0`: 核心前置，不做就无法推进后续工作
- `P1`: 第一批高价值能力
- `P2`: 重要增强项
- `P3`: 产品化与 rollout 能力

### 状态定义
- `TODO`
- `READY`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`

### Story 编号规则
- `E1-S1` = Epic 1 的 Story 1

---

## 2. Epic 总览

| Epic | Theme | Priority | Depends On |
|---|---|---|---|
| **E0** | Prerequisite: Project Bootstrap & SDK Contract Definition | P0 | — |
| **E1** | Component SDK Foundation | P0 | E0 |
| **E2** | Component Discovery, Loading & Registry | P0 | E1 |
| **E3** | Connection Engine & Graph Versioning | P0 | E1 |
| **E4** | Core Components (9 + Optimizer Skeleton) | P0 | E1, E2, E3 |
| **E5** | Four-Level Safety Chain & Sandbox | P1 | E3, E4, E6-minimal |
| **E6** | Observability, Audit & Provenance | P1 | E4 |
| **E7** | Hot-Reload & State Migration | P1 | E3, E4 |
| **E8** | Optimizer & Self-Growth Engine | P2 | E4, E5, E6 |
| **E9** | Template Library & Code Generation | P2 | E1, E8 |
| **E10** | Productization, Extension Ecosystem & Rollout | P3 | E1–E9 |

---

## 3. Wave 计划

### Wave 0 — Prerequisites
- 确定项目结构、包名、target Python 版本、依赖管理、测试框架
- 定义 SDK 核心接口契约：HarnessComponent 生命周期、HarnessAPI 注入、ComponentManifest schema
- 从 wiki 提取核心数据模型并转化为 Pydantic schema
- 搭建 CI 基础（lint + test）

### Wave 1 — SDK & Infrastructure
- `HarnessComponent` base class
- `HarnessAPI` interface declaration
- `ComponentRuntime` injection
- `ComponentManifest` schema
- `ComponentDiscovery` (4 sources)
- `ComponentLoader` (validation + dependency resolution)
- `ComponentRegistry` (pending zone + commit/rollback)

### Wave 2 — Connection & Graph
- `ConnectionEngine` data routing
- `EventBus` dispatch
- `CompatibilityValidator` (5 rules)
- `GraphVersionManager` (immutable snapshots, candidate/active/rollback lifecycle)
- `ContractPruner`
- XML/XSD configuration parser

### Wave 3 — Core Components + Minimal Observability
- 9 core components: Runtime, Gateway, Memory, ToolHub, Planner, Executor, Evaluation, Observability, Policy
- Optimizer skeleton (observe, propose, evaluate, commit hooks)
- Default connection topology
- Protected component boundaries
- **Minimal observability**: metrics endpoint, trace IDs, audit event schema (needed by E5 safety chain)

### Wave 4 — Safety & Advanced Observability
- 4-level safety chain: SandboxValidator → ABShadowTester → PolicyVeto → AutoRollback
- 3-tier sandbox: V8/WASM, gVisor, Firecracker
- Constitutional rules (C-01 through C-05, R-01 through R-03)
- **Advanced observability**: Trace/Replay, Merkle audit chain, provenance queries

### Wave 5 — Hot-Reload & Optimizer
- Suspend-Transform-Resume protocol
- Checkpoint management
- Saga rollback
- Evolutionary search engine
- GIN state encoder
- Action funnel
- Convergence criteria

### Wave 6 — Templates & Productization
- Template registry
- Slot-filling engine
- Code generation pipeline
- Extension guide
- Evaluation fixtures
- API stability guarantees

---

## 4. Epic E0 — Prerequisite: Project Bootstrap & SDK Contract Definition

**Goal:** 搭建 Meta-Harness 独立项目骨架，定义 SDK 核心接口契约，确保后续 Epic 基于稳定的数据模型。

### E0-S1 搭建项目骨架
- **Priority:** P0
- **Status:** TODO
- **Depends On:** —
- **Work:**
  - 确定 Python 版本要求
  - 确定核心依赖：pydantic, aiohttp, networkx (DAG)
  - 确定可选依赖：torch (GIN), wasmtime (WASM), gVisor/Firecracker bindings
  - 确定测试框架：pytest + asyncio_mode="auto"
  - 搭建 CI 基础：lint (ruff) + test (pytest)
- **Done when:**
  - `pyproject.toml` 已定义核心依赖和可选依赖组
  - `meta_harness/__init__.py` 可导入
  - `pytest` 和 `ruff` 可正常运行

### E0-S2 定义 SDK 接口契约
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E0-S1
- **Work:**
  - 从 wiki 提取核心概念，转化为 Python 接口定义
  - 定义核心协议：组件生命周期、接口声明、运行时注入
  - 定义数据模型边界：哪些是 SDK 层的，哪些是 Engine 层的，哪些是 Component 层的
- **Done when:**
  - 有一份 SDK 接口契约文档，覆盖 lifecycle, registration, safety, hot-reload, observability 5 个维度
  - 明确 `meta_harness/sdk/` 的包结构与职责分层

### E0-S3 定义包结构与分层
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E0-S2
- **Work:**
  - 定义包结构：
    - `meta_harness/sdk/` — Component SDK（基类、API、Manifest、Runtime 注入）
    - `meta_harness/engine/` — 连接引擎、图版本管理、兼容性校验
    - `meta_harness/components/` — 9 大核心组件实现
    - `meta_harness/governance/` — 安全链、沙箱、宪法层
    - `meta_harness/optimizer/` — 优化器、搜索策略、收敛检测
    - `meta_harness/observability/` — 指标、Trace、Merkle 审计
  - 创建包骨架和 `__init__.py`
- **Done when:**
  - 所有顶级包已创建
  - 每个包有 `__init__.py` 和简要 docstring 说明职责

### E0 Exit Criteria
- 项目骨架可安装和导入
- SDK 接口契约文档完成
- 包结构与分层明确
- CI 基础可用

---

## 5. Epic E1 — Component SDK Foundation

**Goal:** 建立 Meta-Harness 的组件抽象层，定义组件基类、API 注入接口、运行时注入、和 Manifest schema。

### E1-S1 定义 `HarnessComponent` base class
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E0-S3
- **Work:**
  - 定义抽象基类，包含以下 hooks：
    - `declare_interface(api: HarnessAPI)` — 同步、无 I/O、幂等
    - `activate(runtime: ComponentRuntime)` — 异步、I/O 允许、30s 超时
    - `deactivate()` — 清理释放
    - `export_state()` / `import_state()`
    - `transform_state(old_state, from_ver, to_ver)` — 状态迁移
    - `health_check()`
  - 定义 `ComponentType` enum: CORE, TEMPLATE, META, GOVERNANCE
  - 定义 `ComponentPhase` enum: DISCOVERED → VALIDATED_STATIC → ASSEMBLED → VALIDATED_DYNAMIC → ACTIVATED → COMMITTED → SUSPENDED → FAILED
- **Done when:**
  - `HarnessComponent` 可被子类化
  - Phase transitions 只能单向推进（FAILED 除外）

### E1-S2 定义 `HarnessAPI` interface declaration
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1-S1
- **Work:**
  - API 提供以下方法：
    - `declare_input(name, type, required, description)`
    - `declare_output(name, type, description)`
    - `declare_event(name, payload_type)`
    - `provide_capability(capability)` / `require_capability(capability)`
    - `bind_slot(slot, mode)` / `reserve_slot(slot)`
    - `register_connection_handler(input_name, handler, priority)`
    - `register_hook(event, handler, kind, priority, matcher)`
    - `register_service(name, service_cls, policy)`
    - `register_validator(name, validator, phase)`
    - `register_migration_adapter(from_version, to_version, adapter)`
    - `_commit()`
- **Done when:**
  - 组件可以通过 `declare_interface(api)` 声明完整的接口面
  - 类型系统支持基本类型检查（string, int, float, list, dict, custom）
  - Slot 和 capability system 可被组件声明和消费

### E1-S3 定义 `ComponentRuntime` injection
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1-S1
- **Work:**
  - Runtime 注入以下能力：
    - `storage_path` — 私有存储路径
    - `config` — 组件配置
    - `logger` — 结构化日志
    - `metrics` — 指标收集器
    - `trace_store` — Trace 存储
    - `event_bus` — 事件总线
    - `llm` — ComponentLLMProxy
    - `sandbox_client` — 沙箱执行客户端
    - `graph_reader` — 当前图查询接口
    - `mutation_submit` — 提交 mutation proposal
    - `process_direct(content, **kwargs)`
    - `tool_execute(tool_name, params)`
- **Done when:**
  - 组件在 `activate()` 阶段可以访问所有 runtime 能力
  - Runtime 已区分只读 graph access 与 mutation submission

### E1-S4 定义 `ComponentManifest` schema
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1-S1
- **Work:**
  - 定义 `harness.component.json` schema：
    - id, name, version, description
    - `kind` (component kind)
    - `entry` (module path)
    - harness_version (compatibility constraint)
    - deps (component dependencies)
    - bins, env (binary/environment dependencies)
    - `contracts` (inputs / outputs / events)
    - `provides` / `requires` (capability lists)
    - slots (extensible capability slots)
    - `safety` (protected, hot_swap)
    - `state_schema_version`
  - Pydantic model + JSON Schema
- **Done when:**
  - Manifest 可以被解析、验证、序列化
  - 至少 3 个示例 manifest（core, template, meta）
  - 字段命名与 wiki 规范一致 (`kind`, `entry`, `contracts`, `safety`)

### E1 Exit Criteria
- `HarnessComponent` 可被子类化并实现完整 lifecycle
- `HarnessAPI` 支持接口声明和行为注册
- `ComponentRuntime` 提供标准注入能力
- `ComponentManifest` 有 Pydantic schema 和示例

---

## 6. Epic E2 — Component Discovery, Loading & Registry

**Goal:** 建立组件发现、加载、验证和注册的完整 pipeline。

### E2-S1 实现 `ComponentDiscovery` (4 sources)
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1-S4
- **Work:**
  - 4 个扫描源：
    - `scan_bundled()` — `metaharness/components/*`
    - `scan_templates()` — 模板库中的组件骨架
    - `scan_market()` — 组件市场（远程）
    - `scan_custom()` — 用户自定义路径
  - 冲突解决：高优先级覆盖低优先级
- **Done when:**
  - 4 个扫描源都能独立工作
  - 冲突解决逻辑正确（bundled > template > market > custom）

### E2-S2 实现 `ComponentLoader` — static validation
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E2-S1, E1-S4
- **Work:**
  - 检查 `harness_version` 兼容性
  - 检查 bins/env 依赖
  - 解析和验证 `harness.component.json`
  - `import_module()` 加载组件类
  - 记录验证失败原因，phase=FAILED
- **Done when:**
  - 无效 manifest、版本不兼容、依赖缺失都能正确报告
  - 通过验证的组件进入 VALIDATED_STATIC phase

### E2-S3 实现 dependency resolution (Kahn's algorithm)
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E2-S2
- **Work:**
  - Kahn 算法拓扑排序
  - 循环依赖检测 → CircularDependencyError
  - 过滤已禁用组件 (config.enabled=False)
- **Done when:**
  - 给定一组组件，输出正确的加载顺序
  - 循环依赖被检测并报告

### E2-S4 实现 `ComponentRegistry` — staged registration
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E2-S3, E1-S2
- **Work:**
  - 组件注册流程：
    1. 组件类实例化（无参构造）
    2. `declare_interface(api)` — 声明端口 / slot / capability
    3. `register_hook()` / `register_service()` / `register_validator()`
    4. 写入 pending 区
    5. 冲突检测（ID / port / protected slot）
    6. `_commit()` 或 rollback
  - 统一管理：组件、Slot、Capability、Graph版本、Pending变更
- **Done when:**
  - 注册失败时组件被完全回滚
  - 冲突检测能捕获 ID、端口和 protected slot 冲突
  - Registry 状态可查询（按 phase, type, id）

### E2-S5 实现 `HarnessRuntime.boot()` orchestration
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E2-S4
- **Work:**
  - 编排完整启动流程：
    - 创建 Registry
    - 配置 Discovery
    - 配置 Loader
    - discover_all() → validate → resolve deps → register
  - 返回 BootResult (loaded, failed 列表)
- **Done when:**
  - 至少 2 个测试组件可以通过完整 boot 流程加载

### E2 Exit Criteria
- 组件可以从 4 个源被发现
- 通过验证的组件可以按依赖顺序加载和注册
- 注册失败的组件被正确回滚
- boot() 能编排完整启动流程

---

## 7. Epic E3 — Connection Engine & Graph Versioning

**Goal:** 建立组件间的数据路由、事件分发、兼容性校验、和不可变图版本管理。

### E3-S1 定义端口与连接模型
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1-S2
- **Work:**
  - `Input` model: name, contract/type, required, description
  - `Output` model: name, contract/type, description
  - `Event` model: name, payload_type, subscribers
  - `Connection` model: source_component + source_output → target_component + target_input + payload/mode/policy
  - `PendingConnection` / `PendingConnectionSet`: 尚未提交的候选连接
- **Done when:**
  - 所有端口和连接类型有 Pydantic 模型
  - Connection 可以被验证（contract 匹配、引用完整性）

### E3-S2 实现 `ConnectionEngine` routing
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E3-S1
- **Work:**
  - 数据路由：根据 Connection 定义将 Output 数据分发到 Input
  - 事件路由：EventBus 发布/订阅模式
  - 支持 `sync` / `async` / `event` / `shadow` routing modes
  - 实现 `PortIndex` 与 `RouteTable`
  - Trace ID 在跨组件路由中传播
- **Done when:**
  - 两个测试组件可以通过 ConnectionEngine 交换数据
  - 事件可以通过 EventBus 传播
  - shadow route 不影响主路径输出

### E3-S3 实现 `CompatibilityValidator` (5 rules)
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E3-S1
- **Work:**
  - Rule 1: contract 匹配 — Connection.source.Output.contract == Connection.target.Input.contract
  - Rule 2: 事件声明 — trigger 事件必须被显式声明
  - Rule 3: 输入完整性 — required=true 的 Input 必须被 Connection 满足
  - Rule 4: ID 唯一性
  - Rule 5: graph consistency — 无非法循环 / protected slot 不可覆盖
- **Done when:**
  - 5 条规则各自有 pass/fail 测试用例
  - 校验结果包含具体错误位置和建议

### E3-S4 实现 `GraphVersionManager`
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E3-S3
- **Work:**
  - 创建不可变 graph 快照
  - 版本生命周期：candidate → active → rollback_target → archived
  - 原子性切换：candidate → active（旧版本成为 rollback_target）
  - 递增 graph_version_number
  - 版本退休与 archival（防止 version rot）
  - 最小保留数量配置
- **Done when:**
  - 候选图可以被组装、校验、提交为 active graph
  - active graph 可以回滚到 rollback_target
  - archived 版本被正确清理

### E3-S5 实现 XML/XSD 配置解析器
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E3-S1
- **Work:**
  - 解析 `harness.config.xml`
  - XSD schema 验证
  - 从 XML 提取组件定义和连接定义
- **Done when:**
  - XML 配置可以被解析为组件和连接模型
  - 不合规的 XML 被拒绝并报告错误

### E3-S6 实现 `ContractPruner`
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E3-S3
- **Work:**
  - 根据兼容性约束剪枝搜索空间
  - 排除不兼容的连接提案
  - 减少优化器的探索范围
- **Done when:**
  - 给定一组候选变更，输出兼容的子集
  - 搜索空间减少率可测量

### E3 Exit Criteria
- ConnectionEngine 可以在组件间路由数据
- CompatibilityValidator 执行 5 条规则
- GraphVersionManager 管理完整的版本生命周期
- 候选图可以提交为 active graph version

---

## 8. Epic E4 — Core Components (9 + Optimizer Skeleton)

**Goal:** 实现 9 个核心组件和 Optimizer 骨架，建立默认连接拓扑。

**Implementation order (from wiki):**
- Wave A: Runtime + Memory + Evaluation (data plane core)
- Wave B: Policy + Observability (control plane + evidence)
- Wave C: Planner + Executor + ToolHub (execution plane)
- Wave D: Gateway (entry point)
- Wave E: Optimizer (meta-layer)

### E4-S1 实现 `Runtime` 组件
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1, E2, E3
- **Work:**
  - 任务调度与流程编排
  - 指令分发到其他组件
  - graph version context 管理
  - staged lifecycle execution, timeout/retry
  - 默认实现：`IterativeRuntime`
  - 输入: Command, 输出: Action, Event: on_schedule
- **Done when:**
  - 可以接收 Command 并分发到对应执行路径
  - `IterativeRuntime` 作为默认 runtime 可用

### E4-S2 实现 `Gateway` 组件
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E4-S1
- **Work:**
  - 外部通信接口（API、CLI、消息队列）
  - 凭证管理
  - Identity root capability 管理
  - 默认实现：`DefaultGateway`
  - 输入: RawRequest, 输出: Command
- **Done when:**
  - 可以接收外部请求并转换为内部 Command
  - 凭证不进入 LLM / planner path

### E4-S3 实现 `Memory` 组件
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1
- **Work:**
  - 上下文读写
  - 执行轨迹持久化（热/温/冷存储）
  - checkpoint / snapshot / restore
  - counter-factual diagnosis interfaces: compare_traces, replay_trace
  - 默认实现：`JsonlMemory`
  - 输入: StoreQuery, 输出: ContextSnapshot
- **Done when:**
  - 可以存储和检索上下文数据
  - 支持时间范围和键值查询
  - `JsonlMemory` 作为默认 memory 可用

### E4-S4 实现 `ToolHub` 组件
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E1
- **Work:**
  - 工具注册、发现、执行
  - 执行沙箱化（委托给 Sandbox 组件）
  - 输入: ToolCall, 输出: ToolResult
- **Done when:**
  - 工具可以注册、发现和执行
  - 执行结果被正确返回

### E4-S5 实现 `Planner` 组件
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E1, E4-S3
- **Work:**
  - 任务分解与推理
  - 策略选择
  - 输入: Task, 输出: Plan
- **Done when:**
  - 可以将任务分解为可执行步骤

### E4-S6 实现 `Executor` 组件
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E1, E4-S4
- **Work:**
  - 动作执行与结果收集
  - 重试和错误处理
  - 输入: Plan, 输出: ActionResult
- **Done when:**
  - 可以执行 Plan 中的步骤并收集结果

### E4-S7 实现 `Evaluation` 组件
- **Priority:** P0
- **Status:** TODO
- **Depends On:** E1
- **Work:**
  - 性能指标收集
  - 质量控制 (QC)
  - 适应度评估
  - loop guard / termination signal
  - 默认实现：`DefaultEvaluation`
  - 输入: ActionResult, 输出: EvaluationReport
- **Done when:**
  - 可以评估执行结果的质量
  - loop guard sub-module 可发出 stop signal

### E4-S8 实现 `Observability` 组件
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E4-S1, E4-S3, E4-S7
- **Work:**
  - 指标收集和暴露
  - 健康监控
  - trace emission + trace IDs
  - audit event schema
  - 默认实现：`StructuredObservability`
  - 输入: MetricSample, 输出: MetricAggregate
- **Done when:**
  - 可以收集和暴露系统指标
  - trace ID 可跨组件传播

### E4-S9 实现 `Policy` 组件
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E4-S7
- **Work:**
  - 权限执行
  - 约束检查
  - 宪法规则管理 (C-01 through C-05, R-01 through R-03)
  - 受保护组件标记
  - Guard / Mutate / Reduce hooks
  - 默认实现：`ConstitutionalPolicy`
  - 输入: Action, 输出: Decision
- **Done when:**
  - 可以执行权限检查
  - 可以拒绝违反宪法规则的操作
  - Guard / Mutate / Reduce hooks 可用

### E4-S10 实现 Optimizer 骨架
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E1
- **Work:**
  - 定义 Optimizer 为元层组件（不参与任务执行）
  - 实现 hooks: observe(), propose(), evaluate(), commit()
  - 实现 protected component 边界
  - 定义 PendingMutation 模型
  - 初版只支持 observe（收集指标），propose 返回空列表
- **Done when:**
  - Optimizer 可以被加载和激活
  - observe() 能读取 Evaluation 和 Observability 的输出

### E4-S11 默认连接拓扑与集成测试
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E4-S1 through E4-S10
- **Work:**
  - 定义 9 组件 + Optimizer 的默认连接
  - 端到端集成测试：Command → Gateway → Runtime → Planner → Executor → Evaluation → Observability
  - 孤儿组件检测
- **Done when:**
  - 默认拓扑可以被 ConnectionEngine 校验和加载
  - 端到端测试通过

### E4 Exit Criteria
- 9 个核心组件全部注册并可独立工作
- Optimizer 骨架可以 observe 指标
- 默认连接拓扑通过 CompatibilityValidator
- 端到端集成测试通过
- **Minimal observability built-in**: metrics endpoint, trace IDs, audit event schema (prerequisite for E5 safety chain)

---

## 9. Epic E5 — Four-Level Safety Chain & Sandbox

**Goal:** 建立四级安全链路和三层沙箱，确保候选配置在被提交前经过严格验证。

**Note:** E5 depends on minimal observability from E4 (metrics endpoint, trace IDs). AutoRollback (E5-S4) and ABShadowTester (E5-S2) require metrics collection to function.

### E5-S1 Level 1: SandboxValidator
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E4, E3-S4
- **Work:**
  - 在隔离环境中执行回归测试
  - 重放历史失败用例
  - 资源限制：timeout / memory / network
  - 根据风险等级选择沙箱层级
- **Done when:**
  - 候选配置在沙箱中完成回归测试
  - 失败的配置被拒绝并记录原因

### E5-S2 Level 2: ABShadowTester
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E5-S1
- **Work:**
  - 复制生产流量到候选配置
  - 候选输出仅记录，不影响用户
  - 基础比较：候选输出 vs 基线输出的数值差异
  - 统计显著性检验：配对 t 检验 / Wilcoxon (stretch goal — basic comparison first)
  - 候选配置劣于基线时终止上线
- **Done when:**
  - 影子测试可以执行并产出比较报告
  - 劣于基线的候选被正确拒绝

### E5-S3 Level 3: PolicyVeto (Constitutional Review)
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E5-S2, E4-S9
- **Work:**
  - 审查安全不变量：
    - C-01: 资源硬顶约束
    - C-02: 影子验证一致性
    - C-03: 关键路径不可篡改
    - C-04: Token 预算熔断
    - C-05: 隐私泄露阻断
    - R-01: 数据溯源强制（科研）
    - R-02: 不可重现性警报（科研）
    - R-03: 同行评审模拟（科研）
  - 违反不可变规则 → 宪法否决
- **Done when:**
  - 违反 C-01 到 C-05 的候选被正确否决
  - 否决原因包含具体违反的规则

### E5-S4 Level 4: AutoRollback with Observation Window
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E5-S3, E3-S4, E4-minimal-observability
- **Work:**
  - 创建 Checkpoint（当前 active graph 快照）
  - 启动观察窗口：max(20 tasks, 300s)
  - 采集健康指标：错误率 / 延迟 P99 / 资源异常 (from E4 metrics endpoint)
  - Z-Score 异常检测：T_new > μ(T_old) + 3σ(T_old)
  - 性能退化 → 触发回滚
- **Done when:**
  - 观察窗口可以检测性能退化
  - 回滚正确恢复到 rollback_target

### E5-S5 Safety Chain Pipeline Integration
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E5-S1 through E5-S4
- **Work:**
  - 串联 4 级：SandboxValidator → ABShadowTester → PolicyVeto → AutoRollback
  - 任何一级失败 → 拒绝整个候选
  - 全部通过 → 提交并进入观察窗口
- **Done when:**
  - 完整 pipeline 可以执行
  - 每一级的通过/失败路径都被测试

### E5-S6 Three-Tier Sandbox Implementation
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E5-S1
- **Work:**
  - V8/WASM tier: <1ms，简单逻辑筛选
  - gVisor tier: ~50ms，Python 脚本隔离
  - Firecracker tier: ~30ms startup，高危操作深度隔离
  - 风险等级 → 沙箱层级映射
- **Done when:**
  - 至少 1 个 tier 可用（WASM 为最小可行）
  - 风险等级自动选择正确的 tier
  - (stretch: gVisor tier operational)

### E5 Exit Criteria
- 4 级安全链路完整串联
- 候选配置必须逐级通过
- 至少 1 个沙箱 tier 可用 (WASM)
- 回滚机制在性能退化时正确触发

---

## 10. Epic E6 — Observability, Audit & Provenance

**Goal:** 建立高级观测能力：Trace/Replay、PROV-based evidence、Merkle 审计链、和溯源查询。

**Note:** Minimal observability (metrics endpoint, trace IDs, audit event schema) is built into E4 core components. This Epic covers the advanced capabilities that build on that foundation.

### E6-S1 三层指标收集
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E4-S8
- **Work:**
  - 系统层：CPU, memory, I/O, network, component count, graph version count
  - 组件层：per-component latency, throughput, error rate, resource usage
  - 任务层：per-task execution trajectory with timestamps and outcomes
- **Done when:**
  - 三层指标可以通过统一接口查询

### E6-S2 Trace/Replay 机制
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E6-S1
- **Work:**
  - 执行轨迹持久化到分层存储（热/温/冷）
  - 按 task ID、component、time range、outcome 查询
  - 历史执行可重放用于诊断
- **Done when:**
  - 至少一个任务执行轨迹可以被查询和重放

### E6-S3 PROV + Merkle 审计链
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E6-S1
- **Work:**
  - 每个 state transition、mutation、safety decision 产生 PROV-based evidence object
  - Evidence objects 作为 Merkle tree leaves
  - Merkle root 提供防篡改完整性
  - 只追加审计日志持久化
- **Done when:**
  - 任何篡改都可以通过 Merkle root 验证检测
  - 审计日志覆盖所有关键操作
  - evidence object schema 与 PROV mapping 一致

### E6-S4 Provenance 查询
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E6-S3
- **Work:**
  - "为什么这个组件被修改？" → 完整溯源链
  - 查询 Optimizer proposal → Safety chain decision → Commit/rollback → Outcome
- **Done when:**
  - 可以追溯任何组件变更的完整决策链

### E6 Exit Criteria
- 三层指标可收集和查询
- 执行轨迹可持久化和重放
- Merkle 审计链覆盖所有关键操作
- Provenance 查询可追溯变更原因

---

## 11. Epic E7 — Hot-Reload & State Migration

**Goal:** 实现 Suspend-Transform-Resume 热加载协议、Checkpoint 管理、和 Saga 回滚。

**Note:** Hot-reload requires component state contracts from E4. At minimum, Memory and Runtime must define stateful behavior before suspend/resume is meaningful.

### E7-S1 Suspend-Transform-Resume 协议
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E3, E4
- **Work:**
  - `suspend()`: 停止接收新消息，drain(timeout=30s) 等待当前操作完成
  - `transform_state(old_state, delta)`: τ: S_old × ΔP → S_new
  - `resume(new_state)`: 注入迁移后状态，恢复消息处理
  - 消息缓冲：suspend 期间的消息存入 buffer，resume 后处理
- **Done when:**
  - 组件可以在运行中被 suspend 和 resume
  - 零消息丢失
  - 至少一个有状态组件（Memory 或 Runtime）成功完成 suspend-migrate-resume cycle

### E7-S2 Checkpoint 管理
- **Priority:** P1
- **Status:** TODO
- **Depends On:** E7-S1, E3-S4
- **Work:**
  - suspend 时创建 state_snapshot
  - GraphVersionManager 存储 checkpoint
  - checkpoint 可用于回滚
- **Done when:**
  - checkpoint 可以被创建和恢复

### E7-S3 State Migration Adapter
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E7-S1
- **Work:**
  - 组件注册 migration_adapter: (from_version, to_version) → transform
  - Optimizer 同步生成 Python 转换逻辑
  - 版本不匹配时自动选择 adapter 链
- **Done when:**
  - 状态可以从 v1 格式迁移到 v2 格式

### E7-S4 Saga 回滚机制
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E7-S1, E3-S4
- **Work:**
  - 多步迁移失败时触发补偿事务
  - 每步记录补偿操作
  - 失败时逆序执行补偿
- **Done when:**
  - 3 步迁移在第 2 步失败时，前 2 步的补偿事务被正确执行

### E7-S5 Crash Recovery
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E7-S2, E6-S1
- **Work:**
  - 进程崩溃后从 checkpoint 恢复 graph state
  - replay in-flight trace to rebuild state where possible
  - 特殊崩溃场景：migration crash / trace store unavailable
- **Done when:**
  - 至少一个 crash scenario 可从 checkpoint 恢复
  - 恢复路径生成 audit evidence

### E7 Exit Criteria
- Suspend-Transform-Resume 完整可用
- 零消息丢失
- Checkpoint 可创建和恢复
- Saga 回滚正确补偿失败的多步迁移
- 至少一个 crash recovery fixture 通过

---

## 12. Epic E8 — Optimizer & Self-Growth Engine

**Goal:** 激活自修改循环：evolutionary search、GIN 状态编码、收敛检测、和行为策略学习。

**Search structure (from wiki):**
- Phase A: Local parameter search
- Phase B: Topology & template search
- Phase C: Constrained synthesis

### E8-S1 Layered Trigger Mechanism
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E4-S10, E6
- **Work:**
  - 5 层触发：
    - L1: 参数调整（learning rate, temperature, top_k）
    - L2: 连接重连（组件间拓扑变更）
    - L3: 模板替换（组件实现替换）
    - L4: 代码补丁（组件逻辑修改）
    - L5: 行为策略（新的决策策略）
  - 可配置阈值：性能偏差超过阈值才触发
- **Done when:**
  - 每层触发可独立配置和测试
  - 未超过阈值时不触发

### E8-S2 Three-Phase Search Engine
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E8-S1
- **Work:**
  - Phase A: Local parameter search (evolutionary + Bayesian)
  - Phase B: Topology & template search
  - Phase C: Constrained synthesis (LLM-based proposer; optional after A/B)
  - 种群初始化：从当前配置 + 随机扰动生成初始种群
  - 交叉算子：两个配置组合
  - 变异算子：参数/连接/模板/代码变更
  - 选择：锦标赛选择或精英保留
  - 适应度评估：委托给 Evaluation 组件
- **Done when:**
  - 至少 3 轮搜索完成，适应度有改善趋势
  - Search escalation rules 已定义（A → B → C）

### E8-S3 GIN State Encoder
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E8-S2
- **Work:**
  - Graph Isomorphism Network 编码当前组件拓扑
  - 输出固定维度向量作为 Optimizer 状态表示
  - 处理非 Markovian 状态：加入轨迹摘要
- **Done when:**
  - 不同的组件拓扑编码为不同的向量
  - 相似的拓扑编码为相似的向量

### E8-S4 Four-Layer Action Funnel
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E8-S2
- **Work:**
  - 参数层：安全、低影响、高频率
  - 连接层：中等影响、中等频率
  - 模板/代码层：高影响、低频率
  - 策略层：最高影响、最低频率
  - Funnel 从安全到激进逐渐收窄
- **Done when:**
  - 每层的动作空间有明确边界
  - 高影响动作需要更多验证

### E8-S5 Convergence Detection
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E8-S2
- **Work:**
  - 三重收敛标准：
    1. Hypervolume 稳定性（Pareto front 不再显著改善）
    2. 统计显著性（改进不再显著）
    3. 复杂度上限（配置复杂度不超过阈值）
  - Dead End 检测：同一意图连续 3 次回滚 → 标记为 Dead End
- **Done when:**
  - 收敛时搜索正确停止
  - Dead End 被正确标记和记录

### E8-S6 Negative Reward Feedback Loop
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E8-S2, E5
- **Work:**
  - 安全链失败 → 强惩罚信号 (-R_fail, -R_veto)
  - 回滚事件 → 失败轨迹记录
  - 惩罚信号反馈到搜索策略
  - 记录到 Memory 供反事实诊断使用
- **Done when:**
  - 失败的提议在后续搜索中被降低权重

### E8-S7 MVP Proposer
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E8-S2, E6
- **Work:**
  - `LogGopher`: mine failure patterns from traces
  - `DiffAnalyzer`: compare successful vs failed runs
  - `XMLPatcher`: generate constrained graph/config patches
- **Done when:**
  - MVP proposer can emit at least one valid candidate patch from historical failures

### E8 Exit Criteria
- Optimizer 可以触发、搜索、提议、评估候选变更
- 至少 3 轮优化完成，适应度有可测量改善
- 收敛检测正确停止搜索
- Dead End 检测防止重复失败
- MVP proposer components (`LogGopher`, `DiffAnalyzer`, `XMLPatcher`) are defined

---

## 13. Epic E9 — Template Library & Code Generation

**Goal:** 建立模板注册表、槽位填充引擎、和代码生成管线。

### E9-S1 Template Registry & Discovery
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E1
- **Work:**
  - 策划模板：BM25Retriever, ContextPruner, ChainOfThoughtPlanner, RetryWithBackoff 等
  - 模板 manifest 格式
  - 模板发现和注册
- **Done when:**
  - 至少 5 个模板可以被发现和加载

### E9-S2 Slot-Filling Engine
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E9-S1
- **Work:**
  - 模板声明必需的 slots
  - 引擎从组件 capabilities 填充 slots
  - 不完整的填充被拒绝
- **Done when:**
  - 模板 slots 可以被自动填充
  - 不完整填充被正确报告

### E9-S3 Code Generation Pipeline
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E9-S2
- **Work:**
  - 模板选择 → 参数填充 → 代码生成 → mypy 检查 → 沙箱测试 → 注册
  - 生成代码的结构化验证
- **Done when:**
  - 至少 3 个工作组件通过代码生成管线产出

### E9-S4 Migration Adapter System
- **Priority:** P2
- **Status:** TODO
- **Depends On:** E9-S3
- **Work:**
  - 模板版本变更触发 migration adapters
  - 状态转换适配器注册和执行
- **Done when:**
  - 模板升级时已有实例的状态被正确迁移

### E9 Exit Criteria
- 模板注册表可用
- Slot-filling 引擎可以自动填充模板
- 代码生成管线产出的组件通过沙箱测试
- Migration adapters 处理模板版本升级

---

## 14. Epic E10 — Productization, Extension Ecosystem & Rollout

**Goal:** 让 Meta-Harness 成为一个稳定、文档完善、可扩展的平台。

### E10-S1 Extension Guide & Documentation
- **Priority:** P3
- **Status:** TODO
- **Depends On:** E1–E9
- **Work:**
  - 自定义组件开发指南：manifest → implement → test → register → deploy
  - Candidate-graph-first workflow 文档
  - 受保护组件约束文档
  - Optimizer 扩展点文档
- **Done when:**
  - 开发者无需阅读内部设计文档也能开发自定义组件

### E10-S2 Evaluation Fixtures
- **Priority:** P3
- **Status:** TODO
- **Depends On:** E5, E7, E8
- **Work:**
  - 安全链 fixture：sandbox pass/fail, A/B reject, veto, rollback
  - 热加载 fixture：suspend-transform-resume with state migration
  - Optimizer fixture：convergence, dead end, reward feedback
- **Done when:**
  - 每个 workflow primitive 都有 fixture 覆盖

### E10-S3 API Stability & Performance Benchmarks
- **Priority:** P3
- **Status:** TODO
- **Depends On:** E1–E9
- **Work:**
  - 公共 SDK 接口稳定性保证
  - 性能基准：boot time, safety-chain latency, hot-reload downtime
  - 版本间兼容性验证
- **Done when:**
  - 性能指标被记录和追踪
  - API 不兼容变更被明确标记

### E10 Exit Criteria
- Extension guide 覆盖所有主要扩展点
- Evaluation fixtures 覆盖所有关键路径
- API 稳定性保证明确
- 性能基准被建立

---

## 15. Critical Path

```text
E0 (Project Bootstrap & SDK Contracts)
  -> E1 (Component SDK Foundation)
     -> E2 (Discovery, Loading & Registry)
     -> E3 (Connection Engine & Graph Versioning)
        -> E4 (Core Components 9 + Optimizer Skeleton + Minimal Observability)
           ├──> E5 (Safety Chain & Sandbox) — needs E4 metrics
           ├──> E6 (Advanced Observability: Trace/Replay, Merkle, Provenance)
           └──> E7 (Hot-Reload & State Migration) — needs E4 state contracts
              -> E8 (Optimizer & Self-Growth) — needs E5 + E6
                 -> E9 (Template Library & Code Gen)
                    -> E10 (Productization & Rollout)

with additional dependencies:
E4 depends on E2 + E3
E5 depends on E4-minimal-observability
E7 depends on E4 state contracts (Memory, Runtime)
E8 depends on E5 + E6
```

### MVP Release Track (v0.5)

```text
E0 + E1 -> E2 + E3 -> E4 (minimal: 2 components + candidate graph)
   = v0.5: boot → candidate graph → commit/rollback → one stable end-to-end topology
```

### What v0.5 MVP Excludes
- RL enhancement
- Firecracker sandbox (WASM only)
- Full Merkle provenance (simple audit log)
- Template code generation
- Statistical shadow testing
- GIN state encoding

### Strict Dependencies
- `HarnessComponent` 必须先于所有 downstream 组件
- `ComponentRegistry` 的 pending zone 必须先于 candidate graph assembly
- `GraphVersionManager` 必须先于 safety chain 的 checkpoint
- Core Components + minimal observability 必须先于 safety chain (E5 needs metrics)
- Core Components state contracts 必须先于 hot-reload (E7 needs Memory/Runtime stateful behavior)
- Observability 指标必须先于 Optimizer 的 fitness 信号
- Safety chain 必须先于 Optimizer 的真实 mutation 提交

### Parallel Opportunities
- E2 和 E3 可在 E1 完成后并行推进
- E5, E6, E7 可在 E4 完成后并行推进（但 E5 需要 E4 minimal observability，E7 需要 E4 state contracts）
- E9 可在 E8 完成后与 E10 并行推进
- Documentation 可在每层接口稳定后提前准备

---

## 16. Recommended First Sprint

如果只做一个非常务实的第一批 sprint，建议选这 6 项：

1. `E0-S1` 搭建项目骨架
2. `E0-S2` 定义 SDK 接口契约
3. `E0-S3` 定义包结构与分层
4. `E1-S1` 定义 `HarnessComponent` base class
5. `E1-S2` 定义 `HarnessAPI` interface declaration
6. `E1-S4` 定义 `ComponentManifest` schema

### Sprint Goal
- 锁定 Meta-Harness SDK 的核心数据模型与接口契约
- 搭建独立项目骨架，不依赖任何外部插件框架
- 在不碰复杂 orchestration / safety 的前提下，先把模型层稳定下来

### Sprint Exit Criteria
- `HarnessComponent`、`HarnessAPI`、`ComponentRuntime`、`ComponentManifest` 四个核心 schema 已稳定
- 项目骨架可安装、CI 可运行
- ADR-001 至 ADR-004 草案完成（taxonomy, boundaries, XML vs internal, protected components）
- `HarnessAPI` interface declaration 可被子类使用

---

## 17. First Sprint Implementation Task Sheet

### 17.1 `E0-S1` 搭建项目骨架

**目标：** 创建独立可安装的 Meta-Harness 项目。

**建议文件**
- `meta_harness/pyproject.toml`
- `meta_harness/__init__.py`
- `meta_harness/conftest.py`

**要做的事**
- 定义 Python 版本要求（建议 >=3.11）
- 核心依赖：pydantic, aiohttp, networkx
- 可选依赖：torch (GIN), wasmtime (WASM)
- 测试：pytest + asyncio_mode="auto"
- CI：ruff lint + pytest

**交付物**
- 可安装的 `pyproject.toml`
- `meta_harness/__init__.py`
- `ruff check .` 和 `pytest` 可正常运行

### 17.2 `E0-S2` 定义 SDK 接口契约

**目标：** 从 wiki 提取核心概念，转化为 Python 接口定义和契约文档。

**建议文件**
- `meta_harness/sdk/contracts.py`
- `meta_harness/sdk/README.md`

**建议类 / 函数**
- `ComponentLifecycle` (Protocol)
- `PortDeclaration` (Protocol)
- `MutationProposal` (Protocol)

**要做的事**
- 提取 wiki 中的核心概念：组件生命周期、接口声明、候选图、安全链
- 定义 Python Protocol / Abstract Base Class 契约
- 文档化 5 维度接口边界：lifecycle, registration, safety, hot-reload, observability
- 输出 4 份 ADR 草案：
  - ADR-001: 组件分类法（9 core + meta-layer，Identity/Sandbox/Browser 不是核心组件）
  - ADR-002: 包边界与命名（`metaharness` vs `meta_harness`; sdk / engine / components / governance / optimizer / observability）
  - ADR-003: XML 配置 vs 内部模型
  - ADR-004: 受保护组件定义与修改限制

**交付物**
- SDK 接口契约文档
- Protocol / ABC 定义
- 职责分层图：SDK / Engine / Component / Governance / Optimizer
- ADR-001 至 ADR-004 草案

### 17.3 `E0-S3` 定义包结构与分层

**目标：** 创建 Meta-Harness 的包骨架。

**建议文件**
- `meta_harness/sdk/__init__.py`
- `meta_harness/engine/__init__.py`
- `meta_harness/components/__init__.py`
- `meta_harness/governance/__init__.py`
- `meta_harness/optimizer/__init__.py`
- `meta_harness/observability/__init__.py`

**要做的事**
- 创建 6 个顶级包，每个有 docstring 说明职责
- 定义包间依赖规则（sdk 不依赖 engine，engine 不依赖 components，etc.）

**交付物**
- 所有顶级包已创建
- 每个包有 `__init__.py` 和 docstring

### 17.4 `E1-S1` 定义 `HarnessComponent` base class

**目标：** 定义组件基类和生命周期枚举。

**建议文件**
- `meta_harness/sdk/component.py`
- `meta_harness/sdk/types.py`

**建议类 / 函数**
- `HarnessComponent`
- `ComponentType` (enum)
- `ComponentPhase` (enum)

**要做的事**
- 定义抽象基类 with lifecycle hooks
- 定义 phase transition rules
- 定义 component type taxonomy

**交付物**
- `HarnessComponent` 类骨架
- Phase transition validator
- 一组最小 fixture: valid transition, invalid transition

### 17.5 `E1-S2` 定义 `HarnessAPI` interface declaration

**目标：** 定义组件接口声明 API。

**建议文件**
- `meta_harness/sdk/api.py`
- `tests/sdk/test_api.py`

**建议类 / 函数**
- `HarnessAPI`
- `PortDeclaration`
- `HookKind` (enum: NOTIFY/MUTATE/REDUCE/GUARD)

**要做的事**
- API methods: declare_input, declare_output, declare_event, register_connection_handler, register_hook, register_migration_adapter
- 类型系统：基本类型 + custom 类型支持

**交付物**
- `HarnessAPI` 类
- 类型匹配测试
- 一组最小 fixture: 声明端口、注册 hook

### 17.6 `E1-S4` 定义 `ComponentManifest` schema

**目标：** 定义组件清单的 Pydantic schema。

**建议文件**
- `meta_harness/sdk/manifest.py`
- `tests/sdk/test_manifest.py`

**建议类 / 函数**
- `ComponentManifest`
- `ComponentDependency`
- `PortDeclaration`
- `SlotDeclaration`
- `validate_manifest()`

**要做的事**
- 定义 manifest 的所有字段
- JSON Schema 导出
- 示例 manifest

**交付物**
- `ComponentManifest` Pydantic model
- JSON Schema
- 3 个示例 manifest (core, template, meta)

### 17.7 `E3-S1` 定义端口与连接模型

**目标：** 定义 Input/Output/Event/Connection 的数据模型。

**建议文件**
- `meta_harness/sdk/ports.py`
- `meta_harness/sdk/connection.py`
- `tests/sdk/test_connection_models.py`

**建议类 / 函数**
- `Input`, `Output`, `Event`
- `Connection`, `PendingConnection`
- `validate_connection()`

**要做的事**
- 定义端口和连接的 Pydantic 模型
- 类型匹配校验
- 引用完整性校验

**交付物**
- 端口和连接模型
- 校验函数
- 最小 fixture: valid connection, type mismatch, missing reference

### 17.8 第一批实现顺序

```text
project bootstrap (pyproject.toml, CI)
  -> SDK interface contracts + ADRs
     -> package structure (6 top-level packages)
        -> HarnessComponent base class
           -> HarnessAPI interface declaration
              -> ComponentManifest schema
```

### 17.9 第一批最小测试面
- `tests/sdk/test_component_base.py`
- `tests/sdk/test_api.py`
- `tests/sdk/test_manifest.py`
- `tests/test_bootstrap.py` (verify import and basic structure)

### 17.10 第一批完成定义
- 项目可安装、CI 可运行
- `HarnessComponent` 可被子类化，lifecycle hooks 可实现
- `HarnessAPI` interface declaration 可被组件使用
- `ComponentManifest` 有完整 Pydantic schema 和示例
- `ComponentPhase` transitions 有校验
- ADR-001 至 ADR-004 草案完成

---

## 18. Done 定义

一个 Epic 只有在以下条件同时满足时才算 Done：

- 核心类 / 接口可用
- 至少有一组测试或 fixture 覆盖主路径
- 结构化输出可被 downstream consumer 使用
- 没有引入与 wiki 设计文档相违背的假设

---

## 19. 结论

这个 backlog 的压缩原则是：
- 先稳定 SDK 和核心数据模型
- 再稳定连接引擎和组件拓扑
- 再实现 9 大核心组件
- 再建设安全链、观测和热加载
- 最后激活 Optimizer 和模板生态
- 最后做产品化和 rollout

因此，Meta-Harness 最推荐的实际起点不是直接实现 Optimizer 或安全链，而是：

> **先把 HarnessComponent、ComponentManifest、ConnectionEngine、GraphVersionManager 这条基础设施打牢。**

因为只有先把 SDK 和连接引擎组织起来，后面的组件实现、安全验证、自修改优化才会真正稳。
