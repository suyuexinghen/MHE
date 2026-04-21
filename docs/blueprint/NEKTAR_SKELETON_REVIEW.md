# `metaharness_nektar` 骨架代码审查

Date: 2026-04-20

---

## 总体判定

**骨架可用，但有 7 处必须修复才能安全进入下一轮实现。**

整体架构方向与 MHE 模式高度对齐。types/contracts/slots/capabilities 四件套与 `metaharness_ai4pde` 风格一致。组件生命周期（`activate`/`deactivate`/`declare_interface`）正确继承 `HarnessComponent`。`protected = True` 在 validator 上正确声明。测试通过，lint 通过。

以下逐项分析。

---

## 1. 必须修复

### 1.1 manifest.json 只注册了 gateway 一个组件，缺少其余 4 个

**现状：** `manifest.json` 只包含 `NektarGatewayComponent` 一个 entry。

**问题：** `metaharness_ai4pde` 的 manifest 只描述一个组件是因为每个组件有独立 manifest。但 Nektar 包用了 flat layout，所有 5 个组件在同一 package 里。当前 discovery 系统按 manifest 文件扫描，一个 JSON 只能声明一个组件。

**影响：** 其余 4 个组件（session_compiler, solver_executor, postprocess, validator）无法被 discovery 发现。

**修复方案：** 创建 5 个独立 manifest JSON（与 ai4pde 一个组件一个 manifest 的惯例一致），放在 `MHE/src/metaharness_nektar/manifests/` 或包根目录下按组件命名：
- `manifest.gateway.json`
- `manifest.compiler.json`
- `manifest.executor.json`
- `manifest.postprocess.json`
- `manifest.validator.json`

或者等下一轮改 discovery 支持多组件 manifest。但现在应至少补全 4 个 manifest。

### 1.2 `NektarSessionPlan.equation_type` 的 Union 类型无法被 Pydantic 正确反序列化

**现状（contracts.py:77）：**
```python
equation_type: NektarAdrEqType | NektarIncnsEqType
```

**问题：** Pydantic v2 的 Union 反序列化在两个 enum 的值不重叠时不会出问题（此处确实不重叠），但 `solver_executor.py:37` 里用 `str(plan.equation_type.value)` 访问值，如果未来 enum 成员值出现交叉，会引发歧义。更重要的是，`build_plan()` 里硬编码 `NektarAdrEqType.HELMHOLTZ` 而不检查 `problem.solver_family`，当 family 是 `INCNS` 时会产出非法 plan。

**修复：** `build_plan()` 必须按 `solver_family` 分支选择正确的 `equation_type` 默认值：
```python
if problem.solver_family == NektarSolverFamily.ADR:
    default_eq = NektarAdrEqType.HELMHOLTZ
elif problem.solver_family == NektarSolverFamily.INCNS:
    default_eq = NektarIncnsEqType.UNSTEADY_NAVIER_STOKES
```

### 1.3 `PostprocessComponent.run_postprocess()` 直接 mutate artifact 的 list 字段

**现状（postprocess.py:26-28）：**
```python
updated = artifact.model_copy(deep=True)
updated.derived_files.append("solution.vtu")
updated.filter_output.files.append("solution.vtu")
```

**问题：** `model_copy(deep=True)` 已经深拷贝了所有字段，所以这里不会产生副作用。但从代码意图看，`deep=True` 的开销对一个 stub 来说不必要——如果后续实现里忘了 `deep=True`，就会产生共享 list 的 bug。这是正确的实现，但应在 `run_postprocess` 方法注释中标明"必须 deep copy"的约束。

**严重度：** 低。当前行为正确，只是缺少显式约束注释。

### 1.4 `NektarBoundaryCondition.prim_coeff` 应该有 Robin BC 时的必填校验

**现状（contracts.py:18-24）：**
```python
class NektarBoundaryCondition(BaseModel):
    region: str
    field: str
    condition_type: NektarBoundaryConditionType
    value: str | None = None
    user_defined_type: str | None = None
    prim_coeff: str | None = None
```

**问题：** 蓝图审查明确要求"Robin BC 缺 PRIMCOEFF 应被拒绝"，但 contract 层没有任何 validator 强制这个约束。蓝图里画了 `validate_boundary_conditions()` 函数，但实际代码里没有引用它。

**修复：** 添加 `model_validator`：
```python
from pydantic import model_validator

@model_validator(mode="after")
def validate_robin_prim_coeff(self) -> "NektarBoundaryCondition":
    if self.condition_type == NektarBoundaryConditionType.ROBIN and self.prim_coeff is None:
        raise ValueError("Robin BC requires prim_coeff (PRIMCOEFF in Nektar++ XML)")
    return self
```

### 1.5 `NektarGeometrySection` 缺 dimension 校验

**现状（contracts.py:27-34）：** `NektarGeometrySection` 没有 `dimension` 字段，所以蓝图里要求的 "EDGE required for DIM>=2, FACE required for DIM=3" 校验无法实现。

**问题：** 蓝图审查明确修复了 `GeometrySection` 应带 `dimension` 和 `space_dimension` 字段并做 model_validator。实际代码里 `NektarGeometrySection` 是一个纯数据容器，完全没有 dimension 信息。

**修复：** 给 `NektarGeometrySection` 加 `dimension: int` 和对应的 model_validator。

### 1.6 `solver_executor.py` 缺少 router 职责

**现状：** 计划说"solver_router 逻辑先内聚在 solver_executor.py 中"，但 `SolverExecutorComponent` 只做了执行分发，没有做路由校验（如验证 equation_type 是否属于该 solver_family 的合法值）。

**问题：** 蓝图的 `SolverRouterComponent` 职责包括"validate equation_type against the solver family's admissible values"。当前 `execute_plan()` 只检查 `solver_family` 是否在 `{ADR, INCNS}` 中，不检查 `equation_type` 与 `solver_family` 的匹配。

**修复：** 在 `execute_plan()` 中加 validation：
```python
def _validate_eq_type(self, plan: NektarSessionPlan) -> None:
    if plan.solver_family == NektarSolverFamily.ADR:
        if not isinstance(plan.equation_type, NektarAdrEqType):
            raise ValueError(f"ADR family requires NektarAdrEqType, got {type(plan.equation_type)}")
    elif plan.solver_family == NektarSolverFamily.INCNS:
        if not isinstance(plan.equation_type, NektarIncnsEqType):
            raise ValueError(f"IncNS family requires NektarIncnsEqType, got {type(plan.equation_type)}")
```

### 1.7 `__init__.py` 导出 `build_session_plan` 但测试未覆盖

**现状：** `__init__.py:52` 导出 `build_session_plan`，但 `test_metaharness_nektar_imports.py` 里没有测试这个 module-level helper 的行为。

**问题：** `build_session_plan` 是一个绕过组件生命周期的便捷函数。它的行为与 `SessionCompilerComponent.build_plan()` 一致（只是包了一层实例化），但如果 `SessionCompilerComponent` 未来加 constructor 注入或状态，这个 helper 会静默绕过那些初始化路径。

**修复：** 在测试中添加 `build_session_plan` 的基本行为测试，或考虑下一轮移除这个 helper（让调用方显式通过组件走）。

---

## 2. 应该修复

### 2.1 `NektarRunArtifact` 缺 `solver_binary` 字段

蓝图 `NektarSessionPlan` 有 `solver_binary: str` 字段，用于指定实际要调用的 Nektar++ 可执行文件。`NektarRunArtifact` 应该记录实际使用了哪个 binary，便于 debug。

### 2.2 `FilterOutputSummary` 比蓝图简化太多

蓝图定义了 `checkpoint_files`, `history_point_files`, `energy_norms`, `error_norms`, `moving_body_forces`, `fieldconvert_intermediates` 等 typed 字段。实际代码只有 `files: list[str]`, `metrics: dict`, `metadata: dict`。这对 Phase 1 stub 可以接受，但应在代码中加 `# TODO: expand per blueprint` 注释，防止遗忘。

### 2.3 `NektarValidationReport` 的字段名与蓝图不完全一致

蓝图里有 `solver_exited_cleanly`, `field_files_exist`, `error_vs_reference`。实际代码用了 `solver_exit_ok`, `outputs_present`, `reference_error_ok`。命名差异本身不是 bug，但如果后续要统一蓝图和代码，应保持一致。

### 2.4 `capabilities.py` 的命名空间与蓝图不同

蓝图：`CAP_NEKTAR_CASE_COMPILE = "nektar.compile.case"`
实际：`CAP_NEKTAR_CASE_COMPILE = "nektar.case.compile"`

蓝图按 `<domain>.<category>.<name>` 排列（与 ai4pde 一致），实际代码按 `<domain>.<qualifier>.<qualifier>` 排列。应统一为蓝图定义的格式。

---

## 3. 风格对齐确认

| 维度 | ai4pde 惯例 | nektar 实现 | 判定 |
|------|------------|------------|------|
| `str, Enum` 类型 | Yes | Yes | OK |
| Pydantic v2 BaseModel | Yes | Yes | OK |
| `task_id` 全模型贯通 | Yes | Yes | OK |
| `Field(default_factory=...)` | Yes | Yes | OK |
| slot 常量 plain string | Yes | Yes | OK |
| `PROTECTED_SLOTS` frozenset | Yes | Yes | OK |
| `HarnessComponent` 子类 | Yes | Yes | OK |
| `protected = True` class attr | Yes (reference_solver) | Yes (validator) | OK |
| `CANONICAL_CAPABILITIES` frozenset | Yes | Yes | OK |
| `__all__` 导出列表 | Yes | Yes | OK |
| manifest JSON 格式 | Yes (one per component) | 部分（仅 gateway） | **需补** |
| `activate`/`deactivate` async | Yes | Yes | OK |

---

## 4. 测试覆盖评估

### 已有测试

- `test_metaharness_nektar_imports.py` — import 正确性、enum 实例化、contract 默认值
- `test_metaharness_nektar_manifest.py` — manifest 解析、entry 可导入

### 缺失测试（应下一轮补）

- `build_plan()` 在 `solver_family=INCNS` 时应返回 `NektarIncnsEqType`
- Robin BC 缺 `prim_coeff` 应 raise `ValueError`
- `execute_plan()` 拒绝 family/eq_type 不匹配
- `NektarGeometrySection` dimension 校验
- 5 个组件各自的 `declare_interface()` 返回非空 declarations

---

## 5. 总结

骨架的架构方向完全正确。核心问题集中在：

1. **manifest 不完整**（只有 1/5 组件）
2. **contract 校验缺失**（Robin PRIMCOEFF、geometry dimension）
3. **router 校验缺失**（equation_type vs solver_family 匹配）
4. **capability 命名空间偏差**

这些都是"下一轮实现前必须修"的级别，不影响骨架的 import/test 通过，但如果直接进入 XML render 或 solver execute 阶段，会在运行时暴露。
