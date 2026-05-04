# MHE Documentation Index

本目录保留面向使用者与当前实现的入口文档；扩展设计、路线图、benchmark 方法、research-loop 资料和历史报告下沉到 `wiki/`、`blueprint/` 或 `docs/.trash/`。

## Root Guides

- [USER_GUIDE.md](USER_GUIDE.md) — 面向使用者的主操作指南
- [TEST_GUIDE.md](TEST_GUIDE.md) — 面向开发者/维护者的测试与验证指南
- [TECHNICAL_MANUAL.md](TECHNICAL_MANUAL.md) — 当前 MHE 实现对齐的英文技术手册
- [qcompute-user-manual.md](qcompute-user-manual.md) — QCompute 使用、测试、硬件 gate 与 claim boundary 指南

## Wiki Navigation

- [wiki/README.md](wiki/README.md) — 全量 wiki 总入口
- [wiki/meta-harness-engineer/README.md](wiki/meta-harness-engineer/README.md) — 工程实现导向 wiki
- [wiki/meta-harness-engineer/meta-harness-wiki/README.md](wiki/meta-harness-engineer/meta-harness-wiki/README.md) — Meta-Harness core / SDK / runtime 工程 wiki
- [wiki/meta-harness-engineer/benchmark/README.md](wiki/meta-harness-engineer/benchmark/README.md) — benchmark comparison、approval gate、CI/CD 与结论边界索引
- [wiki/meta-harness-engineer/research-loop-mvp-wiki/README.md](wiki/meta-harness-engineer/research-loop-mvp-wiki/README.md) — benchmark-backed Research Loop MVP wiki
- [wiki/meta-harness-book/README.md](wiki/meta-harness-book/README.md) — 研究/设计导向文档

## Framework Upgrade And Portfolio Roadmaps

- [wiki/meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md](wiki/meta-harness-engineer/meta-harness-wiki/11-upgraded-core-framework-and-extension-improvement.md) — assembly、instantiation、selection、metrics 升级后的 core 能力与 extension 改进指南
- [wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-blueprint.md](wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-blueprint.md) — extension core-improvement blueprint
- [wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-implementation-plan.md](wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-implementation-plan.md) — extension core-improvement implementation plan
- [wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-roadmap.md](wiki/meta-harness-engineer/blueprint/13-extension-core-improvement-roadmap.md) — extension core-improvement roadmap
- [wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-blueprint.md](wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-blueprint.md) — benchmark comparison CI/CD blueprint
- [wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md](wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-implementation-plan.md) — benchmark comparison CI/CD implementation plan
- [wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-roadmap.md](wiki/meta-harness-engineer/blueprint/12-benchmark-comparison-cicd-roadmap.md) — benchmark comparison CI/CD roadmap

## Extension Wikis

- [wiki/meta-harness-engineer/ai4pde-agent-wiki/README.md](wiki/meta-harness-engineer/ai4pde-agent-wiki/README.md) — AI4PDE extension wiki
- [wiki/meta-harness-engineer/nektar-engine-wiki/README.md](wiki/meta-harness-engineer/nektar-engine-wiki/README.md) — Nektar extension wiki
- [wiki/meta-harness-engineer/deepmd-engine-wiki/README.md](wiki/meta-harness-engineer/deepmd-engine-wiki/README.md) — DeepMD / DP-GEN extension wiki
- [wiki/meta-harness-engineer/jedi-engine-wiki/README.md](wiki/meta-harness-engineer/jedi-engine-wiki/README.md) — JEDI extension wiki
- [wiki/meta-harness-engineer/abacus-engine-wiki/README.md](wiki/meta-harness-engineer/abacus-engine-wiki/README.md) — ABACUS extension wiki
- [wiki/meta-harness-engineer/qcompute-engine-wiki/README.md](wiki/meta-harness-engineer/qcompute-engine-wiki/README.md) — QCompute extension wiki
- [wiki/meta-harness-engineer/octave-engine-wiki/README.md](wiki/meta-harness-engineer/octave-engine-wiki/README.md) — Octave extension wiki
- [wiki/meta-harness-engineer/fealpy-engine-wiki/README.md](wiki/meta-harness-engineer/fealpy-engine-wiki/README.md) — FEALPy extension wiki
- [wiki/meta-harness-engineer/pycfd-engine-wiki/README.md](wiki/meta-harness-engineer/pycfd-engine-wiki/README.md) — PyCFD extension wiki
- [wiki/meta-harness-engineer/blueprint/10-boutpp-extension-blueprint.md](wiki/meta-harness-engineer/blueprint/10-boutpp-extension-blueprint.md) — BOUT++ extension blueprint
- [wiki/meta-harness-engineer/blueprint/11-moose-extension-blueprint.md](wiki/meta-harness-engineer/blueprint/11-moose-extension-blueprint.md) — MOOSE extension blueprint

## Claim Boundaries

- Metrics and benchmark reports improve governance, reproducibility, and auditability; they do not prove scientific validity by themselves.
- Simulation and dry-run paths are not real execution.
- External verification requires explicit external evidence refs such as solver logs, receipts, artifact hashes, reviewed tolerances, or hardware/backend proof.
- Optional real-tool and hardware paths remain gated by local prerequisites, credentials, and explicit opt-in.

## Reclassified Documents

以下文档已经迁入更合适的子目录：

- 扩展与优化器开发规范：见 `wiki/meta-harness-engineer/meta-harness-wiki/10-extension-guide.md` 与 `05-self-growth.md`
- 受保护组件与稳定性策略：见 `wiki/meta-harness-engineer/meta-harness-wiki/02-component-sdk.md`、`03-core-components.md`、`06-safety-governance.md`
- AI4PDE / Nektar 对比手册：`wiki/meta-harness-engineer/ai4pde-agent-wiki/06-ai4pde-nektar-comparison.md`
- ABACUS handoff 报告：`wiki/meta-harness-engineer/blueprint/05-abacus-extension-handoff-report.md`
- MHE wiki 差距 / 对齐 / 近期工作报告：见 `wiki/meta-harness-engineer/blueprint/`

## Archive

- [docs/.trash/](.trash/) — 已被现有 canonical 页面吸收的旧根目录文档归档
