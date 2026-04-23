# 05. ABACUS Roadmap

> 状态：proposed | 面向 `metaharness_ext.abacus` 的正式执行路线图

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

- 先解决 environment 与输入边界
- 先用 SCF 打通最小闭环
- 再进入 relax / MD 等更复杂 family
- 最后再把 DPMD-in-ABACUS 纳入统一执行与验证语义

通用验收标准：每个 Phase 完成后，相关测试与 lint 必须保持零回归。

---

## 5.2 Phase 0：Environment Probe + SCF Minimal Baseline

### 5.2.1 目标

交付一个“可以检查 ABACUS 环境、生成 `INPUT/STRU/KPT`、完成最小 SCF 运行并返回结构化结果”的最小可用链路。

### 5.2.2 任务

1. 新增 `metaharness_ext.abacus` 包骨架与 manifests
2. 新增最小 `gateway.py`
3. 在 `contracts.py` 中引入 ABACUS family-aware contracts
4. 新增 `environment.py`，实现 `--version` / `--info` / `--check-input` probe
5. 新增 `input_compiler.py`
6. 新增 `executor.py`，支持 direct 与最小 launcher 运行
7. 新增 `validator.py`
8. 新增 ABACUS 定向测试

### 5.2.3 验收标准

- 能从 typed spec 生成稳定 `INPUT/STRU/KPT`
- 能明确报告 binary / launcher / required path 缺失
- 能发现 `OUT.<suffix>/` 与关键输入快照
- 能区分 environment / input / runtime / validation failure

---

## 5.3 Phase 1：NSCF / Relax Baseline

### 5.3.1 目标

把最小 SCF 基线扩展到更常见的后续电子结构与结构优化路径。

### 5.3.2 任务

1. 新增 `AbacusNscfSpec` 与 `AbacusRelaxSpec`
2. 扩展 compiler 与 family-aware 约束
3. 扩展 artifact 发现逻辑
4. 在 validator 中加入 final structure 规则
5. 新增相关测试

### 5.3.3 验收标准

- `nscf` / `relax` 进入同一套 typed workflow
- `relax` 成功不只看 return code
- final structure evidence 可被稳定消费

---

## 5.4 Phase 2：MD Baseline

### 5.4.1 目标

把 ABACUS extension 扩展到受控 MD 路径。

### 5.4.2 任务

1. 定义 `AbacusMdSpec`
2. 支持 MD 关键参数的受控 compiler
3. 收集 `MD_dump`、`Restart_md.dat`、`STRU_MD_*`
4. 加入 restart-aware validator 语义
5. 新增 MD baseline 测试

### 5.4.3 验收标准

- MD 成为首版正式支持 family
- restart / dump artifact 可被结构化收集
- validator 能给出稳定最小成功判定

---

## 5.5 Phase 3：ABACUS+DeePMD Mode

### 5.5.1 目标

把 `calculation=md + esolver_type=dp + pot_file` 的模式纳入同一套 ABACUS extension。

### 5.5.2 任务

1. 在 `AbacusMdSpec` 中引入 DPMD-specific typed fields
2. environment probe 中识别 DeePMD support
3. compiler 中显式渲染 `pot_file`
4. validator 中增加 DPMD mode 的前提与成功规则
5. 新增该模式测试

### 5.5.3 验收标准

- DPMD-in-ABACUS 明确属于 ABACUS mode
- 缺少 DeePMD support 时失败语义清晰
- `pot_file` 与 mode-specific 约束进入 typed boundary

---

## 5.6 Phase 4：Examples / Study / Governance Hardening

### 5.6.1 目标

把系统从“设计与最小 baseline 可行”推进到“可演示、可扩展、可治理”。

### 5.6.2 任务

1. 新增 example manifests 与 graph
2. 增加更真实的 artifact / diagnostics 测试
3. 评估 future study / mutation axes
4. 明确 launcher/HPC/policy gate 边界
5. 如需要，新增 implementation plan 文档

### 5.6.3 验收标准

- 有最小可演示 graph 与 example manifests
- regression tests 覆盖主要 artifact / validator 分支
- 后续治理与 study 扩展有清晰入口

---

## 5.7 测试路线图

### 首批测试建议

- `MHE/tests/test_metaharness_abacus_manifest.py`
- `MHE/tests/test_metaharness_abacus_executor.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`

### 测试重点

- manifest / component declaration 一致性
- compiler 输出文件稳定性
- executor command / workspace 语义
- validator failure taxonomy
- family-aware artifact discovery

---

## 5.8 完成标准

本路线的首轮完成标准：

- ABACUS docs 边界清晰
- future package skeleton 明确
- family/mode 命名在 wiki 和 blueprint 中一致
- artifact/evidence 语义以 `OUT.<suffix>/` 为中心
- ABACUS+DeePMD 被清晰建模为 ABACUS mode
