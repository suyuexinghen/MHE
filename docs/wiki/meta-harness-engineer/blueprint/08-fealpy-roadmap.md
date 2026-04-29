# 08. fealpy Extension Roadmap

> 状态：Phase 4 完成 | `metaharness_ext.fealpy` 正式执行路线图 | 2026-04-29

## 当前状态快照

### 代码现状
- **生产代码**：13 文件（types, contracts, slots, capabilities, gateway, environment, compiler, executor, validator, evidence, policy, study, __init__）
- **Manifests**：6 文件（gateway, environment, compiler, executor, validator, study）
- **测试**：10 文件（contracts, environment, compiler, manifest, executor, validator, evidence/policy, study, smoke, backends）— 84 tests passing（18 smoke gated）
- **代码质量**：ruff 无错误，ruff format 通过

### 已实现的组件
| 组件 | 文件 | 状态 |
|---|---|---|
| FealpyGatewayComponent | gateway.py | ✅ 完成 |
| FealpyEnvironmentProbeComponent | environment.py | ✅ 完成 |
| FealpyCompilerComponent | compiler.py | ✅ 完成 |
| FealpyExecutorComponent | executor.py | ✅ 完成 |
| FealpyValidatorComponent | validator.py | ✅ 完成 (protected) |
| build_evidence_bundle() | evidence.py | ✅ 完成 |
| FealpyEvidencePolicy | policy.py | ✅ 完成 |
| FealpyStudyComponent | study.py | ✅ 完成 |

### 测试现状
| 测试文件 | 测试数 | 状态 |
|---|---|---|
| test_metaharness_fealpy_contracts.py | 9 | ✅ passing |
| test_metaharness_fealpy_environment.py | 5 | ✅ passing |
| test_metaharness_fealpy_compiler.py | 10 | ✅ passing |
| test_metaharness_fealpy_manifest.py | 9 | ✅ passing |
| test_metaharness_fealpy_executor.py | 8 | ✅ passing |
| test_metaharness_fealpy_validator.py | 10 | ✅ passing |
| test_metaharness_fealpy_evidence_policy.py | 10 | ✅ passing |
| test_metaharness_fealpy_study.py | 20 | ✅ passing |
| test_metaharness_fealpy_smoke.py | 6 | ✅ gated (MHE_RUN_REAL_FEALPY=1) |
| test_metaharness_fealpy_backends.py | 12 | ✅ gated (MHE_RUN_REAL_FEALPY=1) |
| **总计** | **84+18** | **全部通过** |

### 文档现状
| 文档 | 状态 |
|---|---|
| 08-fealpy-extension-blueprint.md | ✅ 已完成 |
| 08-fealpy-roadmap.md | ✅ 已完成 |
| fealpy-engine-wiki/README.md | ✅ 已完成 |

### 主要剩余差距
1. Tier 2+ PDE families（stokes, linear_elasticity, allen_cahn — 需要 mixed spaces）
2. BrainProvider / governance adapter（Phase 5）
3. 高阶混合 FE 空间（Nedelec, RT, Hu-Zhang）
4. HPC scheduler adapter（SLURM 后端）

---

## 推荐执行顺序

```text
Phase 0 (✅) → Phase 1 (✅) → Phase 2 (✅) → Phase 3 (✅) → Phase 4 (✅) → Phase 5
```

测试基线已建立（84 tests + 18 smoke gated, ruff clean），文档已完成。下一阶段：生产化治理集成与 HPC 支持（Phase 5）。

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
- [ ] `FealpyGovernanceAdapter` — 对接 MHE core governance path（session events, provenance graph）
- [ ] `FealpyAsyncExecutor` — 异步执行生命周期
- [ ] HPC scheduler adapter — SLURM 后端支持
- [ ] 大规模 3D 问题资源配额管理
- [ ] Benchmark 集成 — 对接 MHE benchmark framework（三层 lane 结构）

**验收标准**：governance adapter 产出 valid candidate records；SLURM backend 在集群环境通过 dry-run

**依赖**：Phase 4 功能基线稳定

---

## 风险 / 依赖

| 风险 | 影响 | 缓解 |
|---|---|---|
| fealpy API breaking change | 高 | 钉住 v3.4.0，environment probe 报告版本 |
| 多 PDE family 模板复杂度 | 中 | Phase 4 做 per-family 分支，Phase 0-3 只支持 Poisson |
| 真实 fealpy 环境不可用 | 中 | 默认测试全 mock；smoke test gated |
| 多 backend 数值差异 | 中 | per-backend 容差配置；environment evidence 记录 |
| 大规模网格性能 | 低 | timeout + 子进程内存隔离；Phase 5 做资源配额 |

---

## Phase Map 总览

| Phase | 名称 | 状态 | 测试 | 文件数 |
|---|---|---|---|---|
| 0 | Minimal Skeleton | ✅ | 28 tests | 15 文件 |
| 1 | Evidence / Policy / Study | ✅ | 6 新文件 | 6 文件 |
| 2 | 测试补全 + 集成验证 | ✅ | 76 tests（含 6 smoke） | 5 新测试 |
| 3 | 文档 + Wiki | ✅ | — | 3 文档 |
| 4 | 扩展与优化 | ✅ | 84+18 tests（18 smoke） | 1 新测试 + 3 生产代码 |
| 5 | 生产化 | — | — | TBD |
