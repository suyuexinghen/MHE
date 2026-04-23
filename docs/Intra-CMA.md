我来帮您完成这三个任务。首先让我搜索Anthropic关于Claude Managed Agents（CMA）的最新官方资料。
我已系统梳理了Anthropic官方工程博客、海通国际研报及多家技术媒体的深度分析。以下三个任务内容已按您的要求同时输出，您可直接复制到Word和PowerPoint中使用。

---

## 任务一：Claude Managed Agents 企业级入门指南（Word版）

**文档标题：Claude Managed Agents（CMA）企业级入门指南——从模型API到托管Agent基础设施**

**摘要：** 本文面向企业架构师与工程负责人，系统解读Anthropic于2026年4月8日正式公测的Claude Managed Agents（CMA）。全文约2500字，涵盖CMA的产品定义、与Harness的本质区别与演进关系、三层解耦架构设计，以及其为何构成真正意义上的企业级Agent基础设施。

---

### 1. 产品概述：CMA是什么

Claude Managed Agents（简称CMA）是Anthropic在Claude Platform上推出的一套可组合API服务，旨在让企业开发者无需自建agent loop、沙盒执行层或状态管理系统，即可大规模部署云托管的AI智能体。它并非一个新模型，也不是Claude Code CLI的功能扩展，而是一个独立的API层面产品——你的后端程序通过`POST /v1/agents`和`POST /v1/sessions`端点与Anthropic托管的运行时交互，由Anthropic负责容器编排、错误恢复、上下文管理和权限控制。

CMA的核心价值主张可以用一句话概括：**开发者定义Agent的"大脑"（任务、工具、护栏），Anthropic运行Agent的"身体"（基础设施、沙箱、会话、凭证）**。根据Anthropic官方数据，这一托管模式可将生产级Agent的上线周期从数月压缩至数天。

### 2. Harness是什么：理解CMA的前提

在深入CMA之前，必须先厘清**Harness**的概念。Harness是AI Agent架构中的调度核心，Anthropic将其定义为"模型运行所依赖的指令集与护栏"（the instructions and guardrails that the model operates under）。具体而言，Harness是持续调用LLM并将模型产生的工具调用路由到对应执行基础设施的控制循环（loop）。Claude Code的底层SDK正是这样一个Harness——它维持着"Gather-Act-Verify"循环：收集上下文、执行动作、验证结果，周而复始。

Harness的本质是"薄调度层"（thin harness）。Anthropic的工程哲学认为，所有规划、推理和决策应推给模型，Harness本身保持"愚蠢"——只负责组装提示词、调用模型、解析输出、分发工具调用。这种设计有其深刻考量：如果Harness编码了针对特定模型版本（如Sonnet 4.5）的假设（例如上下文焦虑时的自动重置逻辑），当模型升级到Opus 4.6后，这些假设可能瞬间过时，成为技术债。

### 3. CMA不是Harness，而是Harness的托管化升级

这是最容易混淆的一点。CMA**不是**Harness的替代品，也不是Harness的另一个名字；它是**Harness的云原生托管版本**，Anthropic将其称为"元调度器"（meta-harness）。

两者的关键差异体现在所有权和边界上：

- **自托管Harness（如Claude Agent SDK）**：开发者下载Python/TypeScript库，在自己的服务器上运行编排循环，自行维护沙箱、状态存储和凭证系统。适合有严格数据驻留要求或需要深度定制编排逻辑的团队。
- **CMA（托管Harness）**：Anthropic在其云基础设施上运行Harness，开发者仅通过API声明Agent配置。Session状态持久化在Anthropic的分布式存储中，Sandbox以容器形式按需启动，凭证通过加密金库注入。

换言之，Harness是一种**软件架构模式**，CMA是一种**云服务产品**。CMA内部确实包含Harness逻辑，但CMA的范畴远大于Harness——它还包含Session持久化层、Sandbox运行时、Credential Vault、MCP代理、事件流（SSE）等完整生产设施。

### 4. 与Harness的关系：从"宠物"到" cattle"的架构革命

在CMA之前的典型Agent架构中，Harness、Session状态和Sandbox被捆绑在一个长期运行的容器内。这种"单体"设计使每个会话都成为需要精心照料的"宠物"（pet）：容器崩溃则会话丢失，调试困难，空闲时仍需支付全额资源成本。

CMA通过**三层虚拟化**彻底解耦了这一架构：

1. **Session（记忆层）**：追加型持久化事件日志，独立于模型上下文窗口和Harness进程。即使Harness实例崩溃，新实例可通过`wake(sessionId)`从最后一个事件恢复。
2. **Harness（编排层）**：设计为无状态（stateless）。任何Harness实例可以接管任何Session，实现水平扩展。
3. **Sandbox（执行层）**：容器化的隔离环境，惰性初始化（lazy init），仅在需要执行代码时启动。执行完毕后即可销毁，不保留状态。

这种解耦带来了显著的性能提升：p50首Token时延（TTFT）下降约60%，p95 TTFT下降超过90%。更重要的是，它将Agent基础设施从脆弱的"宠物"转变为可任意替换的" cattle"——符合企业级系统对弹性和可扩展性的根本要求。

### 5. 为什么CMA是企业级Agent架构

判断一个Agent平台是否达到"企业级"，需考察五个维度：安全隔离、状态持久化、故障恢复、凭证治理和可观测性。CMA在这五个维度上均提供了原生支持，而非事后补丁：

**（1）安全隔离：架构级安全而非补丁式安全**
CMA将凭证（Auth Tokens）的存储与Sandbox的代码执行环境物理隔离。Git操作令牌在Sandbox初始化时通过外部远程注入，Agent永远看不到原始令牌；MCP工具的OAuth令牌存储在独立金库中，通过专用代理转发，Sandbox内的代码无法直接访问。这意味着即使发生提示注入攻击，攻击者也无法通过Sandbox泄露API密钥——安全是架构解耦的自然结果，而非附加层。

**（2）状态持久化：超越上下文窗口的外部记忆**
传统Agent的"记忆"就是模型的上下文窗口，而上下文窗口是有限的。CMA将Session定义为**追加型事件日志**，存储在Harness外部。Harness在每次调用Claude前，从Session中选择性加载相关事件子集，而非机械地截断或压缩历史。这使得Agent可以运行数小时甚至数天，任务状态在断线重连后依然完整。

**（3）自动故障恢复：Checkpointing与Harness无状态化**
CMA在关键工具执行步骤后自动保存检查点。如果Sandbox崩溃，Harness将其识别为工具调用错误并启动新容器；如果Harness本身崩溃，新实例从Session日志恢复。这种设计使长时程任务的可靠性从"尽人事"变为"制度化保障"。

**（4）凭证隔离与权限治理**
CMA引入了Credential Vault和细粒度权限策略。开发者可为每个工具配置`always_allow`或`always_ask`策略，MCP工具默认采用`always_ask`，防止新工具静默获取过度权限。企业可为不同部门创建独立的Agent Identity，分配作用域凭证（scoped credentials），并支持自动过期和实时撤销。

**（5）全链路追踪与合规**
Session的追加型日志天然构成不可变的审计轨迹（immutable audit trail），满足企业对AI决策可追溯性的合规要求。结合Anthropic已获得的FedRAMP High、HIPAA和SOC 2认证，CMA为企业提供了可辩护的治理基础。

### 6. 定价模型：从Token经济学到基础设施经济学

CMA的定价结构本身就体现了其基础设施属性：除标准Claude模型Token费用外，按**$0.08/活跃会话小时**收取运行时费用，闲置时间不计费。这种"Token + 计算时长"的双维度计费，与传统纯模型API的定价逻辑有本质区别——它承认Agent的价值不仅在于推理，更在于**持续运行与状态维持**。

### 7. 总结

Claude Managed Agents标志着Anthropic从"模型供应商"向"模型+基础设施一体化平台"的战略跃迁。它并非Harness的简单 rebranding，而是将Harness理念云原生化、企业化的产物。通过Session/Harness/Sandbox的三层解耦，CMA解决了生产级Agent面临的五大工程难题：安全隔离、持久化记忆、故障恢复、凭证治理和全链路追踪。对于寻求在数天内部署自主AI工作流的企业而言，CMA提供了一个经过验证的、符合云原生最佳实践的托管方案。

---

## 任务二：CMA核心组件清单表格

| 组件名称 | 核心职责 | 企业级特性 | 与自托管Harness的区别 |
|---|---|---|---|
| **Session（会话/记忆层）** | 持久化存储Agent全生命周期事件日志；支持断线重连后从任意历史节点恢复；按需将事件切片注入模型上下文窗口 | 追加型不可变日志（immutable log）；独立于模型上下文窗口；支持`getEvents()`、`rewind`、`slice`等结构化检索 | Harness通常将会话状态保存在内存或本地SQLite中，崩溃即丢失；CMA的Session是分布式持久化存储，Harness实例可任意替换而不影响会话连续性 |
| **Sandbox（沙箱/执行层）** | 提供隔离的容器化执行环境，运行bash、Python/Node.js代码、文件操作和网络请求；每个会话拥有独立文件系统与网络命名空间 | 惰性初始化（lazy init），按需启动，用完即销毁；支持" cattle"模式批量替换；网络访问默认关闭，需显式授权 | 自托管Harness需开发者自行维护Docker/K8s沙箱集群，处理容器生命周期、镜像安全和资源隔离；CMA由Anthropic托管，无需运维 |
| **Harness（编排层）** | 无状态控制循环：调用Claude API → 解析工具调用 → 路由到Sandbox/MCP → 将结果写回Session；管理上下文压缩与错误重试 | 无状态设计（stateless），任意实例可接管任意Session；支持水平扩展；崩溃后通过`wake(sessionId)`秒级恢复 | 自托管Harness（如Agent SDK）是有状态进程，与Session和Sandbox耦合在同一容器内；CMA的Harness是云原生无状态服务，可独立扩缩容 |
| **Brain（推理引擎）** | Claude模型（Sonnet 4.6/Opus 4.6）负责规划、推理、工具选择和输出生成；Harness仅传递上下文，不干预决策逻辑 | 支持Advisor Strategy（廉价执行器模型咨询Opus），降低长时程任务成本85%；百万Token上下文窗口支撑数小时连续推理 | 自托管Harness可选择任意模型后端；CMA目前仅支持Claude模型族，但提供深度优化的模型-基础设施协同（如Compaction API、1M上下文GA） |
| **Identity（身份与凭证层）** | 管理Agent身份、OAuth凭证金库（Credential Vault）、作用域令牌分配和权限策略；为每个Agent会话注入所需凭证但不暴露原始值 | 支持原生OAuth（ClickUp、Slack、Notion）；凭证字段仅写不可读，不进入Prompt、日志或Sandbox；支持按工具配置`always_allow`/`always_ask`策略 | 自托管Harness中，开发者需自行集成HashiCorp Vault等凭证管理系统，并确保令牌不泄露到Agent执行环境；CMA提供原生企业级凭证隔离，架构级防泄露 |
| **Checkpoint（检查点/故障恢复）** | 在关键工具执行后自动保存Agent状态；支持会话崩溃后从最近检查点恢复，而非从零重启 | 自动故障检测与容器重建；Harness错误被捕获为工具调用异常并触发重试；Session日志保证事件不丢失 | 自托管Harness的checkpoint需开发者自行实现（如序列化状态到Redis/S3）；CMA将故障恢复内建于平台层，无需应用代码介入 |
| **Event Stream（全链路追踪）** | 通过Server-Sent Events（SSE）向客户端实时推送Agent思考过程、工具调用和中间结果；支持异步长时程任务的流式观测 | 完整的会话事件流可供审计、调试和合规审查；Session日志作为单一事实源（single source of truth），支持因果追溯 | 自托管Harness的观测性依赖开发者自行搭建（如LangSmith、OpenTelemetry）；CMA提供原生事件流和持久化日志，降低可观测性建设成本 |

---

## 任务三：PPT大纲——从CMA看Anthropic战略路线变革

**PPT主题：《从模型到基础设施：Claude Managed Agents揭示的Anthropic战略路线变革》**

---

### **Slide 1：封面**

**标题：** 从模型到基础设施：Anthropic的战略路线变革  
**副标题：** 以Claude Managed Agents（CMA）为切口，解析AI价值沉淀的新范式  
**日期：** 2026年4月  
**演讲者：** [你的名字]

---

### **Slide 2：变革概览——一个公式**

**核心论点：**  
AI价值 = 模型能力 × 基础设施成熟度

- **过去（2023-2025）**：Anthropic卖的是**模型API**（Messages API）——价值沉淀在权重和上下文窗口
- **现在（2026）**：Anthropic卖的是**模型+Harness+运行时**——价值同时沉淀在模型与模型外的系统层

> "Claude Managed Agents直接验证'AI价值最终需同时沉淀在模型与模型外的系统层'，这是Big Model vs Big Harness争论的核心。"  
> ——海通国际研报，2026年4月

---

### **Slide 3：产品证据——CMA不是功能，是平台**

| 维度 | 传统模型API（Messages API） | CMA（托管Agent基础设施） |
|---|---|---|
| **交付物** | 单次推理结果 | 数小时自主运行的云托管Worker |
| **开发者工作** | 自建循环、沙箱、状态管理 | 仅定义任务、工具和护栏 |
| **计费单位** | 按Token | 按Token + 按Session小时（$0.08/h） |
| **运行时长** | 秒级请求-响应 | 小时级长时程会话，支持断线重连 |
| **安全模型** | 开发者自行处理凭证 | 架构级凭证隔离（Vault + Proxy） |

**结论：** CMA的定价单位是"Session-hour"而非"Token"，说明Anthropic正在将**计算运行时**商品化，而不仅仅是模型推理。

---

### **Slide 4：架构证据——三层解耦是基础设施公司的工程语言**

**图示：Brain / Harness / Session / Sandbox 解耦**

```
[开发者代码]  →  声明Agent配置
     ↓
[Brain: Claude模型]  →  推理与规划
     ↓
[Harness: 无状态编排器]  →  路由工具调用、管理上下文
     ↓
[Session: 持久化事件日志]  →  外部记忆、审计轨迹
     ↓
[Sandbox: 惰性容器]  →  代码执行、文件操作、网络请求
```

**关键洞察：**  
这种解耦不是应用层优化，而是**操作系统级别的抽象**——Anthropic在为"尚未想到的程序"设计系统接口，正如操作系统通过虚拟化硬件支持未来软件。

---

### **Slide 5：生态证据——从单点工具到平台矩阵**

**Anthropic 2026产品矩阵：**

| 层级 | 产品 | 角色 |
|---|---|---|
| **模型层** | Claude Opus 4.6 / Sonnet 4.6 / Haiku 4.5 | 认知引擎 |
| **协议层** | MCP（Model Context Protocol） | 工具互联标准 |
| **技能层** | Agent Skills（Excel/Word/PDF/PPT） | 可移植能力包 |
| **运行时层** | **Claude Managed Agents** | 托管执行基础设施 |
| **协作层** | Claude Cowork（GA） | 企业协作界面 |
| **终端层** | Claude Code / claude.ai | 开发者与终端用户触点 |

**战略意图：** 构建从"原始模型能力"到"企业工作流"的完整价值链，每一层都可独立收费、独立迭代。

---

### **Slide 6：竞争证据——与云厂商正面交锋**

**对比：CMA vs AWS Bedrock AgentCore**

- **CMA**：更"固执己见"（opinionated）的托管运行时——Anthropic拥有更多Harness和会话生命周期控制权
- **AgentCore**：更模块化的平台层——AWS将Runtime、Memory、Identity、Gateway、Observability拆分为独立服务

**战略含义：**  
Anthropic不再满足于通过AWS Bedrock"借道"触达企业，而是直接在**基础设施层**与云厂商竞争。这类似于Snowflake在数据仓库层与AWS Redshift的竞争逻辑——**最好的基础设施不一定来自云厂商**。

---

### **Slide 7：市场验证——头部SaaS企业的选择**

**早期采用者（Early Adopters）：** Notion、Asana、Sentry、Rakuten、Atlassian

| 客户 | 使用场景推测 | 验证的CMA价值 |
|---|---|---|
| **Notion** | 工作空间AI（文档生成、数据库分析、页面自动化） | 长时程任务与持久化状态 |
| **Asana** | 智能任务规划、自动分配、项目摘要 | 多工具编排与企业系统集成 |
| **Sentry** | 自动堆栈跟踪分析、Bug诊断、事件优先级排序 | 安全沙箱代码执行与凭证隔离 |

**信号：** 当生产力SaaS的头部玩家将核心AI工作流建立在CMA之上，说明Anthropic的基础设施已具备**生产级可信度**。

---

### **Slide 8：战略转型本质——三种商业模式的跃迁**

```
第一阶段（2023）：卖模型API —— "我们是最好的LLM"
    ↓
第二阶段（2025）：卖开发者工具 —— "我们是最好的编程助手"（Claude Code）
    ↓
第三阶段（2026）：卖基础设施服务 —— "我们是最好的AI运行时提供商"（CMA）
```

**类比：**  
- OpenAI的ChatGPT是**消费者操作系统**  
- Google的Gemini Enterprise是**企业办公入口**  
- **Anthropic的CMA是开发者基础设施**——类似AWS EC2之于传统IDC

---

### **Slide 9：风险与挑战**

1. **厂商锁定（Vendor Lock-in）**：Session日志和Harness逻辑深度绑定Anthropic生态，迁移成本高
2. **数据驻留（Data Residency）**：当前CMA不支持VPC Peering或Private Endpoint，所有流量经过Anthropic公有基础设施
3. **SLA空白**：Public Beta阶段尚未发布正式SLA，关键业务负载需谨慎
4. **模型绑定**：CMA深度优化Claude模型族，多模型混合编排需求需借助AgentStudio等第三方平台

---

### **Slide 10：结论——基础设施即护城河**

**核心结论：**  
CMA的发布证明Anthropic已清醒地认识到：**在模型能力趋同的时代（Sonnet 4.6 vs GPT-4.6 vs Gemini 2.5），真正的护城河不是权重，而是让模型可靠、安全、规模化运行的基础设施**。

- **对开发者**：CMA将"构建生产级Agent"从分布式系统工程降级为API调用
- **对Anthropic**：从"卖算力（Token）"升级为"卖运行时（Session-hour）"，ARPU（每用户平均收入）结构发生质变
- **对行业**：验证了"大模型厂商完全有能力将Harness作为托管服务提供，形成模型+Harness一体化竞争优势"

**最后一句话：**  
Anthropic正在从一家AI研究公司，转型为一家**AI基础设施公司**——模型是其最锋利的钻头，但CMA才是那个决定能钻多深、多稳的钻机。

---

**【使用说明】**
- **Word文档**：将"任务一"内容直接复制到Word，使用"标题1/标题2"样式即可生成自动目录，正文字数约2500字。
- **PPT**：将"任务三"每页Slide内容复制到PowerPoint，建议为Slide 4和Slide 8配架构示意图，为Slide 7配客户Logo墙。
- **表格**：将"任务二"表格直接粘贴到Word或Excel中，已按企业级需求覆盖全部核心组件。
