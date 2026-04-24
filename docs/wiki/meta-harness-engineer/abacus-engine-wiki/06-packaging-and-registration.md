# 06. 封装与注册

## 6.1 为什么 ABACUS extension 需要明确的 packaging 约定

`metaharness_ext.abacus` 不是一组松散脚本，而是需要被 MHE runtime、manifest loader、测试和 reviewer 共同识别的正式扩展包。

因此，目录结构、exports、capabilities、slots、manifest 与 protected boundary 都需要稳定命名。

---

## 6.2 当前目录结构

当前包结构大致为：

```text
MHE/src/metaharness_ext/abacus/
  |- __init__.py
  |- capabilities.py
  |- contracts.py
  |- environment.py
  |- executor.py
  |- gateway.py
  |- input_compiler.py
  |- slots.py
  |- validator.py
  |- manifest.json
  |- gateway.json
  |- environment.json
  |- input_compiler.json
  |- executor.json
  |- validator.json
```

这说明当前扩展已经有清晰的组件边界，而不是单文件实现。

---

## 6.3 capabilities

`capabilities.py` 当前定义的 canonical capabilities 包括：

- `abacus.environment.probe`
- `abacus.compile.case`
- `abacus.scf.run`
- `abacus.nscf.run`
- `abacus.relax.run`
- `abacus.md.run`
- `abacus.validation.check`

这些 capability 名称是对外能力词表，不应漂移为测试内部约定。

---

## 6.4 slots

`slots.py` 当前定义的 canonical slots 为：

- `abacus_gateway.primary`
- `abacus_environment.primary`
- `abacus_input_compiler.primary`
- `abacus_executor.primary`
- `abacus_validator.primary`

其中当前唯一进入 `PROTECTED_SLOTS` 的是：

- `abacus_validator.primary`

这点很关键：当前真正受保护的是 validator boundary，而不是整个 ABACUS 包。

---

## 6.5 manifest 设计

当前 ABACUS 包内已经存在：

- `manifest.json`
- `gateway.json`
- `environment.json`
- `input_compiler.json`
- `executor.json`
- `validator.json`

其中当前最重要的治理事实是：

- 根 `manifest.json` 不是 protected component
- `validator.json` 的 `kind` 是 `governance`
- `validator.json` 的 `safety.protected` 是 `true`
- manifests 已开始显式包含 `policy.sandbox` / `policy.credentials`

因此文档不应把整个 ABACUS 扩展误写成“全包 protected”。

---

## 6.6 `__init__.py` 与 public surface

ABACUS 的 public surface 应保持：

- 导出 contracts / component classes
- 导出 capability constants 与 slot constants
- 保持稳定 `__all__`

而不应承担隐式环境探测或运行时副作用。

---

## 6.7 当前 packaging 的语气边界

由于 ABACUS extension 仍在开发中，packaging 文档的正确语气应是：

- 明确当前已经存在的组件与 manifest 边界
- 明确 validator 是当前唯一 protected governance boundary
- 不把尚未完全完成的更高层 policy / evidence integration 写成“已经结束的工作”

---

## 6.8 结论

ABACUS 的 packaging 层主张应是：

- public exports 清晰
- capabilities / slots 稳定命名
- manifest 与组件边界一一对应
- validator 作为当前唯一 protected boundary 被明确表达

这样即使扩展仍在开发中，registration 与治理边界也不会漂移。
