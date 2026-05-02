# 03 — 模型与数据流

## 3.1 核心模型

定义位置：`src/metaharness/sdk/research.py`（~191 行，17 个类）

### ResearchQuestion

```python
question_id: str
statement: str
formal_spec: dict          # {"primary_metric": "l2_error", "relation": "lt", "target": 0.01}
status: Literal["open", "active", "answered", "stale"]
created_from: str | None   # "benchmark:<suite>:<case_id>"
validation_strategy: Literal["GROUND_TRUTH"]
```

P0 只支持 `GROUND_TRUTH`。以下保留到后续：`SELF_CONSISTENCY`、`BASELINE_COMPARISON`、`EXPERT_REVIEW`、`parent_question_id`。

### Hypothesis

```python
hypothesis_id: str
question_id: str
statement: str
prediction: dict           # {"l2_error": {"relation": "lt", "value": 0.01}}
status: Literal["proposed", "testing", "supported", "refuted"]
```

MVP 中 hypothesis 由 rule-based designer 从 question 确定性推导，不由 LLM 生成。

### ExperimentPlan

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

P0 的 ExperimentPlan 不驱动 runtime 执行，只用于绑定已有 benchmark result 与研究假设。

### EvidenceBundle

```python
bundle_id: str
experiment_plan_id: str
artifact_refs: list[str]
metrics: dict
status: Literal["passed", "failed", "skipped"]
failure_category: str | None    # runner_error, validation_error, timeout
confidence: float
confidence_method: str
validation_strategy: str
domain_tags: dict               # suite, case_id, lane, backend
supports: list[str]             # hypothesis_ids
refutes: list[str]              # hypothesis_ids
```

`domain_tags` 从 P0 开始保存，为未来负结果聚合预留。

### Decision

```python
decision_id: str
hypothesis_id: str
evidence_bundle_id: str
decision: Literal["ADVANCE", "REFINE"]
requires_approval: bool
reasoning: str
```

P0 不执行 PIVOT/RESCOPE/ABANDON。

### Review

```python
review_id: str
evidence_bundle_id: str
reviewer_type: str                     # "metric_threshold" | "llm" | "human"
recommendation: Literal["ADVANCE", "REFINE"]
reasoning: str
dimensions: dict
reviewer_version: str
calibration_status: str | None
```

P0-P2 只使用 `MetricThresholdReviewer`（deterministic）。

### ResearchConclusion

```python
question_id: str
question_status: str
supported_hypotheses: list[str]
refuted_hypotheses: list[str]
deferred_hypotheses: list[str]
negative_results: list[str]
status: str
```

### ResearchDossier

```python
dossier_id: str
question_id: str
claims: list[Claim]
negative_result_clusters: list[NegativeResultCluster]
conclusion: ResearchConclusion
schema_version: str
```

## 3.2 数据流

### summary.json → EvidenceBundle（只读 mapper）

输入：benchmark lane summary JSON

```json
{
  "suite": "fealpy-pde",
  "case_id": "poisson-2d-numpy",
  "lane": "extension",
  "status": "passed",
  "metrics": {"l2_error": 0.002487, "h1_error": 2.225, "dof": 289},
  "failure_category": null
}
```

映射规则：
- `status == "passed"` 且 primary metric 满足 prediction → `supports=[hypothesis_id]`
- `status == "passed"` 但 primary metric 不满足 → `refutes=[hypothesis_id]`
- `status == "failed"` → `confidence=0.0`，不直接 refute 科学假设

### EvidenceBundle → ScoredEvidence

- `EvidenceBundle.metrics → ScoredEvidence.metrics`
- `EvidenceBundle.confidence → ScoredEvidence.score`
- `EvidenceBundle.artifact_refs → ScoredEvidence.evidence_refs`
- `failure_category/domain_tags → ScoredEvidence.attributes`

### 端到端研究闭环

```text
ResearchQuestion
  └─ Hypothesis (rule-based designer 确定性推导)
      └─ ExperimentPlan (绑定 fixture summary)
          └─ EvidenceBundle (mapper: summary → evidence)
              └─ Review (MetricThresholdReviewer: primary metric vs prediction)
                  └─ Decision (ADVANCE | REFINE)
                      └─ ResearchConclusion
                      └─ ResearchDossier
```

## 3.3 Store 策略

定义位置：`src/metaharness/research/store.py`（~114 行）

- 格式：JSONL
- 每类对象一条记录
- artifact/provenance 只保存引用，不复制 artifact

核心接口：

```python
record_question(question)
record_hypothesis(hypothesis)
record_plan(plan)
record_evidence(evidence)
record_decision(decision)
list_hypotheses(question_id)      → list[Hypothesis]
evidence_for(hypothesis_id)       → list[EvidenceBundle]
decision_history(question_id)     → list[Decision]
```

P2 之后再考虑与 provenance Merkle tree / audit graph 深度集成。

## 3.4 MetricSchema sidecar registry

定义位置：`src/metaharness/sdk/research.py`

```python
class MetricSchema(BaseModel):
    name: str
    relation: Literal["lt", "gt", "approx"]
    target: float | None
    unit: str
    is_primary: bool
```

P0/P1 不修改 `BenchmarkCaseSpec` 主模型。先以 sidecar registry 形式存在，稳定后再考虑提升进 benchmark core model。
