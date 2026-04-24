# ABACUS Extension Handoff Report

> 目的：给新的 Claude Code 对话窗口提供一份可直接接力开发的工作指导文档。
> 范围：`MHE/src/metaharness_ext/abacus/` 与对应测试 / wiki。
> 状态基线：Phase 0 已完成，Phase 1（NSCF / relax baseline）已完成并通过定向测试；Phase 2（MD baseline）与 Phase 3（`md + dp` typed baseline）已完成并通过 ABACUS 定向测试，下一步进入 Phase 4。

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

下一阶段应进入：

- **Phase 4**：Examples / Study / Governance Hardening

---

## 2. 已完成进度

### 2.1 文档与设计侧

ABACUS wiki 已建立并形成较完整的实施依据：

- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/README.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/01-overview.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/02-workflow-and-components.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/03-contracts-and-artifacts.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/04-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/05-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/06-implementation-hardening-checklist.md`

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
  - relax：读取 `relax_controls["restart_file_path"]`
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
  - 需要 `running_nscf.log` 或 `running_scf.log`
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

### 6.1 主线建议：进入 Phase 3（MD + DP / typed hardening）

根据路线图：

- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/05-roadmap.md`

Phase 2（MD baseline）已完成，本轮已补齐：

1. `AbacusMdSpec` 的 end-to-end workflow 接线
2. compiler 对 MD family 的 dispatch 与 baseline 渲染
3. validator 对 MD success evidence 的 family-specific 判断
4. MD 定向测试、minimal demo，以及 gateway 直测
5. 完整 ABACUS 套件回归验证（`33 passed`）

下一个正式 phase 应进入：

- **Phase 3: MD + DP / typed hardening**

建议的 Phase 3 目标：

1. 支持 `md + esolver_type=dp` 的受控 typed 接口
2. 明确 `pot_file`、runtime prerequisites 与 environment probe 的联动
3. 收紧/类型化 MD 关键控制项，减少隐式 `params` 语义
4. 继续补强 validator 与 artifact 语义，避免只停留在文件存在性层面
5. 保持 Phase 0/1/2 全量零回归

### 6.2 建议的实施顺序

#### Step 1: 定义 Phase 3 范围

先明确本轮只做：

- `md + dp` 的最小 typed 闭环
- 与 `pot_file` / DeepMD 支持检测相关的必要环境约束

暂时不要做：

- 更大范围的任意 `INPUT` passthrough
- 过早引入复杂 HPC policy
- 超出当前 typed contract 边界的大规模重构

#### Step 2: 扩展 contracts / environment

目标文件：

- `MHE/src/metaharness_ext/abacus/contracts.py`
- `MHE/src/metaharness_ext/abacus/environment.py`

需要加入：

- `md + dp` 的组合校验
- `pot_file` / 相关运行时前置条件的显式约束
- 与 DeepMD 支持检测一致的环境验证规则

#### Step 3: 扩展 compiler / executor / validator

目标文件：

- `MHE/src/metaharness_ext/abacus/input_compiler.py`
- `MHE/src/metaharness_ext/abacus/executor.py`
- `MHE/src/metaharness_ext/abacus/validator.py`

需要加入：

- `md + dp` 的受控编译路径
- Phase 3 所需 runtime prerequisites 的显式纳入
- 更细化的 MD 成功证据与失败诊断语义

#### Step 4: 扩展 tests / docs

建议新增或扩展：

- `MHE/tests/test_metaharness_abacus_environment.py`
- `MHE/tests/test_metaharness_abacus_compiler.py`
- `MHE/tests/test_metaharness_abacus_validator.py`
- `MHE/tests/test_metaharness_abacus_gateway.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`

---

## 7. 当前已知的小缺口 / 后续优化点

这些不是 blocker，但可以作为后续质量提升点：

1. `relax_controls["restart_file_path"]` 目前仍是隐式 key，typedness 不够强
2. `input_compiler.py` 中 `params` / `relax_controls` 的渲染顺序依赖 dict insertion order；虽然 Python 现在稳定，但如果上游构造顺序不稳定，字节级重现性仍可能漂移
3. `plan.required_runtime_paths` 当前未完整收纳 `required_paths` / `pseudo_files` / `orbital_files`
4. NSCF 目前接受 `running_nscf.log` 或 `running_scf.log` 作为成功证据之一，这一规则较宽松，后续可以再收紧
5. 可补更多边界测试：
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
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/04-extension-blueprint.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/05-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/06-implementation-hardening-checklist.md`

### 8.2 代码参考

- `MHE/src/metaharness_ext/abacus/contracts.py`
- `MHE/src/metaharness_ext/abacus/gateway.py`
- `MHE/src/metaharness_ext/abacus/environment.py`
- `MHE/src/metaharness_ext/abacus/input_compiler.py`
- `MHE/src/metaharness_ext/abacus/executor.py`
- `MHE/src/metaharness_ext/abacus/validator.py`

### 8.3 测试参考

- `MHE/tests/test_metaharness_abacus_manifest.py`
- `MHE/tests/test_metaharness_abacus_executor.py`
- `MHE/tests/test_metaharness_abacus_minimal_demo.py`
- `MHE/tests/test_metaharness_abacus_compiler.py`
- `MHE/tests/test_metaharness_abacus_environment.py`
- `MHE/tests/test_metaharness_abacus_validator.py`

### 8.4 可借鉴的其他扩展模式

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

1. 阅读 ABACUS roadmap 与 hardening checklist
2. 审查当前 `contracts / environment / compiler / validator` 中 Phase 3 相关空缺
3. 仅实现 `md + dp` 的最小 typed baseline
4. 明确 `pot_file`、环境探测、runtime prerequisites 的联动
5. 补齐 Phase 3 定向测试与回归验证
6. 运行 `ruff + pytest` 做 ABACUS 定向验证

---

## 10. 可直接复制给新对话窗口的提示词

下面这段可以直接复制到新的 Claude Code 对话窗口：

```markdown
请继续开发 `MHE` 中的 `ABACUS extension`，当前目标是从已完成的 Phase 2 继续推进到 **Phase 3: MD + DP / typed hardening**。

先阅读并遵循这些文件：
- `MHE/docs/ABACUS_EXTENSION_HANDOFF_REPORT.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/README.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/05-roadmap.md`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/06-implementation-hardening-checklist.md`

当前已知状态：
- Phase 0（SCF baseline）已完成
- Phase 1（NSCF / relax baseline）已完成
- Phase 2（MD baseline）已完成
- ABACUS package 已存在于 `MHE/src/metaharness_ext/abacus/`
- 定向测试已存在于 `MHE/tests/test_metaharness_abacus_*.py`
- 最近一次 ABACUS 定向测试结果是 `33 passed`

请只在 ABACUS 范围内工作，避免碰其他未提交改动。主要工作目录：
- `MHE/src/metaharness_ext/abacus/`
- `MHE/tests/test_metaharness_abacus_*.py`
- `MHE/docs/wiki/meta-harness-engineer/abacus-engine-wiki/`

本轮实施目标：
1. 为 `md + esolver_type=dp` 建立最小 typed 闭环
2. 在 `contracts.py` / `environment.py` 中补强 `pot_file` 与环境约束
3. 在 `input_compiler.py` / `executor.py` / `validator.py` 中支持 Phase 3 所需路径与证据语义
4. 新增或扩展 Phase 3 定向测试
5. 最后运行：
   - `ruff check --fix MHE/src/metaharness_ext/abacus/ MHE/tests/test_metaharness_abacus_*.py`
   - `ruff format MHE/src/metaharness_ext/abacus/ MHE/tests/test_metaharness_abacus_*.py`
   - `pytest MHE/tests/test_metaharness_abacus_*.py`

实施约束：
- 先只做 `md + dp` 的最小 typed 范围
- 不要引入任意 `INPUT` passthrough
- 继续坚持 evidence-first validator，不要只看 return code
- 如需参考现有模式，可借鉴 `jedi` / `nektar` / `deepmd` 扩展

完成后请汇报：
- 改了哪些文件
- Phase 3 的成功证据规则是什么
- 跑了哪些测试，结果如何
- 还剩哪些更后续的缺口
```

---

## 11. 结论

如果新对话窗口要继续推进，**最合理的下一步是实现 Phase 3（MD + DP / typed hardening）**，而不是回头重做 Phase 0/1/2。

当前代码已经具备：

- 稳定的 ABACUS 扩展骨架
- family-aware typed contracts
- SCF / NSCF / relax / MD end-to-end baseline
- 初步成熟的 evidence-first validation 语义

因此接下来的工作应聚焦在：

- `md + dp` 的最小 typed 闭环
- 保持 Phase 0/1/2 零回归
- 继续收紧运行前置条件与 validator 证据语义
