# 02. 架构总览

## 2.1 组件链

本文档定义组件职责边界；具体 contract、execution mode 与 failure taxonomy 分别以 [03-contracts 设计](03-contracts.md)、[04-执行链设计](04-execution-pipeline.md)、[05-环境与验证](05-environment-and-validation.md) 为准。

`metaharness_ext.jedi` 的推荐组件链如下：

```text
JediGateway
  -> JediEnvironmentProbe
    -> JediConfigCompiler
      -> JediInputPreprocessor
        -> JediExecutor
          -> JediValidator
```

在这个基础主链之外，diagnostics collector、evidence / policy seam 与更丰富的解释层可以继续叠加；它们已经是当前设计与代码讨论的一部分，但不改变本页描述的最小 canonical 组件链。

---

## 2.2 组件职责

### JediGateway

职责：

- 接收高层 request
- 规范化为 `JediExperimentSpec`
- 选择 application family
- 选择 execution mode
- 调度后续组件

不负责：

- 直接构造命令行细节
- 解析 diagnostics
- 直接判定 scientific success

### JediEnvironmentProbe

职责：

- 检查 binary 是否存在
- 检查 launcher 是否可用
- 检查 shared libraries 是否可解析
- 检查 YAML / testinput / data path 是否存在
- 返回结构化环境报告

不负责：

- 自动修复环境
- 隐式下载数据
- 编译 YAML

### JediConfigCompiler

职责：

- 把 typed spec 编译成受控 YAML
- 按 family 生成不同顶层块
- 产出稳定、可预测的输出结构

不负责：

- 接收任意 YAML 透传
- 运行外部进程
- 根据 stderr 反推配置逻辑

### JediInputPreprocessor

职责：

- 在 run dir materialize `config.yaml`
- 校验 `required_runtime_paths`
- 记录 `prepared_inputs`

不负责：

- 自动下载数据
- 修复环境缺失
- 解释 scientific result

### JediExecutor

职责：

- 构造 `schema` / `validate_only` / `real_run` 命令
- 运行 executable
- 记录 stdout / stderr / return code / schema path / output evidence
- 归档 run artifact

不负责：

- 理解业务级 YAML 语义
- 解释 scientific result

### JediValidator

职责：

- 综合 environment report 与 run artifact
- 输出稳定的 `JediValidationReport`
- 区分 `environment_invalid` / `validated` / `executed` / `validation_failed` / `runtime_failed`

不负责：

- 再次编译 YAML
- 直接运行 executable

---

## 2.3 为什么 preprocessor 保持窄边界

这里的目标是控制组件职责，而不是把 runtime 基础面拆散：

- preprocessor 作为正式组件进入主链，但职责收敛在 materialization 与 required-path verification
- executor / validator 承接 `real_run` 与 runtime evidence 归档
- 更重的 diagnostics collector 与 IODA/HDF5/ODB 组级 interpretation 属于可叠加能力，而不是 preprocessor 的职责

因此本页强调的是稳定骨架：`spec -> env -> YAML -> preprocess -> mode-aware execution -> evidence-first validation`。

---

## 2.4 架构边界

设计时应持续检查以下边界没有被破坏：

- gateway 不承担 compiler/executor 细节
- compiler 不退化为 YAML passthrough
- executor 不理解 family-specific YAML 结构
- validator 不回头补做环境探测或配置编译
- study/mutation 不绕过 typed spec 直接改最终 YAML

这些边界一旦混掉，后续扩展到 `hofx`、`variational`、`local_ensemble_da` 会迅速失控。