# 04. 环境、验证与证据

## 4.1 执行管线主链路

```text
┌─────────────────────────────────────────────────────────────┐
│  1. Gateway: 接收 spec，选择 family，拒绝越界模式            │
│     -> OctaveExperimentSpec                                  │
├─────────────────────────────────────────────────────────────┤
│  2. Environment Probe: 检测 octave-cli、packages、workspace  │
│     -> OctaveEnvironmentReport                               │
├─────────────────────────────────────────────────────────────┤
│  3. Script Compiler: spec -> wrapper .m + workspace staging  │
│     -> OctaveRunPlan                                         │
├─────────────────────────────────────────────────────────────┤
│  4. Executor: octave-cli --no-gui --quiet --no-init-file     │
│     -> OctaveRunArtifact (stdout/stderr/outputs/figures)     │
├─────────────────────────────────────────────────────────────┤
│  5. Validator: output schema + numeric tolerance + warnings  │
│     -> OctaveValidationReport                                │
├─────────────────────────────────────────────────────────────┤
│  6. Evidence Policy: report -> ready/defer/blocked           │
│     -> governance_state + blocks_promotion                   │
└─────────────────────────────────────────────────────────────┘
```

## 4.2 Environment Probe 探测内容

| 探测项 | 方法 | 失败后果 |
|--------|------|----------|
| `octave-cli` 存在 | `shutil.which('octave-cli')` | blocking — 无法执行 |
| Octave 版本 | `octave-cli --version` | 可配置最低版本要求 |
| Package 可用性 | `pkg list` 或 probe 脚本 | 按 spec 中 required/optional 判定 |
| Workspace 可写 | 尝试创建临时文件 | blocking — 无法保存输出 |
| BLAS/LAPACK | `octave --eval "version -blas"` 等 | 记录到 environment facts |
| Graphics backend | `graphics_toolkit()`（仅当 spec 声明 figure 输出时探测） | 可选事实，不阻塞执行；`--no-gui` 下可能未初始化 |

## 4.3 外部依赖策略

### 必需运行时前提

| 依赖 | 用途 | 检测位置 |
|------|------|----------|
| `octave-cli` | 非交互执行 Octave 脚本 | Environment probe |
| 可写 workspace | 输入/输出/日志/证据落盘 | Environment probe / Executor |

### 可选 Octave package（按需声明）

| Package | 典型用途 | 策略 |
|---------|---------|------|
| `io` | 表格、Excel/CSV 数据交换 | required/optional by spec |
| `statistics` | 统计分析 | required/optional by spec |
| `signal` | 信号处理 | required/optional by spec |
| `control` | 控制系统 | required/optional by spec |
| `optim` | 优化 | required/optional by spec |
| `symbolic` | 符号计算 | optional, version-sensitive |
| `image` | 图像处理 | optional |

**首版不在 executor 中自动安装 package。** 缺失 package 进入 environment report 和 validation issue，由用户或外部环境管理解决。

## 4.4 Validation Report 状态机

```text
                    +---------------------+
                    | environment_invalid |
                    +---------------------+
                              |
                    +---------------------+
                    | compile_failed      |
                    +---------------------+
                              |
                    +---------------------+
                    | runtime_failed      |
                    +---------------------+
                              |
                    +---------------------+
                    | output_missing      |
                    +---------------------+
                              |
                    +---------------------+
                    | output_parse_failed |
                    +---------------------+
                              |
                    +---------------------+
                    | numeric_validation  |
                    | _failed             |
                    +---------------------+
                              |
                    +---------------------+
                    | executed            |
                    +---------------------+
```

状态按优先级递减：一旦命中更高优先级的状态，不再评估更低优先级的检查。`executed` 是唯一表示"所有检查通过"的终态。

## 4.5 Warning 分类策略

Executor 捕获的 stderr 和 Octave warning 按严重程度分类：

| 级别 | 示例 | 对 promotion 的影响 |
|------|------|---------------------|
| `benign` | `warning: division by zero (result set to Inf)` — 已知数值行为 | 不阻塞 |
| `suspicious` | `warning: load: variable 'x' not found` — 可能表示输入问题 | defer |
| `blocking` | `error: 'statistics' package not installed` — 环境不完整 | blocked |

## 4.6 Evidence Policy 判定逻辑

`OctaveEvidencePolicy` 基于 environment、artifact、validation 和 output completeness 生成 governance 建议：

| 条件 | governance_state |
|------|-----------------|
| environment missing 或 package missing | `blocked` |
| run completed 但缺少结构化输出 | `defer` 或 `blocked` |
| numeric tolerance failed | `blocked` |
| warning suspicious 但核心输出完整 | `defer` |
| all checks passed 且 evidence complete | `ready` |

## 4.7 Evidence Bundle 组成

```text
OctaveEvidenceBundle:
  ├── environment_report: OctaveEnvironmentReport
  ├── run_plan: OctaveRunPlan
  ├── run_artifact: OctaveRunArtifact
  ├── validation_report: OctaveValidationReport
  ├── policy_report: OctavePolicyReport
  ├── evidence_refs: list[str]
  └── scored_evidence: ScoredEvidence | None
```

所有 evidence 通过 `artifact_store` 管理，自动进入 provenance graph。每个 artifact 都能追溯到 plan hash、script hash、input asset hash 与 output hash。
