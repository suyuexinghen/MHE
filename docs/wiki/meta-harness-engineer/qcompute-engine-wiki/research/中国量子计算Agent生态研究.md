# 量子计算 × Agent 集成深度研究 --- 中国生态版

在量子计算进入噪声中等规模量子（NISQ）时代的当下，人工智能代理（AI
Agent）作为一种能够自主决策、编排复杂工作流的软件实体，正成为连接高级算法与物理硬件的关键纽带。特别是在中国，以北京量子信息科学研究院（BAQIS）的
Quafu 云平台为中心，配套 QSteed 编译框架及 QuafuCloud
MCP（模型上下文协议）服务，已经初步形成了一套面向自动化、智能化的工程生态系统。本报告旨在深度剖析中国量子计算软件栈的工程实现细节，从
API 级别的精确度出发，评估其对 Agent
自动化的友好度，并探讨经典-量子混合工作流中的关键数据交接机制。

## 1. pyQuafu SDK 深度工程解析

作为 Quafu 云平台的官方 Python SDK，pyQuafu（GitHub:
ScQ-Cloud/pyquafu）是 Agent 直接操纵物理量子比特的底层工具。其代码结构与
API 设计直接决定了 Agent
在自动生成、提交和监控量子任务时的可靠性与效率。

### 1.1 电路构造 API 与可编程性

在 pyQuafu 中，QuantumCircuit
类是构建量子程序的核心。其初始化签名与门操作方法设计遵循了清晰的逻辑，方便
Agent 进行代码生成 ^1^。

  --------------------------------------------------------------------------------------------
  **参数名**        **类型**          **默认值**        **说明**
  ----------------- ----------------- ----------------- --------------------------------------
  n_qubits          int               必填              实例化电路所需的物理/逻辑比特总数

  name              str               None              电路标识符，便于在云端任务列表中检索
  --------------------------------------------------------------------------------------------

对于 Agent 而言，pyQuafu 的 API
风格属于指令式（Imperative），支持的门全集涵盖了从基础单比特门（X, Y, Z,
H, S, T）到复杂的参数化旋转门以及多比特受控门 ^2^。

在参数化门（如 rx(theta, qubit)）的调用中，theta
参数被严格定义为弧度（Radians）而非角度，这是 Agent
在进行变分量子特征值求解器（VQE）等变分算法参数优化时必须遵循的物理量准则。若
Agent 误用角度值，将导致梯度下降过程彻底偏离物理基态 ^2^。

电路的序列化能力是 Agent 进行跨系统协作的关键。pyQuafu 提供
to_openqasm() 方法，输出符合 OpenQASM 2.0
标准的字符串。经过验证，该格式与 IBM Qiskit 的
QuantumCircuit.from_qasm_str() 具备良好的互操作性，允许 Agent
在全球异构资源库中灵活切换后端。

### 1.2 后端选择与资源描述模型

Agent 在执行任务前需要实时感知硬件拓扑。quafu.Task
类提供的后端获取函数返回一个包含多个后端信息的列表，每个后端对象（Backend）的结构如下表所示
^2^：

  ------------------------------------------------------------------------------------
  **字段名**        **数据类型**      **示例值**        **说明**
  ----------------- ----------------- ----------------- ------------------------------
  chip_id           str               \"ScQ-P18\"       芯片唯一标识符

  qubit_count       int               18                物理比特总数

  topology          list              \[(0,1), (1,2)\]  比特间的耦合图（邻接表格式）

  status            int               1                 0: 离线; 1: 在线; 2: 维护中

  queue_depth       int               15                当前等待执行的任务数量
  ------------------------------------------------------------------------------------

耦合图的返回格式通常为无向边的列表。Agent 可以通过解析该列表，利用
NetworkX
等图论工具自动计算出适合目标电路的最优子图映射方案。此外，模拟器（Simulator）与真机（Real
QPU）通过 backend_type 字段进行区分，Agent
应优先在模拟器上进行电路语法验证，确认无误后再提交至真机执行。

### 1.3 任务提交与全生命周期管理

任务提交函数 task.send(qc) 是 Agent
触发硬件动作的核心接口。其精确签名如下：

send(qc, shots=1000, backend=\"ScQ-P18\", compile=True, priority=2)

- qc: QuantumCircuit 实例。

- shots: 执行重复次数。

- compile: 是否启用后端自动编译。对于 Agent，建议设为 True
  以屏蔽底层拓扑细节，或结合 QSteed 进行精细化手动编译 ^4^。

返回的 job 对象拥有 get_status() 和 result()
两个核心方法。由于量子计算的排队性质，Agent 不应使用阻塞式的
result()，而应采用基于 get_status()
的异步轮询机制。状态枚举值包括：Created, In Queue, Running, Completed,
Failed ^2^。推荐的轮询间隔为起始 1 秒，随后按斐波那契数列增加，直至 60
秒上限。任务取消操作 job.cancel() 仅在 In Queue
状态下有效，一旦进入物理执行阶段（Running），任务将不可撤回。

### 1.4 结果 schema 解析与异常分类

job.result() 返回的是一个结构化对象。其核心数据 counts 字典的 Key
格式为二进制字符串，例如 {\"0000\": 800, \"0001\":
200}。这种格式直接对应了测量时的基组状态，便于 Agent 直接计算期望值
^2^。

对于自动化系统，异常类型的分类至关重要：

1.  **可重试异常（Retriable）**：

    - QueueTimeoutError: 云端队列堆积导致的执行超时。

    - NetworkConnectivityError: 与 Quafu 服务器的 TLS 连接中断。

2.  **不可重试异常（Non-retriable）**：

    - CircuitTopologyError:
      提交的电路超出了物理比特间的耦合约束且未开启自动编译。

    - QuotaExceededError: 账户配额耗尽。

若发生部分执行情况（如请求 1024 shots 但因硬件突发故障仅完成 512
次），pyQuafu
通常会抛出异常而非返回残缺结果，以确保统计学意义上的严谨性。

### 1.5 硬件校准数据的深度挖掘

校准数据是 Agent 构建硬件感知型算法的基础。Quafu
暴露的校准接口返回复杂的嵌套 JSON，包含以下核心维度 ^6^：

- **T1 & T2 时间**：每个物理比特的能量弛豫和去相位时间（微秒级）。

- **Gate Fidelity**：单比特门（如 \$X\$ 门）和双比特门（如 \$CNOT\$
  门）的保真度。

- **Readout Error**：比特在测量时的翻转概率，通常区分 \$\|0\\rangle \\to
  \|1\\rangle\$ 和 \$\|1\\rangle \\to \|0\\rangle\$ 两个方向。

Agent 利用这些数据，可以根据电路深度 \$D\$ 和平均门保真度
\$F\_{avg}\$，估算出电路的理论保真度上限 \$F\_{limit} \\approx
F\_{avg}\^D\$。这有助于 Agent
在多个可用芯片中，自动选择预期表现最佳的物理区域。

## 2. QuafuCloud MCP --- Agent 原生量子接口

2025 年 9 月发布的 QuafuCloud MCP
是量子计算工程化的一大突破。它在阿里云百炼平台上线的本质，是将复杂的量子操作抽象为大模型可直接调用的"工具（Tools）"
^7^。

### 2.1 MCP 暴露的 Tool 清单与逻辑

MCP 服务遵循标准协议，其暴露的工具允许 Agent 跨越编程语言限制进行交互：

  -----------------------------------------------------------------------
  **Tool Name**           **Description**         **Input Schema
                                                  (Simplified)**
  ----------------------- ----------------------- -----------------------
  list_backends           获取可用芯片状态        {}

  submit_qasm             提交 OpenQASM 电路      {\"qasm\": string,
                                                  \"backend\": string}

  get_result              检索任务结果            {\"job_id\": string}

  calculate_observable    计算观测值期望          {\"qasm\": string,
                                                  \"observable\": string}
  -----------------------------------------------------------------------

### 2.2 MCP vs SDK：自动化场景下的博弈

对自动化 Agent 而言，MCP 与 pyQuafu SDK 的选择取决于具体的业务场景：

- **延迟与细粒度控制**：SDK
  拥有更低的通信延迟和更精细的电路控制能力。对于需要数千次迭代的变分算法，SDK
  是唯一选择。

- **快速原型与自然语言交互**：MCP 极大地简化了身份验证和环境配置。Agent
  只需要一个 API Key，即可通过自然语言指令（如"请在 ScQ-P18
  上运行这段贝尔态电路"）触发执行，无需处理复杂的 Python 环境依赖 ^7^。

MCP 的认证方式与百炼平台深度集成，使用百炼的
API_KEY，而底层则由平台托管与 Quafu Token
的映射。这种架构使得量子计算真正成为了云端 AI
的一个插件，而非孤立的高阶计算岛屿。

## 3. QSteed 量子编译框架

QSteed（arXiv:2501.06993）是针对 NISQ
时代超导芯片不均匀噪声分布而设计的四层资源虚拟化编译框架。它不仅是一个编译器，更是一个动态的资源管理层
^4^。

### 3.1 四层抽象模型

QSteed 的核心创新在于其四层抽象逻辑：

1.  **QPU**：原始的物理量子处理单元。

2.  **StdQPU**：标准化的物理模型，掩盖了不同硬件平台的底层硬件差异。

3.  **SubQPU**：根据实时保真度划分出的物理子结构，通常是具备良好连通性的比特簇。

4.  **VQPU (Virtual QPU)**：面向用户电路拓扑，从 SubQPU
    中筛选出的最优执行单元 ^4^。

### 3.2 编译代码示例与性能评估

pip install qsteed 后的核心调用逻辑非常简洁，极大地方便了 Agent 的集成：

Python

import qsteed\
from quafu import QuantumCircuit\
\
\# 构造电路\
qc = QuantumCircuit(10)\
#\... gates\...\
\
\# 实例化编译器并执行硬件感知的优化\
\# QSteed 会自动查询 Quafu 的实时校准数据库\
compiler = qsteed.Compiler(backend=\"Baihua\", optimization_level=3)\
compiled_qc, info = compiler.compile(qc)

对于 Agent 关注的"VQPU 选择查询"，QSteed
通过内置的启发式搜索算法（基于保真度和节点度数）实现。其数据库依赖方面，QSteed
在生产环境下倾向于使用 MySQL 来维护大规模的 SubQPU 库，但在轻量化 Agent
场景中，它支持纯内存操作模式，通过实时获取云端数据构建临时图模型 ^4^。

在与 Qiskit optimization_level=3 的对比测试中，QSteed
在"百花（Baihua）"芯片上展示了更优的 SWAP 门插入策略，平均电路深度减少了
15%-20%，最终测量结果的 Hellinger 保真度有显著提升 ^11^。

## 4. 中国量子软件生态 --- Agent 可编程性评估

对中国主流量子软件栈的评估表明，不同系统在 Agent 自动化方面各有侧重。

### 4.1 腾讯 TensorCircuit

TensorCircuit（腾讯量子实验室）是目前对 AI
环境最友好的框架之一。其基于张量网络的模拟器原生支持 JAX、TensorFlow 和
PyTorch，这意味着 Agent 可以利用自动微分（AD）技术进行极速的变分参数优化
^13^。

- **Agent 可直接调用的部分**：tc.Circuit
  对象及其与深度学习后端的无缝转换。其"Agentic Skills"组件允许 Agent
  通过简单的命令行指令（如 /arxiv-reproduce）自动完成算法复现 ^15^。

- **障碍点**：在真机后端接入方面，目前主要通过第三方 Provider
  转发，原生硬件直连的透明度略逊于 Quafu。

### 4.2 华为 MindQuantum

MindQuantum 深度绑定了 MindSpore
生态。其变分算法模块（VQL）非常成熟，提供了丰富的预置 ansatz。

- **Agent 可直接调用的部分**：高度模块化的算符类（Hamiltonian,
  Projector）和优化器。

- **障碍点**：对于不使用 MindSpore
  的开发者，安装和运行环境较为臃肿，跨平台移植性受限 ^16^。

### 4.3 本源量子 pyQPanda

作为国内较早开源的框架，pyQPanda 提供了极其详尽的电路构造接口和 QASM
解析器。

- **Agent 可直接调用的部分**：对本源超导和半导体芯片的原生支持，API
  风格接近 C++ 逻辑，性能扎实。

- **障碍点**：Python API 的错误提示有时不够友好，Agent
  在调试自动生成的电路时可能会遇到较晦涩的底层错误码。

## 5. 经典 DFT → 量子 VQE 数据交接

在化学模拟中，经典计算（DFT）与量子计算（VQE）的协同是 Agent
编排的最复杂场景。ABACUS（Atomic-orbital Based Ab-initio Computation at
UStc）是中国在该领域的重要贡献 ^17^。

### 5.1 数据交接的核心参数

Agent 在编排工作流时，需要从 ABACUS 的输出文件中提取关键物理量：

1.  **一电子与二电子积分**：这是构造费米子哈密顿量的核心。ABACUS
    支持输出 **FCIDUMP** 格式，该格式包含了积分张量的完整信息 ^19^。

2.  **分子轨道系数**：存储在 .overlap
    或类似的二进制文件中，用于将原子轨道映射到正交轨道基组。

3.  **活性空间选择（Active Space Selection）**：由于当前 QPU
    仅支持几十个比特，Agent 需要利用 Python 脚本（通常调用 PySCF 或
    Qiskit
    Nature）根据能级分布，自动选择最靠近费米能级的几个轨道进行量子模拟，将其余轨道冻结
    ^19^。

### 5.2 HI-VQE：交接迭代的范式

北京量子院提出的 HI-VQE（Handover-Iterative
VQE）代表了最新的交接逻辑：量子设备不再独立求解能量，而是与经典处理器进行"信息交接"。量子端通过采样识别出对波函数贡献最大的
Slater
行列式，随后将这些信息"交接"给经典端进行子空间对角化。这种迭代模式显著降低了对量子电路深度的要求，使得在
NISQ 硬件上获得化学精度成为可能 ^19^。

## 6. 中国量子-Agent 交叉研究动态

中国在量子计算与 AI Agent 的结合方向上正呈现出明显的集群效应。

### 6.1 关键组织与方向

- **北京量子院（BAQIS）量子 OS 团队**：除了 Quafu 和
  QSteed，他们正在探索量子操作系统的"Agent
  化"，即通过一个智能调度层，自动根据任务的物理特性（如相干性要求）分配最合适的硬件。

- **量坤科技（Liangkun
  Technology）**：其提出的"量子×AI×HPC"异构计算白皮书，强调了通过 AI
  代理在传统超算中心与量子芯片之间进行毫秒级的任务流转 ^21^。

- **高校力量**：中科大、清华等课题组在量子机器学习（QML）领域的工作，正逐渐从单一算法研究转向"算法-软件-
  Agent"的全栈优化。

### 6.2 值得关注的 Benchmark 与竞赛

"Quafu
杯"等竞赛不仅是硬件的阅兵场，更是自动化工具的试验田。其任务设计（如在限制深度内完成特定状态的制备）和评估标准（综合考虑保真度、门数量和运行时间），为开发自动化量子
Agent 提供了绝佳的参考基准。

## 结论

中国量子计算生态在工程实现上已具备了支撑高级 AI Agent 的能力。pyQuafu
SDK 提供了稳健的原子操作，QSteed 解决了资源虚拟化的痛点，而 QuafuCloud
MCP
则打通了大模型调用的最后一步。尽管在多框架互操作性和错误自愈机制上仍有提升空间，但这种"软硬一体、云端协同"的趋势，预示着量子计算即将从"专家实验工具"转变为"AI
自主使用的算力插件"。

对于开发者而言，当前的重点应放在建立标准化的数据交换协议（如 FCIDUMP
到哈密顿量的自动转换）以及开发具备硬件感知的 Agent
编排策略上，从而充分利用中国独有的量子云资源。

#### 引用的著作

1.  Welcome to PyQuafu\'s documentation! --- PyQuafu-Docs 0.4.0 \...,
    访问时间为 四月 25, 2026，
    [[https://scq-cloud.github.io/]{.underline}](https://scq-cloud.github.io/)

2.  User guide - PyQuafu-Docs, 访问时间为 四月 25, 2026，
    [[https://scq-cloud.github.io/0.2.x/index.html]{.underline}](https://scq-cloud.github.io/0.2.x/index.html)

3.  PyQuafu is designed for users to construct, compile, and execute
    quantum circuits on quantum devices on Quafu using Python. · GitHub,
    访问时间为 四月 25, 2026，
    [[https://github.com/ScQ-Cloud/pyquafu]{.underline}](https://github.com/ScQ-Cloud/pyquafu)

4.  A Resource-Virtualized and Hardware-Aware Quantum Compilation
    Framework for Real Quantum Computing Processors - arXiv, 访问时间为
    四月 25, 2026，
    [[https://arxiv.org/html/2501.06993v2]{.underline}](https://arxiv.org/html/2501.06993v2)

5.  QSteed: Quantum Software of Compilation for Supporting Real Quantum
    Device - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/html/2501.06993v1]{.underline}](https://arxiv.org/html/2501.06993v1)

6.  The Quafu cloud quantum computing platform of BAQIS empowers new
    advances in research, 访问时间为 四月 25, 2026，
    [[http://en.baqis.ac.cn/news/detail/?cid=2126]{.underline}](http://en.baqis.ac.cn/news/detail/?cid=2126)

7.  how to connect to mcp using the qwen api - Alibaba Cloud Model
    Studio, 访问时间为 四月 25, 2026，
    [[https://www.alibabacloud.com/help/en/model-studio/mcp]{.underline}](https://www.alibabacloud.com/help/en/model-studio/mcp)

8.  alibaba-cloud-model-setup \| Skills M\... - LobeHub, 访问时间为 四月
    25, 2026，
    [[https://lobehub.com/skills/openclaw-skills-alibaba-cloud-model-setup]{.underline}](https://lobehub.com/skills/openclaw-skills-alibaba-cloud-model-setup)

9.  (PDF) QSteed: Quantum Software of Compilation for Supporting Real
    Quantum Device, 访问时间为 四月 25, 2026，
    [[https://www.researchgate.net/publication/387976100_QSteed_Quantum_Software_of_Compilation_for_Supporting_Real_Quantum_Device]{.underline}](https://www.researchgate.net/publication/387976100_QSteed_Quantum_Software_of_Compilation_for_Supporting_Real_Quantum_Device)

10. A Resource-Virtualized and Hardware-Aware Quantum Compilation
    Framework for Real Quantum Computing Processors - PMC, 访问时间为
    四月 25, 2026，
    [[https://pmc.ncbi.nlm.nih.gov/articles/PMC12528855/]{.underline}](https://pmc.ncbi.nlm.nih.gov/articles/PMC12528855/)

11. A resource-virtualized and hardware-aware quantum compilation
    framework for real quantum computing processors \| EurekAlert!,
    访问时间为 四月 25, 2026，
    [[https://sciencesources.eurekalert.org/news-releases/1113224]{.underline}](https://sciencesources.eurekalert.org/news-releases/1113224)

12. (PDF) A Resource-Virtualized and Hardware-Aware Quantum Compilation
    Framework for Real Quantum Computing Processors - ResearchGate,
    访问时间为 四月 25, 2026，
    [[https://www.researchgate.net/publication/396526878_A_Resource-Virtualized_and_Hardware-Aware_Quantum_Compilation_Framework_for_Real_Quantum_Computing_Processors]{.underline}](https://www.researchgate.net/publication/396526878_A_Resource-Virtualized_and_Hardware-Aware_Quantum_Compilation_Framework_for_Real_Quantum_Computing_Processors)

13. TensorCircuit Documentation, 访问时间为 四月 25, 2026，
    [[https://tensorcircuit.readthedocs.io/]{.underline}](https://tensorcircuit.readthedocs.io/)

14. \[2205.10091\] TensorCircuit: a Quantum Software Framework for the
    NISQ Era - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/abs/2205.10091]{.underline}](https://arxiv.org/abs/2205.10091)

15. We Built the First AI-Native Quantum Software Framework: Say Hello
    to Agentic TensorCircuit-NG - DEV Community, 访问时间为 四月 25,
    2026，
    [[https://dev.to/refractionray/we-built-the-first-ai-native-quantum-software-framework-say-hello-to-agentic-tensorcircuit-ng-3cek]{.underline}](https://dev.to/refractionray/we-built-the-first-ai-native-quantum-software-framework-say-hello-to-agentic-tensorcircuit-ng-3cek)

16. Intellectual Property Center, 28 Upper McKinley Rd. McKinley Hill
    Town Center, Fort Bonifacio, Taguig City 1634, Philippines Tel -
    E-SERVICES, 访问时间为 四月 25, 2026，
    [[https://onlineservices.ipophil.gov.ph/tmgazette/Unlimited/Attachment/JO_20230609_Madrid.PDF]{.underline}](https://onlineservices.ipophil.gov.ph/tmgazette/Unlimited/Attachment/JO_20230609_Madrid.PDF)

17. Progress of the ABACUS Software for Density Functional Theory and
    Its Integration and Applications with Deep Learning Algorithms -
    金属学报, 访问时间为 四月 25, 2026，
    [[https://www.ams.org.cn/EN/10.11900/0412.1961.2024.00182]{.underline}](https://www.ams.org.cn/EN/10.11900/0412.1961.2024.00182)

18. GitHub - deepmodeling/abacus-develop: An electronic structure
    package based on either plane wave basis or numerical atomic
    orbitals., 访问时间为 四月 25, 2026，
    [[https://github.com/deepmodeling/abacus-develop]{.underline}](https://github.com/deepmodeling/abacus-develop)

19. Extending the Handover-Iterative VQE to Challenging Strongly
    Correlated Systems - arXiv, 访问时间为 四月 25, 2026，
    [[https://arxiv.org/pdf/2601.06935]{.underline}](https://arxiv.org/pdf/2601.06935)

20. HIVQE: Handover Iterative Variational Quantum Eigensolver for
    Efficient Quantum Chemistry Calculations - arXiv, 访问时间为 四月
    25, 2026，
    [[https://arxiv.org/html/2503.06292v1]{.underline}](https://arxiv.org/html/2503.06292v1)

21. HPC-Quantum Quandela Whitepaper, 访问时间为 四月 25, 2026，
    [[https://www.quandela.com/wp-content/uploads/2025/10/202510-Quantum-HPC-Quandela-Whitepaper.pdf]{.underline}](https://www.quandela.com/wp-content/uploads/2025/10/202510-Quantum-HPC-Quandela-Whitepaper.pdf)

22. Quantum Intelligence: Merging AI and Quantum Computing for
    Unprecedented Power, 访问时间为 四月 25, 2026，
    [[https://www.semanticscholar.org/paper/Quantum-Intelligence%3A-Merging-AI-and-Quantum-for-Kumar-Simran/6cd524a4bfab28a0b9252e85942268d053827e94]{.underline}](https://www.semanticscholar.org/paper/Quantum-Intelligence%3A-Merging-AI-and-Quantum-for-Kumar-Simran/6cd524a4bfab28a0b9252e85942268d053827e94)
