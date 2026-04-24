# 01. 扩展定位

## 1.1 目标

`metaharness_ext.jedi` 的目标不是重写 JEDI，而是把 JEDI 这类 **YAML-configured、launcher-driven、artifact-producing** 的数据同化应用族，以受控、可验证、可审计的方式接入 `Meta-Harness Engineer`。

当前最小 canonical 闭环是：

```text
spec -> environment probe -> controlled YAML -> explicit preprocessing -> mode-aware execution -> validation report
```

在这个基础上，还可以继续向 richer evidence interpretation 与 study seam 扩展，但这些属于后续能力叠加，而不是本页主线。

关于 execution mode、failure taxonomy 与 report 语义，分别以 [04-执行链设计](04-execution-pipeline.md)、[05-环境与验证](05-environment-and-validation.md) 为准。

---

## 1.2 为什么需要单独的 JEDI extension

JEDI 不能直接复用 `metaharness_ext.nektar` 或 `metaharness_ext.ai4pde` 的原因，不在于“求解器不同”，而在于它的控制面与失败边界不同：

- 配置主入口是 YAML，而不是 XML 或 Python-native config object
- 运行入口是 `<launcher> <app>.x config.yaml`，而不是单一本地函数调用
- `schema` / `validate-only` / `real-run` 三类模式需要分层建模，但它们都属于当前基础执行接口面
- 失败可能来自 binary、MPI launcher、shared library、testinput/data path，而不只是配置逻辑
- 证据面不仅是 stdout/stderr，还包括 diagnostics、output、reference/test files

因此，JEDI extension 必须把这些工程事实显式建模，而不是隐藏在“run solver”这一层笼统抽象后面。

---

## 1.3 选择哪一层作为 MHE 接口

JEDI 的潜在接入层可以粗分为四类：

- Level 1：模型接口 / Traits / State / Geometry / Model
- Level 2：观测算子 / UFO / QC / ObsFilter
- Level 3：YAML experiment config
- Level 4：外部 wrapper（launcher / executable / workflow）

`metaharness_ext.jedi` 的首版明确选择：

- **Level 4 为主**：MHE 负责 gateway、environment probe、compiler、executor、validator
- **Level 3 为辅**：MHE 负责生成受控 YAML，而不是透传任意 YAML
- **不进入 Level 1/2**：不在首版实现新的 model interface、obs operator 或 C++ binding

这不是能力不足，而是职责边界的刻意选择：MHE 擅长承接的是 **控制面治理、执行链编排、证据归档与结果判定**。

---

## 1.4 首版范围边界

### 在范围内

- family-aware typed contracts
- controlled YAML compiler
- environment probe
- mode-aware executor（包含 `schema` / `validate_only` / `real_run`）
- validation report
- manifest-driven packaging
- 面向 `variational` / `local_ensemble_da` / `hofx` / `forecast` 的 family 边界设计

### 不在范围内

- 新的 JEDI C++ 内核扩展
- IODA converter pipeline
- 任意 public executable 的自动发现和全覆盖支持
- HPC scheduler 编排
- 无约束 YAML patch / merge / round-trip 编辑
- 直接把 JEDI 变成 Python SDK

---

## 1.5 设计原则

### contract-first

所有输入都先进入 typed spec，再由 compiler 生成 YAML；研究层和 agent 层都不直接拼接原始 YAML。

### evidence-first

validator 不能只看 return code，必须保留 YAML、stdout、stderr、schema、diagnostics 等可审计证据。

### family-aware

不同 application family 的顶层结构、运行方式和失败语义不同，不能塞进一个松散的单一 spec。

### environment-explicit

binary 缺失、launcher 缺失、shared library 缺失、data path 缺失要作为显式 failure，而不是被误归因为配置错误。

---

## 1.6 与软件 wiki 的分界

如果问题属于以下范围，应优先查外部 JEDI 软件文档，而不是继续膨胀本目录：

- OOPS / IODA / UFO / SABER 的通用技术背景
- JEDI bundle 构建细节
- 各类 minimizer 的算法原理百科
- 观测系统的领域知识总览

本目录只保留这些背景对 `metaharness_ext.jedi` 设计真正产生约束的部分。