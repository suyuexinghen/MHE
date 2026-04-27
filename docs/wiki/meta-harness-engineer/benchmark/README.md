# Benchmark Wiki

> 版本：v0.1 | 最后更新：2026-04-27

本目录收纳 MHE 相关 benchmark 设计、实验计划与结果报告。它不替代各 extension 的设计 wiki，而是记录跨工具、跨流程、跨 agent 形态的对比实验。

## 目录导航

| 文档 | 主题 | 读者 |
|---|---|---|
| [01-Octave-native 与 Nektar PDE 双任务 Benchmark](01-nektar-pde-agent-vs-direct-octave.md) | 拆分为方向 A：Octave 9.2.0 native cases，方向 B：Nektar++ PDE cases；两者都采用 extension pipeline baseline、direct Claude CLI、MHE Claude CLI agent 三层 lane | MHE / Octave / Nektar 维护者 |
| [02-Octave-native Benchmark 测试方法报告](02-octave-native-benchmark-method.md) | 具体展开 Octave-native cases 的 spec、extension baseline、direct Claude CLI、MHE Claude CLI agent、metrics、attempt log、comparator 与 acceptance criteria | MHE / Octave 维护者 |
| [03-Nektar PDE Benchmark 测试方法报告](03-nektar-pde-benchmark-method.md) | 具体展开 Nektar PDE cases 的 spec、extension baseline、direct Claude CLI、MHE Claude CLI agent（`metaharness_ext.nektar`）、error norm 解析、attempt log、comparator 与 acceptance criteria | MHE / Nektar 维护者 |

## 写作边界

- 只记录 benchmark 任务设计、实验协议、交付物和报告结构。
- 不在本目录承诺某个 extension 已完成未验证能力。
- 不把 Nektar++ mesh utility 测试误写成 PDE solver benchmark；`utilities/NekMesh/Tests/Nektar++` 可作为 mesh/geometry 参考，但 PDE 方程 benchmark 应优先参考 solver tests。
- 实验产物默认写入 `.runs/`，报告再引用 summary JSON 与 evidence 文件。
