# 07. 范围与分工

## 7.1 QCompute 的职责边界

### 7.1.1 QCompute 负责的

| 职责 | 组件 | 说明 |
|------|------|------|
| 量子实验规格校验 | Gateway | 校验 `QComputeExperimentSpec` 的完整性与合法性 |
| 后端探测与噪声采集 | Environment | 查询 Quafu/Qiskit Aer 状态、获取校准数据 |
| 电路编译与 transpilation | ConfigCompiler | 逻辑电路→物理电路映射、SWAP 优化、门分解 |
| 量子任务提交与结果收集 | Executor | 通过 SDK 提交任务、管理生命周期、捕获输出 |
| 验证与保真度评估 | Validator | 完整性、统计显著性、保真度、噪声影响评分 |
| 证据打包 | Evidence | 构建 `QComputeEvidenceBundle` |
| 策略门控 | Policy | 基于 fidelity threshold、noise tolerance 的 allow/reject/defer 判断 |
| 治理适配 | Governance | 将 validation report 转换为 CandidateRecord |
| Study/超参数搜索 | Study | C×L×K 结构化的实验网格搜索 |
| Quafu 适配器 | Executor | pyQuafu SDK 封装 |
| Qiskit Aer 适配器 | Executor | qiskit-aer 封装 |

### 7.1.2 QCompute 不负责的

| 职责 | 由谁负责 | 说明 |
|------|---------|------|
| 哈密顿量生成 | ABACUS / 外部求解器 | QCompute 只接收哈密顿量作为输入 |
| 分子构型优化 | ABACUS / DeepMD | 经典计算端的分子动力学与结构优化 |
| Agent 推理与决策 | MHE BrainProvider | QCompute 只提供 proposal 的评估结果 |
| Graph promotion 决策 | MHE HarnessRuntime | QCompute 只提供 evidence，不自主决定 commit |
| Session/Audit/Provenance 管理 | MHE 核心 | QCompute 产出 evidence refs，核心负责持久化与关联 |
| 量子纠错码设计 | 外部研究工具 | QCompute 只集成已有错误缓解策略，不设计新的 QEC 方案 |
| 量子硬件校准 | Quafu 平台运营方 | QCompute 只读取校准数据，不执行校准操作 |
| 脉冲级控制 | 不在首版范围 | 首版聚焦门级电路，脉冲优化为未来扩展 |

## 7.2 与 MHE 核心的集成面

```
QCompute Extension                    MHE Core
─────────────────                    ────────
QComputeExperimentSpec (用户输入)
  │
  ├─ Environment.probe()             [ComponentRuntime]
  ├─ ConfigCompiler.compile()
  ├─ Executor.execute()
  ├─ Validator.validate()
  ├─ Evidence.build_bundle()  ────→  SessionStore.append(event)
  ├─ Policy.evaluate()         ────→  SafetyPipeline.review()
  └─ Governance.adapt()        ────→  CandidateRecord
                                      │
                                      ├─ PromotionContext
                                      ├─ commit_graph()
                                      └─ Provenance Graph (WAS_DERIVED_FROM)
```

## 7.3 跨扩展协作面

### 7.3.1a ABACUS → QCompute 数据契约

**数据流与职责边界**：

```
ABACUS (经典端)                          QCompute (量子端)
─────────────────                       ────────────────
1. DFT SCF 计算
2. 输出 FCIDUMP 文件              ──→  3. 读取 FCIDUMP → 费米子哈密顿量
  （一电子 + 二电子积分）               4. 活性空间选择 (PySCF/Qiskit Nature)
                                      5. Fermion-to-Qubit 映射
                                         (默认 Jordan-Wigner)
                                      6. VQE ansatz 编译
                                      7. 量子执行
8. 接收量子能量                   ←──  9. 输出 VQE 能量 + 误差
10. 交叉验证：DFT vs Quantum
11. 若量子更优 → 迭代更大活性空间
```

**关键设计决策**：

| 决策点 | 负责方 | 说明 |
|--------|--------|------|
| FCIDUMP 输出 | ABACUS | 标准 ASCII 格式，包含一/二电子积分 |
| 活性空间选择 | QCompute ConfigCompiler | 调用 PySCF 从全轨道中选择 active 子集 |
| Fermion→Qubit 映射 | QCompute ConfigCompiler | 默认 Jordan-Wigner；Bravyi-Kitaev 为选项 |
| 参考能量 | ABACUS | DFT 基态能量作为 VQE 的对照基准 |

**数据交换格式**：FCIDUMP (ASCII) 作为主要交换格式——互操作性好、double precision、业界标准。
HDF5 (二进制) 作为大数据量场景的备选（仅在 ABACUS 和 QCompute 使用相同 PySCF 版本时推荐）。

### 7.3.2 QCompute ↔ DeepMD

协同路径较为间接，但存在以下结合点：

- DeepMD 产出的力场参数可作为量子化学计算的初始猜测
- 量子计算验证 DeepMD 力场在特定分子构型上的精度
- 元优化层面：Study 组件的方法论可在两者间共享

### 7.3.3 QCompute ↔ JEDI

量子计算与数据同化的结合属于前沿交叉方向（量子数据同化）：

- 量子算法加速背景误差协方差矩阵求逆
- 量子 annealing 用于观测算子选择优化
- 此方向暂不纳入首版 scope，作为远期研究留白

## 7.4 版本兼容性

### 7.4.1 SDK 依赖

| SDK | 最低版本 | 说明 |
|-----|---------|------|
| pyQuafu | ≥0.1.0 | Quafu 云平台 Python SDK |
| qiskit | ≥1.0 | 电路构造（QuantumCircuit） |
| qiskit-aer | ≥0.14 | 高性能模拟器 |
| qiskit-ibm-runtime | ≥0.20 (预留) | IBM Quantum 后端 |
| qsteed | ≥0.1.0 (可选) | Quafu 编译加速器（VQPU selection） |
| mitiq | ≥0.30 | 错误缓解标准库 |
| tensorcircuit | ≥2.0 (可选) | AI-native 量子模拟器 |
| pyscf | ≥2.0 (可选) | 活性空间选择（ABACUS 联动需要） |

### 7.4.2 MHE 兼容性

- `harness_version: ">=0.1.0"` —— 需要 `PromotionContext`、`SessionStore`、`ScoredEvidence` 等核心类型
- `state_schema_version: 1` —— 首版状态模式

## 7.5 扩展点与未来方向

| 扩展点 | 说明 | 优先级 |
|--------|------|--------|
| HI-VQE 信息交接范式 | 经典端与量子端迭代交接 Slater 行列式，显著降低电路深度要求 | 中远期（contract 预留） |
| IBM Quantum 后端 | 实现 `ibm_quantum` 平台适配器 | 中 |
| TensorCircuit 后端 | AI-native 量子模拟器，JAX 自动微分加速变分优化 | 中 |
| Cirq / TensorFlow Quantum 后端 | Google 量子生态集成 | 低 |
| 脉冲级优化 | 从门级深入到脉冲级控制参数优化 | 低 |
| 分布式量子计算 | 多芯片协同的电路划分与调度 | 远期 |
| 量子纠错码集成 | surface code / color code 的 Agent 优化选择 | 远期 |
| 量子数据同化 | QCompute ↔ JEDI 交叉 | 远期 |
| Quafu MCP 深度集成 | 超越 SDK，直接使用 MCP 协议的 Agent 工具调用 | 近期 |
| 噪声感知强化学习 | 在 RL 策略中显式建模噪声不确定性 | 中 |

HI-VQE 被认为是 ABACUS↔QCompute 协同的最有潜力路径——它比标准 VQE 对量子电路深度的要求更低，
更可能在 NISQ 设备上达到化学精度。首版通过 FCIDUMP + `active_space` 字段预留了数据契约兼容性。

## 7.6 HI-VQE 协同路径（远期研究）

HI-VQE (Handover-Iterative VQE, arXiv:2503.06292, arXiv:2601.06935)
是北京量子院提出的经典-量子混合计算前沿范式，代表了 QCompute↔ABACUS 长远协同的最优路径。

### 核心创新

标准 VQE 要求量子端独立完成能量求解，对电路深度要求高。
HI-VQE 将量子端定位为"采样器"而非"求解器"：

1. 量子端运行浅层电路，采样识别贡献最大的 Slater 行列式
2. 经典端（ABACUS/PySCF）接收行列式信息，做子空间精确对角化
3. 经典端将修正后的信息反馈给量子端，指导下一轮采样
4. 迭代至收敛

### 对 QCompute 的要求

- 支持部分测量（不要求完整 statevector）
- 支持迭代 handover 协议（非一次性提交）
- 收敛判断从"单次能量精度"变为"子空间能量收敛曲线"

### 首版预留

- `QComputeExperimentSpec.hamiltonian_file` + `active_space` 已预留 FCIDUMP 交换格式
- `QComputeValidationMetrics.convergence_iterations` 支持迭代收敛追踪
- 远期可在 `QComputeExecutionMode` 中增加 `"hi_vqe"` 模式
