# Meta-Harness 插件化架构设计方案

本文讨论 Meta-Harness 如何参考 Aeloon Plugin SDK，演进成一个**可插件扩展、组件可替换、支持热切换与治理约束**的架构。

## 1. 设计目标

Meta-Harness 想解决的问题，不只是“能否给系统加插件”，而是更难的三个问题：

1. **如何让九大核心基础组件与元层组件成为可替换模块**；
2. **如何在运行中对候选组件做验证、切换、回滚**；
3. **如何让第三方扩展不破坏接口契约、安全规则和系统可审计性**。

因此目标架构必须同时满足：

- **扩展性**：支持内置组件、研究型组件、第三方组件；
- **可替换性**：同一组件位点可装配不同实现；
- **安全性**：替换前后都有校验与治理；
- **可观测性**：每次装配、替换、回滚都有证据对象；
- **热重构能力**：运行时支持 suspend-transform-resume。

## 2. 总体架构建议

建议把 Meta-Harness 设计成六层：

1. **Core Kernel 层**：任务执行、组件图调度、状态存储、trace 主线；
2. **Component SDK 层**：标准接口、manifest schema、runtime 注入、注册 API；
3. **Registry & Assembly 层**：组件注册表、能力匹配、依赖解析、图装配器；
4. **Validation & Governance 层**：契约校验、策略校验、沙箱验证、影子测试、回滚判断；
5. **Meta-Optimization 层**：proposer / evaluator / selector / rollback judge；
6. **Plugin / Component Ecosystem 层**：具体实现包，如不同 Memory、Planner、Sandbox、Policy 引擎。

可以把它理解成：

- Aeloon 的 `PluginManager + Registry + Runtime`
- 加上 Meta-Harness 特有的 `Graph Assembly + Safety Validation + Hot Swap`

两套机制叠加后的结果。

## 3. 什么应该被插件化

并不是所有代码都值得做成插件。建议分三层考虑。

### 3.1 第一层：九大核心基础组件的实现可替换

书中九大核心基础组件，本质上是**逻辑位点（slots）**，每个位点允许多个实现：

- Gateway
- Runtime / Orchestrator
- Memory
- ToolHub
- Planner / Reasoner
- Evaluator
- Observability
- Policy
- Identity / Session / Context（按最终书稿术语落位）

这些位点不必每个都允许任意数量实例，但至少应允许：

- 内置默认实现；
- 兼容实现；
- 实验实现；
- 高安全实现。

### 3.2 第二层：元层组件直接做成插件类型

元层组件更适合插件化，因为它们天然是“策略实现”：

- Proposer
- Search Strategy
- Mutation Generator
- Candidate Selector
- Rollback Judge
- Safety Analyzer
- Migration Planner

这类组件比基础组件更频繁迭代，也更适合做研究实验。

### 3.3 第三层：治理与观测扩展点

有些东西不应该替换主节点，而应该作为 hook / service / middleware 扩展点存在：

- 审计记录器
- Policy guard
- 成本预算控制器
- 风险标签器
- Trace enrichers
- 状态栏 / 监控上报器

## 4. 插件模型建议

建议 Meta-Harness 定义三类一等插件：

### 4.1 Component Plugin

对应组件图中的某个节点实现。

例如：

- `metaharness.memory.vectorstore`
- `metaharness.policy.rule_engine`
- `metaharness.sandbox.firecracker`

它们的共同特征是：

- 提供一个或多个 capability；
- 遵守某类输入输出契约；
- 可被图装配器接入具体 slot。

### 4.2 Meta Plugin

对应元层优化与控制逻辑。

例如：

- `metaharness.meta.proposer.log_gopher`
- `metaharness.meta.evaluator.hypervolume`
- `metaharness.meta.selector.pareto_bandit`

### 4.3 Governance Plugin

不直接替换节点，而是在生命周期关键点介入。

例如：

- `metaharness.governance.policy_veto`
- `metaharness.governance.shadow_gate`
- `metaharness.governance.rollback_watchdog`

这个区分很重要，因为三类插件的权限、运行方式和热切换语义不同。

## 5. SDK 应该提供什么

如果要写一套 Meta-Harness Plugin SDK，建议至少包括以下对象。

### 5.1 `ComponentPlugin` 基类

```python
class ComponentPlugin(ABC):
    def register(self, api: ComponentAPI) -> None: ...
    async def activate(self, api: ComponentAPI) -> None: ...
    async def deactivate(self) -> None: ...
    def health_check(self) -> dict[str, Any]: ...
```

这部分可直接借鉴 Aeloon 的 `Plugin`：

- `register()` 只声明能力；
- `activate()` 做外部连接、缓存预热、索引加载；
- `deactivate()` 做清理；
- `health_check()` 供治理层拉取健康状态。

### 5.2 `ComponentService` 基类

对长期运行任务进行托管，例如：

- rollback observer
- async metrics sink
- shadow executor
- background index builder

### 5.3 `ComponentAPI`

它是插件对系统“声明能力”的唯一入口，建议支持：

- `register_component(kind, impl)`
- `register_capability(name, schema)`
- `register_service(name, service_cls, policy=...)`
- `register_hook(event, handler, kind=...)`
- `register_middleware(name, middleware)`
- `register_config_schema(schema_cls)`
- `register_migration_adapter(adapter)`
- `register_validator(validator)`
- `register_status_provider(...)`

其中最关键的是前四个：组件、能力、服务、钩子。

### 5.4 `ComponentRuntime`

建议给插件的运行时能力包括：

- `config`
- `storage_path`
- `logger`
- `llm`
- `artifact_store`
- `trace_store`
- `metrics`
- `event_bus`
- `policy_client`
- `sandbox_client`
- `graph_reader`
- `mutation_submit()`
- `schedule_task()`

核心原则是：

- 给“能力”，不给“整个内核对象”；
- 对写操作统一走受控接口；
- 所有副作用都进入审计链。

## 6. 组件如何变成可替换模块

这里的关键不是把 Python 类挪到 plugin 目录，而是定义**标准接口 + 能力契约 + 装配规则**。

### 6.1 先定义 slot，而不是先定义实现

每个可替换组件位点都应有 slot 定义，例如：

- `memory.primary`
- `planner.primary`
- `evaluator.primary`
- `sandbox.high_risk`
- `policy.veto`

slot 定义应包含：

- 允许的 `kind`
- 必需 capability
- 可选 capability
- 版本要求
- 并发/状态约束
- 是否允许热切换
- 是否 protected

### 6.2 每个实现声明 provides / requires

例如某个 Sandbox 组件可以声明：

- provides: `sandbox.execute`, `sandbox.snapshot`, `sandbox.rollback`
- requires: `artifact_store.read`, `policy.check`

装配器只在 capability 匹配时允许接入。

### 6.3 用 contract 而不是类名耦合

组件之间不要依赖具体类名，而是依赖标准 contract，例如：

- 输入 schema
- 输出 schema
- 支持的 event types
- 失败语义
- timeout / retry 语义
- state snapshot 能力

这样 Memory 的一个实现换成另一个实现时，只要 contract 相同，上层就不必改。

## 7. 建议的 manifest schema

建议定义 `metaharness.component.json`：

```json
{
  "id": "metaharness.sandbox.firecracker",
  "name": "Firecracker Sandbox",
  "version": "0.1.0",
  "kind": "sandbox",
  "entry": "metaharness.plugins.sandbox.firecracker:FirecrackerSandbox",
  "provides": {
    "capabilities": ["sandbox.execute", "sandbox.snapshot", "sandbox.rollback"],
    "slots": ["sandbox.high_risk"]
  },
  "requires": {
    "plugins": ["metaharness.policy.core"],
    "resources": ["/usr/bin/firecracker"],
    "capabilities": ["artifact_store.read", "trace_store.write"]
  },
  "contracts": {
    "input_schema": "sandbox_request@v1",
    "output_schema": "sandbox_result@v1",
    "state_schema": "sandbox_state@v1"
  },
  "compatibility": {
    "graph_api": ">=1.0",
    "runtime_api": ">=1.0"
  },
  "safety": {
    "level": "high-risk",
    "permissions": ["net:deny-default", "fs:readonly-root"],
    "hot_swap": "drain-and-resume"
  }
}
```

与 Aeloon manifest 相比，Meta-Harness 的 manifest 需要多出三块：

- `kind / slots`
- `contracts`
- `safety / hot_swap`

因为这里的核心不是注册命令，而是加入运行中的组件图。

## 8. Registry 该怎么设计

建议定义统一的 `ComponentRegistry`，保存以下信息：

- component record
- plugin record
- slot bindings
- capability index
- dependency graph
- contract versions
- active graph version
- protected component list
- deprecation / retirement state

一个可行的数据结构是：

- `components_by_id`
- `components_by_kind`
- `slot_bindings`
- `capability_providers`
- `graph_versions`
- `pending_mutations`

### 为什么必须统一

因为 Meta-Harness 的问题不是“这个插件存在吗”，而是：

- 它能不能接到当前图上；
- 它有没有满足依赖；
- 它是不是替换了 protected component；
- 替换后是否需要迁移状态；
- 回滚时该恢复哪个 graph version。

这些都要求 registry 同时看见插件层和图层。

## 9. 生命周期建议

强烈建议直接借鉴 Aeloon 的 staged lifecycle，但扩展成适合 Meta-Harness 的八阶段：

1. **Discover**：发现候选组件；
2. **Validate Static**：检查 manifest、版本、依赖、contract；
3. **Register Pending**：写入 pending registry；
4. **Assemble Candidate Graph**：在候选图中完成绑定；
5. **Validate Dynamic**：沙箱、影子测试、策略审查；
6. **Activate**：进入观察窗口；
7. **Commit Graph**：切换 active graph version；
8. **Observe / Rollback**：持续观测，异常时回滚。

可以表示为：

```text
candidate discovered
  -> statically valid
  -> registered
  -> assembled
  -> dynamically validated
  -> activated
  -> committed
  -> observed / rolled back
```

这比 Aeloon 多了图装配和动态验证两个阶段，这是 Meta-Harness 特有需求。

## 10. 热替换协议建议

热替换应统一走一个标准协议，而不是让各组件各自定义。建议定义：

### 10.1 `prepare_swap()`

旧组件与新组件都收到切换通知，返回：

- 是否可切换；
- 是否需要 drain；
- 是否要求 quiescent point；
- 预计 state schema 版本。

### 10.2 `export_state()` / `import_state()`

由旧实现导出状态，新实现导入状态。中间可插入 migration adapter。

### 10.3 `resume()`

完成 cutover 后恢复流量。

### 10.4 `abort_swap()`

任何一步失败时撤销 pending mutation。

这实际上就是书中 suspend-transform-resume 的工程协议化版本。

## 11. Governance 要怎么接进去

插件化会放大系统复杂度，所以治理层必须是一等公民。

建议在以下节点提供 hook：

- `BEFORE_REGISTER_COMPONENT`
- `AFTER_REGISTER_COMPONENT`
- `BEFORE_ASSEMBLE_GRAPH`
- `AFTER_ASSEMBLE_GRAPH`
- `BEFORE_ACTIVATE_CANDIDATE`
- `AFTER_SHADOW_TEST`
- `BEFORE_COMMIT_GRAPH`
- `ROLLBACK_TRIGGERED`
- `EVIDENCE_RECORDED`

其中有三类 hook 非常关键：

1. **Guard hooks**：可 veto；
2. **Mutate hooks**：可补充默认策略或风险标签；
3. **Reduce hooks**：收集多方评估结果。

这部分可直接借鉴 Aeloon 的 `HookType.GUARD / MUTATE / REDUCE / NOTIFY` 模型。

## 12. 建议的目录结构

如果未来实现 Meta-Harness Plugin SDK，目录可参考：

```text
metaharness/
├── core/
│   ├── kernel/
│   ├── graph/
│   ├── runtime/
│   └── execution/
├── sdk/
│   ├── base.py
│   ├── api.py
│   ├── runtime.py
│   ├── registry.py
│   ├── discovery.py
│   ├── loader.py
│   ├── manifest.py
│   ├── hooks.py
│   ├── services.py
│   └── types.py
├── governance/
│   ├── validators/
│   ├── policy/
│   ├── sandbox/
│   ├── shadow/
│   └── rollback/
├── plugins/
│   ├── memory/
│   ├── planner/
│   ├── evaluator/
│   ├── sandbox/
│   ├── policy/
│   └── meta/
└── manifests/
```

这里 `sdk/` 基本对应 Aeloon 的 `_sdk/`，但 `governance/` 和 `core/graph/` 是 Meta-Harness 自己必须额外补出的部分。

## 13. 最推荐的落地路线

如果现在开始实现，我建议按以下顺序推进，而不是一上来就做全量插件化。

### Phase 1：先固定抽象

先定义：

- component kinds
- slot definitions
- capability vocabulary
- manifest schema
- runtime API

这一步不急着热切换。

### Phase 2：做静态插件化

先支持：

- discover / load / register / instantiate
- 离线装配图
- 启动前校验

也就是先做到“启动时可替换”。

### Phase 3：再做动态切换

引入：

- pending candidate graph
- migration adapter
- shadow validation
- rollback watcher

### Phase 4：最后接入元层优化器

让 proposer / evaluator / selector 输出的是：

- 插件候选；
- slot rebinding proposal；
- config patch；
- migration recipe。

也就是让元层优化器操作的是**标准插件与标准图接口**，而不是操作散乱的内部类。

## 14. 最终建议

如果问题是：“Meta-Harness 要不要参考 Aeloon Plugin SDK 设计成插件架构？”

答案是：**应该参考，但不能停留在普通插件系统层面，必须升级成面向组件图与热替换的 Plugin + Contract + Assembly + Governance 架构。**

最值得直接借鉴 Aeloon 的部分有四个：

- `register() -> commit() -> activate()` 的 staged lifecycle；
- `PluginRegistry` 式统一注册表；
- `PluginRuntime` 式受控运行时注入；
- `Discovery / Loader / Manager` 的三段式分层。

最需要 Meta-Harness 自己新增的部分有五个：

- slot / capability 体系；
- component contract schema；
- candidate graph assembly；
- suspend-transform-resume 热替换协议；
- validation / rollback / evidence 一体化治理链。

## 15. 一句话总结

Aeloon Plugin SDK 解决的是“如何把能力安全地接入宿主”；
而 Meta-Harness 还要进一步解决“如何把组件安全地接入、替换并治理一个运行中的自我改进系统”。

所以最合理的方向是：

**以 Aeloon Plugin SDK 为骨架，以组件契约、图装配和安全治理为增量，构建 Meta-Harness 的 Component Plugin SDK。**
