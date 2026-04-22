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

```python
Literal[
    "prepare_data",
    "train",
    "freeze",
    "compress",
    "test",
    "model_devi",
    "neighbor_stat",
    "convert_from",
]
```

这里的 mode 设计应尽量贴近上游实际 CLI，而不是抽象成过粗的 `apply`。对于部署与推理路径，建议在 artifact / evidence 层再区分 Python、C/C++、LAMMPS 等不同消费语义。

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

### `DeepMDTrainSpec`

字段建议：

- `task_id: str`
- `study_id: str | None = None`
- `execution_mode: DeepMDExecutionMode`
- `dataset: DeepMDDatasetSpec`
- `type_map: list[str]`
- `descriptor: DeepMDDescriptorSpec`
- `fitting_net: DeepMDFittingNetSpec`
- `learning_rate: dict[str, object]`
- `loss: dict[str, object]`
- `training: dict[str, object]`
- `working_directory: str | None = None`
- `restart_from: str | None = None`
- `init_model_path: str | None = None`
- `init_frozen_model_path: str | None = None`
- `finetune_from: str | None = None`
- `frozen_model_path: str | None = None`
- `compressed_model_path: str | None = None`

这里应显式区分几类初始化/恢复语义，因为它们直接影响 validator 和 workspace 恢复边界：

- `--init-model`
- `--restart`
- `--init-frz-model`
- finetune / transfer-learning

如果 contract 不把这些路径单独表达，后续很容易把“冷启动训练”“断点恢复”“冻结模型继续训练”混成同一种 run。

### `DeepMDRunPlan`

字段建议：

- `task_id: str`
- `run_id: str`
- `execution_mode: str`
- `command: list[str]`
- `working_directory: str`
- `input_json_path: str | None`
- `expected_outputs: list[str]`
- `expected_logs: list[str]`
- `dataset_paths: list[str]`

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

字段建议：

- `learning_curve_path: str | None`
- `last_step: int | None`
- `rmse_val: float | None`
- `rmse_trn: float | None`
- `rmse_e_val: float | None`
- `rmse_e_trn: float | None`
- `rmse_f_val: float | None`
- `rmse_f_trn: float | None`
- `learning_rate_final: float | None`
- `checkpoint_count: int | None`
- `frozen_model_path: str | None`
- `compressed_model_path: str | None`
- `neighbor_stat_summary: dict[str, float | int] | None`
- `test_metrics: dict[str, float]`
- `test_detail_files: list[str]`
- `training_env_summary: dict[str, str]`
- `messages: list[str]`

除了“RMSE 是否存在”，summary 还应能回答：

- 训练是否真的持续保存 checkpoint
- `freeze` / `compress` 是否真正产出了可交付模型
- `neighbor-stat` 是否给出了可复用的 `sel` 依据
- `dp test -d <prefix>` 一类细节文件是否可追踪
- 当前训练环境、版本与 launcher 线索是否可审计

### `DeepMDValidationReport`

字段建议：

- `task_id: str`
- `run_id: str`
- `passed: bool`
- `status: Literal[
    "environment_invalid",
    "input_invalid",
    "prepared",
    "trained",
    "frozen",
    "compressed",
    "tested",
    "runtime_failed",
    "validation_failed",
    "scientific_check_failed",
  ]`
- `messages: list[str]`
- `summary_metrics: dict[str, float | str]`
- `evidence_files: list[str]`

---

## 3.3 DP-GEN typed contracts

### `DPGenWorkflowMode`

```python
Literal["init_bulk", "init_surf", "run", "simplify", "autotest"]
```

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

否则 evidence bundle 很容易只剩“文件存在性列表”，而失去可解释性。

---

## 3.6 验证边界

### 3.6.1 最小工程证据

首版至少应检查：

- binary / Python env / launcher 是否存在
- required config / dataset / model paths 是否存在
- 关键目录结构是否建立
- checkpoint / frozen / compressed model 是否生成
- `record.dpgen` 与 iteration 目录是否一致

### 3.6.2 最小科学证据

首版至少应支持：

- `lcurve.out` 是否显示 loss 有界且可解析
- `dp test` 是否产生 energy / force / virial RMSE
- `model_devi.out` 是否可解析 candidate / accurate / failed 分布
- autotest 是否产出最小性质报告
- 当 workflow 提供必要信息时，validator 能返回最小科学结论，而不仅是 `return_code == 0`

### 3.6.3 不应延后的领域判据

以下判据不应全都推迟到“高级 diagnostics phase”：

- DeePMD train 是否真实产生 checkpoint 与 learning curve
- DeePMD test 是否真实输出 RMSE
- DP-GEN 是否真的进入 `00.train -> 01.model_devi -> 02.fp`
- DP-GEN 是否已经没有新增 candidate，或 candidate 量显著下降
- simplify 是否已经停止选点

---

## 3.7 未来 mutation / study 约束

后续 study / mutation 必须遵守：

- 只允许对白名单 typed fields 做 mutation
- 不直接在生成后的 JSON 文本上做 patch
- 不直接绕过 `machine.json` 资源与安全边界
- 对高成本 relabeling / HPC 提交要显式进入 policy gate

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
