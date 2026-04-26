# MHE 最近一轮强化工作的详细报告

## 概览

本轮工作以提交 `9babe5b`（`feat(metaharness): strengthen promotion governance and evidence flow`）为主线，目标是在不推翻现有 Meta-Harness Engine（MHE）实现的前提下，把运行时图治理从“可工作的骨架”强化为更接近文档设计的统一控制平面。此次改动重点不在增加单个新功能，而在于把 graph promotion、safety、policy、runtime evidence、hot reload、checkpoint、protected boundary、evaluation 语义与 extension contract 逐步拉到同一条权威路径上。

与之前相比，当前 MHE 在以下方面有了实质性收敛：

- 候选图提交不再只是 `stage -> commit` 的薄路径，而是围绕 `PromotionContext` 进入显式 promotion 流。
- 安全链不再只服务于 proposal 评估，也开始承担 graph promotion authority。
- session 级 evidence 有了正式数据模型和最小可用存储接口，可把 candidate、checkpoint、hot-swap、commit/reject 写入统一事件流。
- protected component 的治理从 slot 层面进一步延伸到 promotion / rewiring / hot-swap 约束。
- extension 层（重点是 AI4PDE 与 Nektar）开始携带 candidate / checkpoint / provenance / scored-evidence 元数据，降低主框架与扩展语义漂移。

## 一、核心数据模型的补强

本轮工作首先补齐了 promotion / evidence / evaluation 所需的公共数据模型，主要落在 `src/metaharness/core/models.py`。

### 1. ValidationIssue 与 ValidationReport 扩展

`ValidationIssue` 新增了：

- `category`
- `blocks_promotion`

这使 validation 不再只是“有无错误”的平面结果，而可以表达：

- 这是语义错误、protected 违规、readiness 问题还是 promotion blocker；
- 该问题是否必须阻止 candidate 成为 active graph。

这一步是后续 gated promotion 的关键，因为 `commit_graph()`、policy review、safety pipeline 都需要同一份可解释的 gating 语义，而不是各自重新判断“什么算严重错误”。

### 2. PromotionContext 成为 graph promotion 的统一载体

新增 `PromotionContext`，字段包括：

- `candidate_id`
- `candidate_snapshot`
- `validation_report`
- `proposed_graph_version`
- `rollback_target`
- `actor`
- `affected_protected_components`
- `created_at`

这让 graph promotion 从“几个临时局部变量拼起来”的过程，提升为显式上下文对象。后续 policy reviewer、session event、audit、provenance、rollback 关联都围绕它展开。

### 3. SessionEvent / SessionEventType 建模

新增 `SessionEventType` 与 `SessionEvent`，为以下运行时事件提供统一结构：

- candidate 创建
- candidate 校验
- safety gate 评估
- candidate reject
- graph commit / rollback
- checkpoint 保存
- hot-swap initiate / complete / rollback

这一步意味着 session 级 evidence 已不再只是“将来可以做”的方向，而是已有正式 payload 结构和最小落地实现。

### 4. ScoredEvidence / BudgetState / ConvergenceState

新增统一的 scored-evidence 数据模型，用于承接 optimizer、evaluation 与 domain validation：

- `ScoredEvidence`
- `BudgetState`
- `ConvergenceState`

核心收益是：extension 不再只需要返回各自风格的 `metrics` 或 `passed/messages`，而是可以逐步对齐到统一的“可比较、可审计、可回放”的 evaluation 负载。

## 二、HarnessRuntime 提升为统一 promotion / evidence 入口

本轮最重要的行为变化发生在 `src/metaharness/core/boot.py`，即 `HarnessRuntime` 的职责被显著强化。

### 1. Runtime 增加 session / audit / provenance 依赖

`HarnessRuntime.__init__()` 现在可以持有：

- `session_id`
- `session_store`
- `audit_log`
- `provenance_graph`

默认实现分别采用：

- `InMemorySessionStore`
- `AuditLog`
- `ProvGraph`

这意味着 runtime 已能够在 promotion 时直接写入 session event、审计记录和 provenance 关系，而不必由外层调用者拼接多套旁路逻辑。

### 2. _append_runtime_evidence()

新增 `_append_runtime_evidence()`，负责：

- 写入 `SessionStore`
- 把 event 与 candidate / graph version 建立 provenance 关系
- 把对应信息写入 `AuditLog`

这是当前“统一 runtime evidence flow”的核心落点。虽然目前仍是 in-memory / process-local 为主，但接口和引用关系已经按长期演进方向搭好了。

### 3. commit_graph() 改成 gated promotion 路径

`commit_graph()` 现在的主路径可以概括为：

1. 执行 manifest policy enforcement；
2. `engine.stage()` 生成 candidate 与 validation report；
3. 构建 `PromotionContext`；
4. 记录 `candidate_created` / `candidate_validated` session evidence；
5. 发布 `BEFORE_COMMIT_GRAPH` 事件；
6. 调用 `SafetyPipeline.evaluate_graph_promotion()`；
7. 记录 `safety_gate_evaluated` evidence；
8. 如果存在 `blocks_promotion` issue 或 safety veto，则 discard candidate、记录失败 lifecycle、写入 `candidate_rejected` evidence，并发布 `CANDIDATE_REJECTED`；
9. 否则 commit、更新 lifecycle、写入 `graph_committed` evidence，并发布 `AFTER_COMMIT_GRAPH`。

这带来的实质变化是：active graph 的切换现在有了统一门控语义，而不是仅由 `ConnectionEngine` 的 validity 结果隐式决定。

## 三、安全与治理路径的收敛

### 1. SafetyPipeline 支持 graph promotion review

`src/metaharness/safety/pipeline.py` 中新增 `evaluate_graph_promotion()`。此前 safety pipeline 主要评估 `MutationProposal`；现在开始接收 `PromotionContext`，作为 graph promotion 的正式 authority path。

目前实现依旧保持向后兼容：

- proposal 级 `evaluate(...)` 没被移除；
- graph promotion 级 review 在无 reviewer 时默认放行；
- 但 runtime 已经把 promotion 显式接到了 safety pipeline 上。

这一步非常关键，因为它把“extension 提 proposal”“policy 做 review”“runtime 做 graph commit”三条原本可能分离的路径收拢到了同一个判决链路上。

### 2. PolicyComponent 新增 review_graph_promotion()

`src/metaharness/components/policy.py` 增加 `review_graph_promotion()`，使 policy component 不再只对 mutation proposal 发声，也能直接参与 candidate promotion 的 allow/reject 决策。

当前逻辑是围绕 `validation_report.issues` 中的 `blocks_promotion` 条目做拒绝判定，并把决策写回 `proposal_reviews` / `decisions`。这虽然仍是最小实现，但已经建立了“policy 参与图晋升”的正式接口面。

## 四、凭证与沙箱策略开始进入 manifest / runtime 主路径

相关改动主要落在：

- `src/metaharness/sdk/manifest.py`
- `src/metaharness/sdk/runtime.py`
- `src/metaharness/components/gateway.py`
- `src/metaharness/components/toolhub.py`
- `src/metaharness/core/boot.py`

### 1. Manifest 新增 PolicySpec

`ComponentManifest` 现在通过 `policy` 字段正式暴露：

- `CredentialPolicySpec`
- `SandboxPolicySpec`

其中包括：

- `requires_subject`
- `allow_inline_credentials`
- `required_claims`
- `sandbox.tier`

同时通过 `sync_legacy_policy_fields()` 保留了与旧 `safety.sandbox_profile` 的兼容。

### 2. Runtime / Gateway / Toolhub 开始消费这些策略

这批改动的意义不只是“字段可写入 manifest”，而是它们开始被运行路径消费：

- runtime 可检查 sandbox tier；
- gateway 可依据凭证策略拒绝不满足 subject/claim 约束的输入；
- toolhub 开始执行 sandbox tier enforcement。

虽然还没有完整 `CredentialVault` 或惰性沙箱基础设施，但本轮已经把“policy 只是注释”推进成“policy 是可执行约束”的阶段。

## 五、protected component enforcement 从静态声明走向执行约束

### 1. Validator 层加强 protected 违规判定

`src/metaharness/core/validators.py` 在原有 protected slot override 之上，继续对 active graph rewiring/removal 等情形强化约束。这意味着 protected 不再仅是“声明式标签”，而开始影响 candidate 是否允许进入 promotion。

### 2. Runtime 与 hot-swap 共同消费 protected 语义

在 runtime promotion 路径中，`affected_protected_components` 会进入 `PromotionContext`；在 hot reload 路径中，protected component 的热替换需要显式 `allow_protected=True`，否则直接被拒绝。

这让 protected boundary 逐步具备了跨模块一致性：

- validator 能发现；
- policy 能审查；
- runtime 能记录；
- hot-swap 能执行拒绝。

## 六、运行时 evidence flow 与 checkpoint / provenance 贯通

### 1. SessionStore 与 InMemorySessionStore

`src/metaharness/observability/events.py` 新增：

- `SessionStore` 抽象
- `InMemorySessionStore` 最小实现
- `make_session_event()` 工厂

这为后续的 `wake(session_id)`、事件重放、session 级查询、SSE/streaming observability 留下了清晰扩展点。

### 2. CheckpointManager 记录证据链

`src/metaharness/hotreload/checkpoint.py` 中，checkpoint 不再只是内存快照容器，还可在 capture 时：

- 写入 `CHECKPOINT_SAVED` session event；
- 生成 `checkpoint:*` provenance entity；
- 建立 event → checkpoint、checkpoint → parent checkpoint 的 `WAS_DERIVED_FROM` 关系；
- 写入 audit record。

这说明 checkpoint 已开始被纳入正式 evidence lineage，而不是孤立的 hotreload 细节。

### 3. HotSwapOrchestrator 写入 lifecycle evidence

`src/metaharness/hotreload/swap.py` 现在会围绕 hot swap 生命周期写入：

- `HOT_SWAP_INITIATED`
- `HOT_SWAP_COMPLETED`
- `HOT_SWAP_ROLLED_BACK`

同时把：

- affected protected components
- checkpoint id
- observation 结果
- audit refs / session-event refs

绑定到 `HotSwapReport.evidence_refs`。这意味着热替换路径已经开始与统一 evidence flow 对齐。

## 七、Optimizer / Evaluation 语义的统一起点

### 1. BrainProvider 抽象

`src/metaharness/core/brain.py` 新增：

- `BrainProvider` protocol
- `FunctionalBrainProvider`

它把 optimizer 的 proposer / evaluator seam 从“运行时临时 callable”提升为正式可替换接口，给后续模型解耦、外部 planner/evaluator 注入留下了稳定边界。

### 2. Evaluation / convergence 对齐 ScoredEvidence

本轮同时把 optimizer / evaluation 相关实现开始对齐到 `ScoredEvidence`。这带来的好处是：

- active graph evaluation 与 candidate evaluation 有机会共享形状；
- extension domain validator 返回的结果可以更容易接入 optimizer 历史；
- 后续可以在 safety、budget、convergence、evidence refs 上做统一比较，而不是在各自 extension 里重复建模。

## 八、AI4PDE 侧的适配情况

AI4PDE 是本轮主扩展适配对象之一，重点变化包括：

### 1. contract surface 升级

`src/metaharness_ext/ai4pde/contracts.py` 与相关类型新增/扩展了：

- candidate identity
- promotion metadata
- safety evaluation
- rollback context
- checkpoint / provenance 相关字段

这使 AI4PDE contract 从“面向 demo 和局部执行链的轻量模型”向“可接入 MHE promotion / evidence authority 的正式模型”靠拢。

### 2. demo 路径迁移到 HarnessRuntime

`src/metaharness_ext/ai4pde/demo.py` 已从直接操纵 `ComponentRegistry` / `ConnectionEngine` 的方式，转而通过：

- `HarnessRuntime.boot()`
- `HarnessRuntime.commit_graph()`

完成 graph 提交。这一点很重要，因为它让 AI4PDE demo 首次真正经过强化后的 lifecycle / policy / evidence 路径，而不再是旁路实现。

### 3. 治理、观测与验证组件适配

`risk_policy.py`、`physics_validator.py`、`observability_hub.py`、`evidence/bundle.py`、`mutations/triggers.py`、`types.py` 等也都开始携带更丰富的 promotion / evidence / scored-evidence 元数据。

总结而言，AI4PDE 已从“轻量 extension”明显向“依赖强化后 MHE 权威边界”的方向迁移，但仍有进一步把 template state / approval / session replay 正式化的空间。

## 九、Nektar 侧的适配情况

Nektar 是另一条已经实质推进的 extension 适配线。

### 1. contracts / execution artifacts 补齐上下文元数据

`src/metaharness_ext/nektar/contracts.py`、`session_compiler.py`、`solver_executor.py`、`validator.py`、`convergence.py` 等开始补充：

- candidate / graph version 信息
- checkpoint / provenance 引用
- scored-evidence 相关输出
- promotion / validation 所需的上下文字段

这使 Nektar 的 artifact-first 工作流不再只是“生成文件 + 执行 + 汇总结果”，而是能把执行结果挂回 MHE 的统一治理与证据链。

### 2. manifest 补齐 policy / binary / environment 语义

多份 Nektar manifest (`manifest.json`、`session_compiler.json`、`solver_executor.json`、`validator.json`、`postprocess.json`、`convergence.json`) 已补入与新 policy surface 对齐的字段，帮助 runtime 更明确地理解其文件系统、二进制、环境与沙箱约束。

整体看，Nektar 的主线优势仍然是 contract-first / artifact-first / 线性执行路径清晰；此次工作是在不破坏这一结构的前提下，为其补足 promotion、evidence、policy 与 scored-evidence 语义。

## 十、测试与验证覆盖

本轮改动伴随了一批核心测试补强，重点包括：

- `tests/test_boot.py`
- `tests/test_safety_pipeline.py`
- `tests/test_hot_reload.py`
- `tests/test_validation.py`
- `tests/test_manifest_extended.py`
- `tests/test_identity_boundary.py`
- `tests/test_toolhub.py`
- `tests/test_optimizer.py`
- `tests/test_optimizer_component_integration.py`
- `tests/test_optimizer_fitness_convergence.py`
- `tests/test_ai4pde_*`
- `tests/test_metaharness_nektar_*`

测试重点覆盖了：

- gated promotion 成功/失败路径；
- policy veto 对 candidate promotion 的阻断；
- session evidence 是否正确写入；
- protected component promotion / rewiring / hot-swap 拒绝；
- checkpoint lineage 与 rollback evidence；
- scored-evidence / optimizer 适配；
- AI4PDE 与 Nektar 的合同面和运行路径兼容性。

这批测试的价值不只是“新增 case 数量”，而是把本次强化工作的关键不变量明确表达出来，降低后续演进时发生静默回退的风险。

## 十一、当前实现达到的程度

如果用“当前 MHE / 强化中的 MHE / 长期 CMA-inspired 方向”三层来概括，本轮工作的定位如下：

### 已经实装并可被代码直接依赖的部分

- promotion context 数据模型
- graph promotion 经由 runtime 统一收敛
- safety pipeline 进入 promotion authority path
- session event/store 最小实现
- checkpoint / hot-swap evidence 接入 session/audit/provenance
- manifest 级 credential/sandbox policy 声明与部分 enforcement
- protected boundary 的进一步执行约束
- scored-evidence 基础模型
- BrainProvider seam
- AI4PDE / Nektar 主干适配

### 已搭好接口但仍属早期或最小实现的部分

- `SessionStore` 仍主要是 in-memory backend
- `wake(session_id)` 还没有完整恢复入口
- `CredentialVault` 仍未取代当前 identity boundary
- 惰性沙箱仍是方向，不是完整执行框架
- graph promotion 的多级 safety gate 仍偏简化
- extension 侧对 session replay / rollback lineage 的深度消费还不充分

## 十二、对后续工作的直接意义

本轮工作最重要的产出，不是某个独立 feature，而是一个更稳定的“强化基线”。它为后续 extension（包括 ABACUS、DeepMD、JEDI）提供了比此前更明确的依赖面：

- 如果扩展要进入正式 graph promotion，就应围绕 `PromotionContext`、`ValidationIssue.blocks_promotion`、policy review 和 runtime evidence 来设计；
- 如果扩展要声明执行边界，就应通过 manifest policy、capability、sandbox tier、credential requirement 暴露给 runtime；
- 如果扩展要输出验证结果，就应尽量靠拢 `ScoredEvidence` / provenance refs / checkpoint lineage，而不是仅返回局部指标；
- 如果扩展涉及可恢复执行或热替换，就需要考虑 checkpoint、session event 与 protected semantics，而不是把运行状态留在隐式进程内对象里。

## 十三、结论

本轮强化工作已经把 MHE 从“具备 promotion / governance / observability / hotreload 骨架的工程雏形”，推进到了“这些能力开始围绕统一数据模型与权威路径协同工作”的阶段。

它还没有完全达到 wiki 中更完整的长期蓝图，尤其在 stateless runtime、session replay / wake、credential vault、惰性沙箱和更强 extension replayability 上仍有距离；但作为主干工程基线，本轮已经完成了几项关键收敛：

- promotion 不再是薄提交，而是显式治理流程；
- safety / policy 开始成为 graph authority 的一部分；
- evidence / checkpoint / provenance 不再是离散特性，而开始在统一 session 语义下连通；
- extension contract 开始跟随主框架的治理与证据模型演进。

因此，这轮工作可以视为一次“控制面成形”的里程碑：之后新增扩展或重构既不应再假定 runtime 是轻量、无治理、无证据的执行壳，也不应绕开 `HarnessRuntime` 直接把候选图提升为 active graph。