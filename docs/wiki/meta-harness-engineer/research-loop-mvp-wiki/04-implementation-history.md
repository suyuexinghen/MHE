# 04 — 实现历史

## 4.1 按阶段交付记录

全部实现于 2026-05-01 至 2026-05-02，共 9 个提交，10 个源文件，982 行研究闭环代码，10 个测试文件。

| Phase | Commit | 日期 | 描述 | 关键文件 |
|-------|--------|------|------|---------|
| P0a | `0469052` | 05-01 23:42 | Research Lifecycle Models | `sdk/research.py` (191 行, 17 个类) |
| P0b | `3d065c6` | 05-01 23:45 | MVP evidence mappers + lightweight store | `research/mappers.py` (166 行), `research/store.py` (114 行) |
| P0c | `d93c17f` | 05-01 23:47 | FEALPy walking skeleton | 最小 smoke test 验证 summary → evidence → decision |
| P1 | `3c1ac2b` | 05-01 23:50 | Minimal orchestrator loop | `core/research.py` (129 行) |
| P1b | `4f4ab3a` | 05-01 23:51 | Rule-based ExperimentDesigner | `sdk/experiment_design.py` (13 行, protocol), `research/domains/fealpy.py` |
| P2 | `b9522b0` | 05-01 23:55 | Deterministic reviewer calibration | `sdk/review.py`, `sdk/review_calibration.py`, `research/reviewers.py` |
| P3 | `2f04a89` | 05-01 23:59 | Hypothesis action space | `research/hypotheses.py` (130 行, GENERATE/REFINE/SELECT/COMBINE + testability filter) |
| P4 | `a95126b` | 05-02 00:02 | Research dossier + negative results | `research/dossier.py` (142 行) |
| v4 CLI | `90b3c88` | 05-02 11:04 | research-run CLI smoke path | `cli.py` (+72 行), 示例输入, 2 fixtures, 3 focused tests |

## 4.2 P0a: Research Lifecycle Models

交付物：`sdk/research.py`

17 个模型类/枚举：
- `ResearchQuestion`、`Hypothesis`、`ExperimentPlan`、`EvidenceBundle`
- `Decision`、`Review`、`ReviewDimensions`
- `ResearchConclusion`、`ResearchDossier`、`Claim`、`ClaimSource`、`NegativeResultCluster`
- `ResearchManifest`、`ArtifactManifest`
- 枚举：`QuestionStatus`、`HypothesisStatus`、`EvidenceStatus`、`ValidationStrategy`、`ReviewerType`

验收：`test_research_lifecycle_models.py` — roundtrip JSON 序列化/反序列化

## 4.3 P0b: Mappers + Lightweight Store

交付物：`research/mappers.py`、`research/store.py`

- `EvidenceMapper.map_summary_to_evidence()`：benchmark summary JSON → `EvidenceBundle`
- `EvidenceMapper.map_evidence_to_scored()`：`EvidenceBundle` → `ScoredEvidence`
- `ResearchStore`：JSONL 存储，`record_*` / `list_*` / `evidence_for` / `decision_history` 接口

验收：`test_research_mappers.py`、`test_research_store.py`

## 4.4 P0c: FEALPy Walking Skeleton

交付物：`tests/test_research_walking_skeleton_fealpy.py`

首个端到端 smoke：取 FEALPy `poisson-2d-numpy` summary fixture，映射为 EvidenceBundle，验证：
- `l2_error < 0.01` hypothesis 被标记为 supported
- Failed execution 不直接 refute hypothesis，只记录 execution failure
- Trace 中 question/hypothesis/plan/evidence/decision 全部可回放

## 4.5 P1: Minimal Orchestrator

交付物：`core/research.py`

`ResearchOrchestrator.pursue(question)`：
- 固定 hypothesis list
- 固定 experiment plan 或 fixture-driven plan
- Deterministic metric-threshold reviewer
- Budget 只强制 `max_experiments`
- 约束：`max_wall_clock` / `max_llm_cost` 作为 schema 字段保留，不强执行

验收：`test_research_orchestrator.py`

## 4.6 P1b: Rule-based ExperimentDesigner

交付物：`sdk/experiment_design.py`、`research/domains/fealpy.py`

- `ExperimentDesignerProtocol`：`design(question, hypothesis) → ExperimentPlan` 协议
- `FEALPyRuleBasedExperimentDesigner`：从 question 的 `formal_spec` 与 hypothesis 的 `prediction` 确定性推导 plan

约束：只支持 FEALPy ground-truth case；不做 LLM design；不做 bandit selection

验收：`test_research_experiment_design.py`

## 4.7 P2: Reviewer + Calibration

交付物：`sdk/review.py`、`sdk/review_calibration.py`、`research/reviewers.py`

- `ReviewerProtocol`：`review(experiment, evidence, baseline, prior_reviews) → Review`
- `MetricThresholdReviewer`：deterministic primary-metric-vs-prediction comparison
- `ReviewCalibration`：calibration fixture set，防止未经校准的 reviewer 进入自动决策路径

验收：`test_research_review.py`

## 4.8 P3: HypothesisActionSpace

交付物：`research/hypotheses.py`

- `GENERATE`：从 question + 现有 evidence 生成新 hypothesis（rule-based，非 LLM）
- `REFINE`：从被反驳 hypothesis + evidence 产生精化版
- `SELECT`：简单 sort-based selection（非 bandit）
- `COMBINE`：综合两个被支持的 hypothesis
- Testability filter：不可测试 hypothesis 不得进入 active set

约束：不复用 `ActionSpaceFunnel`；不映射 `Hypothesis → CandidateRecord`

验收：`test_research_hypotheses.py`

## 4.9 P4: ResearchDossier + Negative Results

交付物：`research/dossier.py`

- `ResearchDossier`：aggregated claims + negative result clusters + conclusion
- `NegativeResultCluster`：按 `failure_category` / `domain_tags` / `metric_schema` 聚合负结果
- `Claim`：可追溯到 `EvidenceBundle` 或 `SOTABaseline`

验收：`test_research_dossier.py`

## 4.10 v4 CLI: research-run Smoke Path

交付物：`cli.py` (+72 行)，示例输入，2 fixtures，3 focused tests

详见 [05-cli-and-user-entry.md](05-cli-and-user-entry.md)。

## 4.11 源码文件清单

| 文件 | 行数 | 角色 |
|------|------|------|
| `src/metaharness/sdk/research.py` | 191 | 17 个核心模型 |
| `src/metaharness/core/research.py` | 129 | ResearchOrchestrator 主循环 |
| `src/metaharness/research/store.py` | 114 | JSONL store |
| `src/metaharness/research/mappers.py` | 166 | summary → evidence 映射 |
| `src/metaharness/research/decision.py` | — | Decision engine |
| `src/metaharness/research/reviewers.py` | — | MetricThresholdReviewer |
| `src/metaharness/research/hypotheses.py` | 130 | HypothesisActionSpace |
| `src/metaharness/research/dossier.py` | 142 | ResearchDossier + NegativeResultCluster |
| `src/metaharness/research/domains/fealpy.py` | — | FEALPy rule-based designer |
| `src/metaharness/sdk/experiment_design.py` | 13 | ExperimentDesignerProtocol |
| `src/metaharness/sdk/review.py` | — | ReviewerProtocol + ReviewDimensions |
| `src/metaharness/sdk/review_calibration.py` | — | Calibration fixtures |
