# MHE Wiki 与实现差距清单报告

## 1. 报告目的

本文档用于系统梳理 `docs/wiki/meta-harness-engineer/meta-harness-wiki` 中声明的功能设计，与当前实现目录 `src/metaharness` 之间的一致性与差距，帮助后续进行文档校准、路线图排序与实现补齐。

本报告采用四类判定：

- **已实现**：文档中的核心功能在代码中已有明确、可运行的实现。
- **部分实现**：代码中已有框架或子能力，但与文档承诺的完整形态仍有明显距离。
- **未找到**：未发现与文档声明相匹配的实现证据。
- **待澄清**：存在相关代码，但是否达到文档描述的能力边界仍不明确。

---

## 2. 总体结论

总体上，MHE 当前状态可概括为：

- **基础骨架已较完整**：组件 SDK、图连接引擎、核心组件骨架、热更新基础设施、审计与 provenance 机制已经成型。
- **工程化能力不均衡**：安全治理、自进化优化、模板化生成、可观测性等模块已经具备接口或子模块，但离 wiki 所描述的“生产级闭环能力”还有差距。
- **若干章节明显超前于代码**：尤其是独立策略控制平面、强隔离沙箱、完整重放与故障恢复、成熟的多目标优化闭环等，当前更多体现为架构方向，而非已完全落地的功能。

换言之，**wiki 更像“目标架构 + 当前实现混合体”**，而不是一份完全与代码同步的实现说明书。

---

## 3. 分类差距清单

### 3.1 已实现能力

#### 3.1.1 组件 SDK 核心机制

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/02-component-sdk.md`
- **实现证据**：
  - `src/metaharness/sdk/base.py:13`
  - `src/metaharness/sdk/api.py:34`
  - `src/metaharness/sdk/runtime.py:14`
  - `src/metaharness/sdk/registry.py:29`

**结论**：组件抽象、声明式 API、运行时注入、注册与激活机制均可在代码中找到清晰实现，属于 wiki 与实现一致度较高的部分。

#### 3.1.2 连接引擎与图版本管理

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/04-connection-engine.md`
- **实现证据**：
  - `src/metaharness/core/connection_engine.py:36`
  - `src/metaharness/core/graph_versions.py:19`
  - `src/metaharness/core/validators.py:11`
  - `src/metaharness/config/xml_parser.py:1`
  - `src/metaharness/config/xsd_validator.py:1`

**结论**：`stage -> validate -> commit/rollback` 的候选图工作流与文档基本一致，是当前实现最成熟的主干能力之一。

#### 3.1.3 核心组件骨架

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/03-core-components.md`
- **实现证据**：
  - `src/metaharness/components/gateway.py:1`
  - `src/metaharness/components/runtime.py:1`
  - `src/metaharness/components/memory.py:1`
  - `src/metaharness/components/toolhub.py:1`
  - `src/metaharness/components/planner.py:1`
  - `src/metaharness/components/executor.py:1`
  - `src/metaharness/components/evaluation.py:1`
  - `src/metaharness/components/observability.py:1`
  - `src/metaharness/components/policy.py:1`
  - `src/metaharness/components/optimizer.py:57`

**结论**：九大基础组件与优化器组件在代码中均有对应实现，但需要注意：这里的“已实现”更多指组件壳体和运行时接入能力存在，不等于每个组件都达到了 wiki 中叙述的全部产品成熟度。

#### 3.1.4 热更新基础设施

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/08-hot-reload.md`
- **实现证据**：
  - `src/metaharness/hotreload/checkpoint.py:24`
  - `src/metaharness/hotreload/migration.py:1`
  - `src/metaharness/hotreload/swap.py:30`
  - `src/metaharness/hotreload/observation.py:39`
  - `src/metaharness/hotreload/saga.py:40`

**结论**：热更新涉及的检查点、迁移适配器、交换与观测窗口均已有代码支持，说明该部分具备较强实现基础。

#### 3.1.5 审计与 Provenance 能力

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/07-observability-audit.md`
- **实现证据**：
  - `src/metaharness/provenance/audit_log.py:40`
  - `src/metaharness/provenance/merkle.py:27`
  - `src/metaharness/provenance/evidence.py:1`
  - `src/metaharness/provenance/query.py:12`
  - `src/metaharness/provenance/counter_factual.py:1`

**结论**：审计日志、Merkle 锚定、证据组织与查询接口都具备较明确的代码基础，这一部分与 wiki 的一致性也较高。

### 3.2 部分实现能力

#### 3.2.1 自进化 / 自增长优化闭环

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/05-self-growth.md`
- **实现证据**：
  - `src/metaharness/optimizer/triggers.py:1`
  - `src/metaharness/optimizer/fitness.py:1`
  - `src/metaharness/optimizer/convergence.py:1`
  - `src/metaharness/optimizer/search/phase_a.py:1`
  - `src/metaharness/optimizer/search/phase_b.py:1`
  - `src/metaharness/optimizer/search/phase_c.py:1`
  - `src/metaharness/optimizer/search/bayesian.py:1`
  - `src/metaharness/optimizer/search/rl.py:1`

**差距说明**：wiki 倾向于描述一个较成熟的多阶段、自驱动、多目标优化体系；而从当前代码看，更接近“可扩展优化框架 + 若干搜索策略模块”的状态。也就是说，闭环的接口与模块划分在，但是否已经形成 wiki 所暗示的稳定生产闭环，证据不足。

#### 3.2.2 安全治理链

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/06-safety-governance.md`
- **实现证据**：
  - `src/metaharness/safety/pipeline.py:1`
  - `src/metaharness/safety/sandbox_validator.py:1`
  - `src/metaharness/safety/ab_shadow.py:1`
  - `src/metaharness/safety/policy_veto.py:1`
  - `src/metaharness/safety/auto_rollback.py:1`
  - `src/metaharness/safety/hooks.py:1`

**差距说明**：代码中已经形成四层防线式的安全链条，但 wiki 对“宪法式治理”“独立权威策略层”“强一致约束库”的表述明显更强，当前实现尚不足以完全支撑这些更高阶承诺。

#### 3.2.3 模板库与代码生成

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/09-template-library.md`
- **实现证据**：
  - `src/metaharness/optimizer/templates/registry.py:1`
  - `src/metaharness/optimizer/templates/slots.py:1`
  - `src/metaharness/optimizer/templates/codegen.py:1`
  - `src/metaharness/optimizer/templates/migration.py:1`

**差距说明**：模板注册、插槽和迁移相关基础设施存在，但 wiki 对模板生态、模板目录规模、代码生成流水线成熟度的描述更像目标状态，而不是现有实现的精确写照。

#### 3.2.4 可观测性运行时

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/07-observability-audit.md`
- **实现证据**：
  - `src/metaharness/observability/metrics.py:1`
  - `src/metaharness/observability/trace.py:1`
  - `src/metaharness/observability/trajectory.py:1`

**差距说明**：指标、追踪、轨迹模块都存在，但从当前实现证据看，尚不足以证明已经达到 wiki 所表述的统一事件流、全链路重放与生产级回溯分析能力。

### 3.3 未找到的能力

#### 3.3.1 独立的 Policy 控制平面

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/06-safety-governance.md`
- **实现检查范围**：`src/metaharness/`

**结论**：未找到足以支撑“独立控制面 / 独立进程或独立权威策略系统 / 签名化策略仓库 / HSM 级审批链”等能力的明确实现证据。当前更像是运行时内部的策略组件与 veto 逻辑，而非真正独立的治理控制平面。

#### 3.3.2 真实的高强度沙箱后端

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/06-safety-governance.md`
- **实现证据**：`src/metaharness/safety/sandbox_tiers.py:1`

**结论**：代码中存在沙箱层级抽象，但没有足够证据表明 gVisor、Firecracker、WASM/V8 等强隔离执行后端已经真实接通并作为成熟后端投入运行。当前更像“接口先行”。

### 3.4 待澄清能力

#### 3.4.1 端到端重放引擎

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/07-observability-audit.md`
- **相关实现证据**：
  - `src/metaharness/provenance/counter_factual.py:1`
  - `docs/TECHNICAL_MANUAL.md:530`

**判断**：存在相关基础模块，但难以确认是否已经形成完整的“端到端运行时重放系统”。当前更稳妥的结论应为“具备部分支撑能力，但未证实 fully replayable runtime”。

#### 3.4.2 热更新期间的集中式 drain / buffer 协议

- **wiki 依据**：`docs/wiki/meta-harness-engineer/meta-harness-wiki/08-hot-reload.md`
- **相关文档证据**：`docs/TECHNICAL_MANUAL.md:375`

**判断**：热更新机制已经存在，但技术手册同时暗示仍缺少统一的 orchestrator 级 drain 协议，因此 wiki 在这里可能略微超前。

---

## 4. 主要偏差模式

### 4.1 文档超前于代码

这是最主要的偏差模式。wiki 中不少章节采用“完成态”叙述，但代码更像“骨架 + 部分实现 + 预留扩展点”。这种写法适合表达架构目标，但不适合作为严格的实现状态说明。

### 4.2 组件存在不等于能力完整

当前很多功能都能在代码树中找到对应模块，但“模块存在”不代表“端到端能力已完成”。例如优化器、安全链、模板库与可观测性都属于这种情况。

### 4.3 运行时工程化能力是主要短板

相比组件声明、图管理、局部热更新等能力，真正偏“基础设施级”的能力——如崩溃恢复、独立控制面、强隔离执行、全链路事件持久化——仍是差距最明显的部分。

---

## 5. 最高风险的五项文档失配

### 5.1 沙箱强度表述偏强

wiki 容易让读者理解为系统已经具备成熟的多级强隔离执行后端，但代码更接近抽象层级存在、真实隔离后端未充分落地的状态。

### 5.2 策略治理独立性表述偏强

wiki 对 Policy 的表述接近“独立权威控制面”，而当前实现证据更像运行时内部治理链条，二者在架构级别上有明显差距。

### 5.3 Replay / 故障恢复能力表述偏强

当前已有 provenance、轨迹和审计模块，但尚不足以证明系统已经具备 CMA 式的完整重放与自动恢复能力。

### 5.4 优化器成熟度表述偏强

wiki 强调自增长、多阶段搜索、多目标性能驱动，但代码侧更像可演化框架与若干算法部件，离成熟的自动优化生产闭环还有距离。

### 5.5 热更新安全边界表述偏强

虽然热更新模块较完整，但统一 drain 协议与更强的状态一致性保障证据不足，说明 wiki 对热更新稳定性的暗示略超前。

---

## 6. 建议的文档修订策略

### 6.1 将 wiki 内容拆分为“已实现”与“目标架构”

建议在每章开头增加状态标签，例如：

- **状态：已实现**
- **状态：部分实现**
- **状态：设计目标**

这样可以显著降低读者把目标架构误读为现状实现的风险。

### 6.2 为关键能力增加“实现证据”小节

每个核心章节建议补一节“代码落点”，直接列出对应源码文件，如：

- `src/metaharness/core/connection_engine.py`
- `src/metaharness/hotreload/swap.py`
- `src/metaharness/safety/pipeline.py`

这样可以把 wiki 从概念说明提升为“可审计设计文档”。

### 6.3 明确区分“抽象存在”与“生产可用”

例如：

- “支持沙箱分层抽象” ≠ “已具备生产可用的强隔离后端”
- “提供 replay 相关模块” ≠ “支持完整端到端重放恢复”

### 6.4 以路线图方式承接超前章节

对于独立策略控制面、强隔离沙箱、自动恢复与完整事件持久化，建议从 wiki 主叙述中移出“现状描述”，转为“下一阶段路线图”或“规划能力”。

---

## 7. 结论

MHE 当前实现并非空泛原型，而是已经具备较强工程基础，尤其在组件 SDK、图连接引擎、热更新基础设施与审计溯源方面已有较扎实落点。但从“wiki 对外宣称的体系能力”角度看，当前实现仍未完全覆盖全部设计承诺。

因此，更准确的表述应当是：

> **MHE 已完成核心架构骨架与若干关键子系统实现，但 wiki 中关于治理、安全、优化与恢复的若干章节仍带有明显的目标架构色彩。**

后续若要提升文档可信度，最优先的工作不是继续增加概念章节，而是同步补齐“实现状态标注 + 代码证据链接 + 路线图声明”三件事。
