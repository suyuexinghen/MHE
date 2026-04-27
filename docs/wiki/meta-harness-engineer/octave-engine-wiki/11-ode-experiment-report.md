# 11. ODE Experiment Report

## 11.1 Summary

本实验使用当前 `metaharness_ext.octave` 本地执行链路测试 GNU Octave ODE 求解能力。任务通过 `OctaveExperimentSpec -> EnvironmentProbe -> ScriptCompiler -> Executor -> Validator` 完整执行，并由 validator 接受为 `executed`。

结论：Octave extension 可以在本机 `octave-cli` 环境下编译 wrapper、运行 `ode45`、收集输出文件、生成 evidence refs，并产出 `governance_state="ready"` 的 validation report。

## 11.2 Experiment Setup

| 项目 | 值 |
|---|---|
| Task ID | `ode-decay-demo` |
| Workspace | `.runs/octave/ode-decay-demo/manual-run` |
| Octave binary | `/usr/bin/octave-cli` |
| Octave version | `GNU Octave, version 9.2.0` |
| Command | `/usr/bin/octave-cli --no-gui --quiet --no-init-file mhe_wrapper.m` |
| Plan ID | `octave-ode-decay-demo-e002fc07e3fc` |
| Run ID | `run-octave-ode-decay-demo-e002fc07e3fc` |
| Summary JSON | `.runs/octave/ode-decay-demo/manual-run/mhe_ode_experiment_summary.json` |

## 11.3 Numerical Problem

求解一阶常微分方程：

```text
y' = -2y, y(0) = 1, t in [0, 2]
```

解析解为：

```text
y(t) = exp(-2t)
```

Octave 脚本使用 `ode45` 计算数值解，并记录：

- `y_final`：数值终点值
- `analytic_final`：解析终点值 `exp(-4)`
- `final_error`：终点绝对误差
- `max_error`：采样点上的最大绝对误差

## 11.4 Pipeline Evidence

执行链路：

1. `OctaveEnvironmentProbeComponent.probe(spec)` 检查 binary、version、workspace writability。
2. `OctaveScriptCompilerComponent.compile(spec, environment)` 生成 `mhe_wrapper.m`。
3. `OctaveExecutorComponent.execute_plan(plan, environment)` 在 workspace 中运行 wrapper。
4. `OctaveValidatorComponent.validate_run(artifact, plan)` 检查 return code、输出文件和 evidence。

关键 evidence 文件：

- `.runs/octave/ode-decay-demo/manual-run/mhe_wrapper.m`
- `.runs/octave/ode-decay-demo/manual-run/outputs/ode_summary.txt`
- `.runs/octave/ode-decay-demo/manual-run/outputs/final_error.txt`
- `.runs/octave/ode-decay-demo/manual-run/outputs/max_error.txt`
- `.runs/octave/ode-decay-demo/manual-run/mhe_status.txt`
- `.runs/octave/ode-decay-demo/manual-run/stdout.log`
- `.runs/octave/ode-decay-demo/manual-run/stderr.log`
- `.runs/octave/ode-decay-demo/manual-run/mhe_ode_experiment_summary.json`

## 11.5 Results

从 `outputs/ode_summary.txt` 读取的结果：

| Metric | Value |
|---|---:|
| steps | `49` |
| y_final | `0.01831596285069622` |
| analytic_final | `0.01831563888873418` |
| final_error | `3.239619620447332e-07` |
| max_error | `2.222757419512167e-06` |

Validator 结果：

| Field | Value |
|---|---|
| artifact status | `completed` |
| return code | `0` |
| validation passed | `true` |
| validation status | `executed` |
| issues | `[]` |
| missing evidence | `[]` |
| governance state | `ready` |
| scored evidence score | `1.0` |
| warning count | `0.0` |

## 11.6 Interpretation

数值误差处于 `ode45` 对该非刚性指数衰减问题的预期范围内。实验没有依赖额外 Octave package，只使用核心 `ode45` 能力，因此环境面较简单。

本次测试验证的 extension 能力包括：

- environment probe 能识别真实 `octave-cli` 和 workspace 可写性
- compiler 能生成 wrapper-first 执行入口
- executor 能在 `.runs/` workspace 中运行 Octave 并收集 stdout/stderr/status/output evidence
- validator 能接受完成状态、return code 和 declared output files
- evidence refs 能覆盖 wrapper、输出文件和日志

## 11.7 Limitations

- 本实验验证的是本地 `OctaveExecutorComponent`，不是 SLURM/K8s real-mode 后端。
- Validator 当前对文件型 output 做存在性验证；数值误差由实验摘要文件记录，而不是通过 parsed variable tolerance 自动判定。
- 没有测试 package loading、plot/figure export、`.mat` 解析或长任务恢复。
- 结果依赖本机 GNU Octave 9.2.0 与默认 `ode45` 行为；跨平台数值差异应通过 tolerance 和环境 evidence 管理。

## 11.8 Reproduction

在仓库 `MHE/` 目录下运行与本实验等价的链路时，需要：

```bash
PYTHONPATH=src python <experiment-driver>.py
```

核心步骤是构造 `OctaveExperimentSpec`，调用 environment/compiler/executor/validator 四个组件，并把摘要写入 `.runs/octave/ode-decay-demo/manual-run/mhe_ode_experiment_summary.json`。

若要运行仓库内 gated smoke 测试：

```bash
MHE_RUN_REAL_OCTAVE=1 python -m pytest -m octave tests/test_metaharness_octave_environment_executor.py -q
```
