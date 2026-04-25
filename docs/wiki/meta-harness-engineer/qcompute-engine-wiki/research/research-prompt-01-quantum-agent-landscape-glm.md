# 量子计算 × Agent 集成深度研究 — 中国生态版

> 本提示与 `research-prompt-01-quantum-agent-landscape.md` 互补。
> 主提示覆盖全球量子-Agent 系统架构、Qiskit/Mitiq 等国际工具链、
> 量子化学混合工作流、跨系统对比和评估基准。
> 本提示聚焦 **中国量子计算生态的工程实现细节**——这些系统的英文文档和
> 社区讨论较少，但公开代码、论文和官方文档中包含足够的技术信息可供深入挖掘。

## 背景

我们正在研究 AI Agent 与量子计算的结合方式，特别关注：

- **量子云平台的 Agent 自动化友好度**：是否能被外部程序全自动调用（无人工干预）
- **量子软件栈的可编程性**：Python API 纯度、结果格式可解析性、错误可恢复性
- **中国量子生态的独有资源**：Quafu 是国内最大的开放量子云平台，
  QuafuCloud MCP 是全球首个量子计算 MCP 服务，QSteed 是专为 Quafu 设计的编译框架
- **经典-量子混合工作流**：DFT 计算与量子 VQE 之间的数据交接

我们不需要量子计算科普或概念综述。我们需要 **API 级别的精度**：
函数签名、返回结构、错误码、限制条件。

**请优先回答**：API 签名和返回 schema > 公开 benchmark 数据 > 架构描述 > 推测分析。
标注信息来源。区分"文档记载"和"推测"。

---

## 1. pyQuafu SDK — 逐函数 API 挖掘

pyQuafu 是 Quafu 云平台的 Python SDK，GitHub 开源 (ScQ-Cloud/pyquafu)。
这是最重要的调查对象——源码即文档。

### 1.1 电路构造

- `QuantumCircuit` 的精确 `__init__` 签名（参数名、类型、默认值）。
- 添加门的方法和 API 风格。支持的门全集列表。
  参数化门（`rx(theta, qubit)` 之类）的调用方式——`theta` 是弧度还是角度？
- 电路深度、门计数、qubit 数的获取方法。电路序列化：`to_openqasm()` 输出格式？
  与 Qiskit 的 `QuantumCircuit.from_qasm_str()` 是否互通？

### 1.2 后端选择

- 获取可用芯片列表的函数和返回结构。请给出一次真实调用的返回示例（脱敏）。
- 芯片描述对象包含的字段（chip_id, qubit_count, topology, status, queue_depth, ...）。
- 耦合图的获取方法和返回格式（`[(0,1), (1,2), ...]`？adjacency list？）。
- 模拟器与真机的区分方式。
- 芯片在线/离线/维护状态的判断。

### 1.3 任务提交与生命周期

- 任务提交函数的精确签名：函数名、所有参数、类型、默认值。
- 返回的 job 对象类型，拥有的方法和属性。
- 任务状态枚举值和状态转换图。轮询机制：`job.result()` 阻塞等待 or
  `job.status()` + sleep？推荐轮询间隔？
- 任务取消：`job.cancel()` 是否支持？什么状态下可以取消？
- 超时处理：SDK 层面的超时参数？真机最大执行时间？

### 1.4 结果获取

- `job.result()` 返回对象的类型。
- `counts` 字典的精确 key 格式。请给出 4-qubit 电路测量结果的真实 key 样例
  （是 `"0000"` 还是 `"0x0"` 还是其他格式？）。
- 是否返回概率分布（`probabilities`）？statevector（模拟器）？执行时间统计？
- 异常类型列表：哪些是可重试的（排队超时）？哪些是不可重试的（电路语法错误）？
- 部分结果：若 shots=1024 但只跑了 500 次，返回什么？

### 1.5 校准数据

- 获取当前校准数据的函数名和返回 JSON 的完整 schema（字段名、类型、嵌套结构）。
- 校准数据包含哪些信息：T1/T2（per qubit）、单比特门保真度（per qubit per gate）、
  双比特门保真度（per qubit pair）、读出保真度（per qubit, |0⟩和|1⟩方向）？
- 校准时间戳和更新频率。
- 如何从校准数据估算一个给定电路的理论保真度上限？

### 1.6 配额与限制

- 免费用户的每日任务数量上限。电路深度/shots 的额外限制？
- 配额超限时的错误消息格式。配额重置时间（北京时间几点）？
- 排队机制和并发提交限制。

---

## 2. QuafuCloud MCP — Agent 原生量子接口

2025 年 9 月，北京量子院发布了全球首个产品级量子计算 MCP 服务，
在阿里云百炼平台上线。

- 请列出 MCP 暴露的 tool 清单（name, description, inputSchema, outputSchema）。
- MCP vs pyQuafu SDK 的功能覆盖度对比：哪些操作只能通过 MCP？哪些只能通过 SDK？
- 对自动化 Agent 使用场景：MCP 和 SDK 哪个延迟更低、可靠性更好、控制粒度更细？
- 认证方式：与 pyQuafu 共享 token 还是独立的百炼 API key？
- 自然语言到量子任务的映射机制和能力边界？
- 是否有公开的 MCP 使用示例或案例？

---

## 3. QSteed 量子编译框架

QSteed (arXiv:2501.06993, Research 2025) 是北京量子院开发的
四层资源虚拟化（QPU→StdQPU→SubQPU→VQPU）编译框架，已在 Quafu 部署。

- `pip install qsteed` 后的 import 方式和核心类。编译电路的最简代码示例（3-10 行）。
- MySQL 依赖：是硬依赖还是可选的？是否有 SQLite 或纯内存替代？
- VQPU 选择查询：如何按芯片、qubit 数、保真度下限筛选可用 VQPU？
- 编译输出报告包含的字段？与 Qiskit `optimization_level=3` 在百花芯片上的
  编译质量对比（SWAP 数、深度、实际执行保真度）——是否有公开 benchmark？
- 社区维护状态：近期 commits、open issues、响应速度？

---

## 4. 中国量子软件生态 — Agent 可编程性评估

对以下系统，请基于**公开代码和文档**（而非官方宣传）评估其 Agent 自动化友好度：

| 系统 | 开发者 | 需要确认 |
|------|--------|---------|
| **pyQuafu** | 北京量子院 | 见第 1 节——已是最高优先级 |
| **QSteed** | 北京量子院 | 见第 3 节 |
| **TensorCircuit** | 腾讯量子实验室 | `import tensorcircuit` 后的 API 风格？VQE 支持？与 Qiskit 互操作？GPU 加速实际效果？ |
| **MindQuantum** | 华为 | 是否绑定 MindSpore？变分算法模块可否独立使用？ |
| **pyQPanda** | 本源量子 | 是否绑定本源芯片？API 成熟度（文档、示例、异常处理）？ |

每个系统给出：**"Agent 可直接调用的部分"**和**"Agent 编排的障碍点"**。

---

## 5. 经典 DFT → 量子 VQE 数据交接

ABACUS (第一性原理 DFT，开源) 与量子计算联动是经典-量子混合工作流的核心场景。

- ABACUS 输出的哪些数据可用于构造量子哈密顿量？
  分子轨道系数的存储格式和读取方式？一电子/二电子积分是否直接输出？
- 费米子→量子比特映射（Jordan-Wigner / Bravyi-Kitaev）在各框架中的实现：
  Qiskit Nature、OpenFermion、PySCF 的 API 和输入格式要求。
- 活性空间选择的 Python 实现：从全电子计算缩到 NISQ 可用的 4-12 qubits。
- 已发表的"经典 DFT vs 量子 VQE"对比数据（H₂、LiH、H₂O 的精度和计算成本）。
- Fermionic Hamiltonian 的标准交换格式：FCIDUMP？HDF5？

---

## 6. 中国量子-Agent 交叉研究动态

- 北京量子院量子 OS 团队（QSteed/Quafu）：除 QSteed+QuafuCloud MCP 外，
  是否有其他量子-Agent 交叉方向的公开工作？
- 量坤科技："量子×AI×HPC"异构计算——是否有公开论文、白皮书或技术博客？
- 国内高校在量子+Agent/量子+AI 方向值得关注的课题组？
  （如中科大、清华、南大等在量子计算和 AI 交叉方向的工作）
- 值得关注的量子计算竞赛/benchmark 活动（Quafu 杯等）？
  其任务设计和评估标准是否可作为自动化量子 Agent 的测试参照？

---

## 输出格式

1. **API 精确文档**：函数签名、返回 schema、错误类型——代码补全级别的精度
2. **代码示例**：pyQuafu、Qiskit Nature、Mitiq 等关键操作的可运行片段
3. **评估矩阵**：中国量子软件栈的 Agent 自动化友好度对比
4. **Benchmark 数据**：公开的性能数字——延迟、成本、规模、阈值
5. **信息缺口**：无法从公开信息确定的内容，标注为"推测"或"需实验验证"

## 重点源

- pyQuafu 源码（GitHub: ScQ-Cloud/pyquafu）——最权威
- QSteed 源码 + 论文 (arXiv:2501.06993, Research 2025)
- Quafu 文档：https://quarkstudio.readthedocs.io/
- 北京量子院新闻：https://www.baqis.ac.cn/news/
- ABACUS 源码和文档
- Qiskit Nature 文档：https://qiskit-community.github.io/qiskit-nature/
- TensorCircuit 论文 (Quantum 7, 912, 2023) + GitHub
- 本源量子 / 华为 MindQuantum / 启科量子 官方文档和 GitHub
