# 10. 开发与扩展指南

本章面向实现者，说明如何在不破坏 `contracts`、`slot/capability system`、`staged lifecycle` 与治理链的前提下扩展 Meta-Harness。重点不是泛泛介绍"可以扩展什么"，而是给出**面向组件图装配、模板实例化、搜索策略扩展、安全治理与调试验证**的具体做法。

为与前文保持一致，本文统一使用：

- **9 core components**：九个核心组件位点
- **Optimizer**：元层优化器
- **ConnectionEngine**：负责候选图装配、路由和图切换
- **Policy / Governance**：负责 veto、风险标注、审计与回滚协同
- **pending mutations**：待提交变更
- **graph versions**：候选图、活动图、回滚图版本体系
- **contracts**：输入/输出/Event 契约

## 10.1 扩展前的总原则

在 Meta-Harness 中，"能扩展"不等于"能直接改"。任何新组件、新模板、新搜索器或新治理规则，都应满足以下原则：

| 原则 | 含义 | 常见误区 |
| --- | --- | --- |
| 先定义接口，再写实现 | 先冻结 `contracts` 与 slot 绑定意图 | 先写类，最后再补 manifest |
| 先进入候选图，再进入活动图 | 一切改动都应走 `pending mutations` | 直接改 active graph |
| 优先小改动 | 先调参，再改拓扑，再换模板，再受限合成 | 一上来就自由生成 |
| 保持证据链 | 每次扩展都应能追溯到 graph version 和验证报告 | 只保留代码 diff，不保留上下文 |
| protected 组件单独对待 | `policy.primary`、关键 `evaluation.loop_guard` 等不能被普通流程直接覆盖 | 把所有组件都当作等价可替换 |

## 10.2 新组件快速开始

最常见的扩展方式，是新增一个可绑定到某个 slot 的组件实现。

### 10.2.1 最小开发流程

```text
1. choose target slot
2. define contracts and capabilities
3. write component manifest
4. implement HarnessComponent
5. register into candidate graph
6. validate and observe
```

### 10.2.2 第一步：选择目标位点

先确认新组件属于哪个稳定位点：

| 组件位点 | 典型扩展例子 |
| --- | --- |
| `planner.primary` | 新的任务分解器、规则路由器、ReAct 规划器 |
| `memory.primary` | 新的状态存储、检索器、快照后端 |
| `evaluation.primary` | 新的多目标评分器、loop guard |
| `toolhub.primary` | 新的工具包装器或执行代理 |
| `observability.primary` | 新的 trace exporter 或 evidence backend |

如果一个实现无法清晰归入既有 slot，就不应急着写组件，而应先讨论是否需要新增位点。

### 10.2.3 第二步：定义 contracts 与 capabilities

一个最小组件至少要回答：

- 它接收什么输入？
- 它输出什么结果？
- 它广播什么事件？
- 它提供什么 capability？
- 它依赖什么 capability？

示例：

```json
{
  "id": "metaharness.evaluation.safe_score",
  "kind": "evaluation",
  "slots": ["evaluation.primary"],
  "contracts": {
    "inputs": [
      {"name": "execution_result", "contract": "ExecutionResult@v1", "required": true}
    ],
    "outputs": [
      {"name": "performance_vector", "contract": "PerformanceVector@v1"}
    ],
    "events": [
      {"name": "on_degradation_detected", "payload": "DegradationReport@v1"}
    ]
  },
  "provides": {
    "capabilities": ["evaluation.score", "evaluation.compare"]
  },
  "requires": {
    "capabilities": ["observability.trace.read"]
  }
}
```

### 10.2.4 第三步：实现组件骨架

```python
class SafeEvaluationComponent(HarnessComponent):
    component_kind = "evaluation"

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("evaluation.primary")
        api.declare_input("execution_result", contract="ExecutionResult@v1")
        api.declare_output("performance_vector", contract="PerformanceVector@v1")
        api.declare_event("on_degradation_detected", payload_contract="DegradationReport@v1")
        api.provide_capability("evaluation.score")
        api.provide_capability("evaluation.compare")
        api.require_capability("observability.trace.read")

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        return None
```

### 10.2.5 第四步：进入候选图（关键）

**这是最容易出错的步骤。** 不要直接把新组件写进活动图，也不要直接调用 `registry.activate()`。正确流程：

```text
1. 生成 component manifest
2. 调用 declare_interface() 填充 pending 草案
3. 进入 candidate graph（静态校验 + 契约匹配）
4. 做动态校验（沙箱 + 影子测试）
5. 提交为新 graph version
```

#### 候选图提交流程示例

```python
async def stage_new_component(
    component_cls: type[HarnessComponent],
    manifest: ComponentManifest,
    registry: ComponentRegistry,
    engine: ConnectionEngine,
    version_manager: GraphVersionManager,
) -> GraphVersion:
    """将新组件安全地提交为候选图版本。

    注意：此函数不修改 active graph，只产生 pending mutations。
    """
    # 1. 注册到 pending 区（不激活）
    pending_id = registry.stage_component(
        component_cls=component_cls,
        manifest=manifest,
    )

    # 2. 静态校验
    static_errors = registry.validate_static(pending_id)
    if static_errors:
        raise StaticValidationError(static_errors)

    # 3. 装配候选图
    candidate = registry.assemble_candidate_graph()

    # 4. 运行 ConnectionEngine 的 5 条兼容规则
    compat_errors = engine.validator.validate(candidate)
    if compat_errors:
        raise CompatibilityError(compat_errors)

    # 5. 生成新的 graph version（仍未激活）
    new_version = version_manager.stage_candidate(candidate)

    # 6. 返回候选版本，等待动态验证和人工/自动审批
    return new_version
```

#### 常见错误

| 错误做法 | 后果 |
|---|---|
| 直接修改 active XML 并重启 | 绕过校验链，可能破坏运行图 |
| `registry.register()` 后立刻 `activate()` | 跳过候选图阶段，无回滚点 |
| 多个改动打包进一个候选图 | 失败时无法定位哪个改动导致退化 |
| 不记录失败候选 | 重复探索同一失败路径 |

#### 正确的激活方式

```python
# 错误：直接激活
# registry.activate(component_id)  # ❌ 永远不要这样做

# 正确：通过 version manager 提交
new_version = await stage_new_component(...)
# 经过 shadow validation + policy veto 后：
version_manager.commit_candidate(new_version.version)
# 进入观察窗口，若退化则自动回滚
```

## 10.3 替换一个核心组件

替换核心组件不是"删旧加新"，而是一次受状态迁移约束的图切换操作。

### 10.3.1 适用场景

| 场景 | 例子 |
| --- | --- |
| 升级实现 | `JsonlMemory` 替换为 `HybridMemory` |
| 切换策略 | `RulePlanner` 替换为 `HybridPlanner` |
| 强化治理 | `RulePolicy` 增强为 `ConstitutionalPolicy` |
| 收敛控制升级 | 旧 `loop_guard` 替换为多重收敛判据实现 |

### 10.3.2 标准替换流程

```text
1. export old component state
2. instantiate new implementation
3. run contract and dependency checks
4. transform state if needed
5. shadow validate new component
6. cut over graph version
7. observe and rollback if degraded
```

**Step 1: 获取原组件的接口契约**

```python
original = registry.get_component("Memory_1")
contract = original.get_interface_contract()
# contract 包含所有 Input/Output/Event 与必需参数
```

**Step 2: 实现新组件，匹配接口契约**

```python
class MyAdvancedMemory(HarnessComponent):
    def declare_interface(self, api: HarnessAPI) -> None:
        api.declare_input(Input(name="query", type=str, required=True))
        api.declare_input(Input(name="context", type=dict, required=True))
        api.declare_output(Output(name="response", type=str))
        api.declare_output(Output(name="metadata", type=dict))
        api.declare_event(Event(name="on_context_update"))
        # 新增端口（可选，不影响兼容性）
        api.declare_output(Output(name="embedding", type=list[float]))
```

**Step 3: 运行兼容性校验**

```python
compatibility = registry.check_compatibility(
    original_type="Memory",
    replacement_type="MyAdvancedMemory"
)
if not compatibility.is_compatible:
    raise IncompatibleReplacement(compatibility.errors)
```

**Step 4: 在沙箱中验证替换**

```python
validation_result = await sandbox.validate_replacement(
    component_id="Memory_1",
    new_component=MyAdvancedMemory,
    test_suite="regression"
)
```

**Step 5: 通过热加载执行替换**

```python
new_config = XMLConfig.from_component(
    component_id="Memory_1",
    new_type="MyAdvancedMemory",
    params={"cache_strategy": "lru", "max_cache_size": 1000}
)
await hot_reload_manager.request_reload(
    component_id="Memory_1",
    new_config=new_config,
    migration_adapter=MemoryToAdvancedMemoryAdapter()
)
```

### 10.3.3 什么时候必须写迁移逻辑

| 情况 | 是否需要迁移 |
| --- | --- |
| 组件无状态 | 通常不需要 |
| 仅改参数，不改状态 schema | 通常不需要 |
| 更换存储后端 | 需要 |
| 更改缓存键结构 | 需要 |
| 更改评分历史格式 | 需要 |

### 10.3.4 最小迁移接口

```python
async def transform_state(
    self,
    old_state: dict[str, object],
    from_version: int,
    to_version: int,
) -> dict[str, object]:
    ...
```

### 10.3.5 protected 组件的特殊规则

以下位点或子能力默认需要更高门槛：

- `policy.primary`
- 身份根或等价授权根
- `evaluation.loop_guard`
- 决定回滚判定的关键治理 hook

这类替换必须额外经过：

- 人工审查或签名授权
- 更长观察窗口
- 更严格影子验证
- 显式回滚预案

## 10.4 创建一个新的模板化组件

如果你不是要直接写一个完整组件，而是要把某类高频改动沉淀成模板，应按"骨架固定、槽位开放"的方式建设模板。

### 10.4.1 判断是否值得做模板

| 特征 | 适合做模板吗 |
| --- | --- |
| 经常重复出现的局部逻辑 | 是 |
| 只改参数和少量规则 | 是 |
| ports 和 contracts 基本稳定 | 是 |
| 依赖大量自由代码生成 | 否 |
| 强依赖未稳定的内部宿主对象 | 否 |

### 10.4.2 模板建设流程

```text
1. freeze contracts and slot binding
2. extract stable skeleton
3. define TemplateSlot schema
4. add validation profile
5. add default tests and examples
6. publish into template catalog
```

### 10.4.3 模板示例

```yaml
template_id: planner.rule_router
component_kind: planner
slot_bindings:
  - planner.primary
slots:
  - name: route_rules
    kind: json
    required: true
  - name: fallback_strategy
    kind: enum
    required: true
  - name: risk_threshold
    kind: float
    required: true
```

### 10.4.4 完整模板骨架示例

```python
class SemanticChunker(HarnessComponent):
    """语义分块组件模板。"""

    name = "SemanticChunker"
    version = "1.0.0"
    base_type = "Memory"

    def declare_interface(self, api: HarnessAPI) -> None:
        api.declare_input(Input(name="text", type=str, required=True))
        api.declare_output(Output(name="chunks", type=list[str]))
        api.declare_event(Event(name="on_chunk_complete"))

    async def process(self, inputs: dict) -> dict:
        text = inputs["text"]
        # === SLOT START: chunk_strategy ===
        chunks = self._default_chunk(text)
        # === SLOT END ===
        await self.emit_event("on_chunk_complete", {"chunk_count": len(chunks)})
        return {"chunks": chunks}

    def _default_chunk(self, text: str) -> list[str]:
        paragraphs = text.split("\n\n")
        return [p.strip() for p in paragraphs if p.strip()]
```

### 10.4.5 模板设计检查单

| 检查项 | 通过标准 |
| --- | --- |
| `contracts` 是否固定 | 输入/输出/Event 已冻结 |
| `slots` 是否有类型与范围 | 每个 slot 有 schema |
| 是否可映射到 `ComponentManifest` | 模板实例化后能转成 manifest |
| 是否有最小测试样例 | 至少覆盖一个成功路径和一个失败路径 |
| 是否有风险标签 | 能进入 Policy 预审 |

## 10.5 扩展 Optimizer 的搜索策略

当基础的三阶段搜索已经可用后，可以继续扩展搜索策略。注意，搜索器是**元层策略实现**，不是普通业务组件。

### 10.5.1 搜索策略接口

```python
class SearchStrategy(ABC):
    """Optimizer 搜索策略的基类。"""

    @abstractmethod
    async def propose(
        self,
        current_state: OptimizerState,
        history: list[EvaluationRecord],
    ) -> list[CandidateConfig]:
        """基于当前状态和历史评估记录，提出候选配置。"""
        ...

    @abstractmethod
    def update(
        self,
        candidate: CandidateConfig,
        evaluation: EvaluationResult,
    ) -> None:
        """根据评估结果更新搜索策略的内部状态。"""
        ...
```

### 10.5.2 实现自定义搜索策略

```python
class BayesianPlusStrategy(SearchStrategy):
    """贝叶斯优化 + 进化搜索的混合策略。"""

    def __init__(self, config: StrategyConfig):
        self.bo_optimizer = GaussianProcessOptimizer(
            config_space=config.param_space,
            acquisition="EHVI",
        )
        self.population_size = config.population_size or 20
        self.population: list[CandidateConfig] = []

    async def propose(
        self,
        current_state: OptimizerState,
        history: list[EvaluationRecord],
    ) -> list[CandidateConfig]:
        candidates = []

        # 路径 1: 贝叶斯优化 — 参数微调
        if history:
            for record in history:
                self.bo_optimizer.tell(record.config, record.metrics)
            bo_suggestion = self.bo_optimizer.ask(n=3)
            candidates.extend(bo_suggestion)

        # 路径 2: 进化搜索 — 结构变更
        if self.population:
            parents = self._select_parents(current_state.pareto_front)
            for parent in parents:
                child = self._mutate(parent)
                candidates.append(child)

        # 路径 3: LLM 提议 — 反事实诊断驱动
        if current_state.bottleneck_detected:
            llm_proposals = await self._llm_propose(current_state, history)
            candidates.extend(llm_proposals)

        return candidates

    def update(
        self,
        candidate: CandidateConfig,
        evaluation: EvaluationResult,
    ) -> None:
        self.bo_optimizer.tell(candidate, evaluation.metrics)
        if evaluation.fitness > self._worst_fitness_in_population():
            self.population.append(candidate)
            if len(self.population) > self.population_size:
                self._cull_population()

    def _mutate(self, parent: CandidateConfig) -> CandidateConfig:
        child = parent.copy()
        if random.random() < 0.85:
            param = random.choice(list(child.params.keys()))
            child.params[param] = self._perturb(child.params[param])
        else:
            child = self._structural_mutation(child)
        return child
```

### 10.5.3 可扩展的搜索策略位点

| 位点 | 作用 | 例子 |
| --- | --- | --- |
| `search_scheduler` | 决定进入 Phase A/B/C | 从固定阈值切到自适应调度 |
| `candidate_ranker` | 候选排序 | 从启发式排序切到 bandit/UCB |
| `state_encoder` | 状态编码 | 从手工特征升级为 GIN 混合编码 |
| `action_generator` | 动作生成 | 增加拓扑重构或模板实例化算子 |
| `convergence_controller` | 收敛判断 | 从单一 HV 阈值升级到三重判据 |

### 10.5.4 搜索策略扩展原则

| 原则 | 说明 |
| --- | --- |
| 不绕过动作漏斗 | 高风险动作不能直接开放 |
| 不绕过 `contract-driven pruning` | 合法候选必须先剪枝 |
| 不直接提交 active graph | 仍需通过 candidate graph |
| 不直接修改 protected 组件 | 需走治理授权 |

### 10.5.5 示例：新增一个 UCB 候选排序器

```python
class UCBCandidateRanker:
    def rank(self, candidates: list[dict[str, object]]) -> list[dict[str, object]]:
        return sorted(
            candidates,
            key=lambda item: item["mean_reward"] + item["explore_bonus"],
            reverse=True,
        )
```

### 10.5.6 注册搜索策略

```python
optimizer_config = {
    "strategy": "BayesianPlusStrategy",
    "strategy_config": {
        "population_size": 20,
        "param_space": {
            "top_k": {"type": "int", "range": [1, 50]},
            "temperature": {"type": "float", "range": [0.0, 2.0]},
        }
    }
}
strategy = StrategyRegistry.create(optimizer_config)
```

## 10.6 添加新的安全规则

安全规则不应散落在业务组件内部，而应尽量作为 Policy / Governance 的规则资产维护。

### 10.6.1 哪些规则适合新增

| 规则类型 | 例子 |
| --- | --- |
| 资源限制 | CPU、内存、token、并发上限 |
| 数据边界 | Secret、隐私、敏感输出过滤 |
| 结构限制 | protected rebinding 禁止、最大图深度 |
| 发布限制 | 影子验证通过率、观察窗口长度 |
| 科研治理 | 溯源、重现性、评审模拟 |

### 10.6.2 规则实现

```python
class MaxConcurrencyRule(GovernanceRule):
    """自定义规则：限制并发任务数。"""

    rule_id = "C-06"
    rule_name = "最大并发约束"
    rule_type = "universal"
    intercept_phase = "runtime"

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent

    def evaluate(self, context: GovernanceContext) -> RuleResult:
        active_tasks = context.runtime_metrics.get("active_task_count", 0)
        violated = active_tasks > self.max_concurrent
        return RuleResult(
            rule_id=self.rule_id,
            passed=not violated,
            details=f"当前并发任务数: {active_tasks}（上限 {self.max_concurrent}）"
        )

    def get_veto_signal(self) -> VetoSignal:
        return VetoSignal(
            severity="medium",
            action="throttle",
            message="并发任务数超限，新任务将被排队"
        )
```

### 10.6.3 规则定义建议

```yaml
rule_id: C-09
name: forbid_unreviewed_policy_rebinding
scope: mutation
severity: high
match:
  target_slot: policy.primary
  actor: optimizer
condition:
  requires_human_review: true
action:
  decision: deny
  reason: "policy.primary cannot be rebound automatically"
```

### 10.6.4 规则接入位置

| 阶段 | 作用 |
| --- | --- |
| proposal pre-check | 早期阻断明显非法提议 |
| candidate graph validation | 检查结构与依赖 |
| shadow validation | 检查行为退化 |
| commit gate | 决定是否允许切换 |
| post-commit observation | 持续监控是否回滚 |

### 10.6.5 新规则上线建议

- 先以 `shadow` 模式运行
- 收集误报与漏报
- 再升级为 `deny` 或 `guard`
- 对高严重级别规则配人工确认通道

### 10.6.6 注册规则

```python
policy_config = {
    "rules": [
        {"id": "C-01", "class": "rules.builtin.ResourceHardCap"},
        {"id": "C-02", "class": "rules.builtin.ShadowConsistency"},
        {"id": "C-03", "class": "rules.builtin.CriticalPathProtection"},
        {"id": "C-04", "class": "rules.builtin.TokenBudgetCircuitBreaker"},
        {"id": "C-05", "class": "rules.builtin.PrivacyLeakBlocker"},
        {"id": "C-06", "class": "rules.custom.my_custom_rule.MaxConcurrencyRule",
         "params": {"max_concurrent": 5}},
    ]
}
```

## 10.7 添加治理 hooks

治理 hooks 是把 Policy / Governance 插入生命周期关键点的标准方式。相比直接改业务代码，hooks 的优势是边界更清晰、审计更完整。

### 10.7.1 推荐 hook 点位

| Hook 事件 | 用途 |
| --- | --- |
| `BEFORE_REGISTER_COMPONENT` | 拦截非法组件注册 |
| `AFTER_REGISTER_COMPONENT` | 补充风险标签或审计信息 |
| `BEFORE_ASSEMBLE_GRAPH` | 检查 slot rebinding 合法性 |
| `BEFORE_ACTIVATE_CANDIDATE` | 做切换前授权 |
| `AFTER_SHADOW_TEST` | 汇总影子测试证据 |
| `BEFORE_COMMIT_GRAPH` | 最终提交闸门 |
| `ROLLBACK_TRIGGERED` | 写入回滚证据与 dead-end 标记 |

### 10.7.2 hook 类型建议

| 类型 | 语义 | 适用场景 |
| --- | --- | --- |
| `GUARD` | 允许 veto | 阻止危险变更 |
| `MUTATE` | 可补充默认字段或风险标签 | 增加治理元数据 |
| `REDUCE` | 汇聚多方判断 | 合并多个验证结论 |
| `NOTIFY` | 只记录，不拦截 | 审计与观测 |

### 10.7.3 hook 示例

```python
async def rate_limit_guard(operation: Operation) -> GuardResult:
    """自定义 Guard 钩子：基于令牌桶的速率限制。"""
    bucket = get_token_bucket(operation.component_id)
    if not bucket.consume():
        return GuardResult(
            blocked=True,
            reason=f"速率限制: {operation.component_id} 已达上限"
        )
    return GuardResult(blocked=False)


async def audit_log_reduce(result: OperationResult) -> None:
    """自定义 Reduce 钩子：将操作结果写入外部审计系统。"""
    external_audit.log({
        "operation": result.operation_type,
        "component": result.component_id,
        "timestamp": result.end_time.isoformat(),
        "success": result.success,
        "duration_ms": result.duration_ms,
    })
```

### 10.7.4 注册 Hook

```python
policy.hook_dispatcher.register("guard", rate_limit_guard)
policy.hook_dispatcher.register("reduce", audit_log_reduce)
```

### 10.7.5 设计建议

- `GUARD` hook 应尽量纯函数化，避免副作用
- `MUTATE` hook 应只补充元数据，不应偷偷改业务语义
- `REDUCE` hook 应输出可审计的聚合理由
- `NOTIFY` hook 应绑定 `graph version` 与 `instantiation_id`

## 10.8 测试模式

Meta-Harness 的测试不能只测"函数能不能跑"，还要测组件是否能装配、能切换、能回滚、能被治理链正确处理。

### 10.8.1 测试层次

| 层次 | 目标 | 例子 |
| --- | --- | --- |
| 单元测试 | 测组件局部逻辑 | 评分函数、路由规则、迁移函数 |
| contract 测试 | 测输入/输出/Event 是否符合声明 | manifest 与实现一致性 |
| 装配测试 | 测 `candidate graph` 是否可构建 | slot/capability 匹配 |
| 影子验证测试 | 测新旧实现并行表现 | 回归率与副作用隔离 |
| 回滚测试 | 测失败后能否恢复 | graph version rollback |
| 治理测试 | 测规则与 hooks 是否按预期 veto | protected 组件保护 |

### 10.8.2 单元测试（使用 Mock Runtime）

```python
from harness_sdk.testing import MockRuntime, create_test_component, MockLLM

async def test_component_with_mock_runtime() -> None:
    """在隔离环境中测试组件局部逻辑。"""
    mock_llm = MockLLM()
    mock_llm.set_response("generate", '{"action": "search", "query": "test"}')
    runtime = MockRuntime(llm=mock_llm)
    component = create_test_component(
        MyComponent,  # 你的组件类
        runtime=runtime,
        config={"param": "test-value"}
    )
    result = await component.process({"input": "test query"})
    assert "output" in result
    assert runtime.llm.call_count == 1
```

### 10.8.3 集成测试（使用沙箱）

```python
from harness_sdk.testing import SandboxTestEnv

async def test_component_in_sandbox() -> None:
    """在沙箱中验证组件行为，不污染 active graph。"""
    async with SandboxTestEnv(tier="general_isolation") as env:
        component_id = await env.deploy(
            component_cls=MyComponent,
            config={"param": "test-value"}
        )
        result = await env.execute_task(
            component_id=component_id,
            task={"input": "integration test query"}
        )
        assert result.success
        assert len(result.output["results"]) <= 3
        metrics = await env.get_metrics(component_id)
        assert metrics.memory_peak_mb < 512
        assert metrics.cpu_avg_percent < 80
```

### 10.8.4 候选图测试模板

```python
def test_candidate_graph_requires_all_required_inputs(candidate_graph):
    errors = CompatibilityValidator().validate(candidate_graph)
    assert "missing required input" not in errors
```

### 10.8.5 回滚测试模板

```python
def test_rollback_restores_previous_graph_version(version_store):
    active = version_store.get_active()
    failed_candidate = version_store.stage_candidate()
    version_store.rollback(to_version=active)
    assert version_store.get_active() == active
```

### 10.8.6 测试优先顺序

```text
unit logic
  -> contract checks
  -> candidate graph assembly
  -> shadow validation
  -> rollback and governance paths
```

## 10.9 调试技巧

Meta-Harness 的调试重点，不是只看栈追踪，而是要能快速定位：问题发生在哪个 graph version、哪个 slot、哪个 hook、哪个验证阶段。

### 10.9.1 常见问题与排查方向

| 症状 | 优先检查 |
| --- | --- |
| 组件装不上图 | `contracts`、slot/capability 匹配、required inputs |
| 组件能装但切换失败 | `activate()`、迁移逻辑、影子验证结果 |
| 切换成功但性能退化 | `Evaluation` 指标、trace diff、路由变化 |
| Proposal 总被拒绝 | Policy 规则、risk level、protected 触碰情况 |
| 回滚后仍异常 | 状态恢复、message replay、旧版本依赖是否完整 |

### 10.9.2 推荐调试顺序

```text
1. identify active graph version
2. inspect candidate diff
3. inspect validation report
4. inspect policy decisions and hooks
5. inspect trace summary and rollback record
```

### 10.9.3 高价值调试视图

| 视图 | 作用 |
| --- | --- |
| `graph diff view` | 看本轮候选改了哪些组件和连接 |
| `slot binding view` | 看 primary/secondary 绑定是否正确 |
| `validation timeline` | 看失败发生在静态校验还是动态验证 |
| `hook decision log` | 看哪个 hook 做了 deny / mutate |
| `rollback lineage` | 看当前版本是如何回滚出来的 |

### 10.9.4 轨迹检查

```python
traces = await observability.get_failed_traces(
    component="Memory_1", limit=5
)
for trace in traces:
    print(f"任务 {trace.task_id}:")
    for step in trace.steps:
        print(f"  步骤 {step.step_id}: {step.action} "
              f"({step.duration_ms}ms, {step.token_used} tokens)")
    print(f"  错误: {trace.error_message}")
```

### 10.9.5 配置版本对比

```python
comparison = await config_manager.diff(version_a="cfg_v5", version_b="cfg_v7")
for diff in comparison.component_diffs:
    print(f"组件 {diff.component_id}:")
    print(f"  参数变更: {diff.param_changes}")
    print(f"  连接变更: {diff.connection_changes}")
    print(f"  接口变更: {diff.interface_changes}")
```

### 10.9.6 证据链回溯

```python
lineage = await audit_query.get_config_lineage(config_id="cfg_v7")
for evidence in lineage:
    print(f"[{evidence.timestamp}] {evidence.prov_id}")
    print(f"  触发原因: {evidence.trigger_reason}")
    print(f"  沙箱结果: {evidence.eval_results.sandbox_status}")
    print(f"  A/B 测试: delta={evidence.eval_results.ab_test_metric_delta}")
    print(f"  Policy 审查: {'通过' if not evidence.eval_results.policy_veto else '否决'}")
    if evidence.rollback_info.triggered:
        print(f"  回滚原因: {evidence.rollback_info.reason}")
```

### 10.9.7 调试时应避免什么

- 直接在生产图上手动修边
- 跳过 Policy 规则做"先跑起来再说"
- 把多个改动打包到一个候选图里一起试
- 不记录失败候选，只保留成功版本

## 10.10 phase-based 实施路线图

为了让扩展体系平稳落地，建议把实现分成多个 phase，而不是一口气把所有高级能力都接入。

### 10.10.1 Phase 1：固定组件与连接骨架

目标：让系统先具备"可声明、可装配、可校验"的基本能力。

| 任务 | 产物 | 验收标准 |
| --- | --- | --- |
| 冻结 `HarnessComponent` / `HarnessAPI` / `ComponentRuntime` | SDK 基类 | 所有抽象方法有类型签名 |
| 定义基础 `contracts` 与 capability vocabulary | 统一接口面 | 9 个核心组件的抽象定义完整 |
| 实现 `ComponentManifest` 与 `ComponentRegistry` | 组件注册表 | 能解析包含 Component/Connection 的完整配置 |
| 实现 `ConnectionEngine` 与 5 条兼容规则 | 候选图装配能力 | 5 条校验规则全部实现并通过单元测试 |

### 10.10.2 Phase 2：支持候选图切换与回滚

目标：让组件扩展不再停留在启动时替换，而是进入 graph version 管理。

| 任务 | 产物 | 验收标准 |
| --- | --- | --- |
| 实现 `pending mutations` | 候选变更草案 | 改动以 delta 形式暂存 |
| 实现 `graph versions` | 活动图/候选图/回滚图 | 每次提交产生单调递增版本 |
| 实现状态导出与迁移接口 | 热切换基础 | 至少 3 个迁移适配器通过测试 |
| 实现观察窗口与 rollback watcher | 回滚闭环 | 能在 300 秒内检测到退化并自动回滚 |

### 10.10.3 Phase 3：引入模板库与最小可行 Proposer

目标：让扩展从"手写组件"升级为"模板化实例化"。

| 任务 | 产物 | 验收标准 |
| --- | --- | --- |
| 建立模板目录与 `TemplateSlot` schema | 组件模板库 | 所有模板通过兼容性校验和单元测试 |
| 实现 6-step code generation pipeline | 模板实例化闭环 | 管线全部自动化 |
| 实现 `LogGopher`、`DiffAnalyzer`、`PatchBuilder` | 最小可行 Proposer | 能从失败轨迹诊断并生成补丁 |
| 接入反事实诊断提示模板 | 诊断驱动 patch 生成 | 诊断输出可映射到 slot values |

### 10.10.4 Phase 4：扩展搜索策略与治理链

目标：把自增长控制面真正做成工业级系统。

| 任务 | 产物 | 验收标准 |
| --- | --- | --- |
| 接入 GIN 混合状态编码 | 结构感知优化输入 | 图结构特征可正确编码 |
| 扩展候选排序与动作生成器 | 更高样本效率 | 非法候选比例显著下降 |
| 新增安全规则和治理 hooks | 更细粒度控制 | C-01~C-05 全部实现并可拦截 |
| 完善 evidence chain 与 replay | 可审计、可复盘 | 完整证据链可回溯任意 graph version |

### 10.10.5 Phase 5：收敛控制与生态化

目标：从单机原型升级为稳定可运营的平台能力。

| 任务 | 产物 | 验收标准 |
| --- | --- | --- |
| 引入三重收敛判据 | 更稳定停机策略 | HV + 统计检验 + 复杂度饱和正常工作 |
| 扩展模板 catalog 与组件市场 | 更丰富的组件生态 | 模板数 >= 10，覆盖全部 9 组件位点 |
| 建立变更质量看板 | 版本质量可视化 | 可实时查看 graph version 健康度 |
| 建立 dead-end memory | 避免重复探索失败路径 | 重复失败路径命中率显著下降 |

### 10.10.6 阶段依赖关系

```text
Phase 1: 固定组件与连接骨架
    |
    ▼
Phase 2: 候选图切换与回滚
    |
    ▼
Phase 3: 模板库与最小可行 Proposer
    |
    ▼
Phase 4: 扩展搜索策略与治理链
    |
    ▼
Phase 5: 收敛控制与生态化
```

**关键约束**：Phase 2（安全机制与回滚）必须在 Phase 4（搜索策略扩展）之前完成。安全沙箱与回滚基础设施是所有优化工作的前提，而非可后置的附加模块。

## 10.11 扩展工作清单

最后给出一个面向开发者的简版 checklist。每次你要扩展 Meta-Harness，可以先过一遍：

| 检查项 | 是/否 |
| --- | --- |
| 已明确目标 slot 和 `component_kind` | |
| 已定义输入/输出/Event contracts | |
| 已声明 provides / requires capabilities | |
| 已写 `ComponentManifest` 或模板 schema | |
| 已考虑是否触碰 protected 组件 | |
| 已进入 `pending mutations` 而非直改 active graph | |
| 已准备最小验证、影子验证与回滚方案 | |
| 已绑定 `graph version`、证据对象与审计记录 | |

### 10.11.1 组件检查清单

- [ ] `harness.component.json` 中的 `<Interface>` 定义完整
- [ ] 所有 `required=true` 的 Input 在 `process()` 中被正确处理
- [ ] 所有 Output 在 `process()` 返回值中包含
- [ ] 组件不包含任何对其他组件的直接依赖（仅通过 Connection 通信）
- [ ] `async def initialize()` 和 `async def shutdown()` 正确实现
- [ ] 单元测试覆盖率 >= 80%
- [ ] 通过 `ruff check --fix .` 和 `ruff format .`

### 10.11.2 模板检查清单

- [ ] 模板骨架包含完整的 `<Interface>` 定义
- [ ] 所有槽位在 `harness.component.json` 中有对应的约束声明
- [ ] 附带的单元测试覆盖正常和边界情况
- [ ] 默认参数值在合理范围内
- [ ] 通过静态兼容性校验

### 10.11.3 安全规则检查清单

- [ ] 规则 ID 遵循命名规范（通用: C-XX, 科研: R-XX）
- [ ] `intercept_phase` 明确指定（pre_compilation / link_time / runtime）
- [ ] `get_veto_signal()` 返回合理的严重级别和处理动作
- [ ] 规则评估逻辑有单元测试覆盖
- [ ] 在 `rules/` 目录中有对应的文档说明

## 10.12 小结

Meta-Harness 的扩展指南可以浓缩为一句话：**一切扩展都必须经过"接口声明 -> 候选装配 -> 治理校验 -> 图版本切换 -> 观察与回滚"的同一条主路径。**

在这个前提下：

- 新组件扩展是增加实现；
- 核心组件替换是受迁移约束的 graph cutover；
- 新模板扩展是把高频改动沉淀为 slot-filled 资产；
- 搜索策略扩展是增强 Optimizer 的元层能力；
- 安全规则与治理 hooks 扩展是把系统边界做得更清晰、更可控。

只有这样，Meta-Harness 才能在保持可进化的同时，仍然是一个**可验证、可回滚、可治理**的工程系统。

## 10.13 对扩展生态的长期影响

除当前强化路线图外，还需要预留对 CMA-inspired 基础设施演进的适配空间。对扩展作者而言，最重要的信号不是“今天必须重写”，而是未来接口压力可能出现在哪里：

- **对 `nektar`、`ai4pde` 一类下游扩展的影响**：如果 `SessionStore` / `SessionEvent` 成为更统一的状态与观测基底，扩展会更需要显式声明哪些状态可导出、哪些事件应结构化上报
- **对 runtime 绑定方式的影响**：如果 `HarnessRuntime` 逐步去状态化，依赖进程内缓存、隐式单例或长驻对象句柄的扩展会承受更大适配压力
- **对凭证与执行面的影响**：如果后续引入 `Credential Vault` 和更强惰性沙箱，扩展应尽量避免默认假设“凭证可直接读取”或“工具执行与宿主进程同边界”
- **对模型接入面的影响**：如果 `BrainProvider` 成为稳定抽象，扩展应更偏向依赖能力与契约，而不是把特定模型 SDK 细节写死在组件内部

因此，面向扩展的稳妥策略仍然是：保持 contracts 清晰、状态导出显式、事件语义结构化、宿主假设最小化。这样既兼容当前 MHE，也更容易适应未来基础设施演进。
