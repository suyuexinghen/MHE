# 02. 运行流程与生命周期

## 2.1 总调用链

`AI4PDE Agent` 的一次完整任务，不再是单一 `pipeline.run()` 的线性链，而是由 **Team Runtime** 与 **Meta-Harness** 共同驱动。

总流程如下：

```text
用户输入
  │
  └─ PDECoordinator.receive()
        │
        ├─ Intent Interpreter / PDE Task Builder
        ├─ Team Runtime 建队 / 任务拆解 / 分配 worker
        ├─ Planner / Method Router 生成工作流图
        ├─ Runtime Orchestrator 执行图
        ├─ Composite Validator 验证结果
        ├─ Asset / Evidence / GraphVersion 持久化
        └─ 若有必要 → Meta-Harness 提议 candidate graph
                         → 验证 / 观察窗口 / 激活 / 回滚
```

---

## 2.2 双生命周期

AI4PDE 子系统同时存在两个生命周期：

### 2.2.1 Team Runtime 生命周期

负责一次具体科研任务的协作执行：

1. 创建 team
2. 生成 task list
3. 启动 worker
4. 分配任务
5. worker 进入 idle / active 循环
6. 完成后 shutdown / recycle

### 2.2.2 Meta-Harness 生命周期

负责工作流和组件图的安全演化：

1. 监听性能 / 失败 / 成本信号
2. 提出 mutation proposal
3. 构建 candidate graph
4. 进行静态 / 沙盒 / 影子验证
5. 激活或回滚
6. 在 observation window 内持续监控

前者回答“这次任务怎么跑”，后者回答“系统如何安全变强”。

---

## 2.3 Phase 0：演化信号检测（可选）

在处理新任务前，或在长任务中途，Meta Layer 可以被动或主动触发：

- validation 长期停留在 `PARTIAL`
- 某类 solver 成本持续过高
- 某模板在最近 benchmark 上退化
- 某条 workflow 重复进入死胡同
- 新 checkpoint / 新模板已可用

此时执行：

```text
Observability / Metrics
  → Optimizer
    → MutationProposal
      → Policy Engine
        → Candidate Graph Validation
```

若 proposal 未通过，则只记录，不污染 active runtime。

---

## 2.4 Phase 1：意图澄清与任务形式化

`PDECoordinator` 接收用户任务后，首先进入问题形式化流程。

### 2.4.1 目标

将自然语言请求转化为结构化 `PDE Task`：

- 问题类型：`forward / inverse / design / surrogate`
- PDE / constitutive law
- geometry / mesh / SDF / point cloud
- BC / IC
- data source
- deliverables
- budget / risk

### 2.4.2 输出对象

```text
PDE Task
  ├─ physics_spec
  ├─ geometry_spec
  ├─ data_spec
  ├─ deliverables
  ├─ budget
  ├─ risk_level
  └─ required_evidence
```

### 2.4.3 澄清协议

若缺少关键字段，coordinator 不应直接启动高成本流程，而应先反问，例如：

- 几何表示是哪一种？
- 是否已有 baseline solver 结果？
- 目标是近似推理还是高保真验证？
- 可接受的 walltime / GPU 预算是多少？

若用户无法提供关键信息或超时（默认 5 分钟无响应）：
- Coordinator 将任务标记为 `status: blocked`
- 发送 `failure_report` 到 Audit Trail
- 向用户建议重新组织需求后再提交

### 2.4.4 Worker-Meta 交互路径约束

Worker 不能直接访问 Meta Layer。所有变更请求必须通过 `PDECoordinator` 代理：

```text
Worker
  → candidate_change_request (mailbox)
    → PDECoordinator
      → Mutation Manager (Meta Layer)
        → 策略审查 / 验证
          → 结果回传
            → PDECoordinator
              → Worker (mailbox)
```

这保证了 Coordinator 作为唯一控制面网关的角色，防止 worker 绕过治理层直接触发图版本变更。

---

## 2.5 Phase 2：Team 创建与任务拆解

任务形式化完成后，进入 Team Runtime。

### 2.5.1 建队

`PDECoordinator` 创建本次运行的 team context：

- `teamName`
- `leadWorkerId`
- `members`
- `backend`
- `allowedPaths`
- `graphVersion`

### 2.5.2 拆解任务

基于 PDE task，将任务拆解为可协作子任务，例如：

- `T1`: 问题形式化确认
- `T2`: 方法选择与模板匹配
- `T3`: 几何与输入预处理
- `T4`: PINN 路径求解
- `T5`: Classical baseline 求解
- `T6`: 物理验证与参考对比
- `T7`: 证据包与报告生成

### 2.5.3 分配 worker

典型分配：

- `MethodRouterWorker` → `T2`
- `GeometryWorker` → `T3`
- `SolverWorker-A` → `T4`
- `ReferenceSolverWorker` → `T5`
- `PhysicsValidatorWorker` → `T6`
- `ReportWorker` → `T7`

> 团队与任务的数据模型定义见 [03-data-models.md](03-data-models.md) 第 3.3–3.4 节。

---

## 2.6 Phase 3：模板匹配与方法规划

在真正执行前，Planner / Method Router 会：

1. 查询 `Template Library`
2. 查询 `Knowledge Adapter`
3. 查询 `Capability Registry`
4. 识别 geometry / PDE / data 三元组合
5. 选择工作流图与 solver family

### 2.6.1 典型路由规则

- 小数据 + 清晰 PDE + inverse → `PINN Strong`
- 有稳定变分原理 → `DEM / Energy`
- 大量样本 + 多次重复推理 → `Operator Learning`
- 需要速度 + 物理校正 → `PINO`
- 需要高保真 baseline / 认证 → `Classical Hybrid`

### 2.6.2 模板绑定

若命中模板，则 Planner 不从零起图，而是：

- 实例化模板
- 绑定 slot
- 约束可变参数
- 生成 `WorkflowGraphVersion(candidate)`

若模板库无匹配结果：
1. MethodRouter 回退至自由规划模式，使用默认风险约束
2. Coordinator 构建基础任务图（不含模板约束）
3. 若 Meta Layer Level 4（受限合成）可用，可生成候选图供审查
4. 此路径产生的任务标记 `template_id: null`

> 模板库的完整目录与匹配规则见 [05-template-library-and-self-growth.md](05-template-library-and-self-growth.md)。

---

## 2.7 Phase 4：治理预检

在求解前必须经过治理预检。

### 2.7.1 预算检查

`Budget Guard` 检查：

- token 预算
- GPU 小时
- walltime
- batch 数量
- HPC 提交额度

### 2.7.2 风险检查

`Risk Gate` 按风险分级：

- `Green`: 自动放行
- `Yellow`: 受约束运行
- `Red`: 需要 coordinator / policy 批准

### 2.7.3 快照保存

进入执行前，`Checkpoint Manager` 保存：

- 初始 task snapshot
- active graph version
- runtime config
- evidence schema version

### 2.7.4 否决处理

若 Red 级请求被否决：
- Coordinator 向用户发送否决原因与建议替代方案
- 任务保持 `status: blocked`，等待用户决策
- 可选：Coordinator 提出降级方案（如用低成本方法替代）

---

## 2.8 Phase 5：求解执行

### 2.8.1 执行模式

运行期支持两类主路径：

#### 路径一：AI4PDE Solver Path

- `PINNStrongExecutor`
- `DEMEnergyExecutor`
- `OperatorLearningExecutor`
- `PINOExecutor`

#### 路径二：Classical Hybrid Path

- `FEM / FVM / FEniCS / OpenFOAM`
- baseline / correction / high-fidelity validation

### 2.8.2 worker 执行语义

每个 worker 完成一轮任务后：

1. 更新 task status
2. 写入 mailbox / task list
3. 进入 `idle`
4. 等待新任务或 shutdown

### 2.8.3 长航时任务

对训练或 HPC 作业：

- 运行期应支持异步心跳
- coordinator 不阻塞等待
- 中间状态进入 checkpoint
- validator 可在阶段性结果上做 early feedback

### 2.8.4 运行期预算执行

- solver worker 每完成一个 checkpoint interval 须上报 cost increment（GPU 时间、token 消耗）
- Checkpoint Manager 将累计消耗与 `BudgetRecord.hard_limit` 对比
- 若超出 hard_limit：强制 suspend，触发 ESCALATE 通知 Coordinator
- 若接近 soft_limit（90%）：发送 warning，Coordinator 决定是否继续

---

## 2.9 Phase 6：验证闭环

求解完成后进入 `Composite Validator`。

### 2.9.1 验证层次

- `Structural Validation`
  - 工件是否完整
  - schema 是否正确
- `Physics Validation`
  - residual
  - BC / IC satisfaction
  - conservation / energy consistency
- `Reference Validation`
  - 与 classical baseline / experiment 对比

### 2.9.2 输出

```text
Validation
  ├─ status
  ├─ confidence
  ├─ violations
  ├─ next_action
  └─ evidence_refs
```

`next_action` 典型取值：

- `DELIVER`
- `RETRY`
- `SUBSTITUTE`
- `REPLAN`
- `HOT_RELOAD`
- `ESCALATE`

> 验证结果的数据模型与 `next_action` 枚举定义见 [03-data-models.md](03-data-models.md) 第 3.6 节。

---

## 2.10 Phase 7：回退、重规划与热加载

### 2.10.1 Retry

适用于：

- 短暂失败
- 超参数可局部调整
- collocation / optimizer 轻微修正即可恢复

### 2.10.2 Substitute

适用于：

- 当前方法族不稳定
- 切换 `PINN ↔ DEM ↔ PINO ↔ Classical`

### 2.10.3 Replan

适用于：

- workflow 图本身有问题
- 需要插入新 validator / reference branch / uncertainty branch

此时触发 Meta Layer 提议 candidate graph。

### 2.10.4 Hot Reload

适用于：

- validator 需要升级
- evidence schema 需要迁移
- 模板元数据需切换
- 中途引入更稳妥的组件

协议：

```text
Suspend
  → Export state
    → Transform via migration adapter
      → Import
        → Resume under observation window
```

> 热加载治理规则与观察窗口参数见 [04-governance-and-observability.md](04-governance-and-observability.md) 第 4.6 和 4.11 节。

---

## 2.11 Phase 8：交付与资产沉淀

当验证通过时，系统应输出：

- 最终结果
- 证据包
- PROV 溯源对象
- graph version
- template id
- runtime metrics

并沉淀以下资产：

- workflow template
- solver config
- validation rule pack
- failure patch
- graph version lineage

若失败，则沉淀：

- failure pattern
- dead-end path
- rejected proposal family

### 2.11.1 用户侧交付格式

- 默认：Markdown 报告 + 结构化 JSON 证据摘要
- 可选：下载完整证据包（含 checkpoint、artifact、provenance）
- 可选：生成可复现的 workflow graph snapshot

---

## 2.12 Worker 生命周期

单个 worker 的生命周期建议为：

```text
spawn
  → initialize identity/team context
    → receive task/message
      → execute one turn
        → update task state
          → send idle_notification
            → wait mailbox/task list
              → resume or shutdown
```

这保证 worker：

- 可复用
- 可恢复
- 可审计
- 不必反复冷启动

---

## 2.13 Meta-Harness 生命周期

单次 proposal 的生命周期建议为：

```text
signal detected
  → mutation proposal
    → policy review
      → candidate graph build
        → static validation
          → shadow/sandbox validation
            → active cutover
              → observation window
                → stabilize or rollback
```

这保证系统变更不会直接污染 live runtime。

---

## 2.14 一次完整任务时序示意

```text
User
 └─ PDECoordinator.receive(query)
     ├─ interpret -> PDE Task
     ├─ create team context
     ├─ create task list
     ├─ planner/template binding
     ├─ governance precheck
     ├─ assign solver / validator / report workers
     ├─ orchestrator.run(workflow graph)
     │   ├─ solver worker executes
     │   ├─ reference solver worker executes
     │   ├─ validator worker evaluates
     │   └─ report worker synthesizes
     ├─ if needed -> meta layer proposes candidate graph
     ├─ validate final bundle
     ├─ save assets / graph version / evidence
     └─ deliver output + provenance
```

---

## 2.15 当前流程特点总结

- 执行协作与系统演化分层
- 多 worker 协作由 team runtime 原生支撑
- 工作流升级走 candidate graph，而非 live 改写
- 证据、图版本、回滚目标是一等对象
- 长航时 PDE 任务具备 idle / recovery / hot reload 语义

这也是 AI4PDE Agent 区别于普通“LLM 调 solver”的核心所在。
