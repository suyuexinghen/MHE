# 05. Family 设计

## 5.1 为什么 family 是一等设计对象

量子计算实验的搜索空间天然是多维的：

- **ansatz 选择**：VQE 的不同 ansatz（UCCSD、HE、EfficientSU2）对同一分子给出不同精度
- **后端选择**：不同芯片的代次、拓扑、噪声特征影响 SWAP 开销和保真度
- **编译策略**：baseline / SABRE / agentic 在深度与保真度之间存在不同的 tradeoff
- **错误缓解**：REM / ZNE / Pauli Twirling 的组合选择影响有效保真度

family 设计将这些维度结构化为可搜索、可比较、可复现的实验网格。
它直接对应 SimpleTES 的 C×L×K 范式，并与 MHE Study 组件对齐。

## 5.2 Family 类型定义

### 5.2.1 AnsatzFamily

```python
class AnsatzFamily(BaseModel):
    family_id: str
    name: str                                          # "UCCSD", "HE", "EfficientSU2"
    num_qubits_range: tuple[int, int]
    num_repetitions_range: tuple[int, int]
    entanglement_patterns: list[str]                   # ["linear", "full", "circular"]
    parameter_count_formula: str | None = None         # 参数数量公式（用于复杂度估算）
```

### 5.2.1a Ansatz 资源缩放参考

| Ansatz | 参数数量 | 门深度 | 适用系统 | 备注 |
|--------|---------|--------|---------|------|
| UCCSD | O(n_occ² × n_virt²) | O(N⁴) | H₂, LiH (2-4 qubits) | 化学精度 ≤1.6 mHa |
| HEA | O(L × N) | O(L) | 中等分子 (4-12 qubits) | 易遭遇 barren plateau |
| ADAPT-VQE | 自适应增长 | 逐步增长 | 复杂分子 | 门增长受误差累积限制 |
| EfficientSU2 | O(L × N) | O(L) | 通用变分 | Qiskit 内置 |

对于 H₂O 等较大分子，必须使用活性空间选择将量子比特数控制在 4-12 范围内。
UCCSD 在 10+ qubits 时门深度可达数万，NISQ 设备上不可行。

搭配建议：
- H₂/LiH 基准：UCCSD + L-BFGS-B + Qiskit Aer
- 中等分子探索：HEA + SPSA + active_space=(2,4) + Quafu
- 复杂系统：ADAPT-VQE + QSteed VQPU selection

### 5.2.2 BackendFamily

```python
class BackendFamily(BaseModel):
    family_id: str
    platform: str
    chip_ids: list[str]                                # 该族包含的芯片 ID
    qubit_count_range: tuple[int, int]
    connectivity_topology: str                         # "grid", "heavy_hex", "all_to_all"
    simulator_equivalent: str | None = None            # 对应的模拟器后端
```

### 5.2.3 ErrorMitigationFamily

```python
class ErrorMitigationFamily(BaseModel):
    family_id: str
    strategies: list[str]                              # ["rem", "zne", "pauli_twirling"]
    combination: Literal["single", "stacked"]          # 单独还是叠加使用
    overhead_factor: float | None = None               # 采样开销倍数
```

## 5.3 Family 与 Study 的关系

Family 提供"有哪些选项"，Study 提供"在选项中怎么搜索"。

```
AnsatzFamily ──┐
BackendFamily ──┼──→ QComputeStudySpec.axes ──→ Study ──→ QComputeStudyReport
MitigationFamily┘        │
                          │
                    C×L×K 结构化
                          │
              ┌───────────┼───────────┐
              │           │           │
              C            L           K
         (并发候选数)  (评估深度)  (最终候选数)
```

### 5.3.1a C×L×K 资源配置参考

SimpleTES 在 C=32, L=100, K=16 设定下取得量子比特路由突破（SWAP 降低 24.5%）。
不同场景需要不同的资源配置策略：

| 场景 | C (并发) | L (迭代深度) | K (候选) | 评估成本 | 说明 |
|------|---------|-------------|---------|---------|------|
| 电路编译（模拟器） | 16-32 | 50-100 | 8-16 | 低（秒级） | 无噪声，可大规模搜索 |
| 电路编译（真机） | 4-8 | 10-20 | 2-4 | 高（分钟-小时级） | 有配额约束 |
| ansatz 结构搜索 | 8-16 | 20-50 | 4-8 | 中 | 结构变化影响深度 |
| 后端比较 | 4-8 | 1-5 | 2-4 | 高 | 每后端都消耗真机配额 |
| 错误缓解策略搜索 | 4-8 | 10-30 | 2-4 | 极高（采样开销 ×γ） | 叠加开销见 4.7.4 |

资源配置的动态自适应是远期优化目标——当前需人工设定，但 Study 组件的
`strategy="agentic"` 模式通过 BrainProvider 可部分实现自适应。

### 5.3.1 Study 与 Agent 的交互

当 `strategy="agentic"` 时，BrainProvider 接管 family 搜索：

1. **Propose**：Agent 从各 family 中选择候选组合，生成 `QComputeExperimentSpec` 实例
2. **Execute**：Study 组件通过 Gateway 编排每个 trial 的执行
3. **Evaluate**：Agent 评估 trial 结果，更新选择策略
4. **Refine**：基于 Pareto 前沿，Agent 提议新的候选区域

```
Study Component                         BrainProvider
     │                                        │
     ├─ request_proposals(history) ──────────→│
     │                                        │
     │←─ return proposals[N] ─────────────────┤
     │                                        │
     ├─ execute_all(proposals)                │
     │   └─ Gateway.run_baseline() × N        │
     │                                        │
     ├─ request_evaluation(results) ─────────→│
     │                                        │
     │←─ return scored_candidates ────────────┤
     │                                        │
     ├─ update_pareto_front()                 │
     │                                        │
     └─ loop (until convergence/budget) ──────┤
```

### 5.3.1b 历史轨迹管理（RPUCB）

当并发轨迹和迭代深度增加后，上下文窗口成为瓶颈。SimpleTES 提出 RPUCB
（Replay-Prioritized Upper Confidence Bound）策略解决此问题：

- 不将全部历史轨迹塞入 prompt（会导致上下文溢出）
- 将历史轨迹视为可调度资源池
- 在"高价值历史节点"和"低频潜力节点"之间做 explore-exploit 平衡
- 类似 UCB 的多臂老虎机策略，为每个历史节点维护价值估计和选择次数

在 QCompute Study 组件中的映射：
```python
def _select_trajectory_context(self, history: list[QComputeStudyTrial], max_prompt_tokens: int) -> list[dict]:
    """Select the most informative subset of history for the next BrainProvider call."""
    # Rank trials by: trajectory_score × exploration_bonus
    # exploration_bonus = sqrt(log(total_trials) / (times_selected + 1))
    # Include top-K within token budget
    ...
```

### 5.3.2 轨迹级评估（Trajectory-Level Evaluation）

SimpleTES 的核心方法论创新：不按单步 reward 优化，而看整条探索轨迹的最终效果。

#### 为什么轨迹级评估对量子计算很重要

量子实验的每一步（电路生成 → 编译 → 执行 → 验证）都有各自的局部指标，
但局部最优的串联不一定产生全局最优的探索路径：
- 一个"语法最简"的电路可能因 SWAP 过多导致保真度崩溃
- 一个"保真度最高"的编译可能因过度优化单次执行而浪费配额
- 一个"收敛最快"的 VQE 迭代可能因过早陷入局部能量极小点

#### 实现方法

1. **轨迹定义**：一次完整的 Study trial = 从初始电路到最终验证的完整过程
2. **评分目标**：只看整条轨迹最终达到的最高分，不按每步 reward 加权
3. **反馈方式**：用最终分反向监督整条路径——让 BrainProvider 学习"什么样的整条探索路径更可能成功"
4. **辅助机制**：
   - Replay buffer：保留 top-R% 轨迹供后续重放
   - 无效后缀截断：若轨迹后半段未改善结果，截断该部分
   - 轨迹多样性奖励：避免所有候选收敛到同一局部最优

#### 在 QCompute 中的实现路径

当前首版 Study 组件的 `QComputeStudyTrial.trajectory_score` 字段已预留轨迹级评分。
在 `agentic` 策略下，BrainProvider 的 `propose()` 调用应接收的不是单步状态，
而是完整的历史轨迹摘要（通过 RPUCB 选择的最有价值子集）。

远期可通过轨迹级后训练（Trajectory-Level Post-training）让模型直接学习
"成功的量子实验探索路径是什么样的"——这比单步 reward 优化更接近科学发现的本质。

## 5.4 Study 组件设计

**Slot**: `qcompute_study.primary`
**Capability**: `qcompute.study.run`

```python
class QComputeStudyComponent(HarnessComponent):
    async def run_study(self, study_spec: QComputeStudySpec) -> QComputeStudyReport: ...
    async def run_single_trial(self, spec: QComputeExperimentSpec) -> QComputeStudyTrial: ...
    async def evaluate_pareto_front(self, trials: list[QComputeStudyTrial], objective: str) -> list[str]: ...
```

### 5.4.1 Study 的执行维度

| 维度 | C (并发) | L (深度) | K (候选) | 说明 |
|------|---------|---------|---------|------|
| ansatz 搜索 | 多个 ansatz 类型并行 | 每个 ansatz 多 repetitions | Pareto 最优 ansatz | 结构搜索 |
| 后端比较 | 多个后端并行 | 每个后端多个 shots | 最佳性价比后端 | 硬件选择 |
| 编译策略 | 多种策略并行 | 每策略多轮优化 | 最优编译方案 | 编译优化 |
| 错误缓解 | 多种缓解组合 | 每组合多轮采样 | 最优缓解策略 | 噪声对抗 |

### 5.4.2 配额感知调度

真机执行的每日配额是硬约束。Study 组件需要配额感知：

```python
async def _schedule_trials(
    self, trials: list[QComputeExperimentSpec], daily_quota: int
) -> list[QComputeExperimentSpec]:
    """Prioritize trials: simulator-backed first, then real-hardware by estimated value."""
    sim_trials = [t for t in trials if t.backend.simulator]
    real_trials = [t for t in trials if not t.backend.simulator]
    real_trials.sort(key=lambda t: self._estimate_information_gain(t), reverse=True)
    return sim_trials + real_trials[:daily_quota]
```

### 5.4.3 SimpleTES 评估驱动闭环在 Study 中的体现

QCompute Study 组件是 SimpleTES C×L×K 范式在 MHE 中的直接实现载体：

| SimpleTES 概念 | QCompute Study 映射 | 说明 |
|---------------|-------------------|------|
| Generator | BrainProvider.propose() | 生成 C 个候选 experiment spec |
| Evaluator | QComputeValidator + Qiskit Aer | L 轮模拟器/真机评估 |
| Policy/Selector | QComputePolicy.evaluate() | 从 K 个终选中筛选最优 |
| RPUCB | `_select_trajectory_context()` | 历史轨迹的探索-利用平衡 |
| Trajectory Score | `QComputeStudyTrial.trajectory_score` | 整条路径的最终评分 |

关键区别：SimpleTES 原版使用 LLM 做 refiner，QCompute Study 使用的是 MHE 的
BrainProvider seam——这允许热替换不同的优化后端（RL 模型、LLM、经典优化器），
而不改变 Study 的执行框架。

## 5.5 Family 与 ABACUS 联动场景

经典 DFT (ABACUS) + 量子 NISQ 混合工作流的 family 设计示例：

```
AnsatzFamily("UCCSD", qubits=(4, 12), reps=(1, 3))
  × BackendFamily("quafu", chips=["Baihua"], qubits=(10, 18))
    × ErrorMitigationFamily("zne_only", strategies=["zne"])
```

Agent 在这个 family 网格中搜索：

1. ABACUS 产出分子哈密顿量（经典预处理）
2. QCompute Study 在 family 网格中搜索最优 VQE ansatz + 后端 + 错误缓解组合
3. 量子端计算基态能量
4. 与 ABACUS 的 DFT 能量对比
5. Agent 评估"经典 vs 量子"的精度-成本 tradeoff
6. 若量子结果优于 DFT 且成本可接受 → promotion；否则继续迭代

## 5.6 Family 的可扩展性

Family 系统设计为 open set：

- 新 ansatz 类型：新增 `AnsatzFamily` 实例 + 在 `QComputeCircuitSpec.ansatz` 中注册
- 新后端平台：新增 `BackendFamily` + 实现对应的执行适配器
- 新错误缓解策略：新增 `ErrorMitigationFamily` + 在 Executor 中实现策略
- 自定义 family：通过 `metadata` 字段携带任意扩展属性
