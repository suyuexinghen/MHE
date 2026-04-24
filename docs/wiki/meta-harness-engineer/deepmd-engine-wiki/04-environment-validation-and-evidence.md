# 04. 环境、验证与证据

## 4.1 为什么 environment probe 是正式组件

DeepMD / DP-GEN 路径的早期失败，很多并不是配置逻辑错误，而是环境前提没有满足：

- binary 不存在
- Python runtime 不可用
- dataset 或 workspace 输入缺失
- `machine.local_root` 不是目录
- 非本地 context 却没有 `machine.remote_root`
- 非 shell batch 却没有 `machine.command`
- 配置了 `machine.python_path` 但解释器不存在

如果没有独立 environment probe，这些问题就会在 executor 或 validator 阶段表现成模糊失败，破坏 failure taxonomy。

---

## 4.2 当前 `DeepMDEnvironmentReport`

当前 environment report 字段为：

- `application_family`
- `execution_mode`
- `dp_available`
- `python_available`
- `required_paths_present`
- `workspace_ready`
- `machine_root_ready`
- `remote_root_configured`
- `scheduler_command_configured`
- `missing_required_paths`
- `environment_prerequisites`
- `missing_prerequisites`
- `messages`

它当前回答的不是“环境是否完美”，而是：

- 本次 family / mode 所需的前提是否具备
- 缺的是路径、Python、machine root，还是 remote / scheduler 配置
- 这些问题应被归到 environment boundary，而不是运行逻辑本身

---

## 4.3 family-aware prerequisite 语义

环境检查不是静态清单，而是 family-aware 的：

### `deepmd_train`

当前主要检查：

- `dp` binary
- Python runtime
- `dataset.train_systems` / `dataset.validation_systems` 引用路径

### `dpgen_run` / `dpgen_simplify` / `dpgen_autotest`

除了 binary 和 Python，还会额外检查：

- `workspace_files`
- `machine.local_root`
- `machine.remote_root`（当 `context_type != "local"`）
- `machine.command`（当 `batch_type != "shell"`）
- `machine.python_path`（若显式配置）

因此 environment probe 的目标不是“多做检查”，而是**按当前 family 解释缺口**。

---

## 4.4 failure source map

参考外部 deepmd-kit troubleshooting material，DeepMD 扩展当前更适合把失败来源归为以下几类，而不是只按 stderr 文本解释：

- **toolchain / build 类**：binary 缺失、Python 不可用、backend 依赖不齐
- **workspace / path 类**：dataset、workspace files、local root、remote root 缺失或形状错误
- **backend / model compatibility 类**：模型文件格式、backend 选择、版本兼容或导出产物不匹配
- **runtime resource 类**：scheduler command 缺失、远程环境未配置、运行中断
- **scientific evidence 类**：命令跑完但缺少 learning curve、RMSE、iteration details 或 property results

MHE 当前不会把这些上游问题逐一展开成产品手册式的修复教程，但 validator 与 evidence 语义应该能稳定表达这些来源类别。

---

## 4.5 canonical failure taxonomy

当前 validator 的 canonical status surface 至少包括：

- `environment_invalid`
- `workspace_failed`
- `trained`
- `frozen`
- `tested`
- `compressed`
- `model_devi_computed`
- `neighbor_stat_computed`
- `baseline_success`
- `simplify_success`
- `converged`
- `autotest_validated`
- `run_failed`
- `runtime_failed`
- `validation_failed`

这组状态的价值在于：

- `environment_invalid` 表示 extension 不应把问题归给运行结果
- `workspace_failed` 表示目录 / 输入准备已经破坏执行前提
- `run_failed` / `runtime_failed` 表示执行期失败，但 family 语义不同
- `validation_failed` 表示命令可能退出成功，但 evidence 不足以支持当前 mode 的最小判定
- 成功态保持 mode-aware 语义，不把所有成功压成同一类

---

## 4.5 evidence-first surface

当前 evidence seam 的第一层是 `build_evidence_bundle(...)`。

它当前会收集：

- `validation.evidence_files`
- `run.workspace_files`
- `run.checkpoint_files`
- `run.model_files`
- `run.diagnostic_files`

并生成：

- `evidence_files`
- `warnings`
- `metadata`

其中 metadata 当前稳定携带：

- `status`
- `return_code`
- `validation_status`

这说明 evidence bundle 现在的职责不是“文件打包”，而是把 run artifact 和 validation 统一成 downstream-ready 的证据面。

---

## 4.6 当前 warnings 语义

`build_evidence_bundle(...)` 当前会显式生成几类 warning：

- `stdout_missing`
- `stderr_missing`
- `dpgen_iteration_evidence_missing`
- `autotest_properties_missing`

这些 warning 的意义不是补充说明，而是直接参与后续 policy 解释。

例如：

- `dpgen_run` / `dpgen_simplify` 缺 iteration collection，不应被视为完整 evidence
- `dpgen_autotest` 没有结构化 property results，不应伪装成“已经验证性质”

---

## 4.7 `DeepMDEvidencePolicy.evaluate(...)`

当前 policy seam 的第二层是 `DeepMDEvidencePolicy.evaluate(...)`。

它当前遵循的决策逻辑是：

### 直接 `reject`

当 validation status 属于以下失败态时：

- `environment_invalid`
- `workspace_failed`
- `run_failed`
- `runtime_failed`
- `validation_failed`

### `defer`

当 evidence 不完整时，例如：

- 缺失 stdout / stderr
- DP-GEN family 缺 iteration details
- autotest family 缺 structured property results
- evidence bundle 没有 attached validation

### `allow`

当 validation 成功且 evidence 足够完整时。

因此 policy seam 当前回答的是：**这份 evidence 是否完整到足以交给下游 review / promotion path**。

---

## 4.8 warnings 与 gate 语义

除了 `allow` / `defer` / `reject`，当前 policy 还会保留额外 warning 线索：

- `simplify_not_converged`
- `relabeling_detected`

这说明 DP-GEN simplify 的“成功”并不自动等价于“已收敛”；同时 relabeling 也被当作应保留的风险线索，而不是被流程吞掉。

---

## 4.9 与 runtime governance 的接缝

DeepMD 扩展当前还没有直接承载完整 session / provenance / scored-evidence 子系统，但它已经在为这些上层路径准备稳定输入：

- validation status 提供 promotion-aware 分类入口
- evidence bundle 保留 warnings 与 metadata
- policy report 给出 `allow` / `defer` / `reject`
- run artifact 保留 working directory、command、stdout / stderr 与 artifact groups

后续要对齐的是更上层 authority path，而不是回退到“只看 return code”。

---

## 4.10 mode-to-artifact 设计提醒

结合上游 workflow 语义与当前扩展代码，DeepMD family 的 mode 与证据面应这样理解：

- `train`：关注 checkpoint、`lcurve.out`、训练 RMSE
- `freeze` / `compress`：关注 model artifacts，而不是训练曲线
- `test`：关注 parseable test metrics
- `model_devi`：关注 deviation diagnostics，而不是模型导出
- `neighbor_stat`：关注邻居统计与 `sel` 线索
- `dpgen_run` / `dpgen_simplify`：关注 `record.dpgen` 与 `iter.*` evidence
- `dpgen_autotest`：关注 structured property results

这也是为什么 validator 不应只返回一个统一成功态，而要保留 mode-aware statuses。

---

## 4.11 结论

DeepMD 的环境、验证与证据设计主张应是：

- 先把环境失败从运行失败中分离
- 再把运行结果整理成 mode-aware validation
- 再把 artifacts、warnings 与 completeness 聚合成 evidence bundle
- 最后由 policy seam 给出 downstream-ready 的 review 决策

这样 failure taxonomy、evidence completeness 与 promotion path 才能保持清晰边界。
