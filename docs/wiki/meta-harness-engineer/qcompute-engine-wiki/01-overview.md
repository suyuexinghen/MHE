# 01. 概述与定位

## 1.1 为什么需要量子计算扩展

NISQ（Noisy Intermediate-Scale Quantum）时代的量子计算已从纯理论走向工程实用化。
Quafu、IBM Qiskit 等云平台提供了可编程访问的真实量子硬件，
使 Agent 系统可以像编排经典求解器一样编排量子计算资源。

QCompute 扩展（`metaharness_ext.qcompute`）将量子计算引入 MHE 框架，
使其成为与 ABACUS（DFT）、DeepMD（分子动力学）、JEDI（数据同化）并列的科学计算 Worker。

## 1.2 核心定位

QCompute 是 MHE 中的 **量子-经典混合计算 Worker**，承担三个关键角色：

1. **量子后端抽象层**：统一 Quafu 真机、Qiskit Aer 模拟器、其他量子云平台为一致的执行接口
2. **Agent 驱动的电路优化器**：以 SimpleTES 的 C×L×K（并发 × 深度 × 候选）评估驱动范式，
   替代静态编译，实现动态的"生成-编译-评估-再生成"闭环
3. **混合计算编排器**：在经典预处理（电路生成、哈密顿量构造）与量子执行之间建立 Agent 可控的调度面

## 1.3 与现有扩展的关系

```
MHE Runtime
  ├─ ABACUS (经典 DFT / 平面波第一性原理)
  │    └─ 生成哈密顿量、预筛选分子构型
  ├─ DeepMD (经典分子动力学)
  │    └─ 力场训练、构型采样
  ├─ JEDI (数据同化)
  │    └─ 观测算子、背景误差协方差
  └─ QCompute (量子计算) ← 本扩展
       ├─ 接收经典端输出的子问题（哈密顿量、ansatz 模板）
       ├─ 编译并提交至量子后端
       └─ 返回量子结果供经典端后处理与迭代
```

### 1.3.1 QCompute 技术栈分层

```
QCompute Extension
  ├─ 应用层：Study (C×L×K 实验网格) + BrainProvider (Agent 优化)
  ├─ 编排层：Gateway (实验编译) + ConfigCompiler (电路编译、映射选择)
  ├─ 执行层：Executor (SDK/MCP 双通道) + Mitiq (错误缓解)
  ├─ 模拟层：Qiskit Aer (主模拟器) + TensorCircuit (变分加速器)
  ├─ 编译加速：QSteed (VQPU 四层虚拟化，Quafu 专用)
  └─ 量子硬件：Quafu 超导芯片 (Baihua 等)
```

QCompute 与 ABACUS 的联动是最自然的切入点：ABACUS 做大规模分子预筛选、
生成哈密顿量 → QCompute 将问题分解为适合 NISQ 设备规模的子问题 →
提交至量子后端 → 对比经典 DFT 与量子 VQE/QPE 结果 → 迭代优化 ansatz 电路。

## 1.4 设计原则

1. **后端无关**：统一抽象层使 Agent 可以无差别调度模拟器和真机，在模拟器中快速迭代后迁移至真机
2. **噪声感知**：合约层原生表达噪声模型、保真度阈值、错误缓解策略选择
3. **证据驱动**：所有量子运行结果通过 evidence bundle 接入 MHE 的 promotion/governance 路径
4. **渐进式接入**：先支持 Quafu（pyQuafu + MCP）和 Qiskit Aer，预留 IBM Quantum、Cirq 等后端扩展点

## 1.5 关键技术参照

| 参照系统 | 与 QCompute 的关系 | 集成优先级 |
|----------|-------------------|-----------|
| **Quafu 云平台** | 主要真机后端；pyQuafu SDK + QuafuCloud MCP 双通道 | P0 (首版) |
| **QSteed** | Quafu 生态的量子编译加速器（VQPU 四层虚拟化 + 硬件感知编译）；作为 ConfigCompiler 的可选编译后端 | P1 (增强) |
| **Qiskit / Qiskit Aer** | 主要模拟器后端 + 电路构造 + transpilation | P0 (首版) |
| **TensorCircuit** | AI-native 量子模拟器（JAX/TF/PyTorch 自动微分）；变分优化加速器 | P1 (增强) |
| **Mitiq** | 错误缓解标准实现路径（ZNE, PEC, MEM）；跨后端兼容 | P0 (首版) |
| **SimpleTES** | 评估驱动科学发现范式（C×L×K + 轨迹级评估）；指导 Study 组件设计 | P0 (方法论) |
| **QAgent** | LLM 多 Agent OpenQASM 编程（Planner-Coder-Reviewer + RAG）；参照其分层 Agent 模式 | P1 (参照) |
| **QUASAR** | Agentic RL 量子编译（4 级分层奖励）；参照其 gated evaluation 机制 | P1 (参照) |
| **PhysMaster** | AI 物理学家自主科研系统；参照其"研究闭环"架构 | P2 (远期) |
| **HI-VQE** | 经典-量子信息交接迭代范式；ABACUS 联动最优路径 | P2 (远期预留) |

## 1.6 最小可行闭环

短期 Demo 验证路径：

```
Agent (MHE Orchestrator)
  ├─ 1. 经典 Worker: 生成 VQE ansatz 电路 (Qiskit/pyQuafu)
  ├─ 2. QCompute Gateway: 编译实验规格 → 选择后端
  ├─ 3. QCompute Executor: 提交至 Quafu 模拟器/真机执行
  ├─ 4. QCompute Validator: 解析能量曲线、计算保真度
  └─ 5. Agent 反馈: 调整 ansatz 参数/纠错策略 → 循环至 1
```

这与 MHE 已验证的 MOOSE/FEniCS 编排思路完全一致——量子计算机只是系统中一个新的 Worker。

### 1.6.1 首版可行性关键决定

以下决定直接决定了首版能否用最少自研代码覆盖最多真实能力：

1. **不自行实现量子编译器**——通过 QSteed（Quafu 生态）和 Qiskit Transpiler 完成
2. **不自行实现错误缓解**——使用 Mitiq 标准库（`execute_with_zne()`, `TensoredMeasFitter`）
3. **模拟器优先验证**——所有电路先在 Qiskit Aer 闭环验证，确认可行后再提交 Quafu 真机
4. **双通道执行**——Quafu 真机同时支持 pyQuafu SDK（低延迟、细粒度控制）和 QuafuCloud MCP（快速原型、自然语言交互）
5. **TensorCircuit 作为变分加速器**——其 JAX 自动微分比 Qiskit 基于采样的梯度估计快一个数量级，
   在 ansatz 搜索场景下可大幅降低 Study 组件的迭代成本

### 1.6.2 首版明确不做的

| 排除项 | 原因 |
|--------|------|
| IBM Quantum / AWS Braket 后端 | 网络延迟和账户障碍；首版聚焦 Quafu |
| 本源 pyQPanda / 华为 MindQuantum | API 成熟度和生态绑定问题；远期评估 |
| 脉冲级优化 | 门级电路是首版边界 |
| 自主量子纠错码设计 | QEC 尚属前沿研究，不宜进入工程扩展 |
| HI-VQE handover 协议 | contract 预留，实现版不包含 |
