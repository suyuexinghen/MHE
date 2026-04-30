# 01. fealpy Extension Overview

## 1. Extension Positioning

`metaharness_ext.fealpy` 将 [fealpy](https://github.com/weihuayi/fealpy)（Python 有限元计算库）作为受控、可声明、可验证、可审计的 FEM/PDE 求解 worker 接入 MHE。

**目标软件**：fealpy v3.4.0 — 提供 24 种 PDE 类型、100+ 带精确解的注册测试问题的 Python FEM 库。

**选择接口层**：fealpy 是纯 Python 库，无独立 CLI 二进制。Integration 通过 compiler 生成自包含 Python 脚本、executor 在子进程中运行实现。计算后端（numpy/pytorch/jax）作为一等公民参数，由 environment probe 运行时检测。

**与其他 MHE extension 的核心差异**：纯 Python 库集成，无需编译依赖；compiler 生成自包含 `solve.py` 脚本而非调用外部 solver 可执行文件。

## 2. Scope Boundaries

### 支持的

- **18 个 PDE families** 通过编译器模板渲染（`_FAMILY_RENDERERS` dispatch dict）
- **5 种 FE 空间类型**：Lagrange（P1/P2）、FirstNedelec（edge elements）、RaviartThomas（H(div) conforming）、HuZhang（elasticity）、Taylor-Hood（P2/P1 mixed）
- **3 种计算后端**：numpy（默认，必需）、pytorch（可选）、jax（可选）
- **6 种网格类型**：interval、tri、quad、tet、hex、uniform
- **6 种求解器方法**：direct、cg、gmres、minres、bicgstab、amg
- **完整 MHE pipeline**：Gateway → Environment → Compiler → Executor → Validator → Evidence → Policy
- **参数扫描收敛性研究**（grid search + Bayesian/LLM-guided optimization）
- **HPC scheduler 集成**：SLURM + Kubernetes 后端
- **Benchmark framework 集成**：三层 lane（extension/direct/agent）+ 多后端对比矩阵
- **3D 资源配额管理**：DOF/内存估算 + enforce gate

### 明确不支持

- FVM、VEM、CDG、CEM、CFD 等非 FEM 计算模式
- fealpy ML 模块（PINN、PENN、RFM）
- 自适应网格细化执行层（`adaptive_refinement` 字段已声明但 executor 未实现 refine loop）
- 在 extension 内部重建 MHE session/audit/graph promotion 系统
- 接受外部用户编写的任意 Python 脚本（只执行 compiler 生成的脚本）

## 3. Design Goals

- **Controllability**：所有计算参数（PDE 类型、网格、FE 空间、求解器、后端）必须通过 typed spec 声明，不允许隐式默认值绕过
- **Typed boundary**：Pydantic contracts 定义 spec→plan→artifact→validation→evidence 全链路的类型边界
- **Validation-first**：exit code 是必要条件，L2/H1 误差对容差才是充分条件；validator 区分 6 种失败状态
- **Evidence integrity**：bundle 聚合 environment + plan + artifact + validation 的结构化证据，5-gate policy chain 评估 promotion readiness
- **Subprocess isolation**：fealpy 在独立 Python 子进程中执行，与 MHE runtime 进程内存隔离，timeout 强制
- **No full-fealpy parity**：聚焦 FEM 管道验证链路，不声称覆盖所有 fealpy 功能

## 4. MHE Integration Seams

| Integration Point | Extension Provides | MHE Core Owns |
|---|---|---|
| Component lifecycle | `activate()` / `deactivate()` / `declare_interface()` | Component discovery, dependency resolution, boot ordering |
| Graph staging | Slot + capability declarations | `ConnectionEngine` semantic validation, graph version commit/rollback |
| Session / Audit | Evidence refs (`fealpy://` prefix), event payloads | `SessionStore`, `AuditLog`, `ProvenanceGraph` |
| Policy / Promotion | `FealpyEvidencePolicy` (5-gate chain) | Platform-level promotion authority |
| Execution lifecycle | `FealpyAsyncExecutor` (submit/poll/cancel/await_result) | `ExecutionLifecycleService` |
| Resource quota | `FealpyResourceQuotaProvider` (DOF/memory estimation) | `RuntimeServices.resolved_resource_quota()` |
| Benchmark | `FealpyBenchmarkRunner`, `FealpyBackendComparisonRunner` | `BenchmarkSuite`, `write_comparison_outputs()`, CLI dispatch |
| Storage | Writes to `ComponentRuntime.storage_path` | `.runs/` directory ownership, artifact store |

**核心原则**：MHE = platform promotion / session / policy / provenance authority；fealpy extension = fealpy FEM workflow、numeric evidence 与 validation contributor。
