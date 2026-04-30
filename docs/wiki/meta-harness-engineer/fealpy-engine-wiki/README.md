# fealpy Extension for MHE Wiki

> Version: v1.0 | Last updated: 2026-04-30 | Status: **Complete**

本目录讨论 **如何设计 `metaharness_ext.fealpy` inside `MHE`**。

聚焦扩展层设计边界：PDE 类型家族、typed contracts、environment/validation/evidence 表面、打包与注册、与 MHE governance path 的对接缝。

**本扩展开发已完成。** 254 tests + 18 smoke gated 全部通过，ruff clean，21 个生产文件，17 个测试文件。

## 什么是 fealpy Extension

`metaharness_ext.fealpy` 是将 [fealpy](https://github.com/weihuayi/fealpy)（Python 有限元计算库）接入 MHE 的科学计算 worker。它将 fealpy 的 FEM 管道封装为可声明、可验证、可审计的 MHE component 链。

**核心能力：**
- 18 个 PDE families 通过 7 个编译器模板渲染（Lagrange/Nedelec/RT/HuZhang/Taylor-Hood FE 空间）
- 3 种计算后端（numpy/pytorch/jax）+ 6 种网格类型 + 6 种求解器方法
- 完整 MHE pipeline：Gateway → Environment → Compiler → Executor → Validator → Evidence → Policy
- 参数扫描收敛性研究（grid search + Bayesian/LLM-guided optimization）
- HPC scheduler 集成（SLURM + Kubernetes）
- Benchmark 三层 lane + 多后端对比矩阵
- 3D 资源配额管理（DOF/内存估算 + enforce gate）

## 本目录范围

本 wiki 讨论 **扩展应该如何设计**，而非实现如何分阶段执行。阶段执行、剩余 backlog 和当前进度跟踪在 `blueprint/` 下的编号文档中。

## 导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-overview](01-overview.md) | 扩展定位、范围边界、设计目标、MHE 集成缝 | 所有人 |
| [02-workflow-and-components](02-workflow-and-components.md) | 规范组件链（17 组件）、各组件职责、数据流 | 架构师/运行时工程师 |
| [03-contracts-and-artifacts](03-contracts-and-artifacts.md) | 12 Pydantic contracts、Run Plan、Run Artifact、Validation Surface | 开发者 |
| [04-environment-validation-and-evidence](04-environment-validation-and-evidence.md) | 环境探针、6 状态失败分类、5-gate policy chain | 运维/治理 |
| [05-family-design](05-family-design.md) | 18 PDE families、7 模板、5 FE 空间、family 扩展规则 | 领域专家 |
| [06-packaging-and-registration](06-packaging-and-registration.md) | 21 文件布局、69 导出、9 capabilities、7 slots、6 manifests | 打包/注册 |
| [07-scope-and-boundaries](07-scope-and-boundaries.md) | Wiki/Blueprint/Roadmap 职责划分、显式不包含内容 | 所有人 |
| [08-fealpy-extension-blueprint](../blueprint/08-fealpy-extension-blueprint.md) | 正式设计蓝图（完整版） | 所有人 |
| [08-fealpy-roadmap](../blueprint/08-fealpy-roadmap.md) | 执行路线图（Phase 0–7 全部完成） | 开发/项目管理 |

## 术语

| 术语 | 含义 |
|---|---|
| **PDE family** | fealpy 中注册的 PDE 类型（18 个已渲染，22 个网关白名单） |
| **example key** | `DATA_TABLE` 中的整数 key，对应具体测试问题 |
| **backend** | 计算后端：`numpy`（默认）、`pytorch`、`jax` |
| **L2 error** | 函数值的 L2 范数误差 `‖u - uh‖_{L2}` |
| **H1 error** | 梯度的 L2 范数误差（H1 半范数）`‖∇u - ∇uh‖_{L2}` |
| **artifact** | 单次执行的全部产物（误差、DOF、wall time、mesh info） |
| **evidence bundle** | 聚合 environment + plan + artifact + validation 的结构化证据 |
| **policy gate** | 5 级 gate 链，每个产出 ALLOW/DEFER/REJECT |
| **study** | 在 task template 上对指定参数轴做参数扫描 |

## 设计原则

- **Pure Python, subprocess isolation** — fealpy 在子进程中执行，内存隔离
- **PDE-model-first** — 基准案例来自 fealpy 注册测试问题库
- **Backend-aware** — 计算后端是一等参数
- **Compiler-generated scripts** — 不接受外部脚本
- **Evidence-first** — exit code 是必要条件，L2/H1 容差是充分条件
- **No full-fealpy parity** — 聚焦 FEM 管道验证链路

## Division of Responsibility with `blueprint/`

- **wiki** = 扩展应该如何设计（稳定设计边界）
- **blueprint** = 正式设计立场
- **roadmap** = 阶段排序和剩余差距（当前：全部完成）
- **implementation plan** = 可执行切片（存在 `.claude/plans/` 中）
- 本扩展目前无 `.trash/` 目录

## 推荐阅读顺序

1. **边界优先**：01-overview → 07-scope → blueprint → roadmap
2. **运行时语义**：02-workflow → 03-contracts → 04-validation-evidence
3. **家族/注册**：05-family-design → 06-packaging
4. **执行路径**：roadmap (Phase 0–7 全部完成)

## 本 Wiki 不包含的内容

- fealpy 库本身的用户手册
- fealpy 的完整构建/安装指南
- MHE core 架构文档（参考 `meta-harness-wiki/`）
- 日常 rollout 日志
- 非扩展设计所必需的任何内容
