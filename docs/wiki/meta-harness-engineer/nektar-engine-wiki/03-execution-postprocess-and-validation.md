# 03. Execution, Postprocess and Validation

## 3.1 执行器：`SolverExecutorComponent`

`SolverExecutorComponent` 位于 `MHE/src/metaharness_ext/nektar/solver_executor.py:23`，是当前实现中最接近“真实运行时边界”的组件。

它有两个鲜明特征：

- **最小依赖**：使用标准库 `subprocess` 而不是更重的作业系统
- **强证据化**：所有运行结果都变成文件与结构化 artifact

---

## 3.2 运行目录与安全边界

执行器通过 `_resolve_run_dir()` 在 `runtime.storage_path / "nektar_runs" / plan.task_id` 下创建运行目录，见 `MHE/src/metaharness_ext/nektar/solver_executor.py:198`。

在此之前会执行 `_validate_task_id()`：

- 禁止空字符串
- 禁止 `..`
- 禁止 `/` 与 `\\`

这一步是当前包里最直接的路径安全边界，防止恶意 `task_id` 把运行目录逃逸出 storage root。

---

## 3.3 solver 执行路径

标准执行流程如下：

1. 校验 `equation_type` 与 `solver_family`
2. 解析 run dir
3. 解析 mesh path
4. 写出 `session.xml`
5. 解析 solver binary
6. 构造 command
7. 用 `subprocess.run()` 执行
8. 写 `solver.stdout.log` / `solver.stderr.log` / `solver.log`
9. 搜索 `*.fld` / `*.chk`
10. 提取误差范数与步进指标
11. 返回 `NektarRunArtifact`

### 3.3.1 不可用路径

若 external mesh 模式缺失 `mesh.source_path`，执行器不会直接抛异常，而会返回 `status="unavailable"` 的 artifact，并把 `fallback_reason` 标成 `mesh_source_not_found`，见 `MHE/src/metaharness_ext/nektar/solver_executor.py:41`。

若 solver binary 找不到，也返回 `status="unavailable"`，原因是 `solver_binary_not_found`，见 `MHE/src/metaharness_ext/nektar/solver_executor.py:73`。

这说明执行器把“环境不足”视为可报告的运行状态，而不是无结构的异常。

### 3.3.2 timeout 路径

若求解超时，会：

- 仍然保存 stdout/stderr
- 尝试发现已经生成的 `.fld` / `.chk`
- 提取当时可见的误差和步进信息
- 返回 `status="failed"`
- `fallback_reason="solver_timeout"`

因此 timeout 不是完全丢失上下文的硬失败，而是“失败但保留尽量多证据”。

---

## 3.4 solver 输出指标提取

## 3.4.1 误差范数

`_extract_error_norms()` 位于 `MHE/src/metaharness_ext/nektar/solver_executor.py:321`。

它从 solver stdout/stderr 中匹配如下格式：

```text
L 2 error (variable u) : 1.11262e-05
L inf error (variable u) : 1.28659e-05
```

并生成：

- `l2_error_u`
- `linf_error_u`

此外，它显式忽略坐标变量：`x / y / z`。

这点非常重要，因为真实 Nektar / `FieldConvert -e` 输出会同时包含坐标误差；当前 validator 只把物理解变量的 L2 误差纳入容差判断。

## 3.4.2 时间与步进指标

`_extract_step_metrics()` 位于 `MHE/src/metaharness_ext/nektar/solver_executor.py:336`，目前会提取：

- `total_steps`
- `final_time`
- `cpu_time`
- `wall_time`

这使 `artifact.filter_output.metrics` 不只包含数值误差，还能承载运行轨迹摘要。

---

## 3.5 后处理器：`PostprocessComponent`

后处理组件定义在 `MHE/src/metaharness_ext/nektar/postprocess.py:17`。

### 3.5.1 总体策略

它的输入是 `NektarRunArtifact`，而不是 `NektarSessionPlan`。这说明当前系统认为：

- postprocess 属于 run artifact enrichment
- 它不改变求解本身，只补充派生文件和评估指标

### 3.5.2 输入文件选择

`_select_input_file()` 在 `MHE/src/metaharness_ext/nektar/postprocess.py:180` 的优先级是：

1. 显式 `step["input"]`
2. `artifact.field_files[0]`
3. 最新 checkpoint（按排序取最后一个）

这套规则在测试里有明确保护：优先 `.fld`，无 `.fld` 时回退 `.chk`。

### 3.5.3 `FieldConvert` 命令构造

`_build_fieldconvert_command()` 在 `MHE/src/metaharness_ext/nektar/postprocess.py:197`。当前支持三种形态：

#### 普通转换

```text
FieldConvert input output
```

#### 误差评估

```text
FieldConvert -e session.xml input error.vtu
```

注意：当前实现已经按本机 Nektar++ 5.9.0 真实行为修正为 **`-e` 仍然必须附带显式输出文件**。

#### 模块式后处理

```text
FieldConvert -m vorticity input vorticity.fld
FieldConvert -m extract:bnd=0 input boundary_b0.dat
```

### 3.5.4 多步 postprocess 计划

`postprocess_plan` 是 step list；`run_postprocess()` 会顺序执行每个 step，并把结果收集到：

```python
artifact.result_summary["postprocess"]
```

其中包含：

- `status`
- `ran_fieldconvert`
- `fallback_reason`
- `steps`

这为更上层 runtime 提供了统一的后处理摘要入口。

---

## 3.6 `FieldConvert -e` 与误差语义

当前实现区分两种误差来源：

1. **solver 输出中的误差范数**：来自 solver 本身 stdout/stderr
2. **`FieldConvert -e` 输出中的误差范数**：来自后处理阶段

这两类都走同一套 `_extract_error_norms()` 规则，因此最终都会汇总到：

```python
artifact.filter_output.error_norms
```

工程上，这带来两个好处：

- validator 不需要关心误差来自 solver 还是 `FieldConvert`
- e2e 测试可以同时覆盖两种证据来源

---

## 3.7 IncNS 收敛指标

除了通用误差范数外，`PostprocessComponent` 还会在 `run_postprocess()` 一开始执行：

```python
updated.filter_output.metrics.update(self._extract_solver_convergence_metrics(updated))
```

对应实现见 `MHE/src/metaharness_ext/nektar/postprocess.py:300`。

它目前能从 IncNS solver log 中识别：

- pressure mapping 收敛迭代数与误差
- velocity mapping 收敛迭代数与误差
- Newton iteration 次数
- `L2Norm[i]`
- `InfNorm[i]`
- 某些 `Iteration: n, Velocity L2, Pressure L2` 形式的行

这说明当前系统对 `IncNS` 的支持已经不只停留在“跑通 solver”，而是开始提取 solver-specific convergence evidence。

---

## 3.8 验证器：`NektarValidatorComponent`

验证器定义在 `MHE/src/metaharness_ext/nektar/validator.py:11`。

### 3.8.1 基本判据

`validate_run()` 的核心输入包括：

- `artifact.result_summary["exit_code"]`
- `artifact.field_files`
- `artifact.filter_output.checkpoint_files`
- `artifact.filter_output.error_norms`
- `artifact.filter_output.metrics`
- `artifact.result_summary["postprocess"]`

它将这些证据转成：

- 布尔结论
- 文字消息
- 结构化指标

### 3.8.2 `error_vs_reference`

`_evaluate_error_vs_reference()` 在 `MHE/src/metaharness_ext/nektar/validator.py:89`。

规则很简单：

- 如果没有 `error_norms`，返回 `None`
- 只收集 key 中包含 `l2` 的值
- 若没有有效 L2 值，返回 `None`
- 否则比较 `max(l2_values) <= tolerance`

默认容差来自：

```python
artifact.result_summary.get("error_tolerance", 1e-3)
```

### 3.8.3 postprocess 状态映射

validator 会把 postprocess 结果显式反映到 messages 中：

- completed -> 成功消息
- failed -> 失败原因
- skipped -> 跳过消息
- unavailable -> 环境不可用消息

因此 validator 不是只看 solver，还会把后处理的健康状况纳入最终摘要。

### 3.8.4 IncNS 指标透传

若 `artifact.filter_output.metrics` 中存在：

- `incns_velocity_iterations`
- `incns_pressure_iterations`
- `incns_newton_iterations`

validator 会：

- 把它们放进 `report.metrics`
- 附加相应的说明消息

---

## 3.9 当前实现的一个关键设计点

当前后处理与验证的实现有一个很清晰的架构选择：

- **提取逻辑尽量靠近数据源**
  - solver executor 负责提取 solver 输出指标
  - postprocess 负责提取 `FieldConvert` 与 IncNS log 指标
- **判定逻辑集中到 validator**

这让系统更容易扩展。未来若新增：

- 更多 `FieldConvert -m` 模块
- 更多 solver family 专属收敛指标
- 更复杂的 reference compare

原则上都不需要重写 validator 的整体框架，只需补充 artifact 上的数据证据即可。