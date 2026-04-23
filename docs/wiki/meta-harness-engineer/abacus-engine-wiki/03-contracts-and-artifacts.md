# 03. ABACUS Contracts 与产物

## 3.1 设计原则

`metaharness_ext.abacus` 的 contracts 设计应满足三个目标：

1. **family-aware**：区分 `scf`、`nscf`、`relax`、`md`
2. **file-aware**：显式表达 `INPUT` / `STRU` / `KPT` 与相关资产
3. **artifact-aware**：运行后的证据不止是 return code，而是 `OUT.<suffix>/` 与家族相关文件集

---

## 3.2 推荐基础字面量

```python
AbacusApplicationFamily = Literal["scf", "nscf", "relax", "md"]
AbacusBasisType = Literal["pw", "lcao"]
AbacusLauncher = Literal["direct", "mpirun", "mpiexec", "srun"]
AbacusESolverType = Literal["ksdft", "dp"]
AbacusRunStatus = Literal["planned", "completed", "failed", "unavailable"]
AbacusValidationStatus = Literal[
    "environment_invalid",
    "input_invalid",
    "executed",
    "validation_failed",
    "runtime_failed",
]
```

这些字面量应该覆盖首版设计范围，不预先承诺所有 ABACUS 边缘模式。

---

## 3.3 推荐 typed specs

### `AbacusExecutableSpec`

建议字段：

- `binary_name: str = "abacus"`
- `launcher: AbacusLauncher = "direct"`
- `timeout_seconds: int | None = None`
- `launcher_args: list[str] = Field(default_factory=list)`
- `env: dict[str, str] = Field(default_factory=dict)`

### `AbacusStructureSpec`

用于表达 `STRU` 的受控内容，至少包括：

- 物种信息
- 晶格常数 / 晶格向量
- 原子坐标
- 可选速度（MD）
- 与 basis / mode 相关的伪势、轨道、模型文件引用

### `AbacusKPointSpec`

用于表达 `KPT`，至少包括：

- 模式（例如 Monkhorst-Pack 风格）
- 网格 / 偏移

首版应允许某些 family 省略 `KPT`，但不能由 executor 隐式猜测。

### `AbacusRunSpec`

顶层请求合同，建议包含：

- `task_id`
- `application_family`
- `basis_type`
- `esolver_type`
- `executable`
- `structure`
- `kpoints`
- `input_parameters`
- `required_paths`
- `working_directory`
- `suffix`

### family-aware variants

建议定义：

- `AbacusScfSpec`
- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- `AbacusMdSpec`

这样能让不同 family 的最小必需字段在 schema 层表达，而不是都推给 validator。

---

## 3.4 mode-specific 关键约束

### `scf`

- 需要 `STRU`
- 通常需要 `KPT`
- `basis_type=lcao` 时通常需要伪势/轨道资产

### `nscf`

- 需要 `STRU`
- 通常需要 `KPT`
- 需要显式表达 read-file / charge reuse 前提，而不是隐式依赖历史目录

### `relax`

- 需要 `STRU`
- success 不只看 return code，还要看最终结构证据

### `md`

- 需要 `STRU`
- `KPT` 依运行模式而定
- 如果 `esolver_type=dp`：
  - 要求 `pot_file`
  - 不要求 `KPT`
  - 文档路径里不要求伪势和轨道文件

---

## 3.5 环境报告

推荐：

```python
class AbacusEnvironmentReport(BaseModel):
    abacus_available: bool
    version_text: str | None = None
    info_text: str | None = None
    check_input_available: bool
    launcher_available: bool
    deeppmd_enabled: bool | None = None
    gpu_enabled: bool | None = None
    required_paths_present: bool
    messages: list[str] = Field(default_factory=list)
```

这个报告的作用不是取代 validator，而是把“环境是否满足运行前提”前移为显式判据。

---

## 3.6 运行计划

推荐：

```python
class AbacusRunPlan(BaseModel):
    task_id: str
    run_id: str
    application_family: AbacusApplicationFamily
    command: list[str]
    working_directory: str
    input_path: str
    stru_path: str
    kpt_path: str | None = None
    output_root: str
    expected_outputs: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)
    required_runtime_paths: list[str] = Field(default_factory=list)
    rendered_inputs: dict[str, str] = Field(default_factory=dict)
    executable: AbacusExecutableSpec
```

关键点：

- plan 要把工作目录和文件路径稳定化
- command 只表达 launcher + `abacus` 的执行入口
- 文件内容与路径应在 plan 中可审计

---

## 3.7 运行产物

推荐：

```python
class AbacusRunArtifact(BaseModel):
    task_id: str
    run_id: str
    application_family: AbacusApplicationFamily
    command: list[str]
    return_code: int | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    working_directory: str
    output_root: str | None = None
    input_files: list[str] = Field(default_factory=list)
    log_files: list[str] = Field(default_factory=list)
    structure_files: list[str] = Field(default_factory=list)
    restart_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    status: AbacusRunStatus = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)
```

推荐 summary 中保留：

- `suffix`
- `effective_input_path`
- `converged: bool | None`
- `final_energy: float | None`
- `md_steps: int | None`
- `dpmd_mode: bool`
- `messages: list[str]`

---

## 3.8 验证报告

推荐：

```python
class AbacusValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool
    status: AbacusValidationStatus
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str | bool] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
```

validator 的职责是将环境、执行与 artifact 统一映射到稳定语义，而不是负责重新解析整个 workspace。

---

## 3.9 证据面

ABACUS extension 的 evidence-first 原则应强调：

- `stdout/stderr` 只是辅证
- `OUT.<suffix>/` 是主证据面
- `OUT.<suffix>/INPUT` 是有效输入快照
- `STRU.cif`、`MD_dump`、`Restart_md.dat` 等 family-specific 文件是成功判据的重要部分

因此 `evidence_files` 建议至少汇总：

- rendered input files
- effective input snapshot
- main logs
- final structure / MD / restart 产物

---

## 3.10 首版 contract 边界

首版 contracts 不应过度建模，也不应过度自由：

- 不把所有 ABACUS 参数都拆成强类型字段
- 也不允许完全无约束的 `INPUT` 文本透传成为默认路径
- 应优先覆盖首版 family 需要的稳定字段
- 超出首版边界的参数可以通过受控 `extra_parameters` 一类入口逐步扩展，但要明确边界与校验责任
