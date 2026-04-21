# 04. 连接引擎与配置

本章把 Meta-Harness 的"组件可组合"落到一个可实现的连接层：用 XML 声明组件图，用 XSD 固定结构边界，用 `ConnectionEngine` 负责静态校验、候选图装配、运行时路由与原子切换。这里的目标不是做一个通用工作流引擎，而是做一个**契约优先、可热切换、可裁剪搜索空间**的组件连接内核。

## 4.1 设计目标

连接层需要同时满足五个工程目标：

| 目标 | 含义 | 对实现的约束 |
| --- | --- | --- |
| 契约清晰 | 组件只通过声明过的输入/输出/Event 连接 | XML 与 manifest 必须同源校验 |
| 路由稳定 | 运行态消息只能沿合法边传播 | `ConnectionEngine` 只接收已提交图版本 |
| 可裁剪 | 优化器不能在非法连接上浪费搜索预算 | 连接候选生成前做 contract-driven pruning |
| 可切换 | 新图可以在运行中替换旧图 | 使用 PendingConnection + graph versioning |
| 可回滚 | 切换失败后能回到上一个稳定图 | 每次提交必须生成可恢复快照 |

## 4.2 XML 配置模型

Meta-Harness 使用 XML 表达"组件声明 + 连接关系 + 运行策略"。建议把接口契约保留在组件 manifest 中，把**装配结果**保留在 XML 中。也就是说：

- manifest 负责声明组件能提供什么；
- XML 负责声明当前系统如何把这些组件接起来；
- `ConnectionEngine` 负责验证"这次接法是否合法且可运行"。

### 4.2.1 核心 XML 标签

| 标签 | 层级 | 作用 | 关键属性 |
| --- | --- | --- | --- |
| `<Harness>` | 根节点 | 定义整张组件图 | `version`, `graphVersion`, `schemaVersion` |
| `<Components>` | 一级 | 声明参与本图的组件实例 | 无 |
| `<Component>` | 二级 | 单个组件实例 | `id`, `type`, `impl`, `version`, `protected` |
| `<Config>` | 三级 | 组件实例配置 | 无，内部为参数子节点 |
| `<Interfaces>` | 二级，可选缓存 | 记录编译后的端口视图 | 无 |
| `<Input>` | 三级 | 输入端口声明 | `name`, `type`, `required`, `cardinality` |
| `<Output>` | 三级 | 输出端口声明 | `name`, `type`, `mode` |
| `<Event>` | 三级 | 事件声明 | `name`, `payloadType` |
| `<Connections>` | 一级 | 连接关系集合 | 无 |
| `<Connection>` | 二级 | 一条静态边 | `id`, `from`, `to`, `payload`, `mode`, `policy` |
| `<Route>` | 三级，可选 | 路由细节 | `when`, `priority`, `fallback` |
| `<OptimizerHints>` | 一级，可选 | 给优化器的裁剪提示 | 无 |
| `<AllowedRewire>` | 二级 | 指定可重接线区域 | `scope`, `maxFanOut` |

### 4.2.2 推荐属性语义

| 属性 | 示例 | 说明 |
| --- | --- | --- |
| `id` | `memory.primary` | 组件或连接的稳定标识符 |
| `type` | `Memory` | 槽位层面的组件类型 |
| `impl` | `metaharness.memory.jsonl` | 具体实现 ID |
| `from` | `planner.primary.plan` | `组件ID.输出端口` |
| `to` | `runtime.core.task` | `组件ID.输入端口` |
| `payload` | `PlanPackage` | 边上传输的数据契约名 |
| `mode` | `sync` / `async` / `event` | 路由模式 |
| `policy` | `required` / `optional` / `shadow` | 切换与失败处理语义 |
| `graphVersion` | `42` | 已提交活动图版本 |
| `schemaVersion` | `1.1` | XML 结构 schema 版本 |

### 4.2.3 最小 3 组件 XML 示例

下面的最小示例体现了"Planner -> Runtime -> Evaluator"的三组件闭环，也是连接引擎的最小可运行单元。

```xml
<Harness version="0.1.0" graphVersion="7" schemaVersion="1.1">
  <Components>
    <Component id="planner.primary" type="Planner" impl="metaharness.planner.react" version="1.0.0">
      <Config>
        <Temperature>0.2</Temperature>
      </Config>
    </Component>

    <Component id="runtime.core" type="Runtime" impl="metaharness.runtime.default" version="1.0.0" protected="true">
      <Config>
        <MaxConcurrentTasks>8</MaxConcurrentTasks>
      </Config>
    </Component>

    <Component id="evaluator.primary" type="Evaluator" impl="metaharness.evaluator.vector" version="1.0.0">
      <Config>
        <WindowSize>16</WindowSize>
      </Config>
    </Component>
  </Components>

  <Connections>
    <Connection
      id="c1"
      from="planner.primary.plan"
      to="runtime.core.task"
      payload="PlanPackage"
      mode="sync"
      policy="required" />

    <Connection
      id="c2"
      from="runtime.core.result"
      to="evaluator.primary.task_result"
      payload="TaskResult"
      mode="async"
      policy="required" />

    <Connection
      id="c3"
      from="evaluator.primary.loop_guard_signal"
      to="runtime.core.guard_signal"
      payload="LoopGuardSignal"
      mode="event"
      policy="optional" />
  </Connections>
</Harness>
```

### 4.2.4 文本拓扑图

```text
planner.primary(plan: PlanPackage)
          |
          v
runtime.core(task -> result)
          |
          v
evaluator.primary(task_result -> performance_vector)
          |
          +---- event: loop_guard_signal ----> runtime.core
```

## 4.3 XSD 方案：先约束结构，再校验契约

XSD 不是为了表达全部语义，而是为了把最容易出错的结构问题尽早拦在编译前。建议采用"两段校验"：

1. **XSD 校验**：结构、字段存在性、基础类型、枚举范围；
2. **Contract 校验**：端口类型、required 输入完备性、版本兼容性、治理规则。

### 4.3.1 XSD 负责什么

| XSD 负责 | 示例 |
| --- | --- |
| 根节点结构合法 | 必须存在 `<Harness>` |
| 属性类型合法 | `graphVersion` 必须是正整数 |
| 标签嵌套合法 | `<Connection>` 只能出现在 `<Connections>` 下 |
| 枚举值合法 | `mode` 只能为 `sync|async|event` |
| 基础唯一性 | `Component/@id`、`Connection/@id` 唯一 |

### 4.3.2 XSD 不负责什么

| 不建议放入 XSD 的语义 | 原因 |
| --- | --- |
| `payload` 是否与端口真实类型匹配 | 需要读组件 manifest |
| 某个 `required` 输入是否已被满足 | 需要全图分析 |
| protected 组件是否允许被替换 | 需要治理层决策 |
| 候选图能否热切换 | 需要动态验证 |

### 4.3.3 XSD 片段示例

```xml
<xs:element name="Connection">
  <xs:complexType>
    <xs:attribute name="id" type="xs:string" use="required"/>
    <xs:attribute name="from" type="xs:string" use="required"/>
    <xs:attribute name="to" type="xs:string" use="required"/>
    <xs:attribute name="payload" type="xs:string" use="required"/>
    <xs:attribute name="mode" use="required">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="sync"/>
          <xs:enumeration value="async"/>
          <xs:enumeration value="event"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="policy" default="required">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="required"/>
          <xs:enumeration value="optional"/>
          <xs:enumeration value="shadow"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
  </xs:complexType>
</xs:element>
```

实现上建议把 XSD 校验放在 `ConfigParser.parse()` 阶段完成，再把解析结果交给 `CompatibilityValidator` 做深层语义检查。

## 4.4 ConnectionEngine：从候选图到运行态路由

`ConnectionEngine` 是连接层的执行核心。它不负责发现组件，也不负责生成候选方案；它只做四件事：

1. 读取已验证的 graph snapshot；
2. 构建端口索引与路由表；
3. 在运行时根据 `from -> to` 关系分发数据；
4. 在 graph version 切换时原子替换整张路由表。

### 4.4.1 核心职责分解

| 模块 | 当前实现对齐 |
| --- | --- |
| `PortIndex` | 已实现，用于从 registry 构建端口索引 |
| `RouteTable` | 已实现，可从活动 snapshot 构建路由表视图 |
| `ConnectionEngine` | 已实现 stage / commit / discard / rollback / emit / emit_async |
| `PendingConnectionSet` | 已实现，作为候选 nodes/edges 的 staged 容器 |
| `GraphVersionStore` | 已实现，保存 candidate / active / rollback / archived snapshot |
| `CompatibilityValidator` | **未以该类名存在**；当前实际为 `core/validators.py` 中的 `validate_graph()` |

### 4.4.2 路由流程

```text
XML + manifests
  -> XSD parse
  -> contract validation
  -> candidate graph assembly
  -> PendingConnectionSet
  -> atomic commit(graphVersion = n + 1)
  -> ConnectionEngine swaps active RouteTable
  -> runtime emit/send/event routing
```

### 4.4.3 路由接口草图

```python
class ConnectionEngine:
    def __init__(self, registry, version_store):
        self._registry = registry
        self._version_store = version_store
        self._active_graph_version = 0
        self._route_table = {}
        self._port_index = {}

    def load_graph(self, graph_snapshot: "GraphSnapshot") -> None:
        self._port_index = self._build_port_index(graph_snapshot)
        self._route_table = self._build_route_table(graph_snapshot)
        self._active_graph_version = graph_snapshot.graph_version

    async def emit(self, source_port: str, payload: object) -> None:
        for binding in self._route_table.get(source_port, []):
            await self._dispatch(binding, payload)

    def stage(self, delta: "PendingConnectionSet") -> "ValidationReport":
        candidate = self._overlay(delta)
        return self._validate(candidate)

    def commit(self, delta: "PendingConnectionSet") -> int:
        candidate = self._overlay(delta)
        version = self._version_store.next_version()
        self._version_store.save(version, candidate)
        self.load_graph(candidate)
        return version
```

### 4.4.4 路由模式建议

| 模式 | 适用场景 | 引擎行为 |
| --- | --- | --- |
| `sync` | 主执行链上的刚性依赖 | 下游失败直接上抛 |
| `async` | 评估、日志、异步记忆写入 | 放入队列并异步消费 |
| `event` | 观测、治理、告警 | 广播到所有订阅端 |
| `shadow` | 候选组件旁路验证 | 主链不依赖结果 |

## 4.5 当前兼容规则（实现视角）

当前实现并不只检查“五条规则”，而是对候选图执行一组更细的语义校验。文档若继续写成固定“五条规则”，会低估当前验证器能力。

| 当前校验项 | 内容 | 失败后果 |
| --- | --- | --- |
| duplicate connection | 连接 ID 不允许重复 | 候选图无效 |
| unknown component / port | 边的源/目标组件与端口必须已注册且已声明 | 候选图无效 |
| payload mismatch | 边上传输的 payload 必须匹配目标输入类型 | 候选图无效 |
| required inputs complete | 所有 required 输入必须被满足 | 候选图无效 |
| protected slot override | protected primary slot 不允许多重绑定 | 候选图无效 |
| cycle detection | 不允许形成环 | 候选图无效 |
| orphan detection | 多节点图中，未被任何连接引用的组件会报错/阻止提交（无输入端口组件除外） | 候选图无效 |

### 4.5.1 规则检查伪代码

```python
class CompatibilityValidator:
    def validate(self, graph: "GraphSnapshot") -> list[str]:
        errors: list[str] = []
        errors += self.check_type_matching(graph)
        errors += self.check_event_declaration(graph)
        errors += self.check_required_inputs(graph)
        errors += self.check_identifier_uniqueness(graph)
        errors += self.check_graph_consistency(graph)
        return errors
```

## 4.6 契约驱动剪枝：让优化器少走弯路

Meta-Harness 里的连接空间增长很快。如果有 `N` 个输出端与 `M` 个输入端，朴素重接线空间接近 `N x M`。而真正合法的连接通常只占其中一小部分。解决方法不是"先连再报错"，而是**在生成动作前先剪枝**。

### 4.6.1 剪枝输入

连接候选生成器应至少读取以下约束：

| 约束来源 | 用途 |
| --- | --- |
| manifest 接口契约 | 过滤类型不兼容的端口组合 |
| slot 约束 | 限制哪些类型的组件可以互连 |
| governance 规则 | 排除 protected 组件的非法重绑定 |
| topology hint | 限制最大 fan-out、最大路径长度 |
| historical failure cache | 避免重复尝试已知非法连接 |

### 4.6.2 剪枝流程图

```text
all possible port pairs
  -> remove type-incompatible pairs
  -> remove undeclared event pairs
  -> remove protected/prohibited rewires
  -> remove topology-violating pairs
  -> rank remaining legal candidates
```

### 4.6.3 剪枝接口草图

```python
class ContractDrivenPruner:
    def legal_targets(self, source_port: str, graph: "GraphSnapshot") -> list[str]:
        candidates = self._all_input_ports(graph)
        candidates = [p for p in candidates if self._type_compatible(source_port, p)]
        candidates = [p for p in candidates if self._event_compatible(source_port, p)]
        candidates = [p for p in candidates if not self._violates_policy(source_port, p)]
        candidates = [p for p in candidates if not self._violates_topology(source_port, p)]
        return candidates
```

这一步的意义不是优化运行速度，而是优化**搜索样本效率**：优化器只对"合法且有意义"的连接做尝试。

## 4.7 PendingConnection 原子提交

Aeloon Plugin SDK 的 staged commit 思路在这里非常关键。Meta-Harness 不应让连接边被逐条写进活动图；否则任意一步失败都可能让系统处于半更新状态。推荐使用 `PendingConnectionSet -> validate -> atomic commit` 三段流程。

### 4.7.1 原子提交流程

```text
optimizer proposes delta
  -> write delta into PendingConnectionSet
  -> run XSD + compatibility + policy validation
  -> assemble candidate graph snapshot
  -> reserve next graph version
  -> atomically swap active snapshot
  -> release old snapshot to rollback queue
```

### 4.7.2 为什么需要 PendingConnection

| 不使用 PendingConnection 的问题 | 原子提交后的改进 |
| --- | --- |
| 图可能处于"只改了一半"的状态 | 候选图全量通过后才切换 |
| 回滚点不清晰 | 每次提交都绑定唯一 graph version |
| 并发修改易冲突 | 通过 staged set 做冲突检测 |
| 路由表可能与配置不一致 | 路由表与图快照同版本切换 |

### 4.7.3 建议数据结构

```python
@dataclass
class PendingConnectionSet:
    base_graph_version: int
    add_edges: list["ConnectionDef"]
    remove_edges: list[str]
    rebind_edges: list["RebindOp"]
    created_at: str
    proposer_id: str
```

## 4.8 图版本化与回滚

一旦允许连接拓扑在运行中变化，`graphVersion` 就必须成为一等状态。建议所有配置、路由表、trace、评估结果都带上 graph version 标签。

### 4.8.1 版本化原则

| 原则 | 说明 |
| --- | --- |
| 单调递增 | 每次成功提交产生 `n+1` |
| 快照不可变 | 已提交版本只读，不原地修改 |
| 结果带版本 | trace / metric / reward 绑定版本号 |
| 回滚显式化 | rollback 本身也是一次版本切换 |
| 版本退役 | 超出保留窗口的版本归档，防止 version rot |

### 4.8.2 版本切换图

```text
v41 active
  -> stage candidate
  -> validate candidate(v42)
  -> cutover to v42
  -> observe
     -> healthy: keep v42
     -> degraded: rollback to v41 or commit v43 as rollback snapshot
```

### 4.8.3 推荐存储对象

| 对象 | 说明 |
| --- | --- |
| `GraphSnapshot` | 某一版本的组件图完整快照 |
| `RouteSnapshot` | 该图编译后的路由表 |
| `ValidationReport` | 该版本提交前的校验报告 |
| `RollbackRecord` | 回滚原因、触发器、恢复目标版本 |

### 4.8.4 GraphVersionManager 实现

```python
class GraphVersionManager:
    def __init__(self) -> None:
        self._versions: list[GraphVersion] = []
        self._current_version: int = -1

    async def commit_mutation(self, mutation: PendingMutation) -> GraphVersion:
        parent = self._versions[self._current_version] if self._current_version >= 0 else None
        new_version = GraphVersion(
            version=len(self._versions),
            parent=parent.version if parent else None,
            mutation=mutation,
            timestamp=datetime.now(),
            graph_snapshot=self._deep_copy_current_graph(),
        )
        try:
            self._apply_mutation(new_version.graph_snapshot, mutation)
            new_version.state = "committed"
            self._versions.append(new_version)
            self._current_version = new_version.version
            return new_version
        except Exception:
            new_version.state = "failed"
            raise

    async def rollback(self) -> GraphVersion:
        if self._current_version <= 0:
            raise ValueError("No previous version to rollback to")
        self._current_version -= 1
        previous = self._versions[self._current_version]
        previous.state = "active"
        return previous
```

## 4.9 运行态建议：连接引擎只看"已提交事实"

为了避免优化器、治理层、运行时互相污染，建议明确边界：

- 优化器只能生成 proposal，不直接改活动图；
- 治理层只能 veto / annotate / authorize，不直接做逐边写入；
- `ConnectionEngine` 只消费"已提交 graph snapshot"；
- Runtime 发消息时只认当前 `active_graph_version` 对应的 `RouteTable`。

这使得系统具备可审计性：任何一次奇怪的路由行为，都能回溯到某个确定版本的 XML 快照与验证报告。

## 4.10 设计约束

### 4.10.1 组件内聚约束

连接层不应将身份校验、沙箱策略、浏览器控制等跨领域逻辑嵌入 `<Connection>` 或 `<Component>` 标签。这些应通过 Policy 的 `policy.tool.guard` 和 `policy.action.guard` 统一处理，保持 XML 的纯粹性。

### 4.10.2 可解释性预算

XML 标签体系应保持稳定。新增标签需经过兼容性审查，避免为短期需求不断扩展 schema。`OptimizerHints` 和 `AllowedRewire` 是预留的扩展点，不应滥用。

### 4.10.3 连接健康与孤儿组件检查

`ConnectionEngine` 在加载 graph snapshot 后，应执行孤儿组件检测：扫描所有声明了 ports 的组件，确认每个组件至少被一个 Connection 引用（或标记为显式孤立）。孤儿组件应生成警告，阻止其进入 active graph。

### 4.10.4 Token / 资源预算底线

`<Connection>` 的 `Property` 可包含 `timeout_ms` 和 `max_retries`，但这些是单次转发的约束。系统级的 token/resource budget floor 应由 Runtime 或 Policy 维护，ConnectionEngine 在路由前检查预算状态，预算耗尽时拒绝新请求。

### 4.10.5 Graph-version retirement

`GraphVersionManager` 应实现自动退役策略：
- 保留最近 N 个 versions（默认 50）用于快速回滚
- 超出窗口的版本将 graph_snapshot 压缩归档，仅保留 `ValidationReport` 和 `RollbackRecord`
- `rollback target` 始终指向保留窗口内的最近稳定版本
- 归档版本保留 Merkle 根，用于长期审计

## 4.11 落地建议

按实施顺序，连接层最值得先做的是以下四件事：

| 优先级 | 建议 |
| --- | --- |
| P0 | 定义 XML 标签、属性与 XSD 基础骨架 |
| P0 | 实现 5 条兼容规则与 `CompatibilityValidator` |
| P1 | 实现 contract-driven pruning，缩小重接线搜索空间 |
| P1 | 实现 `PendingConnectionSet` 与 graph versioning |
| P2 | 让 `ConnectionEngine` 支持 `sync/async/event/shadow` 四种路由模式 |
| P2 | 接入 rollback watcher 与候选图观察窗口 |

一句话概括：**Meta-Harness 的连接层不是"配线表"，而是一个以 XML 为表面表示、以契约校验为编译器、以版本化路由表为运行内核的装配系统。**
