我已经自己把 core 关键面并行读完了。结论很明确：当前 MHE core
  更像“图治理框架”，还不是“运行治理框架”；这正是 QCompute 落地时的主要架构阻力。

  1. 执行模型
  - HarnessComponent 只有生命周期钩子：declare_interface/activate/deactivate/suspend/resume
  /export_state，没有任务执行抽象，见 src/metaharness/sdk/base.py:13
  - HarnessRuntime.boot()
  只是发现、注册、asyncio.run(component.activate(runtime))，不管理长任务，见
  src/metaharness/core/boot.py:200
  - ExecutorComponent / RuntimeComponent 仍是 stub，只处理同步 dict payload，见
  src/metaharness/components/executor.py:10、src/metaharness/components/runtime.py:10
  - 缺口：没有 run/job abstraction、没有 polling/retry/cancel、没有
  queued/running/completed 状态机、没有 batch execution
  - QCompute 需要：core 级 RunPlan / RunArtifact / JobHandle /
  ExecutionStatus，支持真机异步轮询、重试、取消、批量执行

  2. Optimizer / Fitness / Mutation
  - OptimizerComponent 是严格 proposal-only；它只能产出 MutationProposal 并交给
  MutationSubmitter，见 src/metaharness/components/optimizer.py:75
  - BrainProvider 的 propose/evaluate 操作对象是 graph mutation，不是领域实验，见
  src/metaharness/core/brain.py:19
  - MutationProposal 只携带 PendingConnectionSet，见 src/metaharness/core/mutation.py:16
  - FitnessEvaluator 和 TripleConvergence 只有通用标量 fitness / plateau / budget / safety
  floor，见
  src/metaharness/optimizer/fitness.py:80、src/metaharness/optimizer/convergence.py:40
  - 缺口：没有 Study loop、一等化 trial/evidence/trajectory history；C×L×K 只能硬塞进 graph
   mutation
  - QCompute 需要：新增 run-domain optimizer layer：ExperimentProposal / StudyTrial /
  StudyReport，支持 trajectory-level evaluation、CxLxK、Pareto front、domain evidence
  feedback

  3. Safety / Governance
  - SafetyPipeline.evaluate() 会跑 gate，但 evaluate_graph_promotion() 只调用
  reviewer，本身没有 run-level gate，见 src/metaharness/safety/pipeline.py:96
  - PolicyComponent.review_graph_promotion() 只是按 blocks_promotion allow/reject，见
  src/metaharness/components/policy.py:70
  - 缺口：没有 validator-evidence 审查、没有 quota/noise/fidelity/run-result gate、没有
  defer
  - QCompute 需要：promotion authority 从“图校验”扩展到“运行证据校验”，支持 allow / defer /
   reject，并原生理解保真度、噪声、配额、校准时效

  4. Hot reload / Checkpoint
  - 这块反而比想象中强：有 saga 化热切换、checkpoint capture、state migration、observation
  window，见 src/metaharness/hotreload/swap.py:35、src/metaharness/hotreload/checkpoint.py:
  31、src/metaharness/hotreload/observation.py:39
  - 但 CheckpointManager 仅内存存储，checkpoint 内容是组件 state，不是运行 artifact，见
  src/metaharness/hotreload/checkpoint.py:31
  - 缺口：没有面向科学任务的 run checkpoint / artifact snapshot / job resume
  - QCompute 需要：durable checkpoint store，能保存 circuit、backend calibration
  snapshot、raw counts、validation context，而不只是 component state

  5. Event bus / Session store
  - EventBus 是进程内 pub/sub，只有 before_commit_graph / after_commit_graph /
  candidate_rejected 这些命名常量，见 src/metaharness/core/event_bus.py:15
  - SessionStore 已存在，但实现在 observability/events.py，且只有 InMemorySessionStore，见
  src/metaharness/observability/events.py:17
  - 缺口：没有 durable session log，没有 run-level event schema
  - QCompute 需要：追加型持久会话流，事件覆盖 plan_compiled / job_submitted / job_polled /
  job_completed / validation_emitted / evidence_bundled

  6. Observability / Provenance
  - TraceCollector 是内存 trace，见 src/metaharness/observability/trace.py:62
  - AuditLog 支持 JSONL + Merkle anchoring，这很好，见
  src/metaharness/provenance/audit_log.py:40
  - ProvGraph 是内存 PROV 图，关系模型够用，但仍偏泛化，见
  src/metaharness/provenance/evidence.py:65
  - 缺口：没有一等化 scientific artifact lineage schema
  - QCompute 需要：原生表达 experiment_spec -> run_plan -> run_artifact ->
  validation_report -> evidence_bundle 的 provenance 链，并把 calibration snapshot、noise
  model、backend identity 纳入 lineage

  7. Runtime injection surface
  - ComponentRuntime 暴露了很多潜在入口：brain_provider、sandbox_client、process_direct、to
  ol_execute、mutation_submitter，但大多只是空槽位，见 src/metaharness/sdk/runtime.py:16
  - 缺口：没有正式的 workspace manager、artifact registrar、job runner、evidence emitter
  - QCompute 需要：把这些“可选注入字段”变成正式运行时服务协议

  最关键的 5 个 core 改进
  - 新增 run-oriented core contracts：EnvironmentReport / RunPlan / RunArtifact /
  ValidationOutcome / EvidenceBundle
  - 新增 job execution layer：异步任务、轮询、重试、取消、批量执行
  - 新增 run-level governance：review validator evidence，而不只 review graph issues
  - 新增 durable session/audit/provenance store
  - 将 optimizer 从 graph mutation 扩展为 graph layer + experiment/study layer 双层架构
