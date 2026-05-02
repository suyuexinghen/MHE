# 架构升级计划 v4：Research Loop MVP 的用户入口切片

## 1. 文档定位与 plan-v3 关系

本文件是 `docs/plan-drafts/plan-v3.md` 之后的下一份计划文档。

`plan-v3.md` 完成了 Research Loop MVP 与 Science Discovery Vision 的分层：MVP 证明 MHE 可以把已有 benchmark artifact 包装成 `ResearchQuestion → Hypothesis → ExperimentPlan → EvidenceBundle → Decision` 的低侵入闭环；长期愿景再逐步走向开放科学发现。

`plan-v4.md` 不重写 v3，也不扩大到 Phase N。它只定义一个 MVP-adjacent 的下一步：把已经实现并验证的 Research Loop MVP 通过薄 `research-run` CLI 暴露给用户，并提供最小示例输入/输出路径。

## 2. blueprint / plan / roadmap 抽象层级与受众定义

- **Blueprint**：最高抽象层，描述 whole-system schema、长期架构原则、阶段划分、治理边界、关键概念与多 phase 关系。一个 blueprint 可以包含多个 phase。
- **Plan**：中间抽象层，面向用户和项目管理者，说明一个 phase 或工作切片的目标、范围、非目标、验收方式和已选方向。
- **Roadmap**：最低抽象层，面向 agent，增强 plan，补充目标文件、执行步骤、产物、验证命令、提交边界和 reviewer/verifier gates。

本项目采用关系：`blueprint > plan > roadmap`，这里的 `>` 表示抽象层级与约束范围，不表示时间长度。

含义：blueprint 约束长期 whole-system schema；每个 blueprint phase 可以落到一份用户可读 plan；同一切片可配套一份 agent 可执行 roadmap。Plan 与 roadmap 可以覆盖相同交付切片，但服务不同受众：plan 解释“用户为什么需要、完成后看见什么”；roadmap 解释“agent 如何落地、改哪些文件、如何验证”。

## 3. 已完成基线与证据

已完成基线：

- P0a-P4 Research Loop MVP 在当前仓库历史中已有对应实现提交：`0469052` lifecycle models、`3d065c6` evidence mappers/store、`d93c17f` FEALPy walking skeleton、`3c1ac2b` minimal orchestrator、`4f4ab3a` rule-based designer、`b9522b0` reviewer calibration、`2f04a89` hypothesis action space、`a95126b` dossier aggregation。
- MVP 覆盖研究对象建模、benchmark summary 到 evidence 的映射、轻量 store、deterministic decision、最小 orchestrator、review/calibration、hypothesis action space 与 dossier/负结果沉淀方向。
- 当前能力仍是 benchmark-backed research loop，不是开放科学发现系统。

验证证据：

- 可复跑测试入口：`python -m pytest tests/test_research_*.py -q`，覆盖 `tests/test_research_lifecycle_models.py`、`tests/test_research_mappers.py`、`tests/test_research_store.py`、`tests/test_research_walking_skeleton_fealpy.py`、`tests/test_research_experiment_design.py`、`tests/test_research_review.py`、`tests/test_research_hypotheses.py`、`tests/test_research_dossier.py`、`tests/test_research_orchestrator.py`。
- 最近 verifier 记录的测试状态为 `36 passed`、Research-loop 相关 Ruff check 已通过；该状态是本计划输入证据，实施前仍需按第 9 节复跑并记录 stdout。
- 最近 verifier 结论记录为无 blocker，非阻塞缺口为 `research-run` CLI 尚未接线；本文件不新增外部报告路径，也不把该结论扩展为 CLI 已完成。

边界声明：以上证据只证明 Research Loop MVP 的内部闭环已有可复跑测试入口与历史实现证据，不证明 CLI 已存在，也不证明 Phase N 自动科学发现已实现。

## 4. 本阶段选定方向：CLI 化 Research Loop MVP

本阶段选定方向：实现薄 `research-run` CLI，让用户能从命令行运行一个已有 benchmark summary 支撑的研究闭环。

目标体验：

```bash
PYTHONPATH=src python -m metaharness.cli research-run \
  --question examples/research/fealpy_poisson_question.json \
  --summary tests/fixtures/research/fealpy_poisson_summary_passed.json \
  --runs-root .runs/research-loop-smoke
```

预期输出路径：

```text
.runs/research-loop-smoke/
  research_trace.jsonl
  research_question.json
  hypothesis.json        # 默认由 rule-based designer 确定性生成；未来可支持显式输入
  experiment_plan.json
  evidence_bundle.json
  decision.json
  conclusion.json
```

本方向是 MVP-adjacent user-facing slice：它复用既有 research loop，不新增开放式 hypothesis generation，不接 LLM reviewer，不改 runtime graph，不驱动真实 solver。

## 5. 非目标与非声明

本阶段不做：

- 不声称 `research-run` CLI 已存在。
- 不把本切片归类为 Phase N discovery。
- 不实现自动原创科学假设生成。
- 不实现文献级 novelty 判断。
- 不实现论文生成。
- 不引入 LLM reviewer 自动决策。
- 不执行 PIVOT / RESCOPE / ABANDON 自动治理动作。
- 不修改 `HarnessRuntime`、`ConnectionEngine` 或 benchmark core model。
- 不运行真实 solver；只消费已有或 fixture 化的 benchmark summary。
- 不触碰当前无关 staged/untracked benchmark 文档、报告或测试文件。

本阶段目标只声明：让已验证的 Research Loop MVP 通过一个薄 CLI 被用户触达，并产出可检查、可回放的本地 artifact。

## 6. Plan：用户可读目标、范围、验收

用户目标：

- 用户提供一个 research question JSON。
- 用户提供一个 benchmark summary JSON。
- 用户运行 `PYTHONPATH=src python -m metaharness.cli research-run ...`。
- 用户在 `--runs-root` 下看到完整 trace 与关键 JSON artifact。
- 用户从 stdout 与 exit code 判断本次闭环是否成功完成，以及最终 decision 是 `ADVANCE` 还是 `REFINE`。

范围：

- 单 question。
- 单 hypothesis；本切片默认由 FEALPy MVP rule-based designer 从 question 确定性推导并写出 `hypothesis.json`。
- 显式 `--hypothesis` 只作为后续 UX 增强选项；若实现 agent 发现现有 API 已支持外部 hypothesis，可在不扩大 CLI 最小集的前提下作为可选输入处理。
- 单 benchmark summary。
- 单 `ResearchOrchestrator` 闭环。
- 单本地 runs root。
- 只支持 ground-truth benchmark-backed validation。

验收：

- `PYTHONPATH=src python -m metaharness.cli --help` 能看到 `research-run` 子命令。
- `research-run` 接受 `--question`、`--summary`、`--runs-root`。
- passed summary 且 primary metric 满足阈值时，输出 `ADVANCE` 并写出完整 artifact。
- failed summary 不直接 refute 科学假设，而是保留 execution failure 证据并走 `REFINE` 或等价 inconclusive 路径。
- `research_trace.jsonl` 可回放 question、hypothesis、plan、evidence、decision 的链路。
- CLI focused tests 与既有 research tests 通过。
- Ruff check / format check 通过。

## 7. Roadmap：agent 可执行步骤、目标文件、产物、验证命令、提交边界

### 7.0 实现前 API discovery

目标文件：

- `src/metaharness/sdk/research.py`
- `src/metaharness/core/research.py`
- `src/metaharness/research/store.py`
- `src/metaharness/research/domains/fealpy.py`
- `tests/test_research_*.py`

执行步骤：

- 先检查 `ResearchQuestion`、`Hypothesis`、`ExperimentPlan`、`EvidenceBundle`、`Decision` 的序列化入口。
- 确认 `ResearchOrchestrator` 的构造参数、返回值、错误模型与 trace 写入方式。
- 确认 store API 是否已有 artifact/JSONL 写出能力，避免在 CLI 中重复实现持久化语义。
- 确认 FEALPy rule-based designer 是否能从 question 确定性生成 hypothesis；不能时再使用最小示例 hypothesis fixture。
- discovery 结果决定 7.1 的最小接线方式；不得先假设 CLI 所需 API 已稳定。

产物：

- 一组实现前 notes，记录可直接复用的 API、缺口与不需要改动的 core 语义。

### 7.1 接线 CLI 子命令

目标文件：

- `src/metaharness/cli.py`

执行步骤：

- 在完成 7.0 discovery 后，新增 `research-run` argparse subcommand。
- 新增 `_cmd_research_run(args: argparse.Namespace) -> int` 或遵循现有 CLI handler 风格的等价函数。
- 参数最小集：`--question`、`--summary`、`--runs-root`。
- 输入错误返回非零 exit code，并输出可读错误。
- 成功时 stdout 输出 `question_id`、`decision`、`runs_root`、关键 artifact 路径。

产物：

- CLI 可被 `PYTHONPATH=src python -m metaharness.cli research-run ...` 调用。

### 7.2 增加最小示例输入

目标文件：

- `examples/research/fealpy_poisson_question.json`
- 可选：`examples/research/fealpy_poisson_hypothesis.json`，仅在 7.0 发现现有 API 需要外部 hypothesis 时使用；默认路径不要求该文件

执行步骤：

- question JSON 字段对齐现有 `ResearchQuestion` 模型。
- 示例只描述 ground-truth benchmark-backed question。
- 不写入开放科学发现、novelty 或论文生成声明。

产物：

- 用户可复制示例命令直接运行。

### 7.3 增加 summary fixture 或复用现有 fixture

目标文件：

- `tests/fixtures/research/fealpy_poisson_summary_passed.json`
- `tests/fixtures/research/fealpy_poisson_summary_failed.json`

执行步骤：

- 如果已有等价 fixture，优先复用。
- 如果缺失，新增最小 summary JSON fixture。
- fixture 必须小型、确定性、无需真实 solver。

产物：

- CLI tests 与 smoke command 不依赖外部环境。

### 7.4 复用 Research Loop MVP 内部能力

目标文件：

- `src/metaharness/core/research.py`
- `src/metaharness/research/store.py`
- `src/metaharness/research/domains/fealpy.py`
- `src/metaharness/sdk/research.py`

执行步骤：

- CLI 只负责读取 JSON、组装对象、调用既有 orchestrator/store/designer。
- 优先避免修改 core research 语义。
- 若 orchestrator 返回值缺少 CLI 所需拆分 artifact，优先在 CLI 层从返回对象或 store trace 写出用户可读 JSON。
- 不把 iteration metadata 塞入 `ExecutionLifecycleService`。

产物：

- `research_trace.jsonl` 由既有 store 路径生成。
- 拆分 JSON artifact 由 CLI 或 store 辅助写出。

### 7.5 增加 focused CLI 测试

目标文件：

- `tests/test_research_cli.py`

执行步骤：

- 测试 golden path：passed summary → exit code 0 → `ADVANCE` → artifact 存在。
- 测试 failure path：failed summary → 不直接 refute hypothesis → trace 保存 failure evidence。
- 测试输入错误：缺失 question/summary 或非法 JSON → 非零 exit code → 不写出误导性 conclusion。

验证命令：

```bash
python -m pytest tests/test_research_cli.py -q
python -m pytest tests/test_research_*.py -q
ruff check src/metaharness/cli.py src/metaharness/core/research.py src/metaharness/research src/metaharness/sdk/research.py tests/test_research_cli.py
ruff format --check src/metaharness/cli.py src/metaharness/core/research.py src/metaharness/research src/metaharness/sdk/research.py tests/test_research_cli.py
```

手动 smoke：

```bash
PYTHONPATH=src python -m metaharness.cli research-run \
  --question examples/research/fealpy_poisson_question.json \
  --summary tests/fixtures/research/fealpy_poisson_summary_passed.json \
  --runs-root .runs/research-loop-smoke
```

提交边界：

- 推荐单独提交：`feat(research): add research-run CLI smoke path`。
- 只包含 CLI、示例 JSON、fixture、focused tests 与必要的最小 research serialization glue。
- 不包含 benchmark report、approval evidence、Phase N 文档扩张或 runtime core 重构。
- 暂不提交，除非用户明确要求 commit。

## 8. 后续 Phase 选项

CLI 切片完成并通过 reviewer/verifier 后，可选择以下方向：

- **UX 增强**：支持 `--hypothesis`、`--plan`、`--output-format json`、`--print-trace`。
- **多 case research run**：从单 summary 扩展到多个 summary，但仍保持不直接运行 solver。
- **benchmark-run 衔接**：让 benchmark 输出路径自然传给 `research-run`。
- **Dossier 暴露**：把 `ResearchDossier` 作为用户可读 artifact 输出。
- **Reviewer gate 暴露**：只暴露已校准 deterministic reviewer 结果，不引入未校准 LLM 自动决策。
- **Phase N 预研**：另开 blueprint/phase 文档讨论开放科学发现，不与本 MVP-adjacent CLI 切片混合。

## 9. reviewer/verifier gates 与 handoff notes

实现前 gate：

- 确认 `research-run` 是待实现目标，不在文档或报告中写成已有能力。
- 确认当前工作树中无关 staged/untracked 文件不纳入本切片。
- 确认本切片不修改代码以外的 benchmark 报告或 approval evidence。

实现后 reviewer gate：

- reviewer 检查 CLI 是否为薄接线层，是否复用既有 research loop。
- reviewer 检查是否没有引入真实 solver、LLM、runtime graph mutation 或 Phase N 声明。
- reviewer 检查用户 artifact 是否可读、可追溯、可回放。
- reviewer 给出 `complete` 或 `needs changes` 明确结论。

实现后 verifier gate：

- 运行 `python -m pytest tests/test_research_cli.py -q`。
- 运行 `python -m pytest tests/test_research_*.py -q`。
- 运行相关 Ruff check / format check。
- 运行手动 smoke command，并记录 stdout 与 artifact 路径。
- verifier 给出 `complete` 或 `needs changes` 明确结论。

Handoff notes：

- 下一个实现 agent 只应触碰 CLI 切片相关文件。
- 如果发现 `ResearchOrchestrator` 缺少 CLI 所需的返回字段，优先在 CLI 层补用户 artifact，不扩大 core API。
- 示例输入应保持 ground-truth benchmark-backed，不引入开放科学发现承诺。
- Runtime 输出只放在 `.runs/` 下。
- 不要提交当前无关 staged/untracked 文件；如需 commit，必须显式 add 本切片相关路径。
