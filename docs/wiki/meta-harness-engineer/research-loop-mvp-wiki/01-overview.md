# 01 — MVP 概述

## 1.1 Research Loop MVP 是什么

Research Loop MVP 是构建在 MHE benchmark 体系之上的最小科学研究闭环。它将一个已有的 benchmark case 包装为完整的研究生命周期：

```
ResearchQuestion → Hypothesis → ExperimentPlan → EvidenceBundle → Decision
```

核心设计原则：**低侵入**。MVP 不修改 `HarnessRuntime`、`ConnectionEngine`、`ExecutionLifecycleService` 或 `BenchmarkCaseSpec` 主模型。它作为 MHE runtime 之上的非侵入 wrapper 运行。

## 1.2 MVP 与 Science Discovery Vision 的分层

这一区分来自 [plan-v3.md](../../plan-drafts/plan-v3.md)，是整个 Research Loop 设计的基础：

### MVP（已实现）

- 把已有 benchmark artifact 包装成 `ResearchQuestion → Evidence → Decision` 闭环
- 只使用 ground-truth benchmark 结果
- 只做 deterministic metric-threshold decision（ADVANCE / REFINE）
- 只实现轻量 JSONL store 与只读 mapper
- 不声称自动科学发现

### Science Discovery Vision（长期延后，Phase N）

- LLM-powered hypothesis generation
- Calibrated LLM reviewer agent
- Literature ingestion 与 novelty 判断
- Counterfactual reasoning
- 开放未解科学问题 benchmark
- Full natural-language paper generation

## 1.3 闭环示意

```text
Existing benchmark summary.json
  │
  ▼
EvidenceBundle
  ├─ metrics/status/failure_category
  ├─ artifact_refs
  ├─ validation_strategy = GROUND_TRUTH
  └─ confidence_method = deterministic_metric_threshold
  │
  ▼
Metric-threshold Reviewer
  │
  ▼
Decision(ADVANCE | REFINE)
  │
  ▼
ResearchStore(JSONL)
  │
  ▼
ResearchConclusion / ResearchDossier
```

## 1.4 关键对齐约束

### 不修改的组件

- `HarnessRuntime` 主流程
- `ConnectionEngine` 图提交与路由逻辑
- 现有 extension 的 gateway/probe/compiler/executor/validator 链
- `ExecutionLifecycleService` 的单次执行协议
- `BenchmarkCaseSpec` 主模型

### Hypothesis 与 CandidateRecord 分离

- `Hypothesis`：研究层实体，状态 `proposed/testing/supported/refuted/superseded`
- `CandidateRecord`：MHE 图版本候选实体，用于 graph promotion
- MVP 不做 `Hypothesis → CandidateRecord` 映射

### 先只读桥接，再运行时编排

- P0 只实现纯 mapper：`summary.json → EvidenceBundle`、`EvidenceBundle → ScoredEvidence`
- 不把 iteration metadata 塞进 `ExecutionLifecycleService`

### 先 ground-truth case，后开放课题

- MVP 首选：FEALPy `poisson-2d-numpy`，已有 ground truth
- 开放课题（高熵合金、量子纠错、湍流）延后到 Phase N
