# 04. 环境、验证与证据

## 4.1 为什么量子环境探测是独立组件

量子计算的环境前提比经典 HPC 求解器更复杂：

1. **后端多样性**：模拟器、不同芯片代次、不同校准状态——同一电路在不同后端上的结果可能不可比
2. **时变噪声**：超导芯片的 T1/T2 随时间漂移，校准每小时可能变化
3. **排队与配额**：真机有排队深度和每日配额限制，影响实验的可重复性和并行度
4. **SDK 兼容性**：pyQuafu / qiskit-aer 的版本、API token 有效性、功能支持矩阵

因此，Environment 不仅是"探测二进制是否存在"，而是对量子后端进行
**结构化的可用性与噪声特征采集**。

## 4.2 环境探测流程

```
QComputeEnvironmentComponent.probe(backend_spec)
  │
  ├─ 1. 后端可达性检查
  │   ├─ API endpoint ping
  │   ├─ Token 有效性验证
  │   └─ 每日配额余量查询
  │
  ├─ 2. 设备状态查询
  │   ├─ 芯片在线/维护状态
  │   ├─ 当前排队深度
  │   └─ 可用量子比特数
  │
  ├─ 3. 校准数据采集
  │   ├─ T1/T2 热弛豫时间
  │   ├─ 单比特门保真度
  │   ├─ 双比特门（CX）保真度
  │   ├─ 读出保真度
  │   └─ 量子比特连通图
  │
  └─ 4. 生成 QComputeEnvironmentReport
      ├─ 汇总可用性 + 噪声特征
      ├─ 标记缺失前提条件
      └─ 判断是否 blocks_promotion
```

### 4.2.2 配额与重试配置

pyQuafu 平台的实际运行约束：

| 参数 | 默认值 | 来源 |
|------|--------|------|
| `daily_task_limit` | 1000 | pyQuafu 文档；超出排队处理 |
| `quota_reset_time` | 00:00 CST | 需验证（Quafu 官方确认） |
| `max_polling_seconds` | 600 | 推荐上限；避免无休止等待 |
| `retry_base_delay_seconds` | 1 | 斐波那契轮询起点 |
| `retry_max_delay_seconds` | 60 | 斐波那契轮询上限 |
| `max_retries` | 3 | 不可重试异常不触发 retry |

任务状态机：`Created → In Queue → Running → Completed / Failed / Timeout`

- 仅在 `In Queue` 状态可执行 `cancel()`
- 一旦进入 `Running`，任务不可撤回
- 部分执行（如请求 1024 shots 仅完成 512）：pyQuafu 抛出异常而非返回残缺结果

### 4.2.3 校准时效性检查

校准数据的预测能力随时间衰减——超过数小时的校准用于 pre-execution fidelity
估计时，r² 从 ~0.82 降至不可靠水平。Environment 组件应在生成报告时检查校准年龄：

```python
from datetime import datetime, timezone, timedelta

def _check_calibration_freshness(self, calibration_data: QComputeCalibrationData) -> None:
    age = (datetime.now(timezone.utc) - calibration_data.timestamp).total_seconds() / 3600
    if age > 24:
        self._issues.append("CALIBRATION_STALE: calibration data >24h old, blocks_promotion=True")
    elif age > 3:
        self._issues.append("QCOMPUTE_CALIBRATION_STALE_WARN: calibration data >3h old")
```

校准超过 3 小时发出警告（`blocks_promotion=False`），
超过 24 小时标记为不可靠（`blocks_promotion=True`）。

## 4.3 前提条件分类

```python
class QComputePrerequisiteCategory(str, Enum):
    BACKEND_UNREACHABLE = "backend_unreachable"     # 后端不可达
    TOKEN_INVALID = "token_invalid"                 # API token 无效
    QUOTA_EXHAUSTED = "quota_exhausted"             # 每日配额耗尽
    CHIP_OFFLINE = "chip_offline"                   # 芯片维护中
    CALIBRATION_STALE = "calibration_stale"         # 校准过期（>24h）
    SDK_VERSION_MISMATCH = "sdk_version_mismatch"   # SDK 版本不兼容
    QUBIT_COUNT_INSUFFICIENT = "qubit_count_insufficient"  # 芯片比特数不足
```

### 4.3.1 前提条件与 promotion blocking

对接 strengthened MHE 时，前提条件缺失应直接映射到 `blocks_promotion=True`：

| 前提条件 | `blocks_promotion` | 原因 |
|---------|-------------------|------|
| 后端不可达 | `True` | 无法执行，必然失败 |
| Token 无效 | `True` | 无权限提交任务 |
| 配额耗尽 | `True` | 当日无法继续 |
| 芯片离线 | `True` | 目标硬件不可用 |
| 校准过期 | `False`（默认） | 可继续执行但验证标准应放宽 |
| SDK 版本不匹配 | `False`（默认） | 可能有兼容性路径 |

## 4.4 验证语义

### 4.4.1 验证流程

```
QComputeValidator.validate(artifact, plan, environment_report)
  │
  ├─ 1. 完整性检查
  │   ├─ artifact.status == "completed"
  │   ├─ counts 非空或 statevector 可用
  │   └─ 测量 shots 数量 >= plan.shots
  │
  ├─ 2. 统计显著性（真机特有）
  │   ├─ χ² 拟合优度检验
  │   └─ 测量分布与均匀分布的偏离度
  │
  ├─ 3. 保真度评估
  │   ├─ 与理想模拟器结果对比（有参考时）
  │   ├─ 与已知基态能量对比（VQE 场景）
  │   └─ 噪声模型下的理论保真度上限
  │
  ├─ 4. 噪声影响评分
  │   ├─ 基于校准数据的门错误累积估算
  │   ├─ 读出置信度
  │   └─ 噪声对结果方差的贡献
  │
  └─ 5. 生成 QComputeValidationReport
      ├─ 汇总所有指标
      ├─ 生成 ValidationIssue 列表
      └─ 判定 promotion_ready
```

### 4.4.2 验证状态机

```
                    ┌─────────────┐
                    │  submitted   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
     ┌────────────┐ ┌──────────┐ ┌──────────────┐
     │ validated  │ │收敛状态   │ │ 失败状态       │
     │            │ │converged │ │               │
     └────────────┘ └──────────┘ └──────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐ ┌──────────┐ ┌────────────────┐
     │收敛        │ │保真度不足 │ │噪声破坏         │
     │converged   │ │below_    │ │noise_corrupted │
     │            │ │fidelity  │ │                │
     └────────────┘ └──────────┘ └────────────────┘
```

## 4.5 验证与 governance 的映射

Validator 是 QCompute 的 **protected component**。其输出直接参与 MHE 的 promotion decision：

```python
def _build_validation_issues(report: QComputeValidationReport) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if report.status in {QComputeValidationStatus.BACKEND_UNAVAILABLE,
                         QComputeValidationStatus.ENVIRONMENT_INVALID}:
        issues.append(ValidationIssue(
            code="QCOMPUTE_PRECONDITION_FAILED",
            message=f"Backend prerequisite not met: {report.status}",
            subject=report.task_id,
            category=ValidationIssueCategory.INFRASTRUCTURE,
            blocks_promotion=True,
        ))
    if report.status == QComputeValidationStatus.BELOW_FIDELITY_THRESHOLD:
        issues.append(ValidationIssue(
            code="QCOMPUTE_FIDELITY_BELOW_THRESHOLD",
            message=f"Fidelity {report.metrics.fidelity} below threshold",
            subject=report.task_id,
            category=ValidationIssueCategory.SEMANTIC,
            blocks_promotion=True,
        ))
    if report.status == QComputeValidationStatus.NOISE_CORRUPTED:
        issues.append(ValidationIssue(
            code="QCOMPUTE_NOISE_IMPACT_HIGH",
            message=f"Noise impact score {report.metrics.noise_impact_score} exceeds limit",
            subject=report.task_id,
            category=ValidationIssueCategory.SEMANTIC,
            blocks_promotion=False,  # 可由 policy 决定是否阻止
        ))
    return issues
```

## 4.6 证据与审计

### 4.6.1 Evidence bundle 构建

`QComputeEvidenceBundle` 将一次量子实验的完整证据链打包：

1. `environment_report` —— 执行时的环境与噪声快照
2. `run_artifact` —— 原始执行产物
3. `validation_report` —— 验证结论与指标
4. `provenance_inputs` —— 上游输入引用（如 ABACUS 产出的哈密顿量 artifact ref）
5. `scored_evidence` —— 对齐 MHE `ScoredEvidence`，包含 `safety_score`、`budget`、`convergence`

### 4.6.2 审计锚点

QCompute 产出的所有 report 与 artifact 都应被设计为 **audit anchor**：

- `task_id` / `plan_ref` / `artifact_ref` 形成完整的引用链
- `calibration_snapshot` 提供执行时的硬件状态审计记录
- `raw_output_path` 指向不可变的原始输出文件
- `created_at` 时间戳支持时序审计

## 4.7 噪声感知评分

噪声影响评分 (`noise_impact_score`) 是 QCompute 特有的 evidence 维度，
量化噪声对量子运行结果的置信度影响：

### 4.7.1 ESP (Estimated Success Probability)

最简启发式——电路中所有门保真度的乘积：

$$ESP = \prod_{g \in circuit} F_g \times \prod_{q \in measured} (1 - \epsilon_{readout,q})$$

### 4.7.2 QVA (Quantum Vulnerability Analysis)

考虑 2-qubit 门误差传播的高级启发式（r² ≈ 0.82 vs 实测保真度）：

$$QVA = ESP \times \prod_{(q_i,q_j) \in 2Q\ gates} \exp(-w \cdot \sigma_{q_i,q_j})$$

其中 $w$ 为系统特定的误差传播权重，$\sigma_{q_i,q_j}$ 为 qubit pair 的校准噪声标准差。

### 4.7.3 SimpleTES 多目标编译评分

$$Score = w_1 \cdot N_{SWAP} + w_2 \cdot Depth - w_3 \cdot \log(Fidelity_{est})$$

### 4.7.4 误差缓解叠加开销

$$N_{shots,total} = N_{shots} \cdot \prod_{i \in EM} \gamma_i$$

其中 $\gamma_i$ 为第 $i$ 种错误缓解技术的采样开销倍数（ZNE: 2-5x, MEM: 1x, DD: 1x）。

Agent 在策略选择时必须权衡保真度增益与 QPU 时间成本。

评分范围 0-1：0 = 无噪声影响（理想模拟器），1 = 噪声完全淹没信号。

## 4.8 Evidence-first report 设计原则

量子计算的结果天然带有不确定性（概率测量、硬件噪声、校准漂移），
因此 QCompute 的 report 设计遵循 **evidence-first** 原则：

1. **原始数据不可丢弃**：原始 counts/statevector 保存到 `raw_output_path`，不依赖下游二次处理
2. **噪声上下文绑定**：每次真机运行绑定当时的校准快照（`calibration_snapshot`）
3. **评估上下文显式化**：记录使用的参考解、噪声模型参数、阈值设置
4. **可复现性优先**：report 包含足够信息使同一次运行可在模拟器中复现（用于交叉验证）

这使 QCompute 的 evidence 不只是"通过/失败"信号，而是可供 governance 层进行
独立评估的完整上下文。
