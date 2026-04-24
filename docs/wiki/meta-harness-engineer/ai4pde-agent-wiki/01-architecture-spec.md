# 07. AI4PDE Team Runtime + Meta-Harness 架构规范

## 7.1 背景与目标

本文提出一个面向 `AI4PDE` 场景的增强型科学智能体架构：

- 在 **执行协作层** 借鉴 `agent-team` 的 team runtime 设计
- 在 **系统演化层** 借鉴 `Meta-Harness-Engineer (MHE)` 的 meta-harness 设计
- 将二者与现有 `science-agent` 的任务生命周期、能力层、验证闭环相结合

目标不是再造一个“会调 PDE 求解器的聊天 Agent”，而是构建一个：

- **有状态**：任务、成员、证据、检查点可持久化
- **可协作**：多个专业 worker 能围绕同一 PDE 任务协同工作
- **可治理**：高成本求解、工作流变更、自增长都受统一控制
- **可演化**：工作流和组件可通过候选图验证后安全升级
- **可追溯**：每个结论都绑定图版本、验证证据与溯源对象

---

## 7.2 设计命题

`AI4PDE` 不应被实现为单一的“大模型 + 工具调用器”，而应被实现为两个互补运行时的叠加：

1. **AI4PDE Team Runtime**
   - 负责一次具体科研任务中的多 worker 协作执行
   - 关注 team、task、mailbox、approval、idle、shutdown、recovery

2. **AI4PDE Meta-Harness**
   - 负责工作流图、组件图、模板与策略的安全演化
   - 关注 candidate graph、validation、promotion、rollback、template library、self-growth

可概括为：

```text
AI4PDE = Team Runtime（执行协作） + Meta-Harness（受控演化） + PDE Capability Fabric（科学能力）
```

---

## 7.3 总体架构

### 7.3.1 三层视图

```text
┌──────────────────────────────────────────────────────────────┐
│ Meta Layer: AI4PDE Meta-Harness                             │
│ - Optimizer / Proposer                                      │
│ - Policy Engine                                             │
│ - Evaluation Engine                                         │
│ - Connection Engine                                         │
│ - Template Library                                          │
│ - Mutation / Rollback Manager                               │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ Coordination Layer: AI4PDE Team Runtime                     │
│ - PDECoordinator                                             │
│ - Team Registry / Task List / Mailbox                        │
│ - Approval Center                                             │
│ - Worker Lifecycle Manager                                    │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ Runtime Layer: PDE Capability Fabric                         │
│ - Problem Formulator                                          │
│ - Method Router                                               │
│ - Geometry Adapter                                            │
│ - Solver Executors (PINN / DEM / Operator / PINO)            │
│ - Classical Solver Gateway                                    │
│ - Physics / Reference Validator                               │
│ - Evidence / Asset / Observability                            │
└──────────────────────────────────────────────────────────────┘
```

### 7.3.2 三层职责分工

- **Meta Layer**：决定系统“能否变、如何变、何时回滚”
- **Coordination Layer**：决定团队“谁做什么、如何同步、如何审批”
- **Runtime Layer**：决定单次科学任务”如何求解、如何验证、如何交付”

### 7.3.3 审批权责划分

两层审批机制各司其职，互不重叠：

| 审批层 | 管辖范围 | 典型对象 |
|---|---|---|
| **Coordination Layer** (Approval Center) | worker 行为审批 | 工具调用权限、预算消耗、HPC 作业提交、worker shutdown |
| **Meta Layer** (Policy Engine) | 系统结构变更审批 | 图版本切换、模板实例化、验证器修改、组件替换 |

**规则**：worker 发起的变更请求先经过 Coordination Layer 的 Approval Center，再由 Coordinator 代理上送 Meta Layer 的 Policy Engine。两层顺序通过，变更方可执行。

---

## 7.4 AI4PDE Team Runtime

> 完整运行流程与生命周期见 [02-runtime-flow.md](02-runtime-flow.md)。

## 7.4.1 为什么需要 Team Runtime

PDE 科学任务天然具有强分工特征：

- 问题形式化
- 方法选择
- 几何与边界预处理
- 求解执行
- 基线对比
- 物理验证
- 报告生成

若完全由单一 orchestrator 串行执行，容易出现：

- 上下文过载
- 长任务阻塞
- 难以复用专业 worker
- 审批与治理点分散
- 失败恢复粒度粗

因此建议引入 `team-scoped` 运行时。

---

## 7.4.2 角色与成员分离

与 `agent-team` 一样，需区分：

- **Role**：专业能力与人格
- **Member / Worker**：某次运行中的团队实例

典型角色：

- `PDECoordinator`
- `ProblemFormulatorWorker`
- `MethodRouterWorker`
- `GeometryWorker`
- `SolverWorker`
- `ReferenceSolverWorker`
- `PhysicsValidatorWorker`
- `ReportWorker`

同一角色可在一次运行中有多个实例，例如多个 `SolverWorker` 分别尝试 `PINN`、`PINO`、`FEM baseline`。

---

## 7.4.3 共享状态层

建议引入三个 team-scoped 共享状态：

### 第一层：Team Registry

保存：

- `teamName`
- `leadWorkerId`
- `members`
- `backend`
- `isActive`
- `worktreePath`（如需要）
- `allowedPaths`

作用：

- 团队注册表
- 成员发现
- worker 状态镜像

### 第二层：PDE Task List

保存：

- `taskId`
- `subject`
- `description`
- `status`
- `owner`
- `blockedBy`
- `blocks`
- `priority`
- `physicsDomain`
- `costLevel`
- `requiredEvidence`

作用：

- 共享工作队列
- 轻量依赖图
- PDE 子任务拆解承载层

### 第三层：Mailbox / Protocol Bus

保存：

- 普通协作消息
- `approval_request / response`
- `idle_notification`
- `failure_report`
- `shutdown_request / response`
- `candidate_change_notice`

作用：

- 异步控制面总线
- 跨 backend 协议统一层

---

## 7.4.4 协作协议

建议 AI4PDE team runtime 至少支持以下协议消息：

- `task_assignment`
- `idle_notification`
- `failure_report`
- `approval_request`
- `approval_response`
- `shutdown_request`
- `shutdown_response`
- `candidate_graph_request`
- `candidate_graph_result`

其中：

- 普通 worker 不直接改 live workflow
- 对高成本、结构性变化、治理规则变化，必须上送 coordinator / meta layer

---

## 7.4.5 中央审批中心

PDE 场景下的审批对象不只是“能否调用工具”，还包括：

- 是否允许发起高成本训练
- 是否允许提交 HPC 作业
- 是否允许切换 workflow graph
- 是否允许引入新模板实例
- 是否允许修改验证标准

因此 `PDECoordinator` 应作为：

- 用户唯一对话点
- 团队唯一审批桥
- 高风险操作唯一仲裁者

这与 `agent-team` 的 leader 模式一致，但粒度更细。

---

## 7.4.6 idle / recovery 语义

PDE 任务往往长航时且分阶段。

worker 不应“一次执行完就退出”，而应：

1. 完成当前 prompt / task
2. 标记 `idle`
3. 给 coordinator 发送 `idle_notification`
4. 保持可恢复、可复用、可唤醒状态

这样可以支持：

- solver worker 跑完一次基线后等待下一步
- validator worker 等待新证据到达后再工作
- report worker 在最终收尾阶段才被唤醒

---

## 7.5 AI4PDE Meta-Harness

## 7.5.1 为什么需要 Meta-Harness

仅有 team runtime，只能解决“多人协作执行”的问题，不能解决：

- workflow 如何安全升级
- 哪种 PDE 模板更优
- 怎样从失败中结构化学习
- 如何把经验提升为模板
- 怎样避免 live runtime 被直接污染

这些正是 MHE 的强项。

---

## 7.5.2 Meta Layer 的核心组件

### `Optimizer / Proposer`

职责：

- 基于观测数据提出改进建议
- 生成参数级、连接级、模板级 mutation proposal
- 不直接修改 active graph

### `Policy Engine`

职责：

- 审查 proposal 是否违反治理规则
- 对 proposal 做：
  - `allow`
  - `deny`
  - `allow_with_constraints`
  - `escalate`
  - `freeze_path`

### `Evaluation Engine`

职责：

- 多目标评价 candidate graph：
  - scientific accuracy
  - residual quality
  - reproducibility
  - latency
  - GPU / HPC cost
  - robustness

### `Connection Engine`

职责：

- 管理工作流图与组件图的版本
- 维护 candidate graph 与 active graph
- 负责图切换与回滚

### `Template Library`

职责：

- 提供 PDE 专用模板目录
- 限定变化空间
- 沉淀高价值科学工作流骨架

### `Mutation / Rollback Manager`

职责：

- 将 proposal 转化为可验证的 candidate change set
- 管理 observation window
- 执行 rollback

---

## 7.5.3 图版本化原则

AI4PDE 的求解工作流不应是“运行时直接改配置”，而应是：

```text
pending mutation
  → candidate graph
    → static validation
      → shadow / sandbox validation
        → policy approval
          → active graph cutover
            → observation window
              → stabilize or rollback
```

这意味着：

- live workflow 永远有稳定版本号
- 每次变更都可溯源
- 每次升级都保留 rollback target

---

## 7.5.4 PDE 专用模板库

AI4PDE 的**模板目录以 [05-template-library-and-self-growth.md](05-template-library-and-self-growth.md) 第 5.4 节为唯一权威来源**；本节只定义模板系统在架构层必须满足的元数据与约束，不重复维护模板清单。

因此，新增、删减或重命名模板时，应先更新 `05-template-library-and-self-growth.md` 的 catalog，再回看本节是否需要调整模板机制本身。

当前模板体系按四类组织：

- workflow templates
- validation templates
- failure triage templates
- reporting templates

每个模板应显式声明：

- `template_id`
- `supported_slots`
- `fixed_contracts`
- `variable_params`
- `required_validators`
- `risk_level`
- `reproducibility_requirements`
- `migration_hooks`

模板的意义不是”预制脚本”，而是”受控可实例化的科学 workflow skeleton”。

**模板与 MethodRouter 的优先级规则**：当模板处于激活状态时，MethodRouter 只能从模板的 `supported_methods` 中选择。无模板激活时，MethodRouter 拥有完全自由度。模板实例化时，路由决策已被模板骨架约束，Optimizer 只能在 `variable_params` 范围内调优。

---

## 7.5.5 自增长策略

> 自增长机制的详细定义与触发信号见 [05-template-library-and-self-growth.md](05-template-library-and-self-growth.md)。

建议 AI4PDE 遵循与 MHE 相同的增长梯度：

### 一级：参数优化

例如：

- loss 权重
- collocation 采样策略
- optimizer 参数
- stopping criteria
- routing 阈值

### 二级：连接 / 图重排

例如：

- 插入 reference validation 分支
- 在 PINO 前增加 operator warm start
- 在 solver 后增加 uncertainty estimation

### 三级：模板实例化

例如：

- 用 `PINOHybridCorrectionTemplate` 替代普通 `OperatorTemplate`

### 四级：受限合成

仅在前三层无法解决问题时，允许在模板约束下生成小范围新逻辑。

关键原则：

- 优先小改动
- 优先可验证改动
- 禁止无约束自重写

---

## 7.6 PDE Capability Fabric

## 7.6.1 运行时核心槽位

建议将 AI4PDE runtime 组织为以下 **canonical slots**：

| Slot | 绑定策略 | 说明 |
|---|---|---|
| `ProblemFormulator` | worker-bound | 问题形式化与 task normalization |
| `MethodRouter` | worker-bound | 方法选择与执行建议输出 |
| `KnowledgeAdapter` | platform-managed | 外部知识注入与检索适配 |
| `GeometryAdapter` | worker-bound | 几何与网格预处理 |
| `SolverExecutor` | worker-bound | 主求解执行入口 |
| `ReferenceSolver` | worker-bound | 基线 / 高保真参考求解 |
| `PhysicsValidator` | worker-bound | 物理一致性与科学正确性验证 |
| `EvidenceManager` | worker-bound | 证据打包、摘要与报告交付 |
| `ObservabilityHub` | platform-managed | 可观测性基础设施 |
| `AssetMemory` | platform-managed | 资产、失败模式与演化记忆 |
| `PolicyGuard` | protected | 治理与风险控制边界 |

每个槽位都是可替换组件，但必须遵守契约。

> 各 slot 的完整数据模型定义见 [03-data-models.md](03-data-models.md)。模板对 slot 的使用约束见 [05-template-library-and-self-growth.md](05-template-library-and-self-growth.md) 第 5.5 节。

#### Role-to-Slot 映射

| Worker Role | 绑定 Slot | 说明 |
|---|---|---|
| `PDECoordinator` | 无（平台管理层） | leader，不绑定求解 slot |
| `ProblemFormulatorWorker` | `ProblemFormulator` | 问题形式化 |
| `MethodRouterWorker` | `MethodRouter` | 方法选择 |
| `GeometryWorker` | `GeometryAdapter` | 几何预处理 |
| `SolverWorker` | `SolverExecutor` | 求解执行（可多实例） |
| `ReferenceSolverWorker` | `ReferenceSolver` | 基线参考求解 |
| `PhysicsValidatorWorker` | `PhysicsValidator` | 物理验证 |
| `ReportWorker` | `EvidenceManager` | 证据打包与报告生成 |

以下 slot 由平台直接管理，不绑定 worker role：
- `KnowledgeAdapter`：知识注入，由 Coordinator 按需调度
- `ObservabilityHub`：平台基础设施
- `AssetMemory`：平台基础设施
- `PolicyGuard`：平台基础设施（protected slot）

其中 `KnowledgeAdapter` 负责将外部知识源（文献库、结构化数据库、经验规则、方法模板）映射为统一查询接口，供 Planner 和 Validator 按阶段、按粒度调用。它不是 worker 角色，而是由 Coordinator 按需调度的平台级能力。

---

## 7.6.2 Solver Executor 分层

`SolverExecutor` 内建议继续细分：

- `PINNStrongExecutor`
- `DEMEnergyExecutor`
- `OperatorLearningExecutor`
- `PINOExecutor`
- `ClassicalHybridExecutor`

Method Router 只负责：

- 选择策略
- 输出执行建议

而不是把全部求解逻辑塞进一个总控类中。

---

## 7.6.3 Geometry / PDE / Data 的三元适配

建议将 PDE 输入形式标准化为：

- `physics_spec`
- `geometry_spec`
- `data_spec`

其中：

- `physics_spec`：PDE、材料参数、BC/IC、守恒约束
- `geometry_spec`：mesh / CAD / point cloud / SDF
- `data_spec`：simulation data / experiment data / sparse observation

这样 Method Router 与 Template Library 就可以围绕标准三元组做决策。

#### 三元规格示例

以"二维矩形域上的稳态热传导问题"为例：

```json
{
  "physics_spec": {
    "pde_type": "poisson",
    "equation": "-∇·(k∇u) = f",
    "parameters": {"k": 1.0, "f": 0.0},
    "bc": {"left": "u=100", "right": "u=0", "top": "du/dn=0", "bottom": "du/dn=0"},
    "ic": null,
    "conservation": ["energy"],
    "dimension": 2,
    "regime": "steady"
  },
  "geometry_spec": {
    "type": "mesh",
    "format": "msh",
    "source": "gmsh",
    "domain": {"x_range": [0, 1], "y_range": [0, 1]},
    "mesh_resolution": "medium"
  },
  "data_spec": {
    "type": "none",
    "observations": [],
    "reference_solver": "FEM_L2_projection",
    "sparse_observation_refs": []
  }
}
```

### 7.6.4 PDE 失败模式分类

以下为 AI4PDE 场景中常见的失败模式，模板库、Failure Patterns 库和 self-growth 提案器应覆盖这些类别：

| 失败类别 | 典型表现 | 对应回退策略 |
|---|---|---|
| **收敛失败** | 优化器发散、残差停滞不降、loss 震荡 | 调整 loss 权重、更换采样策略、切换至能量形式 |
| **边界违反** | BC/IC 残差超限、约束不满足 | 强化边界采样密度、切换 admissible function 构造方式 |
| **数值不稳定** | NaN/Inf、场值爆炸、负物理量 | 降低学习率、增加正则化、切换至更稳定的求解器族 |
| **参考发散** | 结果与 FEM/FVM 基线偏差超出容限 | 触发 SUBSTITUTE 换方法、或 REPLAN 重构任务图 |
| **预算耗尽** | GPU 时间 / Token 数 / Walltime 超限 | RETRY（降级配置）或 ESCALATE（请求追加预算） |
| **模式不匹配** | 迁移适配器无法桥接新旧 schema | 拒绝迁移、回滚至上一稳定图版本 |
| **验证器退化** | 修改后验证器漏检已知的坏结果 | 触发 Policy 保护、冻结该 slot、等待人工审查 |

每类失败应在 Asset Manager 中沉淀为结构化的 `FailurePattern` 对象。详见 [03-data-models.md](03-data-models.md) 第 3.7.2 节。

---

## 7.7 Scientific Governance

> 治理不变量、风险分级与可观测性的完整定义见 [04-governance-and-observability.md](04-governance-and-observability.md)。

## 7.7.1 为什么需要比普通 Agent 更强的治理

AI4PDE 的失败成本高于普通问答系统：

- GPU / HPC 成本高
- 长时间运行
- 结果易被误解为“科学结论”
- 自增长若失控会污染验证标准

因此必须引入显式治理不变量。

---

## 7.7.2 建议的核心不变量

建议至少定义以下不变量：

- **Provenance Required**：无溯源对象不得交付为正式结果
- **Rollback Required**：无 rollback target 不得切换 active graph
- **Budget Bound**：无预算许可不得发起高成本训练/求解
- **Validator Integrity**：验证标准不可在任务中途静默改变
- **Reference Integrity**：基线求解器输出不得被普通 worker 改写
- **Policy Protection**：`PolicyGuard`、`EvidenceManager`、`ObservabilityHub` 属于 protected slots
- **Reproducibility Threshold**：候选模板不满足最低复现阈值不得入库

---

## 7.7.3 风险分级

建议至少采用三档风险：

- `Green`
  - 文献检索
  - 参数分析
  - 低成本推理
- `Yellow`
  - 中等成本训练
  - 候选 workflow 评估
  - 大量 batch inference
- `Red`
  - 高成本 PDE 训练
  - HPC 提交
  - live graph cutover
  - validator / policy 相关变更

`Red` 级操作必须经过 coordinator + policy 双重批准。

---

## 7.8 Observability / Evidence / Replay

## 7.8.1 观测层不是日志层

AI4PDE 不应只记录 stdout/stderr，而应建立三层观测：

- **L1 Telemetry**：latency、GPU、token、walltime、memory
- **L2 Lifecycle**：team state、task transitions、graph version、mutation events
- **L3 Scientific Evidence**：残差曲线、边界误差、参考对比、checkpoint lineage、validation bundle

---

## 7.8.2 证据包

每个关键输出都应绑定最小证据包：

- `task_id`
- `graph_version`
- `template_id`
- `solver_config`
- `validation_results`
- `reference_comparison`
- `artifact_hashes`
- `checkpoint_refs`
- `provenance`

这使系统具备：

- 可复核
- 可回放
- 可审计
- 可对比

---

## 7.8.3 replay / counterfactual 能力

建议支持：

- replay 某次 task 的 workflow
- replay 某个 candidate graph 的验证过程
- 比较 active graph 与 candidate graph 在同一 benchmark 上的差异

这对 AI4PDE 尤其重要，因为：

- 很多优化是以“换图/换模板/换方法”形式发生的
- 只有可回放，才能真正做科学级比较

---

## 7.9 Hot Reload 与长航时任务

## 7.9.1 为什么需要 Hot Reload

PDE 场景中经常出现：

- 训练跑了很久才发现验证器过弱
- baseline 路径需要补充
- 观测 schema 需要升级
- 新模板需要替换旧模板

此时如果只能重启系统，代价太高。

---

## 7.9.2 建议的热更新协议

建议采用：

```text
Suspend
  → Export state
    → Transform state via migration adapter
      → Import into new component
        → Resume under observation window
          → Rollback if evidence degrades
```

需要重点支持的迁移对象：

- solver checkpoint schema
- task graph schema
- evidence schema
- template metadata schema
- worker runtime state

---

## 7.10 建议的数据对象

建议新增以下结构化对象：

### `PDETeamFile`

保存团队状态与成员信息。

### `PDEWorkerTask`

在普通 `Task` 之上增加：

- `physics_domain`
- `geometry_type`
- `cost_level`
- `required_validators`
- `required_evidence`

### `WorkflowGraphVersion`

保存：

- `graph_version_id`
- `parent_version_id`
- `template_id`
- `active_slots`
- `contracts`
- `mutation_summary`
- `rollback_target`

### `MutationProposal`

保存：

- `proposal_id`
- `proposal_type`
- `target_slots`
- `expected_gain`
- `risk_level`
- `evidence_basis`
- `policy_status`

### `ScientificEvidenceBundle`

保存：

- residual / BC / IC / conservation evidence
- reference comparison
- runtime telemetry
- provenance objects
- validation summary

---

## 7.11 演进路线建议

### Phase 1：引入 Team Runtime

优先实现：

- `PDECoordinator`
- team registry
- team-scoped task list
- mailbox/protocol bus
- idle / approval / shutdown 语义

### Phase 2：引入 Workflow Graph Versioning

优先实现：

- active graph / candidate graph
- graph cutover
- rollback target
- observation window

### Phase 3：引入 PDE Template Library

优先实现：

- forward / inverse / hybrid 模板
- template metadata
- template instantiation pipeline

### Phase 4：引入 Meta Optimization

优先实现：

- parameter tuning proposals
- graph rewiring proposals
- evaluation engine
- failure memory

### Phase 5：引入 Hot Reload + Migration

优先实现：

- checkpoint export/import
- migration adapters
- replay + counterfactual validation

---

## 7.12 与现有 science-agent 的关系

这个规范不是替换现有 `science-agent`，而是定义其下一阶段演化方向。

关系如下：

- 现有 `SciencePipeline` 可视为 v0.x 的单控制器实现
- `AI4PDE Team Runtime` 是其执行协作层增强
- `AI4PDE Meta-Harness` 是其系统演化层增强
- 原有 `Planner / Orchestrator / Validator / AssetManager` 仍保留，但将被进一步槽位化、协议化、图版本化

换句话说：

- 当前架构解决“把科研任务跑起来”
- 新架构进一步解决：
  - “如何让多个专业 worker 协同跑”
  - “如何让 runtime 在不失控的情况下持续进化”

---

## 7.13 最后总结

`AI4PDE Team Runtime + Meta-Harness` 的核心主张是：

- **协作运行时** 与 **演化运行时** 必须分层
- PDE 科学任务需要的不只是求解器，而是：
  - team coordination
  - governed workflow evolution
  - evidence-first delivery
  - replayable, rollbackable graph lifecycle
- `agent-team` 解决“谁协作、怎样协调”
- `MHE` 解决“系统如何安全变强”

因此，AI4PDE 的理想形态不是单体 Agent，而是一个：

- 能协作
- 能观测
- 能审计
- 能演化
- 但永远在治理约束内演化

的科学智能体平台子系统。
