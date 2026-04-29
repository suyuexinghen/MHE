# fealpy Extension for MHE Wiki

> Version: v0.1 | Last updated: 2026-04-29

本目录讨论 **如何设计 `metaharness_ext.fealpy` inside `MHE`**。

聚焦扩展层设计边界：PDE 类型家族、typed contracts、environment/validation/evidence 表面、打包与注册、与 MHE governance path 的对接缝。

**重要：本扩展正在积极开发中，尚未完全实现所有设计目标。**

## 什么是 fealpy Extension

`metaharness_ext.fealpy` 是将 [fealpy](https://github.com/weihuayi/fealpy)（Python 有限元计算库）接入 MHE 的科学计算 worker。它将 fealpy 的 FEM 管道（网格 → 函数空间 → 装配 → 求解 → 误差评估）封装为可声明、可验证、可审计的 MHE component 链。

**核心能力：**
- 通过 `PDEModelManager` 访问 24 种 PDE 类型、100+ 带精确解的测试问题
- 参数化 FEM 管道：PDE 类型、网格参数、FE 阶次、求解器、计算后端
- 自动 L2/H1 误差计算与数值容差验证
- Evidence/Policy governance 管道
- 参数扫描收敛性研究

## 本目录范围

本 wiki 讨论 **扩展应该如何设计**，而非实现如何分阶段执行。阶段执行、剩余 backlog 和当前进度跟踪应在 `blueprint/` 下的编号文档中。

本目录 **不是** 以下内容的主要归属地：
- 阶段性实现排序
- rollout / milestone 叙述
- 当前实现状态跟踪
- 混入设计页面的 blueprint / roadmap 内容

这些内容应放在 `blueprint/` 编号文档下。

---

## 导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [08-fealpy-extension-blueprint](../blueprint/08-fealpy-extension-blueprint.md) | 正式设计蓝图：目标、边界、设计立场、支持家族、组件链、contracts、安全/治理、阶段路线图 | 所有人 |
| [08-fealpy-roadmap](../blueprint/08-fealpy-roadmap.md) | 正式执行路线图：当前状态、已完成阶段、剩余切片、风险/依赖 | 开发/项目管理 |

### 计划中的设计页面（Phase 3+）

| 计划文档 | 主题 |
|---|---|
| 01-overview.md | 扩展定位、范围边界、设计目标、MHE 集成缝 |
| 02-workflow-and-components.md | 规范组件链、各组件职责、组件间数据流 |
| 03-contracts-and-artifacts.md | Typed 输入/任务 contracts、Run Plan、Run Artifact、Validation Surface |
| 04-environment-validation-and-evidence.md | 环境探针表面、失败分类、验证状态、Evidence/Governance 缝 |
| 05-family-design.md | 为什么 family 是一等设计对象、支持的 families、per-family 边界 |
| 06-packaging-and-registration.md | 包布局、导出、capabilities、slots/protected、manifest 表面、注册路径 |
| 07-scope-and-boundaries.md | Wiki 职责、Blueprint 职责、Roadmap 职责、显式不包含内容 |

---

## 术语

| 术语 | 含义 |
|---|---|
| **PDE family** | fealpy `PDEModelManager` 中注册的 PDE 类型（如 `poisson`, `stokes`, `helmholtz`） |
| **example key** | `DATA_TABLE` 中的整数 key，对应 `expXXXX.py` 文件中的具体测试问题 |
| **backend** | fealpy 计算后端：`numpy`（默认）、`pytorch`、`jax` |
| **L2 error** | 函数值的 L2 范数误差 `‖u - uh‖_{L2}` |
| **H1 error** | 梯度的 L2 范数误差（H1 半范数）`‖∇u - ∇uh‖_{L2}` |
| **artifact** | 单次执行的全部产物（L2/H1 误差、DOF、wall time、mesh info） |
| **evidence bundle** | 聚合 environment + run plan + artifact + validation 的结构化证据 |
| **policy gate** | 5 级 gate 链（environment → validation_presence → validation_status → evidence_files → evidence_ready），每个产出 ALLOW/DEFER/REJECT |
| **study** | 在 task template 上对指定参数轴做 grid search 的参数扫描 |

**代码文字拼写注意：**
- `FealpyProblemSpec`（非 FealpyExperimentSpec——区别于 Octave 的命名）
- `fealpy_*` 前缀（全小写，下划线分隔）
- `FEALPY_*_SLOT` 常量（全大写）

---

## 设计原则

- **Pure Python, subprocess isolation**：fealpy 是库，通过子进程隔离执行
- **PDE-model-first**：基准案例来自 fealpy 注册的测试问题库
- **Backend-aware**：计算后端是一等参数，环境探针检测可用性
- **Compiler-generated scripts**：所有执行脚本由 compiler 生成，不接受外部脚本
- **Evidence-first**：exit code 是必要条件，L2/H1 容差是充分条件
- **No full-fealpy parity**：不声称覆盖所有 fealpy 功能

---

## Division of Responsibility with `blueprint/`

- **wiki** = 扩展应该如何设计（稳定设计边界）
- **blueprint** = 正式设计立场（本文档集）
- **roadmap** = 阶段排序和剩余差距
- **implementation plan** = 一个可执行切片
- 本扩展目前无 `.trash/` 目录

---

## 推荐阅读顺序

1. **边界优先路径**：blueprint → roadmap → 本 README（了解设计立场和当前状态）
2. **运行时语义路径**：blueprint §8.5-8.6（组件链 + contracts 设计）
3. **家族/注册路径**：blueprint §8.4（支持边界）、§8.7（包结构）
4. **正式执行路径**：roadmap → Phase 2（下一个待执行切片）

---

## 本 Wiki 不包含的内容

- fealpy 库本身的用户手册（参考 `/home/linden/code/work/Solvers/python/fealpy/docs/`）
- fealpy 的完整构建/安装指南
- MHE core 架构文档（参考 `docs/wiki/meta-harness-engineer/meta-harness-wiki/`）
- 日常 rollout 日志
- 非扩展设计所必需的任何内容
