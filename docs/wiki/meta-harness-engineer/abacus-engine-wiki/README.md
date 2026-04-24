# ABACUS Extension for MHE Wiki

> 版本：v0.2 | 最后更新：2026-04-24

本目录只讨论 **如何在 `MHE` 中设计 `metaharness_ext.abacus`**。

它关注的是扩展层的长期设计边界：application family、typed contracts、environment / validation / evidence surface、packaging / registration，以及 ABACUS 与 strengthened MHE 治理路径的接缝。

需要特别说明的是：**ABACUS extension 仍在开发阶段，尚未完全开发完成。** 因此本目录描述的是当前设计主张、已成形边界与开发中应保持的约束，而不是“全部能力已经落地”的实现宣告。

本目录**不再承载**以下内容作为主线：

- 分阶段实施路线
- rollout / milestone 叙述
- implementation hardening checklist
- 当前实现状态盘点
- 混合在设计文档中的 blueprint / roadmap / checklist 文本

这些内容统一下沉到 `blueprint/` 目录中的正式文档；历史版本保留在 `.trash/` 路径中。

---

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-概述与定位](01-overview.md) | ABACUS 的接口层选择、支持边界与设计定位 | 所有人 |
| [02-工作流与组件链](02-workflow-and-components.md) | gateway / environment / compiler / executor / validator 的组件链 | 架构师 / 运行时工程师 |
| [03-Contracts 与产物](03-contracts-and-artifacts.md) | family-aware contracts、run plan、run artifact、validation / evidence surface | 核心开发 |
| [04-环境、验证与证据](04-environment-validation-and-evidence.md) | environment probe、failure taxonomy、evidence / governance seam | 运行时 / reviewer |
| [05-family 设计](05-family-design.md) | `scf` / `nscf` / `relax` / `md` 与 `md+dp` 的 family 边界 | 架构师 / compiler 维护者 |
| [06-封装与注册](06-packaging-and-registration.md) | 包结构、exports、capabilities、slots、manifest 与 protected boundary | 核心开发 / reviewer |
| [07-范围与分工](07-scope-and-boundaries.md) | design wiki、blueprint、roadmap、`.trash` 与代码真相的职责分工 | 文档维护者 / reviewer |
| [08-运行生命周期](08-runtime-lifecycle.md) | 从 task spec 到 `OUT.<suffix>/` 的 canonical lifecycle 与 family 差异 | 架构师 / 运行时工程师 |
| [09-核心对象与 I/O 模型](09-core-objects-and-io-model.md) | `INPUT` / `STRU` / `KPT`、assets、output root、restart 与 evidence model | 核心开发 / reviewer |

---

## 术语约定

- prose 中使用 **application family**；代码字段写作 `application_family`
- prose 中使用 **launcher**；代码字面量写作 `direct`、`mpirun`、`mpiexec`、`srun`
- **family** 表示扩展层支持的应用族边界；**baseline** 表示某个 family 下被选中的具体运行样例
- **run artifact** 指一次运行产出的结构化结果；`evidence_files` / `evidence_refs` 指 validator 与后续治理路径可消费的关键证据
- **protected boundary** 当前主要指 validator 所在治理边界，而不是整个扩展包中的所有 helper

---

## 设计原则

`metaharness_ext.abacus` 的当前设计应被理解为：

- **family-aware** 的 typed extension
- 以 **INPUT / STRU / KPT** 为稳定控制面
- 以 **workspace + launcher + executable** 为执行面
- 以 **environment probe + validation report** 为失败边界
- 以 **artifact / evidence / governance validation** 为证据面

因此本目录的重点是 **设计边界**，而不是交付顺序。

---

## 与 `blueprint/` 和 `.trash/` 的分工

ABACUS 扩展的正式实施材料位于 `MHE/docs/wiki/meta-harness-engineer/blueprint/`：

- `05-abacus-extension-blueprint.md`：正式设计蓝图
- `05-abacus-roadmap.md`：当前路线与待补齐项

历史上放在 engine wiki 中的旧页面已移动到：

- `MHE/docs/wiki/meta-harness-engineer/.trash/abacus-engine-wiki/04-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/.trash/abacus-engine-wiki/05-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/.trash/abacus-engine-wiki/06-implementation-hardening-checklist.md`

分工原则如下：

- **本 wiki**：回答“这个扩展应如何被设计”
- **blueprint**：回答“正式设计主张是什么”
- **roadmap**：回答“按什么顺序推进、当前还缺什么”
- **.trash**：保留退出主阅读路径的历史页面，供追溯而非主导航阅读

---

## 推荐阅读顺序

### 想先理解 ABACUS 扩展的设计定位

先看：[01-概述与定位](01-overview.md) → [02-工作流与组件链](02-workflow-and-components.md) → [03-Contracts 与产物](03-contracts-and-artifacts.md)

### 想理解失败语义与治理接缝

先看：[04-环境、验证与证据](04-environment-validation-and-evidence.md)

### 想理解 family 与注册面

先看：[05-family 设计](05-family-design.md) → [06-封装与注册](06-packaging-and-registration.md)

### 想理解系统如何从输入走到结果

先看：[08-运行生命周期](08-runtime-lifecycle.md) → [09-核心对象与 I/O 模型](09-core-objects-and-io-model.md)

### 想看正式实施材料

转到：`blueprint/05-abacus-extension-blueprint.md`、`blueprint/05-abacus-roadmap.md`

---

## 不在本目录展开的内容

以下内容不再作为本目录主线：

- ABACUS 软件本体的完整用户手册
- 全量 HPC / scheduler 编排细节
- 实施 checklist 与逐阶段交付顺序
- 当前哪些能力已实现到什么粒度的日常盘点

本目录只保留 **设计 `metaharness_ext.abacus` 所必需** 的内容。
