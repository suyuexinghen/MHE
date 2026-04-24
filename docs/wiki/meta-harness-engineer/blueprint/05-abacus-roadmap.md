# 05. ABACUS Roadmap

> 状态：merged current baseline | 以 `metaharness_ext.abacus` 当前实现与 `abacus-engine-wiki` 为准整理的执行路线图

## 5.1 推荐执行顺序

当前更可靠的路线基线不是旧的“pure proposed”状态，而是：Phase 0–Phase 4 的 family workflow 已经基本落地，接下来的工作重心转向治理面对齐与文档真值同步。

建议按以下顺序理解和执行：

```text
Phase 0: Environment Probe + SCF Minimal Baseline      [已完成]
  -> Phase 1: NSCF / Relax Baseline                    [已完成]
    -> Phase 2: MD Baseline                            [已完成]
      -> Phase 3: ABACUS+DeePMD Mode                   [已完成]
        -> Phase 4: Examples / Study / Governance Hardening [已完成首批交付，继续做治理面对齐]
          -> Current Hardening: Governance Alignment + Blueprint/Wiki Truthfulness
```

关键点：

- 先解决 environment 与输入边界
- 先用 SCF 打通最小闭环
- 再进入 relax / MD 等更复杂 family
- 再把 DPMD-in-ABACUS 纳入统一执行与验证语义
- 当前最后一段工作不再是“再造 pipeline”，而是让已实现能力与 strengthened MHE 的 governance / evidence 主路径对齐

通用验收标准：每个阶段完成后，相关测试、manifest、文档必须保持零回归，并且已实现能力不能继续被写成纯 future plan。

---

## 5.2 Phase 0：Environment Probe + SCF Minimal Baseline

### 5.2.1 状态

已完成。

### 5.2.2 已交付内容

1. `metaharness_ext.abacus` 包骨架与 manifests
2. 最小 `gateway.py`
3. family-aware contracts
4. `environment.py` 中的 `--version` / `--info` / `--check-input` probe
5. `input_compiler.py`
6. `executor.py` 的 direct / launcher 执行基础
7. `validator.py`
8. ABACUS 定向测试

### 5.2.3 保持的验收标准

- 能从 typed spec 生成稳定 `INPUT/STRU/KPT`
- 能明确报告 binary / launcher / required path 缺失
- 能发现 `OUT.<suffix>/` 与关键输入快照
- 能区分 environment / input / runtime / validation failure

---

## 5.3 Phase 1：NSCF / Relax Baseline

### 5.3.1 状态

已完成。

### 5.3.2 已交付内容

1. `AbacusNscfSpec` 与 `AbacusRelaxSpec`
2. compiler 与 family-aware 约束扩展
3. artifact 发现逻辑扩展
4. validator 中的 final structure 规则
5. 对应测试

### 5.3.3 保持的验收标准

- `nscf` / `relax` 进入同一套 typed workflow
- `relax` 成功不只看 return code
- final structure evidence 可被稳定消费

---

## 5.4 Phase 2：MD Baseline

### 5.4.1 状态

已完成。

### 5.4.2 已交付内容

1. `AbacusMdSpec`
2. 受控 MD compiler 路径
3. `MD_dump`、`Restart_md*`、`STRU_MD*` artifact 收集
4. restart-aware validator 语义
5. MD baseline 测试

### 5.4.3 保持的验收标准

- MD 成为正式支持 family
- restart / dump artifact 可被结构化收集
- validator 能给出稳定最小成功判定

---

## 5.5 Phase 3：ABACUS+DeePMD Mode

### 5.5.1 状态

已完成。

### 5.5.2 已交付内容

1. `AbacusMdSpec` 中的 `esolver_type=dp` + `pot_file` typed boundary
2. environment probe 中的 DeePMD support prerequisite 检查
3. compiler 中显式渲染 `pot_file`
4. validator 中对 `md + dp` prerequisite 的阻断语义
5. 相关测试

### 5.5.3 保持的验收标准

- DPMD-in-ABACUS 明确属于 ABACUS mode
- 缺少 DeePMD support 时失败语义清晰
- `pot_file` 与 mode-specific 约束进入 typed boundary
- support unknown 时按保守策略阻断

---

## 5.6 Phase 4：Examples / Study / Governance Hardening

### 5.6.1 状态

已完成首批交付，当前剩余工作聚焦于治理面对齐，而不是再创建基础示例或 family workflow。

### 5.6.2 已交付内容

1. example manifests
2. `examples/graphs/abacus-minimal.xml`
3. 更真实的 artifact / diagnostics 测试
4. Phase 2/3/4 文档同步
5. validator 作为 protected governance component 的当前定位

### 5.6.3 当前剩余硬化项

1. 保持 ABACUS manifests 中已显式声明的 `policy.credentials` / `policy.sandbox` 与测试、example manifests、文档叙述持续一致
2. 保持 validator 已落地的 governance-grade output（`issues`、`blocks_promotion`、`governance_state`、`ScoredEvidence`、canonical `evidence_refs`）与代码现实、测试叙述持续一致
3. 让 blueprint / roadmap / handoff-facing 文档与代码现实保持一致
4. 明确“promotion-ready validation semantics”不等于直接 graph promotion
5. 持续把 docs 描述统一到当前 lifecycle object model：control files、runtime assets、workspace layout、artifact groups、lifecycle state
6. 继续补强边界回归测试与语义收紧项，而不是回退去重做已完成的 family baseline

### 5.6.4 当前验收标准

- 有最小可演示 graph 与 example manifests
- regression tests 覆盖主要 artifact / validator 分支
- manifests、validator、evidence surface 与 strengthened MHE 的治理语义兼容
- 文档不再把现有能力写成纯 future plan

---

## 5.7 当前实现后的下一段工作：Governance Alignment

这一段是当前最真实的 roadmap，而不是新的 family phase。

### 5.7.1 目标

在不重写 ABACUS workflow 的前提下，把 ABACUS extension 的 contract / validator / manifest / evidence surface 对齐到 strengthened MHE 的治理与证据模型。

### 5.7.2 任务

1. 继续增加 governance-oriented regression tests，锁定当前已落地的 `issues` / `blocks_promotion` / `governance_state` / `ScoredEvidence` / canonical `evidence_refs`
2. 同步 `abacus-engine-wiki` 与 merged blueprint / roadmap / handoff
3. 保持 blueprint、roadmap、handoff 文档对 nested lifecycle object model 的表述一致
4. 明确 promotion-ready validation semantics 与 graph promotion authority 的边界
5. 收紧仍偏宽松的 evidence / prerequisite 语义，并补齐对应边界测试
6. 持续把 remaining work 表述限定在真实未完成项，避免把已落地能力写回 future plan

### 5.7.3 验收标准

- ABACUS validation 结果不仅能表达 pass/fail，还能表达 governance blocking semantics
- 执行成功与 promotion approval 的区别在文档与测试中都被明确表达
- manifests 的策略面是显式的，而不是只靠 `safety` 默认值推断
- evidence 结构可被 runtime session / audit / provenance 路径稳定消费

---

## 5.8 测试路线图

### 首批保持覆盖的测试

- `MHE/tests/test_metaharness_abacus_manifest.py`
- `MHE/tests/test_metaharness_abacus_executor.py`
- `MHE/tests/test_metaharness_abacus_gateway.py`
- `MHE/tests/test_metaharness_abacus_environment.py`
- `MHE/tests/test_metaharness_abacus_validator.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`

### 当前新增测试重点

- manifest `policy.credentials` / `policy.sandbox` 一致性
- validator `issues` / `blocks_promotion`
- successful run 的 `ScoredEvidence` 与 canonical `evidence_refs`
- prerequisite missing 与 runtime failure 的治理级区分
- promotion-ready validation does not equal graph promotion

---

## 5.9 完成标准

当前路线的完成标准应更新为：

- ABACUS docs 边界清晰
- blueprint / roadmap / handoff / current code 四者一致
- family/mode 命名在 wiki 和实现中一致
- artifact/evidence 语义以 `OUT.<suffix>/` 为中心
- ABACUS+DeePMD 被清晰建模为 ABACUS mode
- validator 已具备 promotion-ready validation semantics
- manifest policy 与 evidence surface 可被 strengthened MHE 的 runtime / policy / provenance 路径消费
- 已实现能力不再继续被写成纯规划

---

## 5.10 结论

这份 merged roadmap 的作用，不是重新发明 ABACUS 的 phase 顺序，而是把旧路线图重写成与当前代码现实一致的执行真值：

- workflow baseline 已基本完成
- 当前最关键的后续工作是 governance alignment
- 后续所有 wiki 和代码同步，应以这一点为准