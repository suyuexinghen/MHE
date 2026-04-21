# Aeloon Plugin SDK 调研纪要

本文整理 Aeloon Plugin SDK 的关键设计点，目标是为 Meta-Harness 的可插拔化改造提供可直接复用的模式参考。

## 1. 总体判断

Aeloon Plugin SDK 的核心价值不在于“能加载插件”这一点，而在于它把插件系统拆成了五个彼此解耦的层次：

1. **声明层**：`aeloon.plugin.json` 声明插件身份、能力和依赖；
2. **发现/加载层**：Discovery + Loader 负责扫描、校验、拓扑排序与导入；
3. **注册层**：`PluginAPI` + `PluginRegistry` 负责能力声明与原子提交；
4. **运行时层**：`PluginRuntime` 为插件提供隔离后的宿主能力；
5. **生命周期层**：`PluginManager` + `ServiceSupervisor` 负责 boot / activate / deactivate / shutdown。

这套分层特别适合 Meta-Harness，因为 Meta-Harness 本身就是“组件图 + 元层优化器 + 安全治理链”的系统。如果每一类组件都想支持替换，最重要的不是先写组件，而是先把**组件身份、接口契约、注册协议、运行时注入和治理约束**固定下来。

## 2. 目录与职责分解

Aeloon SDK 的主要代码位于 `aeloon/plugins/_sdk/`，职责分工非常清晰：

- `base.py`：定义 `Plugin`、`PluginService` 等抽象基类；
- `api.py`：定义 `PluginAPI`，作为插件声明能力的唯一入口；
- `registry.py`：定义 `PluginRegistry`，保存 commands / tools / services / hooks / middlewares / status providers；
- `runtime.py`：定义 `PluginRuntime` 与 `PluginLLMProxy`；
- `discovery.py`：扫描 bundled / entry points / workspace / extra paths；
- `loader.py`：做 manifest 校验、依赖拓扑排序、导入与实例化；
- `manager.py`：串起发现、加载、注册、激活、关闭全流程；
- `manifest.py`：定义 manifest schema；
- `hooks.py`：定义 HookEvent / HookType 以及分发语义；
- `types.py`：定义 `ServicePolicy`、`CommandContext`、`HookDecision` 等通用类型。

这个结构说明 Aeloon 并没有把“插件系统”做成一个大类，而是拆成多个小模块，各自只处理一种复杂度。

## 3. 插件基类设计

### 3.1 `Plugin`

`Plugin` 的生命周期接口非常克制：

- `register(api)`：同步、幂等、无 I/O；
- `activate(api)`：异步，允许执行启动期 I/O；
- `deactivate()`：异步，负责清理；
- `health_check()`：可选健康检查。

这个设计有两个关键点：

1. **声明阶段与运行阶段分离**：`register()` 只声明能力，不做副作用；
2. **能力发布先于启动行为**：插件先进入 registry，再进入 active 状态。

对于 Meta-Harness 很重要，因为很多组件替换要先验证接口、依赖和安全策略，再决定是否真正启用。

### 3.2 `PluginService`

`PluginService` 把“长生命周期后台任务”从主插件类中抽出来，单独交给 `ServiceSupervisor` 管理。

这意味着：

- 插件类负责“声明和编排”；
- 服务类负责“持续运行”；
- 监管器负责“超时、重启、健康检查”。

对 Meta-Harness 来说，这种拆分非常适合像：

- Shadow A/B runner
- Trace collector
- Rollback watcher
- Policy rule refresher
- Optimizer worker

这类持续运行模块。

## 4. `PluginAPI`：声明能力而不是直接改宿主

Aeloon 的 `PluginAPI` 不是让插件直接改全局状态，而是让插件向 API **登记意图**：

- `register_command`
- `register_tool`
- `register_service`
- `register_cli`
- `register_middleware`
- `register_hook`
- `register_config_schema`
- `register_status_provider`

这些调用先写入 pending 列表，直到 `_commit()` 才一次性写入 `PluginRegistry`。

### 启示

这是一种非常强的工程约束：

- 插件不能边注册边污染系统；
- 冲突检测可以在提交前完成；
- 若中间失败，可以整体回滚；
- 注册阶段天然适合做静态校验。

Meta-Harness 若要支持组件热替换，也应该采取同样策略：

- 候选组件先提交到 `PendingComponentSet`；
- 做 schema / contract / dependency / policy 校验；
- 通过后原子替换到活动图；
- 否则整体丢弃。

## 5. `PluginRegistry`：统一能力注册表

Aeloon 的 `PluginRegistry` 是真正的“插件系统内核”。它统一保存：

- 插件记录；
- commands；
- tools；
- services；
- middlewares；
- CLI builders；
- hooks；
- config schemas；
- status providers。

更关键的是，它的 `commit_plugin()` 会先做**完整冲突检测**，确认没有命名冲突或资源冲突，再一次性写入。

### 启示

Meta-Harness 不应只做“组件加载器”，而应有一个**Component Registry / Capability Registry**，至少记录：

- 组件类型（Memory / Evaluator / Proposer / Sandbox / Policy 等）；
- 组件实现 ID 与版本；
- 接口契约版本；
- 提供的 capability；
- 依赖的 capability；
- 可替换范围；
- 是否为 protected component；
- 当前状态（registered / validated / active / error / retired）。

换句话说，Aeloon 的 `PluginRegistry` 对 Meta-Harness 的对应物，不应只是“插件名表”，而应是**架构图中的能力目录 + 版本目录 + 治理目录**。

## 6. `PluginRuntime`：给插件受控宿主能力

Aeloon 的 `PluginRuntime` 提供的不是“宿主对象全集”，而是一组经过边界收敛的能力：

- `storage_path`
- `config`
- `logger`
- `llm`
- `process_direct()`
- `tool_execute()`
- `internal_session_key()`
- `add_deep_profile_section()`
- `agent_loop`（宿主引用）

这说明它把宿主能力分成两类：

1. **稳定、建议公开的能力**：storage / logger / config / llm；
2. **桥接型能力**：对主 AgentLoop 的有限访问。

### 启示

Meta-Harness 也应该给组件一个标准化运行时，而不是把整个系统对象直接注入进去。建议为每个组件提供 `ComponentRuntime`，其中包括：

- `component_id`
- `storage_path`
- `config`
- `logger`
- `metrics`
- `trace_writer`
- `event_bus`
- `artifact_store`
- `llm`
- `scheduler`
- `policy_client`
- `sandbox_client`
- `graph_view`（只读）
- `mutation_submit()`（受控写接口）

这样组件既能工作，又不会因为直接持有整个宿主内核而失控。

## 7. Discovery / Loader / Manager 的三段式设计

Aeloon 把插件加载过程拆成三段：

### 7.1 Discovery

只解决“哪里有插件”。

来源包括：

- bundled
- setuptools entry points
- workspace plugins
- extra configured paths

### 7.2 Loader

只解决“这个插件能否被导入、依赖是否满足、顺序是什么”。

功能包括：

- manifest requirement 校验；
- 依赖拓扑排序；
- 缺失依赖跳过；
- 循环依赖报错；
- import + instantiate。

### 7.3 Manager

只解决“在运行中的系统里，如何注册、激活、停用、关闭”。

### 启示

Meta-Harness 如果未来支持：

- 官方内置组件
- 用户自定义组件
- 第三方研究组件
- 在线模板市场组件

就必须保留这个三段式架构，否则 discovery、validation、activation 会混成一个难以审计的大流程。

## 8. Manifest 的价值

`aeloon.plugin.json` 并不只是元数据文件，它实际上承担了三个工程职责：

1. **身份声明**：`id`、`version`、`entry`；
2. **能力声明**：`provides`；
3. **依赖声明**：`requires`。

它让 Loader 在 import 前就能做大量工作。

### 启示

Meta-Harness 未来也应为组件包定义 manifest，例如 `metaharness.component.json`，至少包括：

- `id`
- `name`
- `version`
- `kind`
- `entry`
- `provides`
- `requires.capabilities`
- `requires.components`
- `requires.resources`
- `contract.input_schema`
- `contract.output_schema`
- `compatibility.graph_api`
- `safety.level`
- `safety.permissions`
- `hot_swap.mode`

这样，很多“组件能不能接到图里”的问题，可以在真正运行前解决。

## 9. Hook / Middleware / Service 三类扩展点

Aeloon 的一个重要优点是：它没有把所有扩展都塞进一个“Plugin.execute()”。它区分了三类扩展方式：

- **Hook**：对生命周期事件做订阅；
- **Middleware**：包裹主执行链；
- **Service**：长期运行后台逻辑。

### 启示

Meta-Harness 的扩展点也不应只有“替换组件”这一种。至少应区分：

- **Component Plugin**：替换图中的节点实现；
- **Meta Plugin**：替换 proposer / evaluator / selector / rollback judge；
- **Policy Hook**：在 mutation proposal、activation、tool execution 前后插入治理；
- **Observation Service**：持续收集 trace / metrics / evidence；
- **Lifecycle Middleware**：包裹任务执行轮次；
- **Migration Adapter**：负责老状态到新状态的映射。

## 10. 对 Meta-Harness 最值得借鉴的四点

### 10.1 两阶段注册

先声明，再提交，再激活。这个模式几乎应直接照搬。

### 10.2 统一注册表

不要让各类组件分散挂在多个 manager 上，否则难以做冲突校验、依赖解析和审计。

### 10.3 运行时注入

让组件依赖抽象运行时，而不是依赖内核细节。

### 10.4 生命周期隔离

把发现、校验、注册、激活、服务管理、关闭拆开，每一段单独负责。

## 11. 对 Meta-Harness 不应简单照搬的点

Aeloon SDK 很适合“面向 agent 平台功能扩展”的插件，但 Meta-Harness 还多了两类约束：

1. **图结构一致性**：插件不只是注册能力，还要能嵌入组件图；
2. **热替换安全性**：替换发生在运行中的系统里，必须考虑状态迁移与回滚。

因此 Meta-Harness 不能只做 Aeloon 那种“注册 command/tool/service”式 SDK，而需要更进一步，做成：

- 组件契约 SDK
- 组件图装配器
- mutation proposal / validation / activation pipeline
- rollback 与 provenance 一体化框架

## 12. 结论

Aeloon Plugin SDK 给 Meta-Harness 的最好启发不是“插件目录怎么组织”，而是：

- 用 manifest 提前声明；
- 用 registry 统一管理；
- 用 runtime 做能力隔离；
- 用 manager 编排生命周期；
- 用 staged commit 保证原子注册。

如果 Meta-Harness 要把不同组件真正做成可替换模块，最合理的路线不是先写很多组件，而是先定义：

1. 组件接口契约；
2. 组件 manifest；
3. 组件注册表；
4. 组件运行时；
5. 热替换校验与激活协议；
6. 安全治理钩子。

这六件事稳定以后，组件生态才能健康扩展。
