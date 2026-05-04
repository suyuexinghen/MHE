# Benchmark Wiki

> 版本：v0.3 | 最后更新：2026-05-03

本目录收纳 MHE 相关 benchmark 设计、实验计划与结果报告。它不替代各 extension 的设计 wiki，而是记录跨工具、跨流程、跨 agent 形态的对比实验。

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-Octave-native 与 Nektar PDE 双任务 Benchmark](01-nektar-pde-agent-vs-direct-octave.md) | 拆分为方向 A：Octave 9.2.0 native cases，方向 B：Nektar++ PDE cases；两者都采用 extension pipeline baseline、direct Claude CLI、MHE Claude CLI agent 三层 lane | MHE / Octave / Nektar 维护者 |
| [02-Octave-native Benchmark 测试方法报告](02-octave-native-benchmark-method.md) | 具体展开 Octave-native cases 的 spec、extension baseline、direct Claude CLI、MHE Claude CLI agent、metrics、attempt log、comparator 与 acceptance criteria | MHE / Octave 维护者 |
| [03-Nektar PDE Benchmark 测试方法报告](03-nektar-pde-benchmark-method.md) | 具体展开 Nektar PDE cases 的 spec、extension baseline、direct Claude CLI、MHE Claude CLI agent（`metaharness_ext.nektar`）、error norm 解析、attempt log、comparator 与 acceptance criteria | MHE / Nektar 维护者 |
| [04-QCompute × ABACUS Hamiltonian Proxy Benchmark Method](04-qcompute-abacus-hamiltonian-proxy-benchmark-method.md) | 具体展开 `qcompute-abacus` suite 的 H2 FCIDUMP/VQE proxy、JW/BK mapping comparison、Steane QEC memory-syndrome dry-run、ABACUS H/S bridge sentinel、metrics、evidence 与 non-claims | MHE / QCompute / ABACUS / QEC 维护者 |
| [05-Octave-native Benchmark 实验分析报告](04-octave-native-experiment-analysis.md) | 汇总 Octave-native dry-run benchmark 结果、lane evidence、限制与 real-run backlog | MHE / Octave 维护者 |
| [06-Nektar PDE Benchmark 实验分析报告](05-nektar-pde-experiment-analysis.md) | 汇总 Nektar PDE dry-run benchmark 结果、preflight、capability skip、限制与 real-run backlog | MHE / Nektar 维护者 |
| [07-QCompute × ABACUS Hamiltonian Proxy 实验分析报告](07-qcompute-abacus-experiment-analysis.md) | 汇总 qcompute-abacus dry-run benchmark 结果、H2 proxy、H/S bridge sentinel 与 real-run backlog | MHE / QCompute / ABACUS 维护者 |
| [08-Benchmark Roadmap Completion Status](06-benchmark-roadmap-completion-status.md) | 对照 `01` / `02` / `03` roadmap 的实现状态、产物路径、acceptance criteria 和后续 real-run 协议 | MHE 维护者 |
| [09-Real-run Evidence Plan and Deeper Benchmark Analysis](08-real-run-evidence-plan-analysis.md) | 规划下一阶段 real solver / real Claude repeated runs，并汇总 2026-04-30 dry-run repeat smoke 与后续报告边界 | MHE 维护者 / 项目管理者 |
| [10-Nektar PDE Benchmark Work Report](reports/nektar-pde-work-report-20260501.md) | 汇总 Nektar PDE benchmark 工作进展、证据边界、风险分析与下一步行动建议 | MHE 维护者 / 项目管理者 |
| [11-Benchmark Approval-Gating Work Report](reports/approval-gating-work-report.md) | 汇总 benchmark comparison 管理员认可 gate、suite approval manifests、ABACUS scientific blocker 与下一步行动建议 | MHE 维护者 / 项目管理者 |
| [12-BOUT++ Usage Validation Method](09-boutpp-usage-validation-method.md) | 记录 BOUT++ extension baseline、direct CLI/manual workflow、agent-assisted workflow 的 dry-run usage validation slice | MHE / BOUT++ 维护者 |
| [13-BOUT++ Real Smoke Method](11-boutpp-real-smoke-method.md) | 记录使用本地 `/home/linden/code/work/Solvers/FEM/BOUT-dev/build` 构建进行 opt-in real BOUT++ smoke evidence 的方法、skip gate 与 claim boundary | MHE / BOUT++ 维护者 |
| [14-PyCFD PDE Comparison Benchmark Method](10-pycfd-pde-benchmark-method.md) | 设计 PyCFD 2D Euler FVM comparison benchmark：extension/direct/agent lanes、real solver 与 real Claude 分离、residual metrics、approval gates 和 non-claim boundaries | MHE / PyCFD / PDE benchmark 维护者 |
| [15-Benchmark Comparison CI/CD Blueprint](../blueprint/12-benchmark-comparison-cicd-blueprint.md) | 设计 Octave、Nektar、QCompute/QEC、PyCFD、Fealpy benchmark comparison 的 PR、nightly、weekly、release CI/CD 分层 | MHE 维护者 / CI 维护者 |
| [16-Benchmark Comparison CI/CD Implementation Plan](../blueprint/12-benchmark-comparison-cicd-implementation-plan.md) | 记录复用 `benchmark-run` / `benchmark-compare` / `benchmark-approval-check` 的 workflow 实施步骤和验证命令 | MHE 维护者 / CI 维护者 |
| [17-Benchmark Comparison CI/CD Roadmap](../blueprint/12-benchmark-comparison-cicd-roadmap.md) | 规划从 dry-run CI 到 real tools、real Claude、repeat aggregation 和 release approval gate 的证据升级路径 | MHE 维护者 / 项目管理者 |
| [MHE Extension Comparison Conclusions](mhe-extension-comparison-conclusions.md) | 集中记录 MHE extension benchmark 对比结论、claim boundary、术语解释和 dated conclusion log | MHE 维护者 / 项目管理者 |

## 写作边界

- 只记录 benchmark 任务设计、实验协议、交付物和报告结构。
- 不在本目录承诺某个 extension 已完成未验证能力。
- 不把 Nektar++ mesh utility 测试误写成 PDE solver benchmark；`utilities/NekMesh/Tests/Nektar++` 可作为 mesh/geometry 参考，但 PDE 方程 benchmark 应优先参考 solver tests。
- 实验产物默认写入 `.runs/`；空间受限的重复 real-run 可写入 `/var/tmp/mhe-runs/<run-id>`，报告必须显式引用外部 run root、summary JSON 与 evidence 文件。
