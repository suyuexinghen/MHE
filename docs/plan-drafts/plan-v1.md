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
1. 新增科学研究生周期模型 ResearchLifecycle
在 src/metaharness/sdk/research.py 中定义科学研究闭环的一等公民模型：
ResearchQuestion        # 科学问题/假设（源自 idea 或文献 gap）
  → ResearchProposal    # 方案论证（可行性、方法选择、预算估算）
    → ExperimentPlan     # 实验计划（绑定 solver/extension、参数空间）
      → ExperimentRun[]  # 一到多次实验执行
        → EvidenceBundle # 实验证据
          → ResearchReview # AI reviewer 评估可信度与创新性
            → Decision: ADVANCE | REFINE | PIVOT | ABANDON
关键模型：
ResearchQuestion：含 domain、hypothesis、prior_state（已知/未知）、novelty_claim
ResearchProposal：含 method_rationale、feasibility_args、expected_outcome、risk_assessment
ExperimentPlan：绑定 extension family、参数空间、baseline 对照策略
ResearchReview：含 credibility_score、novelty_score、reproducibility_evidence、limitations
ResearchDecision：ADVANCE（进入下一阶段/论文化）、REFINE（调参/换方法重试）、PIVOT（换假设）、ABANDON（放弃）
2. 新增 ResearchOrchestrator 作为闭环驱动器
在 src/metaharness/core/research.py 中实现研究闭环驱动器，它是 HarnessRuntime 之上的一层编排：
ResearchOrchestrator
  包含: HarnessRuntime（已有能力）
  新增:
    - question_pool: 管理 ResearchQuestion 的提出与淘汰
    - proposal_evaluator: 论证可行性（可调用 LLM 或规则引擎）
    - experiment_scheduler: 把 ExperimentPlan 转成 RunPlanProtocol 并交给已有 executor
    - review_agent: 评估 EvidenceBundle 的可信度与创新性
    - decision_engine: 基于 review 结果决定 ADVANCE/REFINE/PIVOT/ABANDON
    - iteration_budget: 约束最大迭代次数和资源消耗
``n
核心循环：
```python
async def research_loop(self, question: ResearchQuestion) -> ResearchOutcome:
    proposal = await self.propose(question)
    for iteration in range(self.iteration_budget):
        plan = await self.plan_experiment(proposal)
        evidence = await self.run_experiment(plan)
        review = await self.review(evidence)
        decision = await self.decide(review)
        if decision == ResearchDecision.ADVANCE:
            return await self.synthesize_paper(question, proposal, evidence, review)
        elif decision == ResearchDecision.REFINE:
            proposal = await self.refine(proposal, review)
        elif decision == ResearchDecision.PIVOT:
            question = await self.pivot(question, review)
            proposal = await self.propose(question)
        elif decision == ResearchDecision.ABANDON:
            return ResearchOutcome.abandoned(question, review)
    return ResearchOutcome.budget_exhausted(question)
3. 扩展 Optimizer 为 HypothesisOptimizer
当前 optimizer 的 action_space + trigger 系统保留（组件图 mutation 仍需要），在其上新增假设空间的优化层：
HypothesisSpace：当前活跃假设的搜索空间表示，含参数化假设模板
HypothesisTrigger：当 evidence 不支撑当前假设时触发假设修订
HypothesisCandidate：新假设候选，走类似 candidate graph 的 safety 验证流
BayesianHypothesisSearch（复用 optimizer/search/bayesian.py）：用贝叶斯优化搜索假设参数空间
4. 新增 Reviewer Agent 协议
在 src/metaharness/sdk/review.py 中定义 reviewer agent 的协议：
class ReviewCriteria(BaseModel):
    credibility_weight: float    # 可信度权重
    novelty_weight: float        # 创新性权重
    reproducibility_weight: float # 可复现性权重
class ResearchPaper(BaseModel):
    question: ResearchQuestion
    proposal: ResearchProposal
    evidence: list[EvidenceBundle]
    review: ResearchReview
    iteration_trace: list[IterationRecord]  # 完整迭代历史
@runtime_checkable
class ReviewerAgent(Protocol):
    async def evaluate(self, paper: ResearchPaper, criteria: ReviewCriteria) -> ReviewVerdict:
        """评估论文可信度与创新性"""
class ReviewVerdict(BaseModel):
    accepted: bool
    credibility_score: float
    novelty_score: float
    reproducibility_score: float
    strengths: list[str]
    weaknesses: list[str]
    required_revisions: list[str]
5. Benchmark 选型与集成策略
选择已公开但尚未解决的课题作为 benchmark：
物理领域：未解决的材料性质预测（如高熵合金相稳定性）
量子计算：量子纠错码的参数优化
PDE 领域：高雷诺数湍流的 surrogate model 精度突破
Benchmark 以 ResearchQuestion 形式注册到 question_pool，附带：
ground_truth_available: bool（部分问题可能有实验对照数据）
baseline_results: list[BaselineResult]（已知方法的当前 SOTA）
novelty_threshold: float（需超越 baseline 多少才算创新）
6. 与已有架构的衔接
保留不动的：
HarnessRuntime、ConnectionEngine、ComponentRegistry、SafetyPipeline、graph version + candidate 流
各 extension 的 gateway/probe/compiler/executor/validator 组件链
ExecutionLifecycleService 和 ExecutionEvidenceRecorder
Optimizer 的组件图 mutation 能力
新增但不侵入的：
ResearchOrchestrator 包裹 HarnessRuntime，不修改 boot 流程
ResearchLifecycle 模型独立于 ComponentPhase，但 evidence 可桥接到已有 ArtifactSnapshotStore
ReviewerAgent 协议独立于 HarnessComponent，但可注册为 component 参与图版本演化
HypothesisOptimizer 继承 optimizer 的 funnel/trigger 模式，扩展了搜索空间
桥接点：
ExperimentPlan → RunPlanProtocol：研究层的实验计划向下转化为执行层的运行计划
EvidenceBundle → ArtifactSnapshot：研究层的证据向上桥接到已有的溯源链
ResearchReview.session_events → SessionStore：review 事件进入已有 session 体系
HypothesisCandidate → CandidateRecord：假设候选可进入已有的 candidate graph 验证流
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
知识边界表达：ResearchQuestion.prior_state 明确标记哪些是已知、哪些是未知/gap
反事实推理：PIVOT 决策意味着 AI 需要跳出当前假设框架
长期记忆：跨 iteration 的知识积累，需要 ResearchTrace 持久化迭代历史
假设原创性评估：novelty_score 需要对比已有文献/知识库，不只是对比 baseline 数值
这些能力在初期可以简化实现，但模型层必须预留。
实施优先级
P0 - 模型层：ResearchLifecycle 模型（ResearchQuestion/Proposal/Plan/Review/Decision）
P0 - 驱动器：ResearchOrchestrator 核心循环 + 桥接到已有 HarnessRuntime
P1 - Reviewer 协议：ReviewerAgent + ResearchPaper + ReviewVerdict
P1 - 假设优化器：HypothesisOptimizer 扩展 optimizer
P2 - Benchmark 集成：开放课题注册 + baseline 对比
P2 - 知识沉淀：ResearchTrace 持久化 + 文献对比能力
