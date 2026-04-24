# ABACUS / DeepMD / JEDI Wiki 修订提纲报告

## 目的

本报告把三套 extension wiki 的后续修订工作，按“文件 -> 章节 -> 具体修订动作”的方式拆开，便于直接执行文档更新。

修订基线来自本轮已落地的 MHE 主干强化：

- `PromotionContext` 与 `ValidationIssue.blocks_promotion`
- policy-gated `HarnessRuntime.commit_graph()`
- `SessionEvent` / `SessionStore` 运行时证据流
- manifest `policy.credentials` / `policy.sandbox`
- protected-component enforcement
- governed hot-swap / checkpoint / audit / provenance evidence
- `ScoredEvidence`
- `BrainProvider` seam

本报告不要求三套 wiki 全部统一成同一模版，但要求它们都明确说明：

1. 扩展如何接入当前 strengthened MHE 的 promotion authority；
2. 扩展的 validator / policy / protected boundary 如何参与图治理；
3. 扩展的 artifacts / validation / evidence 如何映射到 session / audit / provenance；
4. roadmap 中哪些内容已实现，哪些仍是待对齐项。

---

# 一、ABACUS Wiki 修订提纲

## A. `docs/wiki/meta-harness-engineer/abacus-engine-wiki/README.md`

### 建议修订段落

- `## 当前状态`
- `## 定位`
- `## 与其他 wiki 的关系`
- `## 阅读建议`

### 具体修订动作

- 在 `## 当前状态` 中，把“Phase 0-3 已完成，Phase 4 进入主线”保留，但补一句：当前 ABACUS wiki 需要与 strengthened MHE governance / evidence 基线对齐。
- 在 `## 定位` 中新增一段，明确 ABACUS 扩展不只是 file-driven workflow 封装，还要进入：
  - promotion-reviewed candidate path
  - manifest policy declaration
  - protected governance boundary
  - session / audit / provenance evidence flow
- 在 `## 与其他 wiki 的关系` 中补充与 `meta-harness-wiki` 的新关系：ABACUS 现在应依赖 runtime-level promotion / evidence authority，而不是只依赖局部 validator。
- 在 `## 阅读建议` 前或后新增一个短小的“阅读前提 / 当前文档缺口”提示，说明 `03/04/05/06` 中有新增治理语义需要同步吸收。

## B. `docs/wiki/meta-harness-engineer/abacus-engine-wiki/02-workflow-and-components.md`

### 建议修订段落

- `## 2.1 组件链总览`
- `### AbacusGateway`
- `### AbacusEnvironmentProbe`
- `### AbacusExecutor`
- `### AbacusValidator`
- `## 2.8 首版最小 happy path`

### 具体修订动作

- 在 `## 2.1 组件链总览` 末尾新增一小节“与 MHE promotion path 的关系”，说明 ABACUS 组件链的输出最终服务于 `HarnessRuntime.commit_graph()` 后的统一 candidate promotion，而不是 extension-local 决策。
- 在 `AbacusGateway` 段补写 manifest credential / subject / claim 约束的输入边界。
- 在 `AbacusEnvironmentProbe` 段补写：环境探测结果不仅影响是否能运行，还应作为 validator / policy 的 prerequisites evidence。
- 在 `AbacusExecutor` 段补写 sandbox / launcher / binary 约束已经进入 manifest/runtime policy surface。
- 在 `AbacusValidator` 段补写：
  - validator 是 governance component / protected boundary；
  - 它的验证结果应能被提升为 promotion-blocking evidence；
  - “没跑起来 / 跑了但证据不足 / 通过但仍需 policy 审核”应与 runtime governance 兼容。
- 在 happy path 末尾补一段“promotion-ready outcome”，说明从 workspace/artifact 成功到 active graph promotion 之间还有统一治理门。

## C. `docs/wiki/meta-harness-engineer/abacus-engine-wiki/03-contracts-and-artifacts.md`

### 建议修订段落

- `## 3.5 环境报告`
- `## 3.7 运行产物`
- `## 3.8 验证报告`
- `## 3.9 证据面`
- `## 3.10 首版 contract 边界`

### 具体修订动作

- 在 `## 3.5 环境报告` 中新增字段语义说明：环境报告不仅用于本地 preflight，也应承载 promotion prerequisites / missing prereq evidence。
- 在 `## 3.7 运行产物` 中补写 artifact 与 session evidence 的映射关系，例如关键运行输出如何成为 audit/provenance 锚点的上游输入。
- 在 `## 3.8 验证报告` 中补入：
  - promotion-readiness / governance-readiness 语义；
  - 哪些失败属于 `blocks_promotion` 候选；
  - validator 结果如何衔接 policy review。
- 在 `## 3.9 证据面` 中扩展“证据”定义，不只列文件，还要列：
  - environment prerequisite evidence
  - candidate / graph version / checkpoint / audit refs
  - session event linkage 的预期形状
- 在 `## 3.10` 里明确当前不要求 ABACUS 自己实现 session store，但要求 contracts/evidence 不与统一 runtime evidence flow 冲突。

## D. `docs/wiki/meta-harness-engineer/abacus-engine-wiki/04-extension-blueprint.md`

### 建议修订段落

- `## 4.3 组件链`
- `### AbacusExecutor`
- `### AbacusValidator`
- `## 4.7 产物与 evidence 设计`
- `## 4.8 failure taxonomy`
- `## 4.9 首版明确不做的内容`

### 具体修订动作

- 在 `组件链` 总述中新增“治理集成”条目，说明 blueprint 要以 strengthened MHE 为宿主，而非独立 pipeline。
- 在 `AbacusExecutor` 段补上 manifest policy / sandbox / launcher capability 的声明责任。
- 在 `AbacusValidator` 段补上 protected governance component 的定位，以及它如何与 policy review / promotion blocker 协作。
- 在 `产物与 evidence 设计` 中增加一个小节“runtime evidence integration”，解释 ABACUS artifact/evidence 与 session / audit / provenance 的对接接口。
- 在 `failure taxonomy` 中增加“promotion blocker / protected violation / prerequisite missing”三类治理相关失败。
- 在 `不做的内容` 中澄清：当前不要求 ABACUS 自己实现 hot-swap / recovery 机制，但必须保证 validator/environment/executor 语义可被 runtime hot-swap governance 正确消费。

## E. `docs/wiki/meta-harness-engineer/abacus-engine-wiki/05-roadmap.md`

### 建议修订段落

- `## 5.6 Phase 4：Examples / Study / Governance Hardening`
- `## 5.7 测试路线图`
- `## 5.8 首版 acceptance bar`

### 具体修订动作

- 把 `Phase 4` 从“未来治理硬化”改成“对齐当前 strengthened MHE governance primitives”。
- 在 `Phase 4` 任务中明确加入：
  - manifest credential/sandbox policy 补写
  - validator 作为 protected governance component 的文档对齐
  - session/audit/provenance evidence 对齐
  - promotion-ready validation semantics
- 在测试路线图里加入与 governance 相关的测试目标：promotion blocker、protected boundary、environment prerequisite evidence。
- 在 acceptance bar 中补充“文档与代码一致性要求”：已实现能力与 roadmap 不得继续写成纯规划。

## F. `docs/wiki/meta-harness-engineer/abacus-engine-wiki/06-implementation-hardening-checklist.md`

### 建议修订段落

- `## 6.3 environment probe 必须补严的规则`
- `## 6.6 executor 必须补严的规则`
- `## 6.7 validator 必须补严的规则`
- `## 6.10 可以直接作为实现 gate 的完成标准`

### 具体修订动作

- 在 `6.3` 下增加一条：probe 输出必须能区分运行前提缺失与运行失败，并可映射为治理证据。
- 在 `6.6` 下增加一条：executor 的 command / launcher / binary / sandbox tier 语义必须与 manifest policy 对齐。
- 在 `6.7` 下增加两条：
  - validator 输出应可表达 promotion-blocking 条件；
  - validator 作为 protected governance component 时，其边界不可被隐式绕开。
- 在 `6.10` 完成标准中加入：
  - evidence 可被 runtime session/audit/provenance 消费；
  - 关键治理语义已写入 wiki，不再只存在于代码或测试。

---

# 二、DeepMD Wiki 修订提纲

## A. `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/README.md`

### 建议修订段落

- `## 定位`
- `## 阅读建议`
- 新增 `## 当前状态`

### 具体修订动作

- 在 `## 定位` 中补写：DeepMD 扩展当前不只是 JSON + executor wrapper，也已经进入 evidence / policy / study / governance 的较完整实现阶段。
- 新增一个 `## 当前状态`，简述：
  - DeePMD minimal train/test 已有
  - DP-GEN run / simplify / autotest 已有
  - validator / policy / study 已有
  - 当前剩余工作主要是进一步对齐 strengthened MHE promotion/evidence path
- 在 `## 阅读建议` 附近提示：`05-roadmap` 应按“已实现 / 待补齐”阅读，而不是纯未来规划。

## B. `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/02-workflow-and-components.md`

### 建议修订段落

- `### DeepMDValidator`
- `### DeepMDEvidenceManager`
- `### DPGenValidator`
- `## 2.4 首版运行语义`

### 具体修订动作

- 在 `DeepMDValidator` 与 `DPGenValidator` 段补上：
  - validator 的 protected / governance 角色
  - 哪些验证结果会升级为 promotion blockers
  - validator 如何与 policy 共同形成 allow/defer/reject path
- 在 `DeepMDEvidenceManager` 段补上：evidence 已不只是归档文件，而是 policy-bearing / promotion-bearing 输入。
- 在 `2.4` 运行语义中新增一段“与 MHE graph promotion 的关系”，说明 extension-local evidence 最终要进入 runtime-level authority path。

## C. `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/03-contracts-and-artifacts.md`

### 建议修订段落

- `### DeepMDExecutionMode`
- `### DeepMDValidationReport`
- `### DPGenValidationReport`
- `## 3.5 Evidence bundle`
- `## 3.6 验证边界`
- `## 3.7 未来 mutation / study 约束`

### 具体修订动作

- 更新 `DeepMDExecutionMode` / 相关 contracts 说明，使其明确覆盖当前已实现的 `dpgen_run`、`dpgen_simplify`、`dpgen_autotest` 等执行模式。
- 在 `DeepMDValidationReport` / `DPGenValidationReport` 中补写新的状态与结果语义，如 baseline/simplify/autotest/converged 等阶段性判据。
- 在 `Evidence bundle` 中补入：
  - validation completeness
  - DP-GEN iteration evidence
  - autotest property evidence
  - relabeling / transfer-learning 风险提示
  - session / provenance / policy refs 预期
- 在 `验证边界` 中增加一小节，解释“工程通过 / 科学通过 / promotion-ready / policy-defer”四类边界关系。
- 在 `3.7` 中把 study 从纯未来约束改成“已有实现 + 待补齐到 ScoredEvidence / BrainProvider seam”的结构。

## D. `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/04-extension-blueprint.md`

### 建议修订段落

- `### 平台层：MHE 继续负责`
- `## 4.4 槽位与能力蓝图`
- `## 4.6 关键执行语义`
- `## 4.7 首版验证与 evidence 蓝图`

### 具体修订动作

- 在 “平台层：MHE 继续负责” 中明确补入当前已落地的平台能力：promotion context、policy-gated commit、session evidence、protected enforcement、manifest policy。
- 在 `槽位与能力蓝图` 中补入建议 protected slots 与 governance responsibility 的解释，避免把 validator/policy 写成普通 helper。
- 在 `关键执行语义` 中增加“validator / policy / study 如何进入 promotion authority”的说明。
- 在 `验证与 evidence 蓝图` 中增加一节“governance-bearing evidence”，明确 extension evidence 如何被 runtime safety/policy 路径消费。

## E. `docs/wiki/meta-harness-engineer/deepmd-engine-wiki/05-roadmap.md`

### 建议修订方式

- 不再把全文保留为纯未来 phase plan；改成“已实现 / 待补齐”的混合路线图。

### 具体修订动作

- 在 `5.1 推荐执行顺序` 前或后新增一段“当前实现快照”。
- 将 `Phase 0` 到 `Phase 6` 逐段加上状态标记，例如：
  - 已完成
  - 已部分完成
  - 待对齐 strengthened MHE
- 把原来的 `Governance Hardening` 从泛化计划，细化成：
  - promotion-context aware validation
  - session event/store emission
  - scored evidence unification
  - manifest policy / HPC / credential boundary文档对齐
- 在 `里程碑` 里同步更新，避免把已存在的 study/policy/autotest 仍写成未来里程碑。

---

# 三、JEDI Wiki 修订提纲

## A. `docs/wiki/meta-harness-engineer/jedi-engine-wiki/README.md`

### 建议修订段落

- `## 本目录的设计原则`
- `## 与 blueprint / roadmap 的关系`
- `## 当前推荐阅读顺序`

### 具体修订动作

- 在设计原则中补一句：JEDI 现阶段不仅是 evidence-first extension，也需要与 strengthened MHE promotion governance 兼容。
- 在与 blueprint/roadmap 的关系中补充：当前代码已落地 smoke policy、diagnostics enrichment、study，因此本 wiki 不应继续把这些能力视为远期想法。
- 在阅读顺序中给出一句提醒：读 `05/06/08/09` 时要以“当前实现 + governance integration”视角理解，而不是只看 extension-local pipeline。

## B. `docs/wiki/meta-harness-engineer/jedi-engine-wiki/03-contracts.md`

### 建议修订段落

- `## 3.5 environment / run / validation contracts`
- `### JediValidationReport`
- `## 3.8 面向后续 phase 的可扩展性`

### 具体修订动作

- 在 environment/run/validation contracts 总述里增加一段：这些 contract 不只面向 local execution，也要能服务于 promotion gating。
- 在 `JediValidationReport` 段补写：
  - diagnostics/evidence 如何升级为 promotion-readiness 信号；
  - 哪些条件可能被视为 `blocks_promotion`；
  - validator 作为 protected governance component 的上下游关系。
- 在 `3.8` 中补入：后续扩展点应考虑 `ScoredEvidence`、session/provenance refs、BrainProvider seam，而不仅是 compiler family 扩展。

## C. `docs/wiki/meta-harness-engineer/jedi-engine-wiki/05-environment-and-validation.md`

### 建议修订段落

- `## 5.3 failure taxonomy`
- `## 5.4 evidence-first report`
- `## 5.5 diagnostics 在首版中的位置`

### 具体修订动作

- 在 `failure taxonomy` 中加入治理相关分类：
  - environment prerequisite missing
  - protected boundary violation
  - promotion blocker
  - evidence incomplete / policy defer
- 在 `evidence-first report` 中扩展 evidence 的定义，不只写 `evidence_files`，还要加：
  - candidate / graph version / session event refs
  - audit / provenance linkage 的预期
  - diagnostics 作为 governance-grade evidence 的位置
- 在 `diagnostics` 段落中说明：现在 diagnostics enrichment 已经是现状，不是单纯后续阶段。

## D. `docs/wiki/meta-harness-engineer/jedi-engine-wiki/06-implementation-phases.md`

### 建议修订段落

- `### Phase 1`
- `### Phase 2+`
- `## 6.5 reviewer 关注点`

### 具体修订动作

- 把 `Phase 1` 中 smoke policy、diagnostics、study 等内容改成“已落地 / 当前基线”。
- 将 `Phase 2+` 改写为“剩余对齐项”，集中写：
  - promotion governance compatibility
  - manifest policy hardening
  - session/evidence integration
  - richer scored evidence
- 在 reviewer 关注点中加入一条：review 不仅看 pipeline correctness，也看是否与 strengthened MHE governance model 对齐。

## E. `docs/wiki/meta-harness-engineer/jedi-engine-wiki/08-packaging-and-registration.md`

### 建议修订段落

- `## 8.4 capabilities 与 slots`
- `## 8.5 manifest 设计`
- `## 8.7 与现有扩展的一致性`

### 具体修订动作

- 在 capabilities / slots 章节补写 protected slots / governance slots 的语义，避免 manifest 被理解成纯注册元数据。
- 在 `manifest 设计` 中补入：
  - `kind`（`core` / `governance`）
  - `safety.protected`
  - `policy.credentials`
  - `policy.sandbox`
  - legacy `safety.sandbox_profile` 的兼容说明
- 在 `与现有扩展的一致性` 中增加与 ABACUS / DeepMD / Nektar 一致的治理基线说明。

## F. `docs/wiki/meta-harness-engineer/jedi-engine-wiki/09-testing-and-review.md`

### 建议修订段落

- `## 9.2 推荐测试层次`
- `## 9.3 首版测试文件建议`
- `## 9.4 reviewer checklist`
- `## 9.6 Phase 演进时的测试策略`

### 具体修订动作

- 在测试层次中新增 governance-oriented coverage：
  - manifest policy coverage
  - protected validator / promotion blocking coverage
  - diagnostics/evidence → promotion-readiness coverage
- 在首版测试文件建议中补入已存在的 smoke policy / diagnostics / manifest 相关测试事实。
- 在 reviewer checklist 中增加：
  - 文档是否错误地把已实现能力写成未来规划
  - 语义是否与 strengthened MHE governance/evidence model 冲突
- 在 Phase 演进策略中补一句：hot-swap/session-event 相关内容当前只作为 governance integration hook 测，不作为 JEDI 自主执行主线。

---

# 四、三套 Wiki 的统一落地策略

## 建议统一新增的文档要点

每套 wiki 至少在一到两个核心文件中明确写出以下五点：

1. **Promotion authority**
   - 扩展输出如何进入 `PromotionContext` / `commit_graph()` 的统一路径。

2. **Protected boundary**
   - 哪个 validator / policy / slot 是 protected governance boundary。

3. **Manifest policy**
   - `policy.credentials` / `policy.sandbox` / `safety.protected` 如何使用。

4. **Evidence integration**
   - extension artifacts / validation / diagnostics 如何映射到 session / audit / provenance。

5. **Roadmap truthfulness**
   - 已实现的能力要从“计划”改写为“现状”；剩余工作要写成“待对齐 strengthened MHE 的具体缺口”。

## 建议执行顺序

1. 先改三套 `README.md`，统一读者预期。
2. 再改各自最关键的 contracts / validation / blueprint / packaging 文件。
3. 最后改 roadmap / checklist / testing 文件，把 phase 状态与测试建议校准到当前实现。

## 交付标准

修订完成后，应满足：

- 任意一份 wiki 不再把当前已落地能力写成纯 future plan。
- 任意一份 wiki 都能回答“这个扩展如何进入 strengthened MHE 的 promotion / policy / evidence 主路径”。
- 三套 wiki 的治理术语不互相冲突，且与 `docs/MHE_RECENT_WORK_REPORT.md` 的主线叙述一致。
- 三套 wiki 不需要照搬同一模板，但都能落到各自 extension 的真实代码能力与约束上。