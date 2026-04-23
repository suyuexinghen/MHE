# MHE Wiki 与 Meta-Harness Book 对齐差异报告

## 1. 报告目的

本文档用于比较以下两套文档体系是否一致，并给出结构化的对齐判断：

- `docs/wiki/meta-harness-engineer/meta-harness-wiki/`
- `docs/wiki/meta-harness-book/chapters/*.tex`

本报告关注的不是“代码是否实现”，而是：

1. 两套文档是否描述同一个体系；
2. 它们在术语、能力边界、成熟度表达和写作目的上是否一致；
3. 若存在不一致，哪些地方最值得优先修正。

---

## 2. 总体判断

**结论：两者属于“部分对齐（partially aligned）”，而非完全一致。**

原因可以概括为三点：

- **核心架构骨架一致**：两者都围绕“九大核心基础组件 + 元层 Optimizer”“候选图优先”“分阶段生命周期”“自我重长”“安全链”“可观测性”“热更新”等核心概念展开。
- **写作目的不同**：wiki 更偏工程实现说明，反复标注“当前 MHE 已实现到什么程度”；book 更偏研究/架构手册，强调理想化设计与系统性叙述。
- **成熟度表达不一致**：wiki 对现实状态更保守，常把若干能力标为“最小可运行实现”“部分落地”“目标架构”；book 则常把这些能力作为体系设计的既定部分来展开。

因此，更准确的说法不是“wiki 和 book 矛盾”，而是：

> **两者描述的是同一设计谱系，但 wiki 更接近“现状 + 规划”的工程文档，book 更接近“理论化 + 规范化”的总体设计书。**

---

## 3. 章节映射关系

### 3.1 总体架构与术语

对应关系：

- `docs/wiki/meta-harness-engineer/meta-harness-wiki/README.md`
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md`
- `docs/wiki/meta-harness-book/chapters/ch1_introduction.tex`
- `docs/wiki/meta-harness-book/chapters/ch3_architecture.tex`

这部分对齐度较高。两者都采用：

- PDE/迭代收敛类比；
- 九大核心组件 + Optimizer；
- staged lifecycle；
- 受保护能力边界（Identity、Sandbox、Browser）等总体框架。

但 wiki 在概览部分明确提醒“当前 MHE 多数默认组件仍是最小可运行实现”，见 `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md:46`；而 book 在架构章节更倾向于把这些职责直接作为体系定义的一部分来陈述，见 `docs/wiki/meta-harness-book/chapters/ch3_architecture.tex:78`。

### 3.2 组件 SDK、核心组件与连接引擎

对应关系：

- `02-component-sdk.md`
- `03-core-components.md`
- `04-connection-engine.md`
- `ch3_architecture.tex`

这部分大方向一致，但 wiki 粒度更细，更像“工程分册”；book 粒度更高，更像“总论章节”。book 重点给出组件职责与系统整体结构；wiki 额外细化了 manifest、slot、capability、route 编译与连接验证等工程细节。

### 3.3 自我重长 / 优化器

对应关系：

- `05-self-growth.md`
- `09-template-library.md`
- `ch4_self_growth.tex`
- `ch5_engineering.tex`

两者都承认：Optimizer 是元层组件，动作空间应受约束，且系统不应直接允许任意代码重写。但在具体成熟度叙述上差异明显，后文详述。

### 3.4 安全治理、可观测性与热更新

对应关系：

- `06-safety-governance.md`
- `07-observability-audit.md`
- `08-hot-reload.md`
- `ch4_self_growth.tex`
- `ch5_engineering.tex`

wiki 倾向于为每个子系统给出独立章节；book 则将这些内容吸纳进“工程化实现”和“自增长治理”章节中，因此结构上并非一一镜像，但主题上是对应的。

---

## 4. 最重要的差异类型

## 4.1 最大差异：wiki 会区分“当前实现”与“目标架构”，book 大多不区分

这是最根本的差异。

wiki 在多个章节中都显式加入“实现对齐说明（当前 MHE）”，例如：

- `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md:46`
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/07-observability-audit.md:43`
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/08-hot-reload.md:42`
- `docs/wiki/meta-harness-engineer/meta-harness-wiki/05-self-growth.md:564`

这些段落明确说明：

- 组件大多是最小可运行实现；
- observability 的统一 runtime telemetry / full-chain trace / crash recovery 仍主要停留在设计层；
- 热更新已有 STR 骨架，但蓝绿部署、消息缓冲器、WAL 等更重能力仍未产品化；
- 优化器当前已实现的收敛判据与书中 Hypervolume 叙事并不完全一致。

而 book 在相应位置通常采用更“规范化”的表达，把能力当作体系设计中的既定组成来介绍，例如：

- `docs/wiki/meta-harness-book/chapters/ch3_architecture.tex:78`
- `docs/wiki/meta-harness-book/chapters/ch4_self_growth.tex:63`
- `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:193`
- `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:312`

这会导致读者形成不同预期：

- 读 wiki，会觉得系统已经有骨架，但仍在演进；
- 读 book，会觉得这些能力已经构成一个相对完整的工程体系。

**因此，两者最核心的不一致，不是概念矛盾，而是“现实成熟度表述不一致”。**

---

## 4.2 核心组件职责基本一致，但落地状态表达不同

book 在 `docs/wiki/meta-harness-book/chapters/ch3_architecture.tex:78` 直接定义了 Gateway、Runtime、Memory、ToolHub、Planner、Executor、Evaluation、Observability、Policy / Governance 的职责边界。

wiki 则在 `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md:46` 后明确指出：

- Gateway 尚未具备完整凭证边界 / 身份根；
- Runtime 组件本身并不承担全部调度职责，真实装配主要由 `HarnessRuntime` 负责；
- Memory 还不是完整长期记忆系统；
- ToolHub 不是完整远程工具目录与执行代理系统；
- Evaluation 中 Pareto/frontier 仍主要停留在概念层；
- Policy 已有 proposal reviewer 与 safety pipeline，但独立进程级宪法层仍属后续增强。

也就是说：

- **book 强调“应当如何设计”**；
- **wiki 强调“今天实际做到哪一步”**。

在学术写作中这不是问题，但如果读者把 book 当成当前实现说明，就会高估成熟度。

---

## 4.3 Observability / Replay / Crash Recovery 的差异最明显

这一项是对齐风险最高的地方之一。

wiki 在 `docs/wiki/meta-harness-engineer/meta-harness-wiki/07-observability-audit.md:43` 明确指出：

- 已实做：审计日志、Merkle 锚定、PROV 图、查询接口、反事实诊断；
- 仍主要是设计：统一 runtime telemetry、完整 full-chain trace、crash recovery pipeline、冷热分层存储。

而 book 在 `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:312` 将以下能力直接列为 Observability 必须支持的关键运维能力：

- 全链路 Trace；
- 执行回放（Replay）；
- 崩溃恢复支持。

从表达效果上看，book 给人的印象是这些能力已是系统工程基线；而 wiki 则更谨慎，认为这些仍有较大部分属于架构设计目标。

**结论**：两者在 Observability 的概念层面对齐，但在“是否已成为当前体系的成熟能力”这一点上并不一致。

---

## 4.4 沙箱与隔离体系：book 更强，wiki 更保守

book 在 `docs/wiki/meta-harness-book/chapters/ch3_architecture.tex:118` 与 `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:193` 中，将 Sandbox 作为 Executor / ToolHub 的三级隔离依赖边界，并具体展开了：

- WASM / V8 快速筛选层；
- gVisor / 受限容器通用隔离层；
- Firecracker / MicroVM 深度隔离层。

这是一个很完整的工程化沙箱设计。

wiki 在 `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md:67` 中则明确写道：

- 当前仅“部分落地”；
- 已有 `sandbox_validator.py` 与 `sandbox_tiers.py` 的分层 / 门控抽象；
- 尚不是完整容器 / 微虚机执行平台。

因此，这一差异并非“体系结构不同”，而是：

- book 把三级隔离当作推荐 / 规范化方案；
- wiki 说明当前 MHE 还没有完全实现这一整套后端。

---

## 4.5 优化器叙事：book 更理想化，wiki 更贴近现状

book 在 `docs/wiki/meta-harness-book/chapters/ch4_self_growth.tex:63` 与 `docs/wiki/meta-harness-book/chapters/ch4_self_growth.tex:148` 中，强调：

- Hypervolume 作为核心收敛指标；
- Pareto 前沿作为多目标优化基础；
- GIN 等图编码方法在结构优化中的重要性；
- 奖励函数可直接基于超体积增量构造。

这是一套完整且较强的研究型 optimizer 叙事。

wiki 则在 `docs/wiki/meta-harness-engineer/meta-harness-wiki/05-self-growth.md:564` 非常明确地提醒：

- 当前实现确实已经落地三重收敛控制；
- 但实际判据是 `fitness plateau` / `budget exhausted` / `safety floor met`；
- `ΔHV < ε` 的叙事应理解为研究目标，而不是当前代码中的精确实现。

这说明：

- 两者在优化方向上是对齐的；
- 但 book 更像“目标方法论”；
- wiki 更像“当前实现采用了更务实的近似版本”。

因此，若要严格对齐，两者应当对“现有实现”和“研究目标”做更清楚的分层说明。

---

## 4.6 热更新：机制一致，产品化成熟度不一致

wiki 在 `docs/wiki/meta-harness-engineer/meta-harness-wiki/08-hot-reload.md:42` 指出：

- 当前已有 `suspend()` / `resume()` / `transform_state()`；
- `CheckpointManager` 与 `HotSwapOrchestrator` 已构成可运行骨架；
- 但蓝绿部署、消息缓冲器、观测窗口产品化、ARIES/WAL 等多数仍是目标设计。

而 book 在 `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:231` 之后，系统性展开了：

- Saga 风格的分布式事务回滚；
- 事件回放与补偿逻辑；
- checkpoint 类型；
- 审计轨迹保留策略。

这仍然体现同样的模式：

- **机制思想是对齐的**；
- **当前成熟度叙事并不一致**。

---

## 5. 最值得关注的五项不一致

### 5.1 “当前实现”与“目标设计”的边界不一致

这是最重要的不一致，也是所有后续误读的根源。

- wiki：明确区分现实与目标，见 `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md:46`
- book：常以体系说明口吻叙述目标能力，见 `docs/wiki/meta-harness-book/chapters/ch3_architecture.tex:78`

### 5.2 Observability 的成熟度表达不一致

- wiki：统一 telemetry / replay / crash recovery 多数仍属设计，见 `docs/wiki/meta-harness-engineer/meta-harness-wiki/07-observability-audit.md:43`
- book：将其列为关键工程能力，见 `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:312`

### 5.3 Sandbox 的实现强度表达不一致

- wiki：仅部分落地，见 `docs/wiki/meta-harness-engineer/meta-harness-wiki/01-overview.md:67`
- book：三级隔离体系叙述完整，见 `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:193`

### 5.4 Optimizer 收敛判据表达不一致

- wiki：当前实现仍以较务实判据为主，见 `docs/wiki/meta-harness-engineer/meta-harness-wiki/05-self-growth.md:564`
- book：以 Hypervolume / Pareto 为主线，见 `docs/wiki/meta-harness-book/chapters/ch4_self_growth.tex:63`

### 5.5 热更新的产品化程度表达不一致

- wiki：STR 骨架已在，但重型工程能力多为目标，见 `docs/wiki/meta-harness-engineer/meta-harness-wiki/08-hot-reload.md:42`
- book：将更完整的 Saga / checkpoint / replay 体系纳入主叙述，见 `docs/wiki/meta-harness-book/chapters/ch5_engineering.tex:231`

---

## 6. 是否可以认为 wiki 与 book “对齐”

如果“对齐”的含义是：

- 核心概念一致；
- 组件划分一致；
- 架构目标一致；
- 子系统划分大体对应；

那么答案是：**可以认为整体对齐。**

但如果“对齐”的含义是：

- 每一章对成熟度的表述一致；
- 对当前实现状态的陈述一致；
- 对能力是否已落地的判断一致；

那么答案是：**不能认为完全对齐。**

所以最准确的表述应当是：

> **wiki 与 book 在架构思想上对齐，在实现成熟度叙事上存在系统性偏差。**

---

## 7. 建议的修订方向

### 7.1 给 book 增加“实现状态”标记

建议在 book 的关键章节旁增加标记，例如：

- **已在当前 MHE 中落地**
- **已有骨架实现**
- **属于目标架构 / 建议实现**

这样可以避免读者把研究性设计误读为当前产品能力。

### 7.2 给 wiki 增加“与 book 对应章节”链接

建议在每个 wiki 章节顶部加入：

- “本章对应书稿章节：`ch3_architecture.tex`”
- “本章对应书稿章节：`ch4_self_growth.tex`”

这样能降低两套文档并行演进带来的漂移风险。

### 7.3 统一术语层级：现状、目标、建议

建议建立三层标签体系：

- **现状（Current MHE）**
- **目标架构（Target Architecture）**
- **工程建议（Recommended Engineering Pattern）**

book 和 wiki 都按这三层写，能显著提升一致性。

### 7.4 把高风险章节改成“双栏叙述”

对以下章节建议采用“左栏：当前状态；右栏：目标设计”的写法：

- Observability
- Sandbox
- Self-growth / Optimizer
- Hot Reload

因为这些恰好是当前最容易被高估成熟度的部分。

---

## 8. 结论

MHE 的 wiki 与 meta-harness-book 并不是两套互相冲突的文档，而是两种不同写作视角下的同一设计体系：

- wiki 偏工程手册，强调“今天做到哪一步”；
- book 偏研究与总体设计，强调“系统应当长成什么样”。

两者的核心架构思想是一致的，因此从体系层面看，它们是对齐的；但在实现成熟度、产品化程度和能力是否已经落地的表述上，存在持续且系统性的偏差。

因此，最合适的结论不是“wiki 与 book 一致”，也不是“wiki 与 book 冲突”，而是：

> **两者在架构思想上高度同源，在实现状态叙事上部分失配；若要形成统一文档体系，需要显式区分“当前实现”与“目标设计”。**
