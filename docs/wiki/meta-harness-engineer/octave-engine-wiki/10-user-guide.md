# 10. Octave Extension User Guide

## 10.1 用途

`metaharness_ext.octave` 用于把 GNU Octave 脚本纳入 MHE 的 typed execution pipeline：

```text
OctaveExperimentSpec
  -> OctaveEnvironmentReport
  -> OctaveRunPlan
  -> OctaveRunArtifact
  -> OctaveValidationReport
  -> OctaveEvidenceBundle / policy / governance
```

它不是 MATLAB / Simulink / GUI 的完整替代，而是一个 wrapper-first、CLI-first 的受控 Octave 执行扩展。默认执行路径通过编译器生成 `mhe_wrapper.m`，再以 `octave-cli --no-gui --quiet --no-init-file mhe_wrapper.m` 运行。

## 10.2 安装与前置条件

开发环境：

```bash
pip install -e '.[dev]'
```

可选真实 Octave 执行需要本机可找到 `octave-cli`：

```bash
command -v octave-cli
octave-cli --version
```

Kubernetes real-mode 客户端依赖是可选额外依赖：

```bash
pip install -e '.[k8s]'
```

默认测试不会依赖真实 Octave。真实 smoke 测试需要显式打开：

```bash
MHE_RUN_REAL_OCTAVE=1 python -m pytest -m octave tests/test_metaharness_octave_environment_executor.py -q
```

## 10.3 最小任务规格

一个 Octave 任务至少需要：

- `task_id`：简单标识符，不包含 `/`、`\\` 或 `..`
- `script`：inline / file / function 三种模式之一
- `expected_outputs`：至少一个声明的输出，用于 evidence 和 validator
- 可选 `workspace`：不指定时默认落在 `.runs/octave/{task_id}/{run_id}`

示例：

```python
from metaharness_ext.octave.contracts import (
    OctaveExperimentSpec,
    OctaveOutputSpec,
    OctaveScriptSpec,
    OctaveWorkspaceSpec,
)

spec = OctaveExperimentSpec(
    task_id="demo-task",
    script=OctaveScriptSpec(
        mode="inline",
        inline_source="result = 2 + 3;",
    ),
    workspace=OctaveWorkspaceSpec(working_directory=".runs/octave/demo-task/manual-run"),
    expected_outputs=[
        OctaveOutputSpec(name="result", variable_name="result"),
    ],
)
```

`kind="variable"` 输出会由 wrapper 使用 `save('-text', ...)` 写入 `outputs/{variable}.txt`。`kind="text"`、`kind="mat"`、`kind="json"`、`kind="figure"` 等文件型输出需要声明 `file_name`，并由脚本或 wrapper 生成对应文件。

## 10.4 本地执行流程

完整本地链路：

```python
from metaharness_ext.octave.environment import OctaveEnvironmentProbeComponent
from metaharness_ext.octave.executor import OctaveExecutorComponent
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.validator import OctaveValidatorComponent

environment = OctaveEnvironmentProbeComponent().probe(spec)
plan = OctaveScriptCompilerComponent().compile(spec, environment)
artifact = OctaveExecutorComponent().execute_plan(plan, environment)
validation = OctaveValidatorComponent().validate_run(artifact, plan)
```

关键产物：

- `OctaveEnvironmentReport`：`octave-cli` 路径、版本、package probe、workspace 可写性
- `OctaveRunPlan`：`plan_id`、`run_id`、wrapper source、argv、workspace、expected outputs
- `OctaveRunArtifact`：return code、stdout/stderr、output files、status file、warnings、evidence refs
- `OctaveValidationReport`：`passed`、status、issues、missing evidence、scored evidence、governance state

## 10.5 ODE 示例

下面示例求解 `y' = -2y, y(0)=1`，并把数值解终点误差写成 evidence 文件：

```python
from pathlib import Path
from metaharness_ext.octave.contracts import (
    OctaveExperimentSpec,
    OctaveOutputSpec,
    OctaveScriptSpec,
    OctaveWorkspaceSpec,
)

workspace = Path(".runs/octave/ode-decay-demo/manual-run").resolve()
script = r"""
f = @(t, y) -2.0 * y;
tspan = [0, 2];
y0 = 1.0;
[t, y] = ode45(f, tspan, y0);
analytic_final = exp(-4.0);
y_final = y(end);
final_error = abs(y_final - analytic_final);
max_error = max(abs(y - exp(-2.0 .* t)));
fid = fopen('outputs/final_error.txt', 'w'); fprintf(fid, '%.16g\\n', final_error); fclose(fid);
fid = fopen('outputs/max_error.txt', 'w'); fprintf(fid, '%.16g\\n', max_error); fclose(fid);
"""

spec = OctaveExperimentSpec(
    task_id="ode-decay-demo",
    script=OctaveScriptSpec(mode="inline", inline_source=script),
    workspace=OctaveWorkspaceSpec(working_directory=str(workspace)),
    expected_outputs=[
        OctaveOutputSpec(name="final-error", kind="text", file_name="final_error.txt"),
        OctaveOutputSpec(name="max-error", kind="text", file_name="max_error.txt"),
    ],
)
```

本仓库的实测报告见 `11-ode-experiment-report.md`。

## 10.6 Scheduler 与长任务

`OctaveSchedulerAdapter` 根据 plan metadata 路由到 SLURM 或 Kubernetes backend：

- 默认 `dry_run=True`，返回 `dryrun-slurm-*` 或 `dryrun-k8s-*` handle，不提交真实作业
- SLURM real-mode 通过注入 command client 调用 `sbatch`、`squeue`、`sacct`、`scancel`
- Kubernetes real-mode 通过注入 job client 或 `kubernetes` optional dependency 创建 `batch/v1 Job`
- Kubernetes workspace 必须是绝对的 node-visible 路径，当前实现用 `hostPath` 挂载同一路径

生产集群运行前需要确认 workspace 对提交节点和执行节点都可见，且输出仍落在声明的 `OctaveRunArtifact` evidence files 中。

## 10.7 Optimizer 与 Study

v2 提供 `OctaveDomainBrainProvider` 作为参数探索 seam：

- `deterministic`：按 axis 候选顺序提出未尝试 snapshot
- `bayesian`：可注入 Bayesian optimizer；未注入时回退为 deterministic 候选顺序
- `llm_guided`：可注入 LLM-guided optimizer；候选仍会经过 whitelist sanitization

所有 proposal 只允许修改 `OctaveStudyAxis.parameter_path` 白名单内的字段，并通过 `MutationProposal.domain_payload["whitelist_paths"]` 暴露审计边界。

## 10.8 安全边界

编译阶段会调用 `OctaveSecurityScanner.require_safe(spec)`，对 inline/source 内容做静态扫描。危险模式会阻止 compile，例如：

- `system(...)`
- `unix(...)`
- shell bang command
- `urlread` / `urlwrite` / `web`
- `pkg install`

静态扫描是 defense-in-depth，不替代 OS sandbox、容器隔离或集群权限策略。

## 10.9 常见故障

| 现象 | 常见原因 | 处理 |
|---|---|---|
| `environment.available=False` | 找不到 `octave-cli`、workspace 不可写、required package 缺失 | 检查 binary、目录权限、package 声明 |
| `status="runtime_failed"` | wrapper 内 Octave 抛错或 return code 非 0 | 查看 `stderr.log` 与 `mhe_status.txt` |
| `status="output_missing"` | `expected_outputs` 声明与实际文件名不一致 | 确认文件写入 `outputs/` 且 `file_name` 只写文件名 |
| K8s manifest 构建失败 | workspace 是相对路径 | 使用绝对 node-visible workspace |
| 默认 pytest 不跑真实 smoke | `pyproject.toml` 默认排除 `octave` marker | 设置 `MHE_RUN_REAL_OCTAVE=1` 并显式 `-m octave` |

## 10.10 推荐验证命令

```bash
python -m pytest tests/test_metaharness_octave_*.py -q
ruff check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
ruff format --check src/metaharness_ext/octave tests/test_metaharness_octave_*.py
```

真实 Octave smoke：

```bash
MHE_RUN_REAL_OCTAVE=1 python -m pytest -m octave tests/test_metaharness_octave_environment_executor.py -q
```
