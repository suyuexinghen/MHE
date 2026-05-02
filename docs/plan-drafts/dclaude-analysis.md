 You are a senior software architect reviewing an architecture upgrade plan for MHE (Meta-Harness Engine).                                                                                                   
  CURRENT PROBLEMS:                                                                                                                                                                                           
  CURRENT PROBLEMS:y, single-run linear flow (Gateway→Probe→Compiler→Executor→Validator)                                                                                                                      
  - Computation-only, single-run linear flow (Gateway→Probe→Compiler→Executor→Validator)                                                                                                                      
  - No iteration semantics in ExecutionLifecycleServiceot scientific hypotheses                                                                                                                               
  - Optimizer only acts on component graph mutations, not scientific hypotheses                                                                                                                               
  - No unified research problem definition across extensions                                                                                                                                                  
  GOAL: Upgrade to science-research-loop-oriented: idea → proposal → experiment → feedback → iteration                                                                                                        
  GOAL: Upgrade to science-research-loop-oriented: idea → proposal → experiment → feedback → iteration                                                                                                        
  PROPOSED CHANGES:                                                                                                                                                                                           
  PROPOSED CHANGES:cle models (sdk/research.py): ResearchQuestion→Proposal→ExperimentPlan→Evidence→Revi1. ResearchLifecycle models (sdk/research.py):                                                         
  ResearchQuestion→Proposal→ExperimentPlan→Evidence→Review→Decision(ADVANCE/REFINE/PIVOT/ABANDON)): wraps HarnessRuntime, drives iteration loop                                                               
  2. ResearchOrchestrator (core/research.py): wraps HarnessRuntime, drives iteration loop                                                                                                                     
  3. HypothesisOptimizer: extend action_space+trigger to hypothesis searchn                                                                                                                                   
  4. ReviewerAgent protocol (sdk/review.py): credibility/novelty evaluation SOTA                                                                                                                              
  5. Benchmark integration: open problems as ResearchQuestion with baseline SOTARuntime                                                                                                                       
  6. Architecture connection: new layer wraps without intruding existing HarnessRuntime                                                                                                                       
  Connection points: ExperimentPlan→RunPlanProtocol, EvidenceBundle→ArtifactSnapshot, HypothesisCandidaConnection points: ExperimentPlan→RunPlanProtocol, EvidenceBundle→ArtifactSnapshot,                    
  HypothesisCandidate→CandidateRecord                                                                                                                                                                         
  Please review and provide:                                                                                                                                                                                  
  Please review and provide: of the wrapping-without-intrusion design                                                                                                                                         
  1. Architectural soundness of the wrapping-without-intrusion design                                                                                                                                         
  2. Completeness - what is missing                                                                                                                                                                           
  3. Implementation risk ranking                                                                                                                                                                              
  4. Priority order adjustmentseach component                                                                                                                                                                 
  5. Specific improvements for each component                                                                                                                                                                 

● Let me first understand the current architecture before reviewing the upgrade plan.
         
● Explore(Explore MHE architecture)                                                                                                                                                                           
  ⎿  Done (42 tool uses · 102.6k tokens · 2m 43s)                                                                
  (ctrl+o to expand)                                                                                                                                                                                          
                                                                                                                                                                                                              
● Now I have a thorough understanding of the current architecture. Let me provide the review.                                                                                                                 
                                                                                                                                                                                                              
  ---                                                                                                                                                                                                         
  Architecture Review: MHE Science Research Loop Upgrade                                                                                                                                                      
                                                                                                                                                                                                              
  1. Architectural Soundness — Wrapping-Without-Intrusion                                                                                                                                                     
                                                                                                                                                                                                              
  Verdict: Sound in principle, but the connection points need refinement.                                                                                                                                     
                                                                                                                                                                                                              
  The wrapping strategy is the right call. HarnessRuntime is a thick orchestrator (~1100 lines) with a well-defined surface: boot(), commit_graph(), ingest_candidate_record(), register_shadow_runners(), and
   the EventBus. Touching its internals would create regression risk across all extension families (FEALPy, Nektar, pyCFD, QCompute/ABACUS).                                                                  
                                                                                                                                                                                                              
  The proposed connection points are well-chosen:                                                                                                                                                             
                                               
  ┌────────────────────────────┬────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────┐    
  │    Proposal Connection     │                              MHE Existing                              │                                              Fit                                               │ 
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤    
  │ ExperimentPlan →           │ RunPlanProtocol is a @runtime_checkable Protocol in                    │                                                                                                │ 
  │ RunPlanProtocol            │ sdk/execution.py:74 with plan_id, experiment_ref, target_backend,      │ Good. ExperimentPlan extends these fields rather than replacing them.                          │    
  │                            │ execution_params                                                       │                                                                                                │    
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ EvidenceBundle →           │ GraphSnapshot in core/models.py:126 carries graph_version, nodes,      │ Partial mismatch. EvidenceBundle needs numerical metrics + provenance, not graph topology. The │    
  │ ArtifactSnapshot           │ edges                                                                  │  closer match is ScoredEvidence (core/models.py:159) which carries score, metrics,             │
  │                            │                                                                        │ evidence_refs.                                                                                 │    
  ├────────────────────────────┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────┤
  │ HypothesisCandidate →      │ CandidateRecord in core/graph_versions.py:28 tracks candidate_id,      │ Strained. CandidateRecord is graph-mutation-specific. A hypothesis is a different entity type  │    
  │ CandidateRecord            │ snapshot, report, promoted, deferred                                   │ — it's a claim about the world, not a graph edit.                                              │
  └────────────────────────────┴────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────┘    
                                                
  Key risk: CandidateRecord and PromotionContext are deeply coupled to graph topology semantics. Mapping a scientific hypothesis ("increasing mesh resolution reduces L2 error by O(h²)") onto a graph        
  mutation is an abstraction mismatch. I recommend a parallel track, not a mapping: let hypotheses flow through their own state machine that emits CandidateRecords only at the point where a hypothesis
  becomes a concrete experiment proposal.                                                                                                                                                                     
                                                
  The one place wrapping will intrude                                                                                                                                                                         
   
  ExecutionLifecycleService.run() (core/execution.py:66) is single-run: it submits a plan, polls, records events, returns. There is no concept of "this run is iteration 3 of experiment 7 within research    
  question RQ-1." The iteration context must be injected. This requires either:
                                                                                                                                                                                                              
  - Option A (preferred): ResearchOrchestrator wraps ExecutionLifecycleService, adding iteration metadata to the session_id namespace and subscribing to lifecycle events via EventBus. Zero intrusion.       
  - Option B: Add optional iteration_context parameter to ExecutionLifecycleService.run(). Low intrusion, backward-compatible.
                                                                                                                                                                                                              
  ---                                                                                                                                                                                                         
  2. Completeness — What Is Missing                                                                                                                                                                           
                                                                                                                                                                                                              
  2.1 Experiment versioning and lineage         
                                                                                                                                                                                                              
  The proposal has ResearchQuestion → Proposal → ExperimentPlan → Evidence → Review → Decision, but no DAG linking these. If experiment E3 was derived from hypothesis H2 which was a refinement of H1 after  
  evidence from E1 and E2, that lineage must be explicit. Without it, the reviewer cannot assess whether a negative result disproves the parent hypothesis. The provenance subsystem (provenance/) has Merkle 
  trees and audit graphs — reuse these rather than building a parallel lineage tracker.                                                                                                                       
                                                
  2.2 Research asset store                                                                                                                                                                                    
   
  ArtifactStore (provenance/artifact_store.py) stores run artifacts. A research loop also needs to store: hypotheses (with status), experiment plans, review decisions, and the evidence-to-hypothesis        
  mapping. This is not a file-system concern — it's a structured query concern. The proposal should include a ResearchStore (or extend ArtifactStore) with:
  - list_hypotheses(question_id) → list[Hypothesis]                                                                                                                                                           
  - evidence_for(hypothesis_id) → list[EvidenceBundle]                                                                                                                                                        
  - decision_history(question_id) → list[Decision]    
                                                                                                                                                                                                              
  2.3 Resource budget awareness                                                                                                                                                                               
                                                                                                                                                                                                              
  Scientific iteration loops consume real resources (compute time, API costs, human attention). The proposal has no budget model. MHE already has ResourceQuota in sdk/runtime.py and BUDGET_EXHAUSTED in     
  optimizer/convergence.py. The ResearchOrchestrator should accept a ResearchBudget (max experiments, max wall-clock, max LLM cost) and check it before each iteration. Without this, an autonomous loop can  
  burn resources indefinitely.                                                                                                                                                                                
                                                
  2.4 Human-in-the-loop gates                                                                                                                                                                                 
   
  The proposal's Decision enum has ADVANCE/REFINE/PIVOT/ABANDON. But who makes these decisions? The ReviewerAgent protocol evaluates credibility/novelty — that's computational. But PIVOT and ABANDON are    
  strategic decisions that may need human approval. MHE's approval manifest system (.mhe/approvals/*.json) and PromotionContext.actor field already model gated promotions. The research loop should integrate
   with this: ReviewerAgent produces a recommendation, and for PIVOT/ABANDON, the orchestrator checks the approval manifest before acting.                                                                    
                                                
  2.5 Negative result handling                                                                                                                                                                                
   
  The proposal's decision flow implicitly handles negative results (via REFINE/PIVOT), but there's no explicit mechanism for:                                                                                 
  - Publishing negative results as evidence (prevents duplicate dead-ends)
  - Dead-end detection across research questions (hypothesis H for question Q1 may be proven dead by evidence from Q2)                                                                                        
  - Negative result aggregation (3 experiments all failing to converge on the same mesh tells you something different than 3 unrelated failures)
                                                                                                                                                                                                              
  MHE's DeadEndDetector (optimizer/convergence.py:115) tracks per-path improvement but doesn't cross-pollinate between paths. This is worth extending.                                                        
                                                                                                                                                                                                              
  2.6 Experiment reproducibility                                                                                                                                                                              
                                                                                                                                                                                                              
  The proposal generates ExperimentPlan but doesn't address whether re-running the same plan produces the same result. The benchmark comparison framework (benchmark_drivers/compare.py) already computes     
  repeat summary statistics (IQR, pass rate, flaky flags). The ResearchOrchestrator should optionally re-run experiments that produce surprising results (large deviation from predicted outcome) before
  accepting them as evidence. This is a "measure-twice" gate — cheap to add, high value for scientific credibility.                                                                                           
                                                
  ---                                                                                                                                                                                                         
  3. Implementation Risk Ranking
                                                                                                                                                                                                              
  Scale: Low (well-understood, bounded scope), Medium (integration complexity, may need refactoring), High (uncertain design, broad blast radius, or depends on unresolved Medium items).
                                                                                                                                                                                                              
  ┌─────┬──────────────────────────────┬────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐   
  │  #  │          Component           │  Risk  │                                                                        Rationale                                                                        │   
  ├─────┼──────────────────────────────┼────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
  │ 1   │ ResearchLifecycle models     │ Low    │ Pure Pydantic models. No runtime coupling. Can be written and tested in isolation.                                                                      │
  │     │ (sdk/research.py)            │        │                                                                                                                                                         │   
  ├─────┼──────────────────────────────┼────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
  │ 2   │ ResearchOrchestrator         │ Medium │ Wraps HarnessRuntime — the wrapping surface is stable but the iteration loop must handle: partial failure (experiment 3 of 5 crashes), cancellation,    │   
  │     │ (core/research.py)           │        │ and budget exhaustion. State machine design is the hard part, not the MHE integration.                                                                  │   
  ├─────┼──────────────────────────────┼────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
  │     │                              │        │ The current optimizer's action space is graph edges. Extending to hypothesis search means defining a new action type (GENERATE_HYPOTHESIS,              │
  │ 3   │ HypothesisOptimizer          │ High   │ REFINE_HYPOTHESIS, TEST_HYPOTHESIS) with an entirely different legality model. The ContractPruner can't prune hypotheses. This is the riskiest          │   
  │     │                              │        │ component — it's not an extension, it's a parallel optimizer with different semantics.                                                                  │
  ├─────┼──────────────────────────────┼────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
  │ 4   │ ReviewerAgent protocol       │ Low    │ A Protocol class with evaluate(proposal, evidence) → Review. Clean interface, no MHE coupling. The LLM integration (prompting Claude to review) is the  │
  │     │ (sdk/review.py)              │        │ implementation risk, not the architectural integration.                                                                                                 │   
  ├─────┼──────────────────────────────┼────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
  │     │                              │        │ Existing benchmark runners have their own summary models. Mapping BenchmarkCaseSpec → ResearchQuestion and BenchmarkSummary → EvidenceBundle requires   │   
  │ 5   │ Benchmark integration        │ Medium │ agreement on metric schemas. The FEALPy 3-repeat infrastructure already produces the right data shape — the risk is in generalizing across              │   
  │     │                              │        │ Nektar/pyCFD/QCompute which have different metric schemas.                                                                                              │
  ├─────┼──────────────────────────────┼────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤   
  │ 6   │ Architecture integration     │ Medium │ The connection points work, but the dual-track concern (hypotheses vs. graph mutations) means the integration layer has non-trivial translation logic.  │
  │     │ layer                        │        │ Risk is moderate because the translation is well-bounded — it's a mapper, not an orchestrator.                                                          │   
  └─────┴──────────────────────────────┴────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                                                                                                                                              
  ---                                                                                                                                                                                                         
  4. Priority Order Adjustment                 
                                                                                                                                                                                                              
  The current order is: models → orchestrator → hypothesis optimizer → reviewer → benchmark integration → architecture connection.
                                                                                                                                                                                                              
  Recommended order:                                                                                                                                                                                          
                                                                                                                                                                                                              
  1. ResearchLifecycle models (sdk/research.py)                                                                                                                                                               
  2. ResearchStore + lineage tracking (extend provenance/)                                                                                                                                                    
  3. Architecture connection layer (mappers: ExperimentPlan↔RunPlan, Evidence↔ScoredEvidence)                                                                                                                 
  4. Benchmark integration (open problems → ResearchQuestion)                                                                                                                                                 
  5. ResearchOrchestrator (core/research.py) with budget gating                                                                                                                                               
  6. ReviewerAgent protocol (sdk/review.py) + human-in-the-loop gates                                                                                                                                         
  7. HypothesisOptimizer (LAST — highest risk, depends on 1-6 being stable)                                                                                                                                   
                                                                                                                                                                                                              
  Rationale for the reorder:                                                                                                                                                                                  
                                                                                                                                                                                                              
  - Models first because everything depends on them. No risk, fast feedback.                                                                                                                                  
  - ResearchStore second because it's the data foundation. Without it, the orchestrator has nowhere to persist state between iterations.
  - Connection layer third (not last) because it validates the wrapping design early. If the mappers don't work, the orchestrator and hypothesis optimizer need redesign. Find this out before building them. 
  - Benchmark integration fourth because it produces the concrete data the orchestrator will consume. Having real ResearchQuestion instances and real EvidenceBundle outputs lets you test the orchestrator   
  against actual benchmark runs rather than mocks.                                                                                                                                                            
  - Orchestrator fifth — now it has models, storage, mappers, and real data to work with.                                                                                                                     
  - Reviewer sixth — it enhances the orchestrator's decision quality but the orchestrator can function with a trivial reviewer (always ADVANCE on success, REFINE on failure).                                
  - HypothesisOptimizer last — it's the highest-risk component and depends on everything else being stable. Building it early risks building against interfaces that shift.                                   
                                                                                                                                                                                                              
  ---                                                                                                                                                                                                         
  5. Specific Component Improvements                                                                                                                                                                          
                                                                                                                                                                                                              
  5.1 ResearchLifecycle models (sdk/research.py)
                                                                                                                                                                                                              
  Problem: The proposed linear chain Question → Proposal → Plan → Evidence → Review → Decision is too rigid. Real research has branching: one question spawns multiple hypotheses, one hypothesis spawns      
  multiple experiments, one experiment can produce evidence relevant to multiple hypotheses.                                                                                                                  
                                                                                                                                                                                                              
  Recommendation: Model as a DAG, not a chain:                                                                                                                                                                
                                               
  class ResearchQuestion(BaseModel):                                                                                                                                                                          
      question_id: str                                                                                                                                                                                        
      statement: str          # human-readable                                                                                                                                                                
      formal_spec: dict       # machine-readable (metric targets, constraints)                                                                                                                                
      status: Literal["open", "active", "answered", "stale"]                                                                                                                                                  
      parent_question_id: str | None  # for question refinement chains                                                                                                                                        
      created_from: str | None  # benchmark_case_id or manual                                                                                                                                                 
                                                                                                                                                                                                              
  class Hypothesis(BaseModel):                                                                                                                                                                                
      hypothesis_id: str                                                                                                                                                                                      
      question_id: str                                                                                                                                                                                        
      statement: str          # "Increasing mesh resolution reduces L2 error by O(h²)"                                                                                                                        
      prediction: dict        # {"l2_error": {"relation": "lt", "value": 0.001}}                                                                                                                              
      status: Literal["proposed", "testing", "supported", "refuted", "superseded"]                                                                                                                            
      parent_hypothesis_id: str | None  # for refinement chains                                                                                                                                               
      derived_from_evidence: list[str]  # evidence_ids that inspired this hypothesis                                                                                                                          
                                                                                                                                                                                                              
  class ExperimentPlan(BaseModel):                                                                                                                                                                            
      plan_id: str                                                                                                                                                                                            
      hypothesis_id: str                                                                                                                                                                                      
      run_plan_ref: str       # maps to RunPlanProtocol.plan_id                                                                                                                                               
      controls: dict           # fixed parameters                                                                                                                                                             
      variables: dict          # what we're varying                                                                                                                                                           
      expected_outcome: dict   # what the hypothesis predicts                                                                                                                                                 
                                                                                                                                                                                                              
  class EvidenceBundle(BaseModel):                                                                                                                                                                            
      bundle_id: str                                                                                                                                                                                          
      experiment_plan_id: str                                                                                                                                                                                 
      artifact_refs: list[str]   # RunArtifactProtocol.artifact_id references                                                                                                                                 
      metrics: dict                                                                                                                                                                                           
      supports: list[str]        # hypothesis_ids this evidence supports                                                                                                                                      
      refutes: list[str]         # hypothesis_ids this evidence refutes                                                                                                                                       
      confidence: float          # 0-1, statistical confidence in the result                                                                                                                                  
                                                                                                                                                                                                              
  class Review(BaseModel):                                                                                                                                                                                    
      review_id: str                                                                                                                                                                                          
      evidence_bundle_id: str                                                                                                                                                                                 
      reviewer_type: Literal["computational", "human"]                                                                                                                                                        
      credibility_score: float                                                                                                                                                                                
      novelty_score: float                                                                                                                                                                                    
      recommendation: Literal["ADVANCE", "REFINE", "PIVOT", "ABANDON"]                                                                                                                                        
      reasoning: str                                                                                                                                                                                          
                                                                                                                                                                                                              
  class Decision(BaseModel):                                                                                                                                                                                  
      decision_id: str                                                                                                                                                                                        
      review_id: str                                                                                                                                                                                          
      decided_by: str           # "reviewer_agent" or "human:${user_id}"                                                                                                                                      
      decision: Literal["ADVANCE", "REFINE", "PIVOT", "ABANDON"]                                                                                                                                              
      requires_approval: bool   # True for PIVOT/ABANDON                                                                                                                                                      
                                                                                                                                                                                                              
  5.2 ResearchOrchestrator (core/research.py)                                                                                                                                                                 
                                                                                                                                                                                                              
  Problem: The proposal describes "wraps HarnessRuntime, drives iteration loop" but doesn't specify the loop control flow.                                                                                    
                                                
  Recommendation: Model as a state machine with explicit budget awareness:                                                                                                                                    
                                                
  class ResearchOrchestrator:                                                                                                                                                                                 
      def __init__(                                                                                                                                                                                           
          self,                                                                                                                                                                                               
          runtime: HarnessRuntime,                                                                                                                                                                            
          store: ResearchStore,                                                                                                                                                                               
          budget: ResearchBudget,           # max_experiments, max_wall_clock, max_llm_cost                                                                                                                   
          reviewer: ReviewerProtocol | None,  # None = trivial reviewer                                                                                                                                       
          approval_required_for: set[Decision] = {PIVOT, ABANDON},                                                                                                                                            
      ): ...                                                                                                                                                                                                  
                                                                                                                                                                                                              
      async def pursue(                                                                                                                                                                                       
          self,                                                                                                                                                                                               
          question: ResearchQuestion,                                                                                                                                                                         
          *,                                                                                                                                                                                                  
          max_iterations: int = 10,                                                                                                                                                                           
      ) -> ResearchConclusion: ...                                                                                                                                                                            
                                                                                                                                                                                                              
  The loop should be:                                                                                                                                                                                         
                                                                                                                                                                                                              
  1. Generate hypotheses for question (via BrainProvider or static generator)                                                                                                                                 
  2. For each active hypothesis:                                                                                                                                                                              
     a. Design experiment (vary variables, control rest)                                                                                                                                                      
     b. Submit ExperimentPlan → harness executes via ExecutionLifecycleService                                                                                                                                
     c. Collect EvidenceBundle from run artifacts                                                                                                                                                             
     d. Submit to ReviewerAgent → Review                                                                                                                                                                      
     e. Check approval manifest if PIVOT/ABANDON                                                                                                                                                              
     f. Update hypothesis status based on evidence                                                                                                                                                            
  3. Check convergence: all hypotheses resolved? budget exhausted? diminishing returns?                                                                                                                       
  4. If not converged and budget remains → refine surviving hypotheses, goto 2                                                                                                                                
  5. Return ResearchConclusion with evidence DAG and final recommendation                                                                                                                                     
                                                                                                                                                                                                              
  5.3 HypothesisOptimizer                                                                                                                                                                                     
                                                                                                                                                                                                              
  Problem: Current optimizer action space is add_edge / remove_edge / swap_template on component graphs. Hypotheses are a different entity.                                                                   
                                                
  Recommendation: Do NOT extend the existing ActionSpaceFunnel. Instead, implement a HypothesisActionSpace that operates on the research DAG:                                                                 
                                                
  - GENERATE: Given a ResearchQuestion + existing evidence, propose new hypotheses. This is an LLM call, not a graph enumeration.                                                                             
  - REFINE: Given a refuted hypothesis + evidence, propose a refined version (narrower scope, adjusted prediction).
  - SELECT: Given multiple active hypotheses and a budget, choose which to test next (bandit problem — use the existing BayesianOptimizer from optimizer/bayesian.py).                                        
  - COMBINE: Given two supported hypotheses, propose a synthesis.                                                                                                                                             
                                                                                                                                                                                                              
  This can share the BrainProvider protocol (core/brain.py:19) — propose() and evaluate() are the right interface, just with a different action type. The FitnessEvaluator can be reused but needs a new      
  evaluator for hypothesis quality (prediction specificity, testability, novelty relative to SOTA).                                                                                                           
                                                                                                                                                                                                              
  5.4 ReviewerAgent protocol (sdk/review.py)                                                                                                                                                                  
                                               
  Problem: Credibility and novelty are the only evaluation dimensions. For scientific computing, correctness and reproducibility are equally important.                                                       
                                                
  Recommendation:                                                                                                                                                                                             
                                                
  class ReviewDimensions(BaseModel):                                                                                                                                                                          
      credibility: float      # Do I believe this result? (methodology, statistical rigor)                                                                                                                    
      novelty: float          # Is this new relative to SOTA baseline?                                                                                                                                        
      correctness: float      # Does the math check out? (numerical consistency, unit checks)                                                                                                                 
      reproducibility: float  # Would re-running produce the same result? (variance, stability)                                                                                                               
      significance: float     # Does this change our understanding? (effect size relative to noise)                                                                                                           
                                                                                                                                                                                                              
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
                                                                                                                                                                                                              
  The baseline parameter is critical — novelty is meaningless without a reference point. The benchmark integration provides this: the extension lane result (deterministic compiler path) is the natural      
  baseline.                                                                                                                                                                                                   
                                                                                                                                                                                                              
  5.5 Benchmark Integration                                                                                                                                                                                   
                                               
  Problem: Each benchmark suite has different metric schemas. Poisson has l2_error, h1_error; Nektar has different fields; QCompute has Hamiltonian eigenvalues. A ResearchQuestion needs a unified           
  representation.                               
                                                                                                                                                                                                              
  Recommendation: Add a MetricSchema to benchmark cases that declares the semantic meaning of each metric:                                                                                                    
                                               
  class MetricSchema(BaseModel):                                                                                                                                                                              
      name: str                    # "l2_error"                                                                                                                                                               
      relation: Literal["lt", "gt", "approx"]  # "lt" = lower is better                                                                                                                                       
      target: float | None         # None = exploratory                                                                                                                                                       
      unit: str                    # "" (dimensionless), "s", etc.                                                                                                                                            
      is_primary: bool             # primary metrics drive decisions                                                                                                                                          
                                                                                                                                                                                                              
  This lets the ResearchOrchestrator compare results across suites: "reducing l2_error below 0.001" is a meaningful hypothesis regardless of which PDE solver produced the number.                            
                                                                                                                                                                                                              
  The benchmark runner's summary.json already captures metrics, status, preflight_status, and failure_category. Adding a metric_schema field to BenchmarkCaseSpec (or deriving it from expected_metrics + a   
  new schema registry) would close the loop.    
                                                                                                                                                                                                              
  5.6 Missing Integration: SOTA Baseline Registry                                                                                                                                                             
                                               
  The proposal mentions "open problems as ResearchQuestion with baseline" but doesn't specify where baselines live. This is worth its own minimal component:                                                  
                                                
  class SOTABaseline(BaseModel):                                                                                                                                                                              
      baseline_id: str                                                                                                                                                                                        
      research_question_id: str                                                                                                                                                                               
      metric_values: dict       # {"l2_error": 0.002487, ...}                                                                                                                                                 
      source: str               # "benchmark:fealpy-pde:poisson-2d-numpy:extension"                                                                                                                           
      timestamp: datetime                                                                                                                                                                                     
                                                                                                                                                                                                              
  The extension lane (deterministic, zero LLM) is the natural SOTA baseline for every FEALPy case — it's the ground truth the LLM is trying to match. This is cheap to implement: the benchmark runner already
   produces these numbers. Just persist them with a label.                                                                                                                                                    
                                                                                                                                                                                                              
  ---                                           
  Summary                                      
                                                                                                                                                                                                              
  ┌─────────────────┬─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
  │    Dimension    │                                                                         Assessment                                                                          │                           
  ├─────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                           
  │ Wrapping design │ Sound. Use dual-track (hypothesis state machine + graph mutation) rather than forcing hypotheses into CandidateRecord.                                      │                           
  ├─────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                           
  │ Completeness    │ Missing: ResearchStore, budget model, human-in-the-loop gates, negative result handling, reproducibility gating (6 items).                                  │                           
  ├─────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                           
  │ Risk            │ 3 Low, 3 Medium, 1 High (HypothesisOptimizer).                                                                                                              │                           
  ├─────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                           
  │ Priority        │ Models → Store → Connection mappers → Benchmark integration → Orchestrator → Reviewer → HypothesisOptimizer (last).                                         │
  ├─────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤                           
  │ Key improvement │ DAG not chain for research models; separate HypothesisActionSpace from graph ActionSpaceFunnel; add MetricSchema to benchmarks; add SOTA baseline registry. │
  └─────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘                           
                                                
  The highest-leverage next step is writing the research models (sdk/research.py) — it's low-risk, establishes the vocabulary for all subsequent work, and can be reviewed and agreed upon before any runtime 
  code is written.
