# 06. 设计文档分工

## 6.1 为什么这一页不再写实施路线

JEDI wiki 的职责应是解释 `metaharness_ext.jedi` 的 **设计边界**，而不是混合承担 roadmap、implementation plan 与当前实现状态记录。

因此这一页不再展开：

- Phase 0 / Phase 1 / Phase 2+ 的详细推进顺序
- 文件级脚手架清单
- 当前已实现能力盘点
- 里程碑与验收条目

这些内容统一放入 `blueprint/` 目录维护。

---

## 6.2 四类文档的职责分工

`metaharness_ext.jedi` 当前有四类互补文档：

- `blueprint/01-jedi-extension-blueprint.md`
  - 定义正式设计立场、组件链与边界
- `blueprint/01-jedi-extension-roadmap.md`
  - 定义阶段顺序、里程碑与 baseline 推进节奏
- `blueprint/01-jedi-extension-implementation-plan.md`
  - 定义当前阶段的文件、步骤、测试与验收标准
- `jedi-engine-wiki/*.md`
  - 把上述正式主张拆成面向实现与评审的设计说明

简化来说：

- **wiki** 解释“怎么设计”
- **blueprint** 解释“正式主张是什么”
- **roadmap** 解释“先做什么、后做什么”
- **implementation plan** 解释“这一阶段具体怎么落地”

---

## 6.3 本 wiki 保留什么

JEDI wiki 应长期保留以下内容：

- extension positioning
- architecture chain
- family-aware contracts
- execution semantics
- environment / validation taxonomy
- family boundaries
- packaging / registration semantics
- testing / review invariants

这些内容具有较强稳定性，适合作为设计资产长期维护。

---

## 6.4 本 wiki 不保留什么

以下内容不应再作为 wiki 主体：

- 具体 phase 拆分
- baseline 选择顺序
- 实现时新增哪些源码文件
- 测试文件清单
- 当前哪些能力已经落地、哪些尚未落地
- implementation-phase-specific acceptance checklist

这些内容变化频率更高，也更适合放在 `blueprint/` 中统一维护。

---

## 6.5 维护原则

维护 Jedi wiki 时，应优先更新：

- 组件职责边界
- contract 形状
- failure taxonomy
- execution semantics
- reviewer checklist

而不是重新向文档中加入实施顺序或脚手架细节。

如果某段内容开始回答“这一阶段具体改哪些文件、按什么顺序交付、如何验收”，它通常更适合移动到 `blueprint/` 文档，而不是保留在 wiki 中。