# 02. 架构总览

## 2.1 组件链

本文档定义组件职责边界；具体 contract、execution mode 与 failure taxonomy 分别以 [03-contracts 设计](03-contracts.md)、[04-执行链设计](04-execution-pipeline.md)、[05-环境与验证](05-environment-and-validation.md) 为准。

`metaharness_ext.jedi` 的推荐组件链如下：

```text
JediGateway
  -> JediEnvironmentProbe
    -> JediConfigCompiler
      -> JediExecutor
        -> JediValidator
```

Phase 1 之后再扩展为：

```text
JediGateway
  -> JediEnvironmentProbe
    -> JediConfigCompiler
      -> JediInputPreprocessor
        -> JediExecutor
          -> JediDiagnosticsCollector
            -> JediValidator
```

首版故意不把所有能力一次放全，而是先把 **可验证、可报告、可复用** 的最小主链打稳。

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

### JediExecutor

职责：

- 构造 `schema` / `validate_only` / `real_run` 命令
- 运行 executable
- 记录 stdout / stderr / return code / schema path
- 归档 run artifact

不负责：

- 理解业务级 YAML 语义
- 解释 scientific result

### JediValidator

职责：

- 综合 environment report 与 run artifact
- 输出稳定的 `JediValidationReport`
- 区分 environment failure / validation failure / runtime failure

不负责：

- 再次编译 YAML
- 直接运行 executable

---

## 2.3 为什么首版没有 preprocessor 和 diagnostics collector

这不是遗漏，而是分阶段控制复杂度：

- preprocessor 会引入运行目录、文件复制/软链、testinput/data materialization 的额外状态
- diagnostics collector 会引入 IODA/HDF5/ODB 证据提取与组级解析

Phase 0 的目标是先建立稳定的执行前验证闭环；只有当 `spec -> env -> YAML -> validate-only -> report` 已经稳定，才值得进入更重的 runtime 层。

---

## 2.4 架构边界

设计时应持续检查以下边界没有被破坏：

- gateway 不承担 compiler/executor 细节
- compiler 不退化为 YAML passthrough
- executor 不理解 family-specific YAML 结构
- validator 不回头补做环境探测或配置编译
- study/mutation 不绕过 typed spec 直接改最终 YAML

这些边界一旦混掉，后续扩展到 `hofx`、`variational`、`local_ensemble_da` 会迅速失控。