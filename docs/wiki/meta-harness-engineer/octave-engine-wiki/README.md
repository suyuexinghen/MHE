# Octave Extension for MHE Wiki

> 版本：v0.1 | 最后更新：2026-04-27

本目录只讨论**如何在 `MHE` 中设计 `metaharness_ext.octave`**。

它关注的是扩展层的长期设计边界：application family、typed contracts、component pipeline、environment / validation / evidence surface、security / governance seam、packaging / registration、v2 alignment 与科学工作流演化。

本目录**不再承载**以下内容作为主线：

- 分阶段实施细节
- 文件级脚手架清单
- 当前实现状态盘点
- roadmap / milestone 推进说明
- 混合在设计文档中的 implementation plan 叙述

这些内容统一下沉到 `blueprint/07-octave-extension-blueprint.md` 中的正式文档。

---

## 目录导航

| 文档 | 主题 | 读者 |
|------|------|------|
| [01-概述与定位](01-overview.md) | Octave 扩展的设计定位、v1/v2/v3 分层、平台与扩展职责划分 | 所有人 |
| [02-工作流与组件链](02-workflow-and-components.md) | Gateway → EnvironmentProbe → Compiler → Executor → Validator → EvidencePolicy 组件链 | 架构师 / 运行时工程师 |
| [03-Contracts 与产物](03-contracts-and-artifacts.md) | family-aware typed contracts、run plan、run artifact、validation report、evidence bundle | 核心开发 |
| [04-环境、验证与证据](04-environment-validation-evidence.md) | environment probe、validation 状态机、warning 分类、evidence policy seam | 运行时 / reviewer |
| [05-安全与治理](05-security-and-governance.md) | 安全模型、sandbox tier、static script scanner、governance adapter、protected component | 平台 / 治理 / reviewer |
| [06-封装与注册](06-packaging-and-registration.md) | 包结构、exports、capabilities、slots、manifest 与 component registration | 核心开发 / reviewer |
| [07-v2 对齐方案](07-v2-alignment.md) | v2 Scientific Context Adapter、Study Workflow、Execution/HPC、Governance/Optimizer Bridge | 架构师 / 平台 |
| [08-测试与路线图](08-testing-and-roadmap.md) | 测试策略、pytest marker、Phase 0–5 roadmap、完成判据 | 核心开发 / QA |
| [09-范围与分工](09-scope-and-boundaries.md) | 首版支持/不支持边界、与原始愿景的关系、与其他 extension 的分工 | 文档维护者 / reviewer |

---

## 术语约定

- prose 中使用 **application family**；代码字面量写作 `script_run`、`function_eval`、`numeric_benchmark`
- prose 中使用 **wrapper**；代码文件写作 `wrapper.m`（编译器生成的受控入口脚本）
- prose 中使用 **governance state**；代码字面量写作 `ready`、`defer`、`blocked`（与 DeepMD 惯例一致）
- **family** 表示扩展层支持的受控工作流族边界；**baseline** 表示某个 family 下的一次完整执行
- **run artifact** 指一次 `octave-cli` 执行产出的结构化结果；**evidence files** 指对外暴露的关键证据文件
- **policy seam** 指 `OctaveEvidencePolicy.evaluate(...)` 这一层，把 extension-local 结果整理成下游可消费的 governance 输入
- **wrapper-first** 表示所有 Octave 执行都必须通过编译器生成的受控 wrapper `.m`，不直接透传任意脚本
- **`--no-init-file`** 是 GNU Octave 的启动标志，阻止加载 `~/.octaverc`，保证执行环境可复现

---

## 设计原则

`metaharness_ext.octave` 的首版设计应被理解为：

- **CLI-first** 的 typed extension
- 以 **typed spec + wrapper `.m`** 为稳定控制面
- 以 **workspace + executable** 为执行面
- 以 **environment probe + validation report** 为失败边界
- 以 **artifact / diagnostics / evidence / policy** 为证据面
- 以 **typed study + mutation proposal** 为最小研究入口

因此本目录的重点是**设计边界与职责分层**，而不是交付顺序。

---

## 与 `blueprint/` 的分工

Octave 扩展的正式实施材料位于 `MHE/docs/wiki/meta-harness-engineer/blueprint/`：

- `07-octave-extension-blueprint.md`：正式设计蓝图（proposal 状态）

分工原则如下：

- **本 wiki**：回答"这个扩展应如何被设计"
- **blueprint**：回答"正式设计主张是什么"
- **v2 alignment**：回答"如何从 v1 worker 升级为 v2 scientific workflow substrate"

---

## 设计来源

本 wiki 的架构吸收并融合了以下设计思想：

- [meta-harness-wiki](../meta-harness-wiki/)：component SDK、manifest、contracts、runtime、policy、hot reload
- [deepmd-engine-wiki](../deepmd-engine-wiki/)：gateway-pipeline 模式、study component、governance adapter
- [jedi-engine-wiki](../jedi-engine-wiki/)：contracts、execution pipeline、environment/validation pattern
- `docs/.trash/plan/Octave-Ext.md`：原始六层 AI-native 科学计算平台愿景（v1 范围约束、v2/v3 方向参考）

---

## 推荐阅读顺序

### 想先理解扩展的设计定位

先看：[01-概述与定位](01-overview.md) → [02-工作流与组件链](02-workflow-and-components.md) → [03-Contracts 与产物](03-contracts-and-artifacts.md)

### 想理解失败语义与治理接缝

先看：[04-环境、验证与证据](04-environment-validation-evidence.md) → [05-安全与治理](05-security-and-governance.md)

### 想理解注册面与部署形态

先看：[06-封装与注册](06-packaging-and-registration.md)

### 想理解 v2 科学工作流演化方向

先看：[07-v2 对齐方案](07-v2-alignment.md)

### 想看实施材料与路线

转到：`blueprint/07-octave-extension-blueprint.md`

---

## 不在本目录展开的内容

以下内容不再作为本目录主线：

- GNU Octave 软件本体的完整教程
- MATLAB 兼容性百科或迁移指南
- Octave package 生态的 exhaustive 列表
- 全量 HPC / scheduler 编排细节
- rollout phase 的日常推进说明

本目录只保留**设计 `metaharness_ext.octave` 所必需**的内容。
