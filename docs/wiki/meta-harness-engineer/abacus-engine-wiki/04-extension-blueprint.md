# 04. ABACUS 扩展蓝图

> 状态注记（2026-04）：Phase 3（`md + esolver_type=dp` typed baseline）已落地；当前已交付的 Phase 4 主要覆盖 example manifests、`abacus-minimal.xml` 与回归/治理加固，study 仍保留为后续扩展面。

## 4.1 目标

`metaharness_ext.abacus` 的目标，不是重写 ABACUS，也不是把它包装成黑盒命令执行器，而是把 ABACUS 的稳定控制面以 **受控、可声明、可验证、可审计** 的方式接入 MHE。

首版应围绕 ABACUS 已稳定存在的运行模型展开：

```text
INPUT / STRU / KPT + assets + launcher + executable
  -> OUT.<suffix>/ + logs + structures + restart artifacts + structured validation
```

因此扩展层的核心职责是：

1. 用 typed contracts 表达可控的 ABACUS 运行 spec
2. 将 spec 编译成稳定输入文件，而不是透传任意文本配置
3. 以受约束的 workspace / launcher 运行 ABACUS
4. 收集 artifacts、diagnostics 与 mode-aware evidence
5. 生成工程结果与科学证据导向的 validator/report
6. 为后续 study / mutation / policy gate 预留稳定边界
7. 作为 strengthened MHE 的宿主内扩展，对齐统一 promotion authority、manifest policy、protected governance boundary 与 runtime evidence flow

---

## 4.2 设计立场：选择 ABACUS 的哪一层作为 MHE 接口

结合文档事实，可将 ABACUS 的可接入层划分为：

- Level 1：体系、结构与数值物理问题定义
- Level 2：固定文件名输入层（`INPUT` / `STRU` / `KPT`）
- Level 3：launcher + `abacus` 执行层
- Level 4：`OUT.<suffix>/` 与 family-specific 产物层

首版明确选择：

- **Level 2 为主要控制面**
- **Level 3 为执行面**
- **Level 4 为 validator/evidence 面**
- **不进入 Level 1 的全自由参数空间**

---

## 4.3 组件链

首版建议的组件链如下：

除执行闭环外，blueprint 还应明确一个治理集成前提：ABACUS 不是独立 pipeline，而是运行在 strengthened MHE 宿主中的 extension。它的 gateway / environment / executor / validator 必须把结果汇入统一的 promotion、policy 与 evidence authority，而不是自行形成另一套 graph governance。

```text
AbacusGateway
  -> AbacusEnvironmentProbe
    -> AbacusInputCompiler
      -> AbacusExecutor
        -> AbacusValidator
```

### `AbacusGateway`

职责：

- 接收高层 request
- 规范化 `AbacusRunSpec` / family-aware specs
- 选择 family 与 execution variant
- 约束首版支持边界

### `AbacusEnvironmentProbe`

职责：

- 检查 `abacus`、launcher 与相关 runtime path
- 读取 `--version` / `--info` / `--check-input`
- 判断 DeePMD support、GPU support 等 build-time 特性
- 返回结构化 `AbacusEnvironmentReport`

### `AbacusInputCompiler`

职责：

- 将 typed spec 编译为稳定 `INPUT`
- 生成 `STRU`
- 需要时生成 `KPT`
- 决定 `suffix` 与输出目录约定
- 产出 `AbacusRunPlan`

### `AbacusExecutor`

职责：

- 准备工作目录
- 落盘输入文件和必要资产引用
- 运行 launcher + `abacus`
- 收集 stdout/stderr/return code
- 发现 `OUT.<suffix>/` 和关键输出文件
- 声明并遵守 manifest policy 中的 launcher capability、binary boundary 与 sandbox tier，不把运行扩权隐藏在 executor 实现细节里

### `AbacusValidator`

职责：

- 区分 environment / input / runtime / validation failure
- 将 artifacts 统一映射到稳定判定
- 按 family 给出最小成功规则
- 给出可审计 `evidence_files`
- 并行输出 canonical `evidence_refs`
- 输出 `issues`、`blocks_promotion`、`governance_state` 与 `ScoredEvidence`
- 作为 protected governance component 参与 promotion blocker 判断，而不是普通 helper
- 将 validator 结果与 policy review / promotion authority 协作起来，支持 allow / defer / reject 风格的后续治理决策

---

## 4.4 包结构

当前仓库中已落地的骨架如下（最初设计中的 `slots.py` 未纳入当前交付范围）：

```text
MHE/src/metaharness_ext/abacus/
├── __init__.py
├── capabilities.py
├── slots.py
├── contracts.py
├── gateway.py
├── environment.py
├── input_compiler.py
├── executor.py
├── validator.py
├── manifest.json
├── environment.json
├── input_compiler.json
├── executor.json
└── validator.json
```

当前已配套：

```text
MHE/examples/manifests/abacus/
MHE/examples/graphs/abacus-minimal.xml
MHE/tests/test_metaharness_abacus_manifest.py
MHE/tests/test_metaharness_abacus_executor.py
MHE/tests/test_metaharness_abacus_minimal_demo.py
```

---

## 4.5 family 与 mode 设计

首版建议的 application family：

- `scf`
- `nscf`
- `relax`
- `md`

推荐关键 mode 维度：

- `basis_type`: `pw` / `lcao`
- `launcher`: `direct` / `mpirun` / `mpiexec` / `srun`
- `esolver_type`: `ksdft` / `dp`

边界原则：

- family 是上层 workflow 语义
- `basis_type` / `esolver_type` 是运行配置维度
- 不把所有 ABACUS 参数扁平化成同一层 free-form key/value

---

## 4.6 DPMD-in-ABACUS 设计边界

ABACUS+DeePMD 不是第二个扩展，而是 ABACUS 的一个受控运行变体：

```text
application_family = md
esolver_type = dp
pot_file = model.pb
```

因此它应由 `metaharness_ext.abacus` 承担，并受以下规则约束。该 typed baseline 已在当前实现中落地，且对 DeePMD support 采用保守策略：若 `abacus --info` 无法明确确认支持，则按环境前提不足阻断执行。


- environment probe 要确认 ABACUS 构建具备 DeePMD support
- compiler 要显式渲染 `pot_file`
- validator 要对 `md + dp` 组合进行额外前置条件和输出检查
- 不在首版中承担 DeePMD native training pipeline

---

## 4.7 产物与 evidence 设计

推荐按以下类别组织 artifact：

- `input_files`
- `stdout_path`
- `stderr_path`
- `output_root`
- `log_files`
- `structure_files`
- `restart_files`
- `diagnostic_files`

关键证据面：

- rendered `INPUT` / `STRU` / `KPT`
- `OUT.<suffix>/INPUT`
- 运行日志
- SCF / relax / MD 对应产物
- MD restart / trajectory 文件

这能让 validator 和后续 evidence manager 不必重新扫描整个目录树。

### runtime evidence integration

ABACUS artifact/evidence 的设计，不应只服务于 extension-local report。更合理的接口形状是：关键 artifact 路径、environment prerequisite 结果、validation outcome 与补充 diagnostics，能够被映射到 session event、audit record、provenance ref 与 candidate/graph version evidence anchor。当前不要求 ABACUS 自己实现这些 runtime 设施，但 blueprint 必须保证本地 evidence 结构可被它们稳定消费。

---

## 4.8 failure taxonomy

首版建议采用如下 failure taxonomy：

- `environment_invalid`
- `input_invalid`
- `runtime_failed`
- `validation_failed`
- `executed`

解释：

- **environment_invalid**：缺 binary / launcher / feature / required path；其中 prerequisite missing 应能形成治理证据
- **input_invalid**：compiler 生成前或 `--check-input` 暴露的输入前提问题
- **runtime_failed**：return code 非零、timeout、launcher 崩溃
- **validation_failed**：返回码为零但没有足够 artifact/evidence；其中关键缺口可升级为 promotion blocker
- **executed**：满足 family 最小成功标准，但不自动等于已经通过统一治理门
- **protected_boundary_violation**：试图绕过 protected validator / policy / governed path 的违规情况

---

## 4.9 首版明确不做的内容

- 任意自由文本 `INPUT` 透传
- 所有 ABACUS feature 的全量 typed 覆盖
- 完整 HPC 作业编排平台
- 任意外部后处理链自动集成
- 将 DeepMD native workflow 合并进 ABACUS extension

首版的成功标准是：

- 建立 ABACUS 在 MHE 中的正确边界
- 打通一条真实、最小、可验证的执行链
- 给后续 family 扩展、artifact 强化和 DPMD mode 留出稳定接口

当前同样不要求 ABACUS 自己实现 hot-swap / recovery 机制，但要求 environment / executor / validator 的语义能被 runtime 的 hot-swap governance、checkpoint 与 audit/provenance path 正确消费，而不会在扩展层形成冲突或信息丢失。
