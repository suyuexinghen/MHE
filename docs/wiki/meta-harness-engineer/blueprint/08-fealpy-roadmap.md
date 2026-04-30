# 08. fealpy Extension Roadmap

> 状态：Phase 7 完成 — 全部开发目标已达成 | `metaharness_ext.fealpy` 正式执行路线图 | 2026-04-30

## 当前状态快照

### 代码现状
- **生产代码**：21 文件（types, contracts, slots, capabilities, gateway, environment, compiler, executor, validator, evidence, policy, study, governance, async_executor, benchmark_runner, optimizer, scheduler, quota, benchmark_cases, backend_comparison, __init__）
- **Manifests**：6 文件（gateway, environment, compiler, executor, validator, study）
- **测试**：17 文件（contracts, environment, compiler, manifest, executor, validator, evidence/policy, study, smoke, backends, governance, async_executor, optimizer, scheduler, quota, benchmark_cases, backend_comparison）— 254 tests passing（18 smoke gated）
- **代码质量**：ruff 无错误，ruff format 通过

### 已实现的组件
| 组件 | 文件 | 状态 |
|---|---|---|
| FealpyGatewayComponent | gateway.py | ✅ 完成 |
| FealpyEnvironmentProbeComponent | environment.py | ✅ 完成 |
| FealpyCompilerComponent | compiler.py | ✅ 完成 (7 模板: scalar, curl-curl, elasticity, darcy, stokes, allen-cahn, navier-stokes) |
| FealpyExecutorComponent | executor.py | ✅ 完成 (含 quota enforcement) |
| FealpyValidatorComponent | validator.py | ✅ 完成 (protected) |
| build_evidence_bundle() | evidence.py | ✅ 完成 |
| FealpyEvidencePolicy | policy.py | ✅ 完成 |
| FealpyStudyComponent | study.py | ✅ 完成 |
| FealpyGovernanceAdapter | governance.py | ✅ 完成 |
| FealpyAsyncExecutor | async_executor.py | ✅ 完成 |
| FealpyBenchmarkRunner | benchmark_runner.py | ✅ 完成 (三层 lane) |
| FealpyDomainBrainProvider | optimizer.py | ✅ 完成 |
| FealpySlurmBackend | scheduler.py | ✅ 完成 |
| FealpyK8sBackend | scheduler.py | ✅ 完成 |
| FealpySchedulerAdapter | scheduler.py | ✅ 完成 (SLURM + K8s dispatch + quota gate) |
| FealpyResourceQuotaProvider | quota.py | ✅ 完成 (DOF/memory 估算) |
| FealpyBackendComparisonRunner | backend_comparison.py | ✅ 完成 (numpy/pytorch/jax) |
| fealpy_case_catalog() | benchmark_cases.py | ✅ 完成 (8 cases) |

### 测试现状
| 测试文件 | 测试数 | 状态 |
|---|---|---|
| test_metaharness_fealpy_contracts.py | 9 | ✅ passing |
| test_metaharness_fealpy_environment.py | 5 | ✅ passing |
| test_metaharness_fealpy_compiler.py | 24 | ✅ passing |
| test_metaharness_fealpy_manifest.py | 7 | ✅ passing |
| test_metaharness_fealpy_executor.py | 10 | ✅ passing |
| test_metaharness_fealpy_validator.py | 10 | ✅ passing |
| test_metaharness_fealpy_evidence_policy.py | 12 | ✅ passing |
| test_metaharness_fealpy_study.py | 16 | ✅ passing |
| test_metaharness_fealpy_smoke.py | 6 | ✅ gated (MHE_RUN_REAL_FEALPY=1) |
| test_metaharness_fealpy_backends.py | 12 | ✅ gated (MHE_RUN_REAL_FEALPY=1) |
| test_metaharness_fealpy_governance.py | 18 | ✅ passing |
| test_metaharness_fealpy_async_executor.py | 9 | ✅ passing |
| test_metaharness_fealpy_optimizer.py | 22 | ✅ passing |
| test_metaharness_fealpy_scheduler.py | 28 | ✅ passing |
| test_metaharness_fealpy_quota.py | 15 | ✅ passing |
| test_metaharness_fealpy_benchmark_cases.py | 17 | ✅ passing |
| test_metaharness_fealpy_backend_comparison.py | 16 | ✅ passing |
| **总计** | **254+18** | **全部通过** |

### 文档现状
| 文档 | 状态 |
|---|---|
| 08-fealpy-extension-blueprint.md | ✅ 已完成 |
| 08-fealpy-roadmap.md | ✅ 已完成（本文档） |
| fealpy-engine-wiki/ (7-page full wiki) | ✅ 已完成 |

### 主要剩余差距
无 — 所有 roadmap 目标已完成。后续可选增强：fealpy ML 模块（PINN/PENN）、FVM/VEM 计算模式、自适应网格细化执行层实现。

---

## 推荐执行顺序

```text
Phase 0 (✅) → Phase 1 (✅) → Phase 2 (✅) → Phase 3 (✅) → Phase 4 (✅) → Phase 5 (✅) → Phase 6 (✅) → Phase 7 (✅)
```

全部 7 个 Phase 已完成（254 tests + 18 smoke gated, ruff clean）。无强制性剩余工作。

---

## 已完成

### Phase 0：Minimal Skeleton ✅

**目标**：建立扩展骨架——contracts、pipeline 组件、manifest 注册、最小测试。

**交付物**：
- [x] 10 个 Python 文件（所有核心组件 + contract/slot/capability 基础设施）
- [x] 5 个 manifest JSON（gateway, environment, compiler, executor, validator）
- [x] 4 个测试文件，28 tests passing
- [x] ruff 无错误
- [x] `from metaharness_ext.fealpy import *` 成功

**证据**：`python -m pytest tests/test_metaharness_fealpy_*.py -q` → 28 passed

**关键设计决策**：
- fealpy 在子进程中执行（`subprocess.run`），不是 in-process import
- compiler 生成自包含的 `solve.py`，包含内联的 `_build_mesh()` 函数
- 首版只支持 scalar diffusion + source 的 LFEM Poisson 模式

### Phase 1：Evidence / Policy / Study ✅

**目标**：完成 governance pipeline——evidence bundle 组装、policy gate 评估、参数扫描。

**交付物**：
- [x] `evidence.py` — `build_evidence_bundle()` 自由函数
- [x] `policy.py` — `FealpyEvidencePolicy` with 5-gate chain
- [x] `study.py` — `FealpyStudyComponent` with grid search
- [x] 7 个新 Pydantic 模型（FealpyEvidenceBundle, FealpyEvidenceWarning, FealpyPolicyReport, FealpyStudySpec, FealpyStudyAxis, FealpyStudyTrial, FealpyStudyReport）
- [x] `CAP_FEALPY_STUDY_RUN` 加入 capabilities
- [x] `FEALPY_STUDY_SLOT` 加入 slots
- [x] `fealpy_study.json` manifest
- [x] `__init__.py` 更新（约 45 个公共导出）

**已完成**：evidence/policy/study 的 mocked 测试（Phase 2 已补齐）

---

## 剩余切片

### Phase 2：测试补全 + 集成验证 ✅

**目标**：将所有组件纳入测试覆盖，验证 real-fealpy 全链路。

**关键任务**：
- [x] 编写 `test_metaharness_fealpy_executor.py`（mocked subprocess：成功执行/超时/非零退出/JSON 解析失败）
- [x] 编写 `test_metaharness_fealpy_validator.py`（各状态路径：unavailable/timeout/failed/output_missing/numeric_failed/executed）
- [x] 编写 `test_metaharness_fealpy_evidence_policy.py`（bundle 组装、5 gate 场景、ALLOW/DEFER/REJECT 决策）
- [x] 编写 `test_metaharness_fealpy_study.py`（mocked 编译器/执行器/验证器，参数快照生成、trial 排序、最优推荐）
- [x] 真实 fealpy 集成 smoke test：
  - Poisson exp0001, P1, numpy backend
  - 全链路：`gateway.run_baseline(spec)` → L2/H1 errors < tolerance
  - gated by `MHE_RUN_REAL_FEALPY=1`

**验收标准**：
- `python -m pytest tests/test_metaharness_fealpy_*.py -q` — 全部通过（76 tests, 6 smoke gated）
- 真实 smoke test 在有 fealpy 的环境中通过（`MHE_RUN_REAL_FEALPY=1`）
- ruff 无错误，ruff format 通过

**实际文件**：5 个新测试文件（executor, validator, evidence_policy, study, smoke）

### Phase 3：文档 + Wiki ✅

**目标**：完成 blueprint、roadmap、wiki index，建立设计文档基线。

**关键任务**：
- [x] 编写 `08-fealpy-extension-blueprint.md`
- [x] 编写 `08-fealpy-roadmap.md`（本文档）
- [x] 创建 `fealpy-engine-wiki/README.md`（wiki 索引）
- [ ] 后续可选：创建 7-page wiki 集合（01-overview, 02-workflow, 03-contracts, 04-env-validation-evidence, 05-family-design, 06-packaging, 07-scope-boundaries）

**验收标准**：
- blueprint 覆盖所有 13 个章节
- roadmap 反映当前代码/测试/文档真实状态
- wiki README 正确路由到 blueprint、roadmap 和未来设计页面
- 文档不声称未实现的功能已完成

**预估文件**：2 个新文件（roadmap, wiki README），后续可选 7 个 wiki 页面

### Phase 4：扩展与优化 ✅

**目标**：增强 PDE 覆盖、多后端验证、收敛性分析。

**关键任务**：
- [x] 泛化 compiler 模板，支持多 PDE family（_SCALAR_DIFFUSION_FAMILIES frozenset + BC dispatch）
- [x] FE 空间类型 dispatch（`spec.fe_space_type` → Lagrange/Nedelec/RT/Hu-Zhang）
- [x] Solver method 接入（`spec.solver.method` → spsolve）
- [x] 收敛性分析辅助函数（`_compute_drop_ratios`, `_compute_observed_order`）
- [x] `FealpyStudySpec` 扩展字段（`convergence_rule`, `target_tolerance`）
- [x] 多 PDE family 集成 smoke test（9 Tier-1 PDE families）
- [x] 多 backend smoke test（pytorch, jax — 条件跳过）
- [x] Study 收敛性 parameter sweep smoke test

**实际结果**：
- 84 非 smoke tests 通过，18 smoke tests gated
- 9 Tier-1 PDE families 已覆盖（poisson, diffusion_convection_reaction, diffusion_reaction, hyperbolic, wave, interface_poisson, polyharmonic, helmholtz, quasilinear_elliptic）
- BC dispatch: dirichlet / robin / neumann
- ruff 无错误，ruff format 通过

**已延后到 Phase 5**：
- [ ] `FealpyDomainBrainProvider`（LLM-guided mesh/degree 优化）
- [ ] 高阶混合 FE 空间（Nedelec, RT, Hu-Zhang — 需要 mixed integrator）
- [ ] 多 backend benchmark 模式（per-backend 性能对比矩阵）
- [ ] `FealpyConvergenceStudyComponent` — 自动 h-refinement 收敛性研究

### Phase 5：生产化

**目标**：治理集成、HPC 支持、异步执行。

**关键任务**：
- [x] `FealpyGovernanceAdapter` — 对接 MHE core governance path（session events, provenance graph, candidate records, audit log）
- [x] `FealpyAsyncExecutor` — 异步执行生命周期（submit/poll/cancel/await_result）
- [x] `FealpyBenchmarkRunner` — 对接 MHE benchmark framework（三层 lane：extension/direct/agent）
- [x] HPC scheduler adapter — SLURM 后端 dry-run 支持（FealpySlurmBackend + FealpySchedulerAdapter）
- [x] K8s backend — dry-run kubectl apply/get/delete job + conditions mapping
- [ ] 大规模 3D 问题资源配额管理
- [x] `FealpyDomainBrainProvider` — LLM-guided mesh/degree 优化（deferred from Phase 4）

**实际结果**：
- Governance adapter: 18 tests passing — 完整治理管道（core validation report, candidate records, session events, audit log + provenance graph）
- Async executor: 8 tests passing — 遵循 `AsyncExecutorProtocol`（submit/poll/cancel/await_result + ExecutionStatus 映射）
- Benchmark runner: 三层 lane structure（extension 管道 / direct subprocess / agent LLM），guard with environment probe
- HPC scheduler: SLURM + K8s dual backend（Phase 6 补齐 K8s）

**验收标准**：governance adapter 产出 valid candidate records；benchmark runner dry-run 成功

**依赖**：Phase 4 功能基线稳定

### Phase 6：Tier 2 PDE + Mixed FE Spaces + K8s Backend ✅

**目标**：完成 K8s scheduler backend、编译器混合有限元空间模板（Nedelec, RT, Hu-Zhang, Taylor-Hood）、5 个新 PDE family 模板。

**关键任务**：
- [x] `FealpyK8sBackend` — K8s Job YAML 生成、kubectl apply/get/delete、conditions→ExecutionStatus 映射
- [x] `FealpySchedulerAdapter` 扩展 — K8s + SLURM dispatch（`_backend()` / `_backend_for_job()` prefix matching）
- [x] 编译器重构 — 提取 4 个共享模板片段（`_render_header`, `_render_mesh_builder`, `_render_pde_load`, `_render_scalar_output`）
- [x] `_FAMILY_RENDERERS` dispatch dict — 从 frozenset 升级为 `pde_family → renderer_method` 映射
- [x] `_render_curl_curl` — FirstNedelecFESpace + CurlCurlIntegrator
- [x] `_render_linear_elasticity` — HuZhangFESpace + LinearElasticityIntegrator + ElasticMaterial
- [x] `_render_darcy` — RaviartThomasFESpace(P0) + LagrangeFESpace(P0) + BlockForm saddle-point
- [x] `_render_stokes` — Taylor-Hood P2/P1 + ViscousWorkIntegrator + BlockForm + Brezzi-Pitkäranta stabilization
- [x] `darcyforchheimer` → 复用 `_render_darcy` 模板
- [x] 未知 family → fallback 到 `_render_scalar_diffusion`
- [x] 14 new K8s tests + 6 new compiler tests → 176+18 total

**验收标准**：176 non-smoke tests 通过，18 smoke gated，ruff clean。所有 5 个模板生成有效 import + integrator + BC dispatch 代码。

**依赖**：Phase 5 编译器基线

### Phase 7：3D 资源配额 + 瞬态 PDE + 多后端 Benchmark ✅

**目标**：完成 roadmap 三个剩余差距。

**关键任务**：
- [x] **Workstream A — 3D 资源配额管理**
  - Tet/hex 网格渲染（`_render_mesh_builder()` 新增 tet → TetrahedronMesh, hex → HexahedronMesh 分支）
  - `FealpyResourceQuotaProvider` — DOF 估算（Lagrange/Nedelec/RT/HuZhang/Taylor-Hood）、内存估算、exhausted 判定
  - `FEALPY_QUOTA_PROVIDER_SLOT` + `CAP_FEALPY_QUOTA_PROVIDE`
  - `FealpySchedulerAdapter.submit()` 加 quota 参数，exhausted → ValueError
  - `FealpyExecutorComponent.execute_plan()` 顶部 quota check，exhausted → failed artifact
- [x] **Workstream B — Allen-Cahn + Navier-Stokes 模板**
  - `FealpyProblemSpec` 新增 `dt`, `num_time_steps`, `time_integrator` 字段
  - `_render_allen_cahn()` — 半隐式 convex splitting（扩散隐式，双井项显式）+ Newton 迭代
  - `_render_navier_stokes()` — Taylor-Hood P2/P1 + Picard/Oseen 迭代 + 时间循环
  - `_FAMILY_RENDERERS` +2 entries
- [x] **Workstream C — 多后端 Benchmark 对比矩阵**
  - `benchmark_cases.py` — 8 个 fealpy benchmark cases（poisson × 3 backends + 3D + stokes + darcy + elasticity + curlcurl）
  - `backend_comparison.py` — `FealpyBackendComparisonRunner`（跨 numpy/pytorch/jax 运行 + comparison_matrix）
  - MHE core 集成：`models.py` 加 `"fealpy-pde"`, `io.py` 加 SUITE_DIRS entry, `cli.py` 加 `--suite fealpy-pde` 分支, `compare.py` 加 fealpy analysis section

**验收标准**：254 non-smoke tests 通过，18 smoke gated，ruff clean。全部 7 个编译器模板可用。

**依赖**：Phase 6 编译器基线 + MHE benchmark framework

---

## 风险 / 依赖

| 风险 | 影响 | 缓解 |
|---|---|---|
| fealpy API breaking change | 高 | 钉住 v3.4.0，environment probe 报告版本 |
| 多 PDE family 模板复杂度 | 中 | Phase 4 做 per-family 分支，Phase 0-3 只支持 Poisson |
| 真实 fealpy 环境不可用 | 中 | 默认测试全 mock；smoke test gated |
| 多 backend 数值差异 | 中 | per-backend 容差配置；environment evidence 记录 |
| 大规模网格性能 | 低 | timeout + 子进程内存隔离；Phase 7 做资源配额 |

---

## Phase Map 总览

| Phase | 名称 | 状态 | 测试 | 文件数 |
|---|---|---|---|---|
| 0 | Minimal Skeleton | ✅ | 28 tests | 15 文件 |
| 1 | Evidence / Policy / Study | ✅ | 6 新文件 | 6 文件 |
| 2 | 测试补全 + 集成验证 | ✅ | 76 tests（含 6 smoke） | 5 新测试 |
| 3 | 文档 + Wiki | ✅ | — | 3 文档 |
| 4 | 扩展与优化 | ✅ | 84+18 tests（18 smoke） | 1 新测试 + 3 生产代码 |
| 5 | 生产化 | ✅ | 156+18 tests | 5 新生产 + 4 新测试 |
| 6 | Tier 2 PDE + Mixed FE + K8s | ✅ | 176+18 tests | 2 修改 + 2 测试扩展 |
| 7 | 3D Quota + Transient PDE + Benchmark | ✅ | 254+18 tests | 5 新文件 + ~10 修改 |
