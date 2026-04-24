# 03. Contracts 与产物

## 3.1 设计原则

`metaharness_ext.deepmd` 的 contracts 应坚持：

1. **family-aware**：区分 DeePMD 基础训练、DP-GEN run、DP-GEN simplify、DP-GEN autotest
2. **mode-aware**：区分 `train`、`freeze`、`compress`、`test` 等不同执行模式
3. **artifact-first**：所有重要输出都进入 typed artifact / evidence
4. **validator-friendly**：能稳定表达工程状态与科学状态，而不是只给一个 return code

---

## 3.2 DeePMD-kit typed contracts

### `DeepMDExecutionMode`

当前实现已经落地并受测试覆盖的 execution mode 为：

```python
Literal[
    "train",
    "freeze",
    "test",
    "compress",
    "model_devi",
    "neighbor_stat",
]
```

这里的 mode 仍然尽量贴近上游 DeePMD CLI，但首版 contract 只覆盖已经接入到统一 `compiler -> executor -> validator` 管线中的六种命令；`prepare_data`、`convert_from` 等更外围命令暂不纳入当前 typed surface。

### `DeepMDDatasetSpec`

字段建议：

- `dataset_id: str`
- `source_format: Literal["deepmd_npy", "deepmd_raw", "vasp_outcar", "lammps_dump", "hdf5", "other"]`
- `source_paths: list[str]`
- `type_map: list[str]`
- `train_systems: list[str]`
- `validation_systems: list[str]`
- `split_strategy: Literal["explicit", "random", "last_set_as_test"]`
- `set_size: int | None = None`
- `set_prefix: str = "set"`
- `periodic: bool = True`
- `labels_present: list[str] = Field(default_factory=list)`
- `storage_format: Literal["npy", "raw", "hdf5"] = "npy"`
- `mixed_type: bool = False`
- `conversion_required: bool = False`

首版文档还应把 DeePMD 数据目录的最小事实说清楚。典型 `deepmd/npy` 或兼容系统通常包含：

- `type.raw`
- `type_map.raw`（可选，但推荐显式存在）
- `nopbc`（非周期体系时）
- `set.*/coord.npy`
- `set.*/box.npy`
- `set.*/energy.npy`
- `set.*/force.npy`
- `set.*/virial.npy`
- `set.*/fparam.npy` / `set.*/aparam.npy`（按需出现）

因此 dataset contract 不能只表达“路径列表”，还应表达标签完整性、PBC 语义、存储格式以及系统是否满足 descriptor/runtime 约束。

### `DeepMDDescriptorSpec`

字段建议：

- `descriptor_type: Literal["se_e2_a", "se_a", "se_e2_r", "se_e3", "se_atten", "hybrid", "se_a_mask"]`
- `rcut: float`
- `rcut_smth: float`
- `sel: list[int]`
- `neuron: list[int]`
- `axis_neuron: int | None = None`
- `resnet_dt: bool = False`
- `seed: int | None = None`
- `exclude_types: list[list[int]] | None = None`
- `env_protection: float | None = None`
- `type_one_side: bool | None = None`

首版实现不需要一次性把所有 descriptor family 都做成完整 compiler，但文档应提前承认这些 family 的存在，并把 `se_e2_a` 之外的支持状态写清楚。尤其：

- `se_atten` 与 mixed-system 语义相关
- `se_a_mask` 往往带有非周期/掩码约束
- `hybrid` 是多 descriptor 组合，而不是单一字段展开

`sel` 还是一个需要实践指引的高风险参数。文档应建议用 `dp neighbor-stat` 先做邻居统计，再把 `sel` 设到高于观测最大邻居数的安全范围；过小会伤害精度与守恒，过大则提高显存与训练成本。

### `DeepMDFittingNetSpec`

字段建议：

- `neuron: list[int]`
- `resnet_dt: bool = False`
- `seed: int | None = None`
- `trainable: bool | list[bool] | None = None`

### `DeepMDModeInputSpec`

phase-two 在不新增 task family 的前提下，引入了一层轻量 mode-specific 输入：

- `model_path: str | None = None`
- `output_model_path: str | None = None`
- `system_path: str | None = None`
- `system_paths: list[str] = []`
- `sample_count: int | None = None`

当前 contract 约束为：

- `compress` 需要 `mode_inputs.model_path`，若未给定 `output_model_path`，默认补成 `compressed_model.pb`
- `model_devi` 需要 `mode_inputs.model_path` 且至少一个 system path
- `neighbor_stat` 需要至少一个 system path
- `test` 的 dataset path 优先来自 `mode_inputs.system_paths` / `mode_inputs.system_path`，否则回落到 dataset 中的 train/validation systems

### `DeepMDTrainSpec`

当前实现中的核心字段为：

- `task_id: str`
- `application_family: Literal["deepmd_train"]`
- `executable: DeepMDExecutableSpec`
- `dataset: DeepMDDatasetSpec`
- `type_map: list[str]`
- `descriptor: DeepMDDescriptorSpec`
- `fitting_net: DeepMDFittingNetSpec`
- `training: dict[str, Any]`
- `learning_rate: dict[str, Any]`
- `loss: dict[str, Any]`
- `working_directory: str | None = None`
- `mode_inputs: DeepMDModeInputSpec`

首版依然保持 `DeepMDTrainSpec` 作为唯一任务合同，不拆新的 spec family。也就是说，`train`、`freeze`、`test`、`compress`、`model_devi`、`neighbor_stat` 都通过同一个 typed task 进入 compiler，只在 `mode_inputs` 与 `execution_mode` 上做最小分流。

### `DeepMDRunPlan`

当前实现中的核心字段为：

- `task_id: str`
- `run_id: str`
- `execution_mode: DeepMDExecutionMode`
- `command: list[str]`
- `working_directory: str`
- `input_json_path: str | None`
- `expected_outputs: list[str]`
- `expected_logs: list[str]`
- `dataset_paths: list[str]`
- `input_json: dict[str, Any]`
- `executable: DeepMDExecutableSpec`
- `mode_inputs: DeepMDModeInputSpec`

当前 plan 生成语义是：

- `train` 会生成 `input_json`，并把 `input_json_path` 指向 `input.json`
- 非 `train` 模式不强制写训练 JSON，通常使用 `input_json = {}` 与 `input_json_path = None`
- `dataset_paths` 优先取 `mode_inputs.system_paths` / `mode_inputs.system_path`，再回落到 dataset 的 train/validation systems
- `expected_outputs` 会按模式变化：`frozen_model.pb`、`test.out`、`compressed_model.pb`、`model_devi.out`、`neighbor_stat.out`

### `DeepMDRunArtifact`

字段建议：

- `task_id: str`
- `run_id: str`
- `execution_mode: str`
- `command: list[str]`
- `return_code: int | None`
- `stdout_path: str | None`
- `stderr_path: str | None`
- `working_directory: str`
- `checkpoint_files: list[str]`
- `model_files: list[str]`
- `diagnostic_files: list[str]`
- `completed: bool`

### `DeepMDDiagnosticSummary`

当前实现已经落地的 summary 字段为：

- `learning_curve_path: str | None`
- `last_step: int | None`
- `rmse_e_trn: float | None`
- `rmse_f_trn: float | None`
- `test_metrics: dict[str, float]`
- `compressed_model_path: str | None`
- `model_devi_metrics: dict[str, float]`
- `neighbor_stat_metrics: dict[str, float]`
- `messages: list[str]`

其中 phase-two 新增并已接入 executor stdout / diagnostic-file 解析的字段主要是：

- `compressed_model_path`：记录 `compress` 模式识别到的压缩模型路径
- `model_devi_metrics`：承载 `model_devi` 的解析结果，例如 `max_devi_f`、`avg_devi_f`、`min_devi_f`
- `neighbor_stat_metrics`：承载 `neighbor_stat` 的解析结果，例如 `min_nbor_dist`、`max_nbor_size`，以及由 `sel = [...]` 提取出的数值槽位

因此 summary 不再只回答“RMSE 是否存在”，还要能回答：

- `compress` 是否真的产出了可交付的 `.pb` 模型
- `model_devi` 是否输出了最小可解释的偏差统计
- `neighbor_stat` 是否输出了可复用的邻居统计与 `sel` 线索
- phase-two stdout 与 `*.out` 诊断文件中的值是否已经被收敛到统一 typed summary 中

### `DeepMDValidationReport`

当前实现中的字段为：

- `task_id: str`
- `run_id: str`
- `passed: bool`
- `status: Literal[
    "environment_invalid",
    "workspace_failed",
    "trained",
    "frozen",
    "tested",
    "compressed",
    "model_devi_computed",
    "neighbor_stat_computed",
    "baseline_success",
    "simplify_success",
    "converged",
    "autotest_validated",
    "run_failed",
    "runtime_failed",
    "validation_failed",
  ]`
- `messages: list[str]`
- `summary_metrics: dict[str, float | str]`
- `evidence_files: list[str]`

这里的 validator 语义已经与当前 mode surface 对齐：

- 缺失 binary 或环境不可用时返回 `environment_invalid`
- workspace 准备失败时返回 `workspace_failed`
- 非零退出、超时或运行期失败时，DeePMD 单体命令通常返回 `runtime_failed`，而 DP-GEN `run` / `simplify` 返回 `run_failed`
- 零退出但没有足够 evidence 时返回 `validation_failed`
- `freeze` 成功状态是 `frozen`，而不是复用 `trained`
- `compress` 成功状态是 `compressed`
- `model_devi` 成功状态是 `model_devi_computed`
- `neighbor_stat` 成功状态是 `neighbor_stat_computed`
- `dpgen_run` 成功状态是 `baseline_success`
- `dpgen_simplify` 成功状态是 `simplify_success`，若 evidence 明确表明收敛则升级为 `converged`
- `dpgen_autotest` 成功状态是 `autotest_validated`

这些状态不只是“本地跑完了没有”，也是后续 policy / promotion path 的治理输入：失败态通常意味着 candidate 暂不具备 promotion readiness，成功态则只说明其具备进入统一 authority path 的资格。

`summary_metrics` 也已经承担当前实现的对外汇总职责：

- `compress` 会同步 `compressed_model_path`
- `model_devi` 会同步 `model_devi_metrics`
- `neighbor_stat` 会同步 `neighbor_stat_metrics`
- `train` / `test` 仍会继续同步 `last_step`、`rmse_e_trn`、`rmse_f_trn` 与 `test_metrics`

---

## 3.3 DP-GEN typed contracts

### `DPGenWorkflowMode`

```python
Literal["init_bulk", "init_surf", "run", "simplify", "autotest"]
```

与当前实现对齐时，文档还应明确区分 DP-GEN 的 workflow surface 与统一 executor surface：typed task family 仍可使用 `run` / `simplify` / `autotest` 表达领域语义，但真正进入 `DeepMDExecutionMode` 的执行模式已经落到 `dpgen_run`、`dpgen_simplify`、`dpgen_autotest`，从而与 DeePMD 自身的 `train` / `freeze` / `compress` / `test` / `model_devi` / `neighbor_stat` 共享一套 mode-aware validator / evidence pipeline。

### `DPGenRunSpec`

字段建议：

- `task_id: str`
- `study_id: str | None = None`
- `workflow_mode: DPGenWorkflowMode`
- `type_map: list[str]`
- `mass_map: list[float] | None = None`
- `init_data_prefix: str | None = None`
- `init_data_sys: list[str]`
- `sys_configs_prefix: str | None = None`
- `sys_configs: list[list[str]]`
- `numb_models: int = 4`
- `default_training_param: dict[str, object]`
- `model_devi: dict[str, object] | None = None`
- `labeling: dict[str, object] | None = None`
- `working_directory: str | None = None`
- `resume_allowed: bool = True`

### `DPGenMachineSpec`

字段建议：

- `task_id: str`
- `train: list[dict[str, object]]`
- `model_devi: list[dict[str, object]] | None = None`
- `fp: list[dict[str, object]] | None = None`
- `autotest: list[dict[str, object]] | None = None`

### `DPGenRunPlan`

字段建议：

- `task_id: str`
- `run_id: str`
- `workflow_mode: str`
- `command: list[str]`
- `working_directory: str`
- `param_json_path: str | None`
- `machine_json_path: str | None`
- `expected_iteration_dirs: list[str]`
- `expected_reports: list[str]`

### `DPGenIterationReport`

字段建议：

- `iteration_id: str`
- `train_models: list[str]`
- `candidate_count: int | None`
- `accurate_count: int | None`
- `failed_count: int | None`
- `fp_task_count: int | None`
- `record_stage: int | None`
- `summary_metrics: dict[str, float | int | str]`
- `messages: list[str]`

### `DPGenRunArtifact`

字段建议：

- `task_id: str`
- `run_id: str`
- `workflow_mode: str`
- `command: list[str]`
- `return_code: int | None`
- `stdout_path: str | None`
- `stderr_path: str | None`
- `dpgen_log_path: str | None`
- `record_dpgen_path: str | None`
- `iteration_dirs: list[str]`
- `report_files: list[str]`
- `completed: bool`

### `DPGenValidationReport`

字段建议：

- `task_id: str`
- `run_id: str`
- `passed: bool`
- `status: Literal[
    "environment_invalid",
    "workspace_invalid",
    "iteration_incomplete",
    "run_completed",
    "converged",
    "runtime_failed",
    "validation_failed",
    "scientific_check_failed",
  ]`
- `messages: list[str]`
- `summary_metrics: dict[str, float | int | str]`
- `evidence_files: list[str]`

---

## 3.4 Environment report

### `DeepMDEnvironmentReport`

字段建议：

- `dp_available: bool`
- `dpgen_available: bool`
- `dpdata_available: bool`
- `python_available: bool`
- `mpi_available: bool`
- `lammps_available: bool`
- `required_paths_present: bool`
- `remote_backend_ready: bool | None = None`
- `scheduler_ready: bool | None = None`
- `messages: list[str]`

首版文档中这个对象不应只停留在概念层，因为环境失败是 DeepMD / DP-GEN 接入时最高频、也最容易被误判的问题来源之一。

---

## 3.5 Evidence bundle

### `DeepMDEvidenceBundle`

字段建议：

- `bundle_id: str`
- `task_id: str`
- `graph_version_id: str`
- `workflow_family: Literal["deepmd", "dpgen_run", "dpgen_simplify", "dpgen_autotest"]`
- `config_refs: list[str]`
- `artifact_refs: list[str]`
- `diagnostic_refs: list[str]`
- `validation_summary: dict[str, object]`
- `provenance_refs: list[str]`
- `budget_refs: list[str]`
- `reference_compare_refs: list[str] | None = None`

artifact provenance 最好还能回答“哪个命令产生了什么”：

- `dp train` -> `model.ckpt*`、`checkpoint`、`lcurve.out`、训练日志
- `dp freeze` -> `graph.pb` 或等价 frozen model
- `dp compress` -> `graph-compress.pb` 或等价 compressed model
- `dp test` -> RMSE 摘要与可选 detail outputs
- `dp model-devi` / `dpgen run` -> `model_devi.out`、candidate/accurate/failed 证据

当前实现还要求 evidence bundle 能表达 completeness 与 downstream governance 线索，而不只是 artifact refs：

- validation 是否已附着到 evidence bundle
- DP-GEN `run` / `simplify` 是否带有 iteration collection；缺失时应形成 warning / defer 线索
- `autotest` 是否带有结构化 property results；缺失时不应伪装成“已验证”
- 是否出现 relabeling / transfer-learning 线索，需要作为风险提示保留下来
- 后续需要映射到的 session / audit / provenance refs 预期形状，例如 candidate id、graph version、session event linkage、policy decision refs

否则 evidence bundle 很容易只剩“文件存在性列表”，而失去可解释性，也难以支撑治理路径消费。

---

## 3.6 验证边界

### 3.6.1 最小工程证据

当前 DeePMD 首版至少检查：

- binary / Python env / launcher 是否存在
- required dataset / model path 是否存在并能进入命令构造
- `train` 是否生成 checkpoint 或 `lcurve.out`
- `freeze` / `compress` 是否生成 `.pb` 模型文件
- `model_devi` / `neighbor_stat` 是否生成最小诊断 evidence（stdout 或 `*.out`）

### 3.6.2 最小科学证据

当前 DeePMD 首版至少支持：

- `lcurve.out` 是否能提供最小训练收敛线索
- `dp test` 是否产生 parseable RMSE metrics
- `dp model_devi` 是否能解析最小偏差统计，如 `max_devi_f`、`avg_devi_f`、`min_devi_f`
- `dp neighbor_stat` 是否能解析最小邻居统计，如 `min_nbor_dist`、`max_nbor_size` 与 `sel`
- 当 workflow 提供必要信息时，validator 能返回 mode-specific 成功状态，而不仅是 `return_code == 0`

### 3.6.3 工程通过、科学通过与 promotion-ready 的边界

这里至少要区分四层边界：

- **工程通过**：命令运行、workspace 布局、必要 artifact 与日志存在
- **科学通过**：训练、偏差或性质结果提供了最小可解释判据，如 RMSE、`model_devi` 指标、autotest property summary
- **promotion-ready**：validation 与 evidence 已足够完整，可以进入统一 promotion / policy authority path 审核
- **policy-defer**：运行或验证未必失败，但 evidence completeness、session/provenance linkage、iteration detail、property detail 等仍不足，因而只能延后而不能直接晋升

这四层边界不应被压扁成一个布尔结果。DeepMD validator 的职责是把这些边界信号表达清楚，而不是绕开 runtime governance 直接做 graph 级裁决。

### 3.6.4 不应延后的领域判据

以下判据不应全都推迟到“高级 diagnostics phase”：

- DeePMD train 是否真实产生 checkpoint 与 learning curve
- DeePMD test 是否真实输出 RMSE
- DP-GEN 是否真的进入 `00.train -> 01.model_devi -> 02.fp`
- DP-GEN 是否已经没有新增 candidate，或 candidate 量显著下降
- simplify 是否已经停止选点

---

## 3.7 study / mutation：当前实现与后续约束

当前 DeepMD 扩展已经有最小 study baseline：

- `DeepMDStudySpec` / `DeepMDStudyReport` / `DeepMDStudyTrial` 已存在
- mutation 仅允许作用于白名单 typed axis，如 `numb_steps`、`rcut`、`sel`、`model_devi_f_trust_lo`、`model_devi_f_trust_hi`、`relabeling.pick_number`
- 每个 trial 会串联 compiler -> executor -> validator -> evidence bundle -> policy evaluation
- study report 会给出推荐值、推荐 trial 与最小理由

后续 study / mutation 仍必须遵守：

- 只允许对白名单 typed fields 做 mutation
- 不直接在生成后的 JSON 文本上做 patch
- 不直接绕过 `machine.json` 资源与安全边界
- 对高成本 relabeling / HPC 提交要显式进入 policy gate
- 后续还应继续向 strengthened MHE 对齐 `ScoredEvidence` 与 `BrainProvider` seam，但这部分目前仍属于待补齐项，而不是现有 contracts 已完成的能力

建议的首批参数轴：

- DeePMD：`sel`、`rcut`、network width、`numb_steps`
- DP-GEN：`model_devi_f_trust_lo`、`model_devi_f_trust_hi`、温压计划、`fp_task_max`
- simplify：relabeling pick number、冻结层级、trainable mask

---

## 3.8 结论

`metaharness_ext.deepmd` 的 contracts 重点不在“表达全部 DeepModeling 细节”，而在：

- 稳定首版边界
- 固化执行语义
- 固化证据与验证面
- 为后续参数研究与受控演化提供 typed substrate

因此 contracts 设计应优先服务于：**compiler、executor、collector、validator、evidence** 五类核心环节。
