架构升级：从面向算例计算流程到面向科学研究闭环流程
问题陈述
当前 MHE 的核心架构是面向算例计算流程（computation-instance-oriented）的：
执行链路是 Gateway → EnvironmentProbe → InputCompiler → Executor → Validator，单次线性收束
ExecutionLifecycleService 只追踪 submit/poll/complete/fail，没有"假设-实验-反馈"的概念
HarnessRuntime.boot() 组装的是静态组件图，不是迭代研究流程
Optimizer 的 mutation proposal 只作用于组件图版本，不作用于科学假设
各 extension（ABACUS/QCompute/AI4PDE 等）各自封装计算器运行，缺少统一的研究问题定义与迭代语义
目标：升级为面向科学研究闭环流程（science-research-loop-oriented），让 AI 能够完成完整闭环：
> 提出 idea/问题 → 思考方案并论证可行性 → 实施方案并实验 → 反馈迭代
核心灵感来自 trend.md 的关键主张："从模式匹配跨越到提出新假设"——不仅要解决问题，更要提出全新假设。
当前状态要点
组件链设计（src/metaharness/sdk/base.py）：declare_interface → activate → deactivate → export/import_state → suspend/resume → health_check，完备但纯面向计算任务
执行模型（src/metaharness/sdk/execution.py）：RunPlanProtocol → JobHandle → RunArtifactProtocol → ValidationOutcomeProtocol，单次执行生命周期，无迭代
优化器（src/metaharness/optimizer/）：action_space funnel + triggers，只作用于组件图 mutation，不作用于研究假设空间
AI4PDE wiki 已经有双生命周期（Team Runtime + Meta-Harness）和 Phase 0-8 的完整描述，是最佳设计参考，但尚未实现为通用 SDK 原语
Graph version + candidate + safety pipeline 已经具备回滚/观察窗口能力，可以被复用
提议变更
1. 新增科学研究闭环模型 ResearchLifecycle — DAG 而非线性链
在 src/metaharness/sdk/research.py 中定义科学研究闭环的一等公民模型。
关键设计修正：原提案用线性链 Question→Proposal→Plan→Evidence→Review→Decision，但真实研究有分支：一个问题可以产生多个假设，一个假设可以产生多个实验，一个实验的证据可以同时支持或反驳多个假设。因此模型应为 DAG，不是链。
核心实体及关系：
ResearchQuestion ──1:N──→ Hypothesis ──1:N──→ ExperimentPlan ──1:N──→ EvidenceBundle
     ↑                       ↑                       ↑                    │
     │ parent_question       │ parent_hypothesis      │                    │
     └───── derived_from ◄───┘ derived_from_evidence ◄┘                    │
                                             supports / refutes ◄────────┘
                                                        ↓
                                                   Review ──→ Decision
关键模型：
ResearchQuestion：question_id、statement、formal_spec（metric targets/constraints）、status（open/active/answered/stale）、parent_question_id（问题精化链）、created_from（benchmark_case_id 或 manual）
Hypothesis：hypothesis_id、question_id、statement、prediction（{"l2_error": {"relation": "lt", "value": 0.001}}）、status（proposed/testing/supported/refuted/superseded）、parent_hypothesis_id（精化链）、derived_from_evidence（启发此假设的 evidence_ids）
ExperimentPlan：plan_id、hypothesis_id、run_plan_ref（映射到 RunPlanProtocol.plan_id）、controls（固定参数）、variables（可变参数）、expected_outcome（假设预测值）
EvidenceBundle：bundle_id、experiment_plan_id、artifact_refs、metrics、supports（支持假设IDs）、refutes（反驳假设IDs）、confidence（0-1 统计置信度）
Review：review_id、evidence_bundle_id、reviewer_type（computational/human）、credibility_score、novelty_score、correctness_score、reproducibility_score、significance_score、recommendation（ADVANCE/REFINE/PIVOT/ABANDON）、reasoning
Decision：decision_id、review_id、decided_by（reviewer_agent 或 human:${user_id}）、decision、requires_approval（PIVOT/ABANDON 为 True）
与已有模型的桥接：
EvidenceBundle.metrics → ScoredEvidence.metrics（复用 core/models.py:159 的 metrics dict）
EvidenceBundle.confidence → ScoredEvidence.score（归一化置信度）
Decision.requires_approval → PromotionContext.approval_id + .mhe/approvals/ 机制
2. 新增 ResearchOrchestrator 作为闭环驱动器 — 带预算门控和人机协同
在 src/metaharness/core/research.py 中实现研究闭环驱动器，它是 HarnessRuntime 之上的一层编排。
关键设计修正：原提案缺少预算模型、人机协同门控和 ResearchStore 持久化。增加后架构更完整。
ResearchOrchestrator
  包含: HarnessRuntime（已有能力）
  新增:
    - store: ResearchStore（假设/证据/决策的持久化与查询）
    - budget: ResearchBudget（max_experiments, max_wall_clock, max_llm_cost）
    - brain_provider: BrainProvider（复用 core/brain.py:19，假设生成与评估）
    - reviewer: ReviewerProtocol | None（None = 简易 reviewer：成功即 ADVANCE，失败即 REFINE）
    - approval_required_for: set[Decision] = {PIVOT, ABANDON}
    - convergence_checker: TripleConvergence（复用 optimizer/convergence.py:40）
    - dead_end_detector: DeadEndDetector（复用 optimizer/convergence.py:116，跨假设复用）
核心循环（状态机驱动，不是单层 for 循环）：
async def pursue(self, question: ResearchQuestion, *, max_iterations: int = 10) -> ResearchConclusion:
    hypotheses = await self.generate_hypotheses(question)
    for iteration in range(max_iterations):
        if self.budget.exhausted:
            return ResearchConclusion.budget_exhausted(question)
        for hypothesis in self.active_hypotheses(question):
            if self.dead_end_detector.is_dead_end(hypothesis.hypothesis_id):
                hypothesis.status = "superseded"
                continue
            plan = await self.design_experiment(hypothesis)
            evidence = await self.run_experiment(plan)       # → HarnessRuntime.commit_graph()
            review = await self.review(evidence, baseline=self.sota_for(question))
            decision = await self.decide(review)
            if decision.requires_approval and not self.approval_granted(decision):
                decision = Decision.REFINE  # 降级为精化，不执行未授权的 PIVOT/ABANDON
            self.store.record_decision(decision)
            self.update_hypothesis_status(hypothesis, evidence)
        converged = self.convergence_checker.evaluate(
            fitness_history=self.fitness_history(question),
            budget_used=self.budget.used, safety_score=self.safety_score(question),
        )
        if converged.converged:
            break
    return await self.synthesize_conclusion(question)
人机协同门控：PIVOT 和 ABANDON 是战略性决策，可能需要人类批准。利用已有 .mhe/approvals/*.json 和 PromotionContext.actor 机制。
意外结果的可复现性门控（measure-twice gate）：当实验结果与预测偏差过大时，可选重跑一次以确认。
3. 新增 HypothesisActionSpace — 独立于组件图 ActionSpaceFunnel
关键设计修正：原提案将假设搜索作为 optimizer ActionSpaceFunnel 的扩展，但假设与图边是不同实体类型——ContractPruner 无法剪枝假设。应独立实现 HypothesisActionSpace。
当前 optimizer 的 action_space + trigger 系统保留不动（组件图 mutation 仍需要）。在其旁新增假设空间的动作空间：
HypothesisActionSpace（独立于 ActionSpaceFunnel）：
GENERATE：给定 ResearchQuestion + 现有证据，提出新假设（LLM 调用，不是图枚举）
REFINE：给定被反驳的假设 + 证据，提出精化版（更窄范围、调整预测值）
SELECT：给定多个活跃假设 + 预算，选择下一个测试（bandit 问题——复用 optimizer/search/bayesian.py）
COMBINE：给定两个被支持的假设，提出综合
可复用 core/brain.py:19 的 BrainProvider 协议——propose() 和 evaluate() 是正确接口，只是动作类型不同
可复用 optimizer/fitness.py 的 FitnessEvaluator，但需新增假设质量评估器（预测特异性、可测试性、相对于 SOTA 的新颖性）
HypothesisTrigger：当 evidence 不支撑当前假设时触发假设修订，走独立的状态机而非 candidate graph 的 safety 验证流
双轨并行：假设流经自己的状态机（proposed→testing→supported/refuted/superseded），只有当假设变为具体实验提议时才可能产生 CandidateRecord。
4. 新增 Reviewer Agent 协议 — 五维评估 + baseline 对比
在 src/metaharness/sdk/review.py 中定义 reviewer agent 的协议。
关键设计修正：原提案只有 credibility/novelty/reproducibility 三个维度。科学计算还需要 correctness（数学/数值一致性）和 significance（效应量相对噪声）。此外，新颖性没有参照点是无意义的——必须传入 baseline。
class ReviewDimensions(BaseModel):
    credibility: float      # 是否可信？（方法论、统计严谨性）
    novelty: float          # 相对于 SOTA baseline 是否新颖？
    correctness: float      # 数学/数值是否正确？（数值一致性、单位检查）
    reproducibility: float  # 重跑是否产生相同结果？（方差、稳定性）
    significance: float    # 是否改变认知？（效应量相对噪声）
@runtime_checkable
class ReviewerProtocol(Protocol):
    def review(
        self,
        experiment: ExperimentPlan,
        evidence: EvidenceBundle,
        baseline: EvidenceBundle | None,  # SOTA baseline for comparison
        prior_reviews: list[Review],      # context from earlier iterations
    ) -> Review: ...
    def compare(
        self,
        evidence_a: EvidenceBundle,
        evidence_b: EvidenceBundle,
    ) -> ReviewDimensions: ...  # head-to-head comparison
class ResearchPaper(BaseModel):
    question: ResearchQuestion
    hypotheses: list[Hypothesis]
    evidence: list[EvidenceBundle]
    reviews: list[Review]
    iteration_trace: list[IterationRecord]  # 完整迭代历史
class ReviewVerdict(BaseModel):
    accepted: bool
    dimensions: ReviewDimensions
    strengths: list[str]
    weaknesses: list[str]
    required_revisions: list[str]
baseline 参数至关重要——新颖性没有参照点是无意义的。Benchmark 集成提供 baseline：extension lane 结果（确定性编译器路径）是天然 baseline。
SOTA Baseline Registry（新增最小组件）：
class SOTABaseline(BaseModel):
    baseline_id: str
    research_question_id: str
    metric_values: dict       # {"l2_error": 0.002487, ...}
    source: str               # "benchmark:fealpy-pde:poisson-2d-numpy:extension"
    timestamp: datetime
Extension lane（确定性、零 LLM）是每个 FEALPy case 的天然 SOTA baseline——benchmark runner 已经产出这些数值，只需持久化并打标签。
5. Benchmark 选型与集成策略 — 统一 MetricSchema
选择已公开但尚未解决的课题作为 benchmark：
物理领域：未解决的材料性质预测（如高熵合金相稳定性）
量子计算：量子纠错码的参数优化
PDE 领域：高雷诺数湍流的 surrogate model 精度突破
Benchmark 以 ResearchQuestion 形式注册到 question_pool，附带：
ground_truth_available: bool（部分问题可能有实验对照数据）
baseline_results: list[SOTABaseline]（已知方法的当前 SOTA）
novelty_threshold: float（需超越 baseline 多少才算创新）
关键新增：各 benchmark suite 有不同的 metric schema。Poisson 有 l2_error/h1_error，Nektar 有不同字段，QCompute 有 Hamiltonian eigenvalues。ResearchQuestion 需要统一表示。新增 MetricSchema：
class MetricSchema(BaseModel):
    name: str                    # "l2_error"
    relation: Literal["lt", "gt", "approx"]  # "lt" = lower is better
    target: float | None         # None = exploratory
    unit: str                    # "" (dimensionless), "s", etc.
    is_primary: bool             # primary metrics drive decisions
这让 ResearchOrchestrator 能跨 suite 比较结果："reducing l2_error below 0.001" 是有意义的假设，无论哪个 PDE solver 产出这个数值。
Benchmark runner 的 summary.json 已经捕获 metrics/status/preflight_status/failure_category。给 BenchmarkCaseSpec 添加 metric_schema 字段（或从 expected_metrics + 新 schema registry 派生）即可闭环。
6. 与已有架构的衔接 — 双轨设计 + 修正桥接点
保留不动的：
HarnessRuntime、ConnectionEngine、ComponentRegistry、SafetyPipeline、graph version + candidate 流
各 extension 的 gateway/probe/compiler/executor/validator 组件链
ExecutionLifecycleService 和 ExecutionEvidenceRecorder
Optimizer 的组件图 mutation 能力（ActionSpaceFunnel + LayeredTriggerSystem）
新增但不侵入的：
ResearchOrchestrator 包裹 HarnessRuntime，不修改 boot 流程
ResearchLifecycle 模型独立于 ComponentPhase，但 evidence 可桥接到已有 ArtifactSnapshotStore
ReviewerProtocol 协议独立于 HarnessComponent，但可注册为 component 参与图版本演化
HypothesisActionSpace 独立于 ActionSpaceFunnel，但复用 BrainProvider 和 FitnessEvaluator
桥接点（修正后）：
ExperimentPlan.run_plan_ref → RunPlanProtocol.plan_id：研究层的实验计划向下转化为执行层的运行计划。Good fit——ExperimentPlan 扩展 RunPlanProtocol 的字段而非替换
EvidenceBundle → ScoredEvidence（不是 ArtifactSnapshot）：EvidenceBundle 需要数值 metrics + provenance，不是图拓扑。core/models.py:159 的 ScoredEvidence 才是正确映射，它携带 score、metrics、safety_score、budget、convergence、evidence_refs
ResearchReview → SessionStore：review 事件进入已有 session 体系
不映射 HypothesisCandidate → CandidateRecord：假设是关于世界的声明，不是图编辑。假设走独立状态机（proposed→testing→supported/refuted/superseded），只在假设变为具体实验提议时才可能产生 CandidateRecord
唯一需要侵入的地方：ExecutionLifecycleService.run() 是单次执行，没有"这是研究问题 RQ-1 的实验 E3 的第 3 次迭代"的概念。解决方案（Option A，零侵入）：ResearchOrchestrator 包裹 ExecutionLifecycleService，将 iteration metadata 加入 session_id 命名空间，并通过 EventBus 订阅 lifecycle events。
可复用的已有组件：
TripleConvergence（optimizer/convergence.py:40）：研究收敛判断
DeadEndDetector（optimizer/convergence.py:116）：假设无改进检测
BrainProvider（core/brain.py:19）：假设生成与评估
NonMarkovianGuard（optimizer/convergence.py:147）：研究路径的非马尔可夫性提醒
ScoredEvidence（core/models.py:159）：证据桥接
BudgetState（core/models.py:142）：预算消费追踪
7. 研究闭环的完整时序
ResearchOrchestrator.research_loop(question)
  │
  ├─ Phase 1: PROPOSE
  │   └─ question → proposal_evaluator → ResearchProposal
  │
  ├─ Phase 2: PLAN
  │   └─ proposal → method_router → ExperimentPlan
  │      └─ ExperimentPlan 绑定 extension family + solver config
  │
  ├─ Phase 3: EXPERIMENT  (可多轮)
  │   └─ ExperimentPlan → HarnessRuntime.commit_graph() → ExecutionLifecycleService.run()
  │      → RunArtifact → EvidenceBundle
  │
  ├─ Phase 4: REVIEW
  │   └─ EvidenceBundle → ReviewerAgent.evaluate() → ResearchReview
  │
  ├─ Phase 5: DECIDE
  │   └─ ResearchReview → decision_engine → ADVANCE | REFINE | PIVOT | ABANDON
  │
  │   ├─ REFINE → 回到 Phase 2（调参/换方法）
  │   ├─ PIVOT → 回到 Phase 1（换假设）
  │   ├─ ABANDON → 输出失败分析报告
  │   └─ ADVANCE → Phase 6
  │
  └─ Phase 6: SYNTHESIZE
      └─ question + proposal + evidence + review → ResearchPaper
         → ReviewerAgent.evaluate(paper) → ReviewVerdict
         → 若 verdict.accepted → 沉淀为知识资产
         → 若 verdict 要求 revision → 回到 Phase 3 补充实验
8. "爱因斯坦测试"的设计考量
trend.md 提到的核心挑战：如果给 AI 输入 1901 年之前的所有物理知识，它能否独立推导出狭义相对论？
这要求架构支持：
知识边界表达：ResearchQuestion.formal_spec 明确标记哪些是已知、哪些是未知/gap
反事实推理：PIVOT 决策意味着 AI 需要跳出当前假设框架；HypothesisActionSpace.COMBINE 支持假设综合
长期记忆：跨 iteration 的知识积累，ResearchStore + DAG lineage 追踪持久化迭代历史
假设原创性评估：ReviewDimensions.novelty + SOTABaseline 对比已有 baseline，但最终需对比已有文献/知识库
这些能力在初期可以简化实现，但模型层必须预留。
9. 缺失项补充
原提案遗漏的六个关键项：
ResearchStore（src/metaharness/research/store.py）：假设/证据/决策的持久化与查询接口——list_hypotheses(question_id)、evidence_for(hypothesis_id)、decision_history(question_id)。复用 provenance/ 的 Merkle tree 和 audit graph，不另建并行 lineage tracker
ResearchBudget 模型：max_experiments、max_wall_clock、max_llm_cost。复用 core/models.py:142 的 BudgetState，在 ResearchOrchestrator 每轮迭代前检查
人机协同门控：PIVOT/ABANDON 需人类批准。复用 .mhe/approvals/*.json 和 PromotionContext.actor
负结果处理：发布负结果防止重复死胡同；跨 ResearchQuestion 的死胡同交叉检测（扩展现有 DeadEndDetector）；负结果聚合（3 个实验在同一 mesh 上不收敛 vs 3 个无关失败，含义不同）
可复现性门控（measure-twice gate）：当实验结果与预测偏差过大时，可选重跑一次以确认
实验版本与 lineage DAG：如果 E3 继承自 H2 而 H2 是 H1 在 E1/E2 证据后的精化，lineage 必须显式。复用 provenance/ 的 RelationKind
实施优先级（调整后）
原序 models→orchestrator→reviewer→optimizer→benchmark 是从简到难，但遗漏了数据基础和连接验证。调整为：
P0 - 模型层：ResearchLifecycle DAG 模型（ResearchQuestion/Hypothesis/ExperimentPlan/EvidenceBundle/Review/Decision）
P0 - 存储层：ResearchStore + lineage 追踪（扩展 provenance/），不建并行 tracker
P0 - 连接层：桥接 mappers（ExperimentPlan↔RunPlanProtocol, EvidenceBundle↔ScoredEvidence），尽早验证 wrapping 设计
P1 - Benchmark 集成：开放课题→ResearchQuestion + MetricSchema + SOTABaseline，让 orchestrator 有真实数据可测
P1 - 驱动器：ResearchOrchestrator 核心循环 + 预算门控 + 人机协同，有了 models/store/mappers/真实数据后才构建
P1 - Reviewer 协议：ReviewerProtocol + ReviewDimensions + SOTABaseline，增强 orchestrator 决策质量但 orchestrator 可先用简易 reviewer 运转
P2 - 假设动作空间：HypothesisActionSpace（独立于 ActionSpaceFunnel），最高风险组件，等 1-6 稳定后再构建
P2 - 知识沉淀：负结果处理 + 可复现性门控 + 文献对比能力
优先级调整理由：
Models 第一：一切依赖它，零风险，快速反馈
Store 第二：数据基础，没有它 orchestrator 无法在迭代间持久化状态
Connection layer 第三（不是最后）：尽早验证 wrapping 设计。如果 mappers 不工作，orchestrator 和 hypothesis optimizer 需要重设计——在构建它们之前发现这个问题
Benchmark 第四：产出 orchestrator 将消费的真实数据，可用真实 benchmark run 测试而非 mock
Orchestrator 第五：此时有 models、storage、mappers、真实数据
Reviewer 第六：增强决策质量，但 orchestrator 可以用简易 reviewer 运转（成功即 ADVANCE，失败即 REFINE）
HypothesisOptimizer 最后：最高风险组件，依赖前面所有稳定，构建早了等于对着会变的接口建
