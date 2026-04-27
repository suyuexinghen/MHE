# 03. Nektar PDE Benchmark 测试方法报告

## 3.1 目标

本文具体展开方向 B：如何使用 Nektar++ 原生 PDE solver tests，测试 direct Claude CLI、deterministic `metaharness_ext.nektar` pipeline baseline，以及 Claude CLI brain + Nektar extension pipeline 的差异。

测试目标不是评估 Nektar++ solver 本身的数值精度；Nektar++ 已通过自身 regression test suite 保证这些 solver 行为。这里评估的是三种 workflow 在相同 Nektar PDE 任务上的表现：

1. **Extension pipeline baseline**：不调用 LLM，直接用 `metaharness_ext.nektar` 执行 reference case，验证确定性 extension pipeline 能力。
2. **Direct Claude CLI lane**：Claude CLI 直接复制或修改 Nektar++ session XML，调用 `ADRSolver` / `IncNavierStokesSolver` / `CompressibleFlowSolver`，手动解析 stdout 中的 `L 2 error` / `L inf error` 行，整理 summary。
3. **MHE Claude CLI agent lane**：benchmark driver 通过 Claude CLI brain adapter 生成 / 修复 Nektar candidate，再交给 `metaharness_ext.nektar` pipeline 执行和验证。

核心问题：

- 三条 lane 是否都能复现 Nektar++ `.tst` 中记录的 L2/Linf 参考误差。
- Extension pipeline baseline 是否提供稳定的 Nektar session 执行、验证和 evidence 基线。
- Claude CLI agent lane 是否能在使用同一 Claude CLI / model 的前提下，比 direct Claude CLI 更少出现 XML 配置、solver 调用、误差解析、postprocess 和批量管理错误。
- Claude CLI agent lane 的诊断能力（XML 缺字段、solver 发散、FieldConvert 失败）是否优于 direct Claude CLI lane 的手动排查。

## 3.2 测试资源来源

Nektar++ source tree：

```text
/home/linden/code/work/Solvers/Nektar/nektar/
```

### 测试框架

Nektar++ 使用 `Tester` 可执行文件解析 `.tst` XML 文件来运行 regression test。每个 `.tst` 文件指定 solver executable、session XML parameters 和预期 metrics：

```xml
<test>
    <description>简短描述</description>
    <executable>SolverName</executable>
    <parameters>SolverName.xml</parameters>
    <metrics>
        <metric type="L2" id="1">
            <value variable="u" tolerance="1e-08">0.00135233</value>
        </metric>
        <metric type="Linf" id="2">
            <value variable="u" tolerance="1e-08">0.00275937</value>
        </metric>
    </metrics>
</test>
```

Solver 运行时在 stdout 输出 `L 2 error (variable u): 0.00135233` 格式的行，`Tester` 通过 `MetricL2` / `MetricLinf` 正则解析并与 `.tst` 期望值比较。

### 关键目录

| 目录 | 内容 |
|---|---|
| `solvers/ADRSolver/Tests/` | ~200 个 ADR test cases（Helmholtz, advection, diffusion, advection-diffusion, reaction-diffusion） |
| `solvers/IncNavierStokesSolver/Tests/` | ~300 个 IncNS test cases（Taylor vortex, Kovasznay, MMS） |
| `solvers/CompressibleFlowSolver/Tests/` | ~100 个 CompFlow test cases（Euler, isentropic vortex, MMS） |
| `solvers/DiffusionSolver/Tests/` | ~20 个 diffusion test cases |
| `tests/` | Tester 源码（`Tester.cpp.in`, `MetricL2.cpp`, `MetricLInf.cpp`） |

### 已选 Benchmark 对应的 Nektar++ 文件

| Case ID | .tst 路径 | .xml 路径 |
|---|---|---|
| `advection-1d` | `ADRSolver/Tests/Advection1D_WeakDG_GLL_LAGRANGE.tst` | `ADRSolver/Tests/Advection1D_WeakDG_GLL_LAGRANGE.xml` |
| `diffusion-2d` | `DiffusionSolver/Tests/ImDiffusion_m6.tst` | `DiffusionSolver/Tests/ImDiffusion_m6.xml` |
| `advdiff-2d` | `ADRSolver/Tests/UnsteadyAdvectionDiffusion_Order1_001.tst` | `ADRSolver/Tests/UnsteadyAdvectionDiffusion_Order1_001.xml` |
| `advdiff-imex-2d` | `ADRSolver/Tests/UnsteadyAdvectionDiffusion2D_IMEXdirk_2_3_3.tst` | `ADRSolver/Tests/UnsteadyAdvectionDiffusion2D_IMEXdirk_2_3_3.xml` |
| `taylor-vortex-2d` | `IncNavierStokesSolver/Tests/TaylorVor_dt1.tst` | `IncNavierStokesSolver/Tests/TaylorVor_dt1.xml` |
| `euler-1d` | `CompressibleFlowSolver/Tests/Euler1D.tst` | `CompressibleFlowSolver/Tests/Euler1D.xml` |

所有 session XML 都是自包含的——geometry、expansion、boundary conditions、ExactSolution 函数和 solver parameters 全部嵌入在 XML 中，不需要外部 mesh 文件。

## 3.3 首轮 Case List

首轮固定 6 个 cases，覆盖不同 PDE 类型和 solver family：

| Case ID | Solver | PDE 类型 | 维度 / 单元 | ExactSolution | 主要 L2 参考值 | 预计耗时 |
|---|---|---|---|---|---|---|
| `advection-1d` | ADRSolver | UnsteadyAdvection（双曲型） | 1D, 10段, P=3 | 高斯脉冲平流 | L2 u: 0.00960004 | <5s |
| `diffusion-2d` | DiffusionSolver | UnsteadyDiffusion（抛物型） | 2D, 混合, P=6 | 正弦衰减 | L2 u: 0.0020082 | <10s |
| `advdiff-2d` | ADRSolver | UnsteadyAdvectionDiffusion（混合型） | 2D, 4四边, P=9 | 正弦平流衰减 | L2 u: 0.00135233 | <5s |
| `advdiff-imex-2d` | ADRSolver | UnsteadyAdvectionDiffusion（高阶 IMEX） | 2D, 4四边, P=12 | 正弦平流衰减 | L2 u: 1.85112e-07 | <15s |
| `taylor-vortex-2d` | IncNavierStokesSolver | UnsteadyNavierStokes（NS 抛物型） | 2D, 16四边, P=10 | 泰勒衰减涡 | L2 u: 5.9519e-06 | <15s |
| `euler-1d` | CompressibleFlowSolver | EulerCFE（双曲型守恒律） | 1D, 20段, P=3 | 常状态 | L2 rho: 1.98838e-06 | <5s |

覆盖矩阵：

```
PDE 类型:  双曲型 (#1, #6) / 抛物型 (#2, #5) / 混合型 (#3, #4)
维度:      1D (#1, #6) / 2D (#2, #3, #4, #5)
精度跨度:  L2 误差从 1e-2 到 1e-7 (五个数量级)
Solver:    ADRSolver (#1, #3, #4) / DiffusionSolver (#2) / IncNavierStokesSolver (#5) / CompressibleFlowSolver (#6)
```

MHE Nektar extension 已原生支持 `ADRSolver` 和 `IncNavierStokesSolver`（`CAP_NEKTAR_SOLVE_ADR`、`CAP_NEKTAR_SOLVE_INCNS`）。`DiffusionSolver` 和 `CompressibleFlowSolver` 可通过 `NektarSessionPlan` 的 `solver_binary` 字段指定，但 agent lane 的 solver family dispatch 可能需适配。

## 3.4 目录结构

所有实验产物写入 `.runs/`，不写入仓库根目录：

```text
.runs/nektar-pde-benchmark/
  specs/
    advection-1d.json
    diffusion-2d.json
    advdiff-2d.json
    advdiff-imex-2d.json
    taylor-vortex-2d.json
    euler-1d.json
  extension/
    <case_id>/
      case_spec.json
      session.xml
      solver.stdout.log
      solver.stderr.log
      postprocess/
      metrics.json
      validation.json
      evidence.json
      attempt_log.json
      summary.json
  direct/
    <case_id>/
      case_spec.json
      claude_prompt.txt
      claude_command.json
      claude_stdout.json
      claude_stderr.txt
      claude_result.json
      session.xml
      solver.stdout.log
      solver.stderr.log
      metrics.json
      attempt_log.json
      summary.json
  agent/
    <case_id>/
      case_spec.json
      claude_prompt.txt
      claude_command.json
      claude_stdout.json
      claude_stderr.txt
      claude_result.json
      proposal.json
      session.xml
      solver.stdout.log
      solver.stderr.log
      postprocess/
      metrics.json
      validation.json
      evidence.json
      attempt_log.json
      summary.json
  comparison/
    summary_table.csv
    comparison_report.md
    result_bundle.json
    run_manifest.json
  reports/
    nektar-pde-analysis-report.md
    nektar-pde-backlog.md
```

## 3.5 Case Spec 设计

每个 case 先写统一 `case_spec.json`，extension baseline、direct Claude CLI lane 和 MHE Claude CLI agent lane 必须读取同一份 spec。示例：

```json
{
  "case_id": "advdiff-2d",
  "task_family": "nektar_pde",
  "solver_family": "adr",
  "solver_binary": "ADRSolver",
  "source_reference": {
    "tst": "/home/linden/code/work/Solvers/Nektar/nektar/solvers/ADRSolver/Tests/UnsteadyAdvectionDiffusion_Order1_001.tst",
    "xml": "/home/linden/code/work/Solvers/Nektar/nektar/solvers/ADRSolver/Tests/UnsteadyAdvectionDiffusion_Order1_001.xml",
    "description": "2D unsteady advection-diffusion, CG, IMEX order 1"
  },
  "required_capabilities": ["nektar_adr_solver"],
  "pde_type": "unsteady_advection_diffusion",
  "dimension": 2,
  "reference_metrics": {
    "l2_error_u": {"value": 0.00135233, "tolerance": 1e-08},
    "linf_error_u": {"value": 0.00275937, "tolerance": 1e-08}
  },
  "expected_artifacts": [
    "session.xml", "solver.stdout.log", "solver.stderr.log"
  ],
  "expected_metrics": [
    "l2_error_u", "linf_error_u", "elapsed_seconds"
  ]
}
```

字段约定：

- `source_reference` 必填，同时指向 `.tst` 和 `.xml` 文件。
- `reference_metrics` 从 `.tst` 的 `<metrics>` 块提取，保留原始 tolerance。
- `solver_family` 取 `adr` / `incns` / `diffusion` / `compressible`，对应 MHE Nektar extension 的 `NektarSolverFamily`。
- `required_capabilities` 必须与 agent lane 的 capability gate 对应。
- `pde_type` 必须与 Nektar++ session XML 中的 `EvolutionOperator` / equation type 一致。

## 3.6 Extension Pipeline Baseline 测试流程

Extension baseline 不调用 Claude CLI，也不做 LLM 生成。它只验证 `metaharness_ext.nektar` 作为确定性执行基线是否能稳定完成 session compile → solver execute → postprocess → validate → evidence。

流程：

1. 读取 `.runs/nektar-pde-benchmark/specs/<case_id>.json`。
2. 从 `source_reference.xml` 和 case spec 构造 `NektarProblemSpec` 或 `NektarSessionPlan`。
3. 调用 `NektarGatewayComponent`、`SessionCompilerComponent`、`SolverExecutorComponent`、`PostprocessComponent`、`ValidatorComponent`。
4. 写出 `extension/<case_id>/summary.json`、`validation.json`、`evidence.json`。
5. 如果失败，只记录 pipeline failure，不调用 Claude CLI 修复。

该 lane 用于回答：extension pipeline 是否可靠；不用于证明 LLM agent 优势。

## 3.7 Direct Claude CLI Lane 测试流程

Direct Claude CLI lane 模拟 Claude Code 直接使用 Nektar++ CLI 的方式。

流程：

1. 读取 `.runs/nektar-pde-benchmark/specs/<case_id>.json`。
2. 构造 generation prompt，调用 `claude -p` 或 `gclaude -p` 复制或修改 reference session XML。
3. 保存 `claude_prompt.txt`、`claude_command.json`、`claude_stdout.json`、`claude_stderr.txt`、`claude_result.json`。
4. 调用 solver：

```bash
ADRSolver session.xml > solver.stdout.log 2> solver.stderr.log
```

5. 解析 `solver.stdout.log` 中的 `L 2 error` / `L inf error` 行，提取数值。
6. 记录 return code、wall time，写 `metrics.json` 和 `summary.json`。
7. 如果第一次失败，可以调用同一 Claude CLI 做 repair，但必须记录在 `attempt_log.json` 和 Claude evidence 文件中。

Direct Claude CLI lane 禁止调用 `metaharness_ext.nektar` 的任何组件。

### Direct 误差解析约定

`metrics.json` 中的误差值必须从 solver stdout 的正则匹配提取，不得手动填入。推荐正则：

```python
L2_PATTERN = re.compile(
    r"^L 2 error\s*(?:\(variable\s+(\w+)\))?\s*:\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)"
)
LINF_PATTERN = re.compile(
    r"^L inf error\s*(?:\(variable\s+(\w+)\))?\s*:\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)"
)
```

此正则与 Nektar++ `MetricL2.cpp` 中的模式一致。

### Direct 最小 summary 示例

```json
{
  "task": "nektar_pde",
  "case_id": "advdiff-2d",
  "lane": "nektar_direct_claude_cli",
  "backend": "nektar_cli",
  "solver_binary": "ADRSolver",
  "source_reference": "/home/linden/code/work/Solvers/Nektar/nektar/solvers/ADRSolver/Tests/UnsteadyAdvectionDiffusion_Order1_001.tst",
  "command": ["ADRSolver", "session.xml"],
  "return_code": 0,
  "environment": {"cwd": "...", "nektar_version": "5.7.0"},
  "artifacts": {
    "session_xml": "session.xml",
    "field_files": [],
    "checkpoint_files": [],
    "log_files": ["solver.stdout.log", "solver.stderr.log"]
  },
  "metrics": {
    "l2_error_u": 0.00135233,
    "linf_error_u": 0.00275937,
    "elapsed_seconds": 2.1
  },
  "validation": {"passed": true, "status": "executed", "issues": []},
  "effort": {"attempt_count": 1, "repair_count": 0, "manual_interventions": 0},
  "timing": {"driver_elapsed_wall_time_seconds": 3.5, "solver_elapsed_wall_time_seconds": 2.1},
  "evidence_files": ["session.xml", "solver.stdout.log", "solver.stderr.log", "metrics.json", "summary.json"]
}
```

## 3.8 MHE Claude CLI Agent Lane 测试流程

MHE Claude CLI agent lane 使用 Claude CLI 作为 benchmark driver 层的 brain adapter，但仍由 `metaharness_ext.nektar` 负责受控执行、验证和 evidence 归档。

流程：

1. Agent runner 读取同一份 `case_spec.json`。
2. 构造 prompt，调用 `claude -p` 或 `gclaude -p` 生成 `proposal.json` 和 candidate session change。
3. 保存 Claude evidence：`claude_prompt.txt`、`claude_command.json`、`claude_stdout.json`、`claude_stderr.txt`、`claude_result.json`、`proposal.json`。
4. 将 candidate 转换为 `NektarProblemSpec`（通过 `NektarGatewayComponent`）或 `NektarSessionPlan`。
5. `SessionCompilerComponent` 生成 `NektarSessionPlan`。
6. `xml_renderer.write_session_xml()` 渲染 session XML。
7. `SolverExecutorComponent.execute_plan()` 调用 solver binary。
8. `PostprocessComponent` 可选运行 FieldConvert。
9. `ValidatorComponent` 验证 return code、field output 和 error norms。
10. 如果 validation 失败，最多调用 Claude CLI 做受限 repair；每次 repair 都新增 attempt log 和 Claude evidence。
11. 写出 `validation.json`、`evidence.json`、`summary.json`。

MHE Claude CLI agent lane 必须保留两类 evidence：

- Claude evidence：prompt、command、stdout JSON、stderr、proposal、repair proposal。
- Extension evidence：`session.xml`、solver stdout / stderr、postprocess artifact、metrics output、validation report、evidence bundle。

### Agent 与已有 MHE E2E 测试的复用

MHE Nektar extension 的 e2e 测试 (`tests/test_metaharness_nektar_e2e.py`) 已经覆盖 `HELMHOLTZ_1D`、`HELMHOLTZ_2D`、`TAYLOR_VORTEX`。MHE Claude CLI agent lane 应复用相同的 pipeline 但使用 benchmark case spec 和 Claude proposal 作为输入，而不是 e2e 测试中的硬编码常量。

对于 extension 尚未显式注册 solver family 的 case（`diffusion-2d`、`euler-1d`），MHE Claude CLI agent lane 应：

- 使用 `NektarSessionPlan` 的 `solver_binary` 字段指定 solver 路径。
- 记录 `solver_family_dispatch="passthrough"` 标记网关行为。
- 如果 solver binary 不存在，写 `status="unavailable"`。

### Agent 输出要求

MHE Claude CLI agent lane 的 `summary.json` 必须与 direct / extension lane 同构，至少字段一致：

```json
{
  "task": "nektar_pde",
  "case_id": "advdiff-2d",
  "lane": "nektar_mhe_claude_cli_agent",
  "backend": "metaharness_ext.nektar",
  "solver_binary": "ADRSolver",
  "source_reference": "/home/linden/code/work/Solvers/Nektar/nektar/solvers/ADRSolver/Tests/UnsteadyAdvectionDiffusion_Order1_001.tst",
  "command": ["ADRSolver", "session.xml"],
  "return_code": 0,
  "environment": {"cwd": "...", "nektar_version": "5.7.0"},
  "artifacts": {
    "session_xml": "session.xml",
    "field_files": ["session.fld"],
    "checkpoint_files": [],
    "log_files": ["solver.stdout.log", "solver.stderr.log"]
  },
  "metrics": {
    "l2_error_u": 0.00135233,
    "linf_error_u": 0.00275937,
    "elapsed_seconds": 2.1
  },
  "validation": {
    "passed": true,
    "status": "executed",
    "issues": [],
    "validation_report_ref": "validation.json"
  },
  "diagnostics": {
    "detected_error_type": null,
    "suggested_fix": null,
    "postprocess_status": "completed"
  },
  "effort": {"attempt_count": 1, "repair_count": 0, "manual_interventions": 0},
  "timing": {"driver_elapsed_wall_time_seconds": 5.2, "solver_elapsed_wall_time_seconds": 2.1},
  "evidence_files": [
    "case_spec.json",
    "session.xml",
    "solver.stdout.log",
    "solver.stderr.log",
    "metrics.json",
    "validation.json",
    "evidence.json",
    "summary.json"
  ]
}
```

## 3.9 Metric 计算规则

### 通用 metrics

| Metric | 含义 | 来源 |
|---|---|---|
| `l2_error_*` | L2 error norm per variable | solver stdout 正则解析 |
| `linf_error_*` | Linf error norm per variable | solver stdout 正则解析 |
| `elapsed_seconds` | solver 内部耗时 | driver 计时或 solver log |
| `driver_elapsed_wall_time_seconds` | 外层 driver / pipeline 耗时 | driver shell 计时 |
| `return_code` | solver process return code | `subprocess.returncode` |
| `passed` | 误差是否在 `.tst` tolerance 内 | comparator 判定 |
| `attempt_count` | 实际执行尝试次数 | `attempt_log.json` |
| `repair_count` | 失败后修改 XML/参数的次数 | `attempt_log.json` |

### 误差比较规则

每条 metric 与 `.tst` 中记录的 reference metric 比较。这里的语义不是“重新证明解析解误差”，而是验证 extension / direct / agent lane 是否复现 Nektar++ regression test 记录的 solver error norm：

```python
error_diff = abs(parsed_value - reference_value)
passed = error_diff <= tolerance
```

如果 `parsed_value` 来自当前 solver stdout，`reference_value` 来自 `.tst` 的 `<metrics>` 块，则 pass 表示“当前运行与 Nektar++ regression reference 一致”。这不等价于 agent 改善 solver 精度，也不用于跨 PDE case 比较精度高低。

对于 `.tst` 中记录多变量误差的 case（如 Taylor vortex 的 u/v/p），`metrics.json` 必须包含所有变量。

### 额外可观测指标

- **Divergence check**：solver stdout 中是否出现 `NaN`、`inf` 或 `diverged`。
- **CFL/time-step warnings**：solver 是否报告 CFL 超限或 time-step 限制。
- **Conservation drift**：如 solver 输出质量守恒信息，记录初始与最终 mass 差值。
- **Field file existence**：solver 完成后 `.fld` / `.chk` 文件是否存在且非空。

## 3.10 Pass / Fail 判定

每个 case 使用五层判定：

1. **Environment**：solver binary 是否存在（`shutil.which("ADRSolver")`），版本是否可记录。
2. **Execution**：return code 是否为 0，stdout/stderr 是否可保存。
3. **Output**：声明的 field/checkpoint/log 文件是否存在且非空。
4. **Error norms**：解析出的 L2/Linf error 是否满足 `.tst` tolerance。
5. **Postprocess**（extension / agent lane）：FieldConvert 是否成功（如 case spec 要求 postprocess）。

推荐 status：

| Status | 含义 |
|---|---|
| `executed` | solver 执行完成且所有 error norms 通过 tolerance |
| `unavailable` | solver binary 不存在或 session XML 缺失 |
| `failed` | solver return code 非 0，或 solver 内部报错 |
| `output_missing` | 执行成功但 field/checkpoint/log 文件缺失 |
| `numeric_failed` | 输出存在但 L2/Linf error 超出 tolerance |
| `parse_failed` | solver 输出完整但 L2/Linf 行无法解析 |
| `schema_failed` | summary 或 metrics 字段不满足 schema |

## 3.11 Attempt Log

每个 lane 都必须写 `attempt_log.json`：

```json
{
  "case_id": "taylor-vortex-2d",
  "lane": "nektar_direct_claude_cli",
  "attempts": [
    {
      "attempt": 1,
      "command": ["IncNavierStokesSolver", "session.xml"],
      "return_code": 1,
      "status": "failed",
      "issue": "Kinvis not set in session XML parameters section",
      "repair": "added <P> Kinvis = 1 </P> to PARAMETERS block"
    },
    {
      "attempt": 2,
      "command": ["IncNavierStokesSolver", "session.xml"],
      "return_code": 0,
      "status": "executed",
      "issue": null,
      "repair": null
    }
  ]
}
```

`summary.effort.attempt_count` 和 `summary.effort.repair_count` 必须从 `attempt_log.json` 派生。Claude CLI direct / MHE Claude CLI agent lane 还必须记录 `llm_call_count`、`model`、`total_cost_usd`（如果 CLI JSON 输出提供）和 `claude_session_id`（如果存在）。

## 3.12 Nektar Tester 预验证、Schema 校验与重复运行策略

### Nektar Tester 预验证

在 extension / direct / agent lane 之前，Phase 0 必须先用 Nektar++ 自身 Tester 或等价 solver command 验证 reference `.tst` 可运行。该步骤用于确认 benchmark case 本身和本地 Nektar 环境有效，而不是测试 MHE pipeline。

建议为每个 case 保存：

```text
.runs/nektar-pde-benchmark/preflight/<case_id>/tester.stdout.log
.runs/nektar-pde-benchmark/preflight/<case_id>/tester.stderr.log
.runs/nektar-pde-benchmark/preflight/<case_id>/tester_summary.json
```

`tester_summary.json` 最低字段：

```json
{
  "case_id": "advdiff-2d",
  "tst_path": ".../UnsteadyAdvectionDiffusion_Order1_001.tst",
  "xml_path": ".../UnsteadyAdvectionDiffusion_Order1_001.xml",
  "tester_available": true,
  "tester_return_code": 0,
  "reference_metrics_extracted": true,
  "status": "ready|tester_unavailable|reference_failed|missing_files"
}
```

如果 Tester 不可用，可以用 solver command + `.tst` metric extraction 做等价 preflight，但必须在 `tester_summary.json` 中标记 `tester_available=false` 和替代验证方式。

### Summary Schema 校验

每个 lane 生成 `summary.json` 后，必须先通过 schema validation，再进入 comparator。建议 schema 文件保存在：

```text
.runs/nektar-pde-benchmark/schema/nektar_pde_summary.schema.json
.runs/nektar-pde-benchmark/schema/nektar_pde_result_bundle.schema.json
```

最低校验项：

- `task`、`case_id`、`lane`、`backend`、`solver_binary`、`source_reference` 必填。
- `lane` 只能是 `nektar_extension_pipeline`、`nektar_direct_claude_cli` 或 `nektar_mhe_claude_cli_agent`。
- `validation.status` 只能取 `executed`、`unavailable`、`failed`、`output_missing`、`numeric_failed`、`parse_failed`、`schema_failed`。
- `metrics` 必须包含 `case_spec.expected_metrics` 中声明的 error norm 字段，除非 status 为 `unavailable` 或 `failed`。
- `artifacts.log_files` 中的 stdout / stderr 必须存在。
- `evidence_files` 中列出的文件必须实际存在。
- `effort.attempt_count` 与 `attempt_log.json` 中 attempts 长度一致。

schema validation 失败时，case status 设为 `schema_failed`，不得进入 error norm verdict。

### 重复运行与 flaky 处理

Nektar PDE 首轮 benchmark 默认每个 lane 每个 case 至少运行 1 次。正式报告建议每个 case 重复运行 3 次：

```text
.runs/nektar-pde-benchmark/extension/<case_id>/run-001/
.runs/nektar-pde-benchmark/direct/<case_id>/run-001/
.runs/nektar-pde-benchmark/agent/<case_id>/run-001/
```

重复运行规则：

- correctness 采用所有 run 必须通过 `.tst` tolerance 的保守规则。
- timing 使用 median，不使用单次最快值。
- 若 error norm 在 tolerance 内但低位数有差异，记录 `numeric_variance`，不标记失败。
- 若同一 lane 同一 case 出现 pass/fail 混合，标记 `flaky_numeric=true`，报告中必须单独分析。
- 若 solver stdout 解析有时成功、有时失败，标记 `flaky_parse=true`，优先修 parser 或日志捕获。
- `.tst` tolerance 不因本次结果临时放宽；如确需调整，必须在 case spec 中记录原因，并说明偏离 Nektar++ regression reference。

## 3.13 Comparator

Comparator 读取三条 lane 的 summary，但 workflow 优势判断主要比较同一 case 的 direct Claude CLI lane 与 MHE Claude CLI agent lane，不跨 PDE 类型比较数值难度。Extension baseline 用于解释 pipeline 是否可靠，以及 agent lane 失败是否源自 extension gap。

输入：

```text
.runs/nektar-pde-benchmark/extension/*/summary.json
.runs/nektar-pde-benchmark/direct/*/summary.json
.runs/nektar-pde-benchmark/agent/*/summary.json
```

输出：

```text
.runs/nektar-pde-benchmark/comparison/summary_table.csv
.runs/nektar-pde-benchmark/comparison/comparison_report.md
```

`summary_table.csv` 建议列：

```text
case_id,solver_family,pde_type,extension_status,direct_status,agent_status,extension_passed,direct_passed,agent_passed,direct_l2_error_ref_diff,agent_l2_error_ref_diff,direct_linf_error_ref_diff,agent_linf_error_ref_diff,direct_attempts,agent_attempts,direct_repairs,agent_repairs,direct_llm_calls,agent_llm_calls,extension_driver_time,direct_driver_time,agent_driver_time,extension_evidence_count,direct_evidence_count,agent_evidence_count,verdict
```

Comparator verdict 规则：

| Verdict | 条件 |
|---|---|
| `both_passed_agent_more_evidence` | 两边误差都通过，agent evidence 更完整 |
| `both_passed_direct_lighter` | 两边都通过，direct 更快且 evidence 缺口不影响复现 |
| `agent_recovered_direct_failed` | direct 失败（解析错误/配置错误），agent 通过 |
| `agent_diagnosed_issue` | agent 明确诊断了 direct lane 未发现的问题（如 XML 字段缺失、solver divergence） |
| `direct_passed_agent_failed` | direct 通过，agent 失败，需修 extension |
| `both_failed` | 两边都失败，检查 case spec 或环境 |
| `unavailable` | solver binary 或 session XML 不存在 |

## 3.14 结果保存与归档

完成 extension baseline、direct Claude CLI lane 与 MHE Claude CLI agent lane 后，必须把每个 PDE case 的 solver artifact、error norm、attempt log、Claude evidence 和 validation result 汇总为 comparison bundle。该 bundle 是最终分析报告的唯一数据来源，报告不得依赖人工记忆或聊天记录。

### Run Manifest

`comparison/run_manifest.json` 记录本次 Nektar PDE 实验运行环境：

```json
{
  "benchmark": "nektar-pde",
  "run_id": "nektar-pde-20260427-001",
  "created_at": "2026-04-27T00:00:00Z",
  "nektar_source_root": "/home/linden/code/work/Solvers/Nektar/nektar",
  "mhe_repo": "/home/linden/code/git/Aeloon/Aeloon-science-agent/MHE",
  "git_commit": "<commit-or-dirty-state>",
  "solver_binaries": {
    "ADRSolver": "/path/to/ADRSolver",
    "IncNavierStokesSolver": "/path/to/IncNavierStokesSolver",
    "FieldConvert": "/path/to/FieldConvert"
  },
  "nektar_version": "<version-or-null>",
  "claude_cli": {
    "binary": "claude|gclaude",
    "version": "<claude --version>",
    "model": "<configured-model>",
    "output_format": "json",
    "max_turns": 5,
    "permission_mode": "auto",
    "no_session_persistence": true
  },
  "case_ids": ["advection-1d", "taylor-vortex-2d"],
  "lanes": ["nektar_extension_pipeline", "nektar_direct_claude_cli", "nektar_mhe_claude_cli_agent"],
  "unavailable_cases": [],
  "notes": []
}
```

### Result Bundle

`comparison/result_bundle.json` 汇总 extension / direct / agent lane 的 error norm、artifact completeness、Claude metadata、diagnostics 和 verdict：

```json
{
  "benchmark": "nektar-pde",
  "run_id": "nektar-pde-20260427-001",
  "cases": [
    {
      "case_id": "advdiff-2d",
      "solver_family": "adr",
      "pde_type": "unsteady_advection_diffusion",
      "source_tst": ".../UnsteadyAdvectionDiffusion_Order1_001.tst",
      "source_xml": ".../UnsteadyAdvectionDiffusion_Order1_001.xml",
      "extension_summary": "../extension/advdiff-2d/summary.json",
      "direct_summary": "../direct/advdiff-2d/summary.json",
      "agent_summary": "../agent/advdiff-2d/summary.json",
      "extension_passed": true,
      "direct_passed": true,
      "agent_passed": true,
      "metric_deltas": {
        "direct_l2_ref_diff": 0.0,
        "agent_l2_ref_diff": 0.0
      },
      "artifact_delta": {"extension_count": 8, "direct_count": 8, "agent_count": 12},
      "llm_delta": {"direct_llm_calls": 1, "agent_llm_calls": 1},
      "diagnostic_delta": {"agent_detected_error_type": null},
      "timing_delta": {"agent_driver_overhead_seconds": 0.0, "extension_pipeline_overhead_seconds": 0.0},
      "verdict": "both_passed_agent_more_evidence"
    }
  ]
}
```

### 保存原则

- `summary.json` 是单 case 单 lane 的事实来源。
- solver stdout / stderr 必须保留原文，便于复查 error norm 正则解析。
- `metrics.json` 必须只保存从 stdout 或 postprocess artifact 解析出的值，不得手动填入 `.tst` reference 值。
- `summary_table.csv` 是人工快速查看用的扁平表。
- `result_bundle.json` 是分析报告引用的机器可读汇总。
- `run_manifest.json` 记录 solver binary、Nektar source、MHE git state、Claude CLI 配置和 unavailable cases。
- `reports/nektar-pde-analysis-report.md` 只能引用 `summary_table.csv`、`result_bundle.json` 和 case evidence 文件，不引用聊天上下文。

## 3.15 分析报告要求

最终分析报告写入：

```text
.runs/nektar-pde-benchmark/reports/nektar-pde-analysis-report.md
```

报告必须包含：

1. **Executive summary**：一句话结论，说明 agent 是否观察到 Nektar workflow 优势，以及代价是什么。
2. **Hypothesis review**：逐条回应零假设和待验证假设。
3. **Environment**：Nektar++ source path、solver binary availability、MHE git state、case 数量、unavailable cases。
4. **Case results**：引用 `summary_table.csv`，按 solver family / PDE type 分组。
5. **Reference fidelity analysis**：说明是否运行原始 `.tst` / `.xml` 对应 case，是否有修改。
6. **Correctness analysis**：extension / direct / agent 的 L2 / Linf ref diff、parse status、numeric pass/fail。
7. **Workflow quality analysis**：attempts、repairs、Claude CLI calls、parse_failed、output_missing、diagnostic quality、evidence completeness。
8. **Overhead analysis**：agent driver time、direct driver time 与 extension pipeline time 的差异，不解释为 Nektar solver 性能差异。
9. **Failure analysis**：列出失败 case、根因、是否由 agent pipeline 更早诊断。
10. **Backlog**：将发现的问题写入 `reports/nektar-pde-backlog.md`，每项包含 owner area、symptom、evidence ref、suggested fix。
11. **Conclusion**：接受、部分接受或拒绝 agent workflow 优势假设。

报告中每个结论都必须能追溯到以下之一：

- `comparison/summary_table.csv`
- `comparison/result_bundle.json`
- 某个 case 的 `summary.json`
- 某个 case 的 `attempt_log.json`
- 某个 case 的 solver stdout / stderr / validation / evidence 文件
- 原始 Nektar++ `.tst` / `.xml` 文件

### Backlog 格式

`reports/nektar-pde-backlog.md` 建议使用表格：

```markdown
| ID | Area | Symptom | Evidence | Suggested fix | Priority |
|---|---|---|---|---|---|
| NEK-BENCH-001 | error-norm-parser | L2 line exists but metric parser missed variable name | agent/advdiff-2d/solver.stdout.log | align parser with MetricL2.cpp regex | P1 |
```

## 3.16 公平性约束

- 三条 lane 使用同一份 `case_spec.json`，引用同一个 `source_reference.xml`。
- 三条 lane 使用同一个 Nektar++ solver binary。
- Direct Claude CLI lane 与 MHE Claude CLI agent lane 使用同一个 Claude CLI binary、model、budget 和 prompt policy。
- Direct Claude CLI lane 不得调用 `metaharness_ext.nektar` 任何组件。
- MHE Claude CLI agent lane 不得绕过 extension pipeline 直接调用 solver subprocess。
- 三条 lane 使用相同的误差解析正则（与 Nektar++ `MetricL2.cpp` 一致）。
- 所有失败尝试必须写入 `attempt_log.json`。
- MHE Claude CLI agent lane 的 pipeline overhead 必须在 timing 中单独记录，不与 solver 耗时混淆。
- 报告不得把 agent 自动生成的 evidence 直接当作"优势"，必须说明 evidence 是否支持复现、comparator 自动读取和 provenance 追溯。

## 3.17 最小执行顺序

1. 确认 Nektar++ solver binaries 可用：`ADRSolver`、`IncNavierStokesSolver`、`CompressibleFlowSolver`、`DiffusionSolver`。
2. 验证每个 reference `.tst` 和 `.xml` 文件存在。
3. 用 Nektar++ Tester 或等价 solver command 做 preflight，写 `preflight/<case_id>/tester_summary.json`。
4. 写 6 个 `case_spec.json`，从 `.tst` 中提取 reference metrics 和 tolerance。
5. 先跑 `nektar_extension_pipeline` lane，得到 deterministic extension baseline。
6. 再跑 `nektar_direct_claude_cli` lane，得到 direct Claude CLI baseline：
   - Claude CLI 生成 / 复制 reference XML → 调用 solver → 解析 stdout → 写 summary。
7. 再跑 `nektar_mhe_claude_cli_agent` lane，得到 Claude CLI brain + extension pipeline result：
   - 对已支持 solver family（ADR、IncNS）优先测试。
   - 对未显式注册的 solver（Diffusion、CompFlow）记录 `solver_family_dispatch` 行为。
8. 生成并执行 summary schema validation，修正 schema 缺项。
9. 写 comparator，生成 `summary_table.csv`、`result_bundle.json` 和 `run_manifest.json`。
10. 如进入正式报告阶段，每个 case 每条 lane 重复运行 3 次并记录 median timing / flaky flags。
11. 写 `reports/nektar-pde-analysis-report.md`，只陈述观察到的 workflow 差异。
12. 将失败、解析问题和 extension gap 写入 `reports/nektar-pde-backlog.md`。

## 3.18 Acceptance Criteria

- 至少 6 个 Nektar PDE cases 的 extension、direct Claude CLI 与 MHE Claude CLI agent lane 都尝试执行，或明确记录 `unavailable` 原因。
- 至少覆盖 ADRSolver、IncNavierStokesSolver 两个 MHE 已支持 solver family。
- 每个 case 都有 `source_reference` 指向 Nektar++ `.tst` 和 `.xml`。
- 每个 case 都有 preflight `tester_summary.json`，或明确记录 Tester 不可用的替代验证方式。
- 每个完成 case 都有 extension / direct / agent 三份同构 `summary.json`。
- 每个 Claude CLI lane 都有 prompt、command、stdout JSON、stderr 和 proposal evidence（如果该 lane 生成 proposal）。
- 每个 lane 都有 `attempt_log.json`。
- 每个 `summary.json` 都通过 schema validation，或明确记录 `schema_failed`。
- Comparator 能生成 `summary_table.csv`、`comparison_report.md`、`result_bundle.json` 和 `run_manifest.json`。
- 分析报告写入 `reports/nektar-pde-analysis-report.md`。
- Backlog 写入 `reports/nektar-pde-backlog.md`。
- 报告明确区分：solver 数值正确性、workflow 质量（配置/解析/诊断）、Claude CLI 调用成本、pipeline overhead、evidence completeness。
- 报告不得声称 agent 能改善 Nektar++ solver 本身的数值精度。

## 3.19 预期会暴露的问题

该测试方法预计能暴露以下 Nektar extension 优化点：

- `NektarSessionPlan` 对非 ADR/IncNS solver family 的 passthrough 支持是否足够。
- `SolverExecutorComponent` 的 error norm 解析是否与 Nektar++ `MetricL2.cpp` 正则一致。
- `ValidatorComponent` 是否能区分 solver divergence 与 output_missing。
- `xml_renderer` 是否能正确处理所有 6 个 case 的 session XML 结构（包括 IMEX 参数、DG 选项、mixed element types）。
- `PostprocessComponent` 的 FieldConvert 调用在 direct lane 无此步骤时是否增加价值。
- extension 的 `attempt_log` / repair tracking 机制是否足够透明。
- agent 是否能从 `case_spec.json` 自动推断 `NektarSolverFamily` 和 `NektarAdrEqType`，而不是为每个 case 手写分支。
- CompressibleFlowSolver 和 DiffusionSolver 是否应正式注册为新的 `NektarSolverFamily` enum member。

## 3.20 与 MHE 已有 Nektar E2E 测试的关系

| 文件 | 关系 | 说明 |
|---|---|---|
| `tests/test_metaharness_nektar_e2e.py` | 参考 | 提供 HELMHOLTZ_1D、HELMHOLTZ_2D、TAYLOR_VORTEX 的 pipeline 参考用法和 solver path 约定 |
| `tests/test_metaharness_nektar_solver_executor.py` | 参考 | solver executor 的行为测试，为本 benchmark 的 agent lane 设定正确性基线 |
| `src/metaharness_ext/nektar/contracts.py` | 依赖 | `NektarSessionPlan`、`NektarRunArtifact` 是本 benchmark agent lane 的核心数据契约 |
| `src/metaharness_ext/nektar/xml_renderer.py` | 依赖 | session XML 渲染，agent lane 的 session file 由此生成 |

本 benchmark 不应修改 MHE Nektar extension 的核心逻辑。如果 benchmark 发现 extension gap，应记录在 comparator report 中并转为 backlog item，而不是在 benchmark 执行期间修改 extension 以"通过测试"。
