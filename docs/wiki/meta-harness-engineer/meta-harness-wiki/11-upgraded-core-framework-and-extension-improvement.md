# MHE Core 升级框架与 Extension 改进指南

本页介绍 MHE core 在 assembly / instantiation 升级后的新框架能力，并给出现有 extension 如何基于这些能力继续改进的工程路线。它面向维护 core runtime、扩展新 solver family、审查 benchmark/report 结论、以及把 extension 从“能跑一个 case”推进到“可治理、可审计、可比较”的研发人员。

本文只描述当前代码已经实现的框架能力和基于这些能力的改进建议，不把 dry-run、simulation、benchmark 通过、人工审批或科学有效性混为一谈。

## 升级后的核心问题

升级前，MHE core 主要回答：

- 一个 XML / manifest 组合能否形成合法 candidate graph。
- candidate graph 能否通过语义校验与安全门控。
- active graph version、rollback target、session event、audit/provenance 是否能串起来。
- extension 是否能通过自己的 contract、compiler、executor、validator 完成某类任务。

升级后，core 额外开始治理几个过去很难回答的问题：

- 一个 graph 是如何由组件、依赖、历史版本和 evidence 组装出来的。
- 哪些组件是新出现、低复用、低 copy-count 或关键依赖。
- extension 声称的执行模式到底是 simulation、dry-run、staged、instantiated，还是 externally verified。
- graph promotion 何时只是 warning，何时可以 opt-in defer，何时具备 evidence-backed reject 条件。
- component 被 promoted、suspended、deprecated 或 graveyard 的选择状态是否留下记录。
- assembly、instantiation、selection 的证据是否能被汇总成 machine-readable JSON 和 human-readable Markdown report。

这让 MHE core 从“图结构和接口治理”推进到“组装历史、实例化边界、选择压力和证据可见性治理”。

## 当前实现的新增框架层

### Assembly Ledger 与 Copy Count Index

`AssemblyLedger` 是 graph/runtime 外侧的 companion service，不替代 `GraphSnapshot`，也不把 registry 变成历史数据库。它记录 component registration、candidate graph、committed graph 和 dependency DAG snapshot。

`CopyCountIndex` 记录 per-session copy/reuse 计数，包括 registered、candidate membership、committed membership、dependency、invoked、external verified 等维度。它的目标不是证明组件质量，而是让低复用、高组装复杂度和关键依赖风险显性化。

Extension 可以从这里获得的收益：

- manifest dependency 不再只是 boot order 输入，也能成为 assembly evidence。
- repeated benchmark / repeated graph commit 可以累积 copy-count 信号。
- 新组件、低复用组件、关键依赖组件可以在 promotion/report 中被区别对待。

### Dependency DAG Snapshot 与 Assembly Health Summary

`DependencyGraphSnapshot` 把 candidate/committed graph 的 component refs、dependency edges、parent refs、evidence refs 和 conservative scoring 固化为可序列化对象。核心指标包括：

- `assembly_index`：保守的最长依赖路径深度。
- `history_folding_ratio`：组件复用比例。
- `lineage_completeness` / `lineage_status`：已知 lineage 覆盖情况。
- `low_copy_critical_dependency_count`：关键依赖中 copy-count 过低的数量。

`AssemblyHealthSummary` 把这些信号放入 promotion safety evidence 和 committed graph payload。默认仍是 report/warn，而不是自动拒绝。

Extension 可以从这里获得的收益：

- 把“这个 extension 只是临时拼装”与“这个 extension 复用了稳定组件链”区分开。
- benchmark report 可以解释性能或失败是否发生在低 lineage / high assembly-index 图上。
- roadmap 可以优先固化高价值、低复用、关键路径上的组件。

### ExecutionMode 与 InstantiationRecord

`ExecutionMode` 是 core 的标准化执行模式词表，用于把 extension-local mode 映射到可比较的核心边界：

- `simulation`
- `dry_run`
- `staged`
- `instantiated`
- `external_verified`
- `unknown`

`InstantiationRecord` 是 claim/action/evidence reconciliation 的边界对象。它可以保存 native execution mode、claim ref、action ref、run artifact ref、validation ref、internal evidence refs、external evidence refs 和 reconciliation status。

这不是要求 extension 放弃自己的 mode 词表。相反，extension 应保留 native mode，同时把它映射到 core mode，让跨 extension 报告可以比较“真实执行程度”。

Extension 可以从这里获得的收益：

- QCompute 的 `simulate`、JEDI 的 `validate_only` / `real_run`、DeepMD 的 DP-GEN staged flow 可以保留 native vocabulary，同时获得 core-level comparison。
- benchmark 结论可以明确区分 “passed simulation” 与 “externally verified real tool run”。
- extension report 可以把外部 receipt、solver log、hardware/backend proof、artifact hash 放到 external evidence refs 中。

### AssemblyHealthPolicy 与 SelectionLifecycle

`AssemblyHealthGate` 默认保持 `warn_only`，确保已有 extension 行为不被突然打断。配置后可以进入更严格模式：

- `warn_only`：记录风险，仍允许 promotion。
- `defer_high_risk`：对 evidence-backed high/critical risk 返回 defer。
- `reject_critical`：只在显式 critical mismatch evidence 下 reject。

`SelectionLifecycle` 记录 component selection state：

- `promoted`
- `deprecated`
- `suspended`
- `graveyard`

这使 selection pressure 变成可审计记录，而不是 reviewer 或报告中的口头判断。

Extension 可以从这里获得的收益：

- 一个 solver component 被 promotion、suspension 或 graveyard 时有 session/audit/provenance 记录。
- 高风险 extension 可以先以 `warn_only` 收集证据，再 opt-in 到 `defer_high_risk`。
- 只有明确 mismatch evidence 的真实实例化冲突才进入 reject，避免未知证据被误判为失败。

### AssemblyMetricsService 与 CLI Report

`AssemblyMetricsService` 聚合 assembly ledger、copy-count index、dependency DAG snapshot、assembly-health summary、instantiation records 和 selection lifecycle，输出 JSON snapshot 与 Markdown summary。

CLI 入口是：

```bash
PYTHONPATH=src python -m metaharness.cli metrics assembly \
  --graph examples/graphs/minimal-happy-path.xml \
  --manifests examples/manifests/baseline \
  --instantiation-record path/to/instantiation-record.json \
  --markdown-report .runs/assembly-metrics.md
```

报告的边界很重要：

- metrics 不证明科学有效性。
- dry-run 或 simulation evidence 不等价于 real-world instantiation。
- unknown evidence 不计入 externally verified execution。
- externally verified instantiation 必须有 `execution_mode == external_verified` 且存在 external evidence refs。

## Extension 升级通用路线

每个 extension 不需要一次性重写。推荐按以下顺序改进。

### 补齐 manifest dependency 与 capability dependency

优先把 extension 里的真实依赖显式写入 manifest：

- component dependency：例如 executor 依赖 compiler、validator 依赖 executor output。
- capability dependency：例如 solver capability、validation capability、evidence capability。
- critical dependency：对安全、真实运行、外部验证关键的组件要在 policy/evidence 中可定位。

这样 boot order、dependency DAG snapshot、assembly index 和低 copy-count warning 才有可靠输入。

### 让执行证据进入 core reconciliation

Extension executor / validator 仍然可以返回自己的 artifact model，但应在 evidence recorder 或 handoff 层补充：

- `execution_mode`
- `native_execution_mode`
- `instantiation_record`
- `external_evidence_refs`
- `candidate_id`
- `graph_version`

建议把 native mode 原样保留，core mode 只做规范化比较。

### 把外部验证做成 receipt，而不是描述文字

如果 extension 运行了真实工具、真实后端或真实硬件，报告应提供可检查的 external evidence refs，例如：

- solver binary path / version / command manifest。
- stdout/stderr snapshot。
- output artifact hash。
- environment probe result。
- hardware/backend provider receipt。
- benchmark run summary path。

这些 refs 可以成为 `InstantiationRecord.external_evidence_refs`，也可以被后续 metrics/report 汇总。

### 使用 selection lifecycle 表达组件命运

当 extension family 进入迭代维护阶段时，应把 component state 从“文档结论”推进到 lifecycle evidence：

- 通过 benchmark 和 review 的 component：`promoted`。
- 暂停使用但仍保留证据的 component：`suspended`。
- 明确不再推荐的 component：`deprecated`。
- 高风险或错误路线：`graveyard`。

这会帮助 roadmap 说明为什么某个实现被保留、暂停或淘汰。

### 用 metrics report 驱动 roadmap，而不是只看 case pass/fail

Extension report 不应只说“这个 case pass 了”。Phase 5 之后，推荐同时观察：

- assembly index 是否越来越低。
- history folding ratio 是否上升。
- low-copy critical dependency 是否减少。
- unknown instantiation 是否减少。
- external verified instantiation 是否增加。
- promoted / suspended / graveyard state 是否符合 roadmap 判断。

这些指标更适合支持 framework-level improvement，而不是单次 solver 成败。

## Extension Family 改进分析

### AI4PDE

AI4PDE 有较强的研究-loop、evidence manager、experiment memory 和 validation policy 基础。它最适合率先使用新 core 能力来治理“研究假设到实例化证据”的链路。

优先改进：

- 把 problem formulator、method router、solver executor、physics validator、evidence manager 的 dependency relation 显式写入 manifest。
- 把 template instantiation / solver execution / validation report 映射到 `ExecutionMode`，区分 symbolic plan、simulation、dry-run 和真正 solver execution。
- 让 evidence manager 输出 `InstantiationRecord`，把 run artifact、validation report、benchmark summary 和 external solver receipt 连接起来。
- 用 assembly metrics 对比不同 PDE workflow 的 reuse ratio 和 assembly index，避免只凭单个 benchmark case 判断方法优劣。
- 把失败但有价值的路线记录为 suspended 或 graveyard selection state，服务 negative-result memory。

不应宣称：AI4PDE 的 metrics 证明模型科学正确。它们只说明 workflow 证据链更完整、更可审计。

### Nektar

Nektar extension 偏 file/session compiler、executor、postprocess、convergence validator 的传统 solver pipeline。它适合用新 core 能力强化真实工具运行与外部 evidence 边界。

优先改进：

- 把 session compiler、executor、postprocess、convergence analyzer 的 dependency DAG 固化。
- 将 “XML/session 渲染成功” 标为 dry-run 或 staged，而不是 instantiated。
- 只有真实 `nektar++` binary 执行并产生可检查输出时，才记录 instantiated 或 external_verified。
- 把 solver version、mesh/session file hash、stdout/stderr、postprocess outputs 放入 external evidence refs。
- 用 `defer_high_risk` 策略试运行低-copy critical dependency，例如新 solver adapter 或新 postprocess chain。

不应宣称：Nektar wrapper 通过 dry-run 就等价于真实 PDE 求解完成。

### JEDI

JEDI 已经有 native execution mode，如 `schema`、`validate_only`、`real_run`，非常适合映射到 core `ExecutionMode`。

优先改进：

- 保留 `JediExecutionMode`，同时在 evidence recorder 中映射：`schema` / `validate_only` 到 dry_run，`real_run` 到 instantiated，外部结构化 diagnostics 充分时才 external_verified。
- 把 diagnostics、departure files、reference files、launcher metadata 作为 external evidence refs。
- 对 `real_run` completed but no structured diagnostics 的情况记录 critical mismatch candidate，而不是简单通过。
- 将 application family、cost type、launcher、process count 等作为 instantiation attributes，服务跨 case metrics。
- 用 selection lifecycle 记录哪些 JEDI workflow profile 可以 promoted，哪些只适合 staged 或 suspended。

不应宣称：`real_run` 字符串本身证明外部验证；必须有 structured diagnostics 或 receipt。

### DeepMD / DP-GEN

DeepMD/DP-GEN extension 天然是 staged workflow：workspace、train config、machine config、collector、validator、governance 分阶段推进。

优先改进：

- 把 DP-GEN 阶段映射到 staged core mode，避免把 workspace/config generation 误标为 instantiated。
- 只有真实训练、采样、模型输出和 validation artifacts 形成闭环时，才提升到 instantiated。
- 把 dataset refs、model checkpoint hash、training logs、validation metrics 和 environment probe 放入 InstantiationRecord。
- 用 assembly index 分析复杂 workflow 是否因为临时 glue code 过多而增加风险。
- 用 history folding ratio 观察 compiler / validator / governance adapter 是否正在稳定复用。

不应宣称：生成 DP-GEN config 或 workspace 就等于完成材料模拟验证。

### QCompute

QCompute extension 的关键是区分 simulator、mock backend、real backend、hardware/backend proof 和 chemistry/ABACUS handoff。

优先改进：

- 将 `simulate` / mock backend 映射为 simulation，不计入 external verified。
- 真实 backend 或 provider receipt 存在时，才创建 external_verified InstantiationRecord。
- 把 circuit hash、backend name、shot count、mitigation config、result payload hash、provider receipt 写入 external evidence refs。
- 对 QCompute → ABACUS / Hamiltonian proxy handoff，显式记录 cross-extension dependency DAG。
- 用 assembly metrics 说明量子 workflow 是否正在减少临时 adapter、增加可复用 component。

不应宣称：mock/qiskit-aer/pennylane-aer simulation 等同真实量子硬件运行。

### ABACUS

ABACUS extension 更靠近 file-driven scientific execution 与 launcher-aware environment validation。它适合用 instantiation boundary 区分 input generation、launcher dry-run 和真实 DFT execution。

优先改进：

- 把 input compiler、environment probe、launcher、validator、evidence adapter 分成显式 component dependency。
- 把 input deck generation 标为 dry_run 或 staged。
- 把真实 ABACUS binary、launcher command、output directory hash、SCF/convergence logs 作为 external evidence refs。
- 与 QCompute handoff 时，记录 Hamiltonian/input source refs，避免跨 extension claim 断裂。
- 用 selection lifecycle 管理不同 launcher/backend profile 的 promoted/suspended 状态。

不应宣称：input files 生成成功就等于 DFT calculation 已真实完成。

### Octave

Octave extension 是较轻量的 native numerical workflow，适合作为 core metrics/report 的教学和回归基准。

优先改进：

- 把 direct script generation、execution、summary comparison 拆成可观察 dependency path。
- 把 fake-claude / dry-run agent output 与 real octave-cli execution 分开记录。
- 将 octave binary availability、command manifest、generated script hash、summary JSON path 放入 instantiation evidence。
- 用 metrics report 作为 benchmark-run 与 research-run handoff 的 sidecar。

不应宣称：agent 生成脚本或 dry-run summary 等于真实 octave execution。

### FEALPy

FEALPy extension 与 research-loop MVP 已经有 benchmark summary、question/hypothesis/evidence bundle 连接点。它适合把 PDE benchmark evidence 与 assembly/instantiation metrics 结合。

优先改进：

- 对 FEALPy case runner 输出 InstantiationRecord，区分 numpy/reference dry-run、library-backed execution 和 externally verified run。
- 将 solver version、mesh/problem spec、result metrics、benchmark summary path 作为 evidence refs。
- 在 research-run handoff 中引入 assembly metrics sidecar，避免只从 primary metric 评价 workflow。
- 用 selection lifecycle 管理 case family 或 solver profile 的 promoted/suspended 状态。

不应宣称：research decision `ADVANCE` 等于 solver superiority。

### PyCFD

PyCFD extension 正在形成 PDE engine workflow、benchmark runner、compiler、study 结构。新 core 能力可以帮助它从早期 extension 走向可比较 pipeline。

优先改进：

- 在 manifest 中补齐 compiler、runner、validator、study component dependencies。
- 把 generated case/config 与 actual CFD execution 分成 dry_run/staged/instantiated。
- 将 solver logs、field output hash、residual history、validation summary 写入 external evidence refs。
- 用 low-copy critical dependency 指标识别尚未稳定的 compiler/runner glue code。
- 通过 selection lifecycle 标记推荐 case profiles 和被淘汰的 experimental profiles。

不应宣称：case compilation 或 synthetic benchmark summary 证明 CFD solver 正确。

### BOUT++

BOUT++ extension 新增较晚，仍适合以 Phase 6 指南作为成熟路线：先补 assembly evidence，再补 instantiation evidence，最后进入 enforcement。

优先改进：

- 把 benchmark cases、compiler、environment、executor、governance、policy、study、validator 的 dependency path 写入 manifest。
- 将 usage validation、real smoke、full solver run 分成 dry_run、staged、instantiated 或 external_verified。
- 将 BOUT++ binary probe、input deck hash、run directory hash、stdout/stderr、restart/output artifacts 作为 external evidence refs。
- 先在 warn_only 模式收集 assembly health，再对真实 smoke lane opt-in `defer_high_risk`。
- 用 metrics report 追踪 BOUT++ extension 从 low-copy glue 到 reusable solver pipeline 的成熟过程。

不应宣称：usage validation 或 mocked executor 等于真实 BOUT++ simulation。

## Cross-Extension 改进优先级

如果要统一推进所有 extension，建议按以下顺序：

| 优先级 | 工作 | 产出 | 受益 |
| --- | --- | --- | --- |
| 高 | manifest dependency audit | dependency DAG 更真实 | assembly index / lineage metrics 可用 |
| 高 | execution mode mapping | core/native mode 双记录 | simulation 与 instantiation 不再混淆 |
| 高 | InstantiationRecord handoff | run/action/evidence 可追溯 | metrics/report 可比较 |
| 中 | external evidence refs 标准化 | receipt/hash/log/path 统一 | externally verified 结论更可信 |
| 中 | selection lifecycle use | promoted/suspended/deprecated/graveyard 可审计 | roadmap 和 review 更清楚 |
| 中 | metrics sidecar in benchmark/research outputs | JSON/Markdown 可复用 | manager/report 不只看 pass/fail |
| 后续 | opt-in health enforcement | defer/reject 有证据边界 | 高风险 extension promotion 更稳 |

## Review Checklist

维护 extension 或审查 report 时，可以用以下 checklist：

- Manifest 是否表达了真实 dependency，而不是只让 boot order 侥幸通过。
- Assembly health summary 是否包含 dependency graph ref 和 evidence refs。
- Native execution mode 是否被保留，同时映射到 core `ExecutionMode`。
- Simulation/dry-run/staged 是否没有被写成 instantiated。
- External verified 是否同时具备 external evidence refs。
- Unknown evidence 是否没有被计入 externally verified。
- Selection state 是否记录了 promoted/suspended/deprecated/graveyard。
- Metrics report 是否说明 non-claims。
- Benchmark/research conclusion 是否避免把 framework evidence 误写成 scientific proof。

## 落地蓝图与路线图

面向全体 extension 的 portfolio-level 改进材料：

- [Extension Core-Improvement Blueprint](../blueprint/13-extension-core-improvement-blueprint.md)
- [Extension Core-Improvement Implementation Plan](../blueprint/13-extension-core-improvement-implementation-plan.md)
- [Extension Core-Improvement Roadmap](../blueprint/13-extension-core-improvement-roadmap.md)

## 推荐落地方式

每个 extension 的下一轮改进可以采用一个小 slice：

- 选择一个代表性 case。
- 补齐该 case 的 manifest dependency。
- 在 executor/validator handoff 中生成一个 InstantiationRecord。
- 在 benchmark output 中保留 external evidence refs。
- 运行 `metaharness metrics assembly` 生成 JSON 和 Markdown。
- 在 extension wiki 中加入 “assembly / instantiation evidence boundary” 小节。
- 如果 evidence 已稳定，再考虑对该 extension family 使用 `defer_high_risk` 策略。

这样做可以避免一次性重写 extension，同时让每一步都有可测试、可审计、可报告的产物。

## 结论

升级后的 MHE core 不再只关心“图是否合法”或“case 是否通过”。它开始把组装历史、复用程度、执行真实性、选择状态和证据边界纳入统一框架。Extension 的下一阶段改进重点，也应从“新增更多 wrapper”转向“让 wrapper 的依赖、执行、验证和选择命运都可审计”。

这套能力仍然是工程治理能力，不是科学正确性证明。更强的 extension 结论必须来自真实工具执行、外部 evidence refs、重复实验、领域 validator 和明确的 report non-claims。
