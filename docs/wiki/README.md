# MHE Wiki Index

本目录汇总 `Meta-Harness Engineer` 相关 wiki、benchmark 方法与研究手册，作为 `MHE/docs/wiki` 的统一入口。

## 目录导航

- [meta-harness-engineer/](meta-harness-engineer/README.md)
  - 工程实现导向的技术 wiki
  - 包含：Meta-Harness 核心 wiki、Nektar、AI4PDE、JEDI、DeepMD、ABACUS、QCompute、Octave、FEALPy、PyCFD extension wiki，以及 BOUT++ / MOOSE blueprint
  - 包含 benchmark comparison wiki、Research Loop MVP wiki、framework upgrade 与 extension core-improvement blueprint/plan/roadmap
  - 当前实现对齐的补充手册与归类文档已下沉到该目录树内
- [meta-harness-book/](meta-harness-book/README.md)
  - 研究/设计手册与论文式资料
  - 包含：章节草稿、研究报告、参考文献、导出的 PDF

## 推荐阅读路径

### 如果你要理解当前 MHE 工程实现

先看：
- [meta-harness-engineer/README.md](meta-harness-engineer/README.md)
- [meta-harness-engineer/meta-harness-wiki/README.md](meta-harness-engineer/meta-harness-wiki/README.md)
- [meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md](meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md)

### 如果你要理解 Nektar 扩展

先看：
- [meta-harness-engineer/nektar-engine-wiki/README.md](meta-harness-engineer/nektar-engine-wiki/README.md)

### 如果你要理解 AI4PDE 扩展

先看：
- [meta-harness-engineer/ai4pde-agent-wiki/README.md](meta-harness-engineer/ai4pde-agent-wiki/README.md)

### 如果你要理解 JEDI 扩展设计

先看：
- [meta-harness-engineer/jedi-engine-wiki/README.md](meta-harness-engineer/jedi-engine-wiki/README.md)

### 如果你要理解 DeepMD 扩展规划

先看：
- [meta-harness-engineer/deepmd-engine-wiki/README.md](meta-harness-engineer/deepmd-engine-wiki/README.md)
- [meta-harness-engineer/blueprint/04-deepmd-extension-blueprint.md](meta-harness-engineer/blueprint/04-deepmd-extension-blueprint.md)
- [meta-harness-engineer/blueprint/04-deepmd-roadmap.md](meta-harness-engineer/blueprint/04-deepmd-roadmap.md)

### 如果你要理解 ABACUS 扩展规划

先看：
- [meta-harness-engineer/abacus-engine-wiki/README.md](meta-harness-engineer/abacus-engine-wiki/README.md)
- [meta-harness-engineer/blueprint/05-abacus-extension-blueprint.md](meta-harness-engineer/blueprint/05-abacus-extension-blueprint.md)
- [meta-harness-engineer/blueprint/05-abacus-roadmap.md](meta-harness-engineer/blueprint/05-abacus-roadmap.md)

### 如果你要理解 QCompute 扩展

先看：
- [meta-harness-engineer/qcompute-engine-wiki/README.md](meta-harness-engineer/qcompute-engine-wiki/README.md)
- [meta-harness-engineer/blueprint/06-qcompute-extension-blueprint.md](meta-harness-engineer/blueprint/06-qcompute-extension-blueprint.md)
- [meta-harness-engineer/blueprint/06-qcompute-roadmap.md](meta-harness-engineer/blueprint/06-qcompute-roadmap.md)

### 如果你要理解 Octave / FEALPy / PyCFD 扩展

先看：
- [meta-harness-engineer/octave-engine-wiki/README.md](meta-harness-engineer/octave-engine-wiki/README.md)
- [meta-harness-engineer/fealpy-engine-wiki/README.md](meta-harness-engineer/fealpy-engine-wiki/README.md)
- [meta-harness-engineer/pycfd-engine-wiki/README.md](meta-harness-engineer/pycfd-engine-wiki/README.md)

### 如果你要理解 BOUT++ / MOOSE 扩展路线

先看：
- [meta-harness-engineer/blueprint/10-boutpp-extension-blueprint.md](meta-harness-engineer/blueprint/10-boutpp-extension-blueprint.md)
- [meta-harness-engineer/blueprint/10-boutpp-implementation-plan.md](meta-harness-engineer/blueprint/10-boutpp-implementation-plan.md)
- [meta-harness-engineer/blueprint/10-boutpp-roadmap.md](meta-harness-engineer/blueprint/10-boutpp-roadmap.md)
- [meta-harness-engineer/blueprint/11-moose-extension-blueprint.md](meta-harness-engineer/blueprint/11-moose-extension-blueprint.md)
- [meta-harness-engineer/blueprint/11-moose-extension-implementation-plan.md](meta-harness-engineer/blueprint/11-moose-extension-implementation-plan.md)
- [meta-harness-engineer/blueprint/11-moose-extension-roadmap.md](meta-harness-engineer/blueprint/11-moose-extension-roadmap.md)

### 如果你要理解 benchmark comparison 与 approval gates

先看：
- [meta-harness-engineer/benchmark/README.md](meta-harness-engineer/benchmark/README.md)
- [meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-blueprint.md](meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-blueprint.md)
- [meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md](meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md)
- [meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-roadmap.md](meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-roadmap.md)

### 如果你要理解 Research Loop MVP

先看：
- [meta-harness-engineer/research-loop-mvp-wiki/README.md](meta-harness-engineer/research-loop-mvp-wiki/README.md)

### 如果你要看更完整的研究背景或设计论述

先看：
- [meta-harness-book/README.md](meta-harness-book/README.md)

## 结论边界提醒

- benchmark、metrics、approval gate 与 research-loop 输出只支持其 evidence 覆盖范围内的 workflow/reporting 结论。
- dry-run / simulation 不等价于真实 execution。
- 科学有效性、数值正确性、硬件运行或外部验证需要单独的 external evidence refs。
