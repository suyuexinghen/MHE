# 01. JEDI Extension Wiki Refocus Report

> 状态：proposed | 说明 `jedi-engine-wiki/` 如何收敛为面向 `metaharness_ext.jedi` 的设计型 wiki，并把实施性材料回收至 `blueprint/`

## 1.1 目标

本报告的目标是把 `MHE/docs/wiki/meta-harness-engineer/jedi-engine-wiki/` 明确收敛为 **JEDI DeFi / DA extension 设计 wiki**。

这里的“设计”特指：

- MHE 应以哪一层接入 JEDI
- extension 的组件链与边界如何划分
- typed contracts 应如何组织
- execution semantics 应如何定义
- environment / validation / evidence surface 应如何表达
- application family 应如何分裂
- packaging / registration / review invariants 应如何维持

而不再让 wiki 混合承担 roadmap、implementation plan、阶段验收与当前实现盘点的职责。

---

## 1.2 应保留在 wiki 中的设计材料

以下页面构成 Jedi wiki 的稳定设计主干，应保留并继续维护：

- `jedi-engine-wiki/01-extension-positioning.md`
  - 解释为什么 MHE 需要 JEDI extension，以及为何选择 Level 4 wrapper + Level 3 controlled YAML 的接口层级
- `jedi-engine-wiki/02-architecture.md`
  - 解释 gateway / environment / compiler / preprocessor / executor / validator 的组件链与分工
- `jedi-engine-wiki/03-contracts.md`
  - 解释 family-aware typed contracts 与 environment/run/validation contracts
- `jedi-engine-wiki/04-execution-pipeline.md`
  - 解释 execution mode 分层、执行链顺序与 executor 边界
- `jedi-engine-wiki/05-environment-and-validation.md`
  - 解释 environment-gated design、failure taxonomy、evidence/report semantics
- `jedi-engine-wiki/07-family-design.md`
  - 解释 `variational`、`local_ensemble_da`、`hofx`、`forecast` 的 family 边界
- `jedi-engine-wiki/08-packaging-and-registration.md`
  - 解释 package / exports / capabilities / slots / manifest 的设计边界
- `jedi-engine-wiki/09-testing-and-review.md`
  - 解释测试层次、review invariants 与边界守护要点
- `jedi-engine-wiki/README.md`
  - 作为导航页，明确本目录是设计型 wiki，而不是实施计划集合

---

## 1.3 应从 wiki 中抽离的内容

以下类型的内容不再适合作为 wiki 主体：

- 分阶段实施顺序
- baseline 选择与推进节奏
- 文件级脚手架清单
- 当前哪些能力已经实现、哪些还未实现
- 具体测试文件清单
- phase-specific acceptance checklist
- implementation-phase-specific command detail

它们变化更快，更适合在 `blueprint/` 目录中集中维护。

---

## 1.4 针对重点页面的分流建议

### `jedi-engine-wiki/04-execution-pipeline.md`

保留：

- execution mode 分层
- 规范执行链
- executable name 与 CTest test name 的边界
- executor 不理解业务 YAML 结构的设计主张

抽离或弱化：

- 过细的 command-construction 参数映射
- launcher flag 拒绝规则
- 具体 artifact layout 目录样板

这些内容更适合放入 blueprint / implementation plan 作为 contract-level 或 implementation-level 细化。

### `jedi-engine-wiki/06-implementation-phases.md`

该页应从“实施路径”重写为“设计文档分工”。

保留：

- wiki 与 blueprint / roadmap / implementation plan 的职责分工
- 维护原则

抽离：

- Phase 0 / Phase 1 / Phase 2+ 的详细推进叙述
- 当前实现基线盘点
- 文件骨架建议
- phase-aware reviewer notes

### `jedi-engine-wiki/07-family-design.md`

保留：

- family 为什么是一等设计对象
- 四类 family 的边界与结构差异
- family 与 baseline 的概念区分
- 新增 family 的判定规则

抽离或弱化：

- 把 `hofx` 作为首个 smoke baseline 候选的推进理由
- “首个正式 baseline / 第二个正式 baseline”这类交付顺序表达

这些属于 roadmap / implementation plan 的内容，而不是 family 设计本身。

### `jedi-engine-wiki/09-testing-and-review.md`

保留：

- 测试目标
- 推荐测试层次
- reviewer checklist
- 早期返工触发点
- 文档与代码共同守边界的原则

抽离：

- 具体测试文件清单
- 当前实现中已经存在哪些测试面
- 按 phase 推进的测试扩展说明

这些内容更适合放到 implementation plan 或 roadmap。

---

## 1.5 推荐的信息架构

Jedi wiki 建议长期收敛为以下结构：

1. `README.md`
   - scope、术语、阅读顺序、与 `blueprint/` 的分工
2. `01-extension-positioning.md`
   - why / scope / layer choice
3. `02-architecture.md`
   - component chain / responsibilities / non-responsibilities
4. `03-contracts.md`
   - typed boundaries / discriminated union / report models
5. `04-execution-pipeline.md`
   - execution semantics / ordering / executor boundary
6. `05-environment-and-validation.md`
   - prerequisite semantics / failure taxonomy / evidence semantics
7. `06-implementation-phases.md`
   - 仅保留文档职责分工，不再承担 phase 叙述
8. `07-family-design.md`
   - family model / family-vs-baseline distinction
9. `08-packaging-and-registration.md`
   - package / manifest / capability / slot semantics
10. `09-testing-and-review.md`
   - review/test invariants

---

## 1.6 blueprint 侧的内容承接建议

内容分流后，`blueprint/` 应按以下边界承接：

- `01-jedi-extension-blueprint.md`
  - 稳定的正式设计主张
  - contracts / architecture / environment / validation 的正式蓝图表述
- `01-jedi-extension-roadmap.md`
  - phase 顺序
  - baseline 推进节奏
  - milestone 与 risk / tradeoff
- `01-jedi-extension-implementation-plan.md`
  - 具体文件清单
  - 当前阶段实施步骤
  - 测试文件清单
  - acceptance checklist

这三者共同承担原先混入 wiki 的 implementation-heavy 内容。

---

## 1.7 重写后的写作准则

重写 Jedi wiki 时，建议始终坚持以下写法：

- 优先回答“扩展为什么这样设计”
- 明确组件边界，而不是列实施步骤
- 用 family / execution mode / evidence / validation 这些稳定术语组织内容
- 把“当前阶段怎么交付”统一转交给 `blueprint/`
- 把“当前实现已经做到哪里”从设计文档中剥离

这样处理后，Jedi wiki 将更像一套长期稳定的 extension design handbook，而不是与 roadmap / implementation plan 混写的混合文档。