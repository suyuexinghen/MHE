# 架构升级计划 v3：从算例执行框架到科学研究闭环框架

## 0. 文档定位：MVP 与长期愿景分层

本计划分为两层：

1. **Research Loop MVP（4–6 周可落地）**
   - 目标：证明 MHE 可以在不侵入 `HarnessRuntime` / `ConnectionEngine` 的前提下，把一个已有 benchmark case 包装成最小科学研究闭环：
     `ResearchQuestion → Hypothesis → ExperimentPlan → EvidenceBundle → Decision`。
   - 范围：只使用已有 ground-truth benchmark 结果；只做 deterministic metric-threshold decision；只实现轻量 store 与只读 mapper。

2. **Science Discovery Vision（长期科研智能体愿景）**
   - 目标：逐步走向 AI 自动提出假设、设计实验、审查结果、迭代研究，并最终产出可信研究报告/论文。
   - 范围：LLM reviewer、reviewer calibration、HypothesisActionSpace、负结果知识沉淀、论文生成、文献级 novelty 判断、知识边界表达。

这一区分非常重要：**MVP 不声称实现自动科学发现；MVP 只验证研究闭环架构能否低风险地接入现有 MHE benchmark 体系。**

---

## 1. 问题陈述

当前 MHE 的核心架构仍然主要面向算例计算流程（computation-instance-oriented）：

- 执行链路是 `Gateway → EnvironmentProbe → InputCompiler → Executor → Validator`，单次线性收束。
- `ExecutionLifecycleService` 只追踪 submit/poll/complete/fail，没有“假设-实验-反馈”的迭代语义。
- `HarnessRuntime.boot()` 组装静态组件图，不表达研究问题、假设、证据和决策。
- `Optimizer` 的 mutation proposal 作用于组件图版本，不作用于科学假设空间。
- 各 extension（FEALPy、Nektar、pyCFD、QCompute/ABACUS 等）各自封装计算器运行，缺少统一的研究问题定义与证据语义。

目标方向来自 `trend.md` 的关键主张：**从模式匹配跨越到提出新假设**。但工程路线必须先从可验证闭环开始，而不是直接跳到开放科学发现。

---

## 2. 设计原则

### 2.1 低侵入优先

MVP 不修改：

- `HarnessRuntime` 主流程
- `ConnectionEngine` 图提交与路由逻辑
- 现有 extension 的 gateway/probe/compiler/executor/validator 链
- `ExecutionLifecycleService` 的单次执行协议
- `BenchmarkCaseSpec` 主模型

MVP 新增的是研究层 wrapper、sidecar registry、mapper 和 store。

### 2.2 Hypothesis 与 CandidateRecord 严格分离

科学假设是关于世界的声明，不是组件图 mutation：

- `Hypothesis`：研究层实体，状态为 `proposed/testing/supported/refuted/superseded`。
- `CandidateRecord`：MHE 图版本候选实体，用于 graph promotion。

MVP 不做 `HypothesisCandidate → CandidateRecord` 映射。只有当未来某个假设需要改变组件图/工作流模板时，才在具体实验实施阶段产生 graph candidate。

### 2.3 先只读桥接，再运行时编排

P0 只实现纯 mapper：

- benchmark `summary.json → EvidenceBundle`
- `EvidenceBundle → ScoredEvidence`
- `ExperimentPlan metadata → RunPlanProtocol` 兼容字段

不把 iteration metadata 塞进 `ExecutionLifecycleService`，不改 runtime 生命周期。

### 2.4 先 ground-truth case，后开放课题

MVP 不从“已公开但未解决课题”开始。先选已有 ground-truth benchmark：

- 首选：FEALPy `poisson-2d-numpy`
- 备选：Octave 或 Nektar 已有 reference case

理由：开放课题没有 ground truth，会把 validation、review、novelty、human approval 等问题全部提前引入，导致 MVP 失焦。

---

## 3. MVP 的非目标（Non-Claims）

MVP 不声称：

- 自动提出原创科学假设
- 自动解决开放未解科学问题
- 自动判断文献级创新性
- 自动生成可信论文
- 自动执行 PIVOT/RESCOPE/ABANDON 战略决策
- 自动通过 reviewer agent 判断科学价值

MVP 只验证：

- 能把已有 benchmark case 包装为 `ResearchQuestion`
- 能把已有 benchmark summary 转成 `EvidenceBundle`
- 能根据 deterministic metric-threshold 产生 `Decision`
- 能把 research trace 持久化为可查询、可回放的 artifact
- 能保持对现有 MHE runtime 的低侵入接入方式

---

## 4. Research Loop MVP 数据流

```text
Existing benchmark summary.json
  │
  ▼
EvidenceBundle
  │
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
ResearchStore(JSONL/SQLite)
  │
  ▼
ResearchConclusion / ResearchDossier(minimal)
```

最小闭环：

```text
ResearchQuestion
  └─ Hypothesis
      └─ ExperimentPlan
          └─ EvidenceBundle
              └─ Decision
```

P0 不要求完整多分支 DAG；只保留字段和关系以便未来扩展到 DAG。

---

## 5. MVP 模型范围

### 5.1 `ResearchQuestion`

必要字段：

```python
question_id: str
statement: str
formal_spec: dict
status: Literal["open", "active", "answered", "stale"]
created_from: str | None  # benchmark:<suite>:<case_id>
validation_strategy: Literal["GROUND_TRUTH"]
```

P0 只支持 `GROUND_TRUTH`。以下字段保留到 P1/P2：`SELF_CONSISTENCY`、`BASELINE_COMPARISON`、`EXPERT_REVIEW`、`parent_question_id`、knowledge boundary。

### 5.2 `Hypothesis`

必要字段：

```python
hypothesis_id: str
question_id: str
statement: str
prediction: dict  # e.g. {"l2_error": {"relation": "lt", "value": 0.01}}
status: Literal["proposed", "testing", "supported", "refuted"]
```

P0 不实现 hypothesis generation、REFINE、COMBINE、bandit selection。假设由 fixture 或 JSON 输入提供。

### 5.3 `ExperimentPlan`

必要字段：

```python
plan_id: str
hypothesis_id: str
run_plan_ref: str | None
suite: str
case_id: str
lane: str | None
controls: dict
variables: dict
expected_outcome: dict
```

P0 的 `ExperimentPlan` 不驱动 runtime 执行，只用于绑定已有 benchmark result 与研究假设。

### 5.4 `EvidenceBundle`

必要字段：

```python
bundle_id: str
experiment_plan_id: str
artifact_refs: list[str]
metrics: dict
status: Literal["passed", "failed", "skipped"]
failure_category: str | None
confidence: float
confidence_method: str
validation_strategy: str
domain_tags: dict  # mesh, solver, backend, lane, suite, case_id
supports: list[str]
refutes: list[str]
```

`domain_tags` 必须从 P0 开始保存，否则未来无法做负结果聚合。

### 5.5 `Decision`

必要字段：

```python
decision_id: str
hypothesis_id: str
evidence_bundle_id: str
decision: Literal["ADVANCE", "REFINE"]
requires_approval: bool = False
reasoning: str
```

P0 不执行 PIVOT/RESCOPE/ABANDON。P1 可以记录这些决策，但只设置 `requires_approval=True`，不自动执行 gate。

---

## 6. 只读桥接设计

### 6.1 `summary.json → EvidenceBundle`

输入：现有 benchmark lane summary，例如：

```json
{
  "suite": "fealpy-pde",
  "case_id": "poisson-2d-numpy",
  "lane": "extension",
  "status": "passed",
  "metrics": {
    "l2_error": 0.0024865245884339074,
    "h1_error": 2.2250025132790325,
    "dof": 289
  },
  "failure_category": null
}
```

输出：`EvidenceBundle`。

P0 mapper 规则：

- `status == "passed"` 且 primary metric 满足 hypothesis prediction → `supports=[hypothesis_id]`
- `status == "passed"` 但 primary metric 不满足 → `refutes=[hypothesis_id]`
- `status == "failed"` → `confidence=0.0`，不直接 refute 科学假设，先记录为 execution failure

### 6.2 `EvidenceBundle → ScoredEvidence`

映射：

- `EvidenceBundle.metrics → ScoredEvidence.metrics`
- `EvidenceBundle.confidence → ScoredEvidence.score`
- `EvidenceBundle.artifact_refs → ScoredEvidence.evidence_refs`
- `failure_category/domain_tags → ScoredEvidence.attributes`

### 6.3 `ExperimentPlan → RunPlanProtocol`

P0 只做 metadata 兼容，不调用 executor：

- `ExperimentPlan.plan_id → RunPlanProtocol.plan_id`
- `ExperimentPlan.hypothesis_id → RunPlanProtocol.experiment_ref`
- `ExperimentPlan.suite/case_id/lane → execution_params`

---

## 7. Store 策略：轻量优先

P0 不扩展完整 Merkle/audit graph。

推荐：

- JSONL 或 SQLite
- 每类对象一条记录
- artifact/provenance 只保存引用，不复制 artifact

最小接口：

```python
record_question(question: ResearchQuestion) -> None
record_hypothesis(hypothesis: Hypothesis) -> None
record_plan(plan: ExperimentPlan) -> None
record_evidence(evidence: EvidenceBundle) -> None
record_decision(decision: Decision) -> None
list_hypotheses(question_id: str) -> list[Hypothesis]
evidence_for(hypothesis_id: str) -> list[EvidenceBundle]
decision_history(question_id: str) -> list[Decision]
```

P2 之后再考虑与 provenance Merkle tree / audit graph 深度集成。

---

## 8. MetricSchema：sidecar registry，不改主模型

P0/P1 不修改 `BenchmarkCaseSpec` 主模型。先新增 sidecar registry：

```python
class MetricSchema(BaseModel):
    name: str
    relation: Literal["lt", "gt", "approx"]
    target: float | None
    unit: str = ""
    is_primary: bool = False
```

Registry 可从现有 `expected_metrics` 派生：

```json
{
  "fealpy-pde:poisson-2d-numpy": [
    {"name": "l2_error", "relation": "lt", "target": 0.01, "is_primary": true},
    {"name": "h1_error", "relation": "lt", "target": null, "is_primary": false},
    {"name": "dof", "relation": "gt", "target": 0, "is_primary": false}
  ]
}
```

稳定后再考虑把 MetricSchema 提升进 benchmark core model。

---

## 9. 最小 JSON 示例

### 9.1 `research_question.json`

```json
{
  "question_id": "rq-fealpy-poisson-l2-threshold",
  "statement": "Can the FEALPy Poisson 2D numpy benchmark solve with L2 error below 0.01?",
  "formal_spec": {"primary_metric": "l2_error", "relation": "lt", "target": 0.01},
  "status": "active",
  "created_from": "benchmark:fealpy-pde:poisson-2d-numpy",
  "validation_strategy": "GROUND_TRUTH"
}
```

### 9.2 `hypothesis.json`

```json
{
  "hypothesis_id": "h-fealpy-poisson-p1-16x16",
  "question_id": "rq-fealpy-poisson-l2-threshold",
  "statement": "P1 Lagrange elements on the 16x16 Poisson case produce L2 error below 0.01.",
  "prediction": {"l2_error": {"relation": "lt", "value": 0.01}},
  "status": "proposed"
}
```

### 9.3 `evidence_bundle.json`

```json
{
  "bundle_id": "ev-fealpy-poisson-extension-final3",
  "experiment_plan_id": "plan-fealpy-poisson-extension",
  "artifact_refs": [".runs/fealpy-final3-20260501/fealpy-pde-benchmark/extension/poisson-2d-numpy/summary.json"],
  "metrics": {"l2_error": 0.0024865245884339074, "h1_error": 2.2250025132790325, "dof": 289},
  "status": "passed",
  "failure_category": null,
  "confidence": 1.0,
  "confidence_method": "deterministic_metric_threshold",
  "validation_strategy": "GROUND_TRUTH",
  "domain_tags": {"suite": "fealpy-pde", "case_id": "poisson-2d-numpy", "lane": "extension", "backend": "numpy"},
  "supports": ["h-fealpy-poisson-p1-16x16"],
  "refutes": []
}
```

---

## 10. CLI 草案

P1 才需要 CLI；P0 可只做 tests。目标接口：

```bash
PYTHONPATH=src python -m metaharness.cli research-run \
  --question examples/research/poisson_question.json \
  --suite fealpy-pde \
  --case poisson-2d-numpy \
  --lane extension \
  --runs-root .runs/research-loop-smoke
```

预期 artifact：

```text
.runs/research-loop-smoke/
  research_trace.jsonl
  research_question.json
  hypothesis.json
  evidence_bundle.json
  decision.json
  conclusion.json
```

---

## 11. Acceptance Matrix

| Phase | Command / Test | Artifact | Done when |
|---|---|---|---|
| P0a 模型 MVP | `python -m pytest tests/test_research_lifecycle_models.py -q` | model roundtrip JSON | minimal models validate, serialize, deserialize |
| P0b mapper + store | `python -m pytest tests/test_research_mappers.py tests/test_research_store.py -q` | EvidenceBundle JSONL | summary maps to evidence; store roundtrip passes |
| P0c benchmark wrapper smoke | `python -m pytest tests/test_research_walking_skeleton_fealpy.py -q` | research trace JSONL | FEALPy summary supports/refutes one hypothesis |
| P1 minimal orchestrator | `PYTHONPATH=src python -m metaharness.cli research-run ...` | conclusion.json | loop completes with ADVANCE/REFINE decision |
| P1b rule-based designer | focused pytest | experiment design JSON | fixed hypothesis produces deterministic plan |
| P2 reviewer calibration | focused pytest + fixture set | calibration_result.json | bad reviewer cannot enter auto-decision path |
| P3 hypothesis action space | focused pytest | hypothesis candidates JSON | generated hypotheses pass testability filter |

---

## 12. Recommended Roadmap

### P0a：Research 模型 MVP

交付物：

- `src/metaharness/sdk/research.py`
- `ResearchQuestion`
- `Hypothesis`
- `ExperimentPlan`
- `EvidenceBundle`
- `Decision`
- minimal enums: status, validation strategy, decision

约束：

- 不实现 full DAG traversal
- 不实现 reviewer protocol
- 不实现 ExperimentDesignerProtocol
- 不接 LLM

验收：模型 roundtrip + schema validation。

### P0b：Mapper + lightweight Store

交付物：

- `src/metaharness/research/store.py`
- `src/metaharness/research/mappers.py`
- JSONL/SQLite store
- `summary.json → EvidenceBundle`
- `EvidenceBundle → ScoredEvidence`

约束：

- 只读 bridge
- 不改 runtime lifecycle
- 不扩展 Merkle/audit graph

验收：mapper/store tests pass。

### P0c：Benchmark wrapper smoke

交付物：

- `tests/test_research_walking_skeleton_fealpy.py`
- 使用 FEALPy `poisson-2d-numpy` existing summary 或 test fixture summary
- 生成最小 research trace

验收：

- `l2_error < 0.01` hypothesis 被标记为 supported
- failed execution 不会直接 refute hypothesis，只记录 execution failure
- trace 中 question/hypothesis/plan/evidence/decision 全部可回放

### P1：ResearchOrchestrator minimal loop

交付物：

- `src/metaharness/core/research.py`
- 固定 hypothesis list
- 固定 experiment plan 或 fixture-driven plan
- deterministic metric-threshold reviewer
- budget 只强制 `max_experiments`

约束：

- `max_wall_clock` / `max_llm_cost` 作为 schema 字段保留，不强执行
- PIVOT/RESCOPE/ABANDON 只记录 `requires_approval=True`，不接自动 approval gate
- 不接 LLM reviewer

验收：CLI 或 focused test 能完成 single-case research loop。

### P1b：Rule-based ExperimentDesignerProtocol

交付物：

- `src/metaharness/sdk/experiment_design.py`
- `ExperimentDesignerProtocol`
- `FEALPyRuleBasedExperimentDesigner`

约束：

- 只支持 FEALPy ground-truth case
- 不做 LLM design
- 不做 bandit selection

验收：给定 hypothesis/formal_spec，产生 deterministic ExperimentPlan。

### P2：Reviewer + calibration

交付物：

- `src/metaharness/sdk/review.py`
- `src/metaharness/sdk/review_calibration.py`
- `ReviewDimensions`
- deterministic reviewer calibration fixtures
- later: LLMReviewer

约束：

- calibration 不阻塞 MVP
- 先校准 credibility/correctness/reproducibility，不急于校准 novelty
- LLM reviewer 校准失败时回退 rule-based reviewer 或 human review

验收：未经校准 reviewer 不进入自动决策路径。

### P3：HypothesisActionSpace

交付物：

- `HypothesisActionSpace`: GENERATE / REFINE / SELECT / COMBINE
- testability filter
- cost-benefit ranking
- optional BayesianOptimizer-based SELECT

约束：

- 不复用 graph `ActionSpaceFunnel` 作为假设空间
- 不把 Hypothesis 映射为 CandidateRecord
- 只在 experiment implementation 需要改变组件图时产生 graph candidate

验收：生成假设必须可测试；不可测试假设不得进入 active set。

### P4：ResearchDossier 与负结果知识沉淀

交付物：

- `ResearchDossier`
- `NegativeResultAggregator`
- evidence quality policy
- reproducibility tiers

验收：

- 负结果可按 `domain_tags/failure_category/metric_schema` 聚合
- 重复 dead-end 可被识别并阻止再次测试
- dossier 中每个 claim 都能追溯到 EvidenceBundle 或 SOTABaseline

### Phase N：开放科学发现愿景

独立为长期研究路线，不作为近期交付承诺：

- knowledge-boundary-aware hypothesis generation
- literature ingestion
- 文献级 novelty 判断
- counterfactual reasoning
- “爱因斯坦测试”式原创理论发现
- full natural-language paper generation and peer-review loop

---

## 13. 远期架构愿景保留点

当 MVP 稳定后，完整科学研究闭环可扩展为：

```text
ResearchQuestion
  ├─ Hypothesis 1
  │   ├─ ExperimentDesign A
  │   ├─ ExperimentPlan A1/A2/...
  │   ├─ EvidenceBundle...
  │   └─ Review/Decision
  ├─ Hypothesis 2
  └─ Rescoped ResearchQuestion
```

远期新增能力：

- `ValidationStrategy`: SELF_CONSISTENCY / BASELINE_COMPARISON / EXPERT_REVIEW
- `SOTABaselineRegistry`
- calibrated LLM reviewer
- HypothesisActionSpace
- ResearchDossier / PaperSynthesizer
- multi-question portfolio management
- human-in-the-loop governance for PIVOT/RESCOPE/ABANDON

这些能力应建立在 P0/P1 的 artifact、store、mapper 和 acceptance tests 稳定之后。

---

## 14. 最重要的下一步

不要先实现 LLM hypothesis generation、LLM reviewer 或论文生成。

先实现 P0：

1. `sdk/research.py` minimal models
2. lightweight `ResearchStore`
3. `summary.json → EvidenceBundle` mapper
4. `EvidenceBundle → ScoredEvidence` mapper
5. FEALPy `poisson-2d-numpy` walking skeleton test

这能最快验证核心架构假设：**研究层可以作为 MHE runtime 之上的非侵入 wrapper，并且现有 benchmark artifact 足以支撑第一版 ResearchQuestion → Evidence → Decision 闭环。**
