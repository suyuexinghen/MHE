# 03. Contracts 与产物

## 3.1 设计原则

`metaharness_ext.abacus` 的 contracts 当前应坚持：

1. **family-aware**：区分 `scf`、`nscf`、`relax`、`md`
2. **file-aware**：显式表达 `INPUT` / `STRU` / `KPT` 与相关资产
3. **artifact-aware**：运行后的证据不止是 return code，而是 `OUT.<suffix>/` 与 family-aware 文件集
4. **governance-aware**：validation 结果要能自然接入更上层治理路径

---

## 3.2 基础 literals

当前代码中的 canonical literals 为：

```python
AbacusApplicationFamily = Literal["scf", "nscf", "relax", "md"]
AbacusBasisType = Literal["pw", "lcao"]
AbacusLauncher = Literal["direct", "mpirun", "mpiexec", "srun"]
AbacusESolverType = Literal["ksdft", "dp"]
AbacusValidationStatus = Literal[
    "environment_invalid",
    "input_invalid",
    "runtime_failed",
    "validation_failed",
    "executed",
]
```

这些 literal 是 contracts、environment、executor 与 validator 的共同命名主轴。

---

## 3.3 核心 task specs

当前 family-specific specs 为：

- `AbacusScfSpec`
- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- `AbacusMdSpec`

它们共享的关键字段包括：

- `task_id`
- `application_family`
- `executable`
- `structure`
- `kpoints`
- `basis_type`
- `esolver_type`
- `calculation`
- `suffix`
- `params`
- `pseudo_files`
- `orbital_files`
- `pot_file`
- `required_paths`
- `working_directory`

统一入口类型是：

```python
AbacusExperimentSpec = AbacusScfSpec | AbacusNscfSpec | AbacusRelaxSpec | AbacusMdSpec
```

---

## 3.4 当前关键约束

### `AbacusExecutableSpec`

当前 `AbacusExecutableSpec` 负责：

- `binary_name`
- `launcher`
- `timeout_seconds`
- `process_count`
- `launcher_args`

它已经开始把 launcher contract 从松散 shell 参数中收出来。

### family-specific constraints

当前代码里几个重要限制是：

- `basis_type=lcao` 时，`scf` / `nscf` / `relax` 需要 `orbital_files`
- `md` 不支持 `basis_type=lcao`
- `scf` / `nscf` / `relax` 不支持 `esolver_type=dp`
- `md + esolver_type=dp` 必须提供 `pot_file`
- `nscf` 必须提供 `charge_density_path` 或 `restart_file_path`

这些限制属于当前真实 typed boundary，不应被写成“未来可选建议”。

---

## 3.5 环境、计划与运行产物

### `AbacusEnvironmentReport`

当前 environment report 已经是较强的结构化对象，包含：

- `abacus_available` / `abacus_path`
- `version_probe_supported` / `version_probe_succeeded` / `version_output`
- `info_probe_supported` / `info_probe_succeeded` / `info_output`
- `check_input_probe_supported` / `check_input_probe_succeeded` / `check_input_output`
- `requested_launcher` / `launcher_available` / `launcher_path`
- `deeppmd_support_detected` / `gpu_support_detected`
- `required_paths_present` / `missing_required_paths`
- `environment_prerequisites` / `missing_prerequisites`
- `messages` / `evidence_refs`

### `AbacusRunPlan`

当前 run plan 已经承载：

- `task_id` / `run_id`
- `application_family`
- `command`
- `working_directory`
- `input_content` / `structure_content` / `kpoints_content`
- `suffix` / `esolver_type` / `pot_file`
- `environment_prerequisites` / `environment_evidence_refs`
- `output_root`
- `expected_outputs` / `expected_logs`
- `required_runtime_paths`
- `executable`

### `AbacusRunArtifact`

当前 run artifact 已经承载：

- `task_id` / `run_id`
- `application_family`
- `command`
- `return_code`
- `stdout_path` / `stderr_path`
- `prepared_inputs`
- `output_root`
- `output_files`
- `diagnostic_files`
- `structure_files`
- `evidence_refs`
- `working_directory`
- `status`
- `result_summary`

这说明 ABACUS artifact 已经不仅是日志引用，而是当前治理 handoff 的上游输入。

---

## 3.6 validation contract

当前 `AbacusValidationReport` 已经包含：

- `passed`
- `status`
- `messages`
- `summary_metrics`
- `evidence_files`
- `evidence_refs`
- `missing_evidence`
- `issues`
- `blocks_promotion`
- `governance_state`
- `scored_evidence`

这比早期只表达 pass/fail 的 report 更接近 governance-grade validation surface。

它当前不只回答“是否执行成功”，还要回答：

- 问题属于 environment、input、runtime 还是 validation boundary
- 当前结果是否足以形成 promotion blocker
- 证据是否完整到足以进入更高层 review

---

## 3.7 证据面

ABACUS extension 的 evidence-first 原则应理解为：

- `stdout` / `stderr` 只是辅证
- `OUT.<suffix>/` 是主证据面
- `prepared_inputs` 与 effective input snapshot 是输入侧证据
- family-specific 结构产物与 restart 产物是成功判据的重要部分
- `evidence_refs` 是后续 runtime evidence flow 的桥接位

因此 ABACUS contracts 的重点，不在于枚举全部 ABACUS 参数，而在于稳定输出可审计、可解释、可被治理路径消费的证据形状。

---

## 3.8 当前 contracts 的边界

虽然 ABACUS contracts 已经比早期设计更接近治理语义，但 extension 仍在开发中，仍有继续补齐的空间，例如：

- 更丰富的 evidence interpretation
- 更正式的 policy seam
- 更系统的 example / study / audit linkage

这些是继续开发与对齐的重点，不是否定现有 contracts 的理由。

---

## 3.9 结论

ABACUS contracts 的核心价值，在于：

- 固定 family / launcher / solver naming
- 固定 INPUT/STRU/KPT 与 asset boundary
- 固定 environment / run / validation / evidence shape
- 为更上层 runtime governance 提供稳定接口

这样即使扩展仍在开发阶段，设计边界也不会漂移。
