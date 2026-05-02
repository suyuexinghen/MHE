# 02 — 架构演进

## 2.1 演进链总览

```
plan-v1 (strawman)
  │
  ▼
dclaude-analysis (独立 review)
  │
  ▼
plan-v2 (架构修正)
  │
  ▼
plan-v3 (权威计划: MVP/Vision 分层, P0a–P4)
  │
  ▼
plan-v4 (CLI 用户入口切片，build on top of v3)
```

## 2.2 plan-v1：原始 strawman

来源：`docs/plan-drafts/plan-v1.md`

**关键设计**（后被修正）：

- **线性链**：`Question → Proposal → Plan → Evidence → Review → Decision`，单次线性收束
- **HypothesisOptimizer 扩展 Optimizer**：假设搜索作为组件图 ActionSpaceFunnel 的扩展
- **ResearchPaper 模型**：含 question/proposal/evidence/review/iteration_trace 的论文式输出
- **3 维 review**：credibility/novelty/reproducibility
- **6 阶段实施**：P0 模型+驱动器，P1 reviewer+optimizer，P2 benchmark+知识沉淀

**问题**：线性链不能表达真实研究中一个问题→多个假设→多个实验的分支关系。假设空间与组件图空间混在一起。review 维度不足。

## 2.3 dclaude-analysis：独立架构 review

来源：`docs/plan-drafts/dclaude-analysis.md`

对早期 plan-v1 的独立 review，提出了六项缺失：

1. ResearchStore（持久化与查询接口）
2. ResearchBudget 模型（max_experiments/wall_clock/llm_cost）
3. 人机协同门控（PIVOT/ABANDON 需人类批准）
4. 负结果处理（dead-end 检测与聚合）
5. 可复现性门控（measure-twice gate）
6. 实验版本与 lineage DAG

并建议风险排序优先级：Models → Store → Mappers → Benchmark → Orchestrator → Reviewer → HypothesisOptimizer。

## 2.4 plan-v2：架构修正

来源：`docs/plan-drafts/plan-v2.md`

**对 plan-v1 的关键修正**：

| plan-v1 | plan-v2 修正 |
|---------|------------|
| 线性链 | DAG：1 question → N hypotheses → N experiments，多对多 supports/refutes |
| 3 维 review | 5 维：credibility/novelty/correctness/reproducibility/significance |
| HypothesisOptimizer 扩展 Optimizer | HypothesisActionSpace 独立于 ActionSpaceFunnel |
| EvidenceBundle → ArtifactSnapshot | EvidenceBundle → ScoredEvidence（正确桥接） |
| 无 budget | ResearchBudget 模型 |
| 无人机协同 | PIVOT/ABANDON 需人类批准 |

**重新排序的实施优先级**（store/connection 提前，optimizer 最后）：
Models → Store → Connection/Mappers → Benchmark → Orchestrator → Reviewer → HypothesisActionSpace → 知识沉淀

## 2.5 plan-v3：权威计划

来源：`docs/plan-drafts/plan-v3.md`

**核心贡献**：**MVP 与 Science Discovery Vision 的分层**。这是整个 Research Loop 设计中最关键的决策。

- **MVP**（4-6 周可落地）：证明非侵入 wrapper 可行，只用 ground-truth benchmark + deterministic decision
- **Vision**（长期）：LLM reviewer、hypothesis generation、论文生成、文献 novelty 判断

v3 定义了 P0a–P4 的完整交付矩阵（见 [04-implementation-history.md](04-implementation-history.md)）和 Phase N 的显式延后声明。

## 2.6 plan-v4：CLI 用户入口切片

来源：`docs/plan-drafts/plan-v4.md`

**v4 不重写 v3，不扩大 Phase N**。它定义了一个 MVP-adjacent 的下一步：把已完成并验证的 Research Loop MVP 通过薄 `research-run` CLI 暴露给用户。

同时定义了 blueprint/plan/roadmap 的抽象层级与受众区分：
- **Blueprint**：whole-system schema、长期架构原则、多 phase 关系
- **Plan**：面向用户，解释目标/范围/非目标/验收
- **Roadmap**：面向 agent，补充目标文件/执行步骤/产物/验证命令/提交边界

## 2.7 设计演化中的关键决策

1. **DAG 而非链**（v1→v2）：real research is branching
2. **HypothesisActionSpace 独立**（v1→v2）：假设不是图编辑
3. **MVP/Vision 分层**（v2→v3）：最重要的工程决策 — 不声称未实现的能力
4. **CLI 作为独立切片**（v3→v4）：user-facing slice on top of internals — 不混合实现与暴露
