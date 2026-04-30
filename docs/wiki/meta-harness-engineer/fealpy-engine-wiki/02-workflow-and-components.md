# 02. Workflow and Component Chain

## 1. Canonical Component Chain

```text
FealpyGateway (task intake + spec validation)
  → FealpyEnvironmentProbe (fealpy version, backend availability)
    → FealpyCompiler (Python solver script generation)
      → FealpyExecutor (subprocess execution)
        → FealpyValidator (numeric tolerance verification) [protected]
          → build_evidence_bundle() (structured evidence assembly)
            → FealpyEvidencePolicy (5-gate promotion evaluation)

Optional extensions:
  → FealpyStudyComponent (parameter sweep via grid search)
  → FealpyGovernanceAdapter (MHE core governance integration)
  → FealpyAsyncExecutor (async execution lifecycle)
  → FealpyDomainBrainProvider (LLM-guided mesh/degree optimization)

HPC dispatch:
  FealpySchedulerAdapter
    ├── FealpySlurmBackend (sbatch + sacct)
    └── FealpyK8sBackend (kubectl apply/get/delete)

Resource control:
  FealpyResourceQuotaProvider (DOF + memory estimation, exhausted gating)
```

## 2. Component Responsibilities

### Gateway (`fealpy_gateway.primary`)

- 接收 `FealpyProblemSpec`，验证 PDE family 合法性（22 个白名单）
- 提供 `issue_task(spec)` — 验证并返回 spec + metadata
- 提供 `compile_experiment(spec, environment, compiler)` — 编译实验计划
- 提供 `run_baseline(spec)` — 串联完整 pipeline：probe → compile → execute
- `declare_interface()` 绑定 slot `fealpy_gateway.primary`，提供 capability `fealpy.task.issue`

### Environment Probe (`fealpy_environment.primary`)

- 检查 fealpy 包可导入性，获取 `__version__`
- 探测后端可用性：numpy（必需）、pytorch（可选）、jax（可选）
- 返回已注册的 PDE 类型列表（22 种）
- 产出 `FealpyEnvironmentReport`：`available`, `fealpy_version`, `available_backends`, `available_pde_families`, `blocks_promotion`
- `declare_interface()` 绑定 `fealpy_environment.primary`，提供 `fealpy.environment.probe`

### Compiler (`fealpy_compiler.primary`)

- 将 `FealpyProblemSpec` 编译为 `FealpyRunPlan`（含自包含 `solve.py` 脚本源代码）
- 生成确定性 `plan_id`（SHA256 of spec JSON）
- 7 个 PDE 模板方法通过 `_FAMILY_RENDERERS` dispatch dict 路由（18 个 PDE families 映射）
- 4 个共享模板片段：`_render_header`, `_render_mesh_builder`, `_render_pde_load`, `_render_scalar_output`
- 网格构建支持 6 种网格类型（interval, tri, quad, tet, hex, uniform）
- FE 空间类型 dispatch：Lagrange / FirstNedelec / RaviartThomas / HuZhang / Taylor-Hood
- `declare_interface()` 绑定 `fealpy_compiler.primary`，提供 `fealpy.compile`

### Executor (`fealpy_executor.primary`)

- 在 workspace 下写入 `solve.py`
- 通过 `subprocess.run([sys.executable, script_path])` 在子进程中执行
- 控制 timeout、cwd、PYTHONPATH
- 捕获 stdout 并解析 JSON（l2_error, h1_error, linf_error, dof_count, wall_time_seconds, mesh_info）
- 资源配额检查：`runtime.resolved_resource_quota()` exhausted → 立即返回 failed artifact
- 产出 `FealpyRunArtifact`，4 种状态：`completed`, `failed`, `timeout`, `unavailable`
- `declare_interface()` 绑定 `fealpy_executor.primary`，提供 `fealpy.execute.run`

### Validator (`fealpy_validator.primary`) — protected

- 区分 6 种 `FealpyValidationStatus`：`ENVIRONMENT_INVALID`, `COMPILE_FAILED`, `RUNTIME_FAILED`, `OUTPUT_MISSING`, `NUMERIC_VALIDATION_FAILED`, `EXECUTED`
- 检查 artifact status，对 `unavailable`/`timeout`/`failed` 生成对应 `ValidationIssue`
- 对 L2、H1、Linf 误差应用容差检查
- `blocks_promotion` computed field：any issue with `blocks_promotion=True` → entire report blocks
- `protected = True`

### Evidence (`build_evidence_bundle()`)

- 自由函数，从 artifact + validation + environment + plan 组装 `FealpyEvidenceBundle`
- 收集 evidence refs，生成 warning（缺失 validation、环境问题）
- 包含 provenance metadata（task_id, plan_ref, artifact_ref, validation_ref）

### Policy (`FealpyEvidencePolicy`)

- 5 级 gate 链：`fealpy_environment_readiness` → `fealpy_validation_presence` → `fealpy_validation_status` → `fealpy_evidence_files` → `fealpy_evidence_ready`
- 每个 gate 产出 ALLOW / DEFER / REJECT
- 最终决策：ALLOW（全部通过）、DEFER（存疑）、REJECT（阻断）

### Study (`fealpy_study.primary`)

- 接收 `FealpyStudySpec`（task_template + axes），生成参数组合的笛卡尔积
- 对每个参数快照：mutate task → compile → execute → validate → evidence → policy
- 提取目标指标（默认最小化 L2 误差），推荐最优 trial
- 模块级辅助函数：`_compute_drop_ratios()`（收敛率计算）、`_compute_observed_order()`（观测阶）
- `declare_interface()` 绑定 `fealpy_study.primary`，提供 `fealpy.study.run`

### Governance (`FealpyGovernanceAdapter`)

- 对接 MHE core governance path：构建 `ValidationReport`、`CandidateRecord`、`SessionEvent`（3 种类型）
- `emit_runtime_evidence()` — 写入 session store、audit log、provenance graph
- Non-HarnessComponent（通过 adapter 模式集成）

### Async Executor (`FealpyAsyncExecutor`)

- 遵循 `AsyncExecutorProtocol`：`submit(plan) → JobHandle`, `poll(job_id)`, `cancel(job_id)`, `await_result(job_id, timeout) → FealpyRunArtifact`
- 将 `FealpyRunArtifactStatus` 映射到 `ExecutionStatus`

### Domain Brain Provider (`FealpyDomainBrainProvider`)

- 从 study report 提取 `FealpyStudyObservation`，分析收敛性
- 三种优化策略：`deterministic`, `bayesian`, `llm_guided`
- `propose()` 输出 `MutationProposal` 列表（mesh/degree 调整建议）

### Scheduler (`FealpySchedulerAdapter` + backends)

- `FealpySlurmBackend` — sbatch/sacct dry-run 支持，job submission/status mapping
- `FealpyK8sBackend` — kubectl apply/get/delete，K8s conditions → ExecutionStatus 映射
- `FealpySchedulerAdapter` — prefix matching dispatch（`slurm://`, `k8s://`），quota gate
- `FealpySchedulerAdapter.submit(plan, *, quota)` — 可选 quota 参数

### Resource Quota Provider (`fealpy_quota_provider.primary`)

- `estimate_dofs(spec)` — 模块级 DOF 估算（Lagrange/Nedelec/RT/HuZhang/Taylor-Hood，2D/3D）
- `estimate_memory_mb(dofs)` — 粗略内存估算（5 矩阵 × 8-byte float）
- `estimate_quota(spec, dof_limit, memory_mb_limit) → ResourceQuota` — 默认 2M DOFs / 2048 MB
- `declare_interface()` 绑定 `fealpy_quota_provider.primary`，提供 `fealpy.quota.provide`

## 3. Data Flow Between Components

```
FealpyProblemSpec (typed task input)
  │
  ├─→ FealpyEnvironmentProbe.probe(spec) → FealpyEnvironmentReport
  │
  ├─→ FealpyCompiler.compile(spec, environment) → FealpyRunPlan
  │     └─ .script_source (自包含 solve.py)
  │     └─ .workspace_dir
  │     └─ .plan_id (SHA256 deterministic)
  │
  ├─→ FealpyExecutor.execute_plan(plan, environment) → FealpyRunArtifact
  │     └─ .l2_error, .h1_error, .linf_error
  │     └─ .dof_count, .wall_time_seconds
  │     └─ .mesh_info (nc, nn)
  │     └─ .status (completed/failed/timeout/unavailable)
  │
  ├─→ FealpyValidator.validate(artifact, plan) → FealpyValidationReport
  │     └─ .passed (all tolerance checks)
  │     └─ .status (FealpyValidationStatus enum)
  │     └─ .l2_passed, .h1_passed, .linf_passed
  │     └─ .blocks_promotion
  │
  └─→ build_evidence_bundle(artifact, validation, plan, environment)
       → FealpyEvidenceBundle
         └─ FealpyEvidencePolicy.evaluate(bundle) → FealpyPolicyReport
```

Each downstream component can safely assume upstream outputs are type-validated Pydantic models. Components do not bypass previous stages.
