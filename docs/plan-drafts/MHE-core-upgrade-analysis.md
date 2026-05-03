# MHE Core 升级分析：从图运行时到组装选择环境

> 基于《Harness 设计原则：组装理论和抽象谬误-优化版》对照 MHE core 现状的完整分析。
> 综合两轮独立 agent 审查，合并为单一可执行升级路线。

---

## 一、总体判断

MHE core 已经具备"候选图 → 验证 → 安全门 → 提交 → 审计"的成熟闭环，拥有版本图、生命周期追踪、Merkle 锚定审计日志、安全管线、热重载和优化器等子系统。但它更像一个**图运行时/组件注册器**，还不是设计文档所说的"带物理记忆的选择环境"或"诚实的制图工坊"。

升级的核心不是重写 core，而是把**谱系（lineage）、复用（copy count）、实例化边界（simulation/instantiation boundary）**升格为一等模型。

---

## 二、现有对齐情况

MHE 已经具备的基础设施远超大多数 harness 框架：

| 设计原则 | 已有 MHE 基础设施 | 完备度 |
|---|---|---|
| 物理记忆（6.1） | `ProvGraph`、`AuditLog`（Merkle 锚定，持久化至 JSONL 磁盘文件）、`ArtifactSnapshotStore`、`SessionStore` | 高 |
| 递归复用（6.2） | `resolve_boot_order()` 通过 Kahn 拓扑排序解析依赖 DAG（`sdk/dependency.py`） | 中 |
| 拷贝数信任（6.3） | 无 | 无 |
| 选择压（6.4） | `SafetyPipeline` 含沙箱验证、AB 影子测试、策略否决门、提交后自动回滚 | 中 |
| 反随机涌现（6.5） | 无 | 无 |
| 显式制图者（6.6） | 无 | 无 |
| 模拟-实例化隔离（6.7） | 无（candidate/active 不等同于此语义） | 无 |
| 因果闭环（6.8） | `ExecutionLifecycleService` 含 SUBMITTED/RUNNING/COMPLETED/FAILED/CANCELLED 事件 | 中 |
| 转导透明（6.9） | 无 | 无 |
| 机制确定性（6.10） | Graph 版本管理、严格的生命周期转换（`LifecycleTracker`） | 中 |
| 反涌现谦逊（6.11） | 无 | 无 |
| 物理主义检验门（6.12） | `ExecutionEvidenceRecorder` 纪录工件和验证结果 | 中 |

**关键发现**：MHE 在"记录发生了什么"方面很强，但在"判断发生的事有多复杂、是否经过可靠复用路径、是模拟还是真实执行"方面存在系统盲区。

---

## 三、关键差距详解

### 3.1 组装层差距

#### 3.1.1 无组件拷贝计数

`ComponentRegistry`（`src/metaharness/sdk/registry.py:29`）是一个 `dict[str, RegisteredComponent]`，每个组件 ID 唯一存在。系统中没有任何地方记录组件被实例化、调用、或组合进高阶工作流的次数。无法回答"这个组件被复用过多少次？"

**影响原则**：6.2（递归复用）、6.3（拷贝数信任）、6.5（反随机涌现）

#### 3.1.2 依赖 DAG 不持久化

依赖图在 `sdk/dependency.py` 中被 Kahn 算法解析后仅在引导期间使用，引导完成后即丢弃。`GraphVersionStore` 虽有版本管理和候选记录的持久化能力，但不存储依赖 DAG 结构本身，因此不可查询组件间依赖拓扑，不可跨版本比较。

**影响原则**：6.1（物理记忆）、6.2（递归复用）、7.6（跨环境组装一致性）

#### 3.1.3 无组装指数

从基础单元到目标产物的最短依赖路径长度从未被计算或存储。组件不携带其"因果历史深度"的元数据。

**影响原则**：6.5（反随机涌现）、7.2（组装指数）

#### 3.1.4 无跨版本组件谱系

`provenance/` 子系统的出处跟踪适用于工件（run_plan → run_artifact → validation → evidence），但不适用于组件本身的演化。没有"组件 X v2 由图版本 5 中的组件 X v1 派生出"的概念。

**影响原则**：6.1（物理记忆）、6.2（递归复用）

#### 3.1.5 无选择压机制

组件只增不减。`LifecycleTracker`（`src/metaharness/core/lifecycle_tracker.py`）定义了严格阶段转换（DISCOVERED → VALIDATED_STATIC → ASSEMBLED → VALIDATED_DYNAMIC → ACTIVATED → COMMITTED，加 FAILED 和 SUSPENDED 共 8 个状态），但只存在于内存中，不持久化为会话事件，也不包含 EXPLORATORY / INFRASTRUCTURE / DEPRECATED / GRAVEYARD 等长周期演化状态。

**影响原则**：6.4（选择压原则）

#### 3.1.6 无玻尔兹曼大脑检测

高组装指数、低拷贝数、无谱系的产物（"外观复杂但无可靠制造历史"）不会被标记或拦截。

**影响原则**：6.5（反随机涌现原则）

### 3.2 实例化层差距

#### 3.2.1 无模拟-实例化边界

所有 staged → committed 转换是统一的。没有区分"agent 内部规划了 X"和"X 已在真实世界中执行"。`GraphSnapshot`（`src/metaharness/core/models.py:126`）仅含节点和边，不携带执行模式语义。

**影响原则**：6.7（模拟-实例化隔离）、6.8（因果闭环）

#### 3.2.2 无转导透明度

原始物理输入如何变成符号、符号如何变成动作的过程没有记录。没有"输入从何而来、谁赋义、通过什么映射规则"的可审计链条。

**影响原则**：6.6（显式制图者）、6.9（转导透明）

#### 3.2.3 无声明-行动对账

无法查询"agent 声称执行了某操作 → 外部日志是否确认该操作确实发生？"

**影响原则**：6.7（模拟-实例化隔离）、6.12（物理主义检验门）

#### 3.2.4 因果闭环不完整

`ExecutionEvidenceRecorder`（`src/metaharness/core/execution.py:273`）记录执行工件，但执行结果未系统性地链接回触发决策。反馈回来了，但因果链的"谁决定 → 谁执行 → 谁验证 → 结果如何影响下一轮"没有完整记录。

**影响原则**：6.8（因果闭环）

### 3.3 量化框架差距

设计文档第 7 节定义的 12 项量化指标（组件复用率、组装指数、谱系完整率、生成不可能性指数、选择压强、跨环境一致性、制图者显式度、实例化隔离健全度、因果闭环率、转导透明度、语义漂移指数、物理主义通过率）**无一被计算或暴露**。可观测性基础设施（`MetricsRegistry`，含计数器、仪表、直方图及 `Histogram.summary()` 基础统计计算）已就绪，缺少的是面向组装理论的计算逻辑。

---

## 四、升级路线

### Phase 1：组装账本 + 拷贝计数（最小闭环）

新增 `AssemblyLedger` 服务，独立于 `ComponentRegistry`，记录：

```
AssemblyRecord:
  - component_id / graph_id / template_id
  - parent_ids: list[str]           # 父组件、父图、父模板
  - generation_context: dict        # 生成时的图版本、候选 ID、变异来源
  - validation_results: list[str]   # 验证记录引用
  - created_at_graph_version: int
```

在 `ComponentRegistry` 旁增加 `CopyCountIndex`：

```
CopyCountIndex:
  - call_count: int                 # 被调用次数
  - dependency_count: int           # 被其他组件依赖次数
  - cross_graph_reuse_count: int    # 跨图复用次数
  - critical_path_dependency_count: int  # 关键路径依赖数
```

**埋点位置**：
- `execute_plan()` 每次调用 → `call_count += 1`
- `resolve_boot_order()` 构建 DAG 时 → `dependency_count` 写入
- `commit_graph()` 每次提交 → 记录 `AssemblyRecord`，更新 `cross_graph_reuse_count`

**为什么放 Phase 1**：不改 executor 合约，不破坏现有扩展，但能立即支撑 7.1-7.5 的大部分指标计算。

### Phase 2：持久化 DAG + 组装指数

1. 在 `GraphSnapshot` 中增加 `dep_graph: dict[str, set[str]]` 字段，由 `resolve_boot_order()` 填充，`commit()` 时写入 `GraphVersionStore`
2. 计算每个组件的组装指数 AI = 从基础单元到该组件的最短依赖路径长度
3. 计算谱系完整率 = 可回溯父组件数 / 理论应有父组件数
4. 支持跨图版本 DAG 比较（`|AI_env1 - AI_env2| / AI_env1`）

**关键文件**：`src/metaharness/core/models.py`（GraphSnapshot 扩展）、`src/metaharness/sdk/dependency.py`（持久化输出）

### Phase 3：模拟-实例化边界 + 执行网关

为所有执行事件引入显式的 `ExecutionMode`：

```python
class ExecutionMode(str, Enum):
    SIMULATED = "simulated"            # agent 内部推理、规划、预测
    DRY_RUN = "dry_run"               # 非破坏性试运行
    STAGED = "staged"                 # 已暂存但未生效
    INSTANTIATED = "instantiated"     # 真实副作用已发生
    EXTERNALLY_VERIFIED = "externally_verified"  # 外部日志已确认
```

构建 `InstantiationGateway`，复用现有 `ExecutionEvidenceRecorder`：

- agent 的内部计划默认标记为 SIMULATED
- 只有通过执行网关的动作才标记为 INSTANTIATED
- 每个 INSTANTIATED 动作必须有外部日志或回执
- 执行结果回写 `AssemblyLedger`，闭合因果链
- 声称 INSTANTIATED 但无外部证据 → 自动降级为 DRY_RUN，触发告警

**关键文件**：`src/metaharness/core/execution.py`（ExecutionEvidenceRecorder 扩展）、`src/metaharness/core/boot.py`（commit_graph 中注入执行模式）

### Phase 4：选择压门 + 组件生命周期

扩展 `LifecycleTracker` 的生命周期状态：

```
EXPLORATORY → ACTIVE → INFRASTRUCTURE ⇄ DEPRECATED → GRAVEYARD
```

在 `SafetyPipeline.evaluate_graph_promotion()`（`src/metaharness/safety/pipeline.py:96`）增加组装健康门：

```python
class AssemblyHealthGate:
    """Reject promotions with Boltzmann Brain characteristics."""
    
    def evaluate(self, promotion: PromotionContext) -> GateResult:
        ai = compute_assembly_index(promotion.product)
        c = compute_copy_count(promotion.product)
        lineage = query_lineage(promotion.product)
        
        if ai > THRESHOLD_HIGH and c < THRESHOLD_LOW and not lineage:
            return GateResult(decision=REJECT, reason="Boltzmann Brain detected")
        if c == 0 and promotion.product on critical_path:
            return GateResult(decision=DEFER, reason="zero-copy critical dependency")
        return GateResult(decision=ALLOW)
```

自动晋升/降级规则：
- 拷贝数超阈值 + 跨 N 个图版本存活 → EXPLORATORY → INFRASTRUCTURE
- 连续 M 个版本未被引用 → ACTIVE → DEPRECATED
- 已弃用超过 K 个周期 → DEPRECATED → GRAVEYARD

### Phase 5：量化仪表盘

基于 `MetricsRegistry` 暴露 `mhe metrics` CLI 子命令和 `AssemblyDashboard` 服务：

```text
┌────────────────────────────────────────────┐
│ Harness Assembly & Instantiation Dashboard │
├────────────────────────────────────────────┤
│ 基础组件池大小:              1,240          │
│ 平均组件拷贝数:              47.3           │
│ 最高组装指数产物:            AI = 19        │
│ 高 AI 产物子组件平均拷贝数:  312            │
│ 谱系完整率:                  94.1%          │
│ 历史折叠度:                  91.7%          │
│ 本周随机涌现拦截:            3              │
│ 选择压强度:                  0.78           │
│ 制图者显式度:                96.4%          │
│ 行动声明对账率:              98.2%          │
│ 因果闭环率:                  87.5%          │
│ 转导透明度:                  92.0%          │
│ 语义漂移告警:                1              │
└────────────────────────────────────────────┘
```

---

## 五、架构变更总结

```
当前 MHE Core                      升级后 MHE Core
─────────────────────────────      ────────────────────────────────
ComponentRegistry                  ComponentRegistry
  (dict[id, component])               + CopyCountIndex
                                      + AssemblyLedger
                                  
ConnectionEngine                   ConnectionEngine
  (stage → validate → commit)         + ExecutionMode tag on all events
                                  
boot.py / HarnessRuntime           boot.py / HarnessRuntime
  commit_graph()                      commit_graph()
    → stage → validate → commit         → AssemblyLedger.record()
                                        → InstantiationGateway.gate()
                                        → AssemblyHealthGate.evaluate()
                                  
LifecycleTracker                   LifecycleTracker
  (runtime-only, 8 states)            (persisted, 5 long-cycle states)
                                      + auto-promotion/demotion rules
                                  
SafetyPipeline                     SafetyPipeline
  (sandbox, AB shadow, policy veto,  + AssemblyHealthGate
   post-commit auto-rollback)
                                  
执行层                              执行层
  ExecutionLifecycleService           + ExecutionMode on every event
  ExecutionEvidenceRecorder           → InstantiationGateway (reuses Recorder)
                                  
无                                   AssemblyDashboard
                                      mhe metrics CLI
```

---

## 六、迁移兼容性

所有变更对现有扩展（`metaharness_ext/*`）向后兼容：

- `AssemblyLedger` 是新增服务，不在现有 executor 合约中
- `CopyCountIndex` 的埋点位于 core 调度层，不修改扩展接口
- `ExecutionMode` 默认值为 `INSTANTIATED`，保持现有行为不变
- `AssemblyHealthGate` 初期以 WARN 模式运行，不阻塞现有推广流程

Extension executor 无需任何修改即可从升级中受益（其调用自动被计数和谱系追踪覆盖）。

---

## 七、与设计文档的对应关系

| 文档原则 | 覆盖 Phase | 实现方式 |
|---|---|---|
| 6.1 物理记忆 | Phase 1, 2 | AssemblyLedger + 持久化 DAG |
| 6.2 递归复用 | Phase 1, 2 | CopyCountIndex + 组装指数 |
| 6.3 拷贝数信任 | Phase 1 | CopyCountIndex 阈值 |
| 6.4 选择压 | Phase 4 | 组件生命周期 + 组装健康门 |
| 6.5 反随机涌现 | Phase 4 | 玻尔兹曼大脑检测门 |
| 6.6 显式制图者 | Phase 3 | 执行模式 + 转导记录 |
| 6.7 模拟-实例化隔离 | Phase 3 | ExecutionMode 枚举 + InstantiationGateway |
| 6.8 因果闭环 | Phase 3 | 执行结果回写 AssemblyLedger |
| 6.9 转导透明 | Phase 3 | I/O 映射记录 |
| 6.10 机制确定性 | Phase 2 | 持久化 DAG + 跨版本比较 |
| 6.11 反涌现谦逊 | Phase 4 | 涌现幻觉拦截 |
| 6.12 物理主义检验门 | Phase 3 | 声明-行动对账 |

---

## 八、推荐启动顺序

**第一优先级**（1-2 周，不破坏现有合约）：
1. `AssemblyLedger` — 新服务，记录组件/图/模板的父组件、版本、生成上下文、验证结果
2. `CopyCountIndex` — 在 `execute_plan()`、`commit_graph()` 中埋点
3. `AssemblyHealthGate` — 初期 WARN 模式，接入 `SafetyPipeline`

**第二优先级**（2-4 周）：
4. 持久化 DAG + 组装指数计算
5. `ExecutionMode` 枚举 + `InstantiationGateway`
6. 组件生命周期长周期状态（INFRASTRUCTURE / DEPRECATED / GRAVEYARD）

**第三优先级**（4-6 周）：
7. `AssemblyDashboard` + `mhe metrics` CLI
8. 自动晋升/降级规则
9. 12 项量化指标的全量计算和暴露

这样 MHE 就能从"可验证图运行时"升级为文档所说的"带物理记忆的选择环境 + 诚实的制图工坊"——既让复杂能力通过递归复用和选择压演化出来，又确保符号行为不越界冒充真实执行。
