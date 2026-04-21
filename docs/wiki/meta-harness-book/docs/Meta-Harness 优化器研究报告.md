# 元Harness自我重长框架中智能优化器的工业级实现路径：强化学习、图状态编码与统计收敛判据深度研究报告

## 1. 核心概念界定与优化器决策空间映射

在《Meta-Harness
工程设计手册》的理论框架下，元智能体（Meta-Agent）的本质是超越单一提示词优化，实现对"Harness"（支架程序）的全栈自动化演进。Harness
并非简单的文本容器，而是包含运行时调度、记忆检索策略、工具调用逻辑及评估闭环的确定性软件层。优化器（Optimizer）作为这一进化过程的"中枢神经"，其核心任务是在高维、离散且充满噪声的搜索空间中，识别出能最大化
Pareto 效能的组件拓扑与配置。

为了使该系统从概念原型升级为工业级实现，首先必须对优化器的关键术语进行多维度的工程界定。状态编码（State
Encoding）被定义为将离散的 XML
组件图转化为连续张量的映射过程，它决定了优化器对架构细微变化的敏感度。动作空间（Action
Space）则被界定为一组受限的变换算子，涵盖从微观参数微调到宏观代码生成的层次化操作。搜索策略（Search
Strategy）决定了探索（Exploration）与利用（Exploitation）的平衡，特别是在样本获取成本极高的环境下，如何利用历史轨迹进行启发式搜索。奖励塑形（Reward
Shaping）需在单一准确率指标之外，引入超体积增量与复杂度惩罚项，以引导模型向"精简且高效"的方向进化。统计收敛判据（Convergence
Criterion）则是在评估噪声背景下，基于概率论和贝叶斯推断给出的停止或回溯信号。最后，程序合成（Program
Synthesis）在元Harness语境下是指受限的、基于模板的代码补全，而非漫无边际的自由代码生成。

优化器的设计决策空间呈现出一种嵌套的因果关系链。状态编码直接决定了策略网络的表征能力，进而限制了动作空间的表达效率；评估过程捕获的多维性能指标通过奖励塑形反馈给搜索算法，最终由收敛控制器根据统计显著性决定迭代是否终结。这种闭环机制类似于数值偏微分方程（PDE）中的迭代收敛，但其算子是在非线性的离散逻辑空间中运行。

## 2. 算法架构对比矩阵与系统演进趋势

在自动化设计智能体系统（ADAS）及神经架构搜索（NAS）领域，2024至2026年间涌现出大量具有里程碑意义的研究。通过对
Meta-Harness、ADAS、ENAS、AlphaDev 等 8
个代表性系统的深度剖析，可以发现从"硬编码"到"自我编程"的演变路径清晰可见。

### 算法架构多维对比矩阵

  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  **系统/算法**    **搜索空间表达**   **状态编码方案**       **搜索算法**         **奖励/评估设计**      **样本效率**   **多目标支持**   **模板依赖度**   **收敛判据**
  ---------------- ------------------ ---------------------- -------------------- ---------------------- -------------- ---------------- ---------------- -------------------
  **Meta-Harness   自由 Python 代码   全文件系统轨迹 +       编码智能体 (Claude   轨迹溯源 +             极高 (10-20轮) 强 (Pareto       极低             性能饱和度
  (Lee et al.                         评分记录               Code)                精度/成本权衡                         Frontier)                         
  2026)** ^1^                                                                                                                                             

  **ADAS / Meta    Python 代码        历史存档 (Archive)     进化搜索 (FM-based)  任务准确率 (Score)     中 (30-50轮)   弱               低               迭代次数限制
  Agent Search**   (Forward 函数)                                                                                                                         
  ^3^                                                                                                                                                     

  **ENAS           参数化有向无环图   RNN 状态向量           强化学习 (Policy     参数共享下的验证精度   极高           否               极高 (算子池)    梯度平滑
  (Efficient       (DAG)                                     Gradient)                                                                                    
  NAS)** ^5^                                                                                                                                              

  **AlphaDev       汇编指令序列       Transformer + CPU 状态 MCTS + RL (AlphaZero 延迟 (Latency) +       极低           是 (多目标评估)  低               算法长度/延迟极限
  (DeepMind)** ^6^                    MLP                    架构)                正确性                                                                  

  **AgentSquare    四类核心模块组合   统一输入输出接口向量   模块进化与组合重构   性能预测器 +           高             是               极高             预测精度收敛
  (MoLAS)** ^7^                                                                   验证集准确率                                                            

  **AFlow (Zhang   预定义算子图       算子逻辑序列           MCTS                 结构化奖励信号         中             是               高               蒙特卡洛置信区间
  et al. 2024)**                                                                                                                                          
  ^8^                                                                                                                                                     

  **MASS           提示词 + 拓扑结构  层次化嵌入             多阶段联合优化       模块级 vs 整体级奖励   中             是               中               验证集早停
  (Multi-Agent                                                                                                                                            
  System Search)**                                                                                                                                        
  ^10^                                                                                                                                                    

  **AutoML-RL      模型流水线         状态-动作轨迹嵌入      PPO / SAC            组合性能指标           中             否               中               性能均值稳定
  (Activeloop)**                                                                                                                                          
  ^12^                                                                                                                                                    
  ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

分析表明，早期的 NAS 方法（如
ENAS）虽然效率极高，但受限于预定义算子，难以生成全新的逻辑结构
^5^。相比之下，AlphaDev 证明了在原子指令层级进行 RL
搜索的潜力，但其数亿次的模拟代价对大多数工程场景而言是不可接受的
^6^。最新的 Meta-Harness
方案则跳出了"神经网络参数化"的陷阱，直接利用具备高级推理能力的编码智能体（如
Claude Code/Opus 4.6）读取包含原始轨迹和评分的文件系统，进行反事实诊断
^14^。这种"基于轨迹的针对性编辑"比"基于分数的黑盒变异"具有显著更高的样本效率。

对于元Harness 优化器而言，最理想的路径是结合 AgentSquare
的模块化稳定性与 Meta-Harness 的诊断深度。其搜索空间应以 XML
描述的组件图为骨架，通过受约束的代码生成对核心逻辑进行微调，从而在
Turing 完备性与工程可控性之间寻找最优平衡点。

## 3. 组件图状态编码方案：从 GNN 到拓扑指纹

将离散的组件图（Component Graph）转化为 RL
优化器可理解的状态表示，是实现"自我重长"的第一步。对于元Harness
初期（5--20
个组件）的规模，状态编码方案必须能够敏锐感知拓扑结构的细微变动，同时保持对训练样本数量的低依赖。

### 3.1 编码方案深度对比

在众多的图编码方法中，固定长度邻接矩阵拼接（MLP-friendly）虽然实现简单，但缺乏对节点置换的不变性（Permutation
Invariance），且难以适应变长图
^16^。普通的图卷积网络（GCN）或图注意力网络（GAT）在处理小规模、具有强逻辑含义的组件图时，容易出现"过度平滑"（Over-smoothing）问题，导致不同功能的拓扑结构被映射为相似的嵌入
^18^。

基于图同构网络（GIN）的拓扑指纹方案被证明是目前最适合此类任务的路径。GIN
采用了单射（Injective）聚合函数，其区分非同构图的能力与
Weisfeiler-Lehman (WL)
测试相当，能够精确识别组件之间的前驱后继关系及闭环路径 ^20^。

### 3.2 推荐编码方案：GIN-based Topology Embedding

针对元Harness 优化器，建议构建如下状态向量 \$s_t\$：

\$\$s_t = \\{ \\text{Embed}(G_t), \\text{Embed}(\\tau_t), \\mathbf{f}\_t
\\}\$\$

其中 \$\\text{Embed}(G_t)\$ 是利用 GIN 提取的全局拓扑嵌入。每一个节点
\$v\$ 的特征向量 \$x_v\$
应包含：组件类型（One-hot）、当前参数哈希、内存占用率及近期评估的局部成功率。

**数学定义与消息传递机制：**

GIN 的第 \$k\$ 层更新过程如下：

\$\$h_v\^{(k)} = MLP\^{(k)} \\left( (1 + \\epsilon\^{(k)}) \\cdot
h_v\^{(k-1)} + \\sum\_{u \\in \\mathcal{N}(v)} h_u\^{(k-1)} \\right)\$\$

通过使用加法聚合而非均值聚合，GIN
保留了节点度的信息，这对识别"扇入/扇出"极高的关键调度组件至关重要 ^20^。

**状态编码实现伪代码：**

Python

class ComponentGraphEncoder(torch.nn.Module):\
def \_\_init\_\_(self, in_channels, hidden_channels):\
super().\_\_init\_\_()\
\# 使用多层感知机增强单射属性\
self.conv1 = GINConv(Sequential(Linear(in_channels, hidden_channels),
ReLU(), Linear(hidden_channels, hidden_channels)))\
self.conv2 = GINConv(Sequential(Linear(hidden_channels,
hidden_channels), ReLU(), Linear(hidden_channels, hidden_channels)))\
self.global_pool = global_add_pool \# 加法聚合保留结构完整性\
\
def forward(self, x, edge_index, batch):\
h = self.conv1(x, edge_index).relu()\
h = self.conv2(h, edge_index).relu()\
\# 产生全图级别的拓扑嵌入向量\
return self.global_pool(h, batch)

这种方案的工程优势在于其推理延迟极低（通常在 1-5ms 级别），远低于 LLM
的推理成本，且能够支持动作空间中"增删节点"导致的动态维度变化。

## 4. 受约束动作空间的分层详细设计

元Harness
优化器的动作空间设计必须在"赋予智能体创造力"与"防止系统崩溃"之间建立刚性约束。建议将动作空间划分为四层阶梯式结构。

### 层级 1：参数微调（Parametric Fine-tuning）

这是最基础的动作层，针对 XML 配置中的数值和枚举属性进行优化。

- **操作范畴**：修改 temperature、max_tokens、top_k、Memory
  缓存策略中的淘汰阈值等。

- **边界条件**：参数值必须符合 XML Schema 定义的区间约束。

- **转移动作**：若连续三轮参数微调未带来 Hypervolume
  提升，系统应自动升级至层级 2。

### 层级 2：连接拓扑重构（Connection Rewiring）

通过修改组件间的 Connection 标签来优化信息流。

- **操作范畴**：增加重试路径、改变 Policy 组件的干预优先级、引入
  Evaluator 与 Optimizer 之间的直接反馈链路。

- **接口契约检查**：利用静态 XML 校验确保 Connection.source 的输出
  Schema 与 Connection.target 的输入 Schema 匹配 ^7^。不合法的连接（如将
  JSON 对象输入到图片解码器）将在动作生成阶段被硬过滤。

### 层级 3：组件模板实例化（Template-based Instantiation）

从预定义的组件模板库中引入新功能块。

- **操作范畴**：检测到任务涉及复杂数学时，实例化一个 Symbolic_Calculator
  模板；检测到长文本处理时，引入 Semantic_Chunker。

- **机制**：优化器从 Component_Pool 中挑选最佳候选，并生成相应的初始化
  XML 配置。

- **优势**：模板是经过工业验证的"安全逻辑单元"，其故障率极低。

### 层级 4：有限度 LLM 代码生成（Restricted Program Synthesis）

当上述手段均失效时，允许 LLM 在受限的沙箱内生成新的原子代码片段。

- **操作范畴**：为 Gateway 编写特定的解析函数，或为 Evaluation
  编写自定义的评分逻辑。

- **严苛约束**：生成的 Python 代码必须通过 mypy 静态类型检查、bandit
  安全扫描，且在预定义的 Unit Test 下运行无误 ^14^。任何引起 Runtime
  崩溃的代码动作将导致即时的严重奖励惩罚（Negative Reward）。

这种四层结构构建了一个防御性的搜索漏斗，将高风险、高成本的代码生成操作限制在极小的搜索半径内，从而显著提高了搜索的稳定性
^23^。

## 5. 模板驱动与自由形式代码生成的效能差距

在元Harness
优化器的设计中，关于"代码生成应采用何种粒度"的争论至关重要。实证研究显示，模板驱动（Template-based）与自由形式（Free-form）生成在错误率和可维护性上存在鸿沟。

### 效能对比量化分析表

  ----------------------------------------------------------------------------------
  **评估维度**           **模板驱动 (Slot  **自由形式 (Full       **统计证据支持**
                         Filling)**        Program Gen)**         
  ---------------------- ----------------- ---------------------- ------------------
  **首轮通过率           85% - 92%         25% - 34% (真实场景)   ^25^
  (Pass@1)**                                                      

  **语法/类型错误率**    \< 2%             15.6% - 19.8%          ^27^

  **逻辑回归             极低 (结构固定)   较高 (副作用难以追踪)  ^28^
  (Regression) 频率**                                             

  **静态检查过滤效率**   极高 (Schema      中                     ^30^
                         可预测)           (逻辑复杂导致伪阳性)   

  **推理时延增量**       近乎零 (替换片段) 显著 (全量重构/校验)   ^31^
  ----------------------------------------------------------------------------------

模板驱动生成的优势源于其对 LLM 的"诱导式约束"。当 LLM 只需在 def
process(data: dict) -\> dict:
的槽位中填充逻辑时，其输出更符合预训练数据中的函数级模式
^26^。而自由形式生成往往会引入冗余的依赖包、非标准的类定义，甚至是与现有
Harness 架构冲突的并行线程逻辑，导致系统在集成阶段崩溃 ^24^。

因此，元Harness 模板库应具备"细粒度骨架"特征。优化器不应要求 LLM
写一个完整的 Memory 类，而应提供包含 save()、retrieve() 接口的骨架，仅让
LLM
实现其核心的"相关度计算函数"。这种"带槽位的细粒度模板"在接口稳定性与可组合性之间达到了最佳平衡点。

## 6. Meta-Harness Proposer 机制深度剖析与迁移

Meta-Harness 的 Proposer（通常基于 Claude Code +
Opus-4.6）展现了目前最先进的"自我重构"能力。通过对其文件系统接口与诊断逻辑的还原，可以为元Harness
优化器提供直接的借鉴路径。

### 6.1 核心工作机制解析

Proposer
的高效源于其对"全量信息"的非对称访问。不同于传统优化器只看最终得分（Score），Meta-Harness
的 Proposer 具备以下 5 个核心机制：

1.  **全历史文件系统接入**：Proposer
    并不被强制加载所有历史作为上下文，而是使用 grep、cat
    等工具按需读取。它会查看 median 82 个文件，涉及 20+ 个候选
    Harness，这种"按需检索"打破了模型上下文窗口的限制 ^1^。

2.  **反事实诊断 (Counterfactual Diagnosis)**：Proposer
    会对比两个得分迥异但结构相似的
    Harness，读取它们的执行轨迹摘要。通过分析"为什么在步骤 T，Harness A
    调用了工具 X 而 Harness B 选择了等待"，实现对失败模式的精准归因
    ^15^。

3.  **读-写-执行 (RWE) 闭环**：Proposer 具备在文件系统中直接修改 Python
    源码、运行测试并观察控制台报错的能力。它更像是一个具有自主权的开发者，而非一个被动的生成模型
    ^14^。

4.  **局部突变主导定律**：统计显示，Proposer
    倾向于进行局部代码修改（比例约
    85%），极少进行整体重写。这种演化策略确保了搜索的连续性，降低了大幅退化的风险。

5.  **失败归因与恢复策略**：当检测到回归（即新版本性能低于旧版本）时，Proposer
    不会简单地回滚，而是会分析"为什么这个修改在任务 A 上起效但在任务 B
    上失效"，从而提取出针对特定子任务的条件分支逻辑 ^14^。

### 6.2 迁移至 XML 配置空间的可行性分析

  ----------------------------------------------------------------------------------------------
  **机制名称**           **迁移方式建议**                   **难度/风险**     **可行性**
  ---------------------- ---------------------------------- ----------------- ------------------
  **文件系统轨迹读取**   将 XML 历史记录与每轮运行的 JSON   低                **可直接迁移**
                         Log 存放在统一目录，允许 Proposer                    
                         检索。                                               

  **代码级反事实诊断**   将诊断对象从"源代码差异"变为"XML   中                **需适配后迁移**
                         节点差异"。                                          

  **RWE 闭环**           允许 Proposer 修改 XML 文件并触发  低                **可直接迁移**
                         Runtime 自动热重载进行评估。                         

  **Unit Test 验证**     XML 结构调整后必须先通过 XSD       极低              **可直接迁移**
                         Schema 校验。                                        

  **Trace 全量分析**     需将 10M tokens 的详细 Trace       高                **不适用于 XML
                         压缩为分层的逻辑树，以便快速                         纯文本**
                         grep。                                               
  ----------------------------------------------------------------------------------------------

### 6.3 "最小可行 Proposer"设计建议

为元Harness 优化器设计的轻量级 Proposer 应包含以下三个核心组件：

- **Log Gopher**：负责将 Evaluation 产生的非结构化 Trace
  转化为带时间戳的结构化 JSON。

- **Diff Analyzer**：利用 LLM
  对比当前最优（Elite）与历史失败案例的配置差异，生成诊断意见。

- **XML Patcher**：基于诊断意见，使用 xpath
  形式生成局部配置增量，而非重写整个 XML 文件。

## 7. Noisy 环境下的统计收敛判据实现指南

在 Agent 系统的性能评估中，LLM 的输出具有随机性，API
请求存在时延方差。在这种"充满噪声"的环境中，单纯依赖超体积（Hypervolume）数值的波动来判断收敛是极其危险的。

### 7.1 三重收敛判据架构

建议采用 Hypervolume + 统计检验 + 复杂度上限的复合判据：

1.  **Pareto 超体积收敛 (HV-Criterion)**： 当 \$\\Delta HV = HV\_{t+1} -
    HV_t \< \\varepsilon\$ 且连续 \$K\$
    轮保持平稳时触发。这标志着系统在多目标优化空间内已触及"收益递减"边缘
    ^34^。

2.  **统计显著性收敛 (Significance-Criterion)**：
    由于评估存在噪声，需对当前 Top-3 Harness 进行多次重复运行（如
    \$N=10\$）。使用 **配对 t 检验 (Paired t-test)** 或其非参数版本
    **Wilcoxon 符号秩检验** 计算 p-value。若 \$p \> \\alpha\$ 且连续
    \$K\$
    轮无法拒绝"新旧架构性能无差异"的假设，则强制停止。这有效防止了由偶然高分引起的"假突变"
    ^36^。

3.  **复杂度饱和惩罚 (Complexity-Cap)**：\
    基于 \$R_t\$ 中的 \$-\\lambda \\cdot \\Delta\_{\\text{complexity}}\$
    项。当组件总数触及预设阈值（如
    \$N=20\$）或连接深度过深导致推理时延突破 SLA
    限制时，无论性能是否仍在提升，优化器必须停止生长。

### 7.2 收敛判据配置参数推荐表

根据不同任务的噪声水平，建议采用以下经验配置 ^31^：

  ---------------------------------------------------------------------------------------------------
  **任务领域类型**        **K            **ε (HV     **α          **λ              **重复实验次数**
                          (轮次阈值)**   容差)**     (显著性)**   (复杂度系数)**   
  ----------------------- -------------- ----------- ------------ ---------------- ------------------
  **逻辑推理 (MATH/IMO)** 8 - 12         0.0005      0.01         0.05             10+

  **代码生成              5 - 8          0.0010      0.05         0.15             5+
  (SWE-bench)**                                                                    

  **信息分类              3 - 5          0.0050      0.05         0.30             3+
  (Classification)**                                                               

  **多轮对话/工具调用**   10+            0.0001      0.01         0.10             15+
  ---------------------------------------------------------------------------------------------------

在实现中，应结合 **贝叶斯优化中的采集函数 (Acquisition
Function)**。使用期望提升（EI）或置信上限（UCB）来决定是否继续探索某个不确定性极高但潜力巨大的分支。如果所有分支的
EI 均低于评估成本阈值，则视为全局收敛。

## 8. 对《Meta-Harness 工程设计手册》的行动化补强建议

为使本书从"意图"升级为"蓝图"，建议针对第 3、4、5 章进行以下精准强化：

### 8.1 第 3 章补强建议：接口契约的剪枝作用

- **新增小节**：3.4 契约驱动的动作空间剪枝策略

- **核心论点**：详细论证通过静态 XML 接口定义（Input/Output Type
  Enforcement）可以将优化器的搜索空间缩减 10-100 倍。

- **建议图表**：绘制一张对比图，展示"盲目随机连接"与"基于契约的合法连接"在搜索步数上的差距。

### 8.2 第 4 章补强建议：Optimizer 算法骨架

- **新增小节**：4.5 状态编码的工程权衡：从 MLP 到 GIN

- **核心论点**：分析为什么在元Harness
  中不能使用简单的固定向量编码，并提供基于 PyTorch Geometric 的 GIN
  编码器实现伪代码 ^21^。

- **新增配置指南**：直接插入本文 7.2
  节的收敛参数表，将其命名为《元Harness 优化器收敛调优速查表》。

### 8.3 第 5 章补强建议：代码生成管线与诊断

- **新增小节**：5.3 细粒度模板：代码生成的安全护栏

- **核心论点**：引用 ^25^ 的数据，论证为什么元Harness
  必须坚持槽位填充模式（Slot Filling）而非全量代码生成。

- **建议插入对比矩阵**：对比"无意识变异"与"基于反事实诊断的
  Proposer"在收敛速度上的差异。

- **新增伪代码**：提供一个"反事实诊断提示词模板"，展示如何引导 Proposer
  分析两个运行轨迹的差异。

## 9. 结论

元Harness
优化器的工业级实现，本质上是一个在离散图结构上进行的高效信贷分配（Credit
Assignment）问题。通过引入 **GIN
状态编码**，我们解决了架构感知难题；通过
**四层受限动作空间**，我们平衡了创造力与稳定性；而 **Meta-Harness 风格的
Proposer 机制** 则为解决样本效率问题提供了"反事实诊断"这一终极武器。

对于《Meta-Harness 工程设计手册》而言，将统计学上的显著性检验与 Pareto
超体积收敛有机结合，是确保元智能体"自我重长"过程不陷入噪声驱动的假进化的唯一路径。这不仅是一项算法优化，更是智能体系统开发从"玄学调优"向"可预测系统工程"迈出的决定性一步。未来的元Harness
将不再是一个静态的支架，而是一个能够在性能与复杂度之间，通过自我博弈不断寻找最优纳什均衡点的动态生命体。

#### 引用的著作

1.  Meta-Harness: End-to-End Optimization of Model Harnesses - arXiv,
    访问时间为 四月 17, 2026，
    [[https://arxiv.org/pdf/2603.28052]{.underline}](https://arxiv.org/pdf/2603.28052)

2.  Meta-Harness: End-To-End Optimization of Model Harnesses - Yoonho
    Lee, 访问时间为 四月 17, 2026，
    [[https://yoonholee.com/meta-harness/paper.pdf]{.underline}](https://yoonholee.com/meta-harness/paper.pdf)

3.  AUTOMATED DESIGN OF AGENTIC SYSTEMS - OpenReview, 访问时间为 四月
    17, 2026，
    [[https://openreview.net/pdf?id=t9U3LW7JVX]{.underline}](https://openreview.net/pdf?id=t9U3LW7JVX)

4.  arXiv:2408.08435v2 \[cs.AI\] 2 Mar 2025, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/pdf/2408.08435]{.underline}](https://arxiv.org/pdf/2408.08435)

5.  Evolving Reinforcement Learning Algorithms \| by bellman - Medium,
    访问时间为 四月 17, 2026，
    [[https://bellman-silentist.medium.com/evolving-reinforcement-learning-algorithms-c9c85ce51c09]{.underline}](https://bellman-silentist.medium.com/evolving-reinforcement-learning-algorithms-c9c85ce51c09)

6.  AlphaDev - Wikipedia, 访问时间为 四月 17, 2026，
    [[https://en.wikipedia.org/wiki/AlphaDev]{.underline}](https://en.wikipedia.org/wiki/AlphaDev)

7.  AGENTSQUARE: AUTOMATIC LLM AGENT SEARCH IN MODULAR DESIGN SPACE -
    ICLR Proceedings, 访问时间为 四月 17, 2026，
    [[https://proceedings.iclr.cc/paper_files/paper/2025/file/0ae94013da7cd459402fd77874e09ee3-Paper-Conference.pdf]{.underline}](https://proceedings.iclr.cc/paper_files/paper/2025/file/0ae94013da7cd459402fd77874e09ee3-Paper-Conference.pdf)

8.  MAS-Zero: Designing Multi-Agent Systems with Zero Supervision -
    arXiv, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2505.14996v4]{.underline}](https://arxiv.org/html/2505.14996v4)

9.  BayesFlow: A Probability Inference Framework for Meta-Agent Assisted
    Workflow Generation - ACL Anthology, 访问时间为 四月 17, 2026，
    [[https://aclanthology.org/2026.findings-eacl.165.pdf]{.underline}](https://aclanthology.org/2026.findings-eacl.165.pdf)

10. Multi-Agent Design: Optimizing Agents with Better Prompts and
    Topologies - arXiv, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2502.02533v1]{.underline}](https://arxiv.org/html/2502.02533v1)

11. MULTI-AGENT DESIGN: OPTIMIZING AGENTS WITH BETTER PROMPTS AND
    TOPOLOGIES - OpenReview, 访问时间为 四月 17, 2026，
    [[https://openreview.net/pdf?id=I05H9RUzHB]{.underline}](https://openreview.net/pdf?id=I05H9RUzHB)

12. What is RL for Robotics? \| Activeloop Glossary, 访问时间为 四月 17,
    2026，
    [[https://www.activeloop.ai/resources/glossary/reinforcement-learning-for-robotics/]{.underline}](https://www.activeloop.ai/resources/glossary/reinforcement-learning-for-robotics/)

13. Project Silicon: What If We Could Do Gradient Descent on Assembly
    Code? \| rewire.it, 访问时间为 四月 17, 2026，
    [[https://rewire.it/blog/project-silicon-gradient-descent-on-assembly-code/]{.underline}](https://rewire.it/blog/project-silicon-gradient-descent-on-assembly-code/)

14. Report on META-HARNESS - Hugging Face, 访问时间为 四月 17, 2026，
    [[https://huggingface.co/blog/Svngoku/meta-harness-end-to-end-optimization-of-model]{.underline}](https://huggingface.co/blog/Svngoku/meta-harness-end-to-end-optimization-of-model)

15. Meta-Harness: End-to-End Optimization of Model Harnesses - Yoonho
    Lee, 访问时间为 四月 17, 2026，
    [[https://yoonholee.com/meta-harness/]{.underline}](https://yoonholee.com/meta-harness/)

16. Towards Heterogeneous Multi-Agent Reinforcement Learning with Graph
    Neural Networks, 访问时间为 四月 17, 2026，
    [[https://sol.sbc.org.br/index.php/eniac/article/download/12161/12026/]{.underline}](https://sol.sbc.org.br/index.php/eniac/article/download/12161/12026/)

17. A NOVEL FRAMEWORK FOR INVARIANT NEURAL NETWORKS APPLIED TO GRAPH AND
    SET DATA, 访问时间为 四月 17, 2026，
    [[https://hammer.purdue.edu/ndownloader/files/27780936]{.underline}](https://hammer.purdue.edu/ndownloader/files/27780936)

18. Graph Learning in Bioinformatics: A Survey of Graph Neural Network
    Architectures, Biological Graph Construction and Bioinformatics
    Applications - PMC, 访问时间为 四月 17, 2026，
    [[https://pmc.ncbi.nlm.nih.gov/articles/PMC12938586/]{.underline}](https://pmc.ncbi.nlm.nih.gov/articles/PMC12938586/)

19. Survey of Graph Neural Network for Internet of Things and NextG
    Networks - arXiv, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2405.17309v2]{.underline}](https://arxiv.org/html/2405.17309v2)

20. Explainable Multimodal Graph Isomorphism Network for Interpreting
    Sex Differences in Adolescent Neurodevelopment - MDPI, 访问时间为
    四月 17, 2026，
    [[https://www.mdpi.com/2076-3417/14/10/4144]{.underline}](https://www.mdpi.com/2076-3417/14/10/4144)

21. Scalable Custom Instruction Identification using Graph Neural
    Networks and Reinforcement Learning - TechRxiv, 访问时间为 四月 17,
    2026，
    [[https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.174702136.65195692]{.underline}](https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.174702136.65195692)

22. SuperagenticAI/metaharness: Meta Harness Implementation - GitHub,
    访问时间为 四月 17, 2026，
    [[https://github.com/SuperagenticAI/metaharness]{.underline}](https://github.com/SuperagenticAI/metaharness)

23. SEAR: Schema-Based Evaluation and Routing for LLM Gateways - arXiv,
    访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2603.26728v1]{.underline}](https://arxiv.org/html/2603.26728v1)

24. The Capabilities and Limitations of Large Language Models in
    Document Automation, 访问时间为 四月 17, 2026，
    [[https://parseur.com/blog/llms-document-automation-capabilities-limitations]{.underline}](https://parseur.com/blog/llms-document-automation-capabilities-limitations)

25. Beyond Synthetic Benchmarks: Evaluating LLM Performance on
    Real-World Class-Level Code Generation - arXiv, 访问时间为 四月 17,
    2026，
    [[https://arxiv.org/html/2510.26130v2]{.underline}](https://arxiv.org/html/2510.26130v2)

26. Self-Spec: Model-Authored Specifications for Reliable LLM Code
    Generation - OpenReview, 访问时间为 四月 17, 2026，
    [[https://openreview.net/pdf?id=6pr7BUGkLp]{.underline}](https://openreview.net/pdf?id=6pr7BUGkLp)

27. Evaluating the Performance of LLM-Generated Code for ChatGPT-4 and
    AutoGen Along with Top-Rated Human Solutions - Computer Science,
    访问时间为 四月 17, 2026，
    [[https://www.cs.wm.edu/\~dcschmidt/PDF/ChatGPT_vs\_\_Stack_Overflow_Performance.pdf]{.underline}](https://www.cs.wm.edu/~dcschmidt/PDF/ChatGPT_vs__Stack_Overflow_Performance.pdf)

28. SWE-Adept: An LLM-Based Agentic Framework for Deep Codebase Analysis
    and Structured Issue Resolution - arXiv, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2603.01327v1]{.underline}](https://arxiv.org/html/2603.01327v1)

29. MCP-enabled LLM for meta-optics inverse design: leveraging
    differentiable solver without LLM expertise - PMC, 访问时间为 四月
    17, 2026，
    [[https://pmc.ncbi.nlm.nih.gov/articles/PMC12717938/]{.underline}](https://pmc.ncbi.nlm.nih.gov/articles/PMC12717938/)

30. LLM-Guided Proof Search - Emergent Mind, 访问时间为 四月 17, 2026，
    [[https://www.emergentmind.com/topics/llm-guided-proof-search]{.underline}](https://www.emergentmind.com/topics/llm-guided-proof-search)

31. Comparative Performance Analysis of Large Language Models for
    Structured Data Processing: An Evaluation Framework Applied to
    Bibliometric Analysis - MDPI, 访问时间为 四月 17, 2026，
    [[https://www.mdpi.com/2076-3417/16/2/669]{.underline}](https://www.mdpi.com/2076-3417/16/2/669)

32. Comparing LLM-based and MDE-based code generation for agile MDE -
    CEUR-WS.org, 访问时间为 四月 17, 2026，
    [[https://ceur-ws.org/Vol-4122/paper13.pdf]{.underline}](https://ceur-ws.org/Vol-4122/paper13.pdf)

33. Notes on: Meta-Harness: End-to-End Optimization of Model Harnesses
    by Lee, Y., Nair, R., Zhang, Q., Lee, K., Khattab, O., &
    Finn, C. (2026) - Hugo Cisneros, 访问时间为 四月 17, 2026，
    [[https://hugocisneros.com/notes/leemetaharnessendtoend2026/]{.underline}](https://hugocisneros.com/notes/leemetaharnessendtoend2026/)

34. (PDF) A Convergence Criterion for Multiobjective Evolutionary
    Algorithms Based on Systematic Statistical Testing - ResearchGate,
    访问时间为 四月 17, 2026，
    [[https://www.researchgate.net/publication/220702011_A_Convergence_Criterion_for_Multiobjective_Evolutionary_Algorithms_Based_on_Systematic_Statistical_Testing]{.underline}](https://www.researchgate.net/publication/220702011_A_Convergence_Criterion_for_Multiobjective_Evolutionary_Algorithms_Based_on_Systematic_Statistical_Testing)

35. Hypervolume-Based Multi-Objective Optimization Method Applying Deep
    Reinforcement Learning to the Optimization of Turbine Blade Shape -
    MDPI, 访问时间为 四月 17, 2026，
    [[https://www.mdpi.com/2673-2688/5/4/85]{.underline}](https://www.mdpi.com/2673-2688/5/4/85)

36. HEAS: HIERARCHICAL EVOLUTIONARY AGENT-BASED SIMULATION FRAMEWORK FOR
    MULTI-OBJECTIVE POLICY SEARCH - arXiv, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2508.15555v3]{.underline}](https://arxiv.org/html/2508.15555v3)

37. Why and How We t-Test \| Towards AI, 访问时间为 四月 17, 2026，
    [[https://towardsai.net/p/machine-learning/why-and-how-we-t-test]{.underline}](https://towardsai.net/p/machine-learning/why-and-how-we-t-test)

38. Shoot First, Ask Questions Later? Building Rational Agents that
    Explore and Act Like People, 访问时间为 四月 17, 2026，
    [[https://arxiv.org/html/2510.20886v2]{.underline}](https://arxiv.org/html/2510.20886v2)

39. Graph Neural Networks: When and Why \| 2026 Guide - CodeSOTA,
    访问时间为 四月 17, 2026，
    [[https://www.codesota.com/guides/graph-neural-networks]{.underline}](https://www.codesota.com/guides/graph-neural-networks)
