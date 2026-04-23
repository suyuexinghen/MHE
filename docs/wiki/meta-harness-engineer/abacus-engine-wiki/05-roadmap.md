# 05. ABACUS 路线图

## 5.1 推荐执行顺序

建议执行顺序如下：

```text
Phase 0: Environment Probe + SCF Minimal Baseline
  -> Phase 1: NSCF / Relax Baseline
    -> Phase 2: MD Baseline
      -> Phase 3: ABACUS+DeePMD Mode
        -> Phase 4: Examples / Study / Governance Hardening
```

关键点：

- 先建立环境与输入边界
- 先打通最小 SCF 执行闭环
- 再进入结构优化与 MD 这类更重的 family
- 最后才把 ABACUS+DeePMD mode 纳入统一 validator 语义

通用验收标准：每个 Phase 完成后，相关测试与文档必须保持零回归。

---

## 5.2 Phase 0：Environment Probe + SCF Minimal Baseline

### 5.2.1 目标

先交付一个“可以检查 ABACUS 环境、生成 `INPUT/STRU/KPT`、完成最小 SCF 运行并返回结构化结果”的最小可用链路。

### 5.2.2 任务

1. 新增 `MHE/src/metaharness_ext/abacus/` 包骨架与 manifests
2. 新增最小 `gateway.py`
3. 在 `contracts.py` 中引入 ABACUS family-aware contracts
4. 新增 `environment.py`，实现 `abacus --version` / `--info` / `--check-input` probe
5. 新增 `input_compiler.py`，把 typed spec 编译成稳定 `INPUT/STRU/KPT`
6. 新增 `executor.py`，支持 direct 或 launcher 驱动的 SCF 运行
7. 新增 `validator.py`，区分 environment/input/runtime/validation failure
8. 新增 ABACUS 定向测试

### 5.2.3 交付物

- `metaharness_ext.abacus` 最小包骨架
- ABACUS typed contracts
- environment probe
- 输入文件 compiler
- SCF baseline executor
- 结构化 validator 与单测

### 5.2.4 验收标准

- 能从 typed spec 生成稳定 `INPUT/STRU/KPT`
- 能明确报告 `abacus` / launcher / required path 缺失
- 能识别 `OUT.<suffix>/` 并收集关键日志/输入快照
- 能区分环境错误、输入错误与运行错误
- 不需要真实大规模计算也能完成首批测试

---

## 5.3 Phase 1：NSCF / Relax Baseline

### 5.3.1 目标

把 Phase 0 从“能跑最小 SCF”推进到“支持最常见的后续电子结构与结构优化路径”。

### 5.3.2 任务

1. 增加 `AbacusNscfSpec` 与 `AbacusRelaxSpec`
2. 在 compiler 中加入 NSCF / relax family 的最小字段与约束
3. 扩展 artifact 发现逻辑
4. 在 validator 中加入 final structure / family-aware success 规则
5. 新增相关测试

### 5.3.3 验收标准

- `nscf` 与 `relax` 进入同一套 gateway/compiler/executor/validator 体系
- `relax` 能识别最终结构证据
- validator 不再只看 return code

---

## 5.4 Phase 2：MD Baseline

### 5.4.1 目标

把 ABACUS extension 从静态/准静态计算扩展到受控 MD 路径。

### 5.4.2 任务

1. 定义 `AbacusMdSpec`
2. 在 compiler 中支持 MD 关键参数
3. 收集 `MD_dump`、`Restart_md.dat`、`STRU_MD_*` 等 artifact
4. 在 validator 中加入 MD-specific success 规则
5. 新增 MD baseline 测试

### 5.4.3 验收标准

- MD 进入同一套 typed workflow
- restart / dump artifact 可被稳定收集
- family-specific validator 语义清晰

---

## 5.5 Phase 3：ABACUS+DeePMD Mode

### 5.5.1 目标

把 `calculation=md + esolver_type=dp + pot_file` 的 ABACUS+DeePMD 路径纳入同一套 ABACUS extension。

### 5.5.2 任务

1. 在 `AbacusMdSpec` 中加入 DPMD-specific typed fields
2. environment probe 检查 DeePMD support
3. compiler 显式渲染 `pot_file`
4. validator 为 `md + dp` 组合增加前提与输出规则
5. 新增 DPMD mode 测试

### 5.5.3 验收标准

- DPMD-in-ABACUS 被建模为 ABACUS mode，而不是第二套扩展
- 缺少 DeePMD support 时失败语义清晰
- `pot_file` 与 family-specific 约束进入 typed boundary

---

## 5.6 Phase 4：Examples / Study / Governance Hardening

### 5.6.1 目标

把系统从“有设计、有最小 baseline”推进到“可演示、可研究、可治理”。

### 5.6.2 任务

1. 新增 `examples/manifests/abacus/`
2. 新增 `examples/graphs/abacus-minimal.xml`
3. 增加更真实的 artifact / diagnostics 测试
4. 评估 future study / mutation axis
5. 明确 launcher / HPC / feature gate 的 policy 边界

### 5.6.3 验收标准

- 有最小可演示 graph 和 example manifests
- artifact 与 validator 行为有稳定 regression tests
- 后续治理与 study 扩展有明确入口

---

## 5.7 测试路线图

### 单元测试优先级

1. manifest tests
2. compiler tests
3. executor command / workspace tests
4. validator tests
5. minimal demo test

### 首版重点测试文件

- `MHE/tests/test_metaharness_abacus_manifest.py`
- `MHE/tests/test_metaharness_abacus_executor.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`

---

## 5.8 首版 acceptance bar

本路线的首轮完成标准：

- ABACUS extension 的 docs 边界清晰
- 首版 family 与 mode 定义一致
- environment / compiler / executor / validator 职责不混淆
- artifact 与 evidence 面以 `OUT.<suffix>/` 为中心
- ABACUS+DeePMD 被清楚定义为 ABACUS mode，而不是另一套扩展实现
