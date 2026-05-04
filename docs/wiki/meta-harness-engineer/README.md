# Meta-Harness Engineer Wiki Index

本目录收纳 `MHE` 的工程实现导向 wiki，面向需要理解、维护和扩展当前代码实现的研发人员。

`meta-harness-wiki/` 是当前 core framework 的 canonical 工程手册：覆盖 SDK、runtime、connection engine、safety、provenance、hot reload、optimizer，以及升级后的 assembly / instantiation / selection / metrics 框架。它同时给出 extension-improvement route，说明各科学计算 extension 如何把执行模式、外部证据、benchmark comparison、approval gate 与 assembly metrics 接入统一治理边界。

## 子目录导航

- [meta-harness-wiki/](meta-harness-wiki/README.md)
  - 通用 Meta-Harness / SDK / runtime / connection engine 技术手册
  - 包含升级后的 core framework 与 extension 改进指南：[11-upgraded-core-framework-and-extension-improvement.md](meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md)
- [nektar-engine-wiki/](nektar-engine-wiki/README.md)
  - `metaharness_ext.nektar` 的架构、contracts、执行链、测试与 roadmap
- [ai4pde-agent-wiki/](ai4pde-agent-wiki/README.md)
  - `metaharness_ext.ai4pde` 的 runtime、数据模型、治理、模板与 roadmap
- [jedi-engine-wiki/](jedi-engine-wiki/README.md)
  - `metaharness_ext.jedi` 的扩展设计 wiki：架构、contracts、执行链与 execution-mode / instantiation 边界
- [deepmd-engine-wiki/](deepmd-engine-wiki/README.md)
  - `metaharness_ext.deepmd` 的 JSON/workspace 执行模型、contracts、blueprint 与 roadmap
- [abacus-engine-wiki/](abacus-engine-wiki/README.md)
  - `metaharness_ext.abacus` 的 file-driven / launcher-aware 扩展设计、blueprint 与 roadmap
- [qcompute-engine-wiki/](qcompute-engine-wiki/README.md)
  - `metaharness_ext.qcompute` 的 simulator、PennyLane、Quafu gate、execution-mode、evidence 与 tested support matrix
- [octave-engine-wiki/](octave-engine-wiki/README.md)
  - `metaharness_ext.octave` 的 native numerical workflow、dry-run/real-tool gate、evidence 与 benchmark route
- [fealpy-engine-wiki/](fealpy-engine-wiki/README.md)
  - `metaharness_ext.fealpy` 的 FEM/PDE workflow、contracts、evidence、benchmark 与 scope boundaries
- [pycfd-engine-wiki/](pycfd-engine-wiki/README.md)
  - `metaharness_ext.pycfd` 的 CFD/PDE workflow、evidence bundle、benchmark comparison 与 real-source gate
- [BOUT++ extension blueprint](blueprint/10-boutpp-extension-blueprint.md)
  - `metaharness_ext.boutpp` 的 implemented baseline、implementation plan、roadmap 与 usage-validation slice
- [MOOSE extension blueprint](blueprint/11-moose-extension-blueprint.md)
  - `metaharness_ext.moose` 的 FEM simulation integration blueprint、implementation plan 与 roadmap
- [blueprint/](blueprint/)
  - 扩展 blueprint、路线图、handoff、gap report、对齐报告、benchmark CI/CD 和 core-improvement materials 的集中目录
- [research-loop-mvp-wiki/](research-loop-mvp-wiki/README.md)
  - Research Loop MVP 的架构演进、模型设计、实现历史、CLI 入口与验收边界
- [benchmark/](benchmark/README.md)
  - 跨 extension / agent / direct workflow 的 benchmark 设计、实验计划、approval gate、CI/CD 与结果报告

## Blueprint 快速入口

- [06-qcompute-extension-blueprint.md](blueprint/06-qcompute-extension-blueprint.md) — QCompute extension blueprint
- [06-qcompute-implementation-plan.md](blueprint/06-qcompute-implementation-plan.md) — QCompute implementation plan
- [06-qcompute-roadmap.md](blueprint/06-qcompute-roadmap.md) — QCompute roadmap
- [07-octave-extension-blueprint.md](blueprint/07-octave-extension-blueprint.md) — Octave extension blueprint
- [08-fealpy-extension-blueprint.md](blueprint/08-fealpy-extension-blueprint.md) — FEALPy extension blueprint
- [08-fealpy-roadmap.md](blueprint/08-fealpy-roadmap.md) — FEALPy roadmap
- [09-pycfd-extension-blueprint.md](blueprint/09-pycfd-extension-blueprint.md) — PyCFD extension blueprint
- [09-pycfd-roadmap.md](blueprint/09-pycfd-roadmap.md) — PyCFD roadmap
- [10-boutpp-extension-blueprint.md](blueprint/10-boutpp-extension-blueprint.md) — BOUT++ extension blueprint
- [10-boutpp-implementation-plan.md](blueprint/10-boutpp-implementation-plan.md) — BOUT++ implementation plan
- [10-boutpp-roadmap.md](blueprint/10-boutpp-roadmap.md) — BOUT++ roadmap
- [11-moose-extension-blueprint.md](blueprint/11-moose-extension-blueprint.md) — MOOSE extension blueprint
- [11-moose-extension-implementation-plan.md](blueprint/11-moose-extension-implementation-plan.md) — MOOSE implementation plan
- [11-moose-extension-roadmap.md](blueprint/11-moose-extension-roadmap.md) — MOOSE roadmap
- [12-benchmark-comparison-cicd-blueprint.md](blueprint/12-benchmark-comparison-cicd-blueprint.md) — Benchmark comparison CI/CD blueprint
- [12-benchmark-comparison-cicd-implementation-plan.md](blueprint/12-benchmark-comparison-cicd-implementation-plan.md) — Benchmark comparison CI/CD implementation plan
- [12-benchmark-comparison-cicd-roadmap.md](blueprint/12-benchmark-comparison-cicd-roadmap.md) — Benchmark comparison CI/CD roadmap
- [13-extension-core-improvement-blueprint.md](blueprint/13-extension-core-improvement-blueprint.md) — Extension core-improvement blueprint
- [13-extension-core-improvement-implementation-plan.md](blueprint/13-extension-core-improvement-implementation-plan.md) — Extension core-improvement implementation plan
- [13-extension-core-improvement-roadmap.md](blueprint/13-extension-core-improvement-roadmap.md) — Extension core-improvement roadmap

## 推荐阅读路径

### 如果你想先理解 MHE 基础设施

先看：
- [meta-harness-wiki/README.md](meta-harness-wiki/README.md)
- [meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md](meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md)

### 如果你正在维护 Nektar 扩展

先看：
- [nektar-engine-wiki/README.md](nektar-engine-wiki/README.md)

### 如果你正在维护 AI4PDE 扩展

先看：
- [ai4pde-agent-wiki/README.md](ai4pde-agent-wiki/README.md)

### 如果你正在规划或实现 JEDI 扩展

先看：
- [jedi-engine-wiki/README.md](jedi-engine-wiki/README.md)

### 如果你正在规划或实现 DeepMD 扩展

先看：
- [deepmd-engine-wiki/README.md](deepmd-engine-wiki/README.md)
- [blueprint/04-deepmd-extension-blueprint.md](blueprint/04-deepmd-extension-blueprint.md)
- [blueprint/04-deepmd-roadmap.md](blueprint/04-deepmd-roadmap.md)

### 如果你正在规划或实现 ABACUS 扩展

先看：
- [abacus-engine-wiki/README.md](abacus-engine-wiki/README.md)
- [blueprint/05-abacus-extension-blueprint.md](blueprint/05-abacus-extension-blueprint.md)
- [blueprint/05-abacus-roadmap.md](blueprint/05-abacus-roadmap.md)

### 如果你正在维护新增 extension 组合

先看：
- [qcompute-engine-wiki/README.md](qcompute-engine-wiki/README.md)
- [octave-engine-wiki/README.md](octave-engine-wiki/README.md)
- [fealpy-engine-wiki/README.md](fealpy-engine-wiki/README.md)
- [pycfd-engine-wiki/README.md](pycfd-engine-wiki/README.md)
- [blueprint/10-boutpp-extension-blueprint.md](blueprint/10-boutpp-extension-blueprint.md)
- [blueprint/11-moose-extension-blueprint.md](blueprint/11-moose-extension-blueprint.md)

### 如果你要理解 benchmark / research-loop surfaces

先看：
- [benchmark/README.md](benchmark/README.md)
- [research-loop-mvp-wiki/README.md](research-loop-mvp-wiki/README.md)

## Claim Boundaries

- Metrics、assembly report、benchmark comparison 与 research-loop trace 只能支持其输入 evidence 覆盖范围内的结论。
- dry-run / simulation 不是真实 solver、真实硬件或真实外部执行。
- external verification 必须有外部 evidence refs；本地 report、CI 通过或 agent summary 不能替代。
- optional real-tool / hardware paths 保持显式 gate，不能作为默认 CI 或默认运行假设。
