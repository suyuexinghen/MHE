# 08. fealpy Extension Blueprint

> 状态：proposal | `MHE/src/metaharness_ext/fealpy` 正式设计蓝图 | 参考 Octave/Nektar extension blueprint 与 fealpy v3.4.0 API

## 8.1 目标

`metaharness_ext.fealpy` 的目标，是把 fealpy（Python 有限元计算库）作为一种 **受控、可声明、可验证、可审计** 的 FEM/PDE 求解 worker 接入 MHE，而不是把 fealpy 包装成任意 Python 脚本运行器。

fealpy extension 的核心价值：

1. 复用 fealpy 的 PDE 模型数据库（24 种 PDE 类型、100+ 注册测试问题，全部带精确解），降低 FEM benchmark 构造门槛；
2. 将 PDE 类型选择、网格参数、有限元空间阶次、求解器方法、后端选择显式建模为 typed contracts；
3. 用 MHE 的 component graph、session、provenance、policy、evidence 与 promotion 语义治理 FEM 计算任务；
4. 为后续 L2/H1 收敛性研究、自适应网格优化、多后端 benchmark 比较保留稳定扩展面；
5. 用自动化 FEM 管道替代"手动编写 fealpy 脚本、人工检查 L2/H1 误差"的非结构化流程。

fealpy 的稳定运行模型：

```text
typed spec (PDE family + example key + mesh params + FE degree + solver + backend)
  → generated Python solver script + workspace
  → python solve.py (subprocess)
  → JSON stdout (l2_error, h1_error, dof, wall_time)
  → numeric validation + evidence bundle + policy handoff
```

fealpy 与其他 MHE extension 的核心差异：**纯 Python 库，无独立 CLI 二进制**。Executor 通过 `subprocess.run([sys.executable, script])` 在子进程中运行 fealpy，而非调用外部 solver 可执行文件。

---

## 8.2 平台与领域边界

### MHE 平台层负责

- manifest discovery / component boot；
- graph candidate staging / semantic validation；
- graph version commit / rollback；
- session event、audit log、artifact snapshot、provenance graph；
- protected-component enforcement；
- policy-gated promotion authority；
- runtime recovery、execution lifecycle service、resource quota；
- BrainProvider / optimizer / mutation proposal 的平台级入口。

### fealpy 扩展层负责

- fealpy PDE problem / mesh / solver / backend 的 typed spec；
- fealpy 环境探针：版本检测、backend 可用性、PDE 类型注册；
- Python solver script 编译（参数化 FEM 管道代码生成）；
- `python solve.py` 子进程执行、timeout、stdout/stderr capture；
- JSON 输出解析（L2/H1 误差、DOF、wall time）；
- 基于 L2/H1/H1-seminorm 容差的数值验证；
- evidence bundle 组装与 policy gate 评估；
- 参数扫描（grid search）收敛性研究。

**核心原则：MHE = platform promotion / session / policy / provenance authority；fealpy extension = fealpy FEM workflow、numeric evidence 与 validation contributor。**

---

## 8.3 设计立场

fealpy extension 首版设计立场：

- **pure-Python integration**：fealpy 是 Python 库，通过子进程隔离执行，不引入编译依赖；
- **PDE-model-first**：fealpy 的 `PDEModelManager` 提供带精确解的注册测试问题，直接作为 benchmark case 来源；
- **backend-aware**：fealpy 支持 numpy/pytorch/jax 多后端，extension 将 backend 作为一等公民参数；
- **script-generation**：compiler 生成自包含的 `solve.py`，包含完整的 FEM 管道（mesh → space → assembly → BCs → solve → error），不依赖外部模板文件；
- **evidence-first**：exit code 只是必要条件，L2/H1 误差对容差才是成功的充分条件；
- **family-driven**：支持的 PDE 类型明确列出在 types.py 中，不假设所有 fealpy model 都可用；
- **no full-fealpy parity claim**：不承诺覆盖所有 fealpy 功能（FVM、VEM、CDG、ML-PINN 等），首版聚焦 LFEM Poisson 验证链路。

---

## 8.4 当前支持边界

### 已实现的 PDE 类型（types.py 声明）

24 种 PDE family：`poisson`, `stokes`, `navier_stokes`, `parabolic`, `hyperbolic`, `helmholtz`, `curlcurl`, `diffusion`, `diffusion_convection`, `diffusion_convection_reaction`, `diffusion_reaction`, `darcyforchheimer`, `linear_elasticity`, `interface_poisson`, `surface_poisson`, `wave`, `allen_cahn`, `nonlinear`, `polyharmonic`, `quasilinear_elliptic`, `optimal_control`, `ion_flow`, `dld_microfluidic_chip`, `mgtensor_possion`

### 已验证的 PDE 类型

- `poisson` — exp0001 (1D sin(πx)) 通过编译器和验证器测试；exp0002 可用于差异化 plan_id 测试

### Backend 支持

| Backend | 环境探针检测 | 编译器支持 | 状态 |
|---|---|---|---|
| numpy | `import numpy` | `bm.set_backend('numpy')` | 默认，已验证 |
| pytorch | `import torch` | `bm.set_backend('pytorch')` | 声明，未测试 |
| jax | `import jax` | `bm.set_backend('jax')` | 声明，未测试 |

### 首版明确不支持

- FVM、VEM、CDG、CEM、CFD 等非 FEM 计算模式；
- 自适应网格细化（`adaptive_refinement` 字段已声明但 executor 未实现）；
- 高阶 FE 空间（Nedelec、Raviart-Thomas、Hu-Zhang 等）；
- fealpy ML 模块（PINN、PENN、RFM）；
- 多 backend 性能对比 benchmark；
- 在 extension 内部重建 MHE session / audit / graph promotion 系统。

---

## 8.5 组件链

```text
FealpyGateway
  → FealpyEnvironmentProbe
    → FealpyCompiler
      → FealpyExecutor
        → FealpyValidator
          → build_evidence_bundle()
            → FealpyEvidencePolicy
              → FealpyStudyComponent (optional, 参数扫描)
```

### Gateway (`fealpy_gateway.primary`)

- 接收 `FealpyProblemSpec`，验证 PDE family 合法性；
- 提供 `issue_task()`, `compile_experiment()`, `run_baseline()` 便捷入口；
- `run_baseline()` 串联完整 pipeline：probe → compile → execute；
- `declare_interface()` 声明 slot、output contract 与 `fealpy.task.issue` capability。

### Environment Probe (`fealpy_environment.primary`)

- 检查 fealpy 包是否可导入，获取 `__version__`；
- 探测 backend 可用性：numpy（必需）、pytorch（可选）、jax（可选）；
- 返回已注册的 PDE 类型列表（24 种）；
- 产出 `FealpyEnvironmentReport`：`available`, `fealpy_version`, `available_backends`, `available_pde_families`, `blocks_promotion`。

### Compiler (`fealpy_compiler.primary`)

- 将 `FealpyProblemSpec` 编译为 `FealpyRunPlan`（含自包含 `solve.py` 脚本）；
- 生成确定性 `plan_id`（SHA256 of spec JSON）；
- 生成的脚本包含：backend 初始化、PDE 模型加载、网格构建、Lagrange FE 空间创建、Bilinear/Linear form 装配、Dirichlet BC 施加、直接求解、L2/H1 误差计算、JSON 结果输出；
- 网格构建函数 `_build_mesh()` 内联在脚本中，支持 interval/tri/quad/uniform 四种网格类型。

### Executor (`fealpy_executor.primary`)

- 在 `.runs/fealpy/<task_id>/<run_id>/` 下准备 workspace；
- 写入 `solve.py`；
- 通过 `subprocess.run([sys.executable, script_path])` 在子进程中执行；
- 控制 timeout、cwd、PYTHONPATH；
- 捕获 stdout 并解析最后一行 JSON；
- 产出 `FealpyRunArtifact`：`l2_error`, `h1_error`, `dof_count`, `wall_time_seconds`, `mesh_info`；
- 区分 `completed`、`failed`、`timeout`、`unavailable` 四种状态。

### Validator (`fealpy_validator.primary`) — protected

- 区分 `environment_invalid` / `compile_failed` / `runtime_failed` / `output_missing` / `numeric_validation_failed` / `executed`；
- 检查 artifact status；对 `unavailable`/`timeout`/`failed` 生成对应的 `ValidationIssue`；
- 对 L2 和 H1 误差应用容差：默认 `l2_tolerance=1e-6`, `h1_tolerance=1e-4`；
- 生成 `FealpyValidationReport`，包含 `l2_passed`、`h1_passed`、`blocks_promotion`、`issues`。

### Evidence (`build_evidence_bundle()` 自由函数)

- 从 run artifact、validation report、environment report、plan 组装 `FealpyEvidenceBundle`；
- 收集 evidence refs，生成 warning（缺失 validation、环境问题）；
- 包含 provenance metadata（task_id、plan_ref、artifact_ref、validation_ref）。

### Policy (`FealpyEvidencePolicy`)

- 5 级 gate 链：`fealpy_environment_readiness` → `fealpy_validation_presence` → `fealpy_validation_status` → `fealpy_evidence_files` → `fealpy_evidence_ready`；
- 每个 gate 产出 `GateResult`（ALLOW/DEFER/REJECT）；
- 最终决策：ALLOW（全部通过）、DEFER（存疑）、REJECT（阻断）。

### Study (`fealpy_study.primary`)

- 接收 `FealpyStudySpec`（task_template + axes），生成参数组合的笛卡尔积；
- 对每个参数快照：mutate task → compile → execute → validate → evidence → policy；
- 提取目标指标（默认最小化 L2 误差），推荐最优 trial；
- 产出 `FealpyStudyReport`（trials、best_trial_id、recommended_parameters、convergence_analysis）。

---

## 8.6 Contracts 设计

### 核心类型

| 类型 | 角色 | 阶段 |
|---|---|---|
| `FealpyProblemSpec` | 用户任务入口（PDE type + mesh + FE degree + solver + backend） | Spec |
| `FealpyMeshSpec` | 网格参数（meshtype, nx, ny, nz, h） | Spec |
| `FealpySolverSpec` | 求解器参数（method, max_iterations, atol, rtol） | Spec |
| `FealpyRunPlan` | 编译后的 solve.py 脚本 + workspace + execution metadata | Plan |
| `FealpyEnvironmentReport` | fealpy version / backend status / PDE families | Report |
| `FealpyRunArtifact` | L2/H1 error / DOF / wall time / mesh info / status | Artifact |
| `FealpyValidationReport` | L2/H1 tolerance checks / issues / blocks_promotion | Report |
| `FealpyEvidenceBundle` | environment + plan + artifact + validation + evidence refs | Bundle |
| `FealpyEvidenceWarning` | code / message / severity / evidence | Warning |
| `FealpyPolicyReport` | decision (allow/defer/reject) / gate results / warnings | Report |
| `FealpyStudySpec` | parameter sweep 定义（axes, objective, goal） | Study |
| `FealpyStudyAxis` | 扫描轴（parameter_path, values or range+step） | Study |
| `FealpyStudyTrial` | 单次 trial（parameters, artifact_ref, metric_value, passed） | Study |
| `FealpyStudyReport` | study 结果（trials, best, convergence_analysis） | Study |

### `FealpyProblemSpec` 字段

- `task_id: str` — 唯一任务标识
- `pde_family: FealpyPdeFamily` — PDE 类型（默认 "poisson"）
- `example_key: int` — fealpy PDEModelManager 中的 example key（默认 1）
- `backend: FealpyBackend` — 计算后端（默认 "numpy"）
- `mesh: FealpyMeshSpec` — 网格参数
- `fe_degree: int` — Lagrange FE 阶次（默认 1）
- `solver: FealpySolverSpec` — 求解器配置
- `adaptive_refinement: int` — 自适应细化步数（默认 0，首版未实现）
- `timeout_seconds: int` — 执行超时（默认 300）

### `FealpyRunArtifact` 字段

- `artifact_id`, `run_id`, `task_id`, `plan_ref`
- `status: FealpyRunArtifactStatus` — completed/failed/timeout/unavailable
- `l2_error: float | None`, `h1_error: float | None`
- `dof_count: int | None` — 全局自由度
- `wall_time_seconds: float | None`
- `mesh_info: dict` — nc (number of cells), nn (number of nodes)

---

## 8.7 包结构

```text
MHE/src/metaharness_ext/fealpy/
├── __init__.py          # 公共 API 重导出
├── types.py             # 枚举和类型别名
├── contracts.py         # Pydantic 数据模型
├── slots.py             # slot 字符串常量
├── capabilities.py      # capability 字符串常量
├── gateway.py           # FealpyGatewayComponent
├── environment.py       # FealpyEnvironmentProbeComponent
├── compiler.py          # FealpyCompilerComponent
├── executor.py          # FealpyExecutorComponent
├── validator.py         # FealpyValidatorComponent (protected)
├── evidence.py          # build_evidence_bundle()
├── policy.py            # FealpyEvidencePolicy
└── study.py             # FealpyStudyComponent

MHE/examples/manifests/fealpy/
├── fealpy_gateway.json
├── fealpy_environment.json
├── fealpy_compiler.json
├── fealpy_executor.json
├── fealpy_validator.json
└── fealpy_study.json

MHE/tests/
├── test_metaharness_fealpy_contracts.py
├── test_metaharness_fealpy_environment.py
├── test_metaharness_fealpy_compiler.py
└── test_metaharness_fealpy_manifest.py
```

---

## 8.8 外部依赖策略

### 运行时前提

| 依赖 | 用途 | 检测位置 |
|---|---|---|
| fealpy | FEM 计算核心 | Environment probe (`import fealpy`) |
| numpy | 默认计算后端 | Environment probe (`import numpy`) |
| pytorch (可选) | 替代计算后端 | Environment probe (`import torch`) |
| jax (可选) | 替代计算后端 | Environment probe (`import jax`) |

### 首版策略

- numpy 缺失 → environment unavailable + blocks_promotion；
- pytorch/jax 缺失 → 仅 warning，不影响 availability；
- 不在 extension 内自动安装 fealpy 或其依赖；
- 编译后的 `solve.py` 是自包含的，不依赖运行时模板文件。

---

## 8.9 安全与治理

fealpy extension 的安全模型：

- **子进程隔离**：fealpy 在独立 Python 子进程中执行，与 MHE runtime 进程内存隔离；
- **workspace-bound**：所有脚本和输出写入 `.runs/fealpy/<task_id>/<run_id>/`；
- **timeout 强制**：每个 spec 指定 timeout_seconds，超时即终止子进程；
- **编译器控制**：executor 只执行 compiler 生成的脚本，不接受外部脚本路径；
- `FealpyValidatorComponent` 设为 `protected`，不能被随意替换；
- JSON stdout 解析失败 → artifact status = failed + 可读 error message；
- manifest 显式声明 sandbox tier、credentials 和 workspace-write policy。

与 MHE core 的集成点：

- 使用 `ComponentRuntime.storage_path` 定位 `.runs`；
- evidence refs 以 `fealpy://` 前缀命名；
- validation issues 遵循 `ValidationIssue` 模型（code, message, subject, blocks_promotion）；
- 后续可接入 `RuntimeServices.artifact_store`、`audit_log`、`provenance_graph`。

---

## 8.10 测试策略

### 当前测试覆盖（28 tests, 0 failures）

- **contracts** (9 tests)：spec 创建/默认值/非法 task_id/非法 degree/非法 timeout/非法 nx/非法 maxiter/validation report 的 blocks_promotion 计算
- **environment** (5 tests)：fealpy 可用/不可用/backend 缺失/PDE families 列表/python version
- **compiler** (5 tests)：确定性的 plan_id/不同 spec 不同 plan_id/脚本包含预期代码行/plan 字段完整性/编译拒绝不可用环境
- **manifest** (9 tests)：5 个 manifest 文件存在性/name 匹配/slot 匹配/capability 匹配/sandbox tier 匹配/protected flag/entry 可导入/declare_interface 成功/registry 注册

### 待添加测试

- `test_metaharness_fealpy_executor.py` — executor 的 mocked subprocess 测试
- `test_metaharness_fealpy_validator.py` — validator 各状态路径测试
- `test_metaharness_fealpy_evidence_policy.py` — evidence bundle 和 policy gate 测试
- `test_metaharness_fealpy_study.py` — study 参数扫描测试
- 真实 fealpy 集成 smoke test（gated by `MHE_RUN_REAL_FEALPY=1`）

### 推荐命令

```bash
python -m pytest tests/test_metaharness_fealpy_*.py -q
ruff check src/metaharness_ext/fealpy tests/test_metaharness_fealpy_*.py
ruff format --check src/metaharness_ext/fealpy tests/test_metaharness_fealpy_*.py
```

---

## 8.11 阶段路线图概览

### Phase 0：Minimal Skeleton ✅ 已完成

- 创建 10 个生产代码文件（types, contracts, slots, capabilities, gateway, environment, compiler, executor, validator, __init__）
- 创建 5 个 manifest JSON（gateway, environment, compiler, executor, validator）
- 创建 4 个测试文件（contracts, environment, compiler, manifest）
- 28 tests passing, ruff 无错误

### Phase 1：Evidence / Policy / Study — 代码已完成，测试待补

- 新增 `evidence.py`（`build_evidence_bundle()` 自由函数）
- 新增 `policy.py`（`FealpyEvidencePolicy` with 5-gate chain）
- 新增 `study.py`（`FealpyStudyComponent` with grid search）
- 扩展 contracts（7 个新 Pydantic 模型）
- 更新 `__init__.py`、`capabilities.py`、`slots.py`
- 新增 `fealpy_study.json` manifest

### Phase 2：测试补全 + 集成验证

- 补全 executor/validator/evidence/policy/study 的 mocked 测试
- 真实 fealpy 集成 smoke test（Poisson exp0001 全链路：gateway → env → compile → execute → validate → evidence → policy）
- ruff + pytest 全部通过

### Phase 3：文档 + Wiki

- 完成 08-fealpy-extension-blueprint.md（本文档）
- 完成 08-fealpy-roadmap.md
- 创建 fealpy-engine-wiki README.md
- 后续可选：完整 7-page wiki 集合（overview, workflow, contracts, env-validation-evidence, family-design, packaging, scope-boundaries）

### Phase 4：扩展与优化（v2）

- **Study 增强**：多目标优化、Bayesian 搜索策略
- **收敛性研究**：自动 h-refinement、p-refinement 扫描
- **多 backend benchmark**：numpy vs pytorch vs jax 性能对比
- **高阶 FE 空间**：Nedelec、Raviart-Thomas、Hu-Zhang 支持
- **BrainProvider**：`FealpyDomainBrainProvider` 实现 LLM-guided mesh/degree 优化
- **Benchmark 集成**：对接到 MHE benchmark framework（三层 lane：extension pipeline / direct Claude CLI / MHE Claude CLI agent）

### Phase 5：生产化

- `FealpyGovernanceAdapter` — 对接 MHE core governance path
- HPC scheduler adapter — SLURM/K8s 后端支持
- `FealpyAsyncExecutor` — 异步执行生命周期
- 大规模 3D 问题的资源配额管理

---

## 8.12 风险与开放问题

| 风险 | 影响 | 缓解 |
|---|---|---|
| fealpy API 不稳定 | 高 | 钉住已知版本（v3.4.0），environment probe 报告版本号 |
| 子进程执行开销 | 低 | fealpy 是纯 Python，启动开销小；后续可考虑 in-process 模式 |
| PDE 模型兼容性 | 中 | 首期只验证 poisson exp0001；其他 PDE 类型声明但未系统测试 |
| 多 backend 行为差异 | 中 | environment probe 检测可用性；数值容差按 backend 调整 |
| 大网格内存溢出 | 中 | timeout 控制 + subprocess 内存隔离 |
| fealpy 安装依赖复杂 | 中 | 只要求 numpy 为最小后端；pytorch/jax 为可选 |

开放问题：

- 是否应该支持 `script` 模式（用户提供任意 Python 脚本），还是坚持 compiler 生成模式？
- 高阶 FE 空间（Nedelec, RT, Hu-Zhang）的 contracts 如何设计？
- 自适应网格细化是否应该在 compiler 层（生成包含 refine 循环的脚本）还是 study 层（多次 run 不同 mesh）？
- 多 PDE 类型（非 Poisson）的 `solve.py` 模板如何泛化？Compiler 是否需要 per-family 分支？

---

## 8.13 首版完成判据

fealpy extension 可被称为 Phase 1 complete 的条件：

- `FealpyProblemSpec → FealpyRunPlan → FealpyRunArtifact → FealpyValidationReport` 全链路可运行；
- `build_evidence_bundle()` + `FealpyEvidencePolicy` 产出有效的 `FealpyPolicyReport`；
- `FealpyStudyComponent` 可运行网格/阶次参数扫描；
- 所有测试不依赖真实 fealpy（mocked），ruff 无错误；
- 真实 fealpy smoke test gated 且自动 skip（无 fealpy 时）；
- 所有生成文件写入 `.runs/fealpy/...`；
- validator 能区分环境不可用、编译失败、运行时失败、输出缺失和数值验证失败；
- validation report 包含 `blocks_promotion`、`ValidationIssue`、`evidence_refs`；
- blueprint、roadmap、wiki、manifests、tests 与实现边界一致；
- 文档不声称覆盖所有 fealpy 功能或全部 PDE 类型。
