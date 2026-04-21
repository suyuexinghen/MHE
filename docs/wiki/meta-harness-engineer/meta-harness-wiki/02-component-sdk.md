# 02. 组件 SDK 架构

本章把 Meta-Harness 的"9 core components + Optimizer"落到一套可实现、可验证、可替换的组件 SDK 上。目标不是再造一个泛化插件系统，而是定义一组面向**组件图装配、slot/capability 约束、staged lifecycle、contracts、pending mutations、graph versions**的工程协议。

## 1. 设计目标与边界

Meta-Harness 的组件 SDK 需要同时解决四类问题：

| 目标 | 说明 | 对应机制 |
|---|---|---|
| 可发现 | 组件可以来自内置、模板、市场、用户路径 | discovery sources |
| 可装配 | 组件不是"挂到宿主"就结束，而是要装入 slot | manifest + contracts + capability matching |
| 可切换 | 运行中允许 staged activation / rollback / graph cutover | pending mutations + graph versions |
| 可治理 | 任何替换都要经过静态校验和动态验证 | validation pipeline + protected components |

与 Aeloon Plugin SDK 相比，Meta-Harness 的增量不在"如何注册命令/工具"，而在"如何把一个实现安全地接到运行中的组件图上"。因此 SDK 的一等对象是：

- `HarnessComponent`：组件实现基类
- `HarnessAPI`：声明端口、hooks、capabilities、slot 绑定意图的 API
- `ComponentRuntime`：受控运行时注入
- `ComponentManifest`：组件身份、contracts、capabilities、safety、slots 的声明格式
- `ComponentLoader`：发现、校验、导入、实例化、挂入候选图
- `ComponentRegistry`：组件目录、slot 绑定、pending mutations、graph versions 的统一注册表

## 2. 分层视图

```text
Meta-Harness Runtime
├── Core Runtime
│   ├── HarnessRuntime
│   ├── ConnectionEngine
│   └── GraphVersionManager
├── Component SDK
│   ├── HarnessComponent
│   ├── HarnessAPI
│   ├── ComponentRuntime
│   ├── ComponentManifest
│   └── ComponentLoader
├── Governance Plane
│   ├── ContractValidator
│   ├── PolicyGuard
│   ├── ShadowValidator
│   └── RollbackJudge
└── Meta Layer
    └── Optimizer
```

这里有两个重要边界：

1. **Optimizer 不直接改活动图**。它只提交 mutation proposal，生成 `pending mutations`。
2. **ConnectionEngine 不关心组件内部实现**。它只消费组件声明的 contracts、slots、capabilities 和 graph bindings。

## 3. `HarnessComponent`：组件抽象基类

`HarnessComponent` 对应 Aeloon 中的 `Plugin`，但注册粒度从 command/tool/service 变成了 input/output/event/slot/capability。

### 3.1 生命周期原则

- `declare_interface()`：同步、幂等、无 I/O，只做声明
- `activate()`：异步，可做启动 I/O
- `deactivate()`：异步，优雅停机
- `export_state()` / `import_state()`：用于 staged replacement
- `health_check()`：供观测和回滚判断读取

### 3.2 建议接口

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any


class ComponentPhase(str, Enum):
    """组件生命周期阶段。"""
    DISCOVERED = "discovered"
    VALIDATED_STATIC = "validated_static"
    ASSEMBLED = "assembled"
    VALIDATED_DYNAMIC = "validated_dynamic"
    ACTIVATED = "activated"
    COMMITTED = "committed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class ComponentType(str, Enum):
    """组件类型分类。"""
    CORE = "core"
    TEMPLATE = "template"
    CUSTOM = "custom"


class HarnessComponent(ABC):
    """Meta-Harness 组件的抽象基类。"""

    component_type: ComponentType = ComponentType.CUSTOM
    protected: bool = False

    @abstractmethod
    def declare_interface(self, api: HarnessAPI) -> None:
        """声明 contracts、ports、capabilities、hooks。禁止 I/O。"""

    @abstractmethod
    async def activate(self, runtime: ComponentRuntime) -> None:
        """启动组件，允许加载模型、建立连接、预热缓存。"""

    @abstractmethod
    async def deactivate(self) -> None:
        """释放资源，结束后台任务。"""

    async def export_state(self) -> dict[str, Any]:
        return {}

    async def import_state(self, state: Mapping[str, Any]) -> None:
        return None

    async def transform_state(
        self,
        old_state: Mapping[str, Any],
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        return dict(old_state)

    def health_check(self) -> dict[str, Any]:
        return {"status": "unknown"}
```

### 3.3 设计要点

| 方法 | 是否允许 I/O | 为什么 |
|---|---|---|
| `declare_interface()` | 否 | 保证静态校验可重复、可回滚 |
| `activate()` | 是 | 加载索引、连接服务、启动 worker |
| `deactivate()` | 是 | 支持优雅关闭和 drain |
| `transform_state()` | 否，最好纯函数化 | 便于迁移测试与回滚 |

### 3.4 生命周期阶段说明

| 阶段 | 方法 | 说明 |
|------|------|------|
| DISCOVERED | — | ComponentLoader 发现 manifest 并加载 |
| VALIDATED_STATIC | `declare_interface()` | 静态校验：类型匹配、事件声明、ID 唯一 |
| ASSEMBLED | — | ConnectionEngine 组装候选图（含 pending mutations） |
| VALIDATED_DYNAMIC | `activate()` | 动态校验：沙箱执行、连接测试 |
| ACTIVATED | — | 组件正式运行 |
| COMMITTED | — | 候选图提交为当前生产图 |
| FAILED | — | 任何阶段失败 |
| SUSPENDED | `export_state()` | 热替换时挂起 |

> **注**：早期实现中曾有 `REGISTERED_PENDING` 阶段，用于描述组件注册到 pending 区的中间状态。在 staged lifecycle 的规范表述中，registration 仍作为实现步骤存在（组件声明写入 pending mutations），但不再作为一个独立的 canonical lifecycle phase。这避免了生命周期状态与 pending mutations 机制的语义混淆。

## 4. `HarnessAPI`：注册与声明入口

Meta-Harness 不应该允许组件在 `declare_interface()` 阶段直接改动全局图结构，而是像 Aeloon `PluginAPI` 一样，先把意图写入 pending 区，再统一提交。

### 4.1 核心职责

| 类别 | API | 作用 |
|---|---|---|
| 端口声明 | `declare_input` / `declare_output` / `declare_event` | 建立 contracts surface |
| 能力声明 | `provide_capability` / `require_capability` | 建立 capability graph |
| slot 绑定意图 | `bind_slot` / `reserve_slot` | 让装配器知道组件想挂到哪个位点 |
| hooks | `register_hook` | 参与治理与生命周期事件 |
| 服务/后台任务 | `register_service` | 托管长期运行逻辑 |
| staged commit | `_commit` / `_rollback` | 原子写入 registry |

### 4.2 建议接口

```python
class HarnessAPI:
    def __init__(
        self,
        component_id: str,
        version: str,
        config: Mapping[str, Any],
        runtime: ComponentRuntime,
        registry: ComponentRegistry,
    ) -> None:
        self._component_id = component_id
        self._version = version
        self._config = config
        self._runtime = runtime
        self._registry = registry

        self._pending_inputs: list[InputPort] = []
        self._pending_outputs: list[OutputPort] = []
        self._pending_events: list[EventPort] = []
        self._pending_connection_handlers: list[ConnectionHandlerRecord] = []
        self._pending_hooks: list[HookRecord] = []
        self._pending_services: list[ServiceRecord] = []
        self._pending_migration_adapters: list[MigrationAdapterRecord] = []
        self._pending_validators: list[ValidatorRecord] = []

    @property
    def id(self) -> str:
        return self._component_id

    @property
    def version(self) -> str:
        return self._version

    @property
    def config(self) -> Mapping[str, Any]:
        return self._config

    @property
    def runtime(self) -> ComponentRuntime:
        return self._runtime

    def declare_input(
        self,
        name: str,
        type: str,
        *,
        required: bool = True,
        description: str = "",
    ) -> None: ...

    def declare_output(
        self,
        name: str,
        type: str,
        *,
        description: str = "",
    ) -> None: ...

    def declare_event(self, name: str, payload_type: str | None = None) -> None: ...

    def provide_capability(self, capability: str) -> None: ...
    def require_capability(self, capability: str) -> None: ...

    def bind_slot(self, slot: str, *, mode: str = "primary") -> None: ...
    def reserve_slot(self, slot: str) -> None: ...

    def register_connection_handler(
        self, input_name: str, handler: Callable[..., Any], *, priority: int = 0
    ) -> None: ...

    def register_hook(
        self, event: str, handler: Callable[..., Any], *,
        kind: HookKind = HookKind.NOTIFY, priority: int = 0, matcher: str | None = None
    ) -> None: ...

    def register_service(
        self, name: str, service_cls: type[ComponentService], *, policy: ServicePolicy | None = None
    ) -> None: ...

    def register_migration_adapter(
        self, from_version: str, to_version: str,
        adapter: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> None: ...

    def register_validator(
        self, name: str, validator: Callable[[dict[str, Any]], list[str]], *,
        phase: ValidationPhase = ValidationPhase.DYNAMIC
    ) -> None: ...

    def _commit(self) -> None:
        self._registry.commit_component(
            self._component_id,
            inputs=self._pending_inputs,
            outputs=self._pending_outputs,
            events=self._pending_events,
            connection_handlers=self._pending_connection_handlers,
            hooks=self._pending_hooks,
            services=self._pending_services,
            migration_adapters=self._pending_migration_adapters,
            validators=self._pending_validators,
        )
        self._clear_pending()

    def _rollback(self) -> None:
        self._clear_pending()
```

### 4.3 pending mutations 模型

和 Aeloon 的 staged registration 一样，Meta-Harness 应把所有注册操作写到 pending 集合中：

```text
pending mutations
├── component record draft
├── port declarations draft
├── capability declarations draft
├── slot binding draft
├── hook registrations draft
└── service registrations draft
```

只有通过静态校验后，`_commit()` 才把这批草案原子写入 `ComponentRegistry` 对应的 candidate graph。

## 5. `ComponentRuntime`：受控运行时上下文

`ComponentRuntime` 对应 Aeloon 的 `PluginRuntime`。原则仍然是"给能力，不给整个宿主对象"。

### 5.1 运行时注入内容

| 属性/方法 | 用途 |
|---|---|
| `component_id` | 当前组件身份 |
| `slot_binding` | 当前绑定到的 slot |
| `storage_path` | 组件私有状态目录 |
| `logger` | 带命名空间日志 |
| `config` | 组件配置片段 |
| `graph_view` | 当前 graph version 的只读视图 |
| `emit()` | 向 output port 发消息 |
| `send_to()` | 直接向目标 input port 发送 |
| `trace()` | 写入观测链路 |
| `policy_client` | 请求治理判断 |
| `sandbox_client` | 创建隔离执行环境 |
| `submit_mutation()` | 受控提交 mutation proposal |

### 5.2 建议接口

```python
class ComponentRuntime:
    def __init__(
        self,
        harness: HarnessRuntime,
        component_id: str,
        config: Mapping[str, Any],
        storage_base: Path,
    ) -> None:
        self._harness = harness
        self._component_id = component_id
        self._config = config
        self._storage_path = storage_base / component_id.replace(".", "/")
        self._logger = logging.getLogger(f"metaharness.component.{component_id}")

    @property
    def component_id(self) -> str:
        return self._component_id

    @property
    def storage_path(self) -> Path:
        self._storage_path.mkdir(parents=True, exist_ok=True)
        return self._storage_path

    @property
    def config(self) -> Mapping[str, Any]:
        return self._config

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def metrics(self) -> MetricsCollector:
        return self._harness.metrics

    @property
    def trace_store(self) -> TraceStore:
        return self._harness.trace_store

    @property
    def event_bus(self) -> EventBus:
        return self._harness.event_bus

    @property
    def llm(self) -> ComponentLLMProxy:
        return self._harness.llm_proxy

    @property
    def sandbox_client(self) -> SandboxClient:
        return self._harness.sandbox_client

    @property
    def graph_reader(self) -> GraphReader:
        return self._harness.graph_reader

    @property
    def mutation_submit(self) -> MutationSubmitter:
        return self._harness.mutation_submitter

    async def process_direct(self, content: str, **kwargs: Any) -> str: ...
    async def tool_execute(self, tool_name: str, params: dict[str, Any]) -> str: ...
```

### 5.3 ComponentRuntime 与 PluginRuntime 对比

| 能力 | PluginRuntime (Aeloon) | ComponentRuntime (Meta-Harness) |
|------|----------------------|-------------------------------|
| ID | `plugin_id` | `component_id` |
| 存储 | `storage_path` | `storage_path`（同） |
| 配置 | `config` | `config`（同） |
| 日志 | `logger` | `logger`（同） |
| LLM | `llm` (PluginLLMProxy) | `llm` (ComponentLLMProxy，受 Policy 限速) |
| 指标 | 无 | `metrics` (MetricsCollector) |
| 轨迹 | 无 | `trace_store` (TraceStore) |
| 事件 | 无 | `event_bus` (EventBus) |
| 沙箱 | 无 | `sandbox_client` (SandboxClient) |
| 图视图 | 无 | `graph_reader` (GraphReader) |
| 变更 | 无 | `mutation_submit` (MutationSubmitter) |
| 代理执行 | `process_direct()` / `tool_execute()` | 同 + 受 Policy 约束 |

## 6. Manifest Schema：组件身份与契约声明

Meta-Harness 的 manifest 不能只描述 `id/version/entry`，还必须描述：

- 组件属于哪个 `kind`
- 它能绑定哪些 `slots`
- 它提供/依赖哪些 `capabilities`
- 它公开哪些 `contracts`
- 它是否是 `protected component`
- 它支持何种 hot-swap 模式
- 它的 `state_schema_version` 与 graph 兼容性

### 6.1 建议 manifest 示例

```json
{
  "id": "metaharness.evaluation.default",
  "name": "Default Evaluation Component",
  "version": "1.0.0",
  "kind": "evaluation",
  "entry": "metaharness.components.evaluation:EvaluationComponent",
  "slots": ["evaluation.primary"],
  "contracts": {
    "inputs": [
      {"name": "task_result", "contract": "TaskResult@v1", "required": true}
    ],
    "outputs": [
      {"name": "performance_vector", "contract": "PerformanceVector@v1"},
      {"name": "loop_guard_signal", "contract": "LoopGuardSignal@v1"}
    ],
    "events": [
      {"name": "on_bottleneck_detected", "payload": "BottleneckReport@v1"}
    ]
  },
  "provides": {
    "capabilities": ["evaluation.score", "evaluation.loop_guard"]
  },
  "requires": {
    "capabilities": ["memory.read", "observability.trace.write"],
    "graph_api": ">=1.0",
    "runtime_api": ">=1.0"
  },
  "safety": {
    "protected": false,
    "hot_swap": "suspend-transform-resume",
    "sandbox_level": "standard"
  },
  "state_schema_version": 2
}
```

### 6.2 schema 字段解释

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | 全局唯一组件 ID |
| `kind` | 是 | 组件类型，如 `memory`、`policy`、`planner` |
| `entry` | 是 | `module:Class` 导入入口 |
| `slots` | 是 | 可绑定位点列表 |
| `contracts` | 是 | ports 与 payload contracts |
| `provides.capabilities` | 是 | 声明可提供能力 |
| `requires.capabilities` | 否 | 声明装配前置能力 |
| `safety.protected` | 是 | 是否受保护 |
| `safety.hot_swap` | 是 | 热切换协议类型 |
| `state_schema_version` | 是 | 迁移和恢复依据 |

## 7. Discovery Sources：组件来源与优先级

参考 Aeloon 的四源发现模型，Meta-Harness 可以保留同样的分层，但语义改成"组件包"而不是"功能插件"。

| 来源 | 说明 | 优先级建议 | 典型用途 |
|---|---|---|---|
| `bundled` | 随 Meta-Harness 发布的默认组件 | 10 | 默认 9 core components 实现 |
| `template` | 官方/团队提供的半成品模板 | 20 | slot 填充式组件生成 |
| `market` | 市场分发的第三方组件 | 30 | 研究组件、替代实现 |
| `custom` | 本地路径或 workspace 组件 | 40 | 实验与私有组件 |

### 7.1 发现协议

```text
ComponentDiscovery.discover_all()
  ├── scan_bundled()
  ├── scan_templates()
  ├── scan_market_cache()
  └── scan_custom_paths()
```

### 7.2 冲突策略

- 相同 `component id` 只保留最高优先级候选
- 相同 `slot` 可保留多个实现，但只能激活一个 `primary binding`
- `protected` 默认实现不能被同优先级以下来源直接覆盖

## 8. `ComponentLoader`：从候选到实例

`ComponentLoader` 对应 Aeloon 的 `PluginLoader`，但比后者多一层"挂接到 candidate graph"。

### 8.1 职责拆分

| 阶段 | 说明 |
|---|---|
| `validate_candidate()` | 检查 manifest 完整性、版本兼容性、contracts 基本合法性 |
| `resolve_dependencies()` | 基于 capability 和 slot 要求解析依赖 |
| `import_component_class()` | 导入实现类 |
| `instantiate()` | 实例化组件 |
| `register_pending()` | 写入 pending mutations |
| `assemble_candidate_graph()` | 在 candidate graph 中完成绑定 |

### 8.2 推荐接口

```python
class ComponentLoader:
    def validate_candidate(self, manifest: dict[str, object]) -> list[str]: ...
    def resolve_dependencies(self, manifests: list[dict[str, object]]) -> list[str]: ...
    def import_component_class(self, entry: str) -> type[HarnessComponent]: ...
    def instantiate(self, cls: type[HarnessComponent]) -> HarnessComponent: ...
    def register_pending(self, component: HarnessComponent, api: HarnessAPI) -> None: ...
    def assemble_candidate_graph(self, candidate_graph_id: str) -> None: ...
```

### 8.3 manifest 验证示例

```python
class ComponentLoader:
    def validate_manifest(self, candidate: ComponentCandidate) -> list[str]:
        errors: list[str] = []
        manifest = candidate.manifest

        if not _ID_PATTERN.match(manifest.id):
            errors.append(f"Invalid component id: {manifest.id}")
        if not _ENTRY_PATTERN.match(manifest.entry):
            errors.append(f"Invalid entry format: {manifest.entry}")
        if not manifest.interface.inputs and not manifest.interface.outputs:
            errors.append("Component must declare at least one input or output")
        for inp in manifest.interface.inputs:
            if not _TYPE_PATTERN.match(inp.type):
                errors.append(f"Invalid input type: {inp.type}")
        for out in manifest.interface.outputs:
            if not _TYPE_PATTERN.match(out.type):
                errors.append(f"Invalid output type: {out.type}")
        if manifest.requires.metaharness_version:
            if not validate_version(manifest.requires.metaharness_version):
                errors.append(f"SDK version mismatch: {manifest.requires.metaharness_version}")
        missing_bins = validate_bins(manifest.requires.bins)
        if missing_bins:
            errors.append(f"Missing binaries: {', '.join(missing_bins)}")
        missing_env = validate_env(manifest.requires.env)
        if missing_env:
            errors.append(f"Missing env vars: {', '.join(missing_env)}")
        if manifest.safety.protected and manifest.component_type != "core":
            errors.append("Only core components can be marked as protected")
        return errors
```

### 8.4 依赖解析与拓扑排序

```python
    def resolve_load_order(self, candidates: list[ComponentCandidate]) -> list[ComponentCandidate]:
        by_id: dict[str, ComponentCandidate] = {c.manifest.id: c for c in candidates}
        in_degree: dict[str, int] = {pid: 0 for pid in by_id}
        dependents: dict[str, list[str]] = {pid: [] for pid in by_id}

        skipped: set[str] = set()
        for pid, candidate in by_id.items():
            for dep in candidate.manifest.requires.components:
                if dep not in by_id:
                    logger.error("Component '{}' requires '{}' which is not available; skipping", pid, dep)
                    skipped.add(pid)
                    break
                in_degree[pid] += 1
                dependents[dep].append(pid)

        changed = True
        while changed:
            changed = False
            for pid in list(by_id):
                if pid in skipped:
                    continue
                for dep in by_id[pid].manifest.requires.components:
                    if dep in skipped:
                        skipped.add(pid)
                        changed = True
                        break

        for sid in skipped:
            in_degree.pop(sid, None)
            dependents.pop(sid, None)

        queue = [pid for pid, deg in in_degree.items() if deg == 0]
        sorted_ids: list[str] = []
        while queue:
            pid = queue.pop(0)
            sorted_ids.append(pid)
            for dep_id in dependents.get(pid, []):
                if dep_id in in_degree:
                    in_degree[dep_id] -= 1
                    if in_degree[dep_id] == 0:
                        queue.append(dep_id)

        remaining = [pid for pid in in_degree if pid not in sorted_ids]
        if remaining:
            raise CircularDependencyError(remaining)
        return [by_id[pid] for pid in sorted_ids]
```

### 8.5 类导入与实例化

```python
    def load_component_class(self, manifest: ComponentManifest) -> type[HarnessComponent]:
        module_path, class_name = manifest.entry.rsplit(":", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        if not (isinstance(cls, type) and issubclass(cls, HarnessComponent)):
            raise ComponentLoadError(f"{manifest.entry} is not a HarnessComponent subclass")
        return cls

    def instantiate(self, cls: type[HarnessComponent]) -> HarnessComponent:
        return cls()
```

## 9. staged lifecycle：从发现到 graph cutover

Meta-Harness 建议使用比 Aeloon 更长的 staged lifecycle。Aeloon 是 `discover → validate → resolve → register → commit → activate`；Meta-Harness 需要扩展到图级别。

### 9.1 生命周期阶段表

| 阶段 | 输入 | 输出 |
|---|---|---|
| Discover | discovery sources | candidate manifests |
| Validate Static | manifests | valid candidates |
| Assemble Candidate Graph | pending mutations | candidate graph |
| Validate Dynamic | candidate graph | approved / rejected |
| Activate Candidate | candidate graph | warm component set |
| Commit Graph | approved candidate graph | new active graph version |
| Observe / Rollback | active graph version | stable / rollback |

> **注**：在 `Validate Static` 与 `Assemble Candidate Graph` 之间，组件实现会进行 registration（将声明写入 pending mutations）。这是必需的实现步骤，但已被吸收进 staged lifecycle 的衔接逻辑中，不作为独立的规范阶段。

### 9.2 文本时序图

```text
ComponentManager.boot_or_swap()
  -> discover candidates
  -> validate manifests/contracts
  -> instantiate components
  -> component.declare_interface(api)
  -> write declarations to pending mutations
  -> assemble candidate graph
  -> run policy + shadow + sandbox validation
  -> activate candidate components
  -> switch active graph version
  -> observe health window
  -> rollback if degradation detected
```

### 9.3 生命周期与 graph versions 的关系

| 对象 | 作用 |
|---|---|
| `pending mutations` | 描述本轮候选变更 |
| `candidate graph` | 尚未生效的图版本 |
| `active graph version` | 当前生产流量使用的图 |
| `rollback target` | 上一个稳定 graph version |

### 9.4 生命周期状态图

```text
                     +------------------+
                     |  discovered      |
                     +---------+--------+
                               |
                               v
                     +------------------+
                     | static validated |
                     +---------+--------+
                               |
                               v
                     +------------------+
                     | candidate graph  |
                     +---------+--------+
                               |
                +--------------+---------------+
                |                              |
                v                              v
      +--------------------+         +--------------------+
      | dynamic approved   |         | dynamic rejected   |
      +---------+----------+         +---------+----------+
                |                              |
                v                              v
      +--------------------+         +--------------------+
      | candidate active   |         | rollback pending   |
      +---------+----------+         +--------------------+
                |
                v
      +--------------------+
      | graph committed    |
      +---------+----------+
                |
                v
      +--------------------+
      | observed stable    |
      +--------------------+
```

### 9.5 失败处理

```text
Validate Static 失败    -> 反馈错误信息，跳过此组件
Pending mutations 失败   -> 回滚 pending 记录，清理状态
Validate Dynamic 失败    -> 反馈给 Optimizer 作为负向奖励信号
Activate 失败           -> 自动回滚到上一 active graph version
Observe 检测到退化       -> 自动回滚 + 通知 Optimizer
```

## 10. contracts：组件装配的真正耦合面

Meta-Harness 组件之间不应该通过类名或内部对象互相耦合，而应该通过 contracts 连接。

### 10.1 contract 组成

| 维度 | 示例 |
|---|---|
| 输入 contract | `TaskRequest@v1` |
| 输出 contract | `ExecutionResult@v1` |
| 事件 contract | `PolicyViolation@v1` |
| 失败语义 | timeout / retriable / fatal |
| 状态 schema | `planner_state@v2` |
| 迁移要求 | `v1 -> v2` adapter |

### 10.2 compatibility checks

建议至少实现 5 条静态规则：

1. output contract 与 target input contract 必须兼容
2. required input 必须能在图中被满足
3. component id 必须全局唯一
4. protected slot 不能被未授权实现覆盖
5. candidate graph 不允许出现非法环路或未声明事件引用

## 11. Aeloon vs Meta-Harness：相同骨架，不同目标

| 维度 | Aeloon Plugin SDK | Meta-Harness Component SDK |
|---|---|---|
| 扩展单位 | Plugin | Component |
| 注册粒度 | command/tool/service/hook | input/output/event/slot/capability |
| 通信方式 | 通过宿主 AgentLoop 间接交互 | 通过 ConnectionEngine 和 contracts 直连 |
| 提交对象 | PluginRegistry | ComponentRegistry + candidate graph |
| 生命周期 | discover → commit → activate | discover → validate → assemble → validate → commit graph |
| 回滚粒度 | 插件级失败恢复 | graph version 级回滚 |
| 安全重点 | Hook guard、配置隔离 | protected components、dynamic validation、evidence chain |
| 热替换 | 非一等能力 | staged lifecycle 的核心能力 |

### 11.1 最值得直接复用的模式

- `declare_interface()` 与 `activate()` 分离
- API 先写 pending 再 `_commit()`
- discovery / loader / manager 三段式职责分离
- runtime 注入边界收敛

### 11.2 必须新增的 Meta-Harness 特性

- slot/capability system
- contracts + graph assembly
- pending mutations
- graph versions
- protected components
- staged lifecycle 下的动态验证与回滚

## 12. 一个最小可实现骨架

```text
metaharness/
├── sdk/
│   ├── base.py           # HarnessComponent
│   ├── api.py            # HarnessAPI
│   ├── runtime.py        # ComponentRuntime
│   ├── manifest.py       # ComponentManifest schema
│   ├── discovery.py      # discovery sources
│   ├── loader.py         # validate/import/instantiate/assemble
│   └── registry.py       # components + slots + graph versions
├── core/
│   ├── runtime.py        # HarnessRuntime
│   ├── connection.py     # ConnectionEngine
│   └── graph_versions.py # active/candidate/rollback
└── governance/
    ├── contracts.py
    ├── policy.py
    ├── shadow.py
    └── rollback.py
```

## 13. 落地建议

按实现优先级，建议这样推进：

1. 先冻结 `HarnessComponent` / `HarnessAPI` / `ComponentRuntime` / manifest schema
2. 再实现 `ComponentRegistry` 与 `ComponentLoader`
3. 然后实现最小 `candidate graph + graph versions`
4. 最后再接 `Optimizer`，让它只操作 mutation proposals，而不是直接改组件对象

这样可以确保 Meta-Harness 从一开始就是"组件图系统"，而不是后期再从普通插件系统硬改过来。

## 14. 设计约束

在 SDK 实现和扩展中，必须遵守以下约束：

### 14.1 组件内聚约束

单个组件必须保持清晰职责边界。禁止将 identity 校验、governance 策略、runtime 调度、tool execution 混成单体组件实现。每个 `HarnessComponent` 子类应只聚焦一个核心职责域。

### 14.2 可解释性预算

SDK 的接口设计应控制概念复杂度。`HarnessComponent` 的基类方法不超过 7 个核心方法；`HarnessAPI` 的注册方法按功能分组（端口/能力/slot/hooks/服务），避免接口膨胀。

### 14.3 连接健康与孤儿组件检查

`ComponentLoader` 在 `assemble_candidate_graph()` 阶段必须检测：声明了 ports 但未被任何 Connection 引用的组件（孤儿组件）。这些组件不应静默进入 candidate graph，而应生成警告或阻止提交。

### 14.4 Token / 资源预算底线

`ComponentRuntime` 的 `sandbox_client` 和 `llm` 代理必须内置资源预算追踪。任何工具调用或 LLM 请求都应累计到当前执行上下文的 token/resource 预算中，当接近硬 ceiling 时提前拒绝，而不是等到溢出后报错。

### 14.5 Graph-version retirement

`ComponentRegistry` 应实现版本自动清理策略：
- 保留最近 N 个 graph versions（默认 50）作为快速回滚目标
- 超出保留窗口的版本归档到冷存储，仅保留 Merkle 摘要
- 被标记为 `failed` 或 `rolled_back` 的版本在观察期（如 7 天）后进入归档队列
- Optimizer 不应读取已归档版本的完整 graph snapshot，只能读取其性能摘要

## 15. MHE 当前 Plugin SDK 设计映射

上一节给出的是 Meta-Harness 组件 SDK 的目标形态；而 `./MHE` 中已经落地的实现，可以看作这一设计的第一版工程化收敛。它并不是一个面向任意宿主的通用插件框架，而是一个围绕 **manifest discovery、声明式 contracts、受控 runtime 注入、graph staged commit、hot reload** 组织起来的组件式 SDK。

### 15.1 SDK 的公开骨架

当前 MHE 的公开骨架主要由四个对象组成：

| 对象 | 当前职责 | 代码位置 |
|---|---|---|
| `HarnessComponent` | 定义 staged lifecycle：声明（抽象）、激活（抽象）、停机（抽象）、状态导入导出、挂起与恢复（均有安全默认实现） | `MHE/src/metaharness/sdk/base.py` |
| `HarnessAPI` | 收集 ports / events / capabilities / slots / hooks / services / validators / migration adapters 的声明 | `MHE/src/metaharness/sdk/api.py` |
| `ComponentRuntime` | 向组件注入受控能力边界，而不是直接暴露宿主内部对象 | `MHE/src/metaharness/sdk/runtime.py` |
| `ComponentManifest` | 声明组件身份、entry、contracts、安全属性、依赖声明与能力需求（当前为标识符列表，无版本约束） | `MHE/src/metaharness/sdk/manifest.py` |

其中最关键的设计原则仍然是：**组件先声明接口，再进入运行态**。`HarnessComponent.declare_interface()` 明确要求无 I/O；真正的资源获取发生在 `activate()`；热替换相关能力则通过 `suspend()` / `resume()` / `export_state()` / `import_state()` / `transform_state()` 暴露出来。这说明 MHE 已经把"组件是可替换运行单元"而不是"静态注册项"作为 SDK 的核心假设。

### 15.2 声明式注册，而不是直接改宿主

MHE 当前的 `HarnessAPI` 已经体现出较完整的声明式 DSL：

- 端口：`declare_input()` / `declare_output()` / `declare_event()`
- 能力：`provide_capability()` / `require_capability()`
- slot：`bind_slot()` / `reserve_slot()`
- 扩展点：`register_hook()` / `register_service()` / `register_validator()`
- 连接处理句柄注册：`register_connection_handler()`
- 热替换迁移：`register_migration_adapter()`

这些声明先进入 `PendingDeclarations`，`_commit()` 将其冻结并返回不可变快照；该快照随后由 boot 编排器通过 `registry.register()` 或 `registry.stage()` 写入注册表。这意味着 MHE 的注册模型已经不是"组件在初始化时随手向全局单例塞回调"，而是**先形成一份原子声明快照，再由 boot/runtime 编排器统一接管**。

### 15.3 Boot 路径体现了 staged lifecycle

从 `HarnessRuntime.boot()` 可以看到，MHE 当前的启动流程是一个简化的 staged pipeline（注意：它尚未实现本章前文提出的完整 staged lifecycle，例如 candidate graph 组装、动态校验与 graph commit 等步骤）：

```text
discovery.resolve()
  -> filter_enabled()
  -> validate_manifest_static()
  -> resolve_boot_order()
  -> declare_component()
  -> api._commit()
  -> registry.register()
  -> migration_adapters.register_declarations()
  -> component.activate(runtime)
  -> lifecycle.record(DISCOVERED / VALIDATED_STATIC / ASSEMBLED)
```

这里有几个值得注意的实现点：

1. **发现是多源的**：`ComponentDiscovery` 支持 `bundled`、`templates`、`market`、`custom` 四类来源，并按优先级覆盖。
2. **静态校验先于激活**：`validate_manifest_static()` 会检查 `harness_version`、依赖的二进制以及环境变量。
3. **依赖顺序由 capability + component deps 共同决定**：`resolve_boot_order()` 同时考虑显式组件依赖和 capability 提供者。
4. **声明先 commit，再写入 registry，最后 activate**：组件实例先完成 `declare_interface()` 与 `_commit()`，冻结后的快照由 `registry.register()` 写入注册表，随后才调用 `component.activate(runtime)` 进入运行态。
5. **生命周期记录是当前实现的一个占位**：`DISCOVERED`、`VALIDATED_STATIC`、`ASSEMBLED` 三个阶段是在 `activate()` **之后** 被连续写入的，这与 Section 3.4 和 Section 9 的语义定义不一致。这说明 `LifecycleTracker` 在当前 boot 流程中主要用于 bookkeeping，真正的 staged lifecycle 语义尚待后续实现对齐。

因此，MHE 的真实实现已经工程上兑现了"先声明、再注册、后激活"的关键原则，但完整的 staged lifecycle（含 candidate graph 组装、动态校验、graph commit）仍然是目标架构，尚未在 `boot()` 中启用。

### 15.4 Runtime 边界是受控注入，不暴露宿主全貌

`ComponentRuntime` 当前暴露的是一组明确收敛的能力面，而不是整个 `HarnessRuntime`：

- 基础能力：`logger`、`config`、`storage_path`
- 观测能力：`metrics`、`trace_store`
- 编排能力：`event_bus`、`graph_reader`、`mutation_submitter`
- 执行能力：`llm`、`sandbox_client`、`process_direct`、`tool_execute`（后两者为可调用字段，由运行时工厂注入）
- 基础设施引用：`identity_boundary`（身份边界）、`migration_adapters`（迁移适配器注册表，热替换时使用）

这种设计和 Aeloon `PluginRuntime` 的精神一致：给插件/组件"足够做事的能力"，但不把宿主的内部状态与生命周期控制权整体泄露出去。对 Meta-Harness 而言，这一点尤其重要，因为组件不仅要运行，还要参与 graph 变更、tool 调用和身份边界管理。

### 15.5 Registry 与 graph 语义已经出现分层

当前 `ComponentRegistry` 负责维护：

- `components`：已注册组件
- `slot_bindings`：slot 到组件的绑定索引
- `capability_index`：capability 到组件的提供者索引
- `pending`：待提交注册区
- `candidate_graph` / `active_graph` / `graph_versions`：图版本引用（实际图版本管理由 `GraphVersionManager` 与 `ConnectionEngine` 负责）
- `pending_mutations`：待提交变更提案

这说明 MHE 现在的注册中心已经不只是一个"组件字典"，而是开始承担 **声明存档 + 装配索引** 的核心职责，同时预留了 graph version 状态管理的字段接口。尤其值得注意的是，`stage()` / `commit_pending()` / `abort_pending()` 已经把"先放入 pending zone，再原子发布"这一机制显式建模出来，为后续的 candidate graph / protected components / reviewer gate 留出了接口位置。

> **说明**：`ComponentLoader` 作为本章 Section 8 中描述的一个类，在当前代码中尚未以类的形态出现。加载与装配逻辑目前分散在 `loader.py` 的模块级函数（`load_manifest`、`instantiate_component`、`declare_component`）以及 `HarnessRuntime.boot()` 的内联逻辑中。

### 15.6 Hot reload 已经是 SDK 的一等能力

MHE 当前的热替换不是简单的"卸载旧组件、加载新组件"，而是围绕 `HotSwapOrchestrator` 实现了一个完整的 saga：

```text
suspend outgoing
  -> capture checkpoint
  -> deactivate outgoing
  -> migrate state
  -> resume incoming
  -> observe window
  -> rollback on failure
```

这条路径依赖三个关键机制：

- `HarnessComponent` 基类提供 `suspend()` / `resume()` / `transform_state()` 等可覆写 hook
- `MigrationAdapterRegistry` 支持显式声明的 state migration adapter；若未命中适配器，则回退到 `HarnessComponent.transform_state()`
- `ObservationWindowEvaluator` 为 swap 后的稳定性判断提供统一观察窗口（可选步骤；若未配置 evaluator，则跳过该步骤并默认视为通过）

因此，在 MHE 里，hot reload 并不是外层脚本层面的附加功能，而是 SDK 生命周期的一部分。组件若想成为可替换的一等公民，就必须在接口层面承诺自己的状态迁移与恢复语义。

### 15.7 MHE 当前实现与目标架构的关系

把本章前文的目标设计与 `./MHE` 当前实现对照起来，可以得到一个比较清晰的判断：

| 目标能力 | 当前 MHE 状态 | 说明 |
|---|---|---|
| 多源发现 | 已实现 | `bundled/templates/market/custom` 已进入 discovery 模型 |
| manifest 驱动装配 | 已实现 | manifest + declaration snapshot 是权威输入 |
| capability / slot 约束 | 已实现基础索引 | registry 与 dependency resolver 已消费这些声明 |
| staged registration | 已实现 | `_commit()` + pending zone 已存在 |
| graph staged commit | 接口已就绪，但未在 boot 流程中启用 | `commit_graph()` 已存在，但 `boot()` 返回后需由调用方显式调用 |
| hot reload / state migration | 已实现核心路径 | saga、checkpoint、adapter registry 已到位 |
| protected components / governance gate | 仅出现字段与查询接口，尚未接入治理策略执行 | `safety.protected` 与 `registry.is_protected()` 已存在，但无策略执行逻辑 |

换句话说，MHE 现在的 Plugin SDK 已经不是一个抽象草图，而是一套**以组件声明为中心、以 runtime 边界为安全面、以 graph 与 hot reload 为演进面**的可运行实现。对后续 wiki 章节（如连接引擎、治理、热重载）而言，这一节提供了一个关键阅读视角：后面的系统并不是附着在 SDK 外侧，而是围绕这套 SDK 的声明、索引、提交与切换机制层层展开的。
