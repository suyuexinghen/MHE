# 01. 概述与定位

## 1.1 Octave 是什么

GNU Octave 是一门面向数值计算的高级解释型语言，语法与 MATLAB 高度兼容，覆盖线性代数、ODE/PDE 求解、信号处理、统计分析、优化、绘图等科学计算核心场景。它的稳定运行入口是 `octave-cli`，通过 `.m` 脚本或函数文件驱动计算，产出数值结果、`.mat` 数据文件和图形输出。

## 1.2 MHE 扩展的目标

`metaharness_ext.octave` 的目标，是把 GNU Octave 作为一种**受控、可声明、可验证、可审计**的科学计算执行 worker 接入 MHE。核心价值：

1. 复用 Octave/MATLAB-like 脚本生态，降低已有科研脚本迁移成本
2. 将脚本、函数、输入数据、package 依赖、数值输出和图像产物显式建模为 typed contracts
3. 用 MHE 的 component graph、session、provenance、policy、evidence 和 promotion 语义治理科学计算任务
4. 用可测试、可复现、可回滚的方式替代"手动打开 Octave/MATLAB 跑脚本并人工检查结果"的非结构化流程
5. 为后续 AI-native 科学计算平台中的 Live Workspace、Scientific Context Engine、多 Agent 编排与 HPC 集成保留稳定扩展面

Octave 的稳定运行模型：

```text
typed spec + input assets + package requirements
  -> generated wrapper .m + workspace layout
  -> octave-cli --no-gui --quiet --no-init-file
  -> logs + .mat / text / CSV / figures
  -> numeric validation + evidence bundle + policy handoff
```

## 1.3 v1/v2/v3 分层

`docs/.trash/plan/Octave-Ext.md` 提出了一个六层 AI-native 科学计算平台（用户交互层 → Live Workspace Engine → Scientific Context Engine → Agent 编排层 → 专业科学 Agent 层 → 块图仿真引擎）作为 MATLAB 替代方案。Octave MHE 扩展按三层递进：

| 层次 | 内容 | 覆盖范围 |
|------|------|----------|
| **v1 Octave worker** | 可控 Octave 执行、证据与验证 | 首版覆盖，保持 deterministic wrapper + typed validation |
| **v2 Scientific workflow substrate** | Scientific Context Adapter、sessionized study、execution lifecycle、governance/optimizer bridge | `07-v2-alignment.md` 详细设计 |
| **v3 Live Workspace / Multi-Agent / HPC platform** | 持久变量空间、多 Agent 协同、生产级集群调度、Notebook/UI | 后续平台能力 |

首版定位不是"MATLAB 替代平台"，而是：

> MHE-managed Octave scientific-computing worker, with a path toward v2 AI-native scientific workflows.

## 1.4 设计立场

- **CLI-first**：以 `octave-cli` 非交互执行为主，不做 GUI / IDE / Live Editor
- **wrapper-first**：由 compiler 生成受控 wrapper `.m`，避免透传任意命令/脚本
- **workspace-first**：所有输入、脚本、输出、日志、证据都落在明确的受控工作目录
- **evidence-first**：return code 只是必要条件，不是成功的充分条件
- **numeric-validation-first**：输出变量、shape、dtype、容差、NaN/Inf、warning 都进入验证
- **package-aware**：Octave package 是环境事实，不假设所有 MATLAB toolbox 等价能力存在
- **promotion-readable**：validator 产出 MHE 可消费的 `ValidationIssue`、`blocks_promotion`、`ScoredEvidence`
- **no MATLAB parity claim**：不承诺 Simulink、App Designer、commercial toolbox 或完整 MATLAB 兼容性

## 1.5 首版 application family

| Family | 说明 |
|--------|------|
| `script_run` | 运行受控 `.m` 脚本或由 spec 生成的 wrapper；图形输出通过 `OctaveOutputSpec(kind="figure")` 支持 |
| `function_eval` | 调用指定函数并保存结构化返回值 |
| `numeric_benchmark` | 运行小型数值 benchmark，输出指标与容差判断 |

package 探测通过 `OctaveEnvironmentProbe.probe()` 组件方法提供，不作为独立 task family。

## 1.6 首版明确不支持

- 任意 shell command execution
- GUI Octave、交互式 REPL、notebook kernel 常驻会话
- MATLAB proprietary toolbox、Simulink、App Designer、Live Editor
- 对所有 Octave packages 的 blanket support
- 自动把任意历史 MATLAB 工程转换为 Octave 工程
- 在 extension 内部重建 MHE session / audit / graph promotion 系统
- 未经白名单的网络访问、文件系统越界访问或动态 package 安装

## 1.7 平台与扩展职责划分

### MHE 平台层负责

- manifest discovery / component boot
- graph candidate staging / semantic validation
- graph version commit / rollback
- session event、audit log、artifact snapshot、provenance graph
- protected-component enforcement
- policy-gated promotion authority
- runtime recovery、execution lifecycle service、resource quota
- BrainProvider / optimizer / mutation proposal 的平台级入口

### Octave 扩展层负责

- Octave task / workspace / script / function / package / output 的 typed spec
- Octave environment probe 与 package discovery
- wrapper `.m` 生成、input asset staging、output schema 编译
- `octave-cli` 执行、timeout、stdout/stderr capture
- `.mat` / JSON / CSV / figure / log artifact discovery
- numeric tolerance、expected variables、warning policy、evidence completeness validation
- domain-local policy hints 和 governance-shaped evidence bundle
- 后续 study / mutation 对 typed whitelist fields 的受控扫描

核心原则：**MHE = platform promotion / session / policy / provenance authority；Octave extension = Octave workflow、workspace、numeric evidence 与 validation contributor。**
