# DeepMD Extension for MHE Wiki

> 版本：v0.2 | 最后更新：2026-04-24

本目录只讨论 **如何在 `MHE` 中设计 `metaharness_ext.deepmd`**。

它关注的是扩展层的长期设计边界：application family、typed contracts、environment / validation / evidence surface、packaging / registration、study seam 与治理接缝。

本目录**不再承载**以下内容作为主线：

- 分阶段实施路线
- rollout / milestone 叙述
- 文件级脚手架清单
- 当前实现进度盘点
- 混合在设计文档中的 blueprint / roadmap 文本

这些内容统一下沉到 `blueprint/` 目录中的正式文档；历史版本保留在 `.trash/` 路径中。

---

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-概述与定位](01-overview.md) | DeepModeling 生态的接口层选择、支持边界与设计定位 | 所有人 |
| [02-工作流与组件链](02-workflow-and-components.md) | gateway / compiler / executor / validator / evidence / study 的组件链 | 架构师 / 运行时工程师 |
| [03-Contracts 与产物](03-contracts-and-artifacts.md) | family-aware typed contracts、run artifact、diagnostics、study models | 核心开发 |
| [04-环境、验证与证据](04-environment-validation-and-evidence.md) | environment probe、failure taxonomy、evidence bundle、policy seam | 运行时 / reviewer |
| [05-family 设计](05-family-design.md) | `deepmd_train`、`dpgen_run`、`dpgen_simplify`、`dpgen_autotest` 的边界 | 架构师 / compiler 维护者 |
| [06-封装与注册](06-packaging-and-registration.md) | 包结构、exports、capabilities、slots、manifest 与 protected boundary | 核心开发 / reviewer |
| [07-范围与分工](07-scope-and-boundaries.md) | design wiki、blueprint、roadmap、`.trash` 与代码真相的职责分工 | 文档维护者 / reviewer |

---

## 术语约定

- prose 中使用 **application family**；代码字段写作 `application_family`
- prose 中使用 **execution mode**；代码字面量写作 `train`、`freeze`、`compress`、`test`、`model_devi`、`neighbor_stat`、`dpgen_run`、`dpgen_simplify`、`dpgen_autotest`
- **family** 表示扩展层支持的工作流族边界；**baseline** 表示某个 family 下被选中的具体运行样例
- **run artifact** 指一次运行产出的结构化结果；`evidence_files` 指对外暴露的关键证据文件
- **policy seam** 指 `build_evidence_bundle(...)` 与 `DeepMDEvidencePolicy.evaluate(...)` 这一层，把 extension-local 结果整理成下游可消费的治理输入
- **runtime handoff** 指 `candidate_record` 进入 `HarnessRuntime.ingest_candidate_record(...)` 的过程；当前 review state 通过 `external_review` 附着在 `CandidateRecord` 上

---

## 设计原则

`metaharness_ext.deepmd` 的当前设计应被理解为：

- **family-aware** 的 typed extension
- 以 **JSON** 为稳定控制面
- 以 **workspace + executable** 为执行面
- 以 **environment probe + validation report** 为失败边界
- 以 **artifact / diagnostics / evidence / policy** 为证据面
- 以 **typed mutation + study report** 为最小研究入口

因此本目录的重点是 **设计边界**，而不是交付顺序。

---

## 与 `blueprint/` 和 `.trash/` 的分工

DeepMD 扩展的正式实施材料位于 `MHE/docs/wiki/meta-harness-engineer/blueprint/`：

- `04-deepmd-extension-blueprint.md`：正式设计蓝图
- `04-deepmd-roadmap.md`：已实现 / 待补齐混合结构的路线图

历史上曾放在 engine wiki 中的旧页面已移动到：

- `MHE/docs/wiki/meta-harness-engineer/.trash/deepmd-engine-wiki/04-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/.trash/deepmd-engine-wiki/05-roadmap.md`

分工原则如下：

- **本 wiki**：回答“这个扩展应如何被设计”
- **blueprint**：回答“正式设计主张是什么”
- **roadmap**：回答“按什么顺序推进、哪些已完成、哪些待对齐”
- **.trash**：保留退出主阅读路径的历史页面，供追溯而非主导航阅读

---

## 推荐阅读顺序

### 想先理解 DeepMD 扩展的设计定位

先看：[01-概述与定位](01-overview.md) → [02-工作流与组件链](02-workflow-and-components.md) → [03-Contracts 与产物](03-contracts-and-artifacts.md)

### 想理解失败语义与治理接缝

先看：[04-环境、验证与证据](04-environment-validation-and-evidence.md)

### 想理解 family 与注册面

先看：[05-family 设计](05-family-design.md) → [06-封装与注册](06-packaging-and-registration.md)

### 想看正式实施材料

转到：`blueprint/04-deepmd-extension-blueprint.md`、`blueprint/04-deepmd-roadmap.md`

---

## 不在本目录展开的内容

以下内容不再作为本目录主线：

- DeePMD-kit / DP-GEN 软件本体的完整教程
- 全量 HPC / scheduler 编排细节
- first-principles backend 的适配百科
- rollout phase 的日常推进说明
- 逐次迭代的任务清单

如需查看上游软件本体材料，可转到外部 deepmd-kit wiki：

- `README.md`：总导航与定位
- `03-architecture.md`：上游源码结构、descriptor / fitting / backend 分层
- `05-developer-guide.md`：上游扩展点与开发者约定
- `06-faq-troubleshooting.md`：构建 / 运行 / 版本兼容问题清单

本目录只保留 **设计 `metaharness_ext.deepmd` 所必需** 的内容。
