# 06. 封装与注册

## 6.1 为什么 DeepMD extension 需要明确的 packaging 约定

`metaharness_ext.deepmd` 不是一组松散脚本，而是需要被 MHE runtime、manifest loader、测试和 reviewer 共同识别的正式扩展包。

因此，目录结构、exports、capabilities、slots、manifest 与 protected boundary 都需要稳定命名。

---

## 6.2 当前目录结构

当前包结构大致为：

```text
MHE/src/metaharness_ext/deepmd/
  |- __init__.py
  |- capabilities.py
  |- collector.py
  |- contracts.py
  |- diagnostics.py
  |- dpgen_machine_compiler.py
  |- dpgen_param_compiler.py
  |- environment.py
  |- evidence.py
  |- executor.py
  |- gateway.py
  |- policy.py
  |- slots.py
  |- study.py
  |- train_config_compiler.py
  |- validator.py
  |- workspace.py
  |- manifest.json
  |- environment.json
  |- executor.json
  |- study.json
  |- train_config_compiler.json
  |- validator.json
```

这个结构说明当前 DeepMD 扩展已经有明确组件边界，而不是把所有逻辑塞进单文件。

---

## 6.3 `__init__.py` 的职责

当前 `__init__.py` 的职责主要是：

- 导出 public contracts / types
- 导出 canonical component classes
- 导出 capability constants、slot constants 与 helper seam

例如它当前导出了：

- contracts：`DeepMDTrainSpec`、`DPGenRunSpec`、`DeepMDEvidenceBundle`、`DeepMDPolicyReport`、`DeepMDStudySpec` 等
- components：`DeepMDGatewayComponent`、`DeepMDEnvironmentProbeComponent`、`DeepMDExecutorComponent`、`DeepMDValidatorComponent`、`DeepMDStudyComponent`
- helpers：`build_train_input_json`、`build_dpgen_param_json`、`build_dpgen_machine_json`、`build_evidence_bundle`、`DeepMDEvidencePolicy`

因此 `__init__.py` 是 public surface，而不是隐式环境探测入口。

---

## 6.4 capabilities

`capabilities.py` 当前定义的 canonical capabilities 包括：

- `deepmd.compile.case`
- `deepmd.environment.probe`
- `deepmd.train.run`
- `deepmd.model.freeze`
- `deepmd.model.test`
- `deepmd.model.compress`
- `deepmd.model.devi`
- `deepmd.dataset.neighbor_stat`
- `deepmd.dpgen.run`
- `deepmd.dpgen.simplify`
- `deepmd.dpgen.autotest`
- `deepmd.validation.check`
- `deepmd.study.run`

这组命名的价值在于：

- 对外表达 extension 能做什么
- 为 runtime wiring 提供稳定 capability vocabulary
- 避免把 family / mode 语义写死在调用方或测试里

---

## 6.5 slots

`slots.py` 当前定义的 canonical slots 为：

- `deepmd_gateway.primary`
- `deepmd_environment.primary`
- `deepmd_config_compiler.primary`
- `deepmd_executor.primary`
- `deepmd_validator.primary`
- `deepmd_study.primary`

其中当前唯一进入 `PROTECTED_SLOTS` 的是：

- `deepmd_validator.primary`

这点很关键：当前真正受保护的是 validator boundary，而不是整个扩展包的所有 helper。

---

## 6.6 manifest 设计

当前包内已经存在：

- `manifest.json`
- `environment.json`
- `executor.json`
- `study.json`
- `train_config_compiler.json`
- `validator.json`

这些 manifest 的意义不是“动态魔法”，而是：

- 让组件边界可审计
- 让 registration 关系不依赖读者猜测
- 让 importability 与 manifest completeness 可测试

当前 manifest 语义里最重要的治理事实是：

- `validator.json` 的 `kind` 是 `governance`
- `validator.json` 的 `safety.protected` 是 `true`
- gateway manifest 当前仍是 `core`

这说明 DeepMD 的治理边界当前落在 validator，而不是 gateway 或 evidence helper。

---

## 6.7 protected boundary 的正确解释

当前 DeepMD 包内至少要严格区分三类对象：

- **registered protected component**：`DeepMDValidatorComponent`
- **registered non-protected components**：gateway / environment / compiler / executor / study
- **unregistered helper seam**：`build_evidence_bundle(...)` 与 `DeepMDEvidencePolicy.evaluate(...)`

因此文档不应把 evidence / policy helper 误写成独立 protected slot，也不应把所有治理语义都说成 manifest 已经完整承载。

---

## 6.8 review 与测试关注点

packaging 层的正式验收点至少包括：

- manifest set completeness
- manifest entry importability
- canonical capability names
- slot naming 稳定性
- protected slot 集合是否符合设计主张

如果这些点不稳，后续文档与代码都会持续漂移。

---

## 6.9 最常见的退化

需要避免：

- 所有类堆进单文件
- helper、component、protected boundary 混成一层
- slot 名称只存在于测试或实现细节中
- 把 manifest 写成单总入口，失去组件级可审计性
- 把 validator 的治理职责误降级为普通 post-run helper

---

## 6.10 结论

DeepMD 的 packaging 层主张应是：

- public exports 清晰
- capabilities / slots 稳定命名
- manifest 与组件边界一一对应
- validator 作为当前唯一 protected governance boundary 被明确表达
- evidence / policy seam 保持为清晰的 helper layer，等待继续与更高层 runtime authority 对齐
