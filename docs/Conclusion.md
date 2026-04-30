
● 研究结论

  - MHE 的 ABACUS × QCompute 当前已从“空缺口”推进到可审计 scaffold：已支持 artifact inventory、H/S header-level parser contract、QCompute pauli_dict proxy conversion contract、tiny dense H/S eigenproblem validator contract、review signoff artifact。
  - 当前最强可支持结论是：MHE 显著提升了 workflow controllability、evidence completeness、claim boundary enforcement 和 overclaim prevention。
  - 仍不能声称真实 ABACUS H/S matrix 已被科学正确转换为 QCompute 可消费 Hamiltonian；当前只有 proxy conversion 与 validator contract，不是 production conversion。
  - ACP 已可作为 reviewer evidence 通道的结构化入口：MHE 能记录 ACP diagnostic、review_signoff.json、claim boundary、missing evidence。
  - 但 ACP reviewer evidence 不能替代 human/scientific sign-off；因此已固化 reviewer_evidence_only=true 和 replaces_human_scientific_signoff=false。
  - abacus-hs-bridge-pending 仍必须保持 skipped；阻塞项是管理员认可 reference fixture、tolerance table、human/scientific sign-off、production converter、real-mode repeated evidence。
  - 下一阶段真正能提升 claim boundary 的工作不是继续扩大 proxy，而是获取认可 fixture 并实现 production H/S→Hamiltonian converter，再用 ACP/human reviewer 双轨生成 signoff evidence。



● 研究结论：FEALPy 现在具备做 Octave/Nektar 同类“三 lane”真实比较 benchmark 的基础，但结论边界必须分层。

  - 已实现的比较基础：fealpy-pde 已接入 extension/direct/agent 三 lane；direct 现在走 Claude/ACP proposal 生成独立 solve.py，不再复用 extension compiler；agent 走 Claude/ACP proposal 生成 FEALPy typed
  spec/patch，再由 MHE compiler/executor/validator/evidence 作为执行权威。
  - 当前可声称：FEALPy benchmark plumbing、lane 分离、proposal preflight、attempt/evidence 记录、CLI dry-run、comparison 输出已可运行；Phase A 对 poisson-2d-numpy 通过。
  - 当前不能声称：不能说 MHE/agent 比 direct Claude Code 求解更准、更快、更稳；dry-run 只证明流程与证据结构，不证明数值能力。
  - 核心产品价值：MHE 的优势首先体现在 workflow controllability：typed spec、受控执行、验证器、证据包、失败分类、可重复 comparison，而不是直接的数值 superiority。
  - 下一步实证路径：先跑 Phase B extension real FEALPy repeated baseline；再跑 Phase C direct,agent with real Claude；最后扩展到 stokes-2d-numpy、可选 backend、3D/quota cases。
  - 最终判断标准：只有 repeated real tools + real Claude proposals 都产生可比 solver outcomes 后，才可以讨论成功率、修复率、数值误差或运行时间差异。

❯ 继续总结octave/nektar之前试验对比                                                                                                                                                                               
                              
● Octave/Nektar 之前试验对比结论可以分成三层：
                                 
  1. 已证明的部分：benchmark 框架能力      
  - Octave、Nektar、QCompute 已能通过统一 benchmark-run / benchmark-compare 产生 lane summaries、attempt logs、comparison bundles、manifest、repeat summary 和报告。
  - 三 lane 结构已成型：extension、direct、agent。                                                                                                                  
  - 已能区分 dry-run、real solver、real Claude、proposal failure、dependency skip、solver failure、repair outcome。
  - repeated dry-run 已验证 repeat aggregation 和 report plumbing。                                                
                                                                   
  2. Octave 当前证据更强                   
  - Octave 已完成 Phase B real-solver baseline。
  - sinc-values、roots-cubic、expm-jordan-2x2 在 extension-only real mode 下用 GNU Octave 9.2.0 跑了 --repeat 3。
  - 结果：9/9 real Octave runs passed。                                                                                                                                                                           
  - 无 dependency skip，无 LLM calls。     
  - roots-cubic 和 sinc-values 有 flaky_timing，主要因为 elapsed time 极小，IQR/median 比例容易放大。                                                                                                             
  - 结论边界：这证明 Octave extension lane 能真实执行小型数值案例并稳定产出指标；但不证明它优于 direct Claude 或 agent。
                                                                                                                                                                                                                  
  3. Nektar 当前仍偏 framework / dependency-gated
  - Nektar benchmark runner 已有 direct/agent/extension 结构、Nektar stdout error norm parser、capability skip、preflight/tester evidence。                                                                       
  - 但目前主要证据仍是 dry-run / scaffold / parser-level / capability-gated evidence。                                                     
  - Nektar real-solver repeated baseline 尚未像 Octave 那样形成完整 Phase B 结论。                                                                                                                                
  - 部分 case 仍需要真实 Nektar++ solver、session XML 映射、solver family 支持和 repeat evidence 来升级为 real solver evidence。                                                                                  
                                                                                                                                                                                                                  
  关键对比                                                                                                                                                                                                        
  - Octave：已进入“小规模真实 solver baseline”阶段。                                                                                                                                                              
  - Nektar：benchmark workflow 已搭好，但真实 solver 对比证据还不足。                                                                                                                                             
  - 两者共同点：都还没有证明 MHE extension 比 direct Claude Code/agent 在数值质量、速度、鲁棒性上更强。                                                                                                           
  - 两者已证明的真实优势：MHE 在 workflow controllability 上更强，包括 schema、lane separation、evidence capture、failure taxonomy、repeat aggregation 和 non-claim reporting。                                   
                                                                                                                                                                                                                  
  管理层可说法                                                                                                                                                                                                    
                                                                                                                                                                                                                  
  ▎ 当前 Octave 已有小规模真实 solver baseline；Nektar 已有可审计 benchmark 框架但需要更多 real solver repeated runs。总体上，MHE 目前证明的是科学工作流可控性和证据完整性提升，而不是数值/性能优越性。
