# 08. 测试与路线图

## 8.1 测试策略

### 默认测试层（不依赖真实 Octave）

- contracts Pydantic validation
- manifest static validation
- gateway family/mode dispatch
- environment missing binary / missing package mocked tests
- compiler wrapper generation snapshot tests
- executor subprocess mocked tests
- validator JSON/CSV/status parsing tests
- warning classification 与 `blocks_promotion` tests
- evidence refs / scored evidence / governance state tests

### 可选真实 Octave smoke

用 `@pytest.mark.octave` 标记，需要本地 `octave-cli`：

- minimal script：`x = 1 + 1`，保存 `.txt` / `.mat` 输出
- function eval：调用受控函数并验证变量
- package probe：检测已安装 package
- numeric tolerance：计算线性代数 / ODE 小例子并校验容差
- plot export：生成 PNG/PDF 并验证文件存在

默认 CI 不应依赖真实 Octave。真实 smoke 应在 `octave-cli` 不存在时自动 skip。

### pytest marker 注册

当前 `pyproject.toml` 注册 `octave` marker，并在默认测试中过滤真实 Octave smoke：

```toml
[tool.pytest.ini_options]
addopts = "-m 'not nektar and not quafu and not octave'"
markers = [
    "octave: opt-in tests requiring MHE_RUN_REAL_OCTAVE=1 and octave-cli",
]
```

真实 Octave smoke 同时使用 `@pytest.mark.octave`、`MHE_RUN_REAL_OCTAVE=1` 和 `shutil.which("octave-cli")` skip 条件。默认 `pytest` 不会运行这些测试；显式使用 `-m octave` 且设置环境变量后才会尝试真实 `octave-cli`。

### 推荐命令

```bash
python -m pytest tests/test_metaharness_octave_*.py -q
MHE_RUN_REAL_OCTAVE=1 python -m pytest -m octave tests/test_metaharness_octave_environment_executor.py -q
```

## 8.2 实施路线图

### Phase 0：Design baseline（当前）

- 完成 blueprint、roadmap、wiki skeleton
- 冻结首版 family、contracts、manifest slot/capability
- 明确不支持 MATLAB parity / Simulink / GUI

### Phase 1：Typed contracts + gateway + compiler

- 实现 contracts、slots、capabilities、manifest
- 实现 gateway skeleton（`issue_task`、`compile_experiment` 入口、family 分发）
- 实现 deterministic wrapper compiler
- gateway / compiler / contract / manifest tests

### Phase 2：Environment + executor

- 实现 `octave-cli` 与 package probe
- 实现 workspace staging 和 mocked subprocess executor
- 所有输出写入 `.runs/octave/...` 或 runtime storage
- missing binary、timeout、nonzero return tests

### Phase 3：Validator + evidence + policy

- 实现 output schema、numeric tolerance、warning classification
- 产出 MHE-compatible `ValidationIssue`、`ScoredEvidence`、`evidence_refs`
- evidence bundle / policy / governance tests

### Phase 4：Integration + minimal demo

- 实现 `run_baseline(...)` 全链路
- graph example、manifest example、minimal demo
- 可选真实 Octave smoke（`@pytest.mark.octave`）

### Phase 5：Scientific workflow expansion

- `OctaveStudyComponent`：parameter sweep / benchmark
- Scientific Context Engine 前置检查（量纲、误差传播）
- HPC/scheduler adapter 和 long-running execution lifecycle 对接

### 阶段依赖

```text
Phase 0: Design baseline
    |
Phase 1: Typed contracts + gateway + compiler
    |
Phase 2: Environment + executor
    |
Phase 3: Validator + evidence + policy
    |
Phase 4: Integration + minimal demo
    |
Phase 5: Scientific workflow expansion
```

## 8.3 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| 任意脚本执行带来安全风险 | 高 | wrapper-first、workspace allowlist、sandbox policy、protected validator |
| MATLAB 兼容性被过度承诺 | 高 | 文档明确 Octave worker，不承诺 toolbox/Simulink parity |
| package 生态差异 | 中 | package probe + required/optional spec + missing prerequisite report |
| 输出格式不稳定 | 中 | 首版优先 JSON/CSV/status file，`.mat` 作为增强 |
| 图像/plot backend 环境差异 | 中 | 图形输出通过 `OctaveOutputSpec(kind="figure")` 支持，真实 smoke gated |
| 长时间任务阻塞 | 中 | 后续接入 ExecutionLifecycleService 和 scheduler adapter |
| 数值结果平台差异 | 中 | 容差、BLAS/LAPACK facts、seed、environment evidence |

## 8.4 首版完成判据

- `OctaveExperimentSpec → OctaveRunPlan → OctaveRunArtifact → OctaveValidationReport` 全链路可运行
- 默认测试不依赖真实 Octave
- 真实 `octave-cli` smoke gated 且自动 skip
- 所有生成文件默认写入 `.runs/`
- validator 能区分环境、编译、运行、输出缺失、数值失败和成功执行
- validation report 包含 `blocks_promotion`、`ValidationIssue`、`ScoredEvidence`、`evidence_refs`
- blueprint、roadmap、wiki、manifest、tests 与实现边界一致
- 文档不声称 MATLAB / Simulink / GUI / toolbox 完整替代
