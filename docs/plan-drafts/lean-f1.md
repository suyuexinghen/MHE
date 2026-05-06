以下是对当前设计的系统分析，按影响程度排列。                                                                                                                                                                 
                                                                                                                                                                                                               
  ---                                                                                                                                                                                                          
  高影响问题                                                                                                                                                                                                   
                                                                                                                                                                                                               
  1. 组件链与 Phase 0 交付不一致                                                                                                                                                                               
                                                                                                                                                                                                               
  Phase 0 声明了 7 个 slot（含 LEAN_BLUEPRINT_COMPILER_SLOT、LEAN_PROOF_WORKSPACE_SLOT），但只创建 5 个组件桩。Phase 2 才实现的组件却有 slot/capability 常量在 Phase 0 落地——这会导致 manifest 声明的 slot     
  没有对应组件实现，ComponentDiscovery 加载时依赖解析失败。两个修法：要么 Phase 0 只声明 5 个 slot（BlueprintCompiler 和 ProofWorkspace 的 slot 推迟到 Phase 2），要么 Phase 0 就为全部 7 个组件创建桩。       
                                                                                                                                                                                                               
  2. Policy 组件无家可归                                                                                                                                                                                       
                                               
  CAP_LEAN_POLICY_EVALUATE 在 capabilities 中声明，但 component chain、slots、package layout、Phase 0 manifests 均无对应组件。policy 功能在 Phase 2 roadmap 中提到（"policy.py:                                
  evaluate()"），但作为一个独立组件它没有 slot、没有 manifest、没有在架构图中出现。建议要么将 policy 合并到 Validator（validator 已负责 blocks_promotion 判断），要么显式增加 LeanPolicyEngine 组件及对应
  slot。                                                                                                                                                                                                       
                                                         
  3. Phase 顺序倒置：proof_audit 应该在 formalization_project 之前                                                                                                                                             
                                               
  proof_audit 是只读验证——跳过 BlueprintCompiler 和 ProofWorkspace，只需 Environment → Executor → Validator → Evidence。formalization_project 需要完整的蓝图 DAG、子代理委派、并行执行协调。当前 Phase         
  4=project、Phase 5=audit，应该互换。更简单的 audit family 可以更早验证 env+executor+validator 链路的正确性，降低 project 阶段的调试复杂度。
                                                                                                                                                                                                               
  ---                                                    
  中影响问题                                 
                                                                                                                                                                                                               
  4. LeanValidationStatus 缺少关键状态
                                                                                                                                                                                                               
  当前 6 个状态缺少：                                                                                                                                                                                          
  - TIMEOUT：lake env lean 超时（与编译失败不同，超时可重试）                                                                                                                                                  
  - WORKSPACE_ERROR：无法创建 tmp 文件或提取环境（不应重试，环境问题）                                                                                                                                         
  - SORRY_TRANSITIVE：目标文件编译通过但依赖的 import 模块中存在 sorries（表层干净，深层未完成）
                                                                                                                                                                                                               
  其中 TIMEOUT 最紧迫——当前 failure taxonomy 提到 subprocess timeout 但 validation status 枚举没有对应值。                                                                                                     
                                                                                                                                                                                                               
  5. Mock backend 不支持结构化诊断输出                                                                                                                                                                         
                                                                                                                                                                                                               
  当前 MockLeanBackend.run() 返回 raw (exit_code, stdout, stderr)。但 Phase 1 的 executor 需要解析 "sorry locations from diagnostic output"——如果 mock 不产出结构化的诊断行（带行号、错误级别），parser        
  的测试就只能测真实 Lean 输出，违反 mock-first 原则。Mock 应支持注入结构化诊断：diagnostics: list[dict] 包含 line, severity, message。
                                                                                                                                                                                                               
  6. LeanTaskSpec 与 LeanProjectSpec 的关系未定义                                                                                                                                                              
                                             
  LeanTaskSpec 有 project_root: str 字段，LeanProjectSpec 也有 project_root: str。它们是嵌入关系（TaskSpec 包含 ProjectSpec）还是引用关系（TaskSpec 引用 ProjectSpec 的 ID）？实现时会有歧义。建议：TaskSpec   
  直接嵌入 ProjectSpec（project: LeanProjectSpec），因为 proof task 的 project context 是必需的，不独立存在。
                                                                                                                                                                                                               
  7. 缺少 restart/resume 语义                                                                                                                                                                                  
                                             
  Proof 过程可能被中断——tmp 文件留在磁盘上，blueprint item 处于 partial 状态。当前设计没有任何 checkpoint/resume 规范。最低限度应说明：(a) ProofWorkspace 的 tmp 文件是否在组件 deactivate 时保留；(b)         
  恢复时如何判断 tmp 文件是否仍然有效（原始文件内容未被外部修改）。
                                                                                                                                                                                                               
  ---                                                    
  低影响问题                                 
                                                                                                                                                                                                               
  8. Family 命名不够直观
                                                                                                                                                                                                               
  formal_proof 含义模糊——所有 family 处理的都是 formal proof。建议改为 discharge_sorry 或 single_lemma，与 formalization_project 和 proof_audit 的粒度形成对比。                                               
                                                                                                                                                                                                               
  9. Evidence provenance 字段不足                                                                                                                                                                              
                                                         
  LeanEvidenceBundle 的 provenance 字段类型是泛化的 dict，但对 proof system 需要记录：Lean toolchain 版本、Mathlib commit hash、使用的 Agent 模型及版本、blueprint 版本号、informal proof 版本号、每次 attempt 
  的 timestamp + tactic + 结果。这些应在 contracts 中显式定义 LeanProvenance 类型。
                                                                                                                                                                                                               
  10. Wiki 页面声明但未创建                                                                                                                                                                                    
                                             
  lean-engine-wiki/README.md 描述了 7 个页面（01-overview.md 到 07-scope-and-boundaries.md），但只有 README 存在。README 应在状态说明中明确 "wiki pages 01–07 are not yet drafted; this README is the current  
  sole wiki artifact"。                                  
                                                                                                                                                                                                               
  11. 缺少具体使用示例                                                                                                                                                                                         
                                             
  蓝图是纯架构描述，没有展示一个具体 proof task 如何流经组件链。建议在蓝图中加入一个 concrete trace example：例如 theorem sum_of_squares (n : ℕ) : ... := by ... 从 LeanTaskSpec 到 LeanEvidenceBundle         
  的完整路径。                                           
                                                                                                                                                                                                               
  12. Gateway component stub 示例中 capability 声明有误                                                                                                                                                        
                                             
  Implementation plan Step 6 中 LeanGatewayComponent.declare_interface() 声明了 provide_capability(CAP_LEAN_ENV_PROBE)，但环境探测是 Environment 组件的功能，不是 Gateway 的。Gateway 应该声明 CAP_LEAN_GATEWAY
   或一个协调类 capability。                             
                                                                                                                                                                                                               
  ---                                                    
  建议优先修复                               
                                                                                                                                                                                                               
  ┌────────┬──────────────────────────────────┬───────────────────────────────────────┐
  │ 优先级 │               问题               │               修改文件                │                                                                                                                        
  ├────────┼──────────────────────────────────┼───────────────────────────────────────┤                                                                                                                        
  │ 1      │ Slot 数量与 Phase 0 组件数量对齐 │ blueprint, implementation-plan        │                                                                                                                        
  ├────────┼──────────────────────────────────┼───────────────────────────────────────┤                                                                                                                        
  │ 2      │ Policy 组件归属明确化            │ blueprint, slots, capabilities        │                                                                                                                        
  ├────────┼──────────────────────────────────┼───────────────────────────────────────┤                                                                                                                        
  │ 3      │ Phase 4↔5 互换                   │ roadmap                               │                                                                                                                        
  ├────────┼──────────────────────────────────┼───────────────────────────────────────┤                                                                                                                        
  │ 4      │ 增加 TIMEOUT 状态                │ types, contracts, implementation-plan │
  ├────────┼──────────────────────────────────┼───────────────────────────────────────┤                                                                                                                        
  │ 5      │ Mock 支持结构化诊断              │ implementation-plan                   │
  ├────────┼──────────────────────────────────┼───────────────────────────────────────┤                                                                                                                        
  │ 6      │ TaskSpec 嵌入 ProjectSpec        │ contracts, implementation-plan        │
  └────────┴──────────────────────────────────┴───────────────────────────────────────┘
