# 07. 范围与分工

## 7.1 为什么要把 design wiki 与 blueprint / roadmap 分开

当 engine wiki 同时承担设计、实施蓝图、路线图与进度盘点时，读者很容易混淆三类问题：

- 这个扩展**应该如何设计**
- 当前代码**已经实现到哪里**
- 下一步**按什么顺序推进**

对 DeepMD 这样的扩展来说，这三类问题都重要，但不应写在同一主阅读路径里。

---

## 7.2 design wiki 的职责

`deepmd-engine-wiki/` 当前应只回答：

- family 应如何划分
- contracts / artifacts / validation / evidence 的边界是什么
- environment probe / policy seam 的正式语义是什么
- packaging / protected boundary 应如何解释
- study / mutation 应如何保持 typed boundary

也就是说，它回答的是 **长期稳定的设计问题**。

---

## 7.3 blueprint 的职责

`blueprint/04-deepmd-extension-blueprint.md` 回答的是：

- 当前正式设计主张是什么
- 哪些组件链与 contracts 是 canonical 版本
- 当前代码与治理主张如何对齐

它比 design wiki 更接近“正式设计裁决”，但仍不等同于路线图。

---

## 7.4 roadmap 的职责

`blueprint/04-deepmd-roadmap.md` 回答的是：

- 当前哪些 phase 已经实现
- 还剩哪些对齐项
- 推荐按什么顺序推进后续补齐

因此 roadmap 是“推进顺序与缺口地图”，不是 wiki 主导航的一部分。

---

## 7.5 `.trash` 的职责

以下历史页面已经退出 DeepMD engine wiki 主导航：

- `.trash/deepmd-engine-wiki/04-extension-blueprint.md`
- `.trash/deepmd-engine-wiki/05-roadmap.md`

`.trash` 的作用不是删除内容，而是：

- 保留历史文字版本以供追溯
- 避免旧页面继续与当前 design wiki 混读
- 明确主阅读路径已迁移到 design wiki + blueprint 目录

---

## 7.6 代码真相优先于文档快照

对 DeepMD 这类快速演化的扩展来说，文档是解释层，不是事实源。

当文档与代码冲突时，应优先以当前代码为准，尤其是：

- `contracts.py`
- `slots.py`
- `capabilities.py`
- `manifest.json` / `validator.json`
- `environment.py`
- `evidence.py`
- `policy.py`
- `study.py`

因此 design wiki 的正确写法应是：

- 固化长期边界
- 避免把短期推进状态写成长期设计事实
- 避免把尚未实现的上层接缝写成“已经存在”

---

## 7.7 与其他 wiki 的关系

### 与 `meta-harness-wiki`

后者描述平台级 runtime / governance / promotion authority；DeepMD wiki 描述 DeepMD 作为领域扩展时应暴露什么边界。

### 与 `jedi-engine-wiki`

JEDI wiki提供了更清晰的 design-only 结构：family、environment、packaging、review invariants 分页明确。DeepMD wiki 当前借鉴的是这种结构分工，而不是复制领域内容。

### 与 `nektar-engine-wiki` / `ai4pde-agent-wiki`

这两个目录提供了如何让 wiki 保持设计聚焦、避免被 rollout 叙述淹没的参考。

---

## 7.8 结论

DeepMD wiki 当前应保持以下分工：

- `deepmd-engine-wiki/`：长期设计手册
- `blueprint/04-deepmd-extension-blueprint.md`：正式设计蓝图
- `blueprint/04-deepmd-roadmap.md`：推进路线与剩余缺口
- `.trash/deepmd-engine-wiki/*`：历史页面归档
- `src/metaharness_ext/deepmd/*`：当前代码真相

只有这样，读者才能在不混淆“设计、现状、推进顺序”的前提下理解 DeepMD 扩展。
