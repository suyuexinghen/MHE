                                                                                                                      
  ---                                                                                                                                                                                                          
  MHE Lean Extension — Detailed Design Summary                                                                                                                                                                 
                                                                                                                                                                                                               
  1. What It Is and What It Isn't                                                                                                                                                                              
                                                                                                                                                                                                               
  metaharness_ext.lean integrates Lean 4 formal theorem proving into MHE's typed, evidence-driven, agent-orchestrable runtime. It is not a theorem-proving AI, a Lean compiler, a Mathlib search engine, or a  
  clone of Numina-Lean-Agent. It is a governance layer that maps Lean-specific concepts (proof goals, sorry markers, compilation diagnostics, blueprint DAGs, statement drift) into MHE's                      
  contract/governance/evidence system.                                                                                                                                                                         
                                                                                                                                                                                                               
  What it delegates:                                                                                                                                                                                           
  - Proof search and tactic generation → MHE BrainProvider / Agent layer                                                                                                                                       
  - Lean compilation → lake env lean subprocess                                                                                                                                                                
  - Theorem retrieval → external tools (loogle, LeanDex, leanexplore) — hooks reserved, implementation deferred                                                                                                
  - Informal reasoning → external LLM discussion partners (Gemini/GPT)                                                                                                                                         
                                                                                                                                                                                                               
  What it owns:                                                                                                                                                                                                
  - Lean project discovery and environment probing                                                                                                                                                             
  - Blueprint DAG compilation                                                                                                                                                                                  
  - Lean subprocess execution with configurable timeouts                                                                                                                                                       
  - Sorry-aware validation and statement drift detection                                                                                                                                                       
  - Evidence bundling (compilation logs, proof states, sorry maps)                                                                                                                                             
  - Policy evaluation (compilation success, sorry thresholds, statement stability)                                                                                                                             
                                                                                                                                                                                                               
  2. Design Principles (with Rationale)                                                                                                                                                                        
                                                                                                                                                                                                               
  Proof-as-artifact. Every proof state is versioned, compilable, and provenance-tracked. LeanRunArtifact records the exact lake env lean command, working directory, full stdout/stderr, and parsed sorry      
  locations. This makes every execution auditable and replayable, which is not the case in ad-hoc agent loops.                                                                                                 
                                                                                                                                                                                                               
  Sorry-aware, not sorry-phobic. In Numina's system, sorry is a legitimate progress marker — an incomplete sub-proof that still lets surrounding code compile. The validator distinguishes three categories:   
  compilation errors (hard failure, blocks_promotion=True), sorries within attempt budget (expected, blocks_promotion=False), and sorries after budget exhaustion (soft failure, blocks_promotion=True). This
  three-way split is essential because a single remaining sorry in a 500-line proof is fundamentally different from a file that fails to parse.                                                                
                                               
  Blueprint-first. Numina's key insight (§4.1) is that directly asking an agent to prove a complex theorem produces suboptimal formulations and local dead ends. The blueprint compiler decomposes a theorem   
  into a dependency DAG of lemmas ordered so dependencies come before dependents (leaves first). Each LeanBlueprintItem carries: a unique label, Lean declaration name, file path, informal statement, informal
   proof sketch, dependency list (uses), status (todo/partial/done), attempt count, and attempt budget. This DAG is the single source of truth — the validator checks the entire DAG, not just individual      
  files.                                       
                                               
  Statement drift is governed. Numina §4.2 documents that during Brascamp-Lieb formalization, the agent autonomously revised incorrect theorem statements. This is a capability, not a bug — but it must be a  
  reviewable governance event. The validator snapshots theorem/lemma declaration hashes before each proof attempt and classifies post-execution changes as added (warn, don't block), modified (block
  promotion, requires review), or removed (block promotion, requires review). The policy engine decides whether to accept the revision based on drift severity and project policy.                             
                                               
  Iterative refine loop. Numina's proof-agent protocol uses 2^n checkpoints (attempts 2, 4, 8, 16, 32...) to trigger informal proof refinement via an external model. When the validator reports persistent    
  sorries at a checkpoint, the blueprint compiler's refine_at_checkpoint() marks the item for informal proof revision. The updated informal proof feeds back into the next set of formalization attempts. This
  prevents the agent from burning its entire budget on a bad strategy.                                                                                                                                         
                                               
  Subgoal isolation. Numina's Putnam A5 strategy (§3.2) isolated a stuck lemma into a separate sub-agent with fresh context, which solved it when the main agent's long context caused instruction-following   
  degradation. The proof workspace component supports delegate_to_subagent(item) which creates an isolated .lean file with minimal imports, passes it to a sub-agent, and merges the proven code back. This is
  particularly valuable for projects with 10+ interdependent lemmas where context pollution becomes a real problem.                                                                                            
                                               
  Mock-first, real-opt-in. The default execution mode is dry-run with a deterministic MockLeanBackend that returns configurable exit codes, stdout, and sorry locations. Real lake env lean execution requires 
  MHE_RUN_REAL_LEAN=1 and a discoverable Lean project. This follows MHE's established pattern (cf. @pytest.mark.boutpp, MHE_RUN_REAL_OCTAVE=1) and prevents the extension from overclaiming capabilities when
  Lean is not installed.                                                                                                                                                                                       
                                               
  3. Component Chain (7 Components)                                                                                                                                                                            
   
  The pipeline follows MHE's gateway-oriented architecture:                                                                                                                                                    
                                               
  LeanGateway                                                                                                                                                                                                  
    → LeanEnvironment       (probe: is Lean/lake available? is the project buildable?)                                                                                                                         
      → LeanBlueprintCompiler  (compile: decompose theorem into dependency DAG)                                                                                                                                
        → LeanProofWorkspace   (prepare: create isolated tmp .lean files)                                                                                                                                      
          → LeanExecutor       (execute: lake env lean, capture diagnostics)                                                                                                                                   
            → LeanValidator    (validate: sorry map, drift detection, completeness ratio)                                                                                                                      
              → LeanEvidence   (bundle: artifacts, reports, provenance, snapshots)                                                                                                                             
                                                                                                                                                                                                               
  Gateway (lean_gateway.primary): Single entry point. Receives LeanTaskSpec, resolves which family to use, orchestrates the full chain. Exposes three methods: prove_sorry() for a single lemma, run_project() 
  for blueprint-driven multi-lemma projects, audit() for read-only validation. Not protected.                                                                                                                  
                                                                                                                                                                                                               
  Environment (lean_environment.primary): Discovers Lean installation via elan toolchain, locates project root by walking up from the target file looking for lean-toolchain + lakefile, checks lake build     
  status, probes optional tools (loogle, leanexplore, LeanDex). Produces LeanEnvironmentReport with blocks_promotion=True when prerequisites are missing. This component gates all real execution.
                                                                                                                                                                                                               
  BlueprintCompiler (lean_blueprint_compiler.primary): Accepts a theorem statement (informal), decomposes it into a LeanBlueprint — an ordered list of LeanBlueprintItem where each item has a label, Lean     
  declaration name, file path, informal statement, informal proof sketch, uses list (dependencies), status, attempt count, and attempt budget. Items are topologically sorted by dependency. Supports
  refine_at_checkpoint() triggered when attempts reach 2^n, which calls out to an external informal reasoner for a revised proof sketch.                                                                       
                                               
  ProofWorkspace (lean_proof_workspace.primary): Manages isolated temporary .lean files. prepare(item) extracts the minimal environment (necessary imports, dependencies) from the original file and creates a 
  standalone file with the target declaration and sorry. restore(item) copies proven code back and deletes the tmp file. Tracks per-item attempt counts, informal proof versions, and statement snapshots.
  Supports delegate_to_subagent(item) for context isolation on difficult sub-lemmas.                                                                                                                           
                                               
  Executor (lean_executor.primary): Invokes lake env lean <file> as a subprocess with the project root as cwd. Captures exit code, stdout, stderr, and duration. Parses sorry locations from diagnostic output 
  using regex on the standard Lean error/warning format. Supports configurable timeouts. Produces LeanRunArtifact.
                                                                                                                                                                                                               
  Validator (lean_validator.primary) — protected: The protected slot means this component's output cannot be bypassed. Distinguishes 6 validation states:                                                      
                                               
  ┌────────────────────┬───────────────────────┬─────────────────────────────────────────┐                                                                                                                     
  │       State        │   blocks_promotion    │                 Meaning                 │                                                                                                                     
  ├────────────────────┼───────────────────────┼─────────────────────────────────────────┤                                                                                                                     
  │ FULLY_PROVEN       │ False                 │ All items sorry-free, compilation clean │                                                                                                                     
  ├────────────────────┼───────────────────────┼─────────────────────────────────────────┤
  │ PARTIALLY_PROVEN   │ False (within budget) │ Sorries remain, budget not exhausted    │                                                                                                                     
  ├────────────────────┼───────────────────────┼─────────────────────────────────────────┤                                                                                                                     
  │ BUDGET_EXHAUSTED   │ True                  │ Max attempts reached                    │                                                                                                                     
  ├────────────────────┼───────────────────────┼─────────────────────────────────────────┤                                                                                                                     
  │ COMPILATION_FAILED │ True                  │ Hard Lean error                         │
  ├────────────────────┼───────────────────────┼─────────────────────────────────────────┤                                                                                                                     
  │ STATEMENT_DRIFT    │ True                  │ Theorem statement changed               │
  ├────────────────────┼───────────────────────┼─────────────────────────────────────────┤                                                                                                                     
  │ ENVIRONMENT_FAILED │ True                  │ Lean/lake missing                       │
  └────────────────────┴───────────────────────┴─────────────────────────────────────────┘                                                                                                                     
                                               
  Also detects statement drift by comparing pre-execution snapshots with post-execution declaration hashes. Produces LeanValidationReport with ScoredEvidence (completeness ratio, drift severity).            
                                               
  Evidence (lean_evidence.primary): Assembles LeanEvidenceBundle containing the environment report, blueprint, all run artifacts, validation report, provenance metadata (agent model, attempt count, blueprint
   version, informal proof version), and statement snapshots. Satisfies MHE EvidenceBundleProtocol for downstream governance consumption.
                                                                                                                                                                                                               
  4. Three Proof Families                                                                                                                                                                                      
                                               
  formal_proof: Single target lemma/theorem, one .lean file, one informal proof sketch. The executor runs lake env lean on the target file. The validator checks that the specific target sorry is removed and 
  the file compiles. This is the first baseline family — the simplest complete workflow.
                                                                                                                                                                                                               
  formalization_project: Blueprint DAG of N items with explicit dependencies. The gateway processes items in dependency order (can parallelize items at the same depth with no interdependencies). The         
  validator checks the full DAG for sorry-free compilation and statement consistency across all items. This maps to Numina's Brascamp-Lieb workflow (8,000+ lines, ~70 definitions/lemmas/theorems).
                                                                                                                                                                                                               
  proof_audit: Read-only. No proof construction, no source modification. The environment probes the project, the executor compiles all target files, the validator reports every error, sorry, and warning with
   per-file breakdown and project-level completeness ratio. This is the MHE equivalent of running lake build and parsing the diagnostic output into structured evidence.
                                                                                                                                                                                                               
  5. Contracts Surface (10 Core Types)                                                                                                                                                                         
                                               
  All types are Pydantic BaseModel subclasses carrying MHE governance metadata (candidate_identity, promotion_metadata, checkpoint_refs, provenance_refs, trace_refs, scored_evidence, execution_policy).      
                                               
  ┌───────────────────────┬──────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────┐                                                        
  │         Type          │     Purpose      │                                               Key Fields                                               │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanTaskSpec          │ User input       │ family, target_file, target_lemma, project_root, budget                                                │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanProjectSpec       │ Project identity │ project_root, toolchain_version, lakefile_path, build_status                                           │                                                        
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanBlueprint         │ Proof plan       │ items: list[LeanBlueprintItem]                                                                         │                                                        
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanBlueprintItem     │ One lemma        │ label, lean_declaration, file, uses, status, attempts, budget, informal_statement, informal_proof      │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanRunPlan           │ Execution plan   │ plan_id, task_ref, target_file, workspace_path                                                         │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanRunArtifact       │ Execution output │ artifact_id, exit_code, stdout, stderr, sorry_locations, duration_seconds                              │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanEnvironmentReport │ Env findings     │ lean_available, lake_available, project_root_found, toolchain_version, blocks_promotion                │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanValidationReport  │ Proof quality    │ status, sorry_count, error_count, drift_changes, completeness_ratio, blocks_promotion, scored_evidence │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanEvidenceBundle    │ Full evidence    │ environment_report, blueprint, artifacts, validation_report, provenance                                │
  ├───────────────────────┼──────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────┤                                                        
  │ LeanCandidateIdentity │ Governance       │ candidate_id, family, graph_version                                                                    │
  └───────────────────────┴──────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────┘                                                        
                                               
  6. What Was Learned from Numina (and What Wasn't Copied)                                                                                                                                                     
                                               
  Adopted patterns:                                                                                                                                                                                            
                                               
  1. Blueprint DAG with dependency ordering (BLUEPRINT_template.md): The uses field, topological sort, and per-item status tracking are directly inspired by Numina's blueprint format. This is encoded in     
  LeanBlueprint / LeanBlueprintItem.           
  2. 2^n checkpoint informal refinement (proof_agent.md lines 107-112): The refine_at_checkpoint() trigger at attempts 2, 4, 8, 16, 32 is taken from Numina's proof-agent protocol. It prevents budget         
  exhaustion on bad strategies.                                                                                                                                                                                
  3. Sorry protocol (proof_agent.md lines 22-44): Numina's rule — "identify the smallest stuck part, leave only that as sorry, everything else must be proven" — is encoded in the validator's sorry-aware
  classification.                                                                                                                                                                                              
  4. Sub-agent context isolation (Putnam A5 strategy, §3.2): The delegate_to_subagent() path in the proof workspace is inspired by Numina's isolation of the alternating-permutations lemma.
  5. Statement self-correction (Brascamp-Lieb §4.2): Numina's observation that the agent can autonomously detect and revise incorrect theorem statements during formalization is the rationale for statement   
  drift detection as a first-class governance event.                                                                                                                                                           
  6. Lean project root discovery (lean_checker.py): The walk-up-from-target-to-find-lean-toolchain pattern is taken from Numina's find_lean_project_root().                                                    
                                                                                                                                                                                                               
  Not adopted (intentionally):                                                                                                                                                                                 
                                                                                                                                                                                                               
  - Numina MCP server: The extension uses lake env lean directly, not lean-lsp-mcp. LSP-level goal inspection, lean file outline, lean multi attempt are deferred. This avoids a hard dependency on a specific 
  MCP server.                                  
  - Numina's specific agent prompts: The coordinator/proof-agent/informal-agent/golfer prompt hierarchy is agent-layer design, not extension-layer design. The extension provides the typed contracts and      
  governance surface; the Agent layer implements the prompting strategy.                                                                                                                                       
  - Numina's CLI skills (lean_check.py, leanexplore.py, discussion_partner.py): These are external tools consumed through capability hooks, not bundled in the extension.
  - Numina's specific model routing (Gemini for informal, GPT for discussion partner): Model choice is a BrainProvider configuration, not an extension concern.                                                
                                                                                                                                                                                                               
  7. Execution Model and Gating                                                                                                                                                                                
                                                                                                                                                                                                               
  Two-tier execution:                                                                                                                                                                                          
                                               
  ┌───────────┬─────────────────────┬──────────────────────────────────────────────────────────────────────────────┐                                                                                           
  │   Mode    │     Active When     │                                   Behavior                                   │
  ├───────────┼─────────────────────┼──────────────────────────────────────────────────────────────────────────────┤                                                                                           
  │ dry_run   │ Default             │ MockLeanBackend returns configurable exit_code/stdout/stderr/sorry_locations │
  ├───────────┼─────────────────────┼──────────────────────────────────────────────────────────────────────────────┤                                                                                           
  │ real_lean │ MHE_RUN_REAL_LEAN=1 │ Actual lake env lean <file> subprocess                                       │                                                                                           
  └───────────┴─────────────────────┴──────────────────────────────────────────────────────────────────────────────┘                                                                                           
                                                                                                                                                                                                               
  The mock backend is not a toy — it's designed to test the full pipeline's response to every failure mode: compilation errors, timeout, partial sorries, full proof success. This is the same pattern used by 
  MHE's QCompute extension (mock backend for Phase 0, real Aer for Phase 1).
                                                                                                                                                                                                               
  Pytest markers: Real Lean tests are marked @pytest.mark.lean and excluded from default pytest runs. This matches MHE's existing convention (@pytest.mark.nektar, @pytest.mark.quafu, @pytest.mark.boutpp).   
                                               
  8. 6-Phase Roadmap                                                                                                                                                                                           
                                               
  ┌───────┬────────────────────────────────────────────────┬───────────────┐                                                                                                                                   
  │ Phase │                     Scope                      │ Lean Required │
  ├───────┼────────────────────────────────────────────────┼───────────────┤                                                                                                                                   
  │ 0     │ Scaffold + Contracts + Mock Backend            │ No            │
  ├───────┼────────────────────────────────────────────────┼───────────────┤                                                                                                                                   
  │ 1     │ Real Lean Environment Probe + Smoketest        │ Yes (gated)   │                                                                                                                                   
  ├───────┼────────────────────────────────────────────────┼───────────────┤                                                                                                                                   
  │ 2     │ Blueprint Compiler + Proof Workspace           │ Yes (gated)   │                                                                                                                                   
  ├───────┼────────────────────────────────────────────────┼───────────────┤                                                                                                                                   
  │ 3     │ Sub-agent Delegation + Statement Drift         │ Yes (gated)   │
  ├───────┼────────────────────────────────────────────────┼───────────────┤                                                                                                                                   
  │ 4     │ Formalization Project Family (multi-lemma DAG) │ Yes (gated)   │
  ├───────┼────────────────────────────────────────────────┼───────────────┤                                                                                                                                   
  │ 5     │ Proof Audit Family (read-only validation)      │ Yes (gated)   │
  └───────┴────────────────────────────────────────────────┴───────────────┘                                                                                                                                   
                                               
  Phase 0 is the smallest truthful slice: contracts, slots, capabilities, component stubs with declare_interface(), manifest JSON per component, mock backend, and manifest/contracts parity tests. ~17 source 
  files, 2 test files, zero external dependencies beyond Pydantic and MHE core. This is what the implementation plan details step-by-step.
