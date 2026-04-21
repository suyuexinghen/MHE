# 09. 模板库与代码生成

本章把 Meta-Harness 的"模板化扩展"落到一套可执行的工程机制上：用**组件模板库（template library）**约束 Optimizer 动作空间，用**slot/capability system**保证装配合法性，用**6 步代码生成管线**把 Proposer 的建议转成可验证候选，再用治理链把高风险自由生成收缩到最小范围。

这里沿用前文术语：

- **9 core components**：九个运行期核心位点
- **Optimizer**：元层优化器
- **Proposer**：生成候选改动的提议器
- **slot/capability system**：位点约束与能力匹配系统
- **contracts**：输入/输出/事件契约
- **pending mutations**：待提交变更
- **graph versions**：候选图、活动图、回滚图版本体系
- **staged lifecycle**：发现、校验、候选装配、激活、提交、回滚

## 9.1 为什么需要组件模板库

如果 Meta-Harness 允许优化器直接进行自由形式代码生成，系统很快会遇到三个问题：

| 问题 | 典型表现 | 工程后果 |
| --- | --- | --- |
| 搜索空间失控 | 任意新类、任意新依赖、任意副作用 | 样本预算迅速耗尽 |
| 集成风险升高 | 端口不匹配、状态迁移缺失、回滚点模糊 | 候选图难以提交 |
| 治理难度陡增 | Policy 很难在语义层面快速判定安全性 | 四级安全链路成本过高 |

因此，Meta-Harness 的代码生成不应从"完整程序自由生成"起步，而应从**模板驱动（template-based）**起步：

1. 先固定组件骨架；
2. 再暴露有限槽位；
3. 让 Optimizer 只在可审计的范围内填充；
4. 最终把输出接回 `candidate graph` 与 `pending mutations` 流程。

一句话概括：**模板库是 Optimizer 的动作漏斗在代码层面的具象化。**

## 9.2 模板设计原则

组件模板库中的每个模板都是一个"半成品"组件：具备完整的接口定义和固定的执行骨架，但内部的某些逻辑允许被 Optimizer 动态填充。设计遵循以下六大原则：

| 原则 | 含义 | 工程价值 |
|---|---|---|
| **骨架先行** | 先固定组件结构，再暴露槽位 | 必须预定义输入/输出/Event 与 slot |
| **契约冻结** | 模板实例化不应改变对外 contract | 默认不允许改动 ports schema |
| **槽位有限** | 只开放少量可验证字段 | 每个 slot 都有类型、范围、默认值 |
| **局部副作用** | 副作用边界必须明确 | 工具调用、文件写入、网络访问需经 Policy |
| **可迁移** | 模板实例升级必须考虑状态迁移 | 给出 `state_schema_version` 与迁移策略 |
| **可审计** | 每次实例化都能形成证据对象 | 记录模板 ID、slot diff、验证报告 |

### 9.2.1 模板目录结构

```
templates/
├── memory/
│   ├── BM25Retriever/
│   │   ├── harness.component.json    # 组件清单（含 Interface 定义）
│   │   ├── skeleton.py               # 执行骨架（含槽位标记）
│   │   ├── tests/                    # 附带的单元测试
│   │   │   ├── test_basic.py
│   │   │   └── test_edge_cases.py
│   │   └── migration/                # 版本迁移适配器
│   │       └── v1_to_v2.py
│   └── ContextPruner/
│       ├── harness.component.json
│       ├── skeleton.py
│         ├── tests/
│       └── migration/
├── planner/
│   ├── ChainOfThoughtPlanner/
│   └── RetryWithBackoff/
├── evaluation/
│   ├── LoopGuard/
│   └── SemanticValidator/
├── policy/
│   └── TokenBudgetGuard/
├── optimizer/
│   ├── LogGopher/
│   ├── DiffAnalyzer/
│   └── XPathPatcher/
└── registry.json                     # 模板库全局注册表
```

### 9.2.2 模板清单文件

```json
{
  "id": "BM25Retriever",
  "type": "Memory",
  "version": "2.1.0",
  "description": "基于 BM25 算法的文本检索组件",
  "base_type": "Memory",
  "interface": {
    "inputs": [
      {"name": "query", "type": "str", "required": true},
      {"name": "corpus", "type": "list[str]", "required": true}
    ],
    "outputs": [
      {"name": "results", "type": "list[SearchResult]"}
    ],
    "events": ["on_retrieval_complete", "on_no_results"]
  },
  "slots": [
    {
      "name": "scoring_function",
      "type": "callable",
      "description": "BM25 评分函数，接收 (query_tokens, doc_tokens) 返回 float",
      "default": "bm25_standard",
      "constraints": {
        "input_types": ["list[str]", "list[str]"],
        "output_type": "float",
        "max_lines": 30
      }
    },
    {
      "name": "rerank_strategy",
      "type": "callable",
      "description": "重排逻辑，接收原始结果列表返回重排后列表",
      "default": null,
      "required": false,
      "constraints": {
        "input_types": ["list[SearchResult]"],
        "output_type": "list[SearchResult]",
        "max_lines": 20
      }
    }
  ],
  "params": {
    "top_k": {"type": "int", "default": 10, "range": [1, 100]},
    "dedup_threshold": {"type": "float", "default": 0.95, "range": [0.0, 1.0]}
  },
  "tests": ["tests/test_basic.py", "tests/test_edge_cases.py"],
  "migration_from": ["1.0", "2.0"]
}
```

### 9.2.3 模板与组件 manifest 的关系

| 对象 | 作用 | 是否面向运行时 |
| --- | --- | --- |
| `ComponentTemplate` | 描述"可生成的半成品骨架" | 否，面向设计期与候选期 |
| `ComponentManifest` | 描述"可被装配的组件实例" | 是，面向装配与运行时 |
| `GraphSnapshot` | 描述"当前被提交的组件图版本" | 是，面向运行时路由 |

也就是说：

```text
template
  -> instantiate with slot values
  -> component manifest + implementation bundle
  -> candidate graph assembly
  -> staged lifecycle validation
```

## 9.3 槽位填充 vs 自由代码生成

### 9.3.1 效能对比

实证研究显示，模板驱动与自由形式代码生成在通过率和可维护性上存在显著差距：

| 评估维度 | 槽位填充 (Slot Filling) | 自由形式 (Full Program Gen) | 差距倍数 |
|---|---|---|---|
| **首轮通过率 (Pass@1)** | 85% - 92% | 25% - 34% | ~3x |
| **语法/类型错误率** | < 2% | 15.6% - 19.8% | ~10x |
| **逻辑回归频率** | 极低（结构固定） | 较高（副作用难以追踪） | - |
| **静态检查过滤效率** | 极高（Schema 可预测） | 中（逻辑复杂导致伪阳性） | - |
| **推理时延增量** | 近乎零（替换片段） | 显著（全量重构/校验） | - |
| **安全审计难度** | 低（变更范围可控） | 高（全量审查） | - |

### 9.3.2 为什么槽位填充更优

模板驱动生成的优势源于其对 LLM 的"诱导式约束"。当 LLM 只需在以下骨架中填充逻辑时：

```python
def process(data: dict) -> dict:
    """__SLOT__: scoring_function — BM25 评分逻辑"""
    # === SLOT START: scoring_function ===
    # LLM 仅在此处生成代码
    # === SLOT END ===
    return result
```

其输出更符合预训练数据中的函数级模式。而自由形式生成往往会引入冗余的依赖包、非标准的类定义，甚至是与现有 Harness 架构冲突的并行线程逻辑，导致系统在集成阶段崩溃。

**核心洞察**：Optimizer 不应要求 LLM 写一个完整的 Memory 类，而应提供包含 `save()`、`retrieve()` 接口的骨架，仅让 LLM 实现其核心的"相关度计算函数"。这种"带槽位的细粒度模板"在接口稳定性与可组合性之间达到了最佳平衡点。

### 9.3.3 两种方式的适用边界

| 维度 | 槽位填充（Slot Filling） | 自由形式生成（Free-form Generation） |
| --- | --- | --- |
| 生成边界 | 固定骨架内填空 | 从零或半零开始生成完整实现 |
| 对 contracts 的影响 | 通常不改变对外契约 | 容易引入未声明契约 |
| 集成成本 | 低 | 高 |
| 静态校验可预测性 | 高 | 中到低 |
| 回归定位难度 | 低，diff 集中在 slots | 高，diff 分散在多处代码 |
| 状态迁移难度 | 低，可提前规划 | 高，常缺乏稳定 schema |
| 适合阶段 | Phase B / Phase C 早期 | 仅适合 Phase C 末段且需强治理 |
| 默认推荐级别 | 推荐默认路径 | 最后手段 |

```text
Phase A: 参数搜索
  -> 不需要代码生成
Phase B: 模板实例化
  -> 以 slot filling 为主
Phase C: 受限合成
  -> 先 slot filling，再允许局部自由生成
```

结论不是"永远禁止自由形式生成"，而是：**只有当模板骨架无法表达目标改动时，才让自由生成进入受限区域。**

## 9.4 模板对象模型

模板库可以抽象成一组一等对象：

```python
from dataclasses import dataclass
from typing import Any


@dataclass
class TemplateSlot:
    name: str
    kind: str
    required: bool
    default: Any | None = None
    range_expr: str | None = None
    description: str = ""


@dataclass
class ComponentTemplate:
    template_id: str
    component_kind: str
    slot_bindings: list[str]
    input_contracts: list[str]
    output_contracts: list[str]
    event_contracts: list[str]
    capabilities: list[str]
    sandbox_level: str
    state_schema_version: int
    slots: list[TemplateSlot]
```

## 9.5 模板目录与分类方式

模板库建议按"组件位点 + 风险等级 + 变异自由度"组织，而不是按作者或项目来源杂乱堆放。

### 9.5.1 推荐目录结构

```text
metaharness/
├── templates/
│   ├── planner/
│   ├── memory/
│   ├── evaluation/
│   ├── observability/
│   ├── policy/
│   ├── optimizer/
│   └── shared/
└── template_manifests/
```

### 9.5.2 模板分类标签

| 标签 | 用途 |
| --- | --- |
| `component_kind` | 对应 `planner`、`memory`、`evaluation` 等 |
| `risk_level` | `low` / `medium` / `high` |
| `synthesis_mode` | `param_only` / `slot_fill` / `restricted_code` |
| `hot_swap_mode` | `restart` / `drain-and-resume` / `suspend-transform-resume` |
| `stateful` | 是否带状态迁移要求 |
| `protected_compatible` | 是否可接近 protected 邻接位点 |

## 9.6 模板目录总表

下面给出一套最小可落地的模板目录（catalog）。这些模板并不是"全部实现"，而是模板库初始化时最值得优先建设的条目。

| 模板 ID | 组件位点 | synthesis mode | 典型槽位 | 默认风险 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `planner.rule_router` | `planner.primary` | `slot_fill` | 路由条件、优先级、回退策略 | 低 | 规则优先的轻量规划器 |
| `planner.react_loop` | `planner.primary` | `slot_fill` | system prompt、step budget、replan trigger | 中 | 面向多步推理 |
| `memory.jsonl_store` | `memory.primary` | `param_only` | flush interval、retention、snapshot window | 低 | 最小可审计 Memory |
| `memory.hybrid_retriever` | `memory.retrieval.secondary` | `slot_fill` | top_k、rerank rule、merge strategy | 中 | 结构化+语义混合检索 |
| `evaluation.multi_objective` | `evaluation.primary` | `slot_fill` | quality weights、latency penalty、cost penalty | 低 | 输出 `PerformanceVector@v1` |
| `evaluation.loop_guard` | `evaluation.primary` | `slot_fill` | ε、K、α、复杂度上限 | 中 | 收敛判据模板 |
| `observability.trace_enricher` | `observability.exporter.secondary` | `slot_fill` | tags、sampling rate、artifact fields | 低 | 追加 trace 元信息 |
| `toolhub.safe_wrapper` | `toolhub.primary` | `slot_fill` | timeout、retry、policy labels | 中 | 工具执行包装器 |
| `policy.rule_pack` | `policy.shadow.secondary` | `param_only` | deny rules、budget cap、secret filters | 高 | 影子治理规则包 |
| `optimizer.log_gopher` | `optimizer.meta` | `slot_fill` | summary schema、window size、failure buckets | 中 | 最小可行 Proposer 的日志采集器 |
| `optimizer.diff_analyzer` | `optimizer.meta` | `slot_fill` | diff granularity、comparison target、ranking rule | 中 | 比较 elite 与失败候选 |
| `optimizer.xpath_patcher` | `optimizer.meta` | `restricted_code` | patch policy、xpath scope、merge rule | 高 | 生成 XML 局部增量 |
| `connection.guard_router` | `shared` | `slot_fill` | route mode、fallback chain、shadow target | 中 | 连接规则与路由策略模板 |
| `migration.state_adapter` | `shared` | `restricted_code` | mapping rules、default values、compat policy | 高 | `state_schema_version` 迁移适配器 |

### 9.6.1 首批模板建设优先级

| 优先级 | 推荐模板 | 理由 |
| --- | --- | --- |
| P0 | `memory.jsonl_store` | 给 graph versions 与 rollback 提供最小状态基线 |
| P0 | `evaluation.multi_objective` | 给 Optimizer 提供稳定评分入口 |
| P0 | `optimizer.log_gopher` | 最小可行 Proposer 的必要前置 |
| P1 | `planner.rule_router` | 支撑低风险结构搜索 |
| P1 | `toolhub.safe_wrapper` | 连接 Policy 与执行平面 |
| P1 | `optimizer.diff_analyzer` | 提升诊断质量 |
| P2 | `migration.state_adapter` | 为热切换与状态演进做准备 |
| P2 | `optimizer.xpath_patcher` | 扩展到更细粒度 XML patch |

## 9.7 6 步代码生成管线

当 Optimizer 决定从模板库实例化一个新组件并对其进行定制时，会触发以下 6 步代码生成管线：

```text
1. select template
2. bind slots
3. synthesize local code or config patch
4. materialize candidate bundle
5. validate in staged lifecycle
6. commit or rollback by graph version
```

### 9.7.1 第 1 步：模板选择

Optimizer 从模板库中选择一个基模板。选择依据：
- 任务类型标签与模板功能域的匹配度
- 当前性能瓶颈指向的组件类型
- 模板的累积成功率（从 Memory 中查询历史数据）
- Policy 允许范围

推荐规则：
- 先选与当前瓶颈最接近的 `component_kind`
- 先选 `param_only` / `slot_fill` 模板
- 仅在前两类模板不足时进入 `restricted_code`

```python
async def select_template(
    self, bottleneck: PerformanceBottleneck
) -> TemplateMetadata:
    """根据性能瓶颈选择最合适的模板。"""
    candidates = self.registry.get_by_base_type(bottleneck.component_type)

    # 按历史成功率排序
    scored = []
    for template in candidates:
        success_rate = await self.memory.get_template_success_rate(
            template_id=template.id,
            task_type=bottleneck.task_type
        )
        scored.append((template, success_rate))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]  # 返回成功率最高的模板
```

### 9.7.2 第 2 步：绑定槽位

对每个 `TemplateSlot` 执行：
- 类型检查
- 范围检查
- 默认值补齐
- Policy 标签注入
- 风险分级

通过规则或轻量级 LLM 调用，填充模板中的可变参数：

```python
async def fill_params(
    self,
    template: TemplateMetadata,
    context: OptimizationContext,
) -> dict:
    """填充模板参数。"""
    filled = {}

    for param_name, param_spec in template.params.items():
        # 规则优先：基于经验值的快速填充
        heuristic_value = self.get_heuristic(param_name, context)
        if heuristic_value is not None:
            filled[param_name] = heuristic_value
            continue

        # LLM 填充：复杂参数调用 LLM 生成
        if param_spec.type in ("str", "callable"):
            prompt = self._build_fill_prompt(param_name, param_spec, context)
            value = await self.llm.generate(prompt, max_tokens=200)
            filled[param_name] = value
        else:
            # 数值参数：取默认值的中值
            default = param_spec.default
            low, high = param_spec.range
            filled[param_name] = (low + high) / 2 if default is None else default

    return filled
```

### 9.7.3 第 3 步：生成局部代码或配置补丁

对于更复杂的逻辑（如自定义过滤函数），调用 LLM 生成 Python 代码片段。这个步骤的目标不是生成整个组件，而是生成受限变更：

- XML 局部 patch
- 配置片段
- 模板内部函数实现
- 迁移适配逻辑

```python
async def generate_slot_code(
    self,
    slot: SlotDefinition,
    context: OptimizationContext,
) -> str:
    """为模板槽位生成代码。"""
    prompt = f"""你是一个组件代码生成器。请在以下约束内生成代码：

## 槽位信息
- 名称: {slot.name}
- 描述: {slot.description}
- 输入类型: {slot.constraints.input_types}
- 输出类型: {slot.constraints.output_type}
- 最大行数: {slot.constraints.max_lines}

## 上下文
- 任务类型: {context.task_type}
- 当前性能瓶颈: {context.bottleneck_description}

## 约束
- 仅生成函数体，不包含 import 语句
- 不使用多线程或异步操作
- 不进行文件系统或网络 I/O
- 仅使用标准库

## 输出格式
仅输出代码，不包含任何解释文本。
"""
    code = await self.llm.generate(prompt, max_tokens=500)

    # 清理：移除 markdown 代码块标记
    code = code.strip().removeprefix("```python").removesuffix("```").strip()
    return code
```

### 9.7.4 第 4 步：物化候选包

生成产物建议包括：

| 产物 | 作用 |
| --- | --- |
| `component manifest` | 用于装配与校验 |
| `implementation patch` | 用于局部代码变更 |
| `config fragment` | 用于参数与策略注入 |
| `migration recipe` | 用于状态迁移 |
| `test bundle` | 用于最小验证 |
| `evidence draft` | 用于审计链记录 |

### 9.7.5 第 5 步：静态检查与单元测试

候选必须进入与普通组件相同的校验链。先执行静态类型检查：

```python
async def static_check(
    self,
    template: TemplateMetadata,
    filled_params: dict,
    generated_code: dict[str, str],
) -> StaticCheckResult:
    """执行静态类型检查。"""
    # 1. 组装完整组件代码
    full_source = self.assemble_source(template, filled_params, generated_code)

    # 2. mypy 类型检查
    mypy_result = await run_mypy(full_source)
    if mypy_result.exit_code != 0:
        return StaticCheckResult(
            passed=False,
            errors=mypy_result.errors,
            stage="mypy"
        )

    # 3. bandit 安全扫描
    bandit_result = await run_bandit(full_source)
    if bandit_result.high_severity_issues:
        return StaticCheckResult(
            passed=False,
            errors=[i.message for i in bandit_result.high_severity_issues],
            stage="bandit"
        )

    # 4. 自定义约束检查（如无禁用 syscall、无网络访问）
    constraint_result = self.check_custom_constraints(full_source)
    if not constraint_result.passed:
        return StaticCheckResult(
            passed=False,
            errors=constraint_result.violations,
            stage="custom_constraints"
        )

    return StaticCheckResult(passed=True, full_source=full_source)
```

再在沙箱中运行模板附带的单元测试用例：

```python
async def run_template_tests(
    self,
    full_source: str,
    template: TemplateMetadata,
) -> TestResult:
    """在沙箱中运行模板的单元测试。"""
    # 创建沙箱环境
    sandbox = await self.sandbox.create(
        tier="general_isolation",  # gVisor 级别
        source_code=full_source,
        test_files=template.tests
    )

    # 执行测试
    result = await sandbox.run_tests(
        test_files=template.tests,
        timeout_sec=60
    )

    await sandbox.destroy()

    if result.failed > 0:
        return TestResult(
            passed=False,
            total=result.total,
            passed=result.passed,
            failed=result.failed,
            failures=[t.traceback for t in result.failures]
        )

    return TestResult(
        passed=True,
        total=result.total,
        passed=result.passed,
        failed=0
    )
```

### 9.7.6 第 6 步：注册入库或回滚

通过全部检查后，将生成的组件注册为候选配置的一部分：

```python
async def register_generated_component(
    self,
    template: TemplateMetadata,
    filled_params: dict,
    full_source: str,
    test_result: TestResult,
) -> RegisteredComponent:
    """注册新生成的组件。"""
    component_id = f"{template.id}_{uuid4().hex[:8]}"

    # 写入组件存储
    await self.component_store.write(
        component_id=component_id,
        source=full_source,
        manifest={
            "template_id": template.id,
            "template_version": template.version,
            "params": filled_params,
            "generated_at": utcnow().isoformat(),
            "test_result": {
                "total": test_result.total,
                "passed": test_result.passed,
            }
        }
    )

    # 注册到 ComponentRegistry
    self.registry.register(
        component_id=component_id,
        interface=template.interface,
        source_path=f"generated/{component_id}"
    )

    return RegisteredComponent(
        component_id=component_id,
        template_id=template.id,
        created_at=utcnow()
    )
```

若通过校验：
- 生成新的 `candidate graph`
- 切换为新的 `graph version`
- 进入观察窗口

若失败：
- 丢弃本轮 `pending mutations`
- 保留失败原因与 slot diff
- 更新 Proposer 的失败记忆

## 9.8 代码生成的最小实现示例

下面给出一个"模板 + 局部打分函数"的最小例子。

### 9.8.1 模板定义示意

```yaml
template_id: evaluation.multi_objective
component_kind: evaluation
slot_bindings:
  - evaluation.primary
slots:
  - name: quality_weight
    kind: float
    required: true
    range_expr: "0.0 <= x <= 1.0"
  - name: latency_penalty
    kind: float
    required: true
    range_expr: "0.0 <= x <= 5.0"
  - name: cost_penalty
    kind: float
    required: true
    range_expr: "0.0 <= x <= 5.0"
  - name: score_formula
    kind: restricted_code
    required: true
```

### 9.8.2 槽位填充后的局部函数

```python
def compute_score(metrics: dict[str, float]) -> float:
    quality = metrics["quality"]
    latency_ms = metrics["latency_ms"]
    cost_usd = metrics["cost_usd"]
    return 0.75 * quality - 0.002 * latency_ms - 0.80 * cost_usd
```

这里真正可变的只有 `score_formula` 所在槽位，而 `EvaluationComponent` 的 ports、contracts 和 runtime 边界都保持不变。

## 9.9 最小可行 Proposer（MVP）

根据前一章的搜索策略，Meta-Harness 不应一开始就构造"大而全"的 Proposer，而应先实现**最小可行 Proposer**，使其只负责三件事：读日志、比差异、出局部 patch。

### 9.9.1 MVP 结构

| 模块 | 作用 | 输入 | 输出 |
| --- | --- | --- | --- |
| `LogGopher` | 收集 trace、metrics、失败摘要 | graph version 结果、日志、artifact | 结构化诊断上下文 |
| `DiffAnalyzer` | 比较 elite 与失败候选差异 | graph diff、配置 diff、结果 diff | 归因结论与 patch 建议 |
| `TemplateSelector` | 选择最合适模板 | 诊断结论、风险预算 | `template_id` |
| `SlotBinder` | 生成 slot 值 | 模板 schema、建议参数 | `slot_values` |
| `PatchBuilder` | 产出局部 patch | 模板、slot 值 | XML patch / code patch |

### 9.9.2 Log Gopher（日志挖掘器）

负责将 Evaluation 产生的非结构化 Trace 转化为带时间戳的结构化 JSON：

```python
class LogGopher:
    """日志挖掘器：从非结构化 Trace 中提取诊断特征。"""

    def mine(self, raw_trace: str) -> StructuredTrace:
        """将原始轨迹转化为结构化诊断数据。"""
        lines = raw_trace.strip().split("\n")
        events = []

        for line in lines:
            # 提取时间戳、组件、动作、结果
            match = self._parse_line(line)
            if match:
                events.append(TraceEvent(
                    timestamp=match["timestamp"],
                    component=match["component"],
                    action=match["action"],
                    result=match["result"],
                    duration_ms=match.get("duration_ms"),
                    token_used=match.get("token_used"),
                    error=match.get("error"),
                ))

        return StructuredTrace(
            events=events,
            total_duration_ms=sum(e.duration_ms or 0 for e in events),
            total_tokens=sum(e.token_used or 0 for e in events),
            failure_points=[e for e in events if e.result == "error"],
            bottlenecks=self._identify_bottlenecks(events),
        )

    def _identify_bottlenecks(self, events: list[TraceEvent]) -> list[str]:
        """识别轨迹中的性能瓶颈。"""
        bottlenecks = []
        for e in events:
            if e.duration_ms and e.duration_ms > 5000:
                bottlenecks.append(f"{e.component}.{e.action} ({e.duration_ms}ms)")
        return bottlenecks
```

### 9.9.3 Diff Analyzer（差异分析器）

利用 LLM 对比当前最优（Elite）与历史失败案例的配置差异，生成诊断意见：

```python
class DiffAnalyzer:
    """差异分析器：对比两个配置的差异并生成诊断。"""

    async def analyze(
        self,
        elite_config: XMLConfig,
        failed_config: XMLConfig,
        elite_trace: TaskTrace,
        failed_trace: TaskTrace,
    ) -> DiagnosticReport:
        """分析两个配置的执行差异。"""
        # 1. 计算 XML Diff
        xml_diff = compute_xml_diff(elite_config, failed_config)

        # 2. 识别执行轨迹差异
        trace_divergences = self._find_divergences(elite_trace, failed_trace)

        # 3. 调用 LLM 生成诊断
        prompt = self._build_diagnostic_prompt(
            xml_diff=xml_diff,
            divergences=trace_divergences,
            elite_score=elite_trace.final_score,
            failed_score=failed_trace.final_score,
        )

        diagnosis = await self.llm.generate(prompt, max_tokens=1000)

        return DiagnosticReport(
            xml_diff=xml_diff,
            trace_divergences=trace_divergences,
            diagnosis=diagnosis,
            suggested_fixes=self._extract_fixes(diagnosis),
        )
```

### 9.9.4 XML Patcher（XML 补丁器）

基于诊断意见，使用 XPath 形式生成局部配置增量，而非重写整个 XML 文件：

```python
class XMLPatcher:
    """XML 补丁器：基于诊断生成局部配置增量。"""

    def generate_patch(
        self,
        base_config: XMLConfig,
        diagnosis: DiagnosticReport,
    ) -> list[ConfigPatch]:
        """根据诊断意见生成配置补丁。"""
        patches = []

        for fix in diagnosis.suggested_fixes:
            match fix.type:
                case "param_change":
                    patches.append(ConfigPatch(
                        xpath=f"//Component[@id='{fix.component_id}']",
                        attribute="params",
                        old_value=fix.old_value,
                        new_value=fix.new_value,
                        description=fix.reasoning,
                    ))

                case "connection_add":
                    patches.append(ConfigPatch(
                        xpath="/Harness/Connections",
                        action="append",
                        new_element=f"""
                            <Connection from="{fix.from_component}"
                                       to="{fix.to_component}"
                                       trigger="{fix.trigger}">
                                <Property key="action" value="{fix.action}"/>
                            </Connection>
                        """,
                        description=fix.reasoning,
                    ))

                case "component_add":
                    patches.append(ConfigPatch(
                        xpath="/Harness/Components",
                        action="append",
                        new_element=f"""
                            <Component id="{fix.component_id}"
                                       type="{fix.template_id}"
                                       params="{fix.params}">
                                {fix.interface_xml}
                            </Component>
                        """,
                        description=fix.reasoning,
                    ))

        return patches

    def apply_patches(
        self,
        base_config: XMLConfig,
        patches: list[ConfigPatch],
    ) -> XMLConfig:
        """将补丁应用到基础配置，生成新配置。"""
        tree = parse_xml(base_config)
        for patch in patches:
            self._apply_single_patch(tree, patch)
        return serialize_xml(tree)
```

### 9.9.5 MVP 工作流

```text
observe active graph results
  -> LogGopher summarizes regressions
  -> DiffAnalyzer compares elite vs failed candidates
  -> TemplateSelector chooses low-risk template
  -> SlotBinder produces bounded slot values
  -> PatchBuilder emits local candidate patch
```

### 9.9.6 为什么 MVP 足够重要

| 价值 | 说明 |
| --- | --- |
| 与模板库天然兼容 | 输出就是模板实例化所需的 slot 值 |
| 与治理链天然兼容 | 产出是局部 patch，不是整仓自由改写 |
| 与样本效率目标兼容 | 优先复用历史失败经验 |
| 与 `graph versions` 兼容 | 每次 proposal 都可绑定到候选版本 |

## 9.10 Proposer 迁移分析

如果把已有 Meta-Harness 风格的 Proposer 迁移到本书提出的组件图与 XML/manifest 体系，可以按下表评估。

| Proposer 机制 | 在 Meta-Harness 原型中的作用 | 向组件图体系迁移方式 | 难度 | 建议 |
| --- | --- | --- | --- | --- |
| 文件系统按需读取 | 按需读取历史运行材料 | 改为读取 `graph snapshots`、trace 摘要、evidence objects | 低 | 直接迁移 |
| 反事实诊断 | 对比高分与低分候选的行为差异 | 对比两个 `graph version` 的结构差异与运行差异 | 中 | 优先迁移 |
| 读-写-执行闭环 | 修改代码并跑测试 | 改为"修改 XML/模板槽位/局部补丁 -> 走验证链" | 中 | 需接入 staged lifecycle |
| 局部突变优先 | 偏好小改动、少回归 | 直接映射为 slot filling 与 XPath patch | 低 | 强烈保留 |
| 代码级 patch | 对源代码做局部编辑 | 优先降级为模板局部槽位 patch | 中 | 建议先模板后代码 |
| 全量 trace 深读 | 依赖大量执行轨迹细节 | 改为 trace 摘要 + failure buckets + evidence 索引 | 高 | 不建议直接照搬 |
| 失败归因恢复 | 不直接回滚，而是分析退化原因 | 与 `RollbackRecord`、失败缓存、dead-end 记忆联动 | 中 | 应作为 MVP 核心能力 |

### 9.10.1 迁移结论

最值得保留的不是"任意写代码"的自由，而是以下三种能力：

- 局部突变优先
- 反事实诊断
- 基于历史失败记忆的恢复策略

最需要重构的是：

- 对原始代码树的直接依赖
- 对全量 trace 的重上下文读取
- 缺乏结构化模板与显式 graph version 的提议接口

## 9.11 反事实诊断提示词模板

模板库与最小可行 Proposer 之间的关键连接点，是**反事实诊断（counterfactual diagnosis）**。它不是简单问"哪个版本更好"，而是要求 Proposer 对相似候选做结构化归因。

### 9.11.1 推荐提示模板

```text
你是 Meta-Harness 的 Proposer，需要比较两个 graph version 的表现差异，输出一个可执行的局部改动建议。

【输入】
- Elite graph version: {{elite_version}}
- Failed graph version: {{failed_version}}
- Target component slot: {{target_slot}}
- Relevant templates: {{candidate_templates}}
- Performance delta:
  - quality: {{delta_quality}}
  - latency_ms: {{delta_latency}}
  - cost_usd: {{delta_cost}}
  - regressions: {{regression_summary}}
- Structural diff:
  {{graph_diff_summary}}
- Trace diff:
  {{trace_diff_summary}}
- Policy constraints:
  {{policy_constraints}}

【任务】
1. 判断失败候选相对 elite 的主要退化原因；
2. 区分"结构问题""参数问题""模板槽位问题""不可归因问题"；
3. 仅提出一个最小局部改动建议，优先选择 slot filling；
4. 输出建议对应的模板 ID、目标槽位和值；
5. 如果没有低风险建议，明确返回 NO_SAFE_PATCH。

【输出格式】
- diagnosis_type:
- root_cause:
- recommended_template:
- target_slot:
- proposed_slot_values:
- expected_effect:
- risk_level:
- validation_focus:
```

### 9.11.2 为什么这个模板有效

| 设计点 | 作用 |
| --- | --- |
| 强制比较 `elite` 与 `failed` | 避免脱离基线的空泛建议 |
| 强制只提一个局部改动 | 控制变更半径 |
| 优先 slot filling | 与模板库和治理链保持一致 |
| 提供 `NO_SAFE_PATCH` 出口 | 防止模型为了回答而乱提建议 |

## 9.12 模板版本管理

### 9.12.1 版本兼容性矩阵

```python
class TemplateVersionManager:
    """模板版本管理器。"""

    def get_compatible_version(
        self,
        template_id: str,
        required_version: str,
    ) -> str:
        """获取与指定版本兼容的最新模板版本。"""
        all_versions = self.registry.get_versions(template_id)
        compatible = [
            v for v in all_versions
            if self._is_compatible(v, required_version)
        ]
        return max(compatible, key=lambda v: parse_version(v))

    def _is_compatible(self, version_a: str, version_b: str) -> bool:
        """检查两个版本的接口是否兼容。"""
        # 主版本号相同即兼容（语义化版本）
        major_a = version_a.split(".")[0]
        major_b = version_b.split(".")[0]
        return major_a == major_b
```

### 9.12.2 版本升级迁移

当模板升级时，自动提供迁移适配器：

```python
class TemplateMigration:
    """模板版本迁移。"""

    async def migrate_config(
        self,
        old_config: XMLConfig,
        old_version: str,
        new_version: str,
    ) -> XMLConfig:
        """将使用旧版本模板的配置迁移到新版本。"""
        adapter_cls = self.migration_registry.get(
            template_id=old_config.template_id,
            from_version=old_version,
            to_version=new_version
        )
        if adapter_cls is None:
            # 无迁移适配器：尝试直接兼容
            if self._is_interface_compatible(old_version, new_version):
                return old_config.update_version(new_version)
            raise MigrationNotAvailable(
                f"无可用的迁移适配器: {old_version} -> {new_version}"
            )

        adapter = adapter_cls()
        return await adapter.migrate(old_config)
```

## 9.13 模板实例的治理接口

模板实例化后，不应绕过治理层。建议每个模板实例在 manifest 中保留以下治理元数据：

| 字段 | 用途 |
| --- | --- |
| `template_id` | 标识来源模板 |
| `instantiation_id` | 标识本次实例化 |
| `risk_level` | 给 Policy 做初筛 |
| `slot_diff` | 记录与模板默认值的差异 |
| `validation_profile` | 指定必须执行的验证项 |
| `rollback_hint` | 指定失败后的回滚目标 |

这样，Policy / Governance 可以针对模板实例做更细粒度的判断，而不是只看最终代码文本。

## 9.14 推荐的落地顺序

| 优先级 | 先做什么 | 为什么 |
| --- | --- | --- |
| P0 | 冻结模板元模型与目录规范 | 先把模板对象定义清楚 |
| P0 | 建立 6 步代码生成管线 | 让模板真正进入系统闭环 |
| P1 | 实现 `evaluation`、`memory`、`optimizer` 三类基础模板 | 覆盖最关键的状态、评分、提议路径 |
| P1 | 实现最小可行 Proposer | 让模板实例化真正可被驱动 |
| P2 | 接入反事实诊断与失败缓存 | 提高样本效率 |
| P2 | 扩展到 `restricted_code` 模板 | 在治理链成熟后再放宽自由度 |

## 9.15 小结

组件模板库的作用，不是替代组件 SDK，而是把"可变部分"从完整实现中剥离出来，变成一套**可约束、可生成、可验证、可回滚**的模板化资产。

因此，本章的核心结论是：

- **模板库是 Optimizer 的受限动作空间；**
- **slot filling 是默认生成模式，自由形式生成只作为最后手段；**
- **模板实例化必须走 6-step code generation pipeline，并进入 `staged lifecycle`；**
- **最小可行 Proposer 应围绕日志诊断、差异分析与局部 patch 构建；**
- **反事实诊断提示模板是连接历史证据与模板生成的关键接口。**
