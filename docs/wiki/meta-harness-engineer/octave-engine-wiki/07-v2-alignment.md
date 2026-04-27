# 07. v2 对齐方案 — 通往 AI-Native 科学工作流

> 状态：proposal | 依赖：Phase 0–5 Octave worker 完成
> 参考：`docs/.trash/plan/Octave-Ext.md`、`blueprint/07-octave-extension-blueprint.md`、本 wiki 01–06 章

## 1. 定位

Step 1（Phase 0–5）交付的是一个 **MHE-managed Octave worker**：类型化契约 → wrapper 编译 → CLI 执行 → 证据验证。它解决了"受控执行"问题。

Step 2 的目标是把 Octave worker 从一条独立 pipeline 提升为 **MHE scientific workflow substrate**——可承载科学上下文验证、sessionized study、长任务执行、governance 与 optimizer 桥接的计算节点。它不新建一个平台，不退回原始六层 MATLAB 替代愿景的大包大揽，而是通过 MHE 现有的 `BrainProvider`、`ExecutionLifecycleService`、`OptimizerComponent`、`MutationProposal`、`ArtifactSnapshotStore` 和 `ComponentRuntime` 扩展面，逐层接入 AI-native 科学计算能力。

> Octave v2 = MHE scientific workflow substrate for Octave-based experiments, bridging controlled worker execution with AI-native scientific context and session orchestration.

## 2. 前置条件

| 前置项 | 来源 | 说明 |
|--------|------|------|
| `OctaveExperimentSpec → OctaveRunPlan → OctaveRunArtifact → OctaveValidationReport` 全链路 | Phase 4 | 端到端可运行 |
| `OctaveStudyComponent` + `OctaveStudySpec` | Phase 5 | 参数扫描原语 |
| `OctaveEvidencePolicy` 产出 `ready/defer/blocked` | Phase 3 | governance 词汇稳定 |
| `unit: str \| None`、`method_hints: dict`、`parameters: dict` 预留字段 | Phase 1 contracts | SCE 接入点 |
| 默认 tests mock/avoid real `octave-cli`；真实 smoke future gated | Phase 4 | 回归安全网 |

## 3. V2 架构：六层叠加

所有新增层在 v1 stable worker 基础上叠加，不修改 v1 链路。

### Layer A — Stable Worker Foundation（v1，不变）

```text
OctaveExperimentSpec
  → OctaveEnvironmentReport
  → OctaveRunPlan
  → OctaveRunArtifact
  → OctaveValidationReport
  → OctaveEvidenceBundle
```

v1 链路必须保持 deterministic wrapper、受控 workspace、`--no-init-file`、typed output schema、numeric validation、evidence refs。

### Layer B — Scientific Context Adapter

在 compiler 前和 validator 后各设一个 hook：

```text
Pre-compile hook:
  OctaveExperimentSpec (with unit/tolerance/method_hints)
    → ScientificContextAdapter.pre_compile(spec)
    → context_issues: list[ValidationIssue]
    → enriched_spec: OctaveExperimentSpec (constants injected, units normalized)

Post-validation hook:
  OctaveValidationReport + OctaveRunArtifact
    → ScientificContextAdapter.post_validate(report, artifact, spec)
    → context_evidence: ScoredEvidence
    → additional_issues: list[ValidationIssue]
    → context_facts: dict (BLAS/LAPACK, platform, numerical method notes)
```

Adapter 不做 promotion，只产出 evidence 和 issues。

**扩展 v1 预留字段为 v2 活跃字段：**

```python
class OctaveOutputSpec(BaseModel):
    variable: str
    kind: Literal["numeric", "array", "figure", "file"]
    unit: str | None = None              # v2: "m/s^2", "eV/c^2"
    expected_shape: tuple[int, ...] | None = None
    expected_dtype: str | None = None
    tolerance: ToleranceSpec | None = None
    uncertainty: UncertaintySpec | None = None   # v2 new
    invariants: list[InvariantSpec] | None = None  # v2 new

class UncertaintySpec(BaseModel):
    """v2: 误差传播规格"""
    source_variables: list[str]
    method: Literal["linear", "monte_carlo", "automatic"] = "automatic"
    confidence_level: float = 0.95

class InvariantSpec(BaseModel):
    """v2: 物理不变量检查"""
    expression: str          # e.g., "sum(inputs) == sum(outputs)"
    description: str
    tolerance: float = 1e-10

class OctaveInputAssetSpec(BaseModel):
    # ... v1 fields
    unit: str | None = None              # v2: input unit
    uncertainty: float | None = None     # v2: input uncertainty magnitude

class OctaveScriptSpec(BaseModel):
    # ... v1 fields
    method_hints: MethodHints | None = None  # v2: 从预留 dict 升级为强类型

class MethodHints(BaseModel):
    """v2: 数值方法提示"""
    problem_type: str | None = None       # "ode", "pde", "optimization", "linear_system"
    stiffness: Literal["auto", "stiff", "non_stiff"] = "auto"
    solver_preference: list[str] | None = None
    sparse: bool | None = None
```

**SCE 新增组件：**

```text
metaharness_ext/octave/sce/
├── __init__.py
├── dimensional.py        # 量纲一致性检查器（基于 pint）
├── error_propagation.py  # 误差传播引擎（基于 uncertainties）
├── constants.py          # CODATA/PDG 物理常数注入 + 溯源标注
├── method_selector.py    # 数值方法推荐器（ODE 刚性检测、稀疏性判断）
└── adapter.py            # OctaveScientificContextAdapter（pre_compile + post_validate）
```

**MHE 集成：** SCE 组件通过 `declare_interface()` 注册 capability `octave.sce.check`。`OctaveScriptCompiler` 在 `requires` 中声明 `octave.sce.check`（optional，缺失时跳过 SCE 检查）。SCE 的 `ValidationIssue` 直接进入现有 evidence bundle 和 governance 判定流程。

### Layer C — Sessionized Study Workflow

完全遵循 DeepMD/QCompute/JEDI study pattern，将单次 run 组织为可追踪的 study：

```python
class OctaveStudyAxis(BaseModel):
    parameter_path: str           # dot-path into OctaveExperimentSpec
    values: list[Any] | None = None
    range: tuple[float, float] | None = None
    step: float | None = None

class OctaveStudySpec(BaseModel):
    study_id: str
    task_id: str
    base_task: OctaveExperimentSpec
    axes: list[OctaveStudyAxis]
    strategy: Literal["grid", "sequential", "bayesian"] = "grid"
    max_trials: int = 100
    objective_metric: str          # key path for metric extraction
    goal: Literal["minimize", "maximize"] = "minimize"
    convergence: StudyConvergenceSpec | None = None
    handoff_policy: Literal["none", "recommended", "all"] = "none"

class OctaveStudyTrial(BaseModel):
    trial_id: str
    parameter_snapshot: dict[str, Any]
    run: OctaveRunArtifact | None = None
    validation: OctaveValidationReport | None = None
    evidence_bundle: OctaveEvidenceBundle | None = None
    policy_report: OctavePolicyReport | None = None
    metric_value: float | None = None
    passed: bool = False
    messages: list[str] = Field(default_factory=list)

class OctaveStudyReport(BaseModel):
    study_id: str
    task_id: str
    trials: list[OctaveStudyTrial]
    best_trial_id: str | None = None
    recommended_parameters: dict[str, Any] | None = None
    convergence_analysis: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
```

**OctaveStudyComponent**（follow DeepMD pattern）：

```python
class OctaveStudyComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OCTAVE_STUDY_SLOT)
        api.declare_input("study", "OctaveStudySpec")
        api.declare_output("report", "OctaveStudyReport", mode="sync")
        api.provide_capability(CAP_OCTAVE_STUDY_RUN)

    def run_study(
        self,
        spec: OctaveStudySpec,
        *,
        compiler: OctaveScriptCompiler,
        executor: OctaveExecutor,
        validator: OctaveValidator,
        context_adapter: OctaveScientificContextAdapter | None = None,
        runtime: HarnessRuntime | None = None,
    ) -> OctaveStudyReport:
        # 1. Enumerate trials from axes
        # 2. For each trial:
        #    a. _mutate_task(spec, value) → OctaveExperimentSpec
        #    b. Optional: context_adapter.pre_compile(spec) → enriched spec
        #    c. compiler.build_plan(spec) → OctaveRunPlan
        #    d. executor.execute_plan(plan) → OctaveRunArtifact
        #    e. validator.validate_run(artifact, plan) → OctaveValidationReport
        #    f. build_evidence_bundle(artifact, validation) → OctaveEvidenceBundle
        #    g. policy.evaluate(bundle) → OctavePolicyReport
        #    h. _extract_metric(validation, spec.objective_metric) → float
        # 3. _recommend_trial(trials, goal) → best trial
        # 4. _handoff_trials(runtime, trials, handoff_policy) → candidate records
        # 5. Build OctaveStudyReport
```

### Layer D — Execution Lifecycle & HPC Adapter

**本地异步执行**：`OctaveAsyncExecutor` 实现 `AsyncExecutorProtocol`，对接 `ExecutionLifecycleService`：

```python
class OctaveAsyncExecutor:
    """Wraps OctaveExecutor to implement AsyncExecutorProtocol."""

    async def submit(self, plan: RunPlanProtocol | Any) -> JobHandle: ...
    async def poll(self, job_id: str) -> ExecutionStatus: ...
    async def cancel(self, job_id: str) -> None: ...
    async def await_result(self, job_id: str, timeout: float | None = None) -> RunArtifactProtocol: ...
```

v2 的 `OctaveGateway.run_baseline_async()` 对接 `ExecutionLifecycleService.run()`，自动记录 `TASK_SUBMITTED` / `TASK_RUNNING` / `TASK_COMPLETED` / `TASK_FAILED` / `TASK_CANCELLED` / `TASK_RETRIED`。

**HPC 后端**：新增 `OctaveSchedulerAdapter`，同一 `OctaveRunPlan` 可路由到不同后端：

```text
OctaveRunPlan
  │
  ▼
ExecutionLifecycleService
  │
  ├───[local mode]──► OctaveAsyncExecutor
  │
  └───[cluster mode]──► OctaveSchedulerAdapter
                          ├─── OctaveSlurmBackend
                          │      ├─ 生成 sbatch 脚本
                          │      ├─ 提交作业 → job_id
                          │      ├─ 轮询 sacct 获取状态
                          │      └─ 收集输出 → OctaveRunArtifact
                          │
                          └─── OctaveK8sBackend
                                 ├─ 生成 Job manifest → submit
                                 ├─ 轮询 pod phase
                                 └─ 收集输出 + 日志 → OctaveRunArtifact
```

**Contract 扩展：**

```python
class OctaveExecutableSpec(BaseModel):
    # ... v1 fields
    target_backend: Literal["local", "slurm", "k8s"] = "local"  # v2
    walltime: str | None = None           # v2: "HH:MM:SS"
    resources: ResourceRequest | None = None  # v2

class ResourceRequest(BaseModel):
    cpus: int = 1
    memory_gb: float = 4.0
    gpus: int = 0
    queue: str | None = None

class SlurmConfig(BaseModel):
    partition: str = "compute"
    nodes: int = 1
    cpus_per_task: int = 1
    memory_gb: int = 8
    time_hours: int = 24
    modules: list[str] = []       # ["octave/9.2.0"]
    account: str | None = None

class K8sConfig(BaseModel):
    image: str = "gnuoctave/octave:9.2.0"
    namespace: str = "mhe-jobs"
    resources: dict[str, dict] = {"requests": {"cpu": "1", "memory": "4Gi"}}
    node_selector: dict[str, str] = {}
```

关键原则：同一个 `OctaveRunArtifact` 无论本地还是集群执行，格式一致——validator 和 evidence policy 无需感知执行后端。

**HPC workspace 传输**（新增组件）：

```text
metaharness_ext/octave/scheduler/
├── __init__.py
├── adapter.py         # OctaveSchedulerAdapter（AsyncExecutorProtocol）
├── slurm_backend.py   # SLURM sbatch/sacct 集成
├── k8s_backend.py     # Kubernetes Job API 集成
└── workspace_sync.py  # workspace 打包/传输/解包
```

### Layer E — Governance & Optimizer Bridge

**Governance Adapter**（follow DeepMD/QCompute pattern）：

```python
class OctaveGovernanceAdapter:
    def __init__(self, *, session_id: str | None = None, actor: str = "octave_governance") -> None:
        self.session_id = session_id
        self.actor = actor

    def build_core_validation_report(self, validation, policy) -> ValidationReport:
        """Merge validation.issues + policy gate issues. Aggregate blocks_promotion."""

    def build_candidate_record(self, bundle, policy, *, snapshot=None) -> CandidateRecord:
        """Build candidate record for graph promotion."""

    def build_session_events(self, bundle, policy) -> list[SessionEvent]:
        """Emit CANDIDATE_VALIDATED, SAFETY_GATE_EVALUATED, CANDIDATE_REJECTED events."""

    def emit_runtime_evidence(self, bundle, policy, *, session_store, audit_log, provenance_graph) -> dict:
        """Full provenance + audit recording via runtime services."""

    def record_with_artifact_store(self, bundle, policy, *, session_store, audit_log, provenance_graph, artifact_store) -> dict:
        """Record evidence + artifact snapshot via ExecutionEvidenceRecorder."""
```

**Optimizer Bridge**：

```python
class OctaveDomainBrainProvider:
    """BrainProvider for Octave parameter exploration."""

    def __init__(self, *, llm: BrainProvider | None = None):
        self._llm = llm  # 可选 LLM backend，通过 ComponentRuntime 注入

    def propose(
        self,
        optimizer: OptimizerComponent,
        observations: list[Observation],
    ) -> list[MutationProposal]:
        """基于历史 Observation 生成下一组参数候选。
        
        策略（可配置）：
        - Bayesian optimization（scikit-optimize）— 默认，可离线运行，可复现
        - LLM-guided — 使用 LLM 理解参数语义，生成物理合理的候选
        - Nelder-Mead simplex — 无需梯度的直接搜索
        Only propose typed whitelist field changes.
        """

    def evaluate(
        self,
        optimizer: OptimizerComponent,
        proposal: MutationProposal,
        observations: list[Observation],
    ) -> ProposalEvaluation:
        """Score proposal against trial history: validation metrics + convergence + governance."""
```

**集成模式：**

```text
OctaveStudyComponent completes trials
  → observations fed to OptimizerComponent
  → OctaveDomainBrainProvider.propose() generates new parameter suggestions
  → New trials created from proposals
  → Convergence checked via TripleConvergence
```

Study 网格扫描与 BrainProvider 自适应搜索互补：

| 模式 | 组件 | 适用场景 |
|------|------|----------|
| 网格扫描 | `OctaveStudyComponent` | 已知参数范围，穷举验证 |
| 自适应搜索 | `OctaveDomainBrainProvider` + `OptimizerComponent` | 参数空间大，需要智能探索 |
| 混合模式 | 两者串联 | Study 粗扫描定界 → BrainProvider 精细优化 |

### Layer F — Enhanced Security & Artifacts

**Static Script Scanner**（compile-time defense-in-depth，不替代 OS sandbox）：

```python
class OctaveSecurityScanner:
    DANGEROUS_PATTERNS = [
        (r'\bsystem\s*\(', "shell_execution"),
        (r'\bunix\s*\(', "shell_execution"),
        (r'!\w', "shell_execution"),
        (r'\burlread\b', "network_access"),
        (r'\burlwrite\b', "network_access"),
        (r'\bweb\b', "network_access"),
        (r'\bpkg\s+install\b', "package_install"),
    ]

    def scan(self, script_content: str) -> SecurityScanReport:
        """Return list of SecurityFinding(code, line, severity, message)."""
```

Scanner 在 compiler 中调用，发现 dangerous patterns 时产出 `ValidationIssue(category=SAFETY, blocks_promotion=True)`。

**Enhanced Artifact Support：**

```python
class OctaveMATFileParser:
    """Parse .mat files using scipy.io.loadmat for structured output extraction."""
    def parse(self, path: Path) -> dict[str, Any]:
        # Extract variable names, shapes, dtypes → structured dict

class OctaveArtifactDetector:
    """Scan workspace for all output artifacts."""
    def detect(self, working_dir: Path, output_spec: list[OctaveOutputSpec]) -> ArtifactDiscovery:
        # Find .mat, .txt, .json, .csv, .png, .pdf, .svg
        # Match against expected outputs
        # Return ArtifactDiscovery(found, missing, unexpected)
```

---

## 4. Live Workspace（v3 方向，不入 v2）

原始愿景中的 Live Workspace Engine 提供持久变量空间。v2 不引入常驻 `octave-cli` 进程或 IPykernel 会话，原因：

1. `octave-cli` 不支持 server mode / kernel protocol；
2. 常驻会话引入状态污染、非确定性和安全边界模糊，与 MHE evidence-first 原则冲突；
3. sessionized artifacts + checkpoint refs（Layer C/D）在保持 run 隔离性的同时提供了等价的状态追踪能力。

后续若 Octave 生态出现稳定的 kernel protocol 实现，可作为 v3 的 `LiveWorkspaceBackend` 接入。当前通过 `workspace_ref` snapshot/restore 模式（见下方开放问题 #2）作为轻量替代，仅供同 session 内 trial 间变量传递。

---

## 5. 原始愿景映射

| 原始六层愿景 | v1 状态 | v2 对齐 | v3/未来 |
|---|---|---|---|
| 用户交互层 | 不覆盖 | study report 可被上层 UI/CLI/Notebook 消费 | Notebook / Workspace UI |
| Live Workspace Engine | 不覆盖 | sessionized artifacts + checkpoint refs（不入 v2 交付） | 持久变量空间 service |
| Scientific Context Engine | 仅预留字段 | v2 核心：unit、uncertainty、method hints、constants、invariants | 完整领域知识库 |
| Agent 编排层 | 不覆盖 | BrainProvider + MutationProposal + study trials | 多 Agent planner / RAG |
| 专业科学 Agent 层 | 不覆盖 | context adapter + evidence 产出科学判断 | 专业 Agent 消费 substrate |
| 块图仿真引擎 | 不覆盖 | 不入 v2 | OpenModelica / FMU/FMI（独立 `metaharness_ext.modelica`） |
| 计算基础设施层 | octave-cli worker | ExecutionLifecycle + resource quota + scheduler adapter seam | SLURM/K8s 生产后端 |

---

## 6. V2 子阶段路线图

```text
Phase 5a: Study Component (v2 核心) — implemented
  ├─ OctaveStudyComponent with OctaveStudySpec / OctaveStudyReport
  ├─ _mutate_task() 和 _recommend_trial()
  ├─ Grid strategy + metric extraction
  └─ Study tests (mocked)

Phase 5b: Governance Adapter + Evidence Pipeline — prototype implemented
  ├─ OctaveGovernanceAdapter
  ├─ build_core_validation_report, build_candidate_record, build_session_events
  ├─ emit_runtime_evidence / record_with_artifact_store no-op safely without runtime services
  └─ Governance tests

Phase 5c: Scientific Context Adapter — implemented
  ├─ OctaveScientificContextAdapter
  ├─ Pre-compile: unit consistency, method hints validation
  ├─ Post-validate: error propagation notes, platform difference explanation, invariants checking
  ├─ Active v2 contract fields: unit, uncertainty, method_hints, invariants
  └─ Context adapter tests

Phase 5d: Execution Lifecycle + Security — prototype implemented
  ├─ OctaveAsyncExecutor (AsyncExecutorProtocol-compatible local wrapper)
  ├─ ExecutionLifecycleService-compatible submit/poll/cancel/await_result seam
  ├─ OctaveSecurityScanner integrated into compiler
  ├─ OctaveMATFileParser / OctaveArtifactDetector
  ├─ Dry-run HPC scheduler adapter + SlurmBackend / K8sBackend + workspace_sync
  └─ Execution, security, artifact, scheduler tests

Phase 5e: Optimizer Bridge — prototype implemented
  ├─ OctaveDomainBrainProvider
  ├─ Study observations → typed whitelist MutationProposal
  ├─ Deterministic untried-parameter proposal strategy
  ├─ Proposal scoring against validation evidence
  └─ Optimizer bridge tests
```

**依赖关系：** 5a 和 5c 可并行启动。5b 依赖 5a（governance 消费 study trial evidence）。5d 依赖 Phase 4 executor 稳定，可与 5a/5c 并行。5e 依赖 5a + 5c（BrainProvider 使用 SCE 提供物理约束）。

---

## 7. 关键文件

### 新建

- `docs/wiki/meta-harness-engineer/octave-engine-wiki/02-v2-alignment.md` — 本文件

### 修改

- `docs/wiki/meta-harness-engineer/blueprint/07-octave-extension-blueprint.md` — Phase 5 拆为 5a–5e 子阶段
- `docs/wiki/meta-harness-engineer/octave-engine-wiki/01-design.md` — 补充 v1/v2/v3 分层引用

### MHE 代码参考（不改动）

- `src/metaharness/core/execution.py` — `ExecutionLifecycleService`, `ExecutionEvidenceRecorder`
- `src/metaharness/sdk/execution.py` — `RunPlanProtocol`, `AsyncExecutorProtocol`, `PollingStrategy`
- `src/metaharness/core/models.py` — `ScoredEvidence`, `ValidationIssue`, `SessionEventType`
- `src/metaharness/provenance/` — `ProvGraph`, `AuditLog`, `ArtifactSnapshotStore`
- `src/metaharness/core/brain.py` — `BrainProvider`, `FunctionalBrainProvider`
- `src/metaharness/core/mutation.py` — `MutationProposal`
- `src/metaharness/components/optimizer.py` — `OptimizerComponent`, `TripleConvergence`, `FitnessEvaluator`
- `src/metaharness_ext/deepmd/study.py` — study pattern reference
- `src/metaharness_ext/qcompute/study.py` — bayesian/agentic strategy reference
- `src/metaharness_ext/jedi/study.py` — study pattern reference
- `src/metaharness_ext/deepmd/governance.py` — governance adapter pattern reference

---

## 8. 完成判据

### 文档层

- v1/v2/v3 映射表清晰，不重新承诺 MATLAB parity
- 每个 v2 对齐面有 MHE 复用路径说明
- study/context/execution/governance/optimizer 各有完整 API 设计

### Prototype 层

- `OctaveStudyComponent` 可运行 grid parameter sweep
- Scientific context adapter 对 unit/tolerance/invariants 产出 evidence
- `OctaveAsyncExecutor` 提供 `ExecutionLifecycleService` 可消费的 async executor seam
- Governance adapter 可 build candidate record、session events、runtime evidence refs
- Security scanner 可检测 `system()`/`unix()`/`!cmd` 等危险模式，并在 compiler 阶段阻断
- MAT/artifact detector、dry-run scheduler adapter、optimizer bridge 均有默认测试覆盖

### Production readiness

- 长任务可取消或以失败状态安全结束；真实恢复语义仍由上层 runtime/session recovery 接管
- Scheduler/HPC adapter 目前是 dry-run backend contract；真实 SLURM/K8s submit/poll/collect 仍需 gated 环境实现
- BrainProvider/mutation proposal 只修改 typed whitelist fields
- 所有默认测试不依赖真实 Octave；真实 smoke gated

---

## 9. 开放设计问题

1. **SCE 检查粒度**：量纲/误差传播检查应在 compiler 前（blocking）还是 validator 后（non-blocking 验证）？默认建议两者都有——pre-compile 做 blocking 检查，post-validate 做 non-blocking 验证并标注 evidence。

2. **Live Workspace 的 session 边界**：workspace snapshot 是否允许跨 session 引用？默认建议同 session 内自动允许，跨 session 需要显式 governance 审批。此功能不入 v2 交付，但 contracts 保留 `workspace_ref` 扩展点。

3. **BrainProvider 的 LLM 选型**：默认 Bayesian optimization（可离线运行，可复现），LLM 通过 `runtime.llm` 可选注入增强。LLM-guided 模式需 governance 审批参数搜索范围。

4. **HPC workspace 传输**：优先支持共享文件系统（Lustre/NFS，HPC 标准做法），对象存储（S3/MinIO）作为后续增强。

5. **块图仿真引擎归属**：独立 `metaharness_ext.modelica` extension，通过 MHE graph 与 Octave extension 协作而非耦合。

6. **Step 2 期间 Step 1 的兼容性**：所有 contract 变化向后兼容——新字段全部可选（`None` 默认值），新 capability 全部 optional（缺失时优雅降级）。

---

## 10. 验证命令

```bash
# 确认没有重新引入范围误导
rg "MATLAB 替代|全面替代|Simulink 替代|Live Workspace" \
  docs/wiki/meta-harness-engineer/octave-engine-wiki/02-v2-alignment.md
# Should only appear in "out of scope" or "v3/未来" context

# 确认 v2 关键组件有具体设计引用
rg "ExecutionLifecycleService|BrainProvider|MutationProposal|OctaveStudyComponent|OctaveGovernanceAdapter" \
  docs/wiki/meta-harness-engineer/octave-engine-wiki/02-v2-alignment.md
# Should show concrete design references

# 确认已删除的 family 没有重新出现
rg "plot_export family|package_probe family" \
  docs/wiki/meta-harness-engineer/octave-engine-wiki/
# Should return no matches

# 后续实现验证
python -m pytest tests/test_metaharness_octave_*.py -q
ruff check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
```
