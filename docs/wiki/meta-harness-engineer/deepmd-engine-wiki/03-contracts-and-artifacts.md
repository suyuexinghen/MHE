# 03. Contracts 与产物

## 3.1 设计原则

`metaharness_ext.deepmd` 的 contracts 当前应坚持：

1. **family-aware**：区分 `deepmd_train`、`dpgen_run`、`dpgen_simplify`、`dpgen_autotest`
2. **mode-aware**：区分 DeePMD 与 DP-GEN 的不同 execution mode
3. **artifact-first**：重要输出进入 typed artifact / evidence surface
4. **validator-friendly**：稳定表达成功态、失败态与 summary metrics
5. **study-safe**：mutation 只作用于白名单 typed fields

---

## 3.2 family 与 mode literals

当前代码中的 canonical literals 为：

### `DeepMDApplicationFamily`

```python
Literal["deepmd_train", "dpgen_run", "dpgen_simplify", "dpgen_autotest"]
```

### `DeepMDExecutionMode`

```python
Literal[
    "train",
    "freeze",
    "test",
    "compress",
    "model_devi",
    "neighbor_stat",
    "dpgen_run",
    "dpgen_simplify",
    "dpgen_autotest",
]
```

### `DeepMDRunStatus`

```python
Literal["planned", "completed", "failed", "unavailable"]
```

这三个 literal 是整个扩展的命名主轴：gateway、compiler、executor、validator、evidence 和 study 都应围绕它们组织，而不是再引入第二套并行命名系统。

---

## 3.3 核心 task specs

### `DeepMDTrainSpec`

`DeepMDTrainSpec` 是 DeePMD family 的核心 spec，当前关键字段包括：

- `task_id`
- `application_family`
- `executable`
- `dataset`
- `type_map`
- `descriptor`
- `fitting_net`
- `training`
- `learning_rate`
- `loss`
- `working_directory`
- `mode_inputs`

当前约束里几个重要事实是：

- `dataset.source_format` 当前只支持 `deepmd_npy`
- `descriptor.descriptor_type` 当前只支持 `se_e2_a`
- `descriptor.rcut_smth` 必须满足 `0 < rcut_smth <= rcut`
- `sel` 与 `fitting_net.neuron` 不能为空
- `compress`、`test`、`model_devi`、`neighbor_stat` 对 `mode_inputs` 有不同必需条件

### `DPGenRunSpec` / `DPGenSimplifySpec` / `DPGenAutotestSpec`

DP-GEN family 当前分别通过三种 spec 表达：

- `DPGenRunSpec`
- `DPGenSimplifySpec`
- `DPGenAutotestSpec`

它们共享的结构特征包括：

- `task_id`
- `application_family`
- `executable`
- `param`
- `machine`
- `working_directory`
- `workspace_files`
- `workspace_inline_files`

其中：

- `DPGenSimplifySpec` 额外包含 `training_init_model`、`trainable_mask`、`relabeling`
- `DPGenAutotestSpec` 额外包含 `properties`

### `DeepMDExperimentSpec`

当前统一入口类型是：

```python
DeepMDTrainSpec | DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec
```

也就是说，environment probe 与若干上层逻辑已经是 family-aware 的，而不是只接受单一 DeePMD train spec。

---

## 3.4 运行计划与运行产物

### `DeepMDRunPlan`

`DeepMDRunPlan` 当前承载：

- `task_id` / `run_id`
- `application_family` / `execution_mode`
- `command`
- `working_directory`
- `input_json_path` / `param_json_path` / `machine_json_path`
- `expected_outputs` / `expected_diagnostics` / `expected_logs`
- `dataset_paths`
- `input_json` / `param_json` / `machine_json`
- `workspace_sources` / `workspace_inline_files`
- `executable` / `mode_inputs` / `properties`

它的意义不只是“准备一条命令”，而是把一次运行前的关键语义固定下来。

### `DeepMDRunArtifact`

`DeepMDRunArtifact` 当前承载：

- `task_id` / `run_id`
- `application_family` / `execution_mode`
- `command`
- `return_code`
- `stdout_path` / `stderr_path`
- `working_directory`
- `workspace_files`
- `checkpoint_files`
- `model_files`
- `diagnostic_files`
- `summary`
- `status`
- `result_summary`

这意味着 run artifact 已经不仅是日志引用；它同时承担 working directory、artifact grouping 与 command provenance 的角色。

---

## 3.5 diagnostics 与 iteration contracts

### `DeepMDDiagnosticSummary`

当前 summary 已经稳定包含：

- learning curve 线索：`learning_curve_path`、`last_step`、`rmse_e_trn`、`rmse_f_trn`、`rmse_e_val`、`rmse_f_val`
- structured metrics：`lcurve_metrics`、`test_metrics`、`model_devi_metrics`、`neighbor_stat_metrics`
- DP-GEN / autotest 线索：`dpgen_collection`、`autotest_properties`
- 其他运行线索：`train_log_path`、`compressed_model_path`、`log_clues`、`messages`

### `DPGenIterationCollection`

DP-GEN 相关的 iteration evidence 当前通过：

- `DPGenIterationSummary`
- `DPGenIterationCollection`

来表达。它们让 DP-GEN family 可以稳定暴露：

- `record.dpgen`
- `iter.*` 结构
- candidate / accurate / failed 计数
- 迭代级 messages

因此 DP-GEN 路径并不是“dpgen 命令跑完就算成功”，而是有独立的 iteration evidence contract。

---

## 3.6 validation、evidence 与 policy contracts

### `DeepMDValidationReport`

当前 canonical status surface 为：

```python
Literal[
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
]
```

这组状态的意义是：

- failure taxonomy 不只回答“有没有报错”
- success taxonomy 不把所有成功都压成单一 `passed = true`
- DeePMD 与 DP-GEN family 可以共享一套 mode-aware validation surface

### `DeepMDEvidenceBundle`

当前 evidence bundle 的字段为：

- `task_id`
- `run_id`
- `application_family`
- `execution_mode`
- `run`
- `validation`
- `summary`
- `evidence_files`
- `warnings`
- `metadata`

当前 metadata 主要稳定携带：

- `status`
- `return_code`
- `validation_status`

### `DeepMDPolicyReport`

当前 policy report 的字段为：

- `passed`
- `decision`
- `reason`
- `warnings`
- `gates`
- `evidence`

当前 decision surface 固定为：

- `allow`
- `defer`
- `reject`

---

## 3.7 study contracts

### `DeepMDMutationAxis`

当前白名单 mutation 轴为：

```python
Literal[
    "numb_steps",
    "rcut",
    "rcut_smth",
    "sel",
    "model_devi_f_trust_lo",
    "model_devi_f_trust_hi",
    "relabeling.pick_number",
]
```

### `DeepMDStudySpec`

当前 study 输入为：

- `study_id`
- `task_id`
- `base_task`
- `axis`
- `metric_key`
- `goal`

其中 `base_task` 当前只接受：

- `DeepMDTrainSpec`
- `DPGenRunSpec`
- `DPGenSimplifySpec`

### `DeepMDStudyTrial` / `DeepMDStudyReport`

study 结果当前已不只是 metric 表，而是同时保留：

- `run`
- `validation`
- `evidence_bundle`
- `policy_report`
- `metric_value`
- `passed`
- `recommended_value`
- `recommended_trial_id`
- `recommended_reason`

这使 study 成为 typed、evidence-bearing 的研究入口，而不是独立于治理边界之外的实验脚本。

---

## 3.8 当前 contracts 的边界

当前 DeepMD contracts 已经形成完整的 extension-local baseline，但仍有几类上层接缝尚未由它们直接承载：

- 更正式的 `ScoredEvidence` 统一形状
- candidate / graph version / session event 的直接引用面
- 更完整的 provenance refs
- runtime-level `ValidationIssue.blocks_promotion` 映射

这些是后续与 strengthened MHE 对齐的重点，不是否定当前 contracts 的理由。

---

## 3.9 结论

DeepMD contracts 的核心价值，不在于覆盖全部 DeepModeling 细节，而在于：

- 固定 family / mode naming
- 固定 compiler / run / validation / evidence 形状
- 固定 failure taxonomy
- 固定 study 的 typed mutation 边界

这样 compiler、executor、validator、policy 和后续 runtime authority 才能共享同一套稳定语义。
