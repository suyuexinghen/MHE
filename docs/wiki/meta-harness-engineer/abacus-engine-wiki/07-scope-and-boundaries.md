# 07. 范围与分工

## 7.1 为什么要把 design wiki 与 blueprint / roadmap 分开

当 engine wiki 同时承担设计、路线图、checklist 与进度盘点时，读者很容易混淆：

- 这个扩展**应该如何设计**
- 当前代码**已经实现到哪里**
- 下一步**按什么顺序推进**

对仍在开发中的 ABACUS extension 来说，这种混淆尤其危险，因为它会让文档同时显得过度承诺和过度飘忽。

---

## 7.2 design wiki 的职责

`abacus-engine-wiki/` 当前应只回答：

- family 应如何划分
- contracts / artifacts / validation 的边界是什么
- environment probe 与 protected validator 应如何解释
- packaging / registration 的治理语义是什么
- ABACUS 与 runtime authority 的接缝在哪里

也就是说，它回答的是 **长期稳定的设计问题**。

---

## 7.3 blueprint 与 roadmap 的职责

- `blueprint/05-abacus-extension-blueprint.md`：正式设计主张
- `blueprint/05-abacus-roadmap.md`：推进顺序、当前缺口与待补齐项

它们比 design wiki 更接近“当前实现主张与后续推进”，但不应再作为主 wiki 导航的一部分。

---

## 7.4 `.trash` 的职责

以下历史页面已经退出 ABACUS engine wiki 主导航：

- `.trash/abacus-engine-wiki/04-extension-blueprint.md`
- `.trash/abacus-engine-wiki/05-roadmap.md`
- `.trash/abacus-engine-wiki/06-implementation-hardening-checklist.md`

`.trash` 的作用不是删除内容，而是保留历史版本供追溯，避免旧页面继续与新的 design wiki 混读。

---

## 7.5 代码真相优先于文档快照

当文档与代码冲突时，应优先以当前代码为准，尤其是：

- `contracts.py`
- `slots.py`
- `capabilities.py`
- `manifest.json` / `validator.json`
- `gateway.py`
- `environment.py`
- `validator.py`

这条原则对 ABACUS 特别重要，因为它仍在开发中，很多边界正在继续收紧而不是已经完全封闭。

---

## 7.6 结论

ABACUS wiki 当前应保持以下分工：

- `abacus-engine-wiki/`：长期设计手册
- `blueprint/05-abacus-extension-blueprint.md`：正式设计蓝图
- `blueprint/05-abacus-roadmap.md`：当前路线与待补齐项
- `.trash/abacus-engine-wiki/*`：历史页面归档
- `src/metaharness_ext/abacus/*`：当前代码真相

只有这样，ABACUS extension 即使还在开发，也能保持清晰、可信的文档边界。
