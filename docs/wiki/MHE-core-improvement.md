
  ABACUS 报告
  - ABACUS 对 MHE core 的期待：需要“类型化运行控制平面”，覆盖 spec -> env probe -> compile
  -> workspace materialize -> execute -> discover output ->
  validate/evidence，而不只是组件装配。
  - 当前已匹配：图级治理已较强，commit_graph()、PromotionContext、安全审查、审计与
  provenance 已具备基础，见
  src/metaharness/core/boot.py:387、src/metaharness/core/models.py:201。
  - 主要不足：core 仍偏“图/组件中心”，缺少科学计算统一的
  RunPlan、RunArtifact、EnvironmentReport、任务级
  ValidationReport；executor/runtime/evaluation 仍较 stub，见
  src/metaharness/components/executor.py:10、src/metaharness/components/runtime.py:10、src/
  metaharness/components/evaluation.py:11。
  - 优先改进
    - 增加 core 级运行期模型：EnvironmentReport、RunPlan、RunArtifact、失败分类。
    - 增加任务执行控制面，与图提交控制面并行存在。
    - 把工作目录、输入文件、输出根目录、日志、证据引用提升为 core 一等对象。
    - 将 provenance/session event 从“图提交事件”扩展到“运行阶段事件”。
    - 把执行期 policy gate 纳入 core，而不只在 graph promotion 时审查。
  - 风险
    - 若 run model 设计过早过重，可能对其他 extension 造成束缚。
    - 若把文件/工作区语义设计得过于 HPC 化，会削弱通用性。
  - 关键文件
    - src/metaharness/core/boot.py:387
    - src/metaharness/core/models.py:109
    - src/metaharness/sdk/runtime.py:16
    - src/metaharness/safety/pipeline.py:34
    - src/metaharness/hotreload/checkpoint.py:31

  DeepMD 报告
  - DeepMD 对 MHE core 的期待：需要 family-aware、evidence-first、可治理的 workflow control
   plane，支持候选物理方案、模式化验证、allow/defer/reject 决策，以及长期运行任务的
  checkpoint / rollback / observation window。
  - 当前已匹配：外部 candidate 注入、promotion context、安全审查、optimizer proposal-only
  边界都已存在，见 src/metaharness/core/boot.py:315、src/metaharness/components/policy.py:7
  0、src/metaharness/components/optimizer.py:75。
  - 主要不足
    - 当前 ValidationReport 只有 valid + issues，不够承载 DeepMD
  需要的模式状态、证据完整性、打分与 defer 语义，见 src/metaharness/core/models.py:119。
    - ComponentRuntime 提供了很多接口，但缺少正式的 workspace / artifact / evidence
  持久化服务，见 src/metaharness/sdk/runtime.py:16。
    - graph validator 只能检查拓扑，不能表达 DeepMD 那类 workflow-family gate。
  - 优先改进
    - 扩展 core 验证记录：加入 status taxonomy、evidence refs、scored
  evidence、completeness。
    - 引入 core 级 evidence bundle / provenance contract。
    - 引入 workflow-run artifact model，统一工作区、日志、checkpoint、输出组。
    - 将 policy 从二元 allow/reject 扩展为 allow/defer/reject。
    - 强化 optimizer/study 与共享 evidence/fitness 对象的对接。
  - 风险
    - tri-state governance 会增加 promotion 流程复杂度。
    - 过强的 core 规范会提高现有扩展的迁移成本。
  - 关键文件
    - src/metaharness/core/models.py:119
    - src/metaharness/core/validators.py:87
    - src/metaharness/core/connection_engine.py
    - src/metaharness/sdk/runtime.py:16
    - src/metaharness/components/policy.py:70

  JEDI 报告
  - JEDI 对 MHE core 的期待：它假定 MHE 是“治理型控制平面”，不只是插件加载器；要求 typed
  contract、candidate/promotion review、protected
  validator、checkpoint/hot-swap/rollback、evidence handoff 与 optimizer seam。
  - 当前已匹配：graph candidate 生命周期、受保护组件、SessionEvent /
  SessionStore、ScoredEvidence、BrainProvider、hot swap/checkpoint primitives
  已有真实实现，见 src/metaharness/core/models.py:159、src/metaharness/core/brain.py:19、sr
  c/metaharness/hotreload/swap.py:35。
  - 主要不足
    - 当前 core 更强于“图级治理”，弱于“领域运行控制平面”；JEDI 的 environment -> compile ->
   preprocess -> mode-aware execute -> validate -> governance handoff
  还缺少对应的一等抽象。
    - ComponentRuntime 更像依赖容器，不是 run-time orchestration service。
    - safety/policy 主要审 graph promotion，不原生审查 run-level validator evidence
  package。
    - 当前 session / graph version store 仍偏内存语义，对治理级持久化支持不足。
  - 优先改进
    - 新增 run-oriented control-plane
  model：RunPlan、RunArtifact、ExecutionMode、ExecutionStatus、ValidationOutcome。
    - 统一 graph validation 与 run validation 的治理证据协议。
    - 增加 artifact/evidence bundle API，稳定标识
  config/stdout/stderr/diagnostics/reference。
    - 扩展 ComponentRuntime：加入 workspace manager、artifact registrar、evidence
  emitter、launcher abstraction。
    - 让 safety/policy 支持 run-level review。
    - 将 session/audit/provenance store 做成可插拔且可持久化。
  - 风险
    - 若把 graph governance 和 run governance 过度耦合，会显著提高 core 复杂度。
    - 持久化治理存储会带来 schema 演进和运维成本。
  - 关键文件
    - src/metaharness/core/boot.py:387
    - src/metaharness/core/models.py:201
    - src/metaharness/core/brain.py:19
    - src/metaharness/sdk/runtime.py:16
    - src/metaharness/safety/pipeline.py:96

  共性结论
  - 三套 wiki 对 MHE core 的共同要求，不是“再加几个组件”，而是把 core
  从图治理框架继续推进为运行治理框架。
  - 最值得优先推进的 4 个 core 改进是：
    - 统一的 run-oriented contracts
    - 一等化 artifact/evidence/workspace
    - run-level policy/gate/review
    - durable session / audit / provenance store
  
  
  AI4PDE 报告

  - AI4PDE 对 MHE core 的期待
    - 把 MHE 当成真正的 control plane：candidate → validate → cutover → observe → rollback
  的完整生命周期。
    - 支持 team/runtime
  级抽象：coordinator、task/mailbox、approval、idle/recovery、budget/risk enforcement。
    - 支持结构化科学资产：WorkflowGraphVersion、mutation record、evidence bundle、template
  生命周期、failure memory、replay/counterfactual。
  - 当前已匹配
    - 图级 staging/commit/rollback 已具备，见
  src/metaharness/core/connection_engine.py:72、src/metaharness/core/graph_versions.py:38。
    - lifecycle、hot swap、checkpoint、audit、provenance、session event 都有基础实现，见
  src/metaharness/sdk/base.py:13、src/metaharness/hotreload/checkpoint.py:31、src/metaharne
  ss/hotreload/swap.py:35。
    - optimizer 是 proposal-only，符合治理边界，见
  src/metaharness/components/optimizer.py:75。
    - core 还没有 team runtime / mailbox / approval center 这类控制面对象。
    - contract 仍以通用 port/slot 为主，没有科学工作流的一等类型。
    - governance 主要是 commit-time 二元门控，缺少 invariant engine、budget ledger、risk
  model、approval routing。
    - observation 主要存在于 hot-swap，不是 graph cutover 的统一观察窗口。
    - 持久化仍偏弱，wiki 对 durable store 的假设偏超前。
  - 优先改进
    - 增加 control-plane domain model：task、worker
  task、team/session、approval、budget、evidence、proposal、failure records。
    - 将 core 明确拆为 coordination / graph evolution / governance / evidence 四个平面。
    - 将 invariant/risk/budget 做成 authoritative services。
    - 扩展 graph lifecycle，引入 observation-window cutover 与自动 rollback。
    - 将 store 做成 durable + queryable。
    - 把 templates 提升为 core 一等资产。
  - 风险
    - 控制面过强会显著提高 core 复杂度，并可能与外部 agent 编排系统重叠。
  - 关键文件
    - src/metaharness/core/boot.py:60
    - src/metaharness/core/models.py:16
    - src/metaharness/core/graph_versions.py:38
    - src/metaharness/core/connection_engine.py:37
    - src/metaharness/safety/pipeline.py:34

  Nektar 报告

  - Nektar 对 MHE core 的期待
    - 将 MHE 作为 solver-specific slice 的控制平面：类型化 contracts、阶段化
  lifecycle、候选图治理、证据捕获、checkpoint/hot-swap、安全 gate、optimizer 驱动
  mutation。
  - 当前已匹配
    - HarnessAPI、ports/capabilities、graph commit/rollback、promotion
  evidence、checkpoint/hot-swap orchestration、proposal-only optimizer 均已具备基础，见
  src/metaharness/sdk/api.py:34、src/metaharness/core/boot.py:200、src/metaharness/hotreloa
  d/swap.py:35。
  - 主要不足
    - lifecycle 目前更多是 bookkeeping，不是真正被执行期语义强约束。
    - evidence 偏 graph-centric，不是 scientific-run-centric。
    - checkpoint/hot-reload 仍偏 in-memory / component-local，缺少 durable scientific state
    - safety 较浅，缺少资源、复现性、evidence completeness、scientific integrity 的内建
  gate。
    - optimizer 还没有真正和 runtime evidence 闭环。
    - 缺少 long-running external solver/job abstraction（timeout/cancel/retry/queue/HPC
  backend）。
  - 优先改进
    - 增加 first-class execution records：RunPlan / RunArtifact / ValidationEvidence。
    - 将 lifecycle 变成 executable semantics，而不是仅记录 phase。
    - 增加 durable checkpoint / evidence store。
    - 引入 job orchestration layer。
    - 强化 safety/governance，增加 reproducibility / evidence completeness gate。
    - 将 optimizer 与 runtime evidence 闭环打通。
    - 为 blue-green evaluation 增加 domain-neutral comparator。
  - 风险
    - 若 execution/job abstraction 过于贴近 HPC，会削弱 generic core 的通用性。
  - 关键文件
    - src/metaharness/core/boot.py:60
    - src/metaharness/sdk/base.py:13
    - src/metaharness/sdk/runtime.py:16
    - src/metaharness/core/connection_engine.py:36
    - src/metaharness/core/graph_versions.py:131
    - src/metaharness/hotreload/checkpoint.py:31

  补充结论
  - ai4pde 更强调 团队式控制平面、审批与预算治理。
  - nektar 更强调 运行记录、外部求解器 orchestration、durable evidence/checkpoint。
  - 两者与前面的 abacus / deepmd / jedi / qcompute 一起看，MHE core
  的下一阶段改进可以归并成 5 条主线：
    - run-oriented contracts
    - durable evidence/provenance/checkpoint
    - execution/job orchestration
    - richer governance（risk/budget/approval/defer）
    - control-plane objects beyond component graph
