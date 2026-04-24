# 01. JEDI Extension Implementation Plan

> 状态：updated | 对当前 `01-jedi-extension-roadmap.md` Phase 0（Environment Probe + Execution Foundation）的边界统一实施计划

## Technical Alignment Notes

本 implementation plan 以 **当前已修正的** `MHE/docs/wiki/meta-harness-engineer/jedi-engine-wiki/`、`01-jedi-extension-blueprint.md` 与 `01-jedi-extension-roadmap.md` 为事实基线。实现与评审默认遵循以下技术事实：

- QG toy-model executable 使用实际二进制名，如 `qg4DVar.x`、`qgLETKF.x`、`qgHofX3D.x`、`qgHofX4D.x`，不要沿用早期下划线命名的占位写法
- `3DFGAT` 不是独立 `cost_type`；FGAT 是 `3D-Var` / `4D-Var` 内通过时间插值体现的运行语义
- 当前本地 GCC 15.2.1 环境下，至少 OOPS 与部分 L95/QG toy-model 路径已被观察到可构建/可运行；但 `ioda` / `ufo` / `saber` 相关 observation stack 的本地可用性不应在 implementation plan 中预设为稳定事实，而应由 `environment probe` 与数据就位状态在执行前显式判定
- diagnostics/output 不应被简化为“纯 NetCDF 日志文件”假设；当前更准确的口径是 IODA/HDF5/ODB diagnostics + 组级证据提取
- 标准 UFO 配置优先使用 `obs operator.name`；`obs space.obs type` 仅应视作 QG legacy YAML 兼容语义
- 文档和实现都必须区分 **CTest test name** 与 **executable name**，例如 `qg_4dvar_rpcg` 可作为测试名存在，但实际运行二进制应写成 `qg4DVar.x`

## 1.1 目标

以当前实现为基线，统一 `MHE/src/metaharness_ext/jedi/` 的 **Phase 0: Environment Probe + Execution Foundation** 语义，使其具备以下最小可用能力：

- 接收 family-aware typed spec
- 编译受控 YAML
- 显式 materialize 运行输入
- 探测 binary / launcher / library / data/testinput prerequisite 环境状态
- 运行 `schema`、`validate_only` 与 `real_run`
- 返回稳定的结构化 `JediEnvironmentReport` 与 `JediValidationReport`

本阶段交付 **基础执行闭环**：显式 preprocessor、mode-aware execution、runtime evidence 归档、preprocessor manifest 记录与 evidence-first validation；但不进入 smoke policy 固化、不引入 richer diagnostics interpretation 或更高层 scientific acceptance checks。

本阶段完成后，系统应具备以下基础能力：

- `spec -> env probe -> YAML -> preprocess -> mode-aware execution -> validation report`
- 明确区分 environment failure、validation failure 与 runtime failure
- 为下一阶段 smoke policy 直接复用 contracts / compiler / preprocessor / executor / validator 骨架

---

## 1.2 范围

### 1.2.1 在范围内

- 新增 `MHE/src/metaharness_ext/jedi/` 包骨架
- 新增 `__init__.py`、`types.py`、`contracts.py`
- 新增 `capabilities.py`、`slots.py`
- 新增 `gateway.py`
- 新增 `environment.py`
- 新增 `config_compiler.py`
- 新增 `executor.py`
- 新增 `validator.py`
- 新增对应 manifest JSON 文件
- 新增 `MHE/tests/test_metaharness_jedi_manifest.py`
- 新增 `MHE/tests/test_metaharness_jedi_imports.py`
- 新增 `MHE/tests/test_metaharness_jedi_environment.py`
- 新增 `MHE/tests/test_metaharness_jedi_validate_only.py`
- 必要时新增 `MHE/tests/test_metaharness_jedi_compiler.py`

### 1.2.2 不在范围内

- `diagnostics.py` / `analyzers.py` 的结构化诊断提取
- environment-gated smoke baseline policy
- richer diagnostics interpretation
- 更高层科学判据（如 `RMS(O-A) < RMS(O-B)`）
- `study` / `mutation` 层
- `EnsembleApplication` 顶层 `files:` 多 YAML 模式
- 新的 model interface / obs operator / covariance C++ 扩展
- IODA converter pipeline

---

## 1.3 现状基线

当前 `MHE/src/metaharness_ext/` 已有：

- `metaharness_ext.nektar`
- `metaharness_ext.ai4pde`

但尚无：

- `MHE/src/metaharness_ext/jedi/`
- `MHE/tests/test_metaharness_jedi*.py`

因此本阶段是 **从零建立 JEDI 扩展骨架**，但实现方式应尽量复用现有扩展的工程约定：

- 包结构与 manifest 组织方式参考 `metaharness_ext.nektar`
- typed contracts 与 exports 组织方式参考 `metaharness_ext.nektar` / `metaharness_ext.ai4pde`
- 测试文件命名遵循 `test_metaharness_<extension>_<topic>.py`

---

## 1.4 设计决策

### 1.4.1 首版只做 Level 4 wrapper，不进入 JEDI 内核扩展

本阶段实现严格停留在：

- gateway
- environment probe
- YAML compiler
- mode-aware executor
- validator

不进入 OOPS/UFO/IODA/SABER 的 C++ 内核扩展，也不尝试 Python binding 层封装。

### 1.4.2 contracts 必须按 application family 分裂，而不是单一松散 spec

`JediExperimentSpec` 使用 discriminated union，至少覆盖：

- `JediVariationalSpec`
- `JediLocalEnsembleDASpec`
- `JediHofXSpec`
- `JediForecastSpec`

原因：

- 各 family 顶层 YAML 结构不同
- 不同 family 的 compiler 生成逻辑不同
- validate-only 错误语义也不同

### 1.4.3 executor 当前支持三种 execution mode

`executor.py` 当前阶段实现三种 execution mode：

1. `schema`
   - `<app>.x --output-json-schema=...`
2. `validate_only`
   - `<app>.x --validate-only config.yaml`
3. `real_run`
   - `<launcher> ... <app>.x config.yaml`

这样可以把当前 Phase 0 的失败尽量收敛在：

- executable 不存在
- launcher 不存在
- shared library 缺失
- testinput / data path 未就位
- YAML 结构非法

smoke baseline policy、环境选择策略与更高层 scientific acceptance 仍留到 Phase 1+。

### 1.4.4 environment probe 要先于 compiler / executor

`environment.py` 必须先于 `config_compiler.py` 和 `executor.py` 执行，至少检查：

- binary 是否存在于 PATH
- launcher 是否可用（`direct` / `mpiexec` / `mpirun` / `srun` / `jsrun`）
- 动态链接是否可解析（`ldd`）
- 所需 runtime path、workspace `testinput` 与数据路径是否存在
- 是否存在 `ctest -R get_` / `qg_get_data` / 等价数据准备前提缺失

这一步的目的不是做“最佳努力”自动修复，而是返回稳定、可审计的 `JediEnvironmentReport`，显式区分 `missing_required_paths`、`missing_data_paths` 与 `missing_prerequisites`。对于当前能够由 spec / workspace / 已引用路径直接判定的 data-prep surface，还应进一步返回 `ready_prerequisites` 与 `prerequisite_evidence`，避免只给出抽象 prerequisite 名称而不说明“哪些前提其实已就绪”。

### 1.4.5 compiler 只能生成受控 YAML，不能退化为任意 YAML 透传器

`config_compiler.py` 的输入是 typed spec，输出是受控 YAML。必须坚持：

- 只接受 contracts 中声明的字段
- 不接受任意外部 YAML 原样透传
- 不在 Phase 0 里支持无约束 patch/merge 语义
- FGAT 只能作为 `3D-Var` / `4D-Var` 内的运行语义表达，而不是额外 `cost_type`

### 1.4.6 validator 只负责判定，不承担编译或执行职责

`validator.py` 只综合：

- environment report
- run artifact
- execution mode

输出稳定的 `JediValidationReport`，至少区分：

- `environment_invalid`
- `validated`
- `executed`
- `validation_failed`
- `runtime_failed`

当前 Phase 0 不引入更高层科学判据，也不引入 richer diagnostics 组级 interpretation；但 `executed` 已经表示“runtime completed with evidence”，不等于 scientific success。

---

## 1.5 目标文件清单

### 1.5.1 新增源码文件

- `MHE/src/metaharness_ext/jedi/__init__.py`
- `MHE/src/metaharness_ext/jedi/types.py`
- `MHE/src/metaharness_ext/jedi/contracts.py`
- `MHE/src/metaharness_ext/jedi/capabilities.py`
- `MHE/src/metaharness_ext/jedi/slots.py`
- `MHE/src/metaharness_ext/jedi/gateway.py`
- `MHE/src/metaharness_ext/jedi/environment.py`
- `MHE/src/metaharness_ext/jedi/config_compiler.py`
- `MHE/src/metaharness_ext/jedi/preprocessor.py`
- `MHE/src/metaharness_ext/jedi/executor.py`
- `MHE/src/metaharness_ext/jedi/validator.py`

### 1.5.2 新增 manifest 文件

- `MHE/src/metaharness_ext/jedi/manifest.json`
- `MHE/src/metaharness_ext/jedi/environment.json`
- `MHE/src/metaharness_ext/jedi/compiler.json`
- `MHE/src/metaharness_ext/jedi/executor.json`
- `MHE/src/metaharness_ext/jedi/validator.json`

### 1.5.3 新增测试文件

- `MHE/tests/test_metaharness_jedi_manifest.py`
- `MHE/tests/test_metaharness_jedi_imports.py`
- `MHE/tests/test_metaharness_jedi_environment.py`
- `MHE/tests/test_metaharness_jedi_validate_only.py`
- `MHE/tests/test_metaharness_jedi_compiler.py`

---

## 1.6 contracts 设计

### 1.6.1 基础枚举/类型

在 `types.py` 中定义：

- `JediApplicationFamily = Literal["variational", "local_ensemble_da", "hofx", "forecast"]`
- `JediExecutionMode = Literal["schema", "validate_only", "real_run"]`
- `JediLauncher = Literal["direct", "mpiexec", "mpirun", "srun", "jsrun"]`

### 1.6.2 executable spec

在 `contracts.py` 中定义：

```python
class JediExecutableSpec(BaseModel):
    binary_name: str
    launcher: JediLauncher = "direct"
    execution_mode: JediExecutionMode = "validate_only"
    timeout_seconds: int | None = None
    process_count: int | None = None
    launcher_args: list[str] = Field(default_factory=list)
```

### 1.6.3 family-aware specs

至少定义：

- `JediCommonSpec`
- `JediVariationalSpec`
- `JediLocalEnsembleDASpec`
- `JediHofXSpec`
- `JediForecastSpec`
- `JediExperimentSpec = Annotated[..., Field(discriminator="application_family")]`

其中 `JediVariationalSpec` 的 `cost_type` 首版限定为：

```python
Literal["3D-Var", "4D-Var", "4DEnsVar", "4D-Weak"]
```

并通过独立字段或等价配置表达 FGAT 运行语义，而不是新增 `"3DFGAT"`。

### 1.6.4 环境/运行/验证 contracts

Phase 0 至少定义：

```python
class JediEnvironmentReport(BaseModel):
    binary_available: bool
    launcher_available: bool
    shared_libraries_resolved: bool
    required_paths_present: bool
    workspace_testinput_present: bool = True
    data_paths_present: bool = True
    data_prerequisites_ready: bool = True
    binary_path: str | None = None
    launcher_path: str | None = None
    workspace_root: str | None = None
    missing_required_paths: list[str] = Field(default_factory=list)
    missing_data_paths: list[str] = Field(default_factory=list)
    missing_prerequisites: list[str] = Field(default_factory=list)
    ready_prerequisites: list[str] = Field(default_factory=list)
    prerequisite_evidence: dict[str, list[str]] = Field(default_factory=dict)
    environment_prerequisites: list[str] = Field(default_factory=list)
    smoke_candidate: JediApplicationFamily | None = None
    smoke_ready: bool = False
    messages: list[str] = Field(default_factory=list)
```

```python
class JediRunPlan(BaseModel):
    task_id: str
    run_id: str
    application_family: JediApplicationFamily
    execution_mode: JediExecutionMode
    command: list[str]
    working_directory: str
    config_path: str
    schema_path: str | None = None
    expected_outputs: list[str] = Field(default_factory=list)
    expected_logs: list[str] = Field(default_factory=list)
    expected_diagnostics: list[str] = Field(default_factory=list)
    expected_references: list[str] = Field(default_factory=list)
    required_runtime_paths: list[str] = Field(default_factory=list)
    scientific_check: Literal["runtime_only", "rms_improves"] = "runtime_only"
    config_text: str
    executable: JediExecutableSpec
```

```python
class JediRunArtifact(BaseModel):
    task_id: str
    run_id: str
    application_family: JediApplicationFamily
    execution_mode: JediExecutionMode
    command: list[str]
    return_code: int | None
    config_path: str | None = None
    schema_path: str | None = None
    stdout_path: str | None = None
    stderr_path: str | None = None
    prepared_inputs: list[str] = Field(default_factory=list)
    working_directory: str
    output_files: list[str] = Field(default_factory=list)
    diagnostic_files: list[str] = Field(default_factory=list)
    reference_files: list[str] = Field(default_factory=list)
    status: JediRunStatus = "planned"
    result_summary: dict[str, Any] = Field(default_factory=dict)
```

```python
class JediValidationReport(BaseModel):
    task_id: str
    run_id: str
    passed: bool
    status: Literal[
        "environment_invalid",
        "validated",
        "executed",
        "validation_failed",
        "runtime_failed",
    ]
    messages: list[str] = Field(default_factory=list)
    summary_metrics: dict[str, float | str] = Field(default_factory=dict)
    evidence_files: list[str] = Field(default_factory=list)
```

---

## 1.7 实施步骤

## Step 1：建立包骨架与 exports

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/__init__.py`
- `MHE/src/metaharness_ext/jedi/types.py`
- `MHE/src/metaharness_ext/jedi/capabilities.py`
- `MHE/src/metaharness_ext/jedi/slots.py`

工作内容：

- 建立与 `metaharness_ext.nektar` 一致的扩展包结构
- 声明 canonical capabilities
- 声明 slots 常量
- 在 `__init__.py` 中统一导出 public API

完成标志：

- `metaharness_ext.jedi` 可被导入
- capabilities / slots / types 的最小 exports 完整

## Step 2：新增 typed contracts

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/contracts.py`

工作内容：

- 新增 executable/environment/run/validation contracts
- 新增四类 family-aware specs
- 使用 discriminated union 形成 `JediExperimentSpec`
- 为 `variational` family 约束正确的 `cost_type` 集合
- 为 observation 配置加注释或字段说明，明确标准 UFO 使用 `obs operator.name`

完成标志：

- `contracts.py` 可导入所有目标 model
- contracts 能表达 Phase 0 所需输入/输出
- 不引入 `3DFGAT` 独立 `cost_type`

## Step 3：新增 gateway

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/gateway.py`
- `MHE/src/metaharness_ext/jedi/manifest.json`

工作内容：

- 实现最小 `JediGatewayComponent`
- 接收 request 并规范化为 `JediExperimentSpec`
- 根据 `application_family` / `execution_mode` 选择执行路径
- 对接 manifest 声明

完成标志：

- gateway 可导入
- manifest entry 与 class 对齐
- tests 能验证 manifest importability

## Step 4：实现 environment probe

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/environment.py`
- `MHE/src/metaharness_ext/jedi/environment.json`

工作内容：

- 探测 binary 是否存在
- 探测 launcher 是否存在
- 探测 `ldd` 结果是否缺库
- 探测 required runtime path、workspace `testinput` 与数据路径是否存在
- 探测数据准备前提是否缺失（`ctest -R get_` / `qg_get_data` / 等价准备步骤）
- 对可直接从当前引用面判定的 prerequisite 返回 `ready` / `missing` 与 evidence path
- 生成 `JediEnvironmentReport`

完成标志：

- 能稳定区分 binary 缺失 / launcher 缺失 / library 缺失 / required path 缺失 / data prerequisite 缺失
- 不把环境失败误报成 validation failure

## Step 5：实现 config compiler

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/config_compiler.py`
- `MHE/src/metaharness_ext/jedi/compiler.json`

工作内容：

- 把 family-aware spec 编译为稳定 YAML
- 为 `variational` 生成 `cost function` / `variational` 等配置块
- 为 `local_ensemble_da` 生成 `window begin` / `window length` / `local ensemble DA` 等配置块
- 为 `hofx` / `forecast` 生成对应顶层块
- 保持 YAML 输出稳定、字段顺序可预测

完成标志：

- 相同 spec 生成稳定 YAML
- 不透传任意外部 YAML
- compiler 单测可覆盖主要 family 的最小样例

## Step 6：实现 mode-aware executor

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/executor.py`
- `MHE/src/metaharness_ext/jedi/executor.json`

工作内容：

- 根据 `execution_mode` 构造命令
- `schema` 模式：`<app>.x --output-json-schema=...`
- `validate_only` 模式：`<app>.x --validate-only config.yaml`
- `real_run` 模式：`<launcher> ... <app>.x config.yaml`，其中 launcher 当前覆盖 `direct` / `mpiexec` / `mpirun` / `srun` / `jsrun`
- 拒绝在 `launcher_args` 中重复声明 process-count 参数，统一要求使用 `executable.process_count`
- 执行前通过 preprocessor 落盘 `config.yaml` 并记录 `preprocessor_manifest.json`
- 记录 command、stdout、stderr、return code、config path 与 runtime evidence
- 生成 `JediRunArtifact`

完成标志：

- 能构造正确命令
- 能记录 stdout/stderr 路径
- 能区分 CTest 测试名与实际 executable 名
- Phase 0 已支持 `real_run`，但不把 smoke policy 与 scientific acceptance 混入 executor

## Step 7：实现 validator

修改/新增文件：

- `MHE/src/metaharness_ext/jedi/validator.py`
- `MHE/src/metaharness_ext/jedi/validator.json`

工作内容：

- 综合 environment report 与 run artifact
- 生成 `JediValidationReport`
- 以 execution mode 区分 `validated` / `validation_failed`
- 在环境缺失时返回 `environment_invalid`
- 保持消息稳定且适合 agent / CLI 消费

完成标志：

- validator 不承担编译或执行职责
- 失败语义清晰且稳定
- evidence_files 指向 YAML / stdout / stderr / schema 等可审计文件

## Step 8：补测试与回归保障

修改/新增文件：

- `MHE/tests/test_metaharness_jedi_manifest.py`
- `MHE/tests/test_metaharness_jedi_imports.py`
- `MHE/tests/test_metaharness_jedi_environment.py`
- `MHE/tests/test_metaharness_jedi_validate_only.py`
- `MHE/tests/test_metaharness_jedi_compiler.py`

工作内容：

- 验证 manifest 集合完整
- 验证 manifest entry 可导入
- 验证 contracts exports 稳定
- 验证 environment probe 的主要失败语义
- 验证 compiler 输出稳定
- 验证 validate-only / schema 命令构造正确

完成标志：

- Phase 0 相关测试通过
- 不破坏现有 `metaharness_ext.nektar` / `metaharness_ext.ai4pde` 测试

---

## 1.8 关键文件

必改：

- `MHE/src/metaharness_ext/jedi/__init__.py`
- `MHE/src/metaharness_ext/jedi/types.py`
- `MHE/src/metaharness_ext/jedi/contracts.py`
- `MHE/src/metaharness_ext/jedi/capabilities.py`
- `MHE/src/metaharness_ext/jedi/slots.py`
- `MHE/src/metaharness_ext/jedi/gateway.py`
- `MHE/src/metaharness_ext/jedi/environment.py`
- `MHE/src/metaharness_ext/jedi/config_compiler.py`
- `MHE/src/metaharness_ext/jedi/preprocessor.py`
- `MHE/src/metaharness_ext/jedi/executor.py`
- `MHE/src/metaharness_ext/jedi/validator.py`

必增：

- `MHE/src/metaharness_ext/jedi/manifest.json`
- `MHE/src/metaharness_ext/jedi/environment.json`
- `MHE/src/metaharness_ext/jedi/compiler.json`
- `MHE/src/metaharness_ext/jedi/executor.json`
- `MHE/src/metaharness_ext/jedi/validator.json`
- `MHE/tests/test_metaharness_jedi_manifest.py`
- `MHE/tests/test_metaharness_jedi_imports.py`
- `MHE/tests/test_metaharness_jedi_environment.py`
- `MHE/tests/test_metaharness_jedi_validate_only.py`
- `MHE/tests/test_metaharness_jedi_compiler.py`

参考实现：

- `MHE/src/metaharness_ext/nektar/__init__.py`
- `MHE/src/metaharness_ext/nektar/capabilities.py`
- `MHE/src/metaharness_ext/nektar/slots.py`
- `MHE/tests/test_metaharness_nektar_manifest.py`

---

## 1.9 验证

实现后按以下顺序验证：

1. `pytest MHE/tests/test_metaharness_jedi_manifest.py`
2. `pytest MHE/tests/test_metaharness_jedi_imports.py`
3. `pytest MHE/tests/test_metaharness_jedi_environment.py`
4. `pytest MHE/tests/test_metaharness_jedi_compiler.py`
5. `pytest MHE/tests/test_metaharness_jedi_validate_only.py`
6. `pytest MHE/tests/test_metaharness_jedi_minimal_demo.py`
7. `pytest MHE/tests/test_metaharness_jedi_smoke.py`
8. `ruff check MHE/src/metaharness_ext/jedi MHE/tests/test_metaharness_jedi_*.py`

验证重点：

- family-aware contracts 是否稳定
- `variational` 的 `cost_type` 集合是否准确
- `environment.py` 是否能稳定区分环境失败与配置失败
- `executor.py` 是否正确构造 `schema` / `validate-only` / `real_run` 命令，而不越权进入 smoke policy
- 是否正确使用实际 executable 名（如 `qg4DVar.x`）
- 是否不会把 `qg_4dvar_rpcg` 这类 CTest 测试名误当成 executable
- 不把 JEDI 数据准备与 `ENABLE_TESTS=ON` 强耦合

---

## 1.10 验收标准

Phase 0 PR 合并前，必须满足：

- `metaharness_ext.jedi` 包骨架、manifests、imports 完整
- 能从 typed spec 生成稳定 YAML
- 能显式报告 binary / launcher / shared libs / data path 缺失
- 能构造 `<app>.x --validate-only config.yaml`
- 能构造 `<app>.x --output-json-schema=...`
- 能构造 real-run 命令并归档 runtime evidence
- validate-only 与 real-run 都返回稳定 `JediValidationReport`
- 环境失败不会被误报为 YAML 逻辑错误
- 相关 `pytest` 与 `ruff check` 零回归

---

## 1.11 Phase 1 入口

本实施计划完成后，下一份直接衔接的实施计划应覆盖 **Phase 1: Toy Smoke Policy + Evidence Strengthening**，重点增加：

- `hofx` smoke baseline
- environment-gated baseline selection policy
- richer IODA 组级 diagnostics interpretation
- `MHE/tests/test_metaharness_jedi_smoke.py`

也就是说，Phase 0 的实现结果必须天然可复用于下一阶段，而不是做一次性脚手架。