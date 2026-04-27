# 09. 范围与分工

## 9.1 首版支持边界

### 首版 application family

| Family | 说明 |
|--------|------|
| `script_run` | 运行受控 `.m` 脚本或由 spec 生成的 wrapper；图形输出通过 `OctaveOutputSpec(kind="figure")` 支持 |
| `function_eval` | 调用指定函数并保存结构化返回值 |
| `numeric_benchmark` | 运行小型数值 benchmark，输出指标与容差判断 |

package 探测通过 `OctaveEnvironmentProbe.probe()` 组件方法提供，不作为独立 task family。

### 首版明确不支持

- 任意 shell command execution
- GUI Octave、交互式 REPL、notebook kernel 常驻会话
- MATLAB proprietary toolbox、Simulink、App Designer、Live Editor
- 对所有 Octave packages 的 blanket support
- 自动把任意历史 MATLAB 工程转换为 Octave 工程
- 在 extension 内部重建 MHE session / audit / graph promotion 系统
- 未经白名单的网络访问、文件系统越界访问或动态 package 安装

## 9.2 与原始 AI-native 平台愿景的关系

`docs/.trash/plan/Octave-Ext.md` 提出了六层 AI-native 科学计算平台。Octave MHE 扩展的覆盖策略：

| 原始六层愿景 | v1 状态 | v2 对齐 | v3/未来 |
|---|---|---|---|
| 用户交互层 | 不覆盖 | study report 可被上层 UI/CLI/Notebook 消费 | Notebook / Workspace UI |
| Live Workspace Engine | 不覆盖 | sessionized artifacts + checkpoint refs（不入 v2 交付） | 持久变量空间 service |
| Scientific Context Engine | 仅预留字段 | v2 核心：unit、uncertainty、method hints、constants、invariants | 完整领域知识库 |
| Agent 编排层 | 不覆盖 | BrainProvider + MutationProposal + study trials | 多 Agent planner / RAG |
| 专业科学 Agent 层 | 不覆盖 | context adapter + evidence 产出科学判断 | 专业 Agent 消费 substrate |
| 块图仿真引擎 | 不覆盖 | 不入 v2 | OpenModelica / FMU/FMI（独立 `metaharness_ext.modelica`） |
| 计算基础设施层 | octave-cli worker | ExecutionLifecycle + resource quota + scheduler adapter seam | SLURM/K8s 生产后端 |

## 9.3 与其他 MHE Extension 的关系

| Extension | 关系 | 说明 |
|-----------|------|------|
| DeepMD | 模式参考 | study component、governance adapter、evidence pipeline 模式 |
| JEDI | 模式参考 | contracts、execution pipeline、environment/validation 模式 |
| ABACUS | 模式参考 | validator protected component、governance_state 惯例 |
| QCompute | 模式参考 | study strategy（bayesian/agentic）、environment readiness gating |
| Nektar | 互补 | PDE 求解 vs 通用数值计算，不同应用领域 |
| AI4PDE | 互补 | AI4PDE 做 PDE 的 AI-native team runtime，Octave 做通用科学计算的受控 worker |

## 9.4 与 blueprint/ 的分工

| 文档 | 职责 |
|------|------|
| 本 wiki | 回答"这个扩展应如何被设计"——设计边界、组件职责、contract 语义 |
| `blueprint/07-octave-extension-blueprint.md` | 回答"正式设计主张是什么"——proposal 状态的设计蓝图 |
| `07-v2-alignment.md`（本 wiki） | 回答"如何从 v1 worker 升级为 v2 scientific workflow substrate" |

## 9.5 开放问题

以下问题在进入对应阶段前需通过独立设计文档解决：

1. **SCE 检查粒度**：量纲/误差传播检查应在 compiler 前（blocking）还是 validator 后（non-blocking 验证）？默认建议两者都有。

2. **Live Workspace 的 session 边界**：workspace snapshot 是否允许跨 session 引用？默认建议同 session 内自动允许，跨 session 需显式 governance 审批。此功能不入 v2 交付。

3. **BrainProvider 的 LLM 选型**：默认 Bayesian optimization（可离线运行，可复现），LLM 通过 `runtime.llm` 可选注入增强。

4. **HPC workspace 传输**：优先支持共享文件系统（Lustre/NFS），对象存储（S3/MinIO）作为后续增强。

5. **块图仿真引擎归属**：独立 `metaharness_ext.modelica` extension，通过 MHE graph 与 Octave extension 协作而非耦合。

6. **首版是否需要支持 `.mat` 解析**：v1 只要求 wrapper 产出 save -text / JSON 摘要；v2 通过 `OctaveMATFileParser`（scipy.io.loadmat）提供 `.mat` 结构化解析。

7. **Step 2 期间 Step 1 的兼容性**：所有 v2 contract 变化向后兼容——新字段全部可选（`None` 默认值），新 capability 全部 optional（缺失时优雅降级）。

## 9.6 不在本 wiki 展开的内容

- GNU Octave 软件本体的完整教程
- MATLAB 兼容性百科或迁移指南
- Octave package 生态的 exhaustive 列表
- 全量 HPC / scheduler 编排细节
- rollout phase 的日常推进说明
- 分阶段执行清单与 milestone 跟踪
