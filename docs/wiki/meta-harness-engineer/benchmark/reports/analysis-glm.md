  MHE Extension vs 直接使用 Claude Code 对比实验结论

  一、当前实验状态：Dry-run 阶段，尚不能得出"求解优劣"的数值结论

  三份报告（Octave / Nektar / QCompute-ABACUS）目前都是 dry-run benchmark，验证的是 benchmark driver 的工程完整性（case catalog、lane
  边界、summary schema、evidence layout、comparator bundle），而非真实科学计算的求解质量。所有 metrics 都是 reference
  echo（回显预设值），不是真实 solver 执行结果。

  已验证的能力：
  - 3 个独立 suite、19 个 case、3 条 lane 的完整 benchmark framework 可运行
  - 每条 lane 都写入了结构化的 summary.json、evidence 文件和 attempt log
  - Generic comparator 成功生成了 result_bundle.json、summary_table.csv、comparison_report.md
  - Capability-gated case（Nektar diffusion-2d/euler-1d、QCompute abacus-hs-bridge-pending）被正确 skip 而非伪造通过

  尚未验证的能力：
  - 真实 Octave octave-cli 执行后的数值精度
  - 真实 Nektar++ solver 的 L2/Linf error norm
  - 真实 Qiskit Aer VQE 的 energy/energy_error
  - 多次重复运行的 timing/flaky 标记

  二、当前阶段能得出的结构性判断

  Extension lane 的确定性优势（已验证）

  ┌─────────────────┬──────────────────────────┬──────────────────────────────────┬────────────────────────────┐
  │      维度       │    Extension (无 LLM)    │        Direct Claude CLI         │ Agent (Claude + Extension) │
  ├─────────────────┼──────────────────────────┼──────────────────────────────────┼────────────────────────────┤
  │ 可复现性        │ 确定性，每次运行产物相同 │ 依赖 LLM 输出质量                │ LLM 输出 + 确定性 pipeline │
  ├─────────────────┼──────────────────────────┼──────────────────────────────────┼────────────────────────────┤
  │ 证据链          │ 最轻量（3-5 个文件）     │ 最重（8 个文件含 prompt/result） │ 中等（5-6 个文件）         │
  ├─────────────────┼──────────────────────────┼──────────────────────────────────┼────────────────────────────┤
  │ Capability 表达 │ 精确 skip unsupported    │ 可能尝试超出能力的操作           │ 与 extension 一致          │
  ├─────────────────┼──────────────────────────┼──────────────────────────────────┼────────────────────────────┤
  │ 首次成功率      │ 100%（dry-run）          │ 100%（dry-run）                  │ 100%（dry-run）            │
  ├─────────────────┼──────────────────────────┼──────────────────────────────────┼────────────────────────────┤
  │ Overhead        │ 最低                     │ 中等（LLM 调用成本）             │ 最高（LLM + pipeline）     │
  └─────────────────┴──────────────────────────┴──────────────────────────────────┴────────────────────────────┘

  Dry-run 阶段 honest conclusion

  ▎ 在 dry-run 阶段，三条 lane 的 pass/fail 无差异，因为 driver 写的是 reference echo。真正的优劣对比必须在 real-mode 运行后才能判断。

  三、MHE Extension 当前需要优化解决的问题

  从 benchmark 实现过程中暴露的设计问题，按优先级排列：

  P0 — 阻塞 real-mode 对比实验

  1. Real-mode 数值执行尚未完成：三个 suite 都需要 --allow-real-tools + 真实 solver
  环境才能产出有意义的对比数据。这是回答老板问题的前提。
  2. Repeated-run 统计缺失：没有 median timing、variance、flaky flag，无法判断 extension pipeline 的 overhead 是否在可接受范围内。
  3. Direct lane 真实 Claude CLI 调用：当前 dry-run 用 FakeClaudeCLIBrainProvider，真实对比需要实际 Claude CLI 调用，且 direct 和 agent
  lane 必须使用相同模型和 budget。

  P1 — Pipeline 固定化带来的限制

  4. Extension pipeline 是硬编码的 linear flow：当前 compile → execute → validate → evidence 是固定顺序，无法让 LLM 在 pipeline
  中间做决策（如根据中间结果选择不同参数化策略）。这是老板提到的"后续让 LLM 更多参与科学计算流程"的核心瓶颈。
  5. Agent lane 只是 "Claude 提案 → 固定 pipeline 执行"：LLM 只在入口生成 proposal，之后完全走 deterministic path，没有 loop-back /
  repair / adaptive re-planning 能力。
  6. Error taxonomy 不够细化：validator 输出的 passed/failed 太粗，缺乏"哪一步失败、为什么、建议怎么修"的结构化诊断信息，导致 LLM
  无法有效参与修复。

  P2 — 科学计算 domain 覆盖

  7. ABACUS H/S bridge 缺失：QCompute 只能消费 FCIDUMP，无法接受 ABACUS 的 out_mat_hs 输出。这是 QCompute-ABACUS 集成的核心缺口。
  8. Nektar solver family 覆盖不完整：DiffusionSolver、IncNavierStokesSolver、CompressibleFlowSolver 的 extension dispatch 未实现，2/6
  case 被 capability skip。
  9. 跨 suite 的 provenance 链断裂：ABACUS 计算产出的 H/S matrix 无法自动流入 QCompute pipeline，需要人工准备 FCIDUMP fixture。

  四、回答老板的核心问题

  Q: MHE extension 对比直接使用 Claude Code 是否存在优势？

  当前证据不足以做最终判断，但从框架设计可以看到方向性的优劣势：

  MHE Extension 的预期优势（需 real-mode 验证）：
  - 确定性 pipeline 保证执行可复现，不受 LLM 输出随机性影响
  - 结构化的 validation/evidence/provenance 使结果可审计
  - Capability gate 防止超出当前能力的错误尝试
  - 批量 case 管理和自动 comparator 降低人工对比成本

  MHE Extension 的当前劣势：
  - Pipeline 过于固定，LLM 只在入口参与一次，无法在流程中自适应调整
  - 对于简单任务，extension 的 ceremony（compile → execute → validate → evidence）可能比 direct Claude CLI 更重
  - Domain 覆盖不完整（Nektar 2 case skip、ABACUS bridge 缺失），extension 能处理的 case 类型还有限

  Q: 如何更好地实现 harness 与科学计算的结合？

  建议的演进路线：

  1. 短期：完成 real-mode 对比实验，用真实数值结果回答优劣问题
  2. 中期：将 pipeline 从 linear flow 改为 LLM-in-the-loop 的 adaptive workflow：
    - LLM 在 compile 阶段选择参数化策略
    - LLM 在 validate 阶段分析失败原因并建议修复
    - LLM 在 evidence 阶段总结科学发现
  3. 长期：实现 ABACUS H/S → FCIDUMP → QCompute 的端到端自动 pipeline，让 LLM 在 domain gap 处做桥接决策

  五、建议的下一步行动

  按优先级：

  1. 用 --allow-real-tools 跑 Octave real-mode benchmark，产出第一份有真实数值的对比报告
  2. 同时让 direct lane 调用真实 Claude CLI（不是 Fake provider），获取 LLM proposal 的真实质量数据
  3. 基于真实对比结果，决定是先优化 pipeline 自适应能力，还是先扩展 domain 覆盖
  4. 设计 LLM-in-the-loop 的 pipeline 原型，在 1-2 个 case 上验证 adaptive workflow 是否比固定 pipeline 有显著提升

  六、按建议完成的第一轮实现状态

  已落地的工程改进：
  - `benchmark-run` 已拆分 `--allow-real-tools` 和 `--allow-real-claude`，可以分别测量真实 solver 执行与真实 Claude CLI proposal 质量。
  - CLI 增加 `--repeat`，重复运行结果写入 `comparison/repeat_summary.json`，为 timing / stability / flaky 判断提供入口。
  - Octave agent lane 增加 adaptive prototype：Claude proposal 可以参数化 extension inline script，validation 失败后可触发 bounded repair loop，并记录 `repair=True` / `llm_call=True` attempt。
  - QCompute × ABACUS 的 `abacus-hs-bridge-pending` 仍保持 truthful skip，但新增 `bridge_status.json`，明确 parser/converter/promotion milestone。
  - `/home/linden/.claude/skills/mhe-benchmark-iteration/` 已补充 real Claude/real solver gate、adaptive-agent protocol、repeat-run reporting、公平性检查和 backlog 模板。

  仍不能声称的结论：
  - 上述改动是 benchmark infrastructure 的实现，不等价于已经证明 MHE extension 在真实数值精度或 runtime 上优于 direct Claude Code。
  - 真实数值结论仍需要安装对应 solver / simulator，使用 `--allow-real-tools`，并结合 `--allow-real-claude`、`--repeat N` 生成新的 comparison bundle 后再写报告。
