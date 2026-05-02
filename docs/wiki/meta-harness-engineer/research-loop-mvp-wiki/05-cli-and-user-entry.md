# 05 — CLI 与用户入口

## 5.1 research-run 子命令

定义位置：`src/metaharness/cli.py`（`_cmd_research_run` 函数, 行 403）

在 `metaharness` CLI 中注册为 `research-run`：

```
usage: metaharness research-run [-h] --question QUESTION
                                --summary SUMMARY --runs-root RUNS_ROOT
```

参数：
- `--question`：ResearchQuestion JSON 路径（必需）
- `--summary`：benchmark summary JSON 路径（必需）
- `--runs-root`：产物输出目录（必需）

## 5.2 示例输入

### Question

`examples/research/fealpy_poisson_question.json`：

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

### Summary（passed）

`tests/fixtures/research/fealpy_poisson_summary_passed.json`：

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

### Summary（failed）

`tests/fixtures/research/fealpy_poisson_summary_failed.json`：

```json
{
  "suite": "fealpy-pde",
  "case_id": "poisson-2d-numpy",
  "lane": "extension",
  "status": "failed",
  "failure_category": "runner_error"
}
```

## 5.3 运行命令

```bash
PYTHONPATH=src python -m metaharness.cli research-run \
  --question examples/research/fealpy_poisson_question.json \
  --summary tests/fixtures/research/fealpy_poisson_summary_passed.json \
  --runs-root .runs/research-loop-smoke
```

## 5.4 预期 stdout

passed summary（满足 primary metric 阈值）：

```json
{
  "artifacts": {...},
  "decision": "ADVANCE",
  "question_id": "rq-fealpy-poisson-l2-threshold",
  "runs_root": ".runs/research-loop-smoke",
  "scope": "deterministic benchmark-backed MVP research loop",
  "non_claims": [
    "open-ended discovery loop",
    "solver superiority",
    "generalized benchmark approval",
    "automated benchmark-to-research handoff"
  ]
}
```

failed summary（runner error）：

```json
{
  "decision": "REFINE",
  "question_id": "rq-fealpy-poisson-l2-threshold"
}
```

exit code：`0` 表示闭环成功完成（不管 decision 是 ADVANCE 还是 REFINE）。exit code `2` 表示输入错误（非法参数、缺失参数等）。

## 5.5 产物文件

`--runs-root` 下产出：

```text
.runs/research-loop-smoke/
  research_trace.jsonl       # 可回放的完整链路
  research_question.json     # 输入 question 副本
  hypothesis.json            # rule-based designer 推导的 hypothesis
  experiment_plan.json       # 实验计划
  evidence_bundle.json       # summary → evidence 映射结果
  decision.json              # ADVANCE 或 REFINE
  review.json                # MetricThresholdReviewer 输出
  research_dossier.json      # 聚合后的研究档案
  conclusion.json            # ResearchConclusion
  artifact_manifest.json     # 输入/产物元数据 + non-claims
```

## 5.6 设计约束

- hypothesis 默认由 FEALPy rule-based designer 从 question 确定性推导（不依赖外部 hypothesis 文件）
- 后续可通过 `--hypothesis` flag 支持显式输入，但不在 MVP 最小集中
- CLI 层只负责读取 JSON、组装对象、调用既有 orchestrator/store/designer，不修改 core research 语义
- 不把 iteration metadata 塞入 `ExecutionLifecycleService`
