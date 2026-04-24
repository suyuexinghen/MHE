# 05. 模板库与自增长机制

## 5.1 为什么模板库与自增长必须一起设计

在 `AI4PDE Agent` 中，模板库与自增长不是两个独立功能，而是一体两面：

- **模板库** 决定系统能在多大范围内安全复用
- **自增长机制** 决定系统如何在约束内持续改进

如果只有自增长而没有模板边界，系统容易失控；如果只有模板而没有自增长，系统会停留在静态工作流。

因此建议采用：

```text
模板库约束搜索空间
  +
自增长在模板和图版本边界内提出改进
```

---

## 5.2 模板库的定位

`PDETemplate Library` 不是“提示词仓库”，也不是“脚本集合”，而是：

- 可实例化的 workflow skeleton
- 带 slot / contract / validator 要求的结构化资产
- 可被 Planner、Optimizer、Connection Engine 共同使用的正式对象

### 模板库至少承担三种作用

1. **减少从零规划的频率**
2. **把成功路径收敛为可复用结构**
3. **把自增长限制在受控变体空间内**

---

## 5.3 模板层级

建议将 AI4PDE 模板分为四类：

## 5.3.1 Workflow Templates

表示端到端科研工作流骨架，例如：

- forward solid mechanics
- inverse parameter identification
- operator surrogate evaluation
- PINO hybrid correction

## 5.3.2 Validation Templates

表示标准验证闭环，例如：

- residual + BC/IC + baseline comparison
- energy consistency + constitutive sanity checks
- uncertainty + reproducibility package

## 5.3.3 Failure Triage Templates

表示失败分析与恢复路径，例如：

- solver divergence triage
- geometry mismatch triage
- candidate graph rollback triage

## 5.3.4 Reporting Templates

表示报告与证据打包结构，例如：

- experiment summary + metrics + provenance
- benchmark comparison report
- candidate-vs-active graph comparison report

---

## 5.4 建议的初始模板目录

本节是 **AI4PDE 模板 catalog 的唯一权威来源**。`01-architecture-spec.md` 只引用本节，不再重复维护模板清单。

建议初始模板至少包括：

- `ForwardSolidMechanicsTemplate`
- `ForwardFluidMechanicsTemplate`：流体力学前向求解，Navier-Stokes 方程族
- `InverseParameterIdentificationTemplate`
- `OperatorSurrogateTemplate`
- `PINOHybridCorrectionTemplate`
- `TopologyOptimizationTemplate`
- `MultiPhysicsCouplingTemplate`：多物理场耦合（流固耦合、热力耦合）
- `DataAssimilationTemplate`：稀疏观测数据融合，PINO 的"近似方程+数据校正"模式
- `UncertaintyQuantificationTemplate`：不确定性量化与置信区间估计
- `ValidationBundleTemplate`：通用验证打包模板，包含以下命名变体：
  - `ConvergenceValidation`：收敛性验证
  - `ConservationValidation`：守恒律验证
  - `BoundaryIntegrityValidation`：边界完整性验证
  - `BenchmarkComparisonValidation`：基准对比验证
- `FailureTriageTemplate`
- `CounterfactualComparisonTemplate`
- `EvidencePackagingTemplate`

> **注意**：本目录就是 AI4PDE 的 authoritative template catalog。`01-architecture-spec.md` 不再维护独立模板列表，只引用本目录。

---

## 5.5 模板结构

每个模板建议至少声明：

```text
PDETemplate
  - template_id
  - name
  - task_family
  - supported_slots
  - fixed_contracts
  - variable_params
  - required_validators
  - risk_level
  - reproducibility_requirements
  - migration_hooks
  - benchmark_profile
  - version
  - status
```

### 关键字段说明

#### `supported_slots`

模板允许绑定的槽位。**canonical slot 名称以 [01-architecture-spec.md](01-architecture-spec.md) 第 7.6.1 节为准**；本节只定义模板通常如何使用这些 slot。

| Slot | 绑定策略 | 模板中是否常用 | 说明 |
|---|---|---|---|
| `ProblemFormulator` | worker-bound | ✅ | 前向/反问题模板通常需要自定义形式化逻辑 |
| `MethodRouter` | worker-bound | ✅ | 核心路由 slot |
| `KnowledgeAdapter` | platform-managed | ⬜ | 通常由平台默认提供 |
| `GeometryAdapter` | worker-bound | ✅ | 几何预处理 |
| `SolverExecutor` | worker-bound | ✅ | 核心求解 slot |
| `ReferenceSolver` | worker-bound | ✅ | 高保真模板需要参考求解 |
| `PhysicsValidator` | worker-bound | ✅ | 核心验证 slot |
| `EvidenceManager` | worker-bound | ⬜ | 报告 / 证据模板通常会绑定 |
| `ObservabilityHub` | platform-managed | ❌ | 平台基础设施，模板不绑定 |
| `AssetMemory` | platform-managed | ❌ | 平台基础设施，模板不绑定 |
| `PolicyGuard` | protected | ❌ | 受保护 slot，模板不绑定 |

#### Role-to-Slot 映射（模板视角）

| Worker Role | 默认绑定 Slot | 模板含义 |
|---|---|---|
| `ProblemFormulatorWorker` | `ProblemFormulator` | 决定任务形式化骨架 |
| `MethodRouterWorker` | `MethodRouter` | 决定方法选择与回退路径 |
| `GeometryWorker` | `GeometryAdapter` | 决定几何/网格处理骨架 |
| `SolverWorker` | `SolverExecutor` | 决定主求解骨架 |
| `ReferenceSolverWorker` | `ReferenceSolver` | 决定 baseline / reference 分支 |
| `PhysicsValidatorWorker` | `PhysicsValidator` | 决定验证闭环骨架 |
| `ReportWorker` | `EvidenceManager` | 决定证据打包与报告交付 |

`PDECoordinator`、`KnowledgeAdapter`、`ObservabilityHub`、`AssetMemory`、`PolicyGuard` 不属于模板直接绑定的 worker-to-slot 范围：前者是管理层角色，后四者是平台管理或受保护能力。

#### `fixed_contracts`

不允许任意修改的契约，例如：

- 输入必须包含 `physics_spec`
- 交付必须包含 `ScientificEvidenceBundle`
- baseline comparison 不可缺失

#### `variable_params`

模板允许搜索和自增长的参数空间，例如：

- loss weights
- routing thresholds
- collocation strategy
- benchmark subset

> slot 的完整定义与 Role-to-Slot 映射见 [01-architecture-spec.md](01-architecture-spec.md) 第 7.6.1 节。

---

## 5.6 模板实例化流程

模板实例化建议遵循：

```text
任务输入
  → Planner 检索相似模板
    → 选择模板
      → 绑定 slots
        → 生成 candidate workflow graph
          → 运行验证
            → 作为 active / candidate 图执行
```

#### 模板未命中时的回退路径

若模板库无匹配结果：

1. MethodRouter 回退至自由规划模式，使用默认风险约束
2. Coordinator 构建基础任务图（`template_id: null`）
3. 若 Meta Layer Level 4（受限合成）已启用，可生成候选图供审查
4. Planner 将任务标记为"非模板化"，后续 Optimizer 可将成功路径提升为新模板

此回退路径是模板库与自增长机制的关键衔接点：反复出现的非模板化成功路径应被自动提名为新模板候选。

### 实例化后的产物

- `template_id`
- `instantiation_id`
- `slot_bindings`
- `graph_version_id`
- `parameter_overrides`
- `validation_profile`

---

## 5.7 模板状态流转

建议模板采用以下状态：

- `draft`
- `candidate`
- `stable`
- `retired`

### 典型流转

```text
draft
  → candidate
    → benchmark validation
      → stable
        → degraded / obsolete
          → retired
```

### 退役条件

- 连续 benchmark 退化
- 无法满足 reproducibility threshold
- 被更优模板稳定替代
- 与新的 protected invariant 冲突

#### 与 WorkflowGraphVersion 状态的对应关系

| 模板状态 | 对应图版本状态 | 说明 |
|---|---|---|
| `draft` | — | 模板尚未实例化，无图版本 |
| `candidate` | `candidate` / `shadow` | 实例化后进入候选/影子验证 |
| `stable` | `stable` / `active` | 通过验证，可正式使用 |
| `degraded` | — | 性能下降但仍可参考 |
| `retired` | `rolled_back` | 已废弃，不可实例化 |

模板不需要 `shadow` 和 `rolled_back` 状态，因为这些是图版本运行期的瞬时状态，而模板是持久化资产。

---

## 5.8 自增长的基本原则

AI4PDE 的自增长不能等价于“自由自修改”。

建议遵循以下原则：

- **先小后大**：先参数，再图，再模板，再受限合成
- **先验证后激活**：proposal 不能直接改 live runtime
- **先记录失败再继续探索**：死胡同要进入 memory
- **先模板化复用，再考虑重新发明**
- **永不绕过治理层**

---

## 5.9 自增长的四级阶梯

## 5.9.1 一级：参数优化

最优先，也是最低风险。

优化对象包括：

- loss 权重
- collocation 采样策略
- optimizer 参数
- stopping criteria
- routing thresholds
- batch 大小

特点：

- 不改变工作流结构
- 验证成本低
- 容易回滚

---

## 5.9.2 二级：连接 / 图重排

在现有模板或 graph skeleton 内部调整连接关系，例如：

- 在 solver 后插入 uncertainty branch
- 在 baseline 前增加 geometry sanity check
- 在 report 前增加 counterfactual comparison node

特点：

- 会影响执行图
- 必须生成 candidate graph
- 需要 observation window

---

## 5.9.3 三级：模板实例化 / 替换

典型操作：

- 用 `PINOHybridCorrectionTemplate` 替换 `OperatorSurrogateTemplate`
- 用更严格的 `ValidationBundleTemplate` 替换旧验证骨架

特点：

- 影响较大
- 但仍在模板约束内
- 非常适合“安全演化”

---

## 5.9.4 四级：受限合成

只有在前三层都无法满足需求时，才允许：

- 在模板边界内生成新的小型节点逻辑
- 生成新的局部 triage / adapter / validator 片段

前提：

- 必须受模板 / contract / policy 约束
- 必须经过 candidate validation
- 不得直接替换 protected slots

#### 升级触发条件

| 升级路径 | 触发条件 | 示例 |
|---|---|---|
| L1 → L2 | 连续 N 次（默认 N=5）L1 提案未产生 Pareto 改进 | 调优 loss 权重 5 轮后残差未降低 |
| L2 → L3 | 搜索预算内（默认 max_proposals=20）未找到有效的拓扑变更 | 所有图重排均未改善多目标评分 |
| L3 → L4 | 观察到的失败模式不在任何已有模板覆盖范围内 | 新型数值不稳定，模板库无对应处理 |
| L4 → ESCALATE | 受限合成提案被 Policy Engine 连续否决 3 次 | 合成逻辑超出安全边界 |

每级设有最大尝试次数（默认 L1: 10, L2: 20, L3: 5, L4: 3），超出后自动 ESCALATE 至人工审查。

---

## 5.10 自增长触发信号

建议至少监听以下信号：

- 同类任务反复 `PARTIAL`
- 某 solver 成本持续过高
- 某模板命中率高但验证通过率低
- 某 graph family 高频回滚
- baseline 与 learned solver 差距持续扩大
- dead-end 路径重复出现
- benchmark 指标进入平台期

这些信号可以进入 `Optimizer / Proposer` 形成 mutation proposal。

---

## 5.11 Proposal 生成与评估

### Proposal 生成来源

- 历史成功模板
- failure patterns
- dead-end memory
- benchmark metrics
- graph version lineage
- worker 失败报告

### Proposal 评估维度

- scientific accuracy
- residual quality
- latency
- cost
- robustness
- reproducibility
- governance compatibility

最终产物是：

- `MutationProposal`
- `CandidateGraph`
- `EvaluationSnapshot`

---

## 5.12 Failure Memory 与 Dead-End Memory

## 5.12.1 Failure Memory

记录“运行失败”的可复用知识，例如：

- PINN 在某类 BC 配置下经常发散
- 某几何预处理路径易导致 baseline mismatch
- 某 operator 模型在特定数据分布上失真

作用：

- 指导 Planner 避免已知坏选择
- 指导 Optimizer 做局部修补

## 5.12.2 Dead-End Memory

记录“演化失败”的坏提案族，例如：

- 某类 graph rewire 总被 policy 否决
- 某模板替换路径在 observation window 中必退化
- 某 validator 热加载组合无法安全迁移

作用：

- 避免 Meta Layer 重复探索已知坏变更路径

#### 失败记忆的时效性

- `FailurePattern` 的 `hit_count` 应配合 `last_seen_at` 字段使用：超过 90 天未被再次触发的 pattern 降级为 `stale`
- `DeadEndRecord` 在相关模板被大幅升级（`template_id` 版本号变更）后可标记为 `revisit_eligible`
- 已否决的变更族在系统发生 major version 升级后可由人工审查重新评估

> 失败模式的治理分类见 [04-governance-and-observability.md](04-governance-and-observability.md) 第 4.13 节。

---

## 5.13 模板晋升策略

一个 workflow 不应因为“刚好成功一次”就变成 stable template。

建议晋升条件：

- 在多个 benchmark / task family 上表现稳定
- 满足 reproducibility threshold
- 有完整 evidence bundle
- 无 protected invariant 违规
- observation window 表现稳定

满足后：

```text
successful graph family
  → promote to candidate template
    → benchmark validation
      → stable template
```

---

## 5.14 模板与图版本的关系

模板不是图版本本身，但图版本通常来自模板实例化。

关系如下：

```text
PDETemplate
  → instantiate
    → WorkflowGraphVersion(candidate)
      → validate
        → activate / rollback
          → if repeatedly successful
            → template promotion or update
```

因此模板库与 graph version store 应双向关联：

- template 能追溯自己生成过哪些 graph versions
- graph version 能追溯自己源自哪个 template

---

## 5.15 对 Aeloon 的实现启发

如果在 Aeloon 中实现，建议把模板库与自增长拆成独立模块：

- `templates.py`
- `template_registry.py`
- `optimizer.py`
- `evaluation.py`
- `dead_end_memory.py`
- `graph_versions.py`
- `mutation_manager.py`

而不是把“优化逻辑”混进 `Planner` 或 `Orchestrator` 中。

---

## 5.16 最后总结

AI4PDE 的模板库与自增长设计应坚持：

- 模板是结构化资产，不是脚本片段
- 自增长是 proposal-based，不是 live self-rewrite
- 成功路径要模板化，失败路径要记忆化
- 小改动优先，大变更后置
- 所有变更都必须经过验证、观察窗口与回滚准备

只有这样，AI4PDE Agent 才能做到：

- 越用越强
- 但不会越长越乱
- 越积累越稳
- 而不是越自改越不可控
