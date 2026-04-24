# ABACUS Engine 技术手册 / 软件 Wiki

> 版本：v0.1 | 最后更新：2026-04-22

本目录面向 `MHE/src/metaharness_ext/abacus` 的规划与后续实现，适合以下读者：

- 需要在 `Meta-Harness` 中接入 `ABACUS` 工作流的研发人员
- 需要理解 `INPUT / STRU / KPT + launcher + executable` 如何落到 MHE 组件链中的架构师
- 需要维护 `environment probe / input compiler / executor / validator` 的工程师
- 需要把 `SCF / NSCF / relax / MD / ABACUS+DeePMD` 纳入受控运行时的平台人员

---

## 文档目录

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-概述与定位](01-overview.md) | ABACUS 工作流背景、与 MHE 的对接价值、首版接口层级选择 | 所有人 |
| [02-工作流与组件链](02-workflow-and-components.md) | ABACUS 的 file-driven workflow、组件职责、执行链与输出目录语义 | 架构师 / 运行时工程师 |
| [03-Contracts 与产物](03-contracts-and-artifacts.md) | typed specs、run plan、run artifact、validation report 与证据边界 | 核心开发 / 配置工程师 |
| [04-扩展蓝图](04-extension-blueprint.md) | `metaharness_ext.abacus` 的正式实现蓝图与首版范围边界 | 架构师 / 扩展开发 |
| [05-路线图](05-roadmap.md) | 按 phase 拆解的正式执行路线与验收标准 | 项目负责人 / 实施工程师 |
| [06-实现前补严清单](06-implementation-hardening-checklist.md) | 把设计陈述压缩成实现前必须机械化的 rules checklist | 架构师 / 扩展开发 / 测试工程师 |

---

## 定位

`metaharness_ext.abacus` 的目标，不是把 `ABACUS` 退化成任意 shell wrapper，也不是把它包装成“任意 INPUT 文本透传器”，而是把 ABACUS 已经稳定存在的控制平面纳入 MHE：

- **配置面**：`INPUT`、`STRU`、`KPT` 以及相关伪势/轨道/模型路径
- **执行面**：`abacus` binary + `mpirun/mpiexec/srun` 等 launcher
- **产物面**：`OUT.<suffix>/`、有效 `INPUT`、SCF 日志、结构输出、MD dump / restart 证据
- **治理面**：typed contracts、environment probe、validator、artifact-aware 审计与后续研究入口

这意味着首版会优先采取 **"typed spec -> workspace files -> launcher/executable -> structured artifacts"** 路线，而不是把 ABACUS 视为一个大而全的自由文本运行器。

在当前 strengthened MHE 语义下，ABACUS 扩展也不再只是 file-driven workflow 的受控封装。它的输出还需要进入统一的 promotion-reviewed candidate path，并对齐 manifest policy declaration、protected governance boundary，以及 session / audit / provenance evidence flow。换言之，ABACUS local validator 可以给出工程与证据判断，但 active graph promotion authority 仍属于 runtime-level governance path。

---

## 首版环境假设

首版文档与实现都应显式说明 ABACUS 的外部依赖闭包，而不是只写成“需要安装 ABACUS”：

- 至少需要 `abacus` binary
- 并行场景通常还需要 `mpirun`、`mpiexec` 或 `srun`
- 真实运行依赖工作目录中的 `INPUT`、`STRU`，以及按模式可选的 `KPT`
- `basis_type=lcao` 时通常需要伪势和轨道文件；`basis_type=pw` 依赖关系不同
- `calculation=md` 且 `esolver_type=dp` 的路径还需要 `pot_file`，并要求 ABACUS 构建时具备 DeePMD 支持
- build-time feature（如 DeePMD、GPU）应视为 environment probe 的结果，而不是默认前提

因此，`metaharness_ext.abacus` 的首版不应假设完整 HPC 与所有可选 feature 总是可用，而应先围绕本地可验证的 minimal path 建立稳定闭环。

---

## 当前依据

本目录的设计依据来自三类材料：

1. 本地 ABACUS 文档
   - `/home/linden/code/work/Solvers/abacus/docs/abacus-deepmodeling-com-en-latest.md`
   - `/home/linden/code/work/Solvers/abacus/docs/abacus-user-guide/`
2. 本仓库已有 Meta-Harness 扩展设计
   - `meta-harness-wiki/README.md`
   - `deepmd-engine-wiki/README.md`
   - `jedi-engine-wiki/README.md`
   - `nektar-engine-wiki/README.md`
3. 当前 MHE 的通用设计边界
   - `HarnessComponent` / manifest / runtime / validator / evidence-first delivery 语义

---

## 当前状态

当前实现已完成：

- Phase 0：SCF baseline
- Phase 1：NSCF / relax baseline
- Phase 2：MD baseline
- Phase 3：`md + dp` typed baseline

当前主线进入：

- Phase 4：examples / graph / regression hardening

同时，本目录需要与 strengthened MHE 的 governance / evidence 基线继续对齐，尤其是 promotion authority、protected validator / policy boundary、manifest credential / sandbox policy，以及 session / audit / provenance evidence integration 的叙述。

## 阅读前提与当前文档缺口

阅读本目录时，建议同时带着 strengthened MHE 的统一治理语义来理解。尤其是 `03` / `04` / `05` / `06` 中涉及 validator、policy、evidence、roadmap 的段落，需要按 promotion / protected boundary / runtime evidence integration 的视角吸收，而不能只按 extension-local pipeline 理解。

## 阅读建议

### 如果你想先理解 ABACUS 为什么适合接入 MHE

先看：[01-概述与定位](01-overview.md)

### 如果你想直接开始设计组件链

先看：[02-工作流与组件链](02-workflow-and-components.md) → [04-扩展蓝图](04-extension-blueprint.md)

### 如果你想先定义 typed contracts

先看：[03-Contracts 与产物](03-contracts-and-artifacts.md)

### 如果你想做正式实施拆解

先看：[05-路线图](05-roadmap.md)

### 如果你想在写代码前先把规则补严

先看：[06-实现前补严清单](06-implementation-hardening-checklist.md)

---

## 与其他 wiki 的关系

- 与 [meta-harness-wiki](../meta-harness-wiki/README.md) 的关系：后者描述通用 `Meta-Harness SDK / Runtime / ConnectionEngine`；本目录描述其上的 `ABACUS` 域扩展方案。当前关系还应补充一点：ABACUS 的 promotion-ready outcome、evidence refs 与 policy review 应依赖 runtime-level promotion / evidence authority，而不是只停留在 extension-local validator 决策。
- 与 [deepmd-engine-wiki](../deepmd-engine-wiki/README.md) 的关系：两者都采用 `gateway -> environment -> compiler -> executor -> validator` 的受控扩展模式，但 DeepMD 偏向 `JSON + workspace`，ABACUS 偏向 `INPUT/STRU/KPT + workspace + launcher`。
- 与 [jedi-engine-wiki](../jedi-engine-wiki/README.md) 的关系：两者都更适合包装“声明式配置 + 外部 executable”的稳定控制面；JEDI 偏向 `YAML + MPI executable`，ABACUS 偏向固定文件名工作目录 + launcher 驱动。
- 与 [nektar-engine-wiki](../nektar-engine-wiki/README.md) 的关系：两者都是真实数值执行后端，但 Nektar 的控制面是 session plan / XML，ABACUS 的控制面是工作目录输入文件集。
- 与 [ai4pde-agent-wiki](../ai4pde-agent-wiki/README.md) 的关系：后者是上层科学智能体 / runtime，本目录是其中一个可接入的第一性原理/原子模拟后端扩展方案。
