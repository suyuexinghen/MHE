  ---
  Meta-Harness Plugin SDK 架构设计

  核心问题：从"固定组件图"到"可插拔组件市场"

  Meta-Harness 书稿提出了 9 个核心组件 + 1 个元层优化器，但当前设计是概念层的——它们之间如何通过标准化
  接口实现可替换、可热插拔、可由第三方扩展，还没有落地。

  Aeloon Plugin SDK 提供了一个成熟的参考模式。关键映射关系如下：

  Aeloon SDK → Meta-Harness SDK 的架构映射

  ┌──────────────────────────┬──────────────────────────────┬───────────────────────────────────┐
  │       Aeloon 概念        │     Meta-Harness 对应物      │               说明                │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ Plugin 基类              │ HarnessComponent 基类        │ 每个核心组件就是一个"系统插件"    │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ aeloon.plugin.json       │ harness.component.json       │ 声明组件的                        │
  │                          │                              │ Interface（Input/Output/Event）   │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ PluginAPI.register_comma │ HarnessAPI.declare_input() / │ 声明端口类型                      │
  │ nd()                     │  declare_output()            │                                   │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ PluginRegistry           │ ComponentRegistry            │ 存储组件实例、连接关系、兼容性校  │
  │                          │                              │ 验结果                            │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ PluginManager.boot()     │ HarnessRuntime.boot()        │ 发现→校验→拓扑排序→实例化→激活    │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ PluginRuntime            │ ComponentRuntime             │ 提供隔离的                        │
  │                          │                              │ storage/logger/config/sandbox     │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ HookDispatcher           │ PolicyConstitutionalLayer    │ GUARD hook ≈ Policy 宪法否决      │
  │ (GUARD/MUTATE/NOTIFY)    │                              │                                   │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ ServiceSupervisor        │ SandboxOrchestrator          │ 管理沙箱生命周期、超时、重启      │
  ├──────────────────────────┼──────────────────────────────┼───────────────────────────────────┤
  │ PluginDiscovery (4 源)   │ ComponentDiscovery (bundled/ │ 多源发现组件                      │
  │                          │ template/market/custom)      │                                   │
  └──────────────────────────┴──────────────────────────────┴───────────────────────────────────┘

  建议的分层架构

  ┌─────────────────────────────────────────────────────┐
  │ Layer 5: Meta-Cycle (Optimizer + MetaCycle Engine)   │
  │   触发重长 → 搜索候选 → 四级安全链路 → 收敛判断      │
  ├─────────────────────────────────────────────────────┤
  │ Layer 4: Component SDK                               │
  │   HarnessComponent 基类                              │
  │   HarnessAPI (declare_input/output/event)            │
  │   ComponentRuntime (storage/logger/sandbox/config)   │
  │   ComponentRegistry (连接图 + 兼容性校验)             │
  │   ComponentDiscovery (bundled/template/market)       │
  ├─────────────────────────────────────────────────────┤
  │ Layer 3: Governance Plane                            │
  │   PolicyLayer (宪法规则 + GUARD hooks)                │
  │   ObservabilityBus (Trace/Replay/Audit)              │
  │   ProvenanceStore (Merkle-anchored evidence chain)   │
  ├─────────────────────────────────────────────────────┤
  │ Layer 2: Infrastructure                              │
  │   SandboxManager (WASM → gVisor → Firecracker)       │
  │   CheckpointManager (snapshot + ARIES log replay)    │
  │   ABTestRouter (shadow traffic + statistical engine) │
  ├─────────────────────────────────────────────────────┤
  │ Layer 1: Core Runtime                                │
  │   HarnessRuntime (boot/shutdown/hot-reload)          │
  │   ConnectionEngine (graph topology + data routing)   │
  │   ConfigParser (XML/XSD + schema validation)         │
  └─────────────────────────────────────────────────────┘

  关键接口定义

  1. HarnessComponent（类似 Plugin 基类）

  from abc import ABC, abstractmethod
  from typing import Any

  class HarnessComponent(ABC):
      """Base class for all meta-harness components.

      Analogous to aeloon.plugin_sdk.base.Plugin, but oriented
      around port-based interface contracts instead of commands/tools.
      """

      @abstractmethod
      def declare_interface(self, api: HarnessAPI) -> None:
          """Declare Input/Output/Event ports. Synchronous, no I/O.

          Maps to <Interface> in XML:
            api.declare_input("command", type="Command", required=True)
            api.declare_output("action", type="Action")
            api.declare_event("on_config_reload")
          """

      @abstractmethod
      async def activate(self, runtime: ComponentRuntime) -> None:
          """Start the component. Async, I/O allowed."""

      @abstractmethod
      async def deactivate(self) -> None:
          """Graceful shutdown."""

      async def transform_state(self, old_state: dict, new_schema: dict) -> dict:
          """Optional: state migration for hot-reload (Suspend-Transform-Resume)."""
          return old_state  # default: identity

      def health_check(self) -> dict[str, Any]:
          return {"status": "unknown"}

  2. HarnessAPI（类似 PluginAPI）

  class HarnessAPI:
      """Registration API for a single component.

      Inspired by aeloon.plugin_sdk.api.PluginAPI's staged registration:
      component.declare_interface(api) → api._commit() → component.activate()
      """

      # --- Interface declaration ---
      def declare_input(self, name: str, type: str, required: bool = True) -> None: ...
      def declare_output(self, name: str, type: str) -> None: ...
      def declare_event(self, name: str) -> None: ...

      # --- Connection registration ---
      def register_connection_handler(
          self, from_port: str, handler: Callable, trigger: str | None = None
      ) -> None: ...

      # --- Hook registration (for Policy/Governance) ---
      def register_hook(
          self, event: str, handler: Callable, kind: HookType = HookType.NOTIFY, priority: int = 0
      ) -> None: ...

      # --- Sandbox request ---
      def request_sandbox(self, policy: SandboxPolicy) -> SandboxHandle: ...

      # --- Staged commit (same pattern as PluginAPI._commit) ---
      def _commit(self) -> None: ...   # atomic write to ComponentRegistry
      def _rollback(self) -> None: ... # on failure

  3. ComponentRuntime（类似 PluginRuntime）

  class ComponentRuntime:
      """Isolated runtime context for a single component.

      Mirrors aeloon.plugin_sdk.runtime.PluginRuntime:
      - storage_path: component-private data
      - logger: namespaced logger
      - config: component-specific config dict
      - sandbox: access to sandbox infrastructure
      """

      @property
      def component_id(self) -> str: ...
      @property
      def storage_path(self) -> Path: ...
      @property
      def logger(self) -> Logger: ...
      @property
      def config(self) -> Mapping[str, Any]: ...

      # Cross-component communication (via ConnectionEngine)
      async def emit(self, port_name: str, data: Any) -> None: ...
      async def send_to(self, component_id: str, input_name: str, data: Any) -> None: ...

      # Sandbox
      def create_sandbox(self, policy: SandboxPolicy) -> SandboxHandle: ...

      # Observability
      def trace(self, operation: str, **tags) -> TraceSpan: ...

  4. ComponentManifest（类似 aeloon.plugin.json）

  {
    "id": "harness.evaluation",
    "name": "Evaluation Component",
    "version": "1.0.0",
    "type": "Evaluation",
    "entry": "harness_components.evaluation:EvaluationComponent",
    "interface": {
      "inputs": [
        {"name": "task_result", "type": "TaskResult", "required": true},
        {"name": "ground_truth", "type": "GroundTruth", "required": false}
      ],
      "outputs": [
        {"name": "performance_vector", "type": "PerformanceVector"},
        {"name": "loop_guard_signal", "type": "LoopGuardSignal"}
      ],
      "events": ["on_bottleneck_detected", "on_convergence"]
    },
    "provides": {
      "hooks": ["BEFORE_SELF_MODIFY", "AFTER_EVALUATE"],
      "governance": ["loop_guard", "quality_control"]
    },
    "requires": {
      "harness_version": ">=1.0.0",
      "protected": false
    },
    "protected": false,
    "state_schema_version": 1
  }

  组件可替换性的关键机制

  1. 接口契约校验（编译时）

  class CompatibilityValidator:
      """Runs the 5 rules from Chapter 3 before any hot-reload."""

      def validate(self, config: HarnessConfig) -> list[ValidationError]:
          errors = []
          errors += self._check_type_matching(config.connections)
          errors += self._check_event_declaration(config.connections, config.components)
          errors += self._check_input_completeness(config.components, config.connections)
          errors += self._check_id_uniqueness(config.components)
          errors += self._check_acyclicity(config.connections)  # optional
          return errors

  2. 受保护组件（Policy/Identity/Evaluation-QC）

  Manifest 中的 "protected": true 标记意味着：
  - Optimizer 不能直接修改此组件的配置
  - 任何修改请求必须通过 Human Review Gate
  - 组件代码完整性通过 Merkle hash 校验

  3. 热加载协议（Suspend-Transform-Resume）

  class HotReloadProtocol:
      """Manages zero-downtime component replacement.

      Inspired by Erlang code_change + Aeloon's staged _commit/_rollback.
      """

      async def execute(self, old_component: HarnessComponent,
                        new_component: HarnessComponent,
                        runtime: ComponentRuntime) -> None:
          # Phase 1: Suspend — buffer incoming messages
          old_state = await old_component.suspend()

          # Phase 2: Transform — migrate state to new schema
          new_state = await new_component.transform_state(old_state, new_schema)

          # Phase 3: Resume — activate new component with migrated state
          await new_component.activate(runtime)
          await new_component.resume(new_state)

          # Phase 4: Verify — observability monitors health
          # If degradation detected → auto-rollback to checkpoint

  4. 模板库作为"半成品组件"

  class ComponentTemplate:
      """A partially-implemented component that Optimizer can instantiate.

      Like Aeloon's plugin concept but with slot-filling:
      - The skeleton (interface + flow) is pre-verified
      - Only specific slots (prompt text, thresholds) are filled by Optimizer/LLM
      """

      template_id: str          # e.g., "BM25Retriever"
      base_type: str            # e.g., "Memory"
      slots: list[TemplateSlot] # e.g., [{"name": "top_k", "type": "int", "range": [1, 100]}]
      interface: InterfaceDef   # pre-declared inputs/outputs/events

      def instantiate(self, slot_values: dict[str, Any]) -> HarnessComponent:
          """Fill slots and return a concrete component instance."""

  与 Aeloon Plugin SDK 的关键差异

  ┌──────────┬───────────────────────┬─────────────────────────────────────┐
  │   维度   │      Aeloon SDK       │          Meta-Harness SDK           │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 注册粒度 │ 命令/工具/服务/中间件 │ Input/Output/Event 端口             │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 组件通信 │ 通过 AgentLoop 间接   │ 通过 ConnectionEngine 直连          │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 安全模型 │ GUARD hooks（工具级） │ 四级安全链路（组件级）              │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 热加载   │ 不支持                │ Suspend-Transform-Resume            │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 自我修改 │ 无                    │ Optimizer + Policy 宪法层           │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 状态迁移 │ 无                    │ transform_state() 回调              │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 沙箱     │ 无内置                │ 三级纵深（WASM→gVisor→Firecracker） │
  ├──────────┼───────────────────────┼─────────────────────────────────────┤
  │ 审计     │ Hook NOTIFY           │ Merkle-anchored ProvenanceStore     │
  └──────────┴───────────────────────┴─────────────────────────────────────┘

  建议的实施路径

  1. 先写接口，不写实现：将上述 HarnessComponent、HarnessAPI、ComponentRuntime、ComponentManifest
  定义为 meta_harness/sdk/ 下的抽象基类和 Pydantic schema
  2. 用 Aeloon SDK 的 lifecycle 验证：借鉴 PluginManager.boot() 的
  discover→validate→resolve→register→commit→activate 六阶段，证明组件图的编排可行
  3. 先实现 3 个核心组件：Runtime（最小调度器）、Memory（JSONL
  存储）、Evaluation（性能向量计算），作为参考实现
  4. Optimizer 作为元层插件：不参与组件图的正常数据流，只在 MetaCycle 触发时介入
  5. Policy 不是一个普通组件：它是独立进程，通过 GUARD hooks 拦截所有 Optimizer 的修改请求

  这个设计让每个 Meta-Harness 组件都可以像 Aeloon 插件一样被独立开发、测试、替换，同时通过接口契约和
  兼容性校验保证组合的正确性。需要我深入某个具体部分吗？
