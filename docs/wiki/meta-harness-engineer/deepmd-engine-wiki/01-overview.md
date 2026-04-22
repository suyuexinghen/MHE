# 01. 概述与定位

## 1.1 DeepMD 解决什么问题

DeepModeling 生态的核心目标，是在量子力学精度与经典分子动力学效率之间建立可工程化的折中：

1. **DeePMD-kit**：从 DFT / AIMD 数据训练 Deep Potential 模型
2. **DP-GEN**：通过 concurrent learning 自动扩充数据集并提升模型质量
3. **DP Library / transfer learning / simplify**：复用已有数据、模型和 relabeling 流程，降低新项目成本

从工程角度看，DeepMD 并不是一个“单步训练器”，而是一个跨越数据准备、训练、冻结、压缩、测试、部署、自动迭代和性质验证的长链工作流。

---

## 1.2 首版接口选择：接哪一层

DeepModeling 生态可粗分为四层：

- **Level 1：物理与数据源层**
  - AIMD / DFT / VASP / QE / ABACUS / Gaussian 等
- **Level 2：模型训练层**
  - DeePMD-kit 的 descriptor、fitting net、loss、optimizer、checkpoint
- **Level 3：并发学习与自动化层**
  - DP-GEN 的 `init` / `run` / `simplify` / `autotest`
- **Level 4：外部封装与工作流层**
  - `input.json` / `param.json` / `machine.json`、目录工作区、命令行执行、结果分析

对 MHE 来说，**首版明确选择 Level 4 为主、Level 3 为辅、Level 2 只做受控参数化，不直接进入训练框架内部 API**：

- **Level 4**：MHE 负责 gateway、compiler、executor、collector、validator、evidence
- **Level 3**：MHE 负责编译受控的 DP-GEN specs 与迭代语义
- **Level 2**：MHE 仅通过 typed training spec 生成 DeePMD 输入，不直接接管模型内部训练图
- **不进入 Level 1**：首版不接管新的 first-principles 代码开发，也不实现数据转换器全家桶

---

## 1.3 为什么 DeepMD 适合接入 MHE

### 1.3.1 控制面天然是声明式的

DeePMD-kit 与 DP-GEN 的关键控制面是 JSON：

- DeePMD-kit：`input.json`
- DP-GEN：`param.json`、`machine.json`

这意味着系统入口不是交互式 API，而是**稳定配置 + 稳定目录结构 + 稳定命令语义**。

### 1.3.2 执行过程天然是 staged lifecycle

DeePMD-kit 教程给出的最小链路是：

```text
data prep -> train -> freeze -> compress -> test -> apply
```

DP-GEN 的主链路则是：

```text
init -> run(00.train -> 01.model_devi -> 02.fp) -> autotest
```

这与 MHE 的 staged runtime 高度同构：

- `declare_interface()`：声明 typed spec 与产物边界
- `VALIDATED_STATIC`：校验 JSON 字段与路径依赖
- `ASSEMBLED`：编译出运行目录和命令计划
- `VALIDATED_DYNAMIC`：校验环境、命令、依赖和输入数据
- `ACTIVATED`：执行训练 / model deviation / fp / autotest
- `COMMITTED`：产物、诊断、验证报告与证据落盘

### 1.3.3 证据面天然丰富

DeepMD 不是只给一个 return code。首版就能稳定提取：

- `lcurve.out` 中的训练/验证误差轨迹
- `model.ckpt*`、`checkpoint`、`graph.pb`、`graph-compress.pb`
- `dp test` 的 energy / force / virial RMSE
- `model_devi.out` 的 `max_devi_f / avg_devi_f`
- `candidate.shuffled.*.out`、`rest_accurate.*.out`、`rest_failed.*.out`
- `record.dpgen` 的阶段推进与恢复点
- autotest 的 `result.out` / `result.json`

这非常适合 MHE 的 evidence-first 设计。

---

## 1.4 关键现实约束

### 1.4.1 DeepMD 是多工具链组合，不是单一 binary

首版至少要面对：

- `dp`
- `dpgen`
- `dpdata`
- `lmp` / `mpirun`
- 外部 first-principles 程序（如 `vasp_std`）

因此 `environment probe` 不能只检查一个 binary 是否存在，而要检查**整条工作流的外部依赖闭包**。

### 1.4.2 首版不应假定所有训练、标签和 HPC 环境都已齐备

实际场景里最容易失败的不是 JSON 语法，而是：

- 数据路径缺失
- `type_map` / `POTCAR` / `POSCAR` 不一致
- `machine.json` 所描述环境不可用
- 远程 scheduler / SSH / queue 配置失效
- `dpgen` 可运行但 `fp` 所需代码或环境缺失

因此 `metaharness_ext.deepmd` 首版必须把这些失败显式建模为 environment/input failure，而不是混成“训练失败”。

### 1.4.3 科学目标边界不能缺席

DeepMD 教程和实践指南都强调：

- 本质目标是覆盖**问题相关的局部构型空间**
- 不应默认追求“通用鲁棒大一统模型”
- trust level / sampling 温压 / 边界定义是首要设计变量

因此首版 validator 不能只检查“训练跑完了”，还要能表达：

- 当前 coverage 是否足以支持目标问题
- model deviation 选点策略是否在合理区间
- 是否已经收敛到“该阶段足够好”的里程碑

---

## 1.5 首版支持边界

### 首版正式支持

1. **DeePMD-kit 基础训练链**
   - data preparation manifest
   - train / freeze / compress / test
2. **DP-GEN run 主链**
   - `00.train`
   - `01.model_devi`
   - `02.fp`
3. **DP-GEN simplify 基础链**
   - transfer-learning / relabeling 风格迭代
4. **DP-GEN autotest 基础链**
   - `make` / `run` / `post`
   - 典型性质报告归档

### 首版明确不支持

- 训练框架底层图结构级别的任意修改
- 任意外部 first-principles 程序的自动适配
- 无约束 JSON 透传与自由 patch
- 生产级大规模 scheduler 编排与集群自治
- 直接把 DP-GEN 当成“随便跑 shell 脚本”的通用 orchestrator
- DP Library 在线同步与外部服务写入

---

## 1.6 统一术语基线

| 术语 | 含义 |
|---|---|
| **DeepMD training** | 由 `dp train input.json` 启动的 DeePMD 模型训练 |
| **Freeze** | 将 checkpoint 导出为 frozen graph（如 `graph.pb`） |
| **Compress** | 将 frozen model 压缩为更快、更省内存的模型 |
| **Model deviation** | 多模型对同一配置预测偏差，用于 candidate 选择 |
| **FP** | first-principles labeling 步骤，如 VASP 重新标注 |
| **Init data** | 初始训练集 |
| **Candidate** | deviation 位于 trust 区间、值得重新标注的配置 |
| **Accurate** | 当前模型已足够准确、无需重标的配置 |
| **Failed** | deviation 过高、可能非物理或严重超界的配置 |
| **Simplify** | 基于已有大数据集与预训练模型做 transfer-learning / relabeling 的迭代流程 |
| **Autotest** | 针对 EOS、elastic、vacancy、surface 等性质的自动性质验证流程 |

---

## 1.7 结论

`metaharness_ext.deepmd` 的最合理落地方式，不是把 DeepModeling 视为 Python API SDK，而是把它视作一个：

- **JSON-configured**
- **workspace-driven**
- **artifact-rich**
- **environment-sensitive**
- **evidence-producing**

的训练 / 并发学习 / 评测应用族。

因此首版的正式扩展路线应是：

- typed contracts
- environment probe
- controlled JSON compiler
- explicit workspace preprocessor
- mode-aware executor
- diagnostics collector
- science-aware validator
- evidence manager

这条路线既符合本地教程材料的工程事实，也符合 MHE 一贯的 contract-first、evidence-first 扩展模式。
