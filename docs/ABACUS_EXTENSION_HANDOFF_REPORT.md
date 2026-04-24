# ABACUS Extension Handoff Report

> 目的：给新的 Claude Code 对话窗口提供一份可直接接力开发的工作指导文档。
> 范围：`MHE/src/metaharness_ext/abacus/` 与对应测试 / wiki。
> 状态基线：Phase 0–4 的 family / mode baseline 已落地；当前真值重点是把 ABACUS 文档、manifest、validator 与 evidence surface 持续对齐到 lifecycle object model 与治理语义。

---

## 1. 当前任务背景

当前正在开发 `Meta-Harness Engine (MHE)` 的 `ABACUS` 扩展，目标是把 ABACUS 的 file-driven workflow 以受控、typed、可验证的形式接入 MHE 组件链：

- `gateway -> environment -> input_compiler -> executor -> validator`
- 控制面围绕 `INPUT / STRU / KPT + launcher + abacus`
- 证据面围绕 `OUT.<suffix>/`、日志、结构文件、输入快照
- 严格坚持 evidence-first validation，而不是 shell wrapper 风格的“能跑就算成功”

当前工作重点已经从设计/文档推进到了真实实现，并且已经打通：

- **Phase 0**：Environment Probe + SCF Minimal Baseline
- **Phase 1**：NSCF / Relax Baseline
- **Phase 2**：MD Baseline
- **Phase 3**：ABACUS+DeePMD Mode
- **Phase 4**：Examples / Study / Governance Hardening（已完成首批交付）

当前阶段不再是进入新的 family phase，而是继续做：

- **Current Hardening**：Governance Alignment + Blueprint/Wiki Truthfulness
- **Current Modeling Truth**：以 lifecycle object model 统一描述 control files、runtime assets、workspace layout、artifact groups、lifecycle state

---

## 2. 已完成进度

### 2.1 文档与设计侧

ABACUS wiki 与 handoff-adjacent 文档已建立并形成当前实施依据：

- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/README.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/01-overview.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/02-workflow-and-components.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/03-contracts-and-artifacts.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/08-runtime-lifecycle.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/09-core-objects-and-io-model.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-roadmap.md`
- `MHE/docs/ABACUS_EXTENSION_HANDOFF_REPORT.md`

### 2.2 代码实现侧

ABACUS extension 已存在完整包骨架：

- `MHE/src/metaharness_ext/abacus/__init__.py`
- `MHE/src/metaharness_ext/abacus/capabilities.py`
- `MHE/src/metaharness_ext/abacus/slots.py`
- `MHE/src/metaharness_ext/abacus/contracts.py`
- `MHE/src/metaharness_ext/abacus/gateway.py`
- `MHE/src/metaharness_ext/abacus/environment.py`
- `MHE/src/metaharness_ext/abacus/input_compiler.py`
- `MHE/src/metaharness_ext/abacus/executor.py`
- `MHE/src/metaharness_ext/abacus/validator.py`
- `MHE/src/metaharness_ext/abacus/manifest.json`
- `MHE/src/metaharness_ext/abacus/gateway.json`
- `MHE/src/metaharness_ext/abacus/environment.json`
- `MHE/src/metaharness_ext/abacus/input_compiler.json`
- `MHE/src/metaharness_ext/abacus/executor.json`
- `MHE/src/metaharness_ext/abacus/validator.json`

### 2.3 当前已支持能力

#### Phase 0 已完成

- `AbacusScfSpec`
- ABACUS binary / launcher / required path environment probe
- `INPUT / STRU / KPT` 渲染
- 结构化 executor
- SCF evidence-first validator
- manifest / executor / minimal demo tests

#### Phase 1 已完成

- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- gateway 可发出 `scf | nscf | relax` 三类任务
- compiler 已支持 `scf | nscf | relax` family dispatch
- environment 已支持 family-aware required path checks
- executor 已支持 richer artifact discovery
- validator 已支持 NSCF / relax family-specific evidence rules
- 新增 compiler / environment / validator / minimal demo tests

---

## 3. 当前实现要点

### 3.1 contracts

关键模型位于：

- `MHE/src/metaharness_ext/abacus/contracts.py`

当前已有的主要 typed boundary：

- `AbacusExecutableSpec`
- `AbacusStructureSpec`
- `AbacusKPointSpec`
- `AbacusScfSpec`
- `AbacusNscfSpec`
- `AbacusRelaxSpec`
- `AbacusMdSpec`（已支持 `md + ksdft` 与 `md + dp` 的受控组合）
- `AbacusEnvironmentReport`
- `AbacusRunPlan`
- `AbacusRunArtifact`
- `AbacusValidationReport`

这些边界当前更适合被理解为 nested lifecycle object model，而不是一组扁平字段列表：

- control-file objects：`INPUT` / `STRU` / `KPT`
- runtime-asset objects：pseudo、orbital、`pot_file`、restart / charge density 等前置资产
- workspace-layout objects：`working_directory`、prepared inputs、`OUT.<suffix>/`
- artifact-group objects：logs、diagnostics、structure / restart / family-specific outputs
- lifecycle-state objects：environment、run、validation 及对应 evidence handoff

关键离散维度：

- `application_family = scf | nscf | relax | md`
- `basis_type = pw | lcao`
- `launcher = direct | mpirun | mpiexec | srun`
- `esolver_type = ksdft | dp`

当前重要约束：

- `nscf` 需要 `charge_density_path` 或 `restart_file_path`
- `nscf` 强制要求 `kpoints`
- `relax` 使用 `relax_controls`
- `md + dp` 要求 `pot_file`，并在 DeePMD support 不明确时按保守策略阻断

### 3.2 gateway

文件：

- `MHE/src/metaharness_ext/abacus/gateway.py`
- `MHE/src/metaharness_ext/abacus/gateway.json`

当前行为：

- 输出类型为 `AbacusExperimentSpec`
- `issue_task()` 已支持：
  - `family="scf"`
  - `family="nscf"`
  - `family="relax"`
  - `family="md"`
- 可传入：
  - `charge_density_path`
  - `restart_file_path`
  - `relax_controls`
  - `pot_file`

### 3.3 environment

文件：

- `MHE/src/metaharness_ext/abacus/environment.py`

当前行为：

- 分离检查：
  - `abacus` binary 是否存在
  - launcher 是否存在
  - `--version`
  - `--info`
  - `--check-input`
- `required_paths_present` 已按 family / mode 做路径扩展：
  - NSCF：charge / restart prerequisite
  - relax：优先读取 typed `restart_file_path`，并兼容 legacy `relax_controls["restart_file_path"]`
  - `md + dp`：要求 `pot_file`
- `deeppmd_probe_supported` / `deeppmd_probe_succeeded` / `deeppmd_support_detected` 已进入环境报告
- `md + dp` 在 DeePMD support 为 `false` 或 `unknown` 时按前提不足处理

### 3.4 input compiler

文件：

- `MHE/src/metaharness_ext/abacus/input_compiler.py`

当前行为：

- 已从 SCF-only 升级为 family dispatcher：
  - `_compile_scf(...)`
  - `_compile_nscf(...)`
  - `_compile_relax(...)`
  - `_compile_md(...)`
- 已统一由 `_build_plan(...)` 生成：
  - `output_root`
  - `expected_outputs`
  - `expected_logs`
  - `required_runtime_paths`
  - `environment_prerequisites`
- `_render_input(...)` 已支持：
  - 基础字段
  - NSCF 的 `charge_density_path` / `restart_file_path`
  - relax 的 `relax_controls`
  - `pot_file`

### 3.5 executor

文件：

- `MHE/src/metaharness_ext/abacus/executor.py`

当前行为：

- 支持 direct 与 launcher 模式的结构化命令构造
- 写入 `INPUT` / `STRU` / `KPT`
- 记录 `stdout.log` / `stderr.log`
- 发现：
  - `output_root`
  - `output_files`
  - `diagnostic_files`
  - `structure_files`
- 通过 `result_summary` 保留 `esolver_type`、`pot_file`、environment prerequisite 等运行上下文
- 对 `OUT.<suffix>/`、MD artifacts 及 family-specific 证据有更强支持

### 3.6 validator

文件：

- `MHE/src/metaharness_ext/abacus/validator.py`

当前 failure taxonomy：

- `environment_invalid`
- `input_invalid`
- `runtime_failed`
- `validation_failed`
- `executed`

当前 evidence 规则：

- `scf`
  - 需要 `OUT.<suffix>/`
  - 需要 `running_scf.log`
- `nscf`
  - 需要 `OUT.<suffix>/`
  - 需要 `running_nscf.log`
- `relax`
  - 需要 `OUT.<suffix>/`
  - 需要最终结构证据：`STRU*` 或 `.cif`
- `md`
  - 需要 `OUT.<suffix>/`
  - 需要至少一类 MD 特征证据：`MD_dump*` / `Restart_md*` / `STRU_MD*`
- `md + dp`
  - 继续复用 MD artifact evidence
  - 若缺少 `deeppmd_support` 等 environment prerequisite，则优先归类为 `environment_invalid`
- 不再仅依赖 `return_code == 0`

---

## 4. 当前测试状态

当前 ABACUS 定向测试文件：

- `MHE/tests/test_metaharness_abacus_manifest.py`
- `MHE/tests/test_metaharness_abacus_executor.py`
- `MHE/tests/test_metaharness_abacus_gateway.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`
- `MHE/tests/test_metaharness_abacus_compiler.py`
- `MHE/tests/test_metaharness_abacus_environment.py`
- `MHE/tests/test_metaharness_abacus_validator.py`

最近一次定向验证命令：

```bash
ruff check --fix MHE/src/metaharness_ext/abacus/ MHE/tests/test_metaharness_abacus_*.py
ruff format MHE/src/metaharness_ext/abacus/ MHE/tests/test_metaharness_abacus_*.py
pytest MHE/tests/test_metaharness_abacus_*.py
```

最近结果：

- `46 passed`

---

## 5. 当前分支/工作区注意事项

当前仓库存在大量未提交改动，不只 ABACUS 一项。因此新对话中要注意：

- **只在 ABACUS 范围内工作**，避免误碰别的扩展/文档
- 目标工作区主要限于：
  - `MHE/src/metaharness_ext/abacus/`
  - `MHE/tests/test_metaharness_abacus_*.py`
  - `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/`
  - `MHE/docs/ABACUS_EXTENSION_HANDOFF_REPORT.md`

当前 `git status` 中与 ABACUS 直接相关的路径大多仍是 `??`，说明这些内容尚未被正式提交。

---

## 6. 下一步工作建议

### 6.1 主线建议：继续 Governance Alignment 与文档真值同步

根据路线图：

- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-roadmap.md`

Phase 0–4 的 family / mode baseline 已完成，当前不再建议把主线写成“进入 Phase 3”。

当前建议的主线目标：

1. 持续把 blueprint / roadmap / handoff / wiki 统一到 lifecycle object model
2. 明确 control files、runtime assets、workspace layout、artifact groups、lifecycle state 的对象分层
3. 保持 manifest policy、validator issues / `blocks_promotion`、`ScoredEvidence` 与 canonical `evidence_refs` 的当前实现、测试、文档叙述持续一致
4. 明确 promotion-ready validation semantics 不等于直接 graph promotion
5. 保持已落地 family / mode 与 ABACUS 定向测试叙述零回归

### 6.2 建议的实施顺序

#### Step 1: 先校正文档真值

先明确本轮优先做：

- blueprint / roadmap / handoff-facing 文档与当前代码现实对齐
- 明确 ABACUS 当前采用 lifecycle object model 组织 contracts 与 evidence

暂时不要做：

- 把已落地能力继续写成未来 phase
- 在 docs 中退回到扁平字段心智模型
- 超出 ABACUS 范围改动其它扩展文档

#### Step 2: 按对象层次核对 contracts / runtime surface

目标文件：

- `MHE/src/metaharness_ext/abacus/contracts.py`
- `MHE/src/metaharness_ext/abacus/environment.py`
- `MHE/src/metaharness_ext/abacus/input_compiler.py`
- `MHE/src/metaharness_ext/abacus/executor.py`
- `MHE/src/metaharness_ext/abacus/validator.py`

核对重点：

- control-file objects
- runtime-asset objects
- workspace-layout objects
- artifact-group objects
- lifecycle-state objects

#### Step 3: 继续治理面对齐

建议后续优先推进：

- 保持 manifest `policy.credentials` / `policy.sandbox` 的实现、tests、docs 一致；当前 credential boundary 是 no-subject / no-required-claims / no ABACUS-private credential payload，后续 subject / claim 语义应随宿主 policy 统一细化
- 保持 validator `issues` / `blocks_promotion` / `ScoredEvidence` / canonical `evidence_refs` 的实现、tests、docs 一致
- promotion-ready validation semantics 与 graph promotion authority 的边界
- 收紧仍偏宽松的 evidence / prerequisite 语义并补齐新增边界回归

#### Step 4: 保持 tests / docs 同步

建议持续核对或扩展：

- `MHE/tests/test_metaharness_abacus_environment.py`
- `MHE/tests/test_metaharness_abacus_compiler.py`
- `MHE/tests/test_metaharness_abacus_validator.py`
- `MHE/tests/test_metaharness_abacus_gateway.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`

---

## 7. 当前已知的小缺口 / 后续优化点

这些不是 blocker，但可以作为后续质量提升点：

1. `input_compiler.py` 中 `params` / `relax_controls` 的渲染顺序依赖 dict insertion order；虽然 Python 现在稳定，但如果上游构造顺序不稳定，字节级重现性仍可能漂移
2. 后续边界测试应聚焦新增语义；以下既有边界已覆盖，不应再列为 open todo：
   - NSCF 只给 `restart_file_path`
   - relax 中 `restart_file_path` 非字符串
   - MD 缺特征产物

---

## 8. 参考文档索引

### 8.1 ABACUS 核心 wiki

- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/README.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/01-overview.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/02-workflow-and-components.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/03-contracts-and-artifacts.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/08-runtime-lifecycle.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/09-core-objects-and-io-model.md`

### 8.2 blueprint / roadmap / handoff 参考

- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-roadmap.md`
- `MHE/docs/ABACUS_EXTENSION_HANDOFF_REPORT.md`

### 8.3 代码参考

- `MHE/src/metaharness_ext/abacus/contracts.py`
- `MHE/src/metaharness_ext/abacus/gateway.py`
- `MHE/src/metaharness_ext/abacus/environment.py`
- `MHE/src/metaharness_ext/abacus/input_compiler.py`
- `MHE/src/metaharness_ext/abacus/executor.py`
- `MHE/src/metaharness_ext/abacus/validator.py`

### 8.4 测试参考

- `MHE/tests/test_metaharness_abacus_manifest.py`
- `MHE/tests/test_metaharness_abacus_executor.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`
- `MHE/tests/test_metaharness_abacus_compiler.py`
- `MHE/tests/test_metaharness_abacus_environment.py`
- `MHE/tests/test_metaharness_abacus_validator.py`

### 8.5 可借鉴的其他扩展模式

- `MHE/src/metaharness_ext/jedi/`
- `MHE/src/metaharness_ext/nektar/`
- `MHE/src/metaharness_ext/deepmd/`

重点可借鉴点：

- family-aware contracts
- environment probe pattern
- compiler dispatch pattern
- evidence-first validator pattern

---

## 9. 给新对话窗口的建议工作计划

建议在新对话中采用下面的计划：

1. 阅读 ABACUS blueprint、roadmap 与 lifecycle / object-model 页面
2. 审查当前 `contracts / environment / compiler / executor / validator` 与 docs 的对象模型是否一致
3. 以 control files、runtime assets、workspace layout、artifact groups、lifecycle state 五层校对文档真值
4. 明确 manifest policy、validator blocker、`ScoredEvidence`、canonical `evidence_refs` 已落地能力与真实剩余缺口
5. 只在 ABACUS 范围内补齐必要文档或治理面对齐代码
6. 运行定向验证，确保 docs 与实现叙述不回退

---

## 10. 可直接复制给新对话窗口的提示词

下面这段可以直接复制到新的 Claude Code 对话窗口：

```markdown
请继续对齐 `MHE` 中 `ABACUS extension` 的治理语义与文档真值，不要把当前主线继续写成“进入新 phase”，也不要再引用已退出主导航的 checklist / legacy wiki 页面作为当前真值。

先阅读并遵循这些文件：
- `MHE/docs/ABACUS_EXTENSION_HANDOFF_REPORT.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/05-abacus-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/08-runtime-lifecycle.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/09-core-objects-and-io-model.md`

当前已知状态：
- Phase 0–4 的 family / mode baseline 已完成
- ABACUS package 已存在于 `MHE/src/metaharness_ext/abacus/`
- 定向测试已存在于 `MHE/tests/test_metaharness_abacus_*.py`
- docs 当前应以 lifecycle object model 描述当前实现

请只在 ABACUS 范围内工作，避免碰其他未提交改动。主要工作目录：
- `MHE/src/metaharness_ext/abacus/`
- `MHE/tests/test_metaharness_abacus_*.py`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/`
- `MHE/docs/wiki/meta-harness-engineer/blueprint/`
- `MHE/docs/ABACUS_EXTENSION_HANDOFF_REPORT.md`

本轮实施目标：
1. 校对 docs 与当前 lifecycle object model 是否一致
2. 明确 control files、runtime assets、workspace layout、artifact groups、lifecycle state 五层对象
3. 继续维护 manifest policy、validator blocker、`ScoredEvidence`、canonical `evidence_refs` 的治理叙述与当前实现一致
4. 保持 promotion-ready validation semantics 与 graph promotion authority 的边界清晰
5. 最后运行必要的定向验证

实施约束：
- 不要把已落地 family / mode 写回 future plan
- 不要引入任意 `INPUT` passthrough
- 继续坚持 evidence-first validator，不要只看 return code
- 如需参考现有模式，可借鉴 `jedi` / `nektar` / `deepmd` 扩展

完成后请汇报：
- 改了哪些文件
- docs 与 lifecycle object model 的对齐点是什么
- 跑了哪些测试，结果如何
- 还剩哪些治理面对齐缺口
```

---

## 11. 结论

如果新对话窗口要继续推进，**最合理的下一步是继续做 governance alignment 与文档真值同步**，而不是回头重做 Phase 0/1/2 或把当前主线退回成新的 family phase。

当前代码已经具备：

- 稳定的 ABACUS 扩展骨架
- family-aware typed contracts
- SCF / NSCF / relax / MD end-to-end baseline
- 初步成熟的 evidence-first validation 语义

因此接下来的工作应聚焦在：

- `md + dp` 的最小 typed 闭环保持与文档/测试一致
- 保持 Phase 0/1/2 零回归
- 继续收紧运行前置条件与 validator 证据语义
