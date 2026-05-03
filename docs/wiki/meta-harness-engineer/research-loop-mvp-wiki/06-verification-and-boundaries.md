# 06 — 验证与边界

## 6.1 测试覆盖

### 研究闭环测试套件（39 passed）

```bash
python -m pytest tests/test_research_*.py -q
```

覆盖文件：
- `test_research_lifecycle_models.py` — 模型 roundtrip JSON
- `test_research_mappers.py` — summary → EvidenceBundle 映射
- `test_research_store.py` — JSONL store roundtrip
- `test_research_walking_skeleton_fealpy.py` — FEALPy smoke
- `test_research_orchestrator.py` — 最小 orchestrator 循环
- `test_research_experiment_design.py` — FEALPy rule-based designer
- `test_research_review.py` — MetricThresholdReviewer + calibration
- `test_research_hypotheses.py` — HypothesisActionSpace + testability filter
- `test_research_dossier.py` — ResearchDossier + negative result aggregation

### CLI focused tests（6 passed）

```bash
python -m pytest tests/test_research_cli.py -q
```

- `test_research_run_cli_writes_traceable_artifacts`：passed summary → ADVANCE + 全部 artifact
- `test_research_run_cli_preserves_execution_failure_without_refuting`：failed summary → REFINE + failure 证据保留
- `test_research_run_cli_rejects_invalid_question`：非法 question → exit 2
- `test_research_run_cli_supports_multi_summary_and_sidecars`：多 summary → plural artifact + sidecar
- `test_research_run_cli_can_handoff_from_benchmark_output`：benchmark-run 输出目录 → research-run handoff
- `test_research_run_cli_supports_text_output_and_trace_printing`：`text` 输出 + trace 打印
- `test_research_run_cli_merges_negative_memory_sidecars`：跨 question 负结果记忆合并

### Format / Lint

```bash
ruff check src/metaharness/cli.py src/metaharness/core/research.py src/metaharness/research src/metaharness/sdk/research.py tests/test_research_cli.py
ruff format --check ...
```

All checks passed.

## 6.2 验证证据

截至 2026-05-02：

| 验证项 | 状态 | 证据 |
|--------|------|------|
| research 测试套件 | 39 passed | `test_research_*.py` |
| CLI focused tests | 3 passed | `test_research_cli.py` |
| Ruff check | All passed | focused check on research paths |
| Ruff format | 13 files already formatted | format check pass |
| Manual smoke | ADVANCE, artifacts present | `.runs/research-loop-smoke/` |
| CLI help | research-run 可见 | `--help` 输出 |
| Example input | exists | `examples/research/fealpy_poisson_question.json` |
| Fixtures | exists | passed + failed in `tests/fixtures/research/` |

## 6.3 非声明（Non-Claims）

Research Loop MVP **不声称**：

- 自动提出原创科学假设
- 自动解决开放未解科学问题
- 自动判断文献级创新性
- 自动生成可信论文
- 自动执行 PIVOT/RESCOPE/ABANDON 战略决策
- 自动通过 LLM reviewer 判断科学价值
- 运行真实 solver（只消费已有或 fixture 化的 benchmark summary）

## 6.4 显式延后能力

以下能力在 plan-v3 Section 12（Phase N）和 plan-v4 Section 8（后续 Phase 选项）中被**显式延后**，不是未完成工作：

### Phase N：开放科学发现愿景

- LLM-powered hypothesis generation
- Calibrated LLM reviewer agent
- Literature ingestion + novelty 判断
- Counterfactual reasoning
- "爱因斯坦测试"式原创理论发现
- Full natural-language paper generation + peer-review loop
- 开放未解问题 benchmarks（高熵合金、量子纠错、湍流）
- PIVOT/RESCOPE/ABANDON 自动治理

### 已实现的确定性增强

- benchmark-run → research-run pipeline handoff
- Multi-summary research run
- `--output-format text` / `--print-trace`
- ResearchDossier、MetricSchema、SOTA baseline、reproducibility、negative-result memory sidecars

### 后续 CLI UX 增强

- `--hypothesis`、`--plan` flags
- ResearchDossier 用户可读 artifact 暴露
- Reviewer gate 暴露

### 更深集成路径

- MetricSchema 提升进 benchmark core model
- Merkle provenance / audit graph 集成
- 跨 question dead-end 检测
- 可复现性门控（measure-twice gate）
- ReviewerProtocol.compare() head-to-head comparison
- Bayesian bandit SELECT（当前为 simple sort-based）

## 6.5 实施完整性

MVP 范围内（plan-v3 P0a–P4 + plan-v4 CLI）：
- 零未完成交付项
- 零未通过 test
- 零未修复 lint error
- 零设计矛盾

所有被 scope in 的内容已交付。所有被 scope out 的内容（Phase N、CLI UX 增强、更深集成）正确地保持在 scope out 状态。
