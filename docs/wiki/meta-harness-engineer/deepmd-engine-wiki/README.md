# DeepMD Engine 技术手册 / 软件 Wiki

> 版本：v0.1 | 最后更新：2026-04-22

本目录面向 `MHE/src/metaharness_ext/deepmd` 的规划与后续实现，适合以下读者：

- 需要在 `Meta-Harness` 中接入 `DeePMD-kit / DP-GEN` 工作流的研发人员
- 需要理解 `data prep / train / freeze / compress / test / run / autotest` 如何落到 MHE 组件链中的架构师
- 需要维护 `config compiler / executor / diagnostics / validator / evidence` 的工程师
- 需要把 DeePMD 训练、DP-GEN 并发学习或 transfer-learning 纳入受控运行时的平台人员

---

## 文档目录

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-概述与定位](01-overview.md) | DeepMD / DP-GEN 工作流背景、与 MHE 的对接价值、首版接口选择 | 所有人 |
| [02-工作流与组件链](02-workflow-and-components.md) | DeePMD-kit 与 DP-GEN 的 staged workflow、组件职责与执行流 | 架构师 / 运行时工程师 |
| [03-Contracts 与产物](03-contracts-and-artifacts.md) | typed specs、run artifacts、diagnostics、evidence 与验证语义 | 核心开发 / 配置工程师 |
| [04-扩展蓝图](04-extension-blueprint.md) | `metaharness_ext.deepmd` 的正式实现蓝图与首版范围边界 | 架构师 / 扩展开发 |
| [05-路线图](05-roadmap.md) | 按 phase 拆解的正式执行路线与验收标准 | 项目负责人 / 实施工程师 |

---

## 定位

`metaharness_ext.deepmd` 的首阶段目标，不是重写 DeePMD-kit 的训练内核，也不是把 DP-GEN 退化成任意 shell pipeline，而是先把 DeepModeling 生态中稳定的控制平面纳入 MHE：

- **配置面**：`input.json`、`param.json`、`machine.json`
- **执行面**：`dp`、`dpgen`、`lmp` 以及外部 first-principles 程序的受控调用
- **证据面**：`lcurve.out`、checkpoint、frozen/compressed model、`model_devi.out`、`record.dpgen`、autotest 输出
- **治理面**：typed contracts、validator、预算 / HPC / relabeling 风险控制、审计与后续参数研究

当前它已不只是 “JSON config + executor wrapper”。现有实现已经覆盖 DeePMD minimal train/test、DP-GEN `run` / `simplify` / `autotest`、typed validator、evidence bundle、policy evaluation 与 study baseline，并且这些输出预期进入 MHE 的统一 promotion / policy / provenance authority path，而不是停留在 extension-local 的局部判断。

这意味着首版会优先采取 **"JSON config + executable wrapper"** 路线，而不是训练框架内嵌或底层 TensorFlow/PyTorch API 直连路线；但在当前实现现实里，这条路线已经自然延伸到了 evidence / policy / study / governance-bearing delivery。

---

## 当前状态

当前 DeepMD 扩展已经完成并受测试覆盖或直接实现支撑的基线包括：

- DeePMD `train` / `freeze` / `compress` / `test` / `model_devi` / `neighbor_stat`
- DP-GEN `dpgen_run` / `dpgen_simplify` / `dpgen_autotest`
- mode-aware validator、DP-GEN iteration collection、autotest property summary
- evidence bundle 与 policy `allow` / `defer` / `reject` 决策
- study baseline 与 mutation white-list

因此本目录后续阅读不应再把 DeepMD wiki 视为纯前瞻设计文档。当前剩余工作主要是继续把这些现有能力与 strengthened MHE 的 promotion context、protected governance boundary、session / audit / provenance evidence path 写得更一致、更明确。

---

## 首版环境假设

首版文档与实现都应把 DeepMD / DP-GEN 的外部依赖闭包说清楚，而不是只写成“需要 DeePMD 环境”：

- DeePMD 基础链至少需要 `dp`、`python`，通常还需要 `dpdata` 做数据整理或格式转换
- DP-GEN 工作流至少需要 `dpgen`，分布式训练场景通常还需要 Horovod/MPI 运行时，如 `mpirun`
- 推理或下游集成场景可能需要 `lmp`、Python runtime、C/C++ runtime，取决于目标部署路径
- `machine.json`、remote root、scheduler、外部 first-principles backend 应视作环境前提，而不是训练逻辑的一部分
- 首版 validator 应把“缺少外部命令、数据目录、初始模型、FP backend、remote/scheduler 配置”判定为 environment failure 或 policy prerequisite，而不是模型失败

这也意味着：`metaharness_ext.deepmd` 的首版不应把完整 HPC / 标注后端可用性当成默认假设，而应优先围绕本地可验证的 DeePMD minimal path 构建稳定闭环。

---

## 当前依据

本目录的设计依据来自三类材料：

1. 本地 DeepModeling 教程材料
   - `/home/linden/code/julia/GSICoreAnalysis.jl/docs/deepmodeling-tutorials/README.md`
   - `/home/linden/code/julia/GSICoreAnalysis.jl/docs/deepmodeling-tutorials/source/Tutorials/DeePMD-kit/learnDoc/Handson-Tutorial(v2.0.3).md`
   - `/home/linden/code/julia/GSICoreAnalysis.jl/docs/deepmodeling-tutorials/source/Tutorials/DP-GEN/learnDoc/DP-GEN_handson.md`
   - `/home/linden/code/julia/GSICoreAnalysis.jl/docs/deepmodeling-tutorials/source/CaseStudies/Practical-Guidelines-for-DP/Practical-Guidelines-for-DP.md`
   - `/home/linden/code/julia/GSICoreAnalysis.jl/docs/deepmodeling-tutorials/source/CaseStudies/Transfer-learning/Transfer-learning.md`
2. 本仓库已有 Meta-Harness 扩展设计
   - `meta-harness-wiki/README.md`
   - `nektar-engine-wiki/README.md`
   - `jedi-engine-wiki/README.md`
   - `blueprint/03-ai4pde-implementation-blueprint.md`
3. 当前 MHE 的通用设计边界
   - `HarnessComponent` / manifest / runtime / graph candidate / validator / evidence-first delivery 语义

---

## 阅读建议

阅读本目录时，建议把 [05-路线图](05-roadmap.md) 理解为“已实现基线 + 待对齐 strengthened MHE 的剩余缺口”，而不是纯未来 phase plan。

### 如果你想先理解 DeepMD 为什么适合接入 MHE

先看：[01-概述与定位](01-overview.md)

### 如果你想直接开始设计组件链

先看：[02-工作流与组件链](02-workflow-and-components.md) → [04-扩展蓝图](04-extension-blueprint.md)

### 如果你想先定义 typed contracts

先看：[03-Contracts 与产物](03-contracts-and-artifacts.md)

### 如果你想做正式实施拆解

先看：[05-路线图](05-roadmap.md)

---

## 与其他 wiki 的关系

- 与 [meta-harness-wiki](../meta-harness-wiki/README.md) 的关系：后者描述通用 `Meta-Harness SDK / Runtime / ConnectionEngine`；本目录描述其上的 `DeepMD / DP-GEN` 域扩展方案。当前 DeepMD validator / policy / evidence 语义应依赖 runtime-level promotion / policy / provenance authority，而不是只停留在 extension-local validator 结论。
- 与 [nektar-engine-wiki](../nektar-engine-wiki/README.md) 的关系：两者都采用 `compiler -> executor -> diagnostics / validator` 的受控求解器/训练器扩展模式，但 DeepMD 的配置面是 JSON + 多阶段目录工作流，而非 XML + 单 solver binary。
- 与 [jedi-engine-wiki](../jedi-engine-wiki/README.md) 的关系：两者都更适合包装“声明式配置 + 外部可执行程序”的稳定控制面；JEDI 偏向 `YAML + MPI executable`，DeepMD 偏向 `JSON + training/iteration workspace`。
- 与 [ai4pde-agent-wiki](../ai4pde-agent-wiki/README.md) 的关系：后者是上层科学智能体 / runtime，本目录是其中可接入的一类 ML potential / concurrent learning 后端。
