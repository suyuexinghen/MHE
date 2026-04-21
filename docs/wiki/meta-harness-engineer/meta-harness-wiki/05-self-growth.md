# 05. 自增长与 Optimizer

本章把 Meta-Harness 的"自增长"定义为一个受治理约束的优化闭环：由触发机制决定何时进入元循环，由搜索策略决定改哪里，由状态编码决定如何理解当前组件图，由动作漏斗决定改动风险边界，由奖励与收敛判据决定何时停止。

这里采用的术语与前文保持一致：**Optimizer** 是元层控制中枢，**Proposer** 负责提出候选改动，**ConnectionEngine** 负责装配后的图切换，**Policy/Governance** 负责 veto 与审计。

---

## 5.1 自增长不是"持续乱改"，而是受限元循环

自增长应理解为：系统在检测到性能停滞、结构失衡或任务分布变化后，进入一次受限的优化周期，对组件图、配置和局部实现进行搜索，并在验证后提交候选图版本。

```
trigger detected
  -> build optimizer state
  -> search candidate mutations
  -> validate candidate graph
  -> shadow / observe
  -> commit or rollback
```

因此，优化器不是常驻写配置的后台脚本，而是一个**按条件触发、按阶段推进、按证据收敛**的元控制器。

---

## 5.2 分层触发机制

触发机制建议做成分层门控，避免系统因为短时噪声而频繁进入高成本搜索。

### 5.2.1 三层触发源

| 层级 | 触发类型 | 典型信号 | 作用 |
| --- | --- | --- | --- |
| L1 运行层 | 局部异常触发 | 延迟飙升、工具失败率升高、某组件健康检查退化 | 触发参数微调或局部重接线 |
| L2 评估层 | 效能停滞触发 | Hypervolume 长时间无提升、成功率平台期 | 触发结构搜索 |
| L3 策略层 | 外部约束触发 | 新任务分布、SLA 变化、预算收缩、人类策略更新 | 触发模板替换或图重组 |

### 5.2.2 触发门控建议

```
raw signals
  -> debounce window
  -> significance filter
  -> budget check
  -> policy gate
  -> optimizer cycle starts
```

### 5.2.3 推荐触发条件

| 条件 | 建议阈值 |
| --- | --- |
| `ΔHV < ε` 连续多轮 | 见 5.10 参数表 |
| 关键组件局部失败率 | 最近窗口超过基线 2σ |
| 平均时延退化 | 超过 SLA 的 10%~20% |
| 成本升高无收益 | 单位成本收益连续下降 |
| 新任务簇出现 | 分布漂移指标超过阈值 |

### 5.2.4 五层修复策略（扩展参考）

在工程实现中，触发后可按从低成本到高成本的顺序依次尝试修复策略：

```
性能瓶颈检测: Pareto 前沿连续 K 轮无新点加入
      │
      ▼
Layer 1: 参数调整 (成本: 极低)
      │ 连续 N1 轮无效
      ▼
Layer 2: 连接重连 (成本: 低)
      │ 连续 N2 轮无效
      ▼
Layer 3: 模板实例化 (成本: 中)
      │ 连续 N3 轮无效
      ▼
Layer 4: 受限代码生成 (成本: 高)
      │ 连续 N4 轮无效
      ▼
Layer 5: 行为策略学习 (成本: 很高)
```

```python
# 每层的无效轮数阈值（建议值，可由 Optimizer 根据任务类型动态调整）
LAYER_THRESHOLDS = {
    "parameter_adjustment": 5,
    "connection_rewiring": 3,
    "template_instantiation": 3,
    "code_generation": 2,
}
```

---

## 5.3 三阶段搜索策略

优化器不应在一开始就进入高自由度代码生成。推荐使用**由浅入深**的三阶段搜索策略，以保证样本效率与系统稳定性。

### 5.3.1 Phase A：局部参数搜索

适用对象：已有结构基本合理，只是阈值、温度、队列长度、缓存策略等配置需要微调。

| 特征 | 内容 |
| --- | --- |
| 搜索对象 | XML 参数、枚举选项、阈值 |
| 成本 | 低 |
| 风险 | 低 |
| 退出条件 | 连续若干轮无显著收益 |

### 5.3.2 Phase B：拓扑与模板搜索

适用对象：局部调参已无效，需要重接线、替换组件实现或实例化新模板。

| 特征 | 内容 |
| --- | --- |
| 搜索对象 | Connection 重接线、slot rebinding、模板实例化 |
| 成本 | 中 |
| 风险 | 中 |
| 关键技术 | contract-driven pruning、candidate graph assembly |

### 5.3.3 Phase C：受限合成搜索

适用对象：前两阶段均无法突破，需要在受限模板槽位中做局部代码补全。

| 特征 | 内容 |
| --- | --- |
| 搜索对象 | 模板槽位、受限逻辑片段 |
| 成本 | 高 |
| 风险 | 高 |
| 护栏 | 静态检查、单测、沙箱、Policy veto |

### 5.3.4 搜索升级规则

```
Phase A stagnates
  -> Phase B if legal structural candidates exist
Phase B stagnates
  -> Phase C only if template-bounded synthesis is available
Phase C fails or regresses
  -> rollback and reduce exploration radius
```

### 5.3.5 进化搜索 + 贝叶斯优化（Phase A/B 首选）

**适用阶段**：系统早期，数据量不足时。

#### 进化策略（ES）

```python
class EvolutionarySearch:
    """进化搜索策略。"""

    def __init__(self, config: EvolutionConfig) -> None:
        self.population_size = config.population_size
        self.mutation_rate = config.mutation_rate
        self.crossover_rate = config.crossover_rate
        self.elite_ratio = config.elite_ratio
        self.population: list[CandidateConfig] = []

    async def evolve(
        self,
        current_graph: ComponentGraph,
        pareto_front: ParetoFront,
        fitness_fn: Callable[[CandidateConfig], float],
    ) -> list[PendingMutation]:
        """执行一轮进化搜索，返回候选变更列表。"""
        if not self.population:
            self.population = self._seed_population(current_graph)

        fitness_scores = [(c, await fitness_fn(c)) for c in self.population]
        survivors = self._pareto_selection(fitness_scores)
        offspring = self._mutate(survivors, current_graph)
        crossed = self._crossover(offspring)
        self.population = survivors + crossed

        return [c.to_mutation() for c in self.population[:self.population_size]]

    def _mutate(
        self,
        candidates: list[CandidateConfig],
        graph: ComponentGraph,
    ) -> list[CandidateConfig]:
        """对候选配置进行变异。"""
        offspring = []
        for candidate in candidates:
            if random.random() < self.mutation_rate:
                mutation_type = random.choice([
                    "param_perturbation",
                    "connection_add",
                    "connection_remove",
                    "param_swap",
                    "template_instantiate",
                ])
                mutated = self._apply_mutation(candidate, mutation_type, graph)
                if mutated:
                    offspring.append(mutated)
        return offspring
```

#### 多目标贝叶斯优化（MOBO）

```python
class BayesianOptimizer:
    """多目标贝叶斯优化。"""

    def __init__(self, config: BayesianConfig) -> None:
        self.surrogate_models: dict[str, GaussianProcessRegressor] = {}
        self.acquisition_fn = ExpectedHypervolumeImprovement()
        self.observations: list[tuple[ConfigVector, PerformanceVector]] = []

    async def suggest(
        self,
        search_space: SearchSpace,
        pareto_front: ParetoFront,
        reference_point: PerformanceVector,
    ) -> PendingMutation:
        """建议下一个探索点。"""
        ...
```

**适用条件**：配置空间维度较低（< 30 维）、评估成本高时。

### 5.3.6 LLM-based Proposer（Phase C 代码级搜索）

与 ADAS 方法对齐。让 LLM 作为提议器（Proposer），基于历史执行轨迹诊断失败并生成新候选配置。

```python
class LLMProposer:
    """基于 LLM 的候选配置提议器。"""

    async def propose(
        self,
        current_config: CandidateConfig,
        failed_traces: list[Trace],
        pareto_front: ParetoFront,
        template_library: TemplateLibrary,
    ) -> PendingMutation:
        """基于失败诊断提出新候选。"""
        prompt = self._build_diagnosis_prompt(
            current_config=current_config,
            failed_traces=failed_traces,
            pareto_front=pareto_front,
        )
        response = await self._llm.chat_json(
            messages=[
                {"role": "system", "content": PROPOSER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ]
        )
        mutation = self._parse_proposal(response, template_library)
        errors = self._static_validate(mutation)
        if errors:
            return await self._retry_with_errors(response, errors)
        return mutation
```

**Meta-Harness 论文的关键发现**：proposer 每轮中位数读取 82 个文件，其中约 41% 是旧 harness 代码，40% 是执行轨迹。**保留原始执行轨迹中的诊断细节**比精致的摘要更有效。

### 5.3.7 RL 增强（可选）

**适用阶段**：系统积累足够运行数据后（候选配置评估记录达数百条以上）。

> **非马尔可夫性说明**：Optimizer 的状态 \(s_t\) 包含当前 Pareto 前沿 \(\mathcal{F}_t\)，而 \(\mathcal{F}_t\) 本身是 Optimizer 历史决策的累积结果。这意味着状态转移不满足 Markov 性：
>
> $$P(s_{t+1} | s_t, a_t, s_{t-1}, a_{t-1}, ...) \neq P(s_{t+1} | s_t, a_t)$$
>
> 基于 MDP 假设的标准 RL 算法（如 PPO）的理论收敛保证不再成立。在实践中，这意味着：
>
> 1. RL 策略可能产生次优决策
> 2. 训练可能不稳定
> 3. 需要更保守的学习率和更大的经验缓冲区
>
> 因此，RL 被定位为**可选增强**而非核心依赖。

---

## 5.4 非马尔可夫 RL 的现实约束

严格来说，Meta-Harness 优化并不是一个干净的马尔可夫决策过程。原因很直接：

- 当前性能取决于长历史运行轨迹，而不是只取决于当前 XML；
- 候选图的收益依赖任务分布、缓存状态、历史失败模式；
- 同一个动作在不同历史上下文下可能产生不同效果；
- 评估噪声和外部 API 波动会破坏"状态充分性"。

因此，本书建议把优化器理解为**带历史记忆、带日志诊断、带离线证据缓存的近似 RL / search 混合器**，而不是纯粹的在线 MDP 求解器。

### 5.4.1 工程含义

| 假设 | 在 Meta-Harness 中的问题 | 对策 |
| --- | --- | --- |
| 马尔可夫性 | 当前图不足以概括全部历史 | 把轨迹摘要与历史统计并入状态 |
| 平稳环境 | 任务分布与成本模型会变 | 使用滑动窗口与分布漂移检测 |
| 即时奖励可信 | 单轮得分噪声大 | 做重复评估与统计显著性检验 |
| 动作独立评估 | 动作存在长期耦合 | 用 graph version 跟踪延迟效应 |

结论是：优化器可以借鉴 RL，但不能把 RL 教科书中的假设原封不动带进系统工程实现。

---

## 5.5 GIN 拓扑编码

> **实现对齐说明（当前 MHE）**：这一节主要描述目标优化器状态编码方向。当前仓库尚未把 GIN / PyG 拓扑编码接入 `OptimizerComponent` 主循环；已落地的是 triggers、fitness、negative-reward loop、dead-end detection、triple convergence，以及离散动作上的轻量 Bayesian 优化器。

优化器的输入状态至少应包含三部分：

\[
s_t = \{ \mathrm{Embed}(G_t), \mathrm{Embed}(\tau_t), \mathbf{m}_t \}
\]

其中：

- `Embed(G_t)`：当前组件图拓扑嵌入；
- `Embed(τ_t)`：近期轨迹与失败模式摘要；
- `m_t`：手工统计特征，如成本、延迟、成功率、组件数、图深度。

在图嵌入部分，推荐使用 GIN（Graph Isomorphism Network），原因不是"它最流行"，而是它对小规模异构组件图的结构分辨能力更强，适合识别 fan-in / fan-out、闭环反馈与关键调度节点。

### 5.5.1 GIN 更新公式

\[
h_v^{(k)} = \mathrm{MLP}^{(k)}\left((1 + \epsilon^{(k)}) h_v^{(k-1)} + \sum_{u \in \mathcal{N}(v)} h_u^{(k-1)}\right)
\]

其中：

- `h_v^{(k)}` 是节点 `v` 在第 `k` 层的表示；
- `ε^{(k)}` 控制自环保留强度；
- 邻居聚合采用求和而不是平均，从而保留节点度与结构差异。

### 5.5.2 节点特征建议

| 特征类别 | 示例 |
| --- | --- |
| 类型特征 | `Planner`、`Memory`、`Evaluator` one-hot |
| 配置特征 | 参数哈希、阈值桶化、策略枚举 |
| 运行特征 | 延迟、局部成功率、错误率 |
| 治理特征 | 是否 protected、是否允许热切换 |
| 拓扑特征 | 入度、出度、层级、是否在关键路径 |

### 5.5.3 PyG 伪代码

```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import GINConv, global_add_pool


class ComponentGIN(torch.nn.Module):
    """GIN-based component graph encoder."""

    def __init__(
        self,
        node_dim: int = 32,
        hidden_dim: int = 64,
        num_layers: int = 3,
        output_dim: int = 128,
    ) -> None:
        super().__init__()
        self.node_dim = node_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        self.node_encoder = torch.nn.Linear(node_dim, hidden_dim)
        self.gin_layers = torch.nn.ModuleList()
        self.batch_norms = torch.nn.ModuleList()
        for _ in range(num_layers):
            mlp = torch.nn.Sequential(
                torch.nn.Linear(hidden_dim, hidden_dim),
                torch.nn.ReLU(),
                torch.nn.Linear(hidden_dim, hidden_dim),
            )
            self.gin_layers.append(GINConv(mlp, train_eps=True))
            self.batch_norms.append(torch.nn.BatchNorm1d(hidden_dim))

        self.readout_proj = torch.nn.Linear(
            hidden_dim * (num_layers + 1), output_dim
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        batch: torch.Tensor,
    ) -> torch.Tensor:
        h = self.node_encoder(x)
        layer_outputs = [global_add_pool(h, batch)]

        for i in range(self.num_layers):
            h = self.gin_layers[i](h, edge_index)
            h = self.batch_norms[i](h)
            h = F.relu(h)
            layer_outputs.append(global_add_pool(h, batch))

        h_graph = torch.cat(layer_outputs, dim=-1)
        return self.readout_proj(h_graph)
```

### 5.5.4 节点特征编码

```python
def encode_node_features(component: ComponentSpec) -> torch.Tensor:
    """Encode component as node feature vector."""
    features = torch.zeros(32)

    type_idx = COMPONENT_TYPE_INDEX[component.base_type]
    features[type_idx] = 1.0

    for cap in component.capabilities:
        if cap in CAPABILITY_INDEX:
            features[9 + CAPABILITY_INDEX[cap]] = 1.0

    features[30] = 1.0 if component.protected else 0.0
    features[31] = min(len(component.inputs) / 10.0, 1.0)

    return features
```

---

## 5.6 状态编码方案对比

| 方案 | 优点 | 缺点 | 适用判断 |
| --- | --- | --- | --- |
| 邻接矩阵 + MLP | 实现最简单 | 不具置换不变性，难适应变长图 | 只适合原型实验 |
| 手工拓扑指纹 | 可解释性高 | 表达能力有限 | 可作为辅助特征 |
| GCN / GAT | 社区成熟 | 小图上易过平滑，结构分辨率一般 | 可作为 baseline |
| GIN | 结构辨识力强，适合小异构图 | 需要图数据管线 | 推荐默认方案 |
| 纯 LLM 文本编码 | 无需额外模型 | 成本高，在线推理不稳定 | 适合离线分析，不适合主状态编码 |

建议实现上采用：**GIN 拓扑嵌入 + 手工统计特征 + 历史轨迹摘要** 的混合状态。

---

## 5.7 四层动作漏斗

动作空间必须比状态空间更严格，因为真实系统的改动成本与失败代价远高于模型训练中的单步试错。推荐使用四层动作漏斗，从低风险到高风险逐级放行。

| 层级 | 动作类型 | 示例 | 护栏 |
| --- | --- | --- | --- |
| L1 参数微调 | 调整现有参数 | `temperature`, `top_k`, `timeout` | 参数范围、预算上限 |
| L2 连接重构 | 增删边、改优先级、改路由模式 | 增加 evaluator 反馈边 | contract-driven pruning |
| L3 模板实例化 | 引入新模板或替换实现 | 加入 `SemanticChunker` | slot/capability 校验 |
| L4 受限合成 | 在模板槽位内生成局部逻辑 | 自定义评分函数 | sandbox + tests + Policy veto |

### 5.7.1 漏斗式放行原则

```
cheap and safe actions first
  -> structural actions second
  -> template actions third
  -> synthesis only as last resort
```

### 5.7.2 为什么要漏斗化

| 如果不做漏斗 | 典型后果 |
| --- | --- |
| 一上来就高自由度生成 | 搜索半径过大，回归率飙升 |
| 结构改动过于频繁 | 难以定位收益来源 |
| 缺少逐层退火 | 样本预算迅速耗尽 |

---

## 5.8 奖励函数与 fitness 设计

优化器不应只追求单一准确率，而应把质量、成本、复杂度、稳定性一起纳入 fitness。

> **实现对齐说明（当前 MHE）**：当前 `optimizer/fitness.py` 已实现可解释的标量 fitness 聚合（`success / efficiency / safety / novelty / penalties`），并记录历史；但 `Pareto front` / `hypervolume` 仍主要停留在文档目标层，而不是当前核心代码里的主评估机制。

### 5.8.1 推荐 reward 形式

\[
R_t = \alpha \cdot \Delta Q_t + \beta \cdot \Delta HV_t - \lambda_c \cdot \Delta C_t - \lambda_k \cdot \Delta K_t - \lambda_r \cdot \mathrm{RegressRisk}_t
\]

其中：

- `ΔQ_t`：核心任务质量提升；
- `ΔHV_t`：Pareto 超体积增量；
- `ΔC_t`：成本或时延增加；
- `ΔK_t`：复杂度增加，如组件数、边数、图深度；
- `RegressRisk_t`：回归风险估计。

### 5.8.2 Fitness 维度建议

| 维度 | 说明 |
| --- | --- |
| 质量 | 成功率、正确率、任务完成率 |
| 效率 | 延迟、token 消耗、工具调用次数 |
| 稳定性 | 方差、失败尾部风险、回归率 |
| 复杂度 | 组件数、连接数、关键路径长度 |
| 可治理性 | protected 改动次数、审计负担 |

### 5.8.3 实践建议

- 奖励评估必须带 `graphVersion`，避免把不同候选图的结果混在一起；
- 对高噪声任务优先看分布统计，而不是单次最好成绩；
- 对复杂度使用显式惩罚，避免系统无限膨胀。

### 5.8.4 进化搜索阶段的适应度函数

\[
\text{fitness}(c) = \Delta HV(c) - \lambda \cdot \Delta_{\text{complexity}}(c)
\]

其中：
- \(\Delta HV(c) = HV(\mathcal{F}_{t+1}, \mathbf{r}) - HV(\mathcal{F}_t, \mathbf{r})\) 是 Pareto 超体积增量
- \(\Delta_{\text{complexity}}(c)\) 是新配置相对于旧配置的复杂度增量

复杂度度量：

\[
\Delta_{\text{complexity}}(c) = w_1 \cdot \Delta n_{\text{components}} + w_2 \cdot \Delta n_{\text{connections}} + w_3 \cdot \Delta d_{\text{max\_depth}}
\]

其中 \(w_1, w_2, w_3\) 是权重系数，默认值 \(w_1 = 1.0, w_2 = 0.5, w_3 = 2.0\)。

### 5.8.5 RL 增强阶段的奖励塑形

```python
def compute_reward(
    mutation: PendingMutation,
    validation_result: ValidationResult,
    old_hv: float,
    new_hv: float,
    old_complexity: float,
    new_complexity: float,
) -> float:
    """计算 Optimizer 动作的奖励值。"""
    hv_delta = new_hv - old_hv
    complexity_delta = new_complexity - old_complexity
    base_reward = hv_delta - LAMBDA_COMPLEXITY * complexity_delta

    rewards = {
        "static_validation_passed": +0.1,
        "sandbox_regression_passed": +0.3,
        "ab_test_significantly_better": +1.0,
        "policy_veto_triggered": -2.0,
        "sandbox_execution_failed": -1.0,
        "rollback_triggered": -1.5,
    }

    total = base_reward
    if validation_result.static_passed:
        total += rewards["static_validation_passed"]
    if validation_result.sandbox_passed:
        total += rewards["sandbox_regression_passed"]
    if validation_result.ab_passed:
        total += rewards["ab_test_significantly_better"]
    if validation_result.policy_vetoed:
        total += rewards["policy_veto_triggered"]
    if validation_result.sandbox_failed:
        total += rewards["sandbox_execution_failed"]
    if validation_result.rolled_back:
        total += rewards["rollback_triggered"]

    return total
```

---

## 5.9 三重收敛判据

当前实现已经落地三重收敛控制，但其判据是 **`fitness plateau` / `budget exhausted` / `safety floor met`**。因此这里的 `ΔHV < ε` 叙事应理解为目标研究表达，而不是当前代码中的精确判据。

### 5.9.1 判据一：超体积收敛

当连续 `K` 轮满足 `ΔHV < ε_t`，说明系统已接近收益递减区间。

### 5.9.2 判据二：统计显著性收敛

对当前 top-k 候选与现有最优版本做重复评估。如果在重复运行后，配对 t 检验或 Wilcoxon 检验长期无法拒绝"性能无显著差异"的原假设，则停止继续扩张。

### 5.9.3 判据三：复杂度饱和

当组件数、连接深度、延迟或预算达到上限，即便还有边际性能提升，也应停止增长。这是防止"收益很小但结构越来越重"的硬约束。

### 5.9.4 收敛判据表

| 判据 | 信号 | 推荐动作 |
| --- | --- | --- |
| HV 收敛 | `ΔHV < ε_t` 连续 `K` 轮 | 降低探索率或停止 |
| 显著性收敛 | `p > α` 连续多轮 | 停止扩张，保留当前 elite |
| 复杂度饱和 | 达到组件/深度/SLA/预算上限 | 强制停止并锁定结构 |

### 5.9.5 收敛决策流程

```
每轮 MetaCycle 结束后:
     │
     ▼
HV 变化 < ε 连续 K 轮?
├── Yes → 收敛 (准则1) → 停止重长
└── No → 统计检验 p > α 连续 K 轮?
         ├── Yes → 收敛 (准则2) → 停止重长
         └── No → 复杂度触及上限?
                  ├── Yes → 强制停止 (准则3) → 锁定当前最优
                  └── No → 继续重长

安全网: 迭代次数 ≥ T_max?
└── Yes → 强制停止, 输出当前 Pareto 前沿
```

---

## 5.10 自适应 epsilon

固定 `ε` 很容易在不同任务域上失灵。建议使用自适应 `ε_t` 来判断"收益是否足够大到值得继续搜索"。

### 5.10.1 一种简单实现

\[
\epsilon_t = \max(\epsilon_{min}, c \cdot \hat{\sigma}_{HV,t})
\]

其中：

- `σ̂_{HV,t}` 是最近窗口内超体积增量的标准差；
- `c` 是灵敏度系数；
- `ε_min` 防止阈值收缩到零。

### 5.10.2 工程解释

| 场景 | 自适应 epsilon 的效果 |
| --- | --- |
| 高噪声任务 | 自动放宽停机阈值，避免误判进步 |
| 低噪声任务 | 自动收紧阈值，提升搜索精度 |
| 分布漂移后 | 可随新窗口动态重估 |

### 5.10.3 自适应收敛阈值实现

```python
class AdaptiveEpsilon:
    """自适应收敛阈值。"""

    def __init__(
        self,
        window: int = 5,
        epsilon_min: float = 0.001,
        multiplier: float = 2.0,
    ) -> None:
        self.window = window
        self.epsilon_min = epsilon_min
        self.multiplier = multiplier
        self.hv_history: list[float] = []

    def update(self, hv: float) -> None:
        """记录新的 HV 值。"""
        self.hv_history.append(hv)
        if len(self.hv_history) > self.window * 2:
            self.hv_history = self.hv_history[-(self.window * 2):]

    def get_epsilon(self) -> float:
        """计算当前自适应阈值。"""
        if len(self.hv_history) < self.window + 1:
            return float("inf")

        deltas = [
            self.hv_history[i] - self.hv_history[i - 1]
            for i in range(-self.window, 0)
        ]
        mean_delta = sum(deltas) / len(deltas)
        variance = sum((d - mean_delta) ** 2 for d in deltas) / (len(deltas) - 1)
        sigma = variance ** 0.5
        return max(self.epsilon_min, self.multiplier * sigma)

    def is_converged(self) -> bool:
        """判断是否收敛。"""
        if len(self.hv_history) < self.window + 1:
            return False
        epsilon = self.get_epsilon()
        recent_deltas = [
            abs(self.hv_history[i] - self.hv_history[i - 1])
            for i in range(-self.window, 0)
        ]
        return all(d < epsilon for d in recent_deltas)

    def adjust_for_task_type(self, task_type: str) -> None:
        """根据任务类型调整参数。"""
        params = CONVERGENCE_PARAMS.get(task_type, CONVERGENCE_PARAMS["default"])
        self.window = params["K"]
        self.epsilon_min = params["epsilon"] * 0.1
        self.multiplier = 2.0
```

---

## 5.11 收敛参数速查表

下表用于给不同任务类型设置优化器的初始参数。实际部署时仍应结合任务噪声与预算做校准。

| 任务类型 | `K` 连续轮次 | `ε_min` | `α` 显著性 | `λ_c` 成本惩罚 | `λ_k` 复杂度惩罚 | 重复评估次数 |
| --- | --- | --- | --- | --- | --- | --- |
| 逻辑推理 | 8-12 | 0.0005 | 0.01 | 0.05 | 0.05 | 10+ |
| 代码生成 | 5-8 | 0.0010 | 0.05 | 0.10 | 0.15 | 5+ |
| 分类任务 | 3-5 | 0.0050 | 0.05 | 0.20 | 0.30 | 3+ |
| 多轮工具调用 | 10+ | 0.0001 | 0.01 | 0.10 | 0.10 | 15+ |

不同任务类型的推荐收敛参数（扩展）：

| 参数 | 符号 | 文本分类 | 数学推理 | 代码生成 | 多轮对话 | 开放研究 |
|------|------|---------|---------|---------|---------|---------|
| 收敛窗口 | \(K\) | 5 | 3 | 5 | 8 | 10 |
| HV 阈值 | \(\varepsilon\) | 0.01 | 0.02 | 0.01 | 0.005 | 0.003 |
| 显著性水平 | \(\alpha\) | 0.05 | 0.10 | 0.05 | 0.05 | 0.10 |
| 复杂度惩罚 | \(\lambda\) | 0.1 | 0.2 | 0.15 | 0.1 | 0.05 |
| 最大组件数 | \(N_{\max}\) | 15 | 12 | 15 | 20 | 25 |
| 最大深度 | \(D_{\max}\) | 5 | 4 | 5 | 6 | 8 |
| 最大迭代 | \(T_{\max}\) | 100 | 50 | 100 | 200 | 500 |
| 人工审查间隔 | \(N_{\text{review}}\) | 20 | 10 | 20 | 50 | 100 |
| 影子流量比例 | — | 10% | 20% | 10% | 5% | 5% |
| 最小样本量 | — | 34 | 20 | 34 | 50 | 100 |
| 观察窗口（秒） | — | 300 | 180 | 300 | 600 | 900 |

---

## 5.12 最小可行 Proposer

在 Meta-Harness 中，不需要一开始就实现一个"全知全能"的优化智能体。更合理的是先做一个**最小可行 Proposer（MVP）**，聚焦于日志诊断、差异分析和局部补丁生成。

### 5.12.1 MVP 组成

| 组件 | 作用 | 输出 |
| --- | --- | --- |
| `LogGopher` | 聚合 trace、metrics、失败摘要 | 结构化诊断上下文 |
| `DiffAnalyzer` | 对比 elite 与失败候选的 XML / graph diff | 改动建议与归因 |
| `XMLPatcher` | 生成 XPath 粒度的局部 patch | 候选 XML 增量 |

### 5.12.2 MVP 工作流

```
read latest graphVersion results
  -> summarize failures and regressions
  -> compare elite vs failed candidates
  -> propose small XML patch
  -> send candidate to validation pipeline
```

### 5.12.3 为什么先做 MVP

| 先做 MVP 的收益 | 说明 |
| --- | --- |
| 风险低 | 不需要一开始就接入全量代码生成 |
| 样本效率高 | 优先利用已有日志与失败案例 |
| 易于审计 | 每次 proposal 都是局部可读 patch |
| 便于治理 | 可与 Policy 和 ConnectionEngine 清晰解耦 |

### 5.12.4 Log Gopher（日志挖掘器）

```python
class LogGopher:
    """从 Memory 中检索和提取执行轨迹关键信息。"""

    def __init__(self, memory: MemoryInterface) -> None:
        self._memory = memory

    async def mine_failure_patterns(
        self,
        component_id: str | None = None,
        limit: int = 10,
    ) -> FailurePatternReport:
        """挖掘失败模式。"""
        traces = await self._memory.get_failed_traces(
            component=component_id,
            limit=limit,
        )
        patterns: dict[str, int] = {}
        component_errors: dict[str, list[str]] = {}

        for trace in traces:
            reason = self._extract_failure_reason(trace)
            patterns[reason] = patterns.get(reason, 0) + 1
            for step in trace.steps:
                if step.status == "error":
                    comp = step.component_id
                    component_errors.setdefault(comp, []).append(step.error_message)

        return FailurePatternReport(
            total_failures=len(traces),
            pattern_distribution=patterns,
            component_errors=component_errors,
        )

    async def mine_performance_trends(
        self,
        metric: str = "accuracy",
        window: int = 20,
    ) -> PerformanceTrend:
        """挖掘性能趋势。"""
        traces = await self._memory.search_traces(
            keyword="performance_vector",
            time_range=TimeRange.last_n_tasks(window),
        )
        values = [t.get_metric(metric) for t in traces if t.has_metric(metric)]
        if len(values) < 3:
            return PerformanceTrend(insufficient_data=True)

        trend_direction = "improving" if values[-1] > values[0] else "degrading"
        trend_magnitude = abs(values[-1] - values[0]) / max(values[0], 0.001)
        is_stagnant = all(abs(v - values[0]) < 0.01 for v in values[-5:])

        return PerformanceTrend(
            direction=trend_direction,
            magnitude=trend_magnitude,
            is_stagnant=is_stagnant,
            recent_values=values[-10:],
        )
```

### 5.12.5 Diff Analyzer（差异分析器）

```python
class DiffAnalyzer:
    """分析配置差异和失败原因，生成修复建议。"""

    async def diagnose(
        self,
        current_config: str,
        failure_report: FailurePatternReport,
        performance_trend: PerformanceTrend,
    ) -> list[RepairSuggestion]:
        """基于失败模式生成修复建议。"""
        suggestions: list[RepairSuggestion] = []

        for component_id, errors in failure_report.component_errors.items():
            if len(errors) >= 3:
                suggestions.append(RepairSuggestion(
                    type="component_replace",
                    target=component_id,
                    reason=f"Component '{component_id}' failed {len(errors)} times",
                    action="Consider replacing with alternative template",
                    confidence=0.7,
                ))

        if performance_trend.is_stagnant:
            suggestions.append(RepairSuggestion(
                type="connection_rewire",
                target="global",
                reason="Performance stagnation detected over recent tasks",
                action="Consider adding ContextPruner or adjusting Memory parameters",
                confidence=0.6,
            ))

        if "context_overflow" in failure_report.pattern_distribution:
            count = failure_report.pattern_distribution["context_overflow"]
            suggestions.append(RepairSuggestion(
                type="param_adjustment",
                target="Memory_1",
                reason=f"Context overflow occurred {count} times",
                action="Reduce window_size or enable summarization strategy",
                confidence=0.8,
                suggested_params={"window_size": "8", "strategy": "hybrid"},
            ))

        if "execution_timeout" in failure_report.pattern_distribution:
            count = failure_report.pattern_distribution["execution_timeout"]
            suggestions.append(RepairSuggestion(
                type="param_adjustment",
                target="Runtime_1",
                reason=f"Execution timeout occurred {count} times",
                action="Increase max_retries or adjust timeout parameters",
                confidence=0.75,
                suggested_params={"max_retries": "5", "retry_delay_ms": "2000"},
            ))

        return sorted(suggestions, key=lambda s: s.confidence, reverse=True)
```

### 5.12.6 XML Patcher（XML 补丁生成器）

```python
class XMLPatcher:
    """根据修复建议生成 XML 配置补丁。"""

    async def patch(
        self,
        current_xml: str,
        suggestion: RepairSuggestion,
    ) -> PendingMutation:
        """根据修复建议生成 PendingMutation。"""
        tree = ET.fromstring(current_xml)

        if suggestion.type == "param_adjustment":
            return self._patch_params(tree, suggestion)
        elif suggestion.type == "connection_rewire":
            return self._patch_connection(tree, suggestion)
        elif suggestion.type == "component_replace":
            return self._patch_component(tree, suggestion)
        else:
            raise ValueError(f"Unknown suggestion type: {suggestion.type}")

    def _patch_params(
        self, tree: ET.Element, suggestion: RepairSuggestion
    ) -> PendingMutation:
        """生成参数调整补丁。"""
        mutations = []
        target_component = self._find_component(tree, suggestion.target)
        config = target_component.find("Config")
        if config is None:
            config = ET.SubElement(target_component, "Config")

        for param_name, param_value in suggestion.suggested_params.items():
            param = config.find(f"Param[@name='{param_name}']")
            if param is not None:
                old_value = param.get("value")
                param.set("value", param_value)
            else:
                param = ET.SubElement(config, "Param")
                param.set("name", param_name)
                param.set("value", param_value)
                old_value = None

            mutations.append({
                "type": "modify_param",
                "target": suggestion.target,
                "param": param_name,
                "old_value": old_value,
                "new_value": param_value,
            })

        return PendingMutation(
            mutation_id=f"mvp_{int(time.time())}",
            mutation_type="modify_param",
            target=suggestion.target,
            params={"changes": mutations},
            proposed_by="mvp_proposer",
        )

    def _patch_connection(
        self, tree: ET.Element, suggestion: RepairSuggestion
    ) -> PendingMutation:
        """生成连接变更补丁。"""
        connections = tree.find("Connections")
        new_conn = ET.SubElement(connections, "Connection")
        new_conn.set("from", suggestion.suggested_params.get("from", ""))
        new_conn.set("to", suggestion.suggested_params.get("to", ""))
        new_conn.set("trigger", suggestion.suggested_params.get("trigger", ""))

        return PendingMutation(
            mutation_id=f"mvp_{int(time.time())}",
            mutation_type="add_connection",
            target="global",
            params=suggestion.suggested_params,
            proposed_by="mvp_proposer",
        )

    def _patch_component(
        self, tree: ET.Element, suggestion: RepairSuggestion
    ) -> PendingMutation:
        """生成组件替换补丁。"""
        return PendingMutation(
            mutation_id=f"mvp_{int(time.time())}",
            mutation_type="replace_component",
            target=suggestion.target,
            params={
                "new_type": suggestion.suggested_params.get("new_type", ""),
                "slot": suggestion.suggested_params.get("slot", ""),
            },
            proposed_by="mvp_proposer",
        )
```

### 5.12.7 MVP 完整流程

```python
class MVPProposer:
    """最小可行 Proposer——用于端到端验证自修改流程。"""

    def __init__(self, memory: MemoryInterface, template_lib: TemplateLibrary) -> None:
        self.gopher = LogGopher(memory)
        self.analyzer = DiffAnalyzer()
        self.patcher = XMLPatcher()

    async def propose_cycle(
        self,
        current_xml: str,
        component_id: str | None = None,
    ) -> list[PendingMutation]:
        """执行一轮 MVP 提议循环。"""
        failures = await self.gopher.mine_failure_patterns(
            component_id=component_id,
            limit=10,
        )
        trends = await self.gopher.mine_performance_trends(
            metric="accuracy",
            window=20,
        )
        suggestions = await self.analyzer.diagnose(
            current_config=current_xml,
            failure_report=failures,
            performance_trend=trends,
        )

        mutations: list[PendingMutation] = []
        for suggestion in suggestions[:3]:
            mutation = await self.patcher.patch(current_xml, suggestion)
            mutations.append(mutation)

        return mutations
```

---

## 5.13 推荐实现骨架

```python
class Optimizer:
    async def run_cycle(self, active_graph_version: int) -> "OptimizationResult":
        state = await self.build_state(active_graph_version)
        trigger = self.trigger_gate.evaluate(state)
        if not trigger.fire:
            return OptimizationResult.skipped("no_trigger")

        phase = self.search_scheduler.select_phase(state)
        action = await self.proposer.propose(state=state, phase=phase)
        candidate = await self.assembler.build_candidate(action)
        report = await self.validator.validate(candidate)
        if not report.ok:
            return OptimizationResult.rejected(report.errors)

        evaluation = await self.shadow_runner.evaluate(candidate)
        decision = self.convergence_controller.decide(evaluation)
        if decision.commit:
            new_version = await self.committer.commit(candidate)
            return OptimizationResult.committed(new_version)
        return OptimizationResult.rolled_back(decision.reason)
```

---

## 5.14 落地顺序建议

| 优先级 | 先做什么 | 为什么 |
| --- | --- | --- |
| P0 | 分层触发门控 | 决定何时进入元循环 |
| P0 | 三阶段搜索调度器 | 决定先调参还是改结构 |
| P1 | GIN + 手工特征混合状态 | 决定优化器是否能理解组件图 |
| P1 | 四层动作漏斗 | 决定改动风险边界 |
| P1 | reward / fitness / convergence controller | 决定何时停机 |
| P2 | 最小可行 Proposer | 决定 proposal 的实际生成能力 |

一句话概括：**Meta-Harness 的自增长在当前实现中，已经具备 proposal-only authority、分层触发、标量 fitness、dead-end/negative-reward 反馈、三重收敛与离散 Bayesian 搜索；而 GIN 编码、Pareto/frontier 主导评估和更强代码合成仍属于下一阶段演进方向。**
