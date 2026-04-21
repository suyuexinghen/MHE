# AI4PDECase XML → PDETaskRequest / PDEPlan 字段映射

## 1. 到 PDETaskRequest 的映射表

目标模型：`MHE/src/metaharness_ai4pde/contracts.py:19` (`PDETaskRequest`)

| AI4PDECase 路径 | PDETaskRequest 字段 | 映射方式 |
|---|---|---|
| `/AI4PDECase/@id` | `task_id` | 直接映射 |
| `/Problem/@type` | `problem_type` | `forward/inverse/design/surrogate` → `ProblemType` 枚举 |
| `/Problem` (Equation + Variables + Parameters + InitialConditions + BoundaryConditions + Reference) | `physics_spec` | 组装成一个嵌套 dict（结构见下） |
| `/Geometry` | `geometry_spec` | 原样结构化为 dict（结构见下） |
| `/Validation` + `/Visualization` + `/Execution/Checkpoint` | `data_spec` | 作为运行/评估/后处理描述打包（结构见下） |
| `/Visualization/*` | `deliverables` | 从 Visualization 段推导（见生成规则） |
| `/Execution/Resources` | `budget` | **M1 新增**：直接映射到 `BudgetRecord` 强类型字段（结构见下） |
| `/Execution/@riskLevel` | `risk_level` | `green/yellow/red` → `RiskLevel` 枚举 |
| `/Problem/Equation + /Geometry + /Discretization` | `goal` | **M4 固定格式**：`{problem_type}:{equation_system}:{domain_shape}:{solver_family}/{backend}` |

### M4: `goal` 固定格式

```
{Problem/@type}:{Problem/Equation/@system}:{Geometry/Domain/@shape}:{Discretization/Solver/@family}/{Discretization/Solver/@backend}
```

示例：`forward:incompressible_navier_stokes:cylinder_in_channel:classical_hybrid/nektar++`

### M1: `budget` 映射

```python
BudgetRecord(
    gpu_hours=float(Resources/@gpuHours or 0),
    cpu_hours=float(Resources/@cpuHours or 0),
    walltime_hours=float(Resources/@walltimeHours or 0),
    hpc_quota=float(Resources/@hpcQuota or 0),
)
```

### `physics_spec` 形状

```python
{
    "equation": {
        "system": str,               # /Problem/Equation/@system
        "form": str | None,          # /Problem/Equation/@form
        "expression": str | None,    # /Problem/Equation/@expression
        "stationary": bool,          # /Problem/Equation/@stationary
        "domain_dim": int,           # /Problem/@domainDim
        "space_dim": int,            # /Problem/@spaceDim
    },
    "variables": [str, ...],         # /Problem/Variables/V text content
    "parameters": {str: str, ...},   # /Problem/Parameters/P @name → text
    "initial_conditions": [
        {"var": str, "value": str | None, "file": str | None},
        ...
    ],
    "boundary_conditions": [
        {
            "name": str,
            "selector": str | None,
            "conditions": [
                {"kind": str, "var": str, "value": str | None, "file": str | None},
                ...
            ],
        },
        ...
    ],
    "reference": {
        "kind": str,
        "source": str | None,
        "metric": str | None,
    } | None,
}
```

**X3 TODO**: `reference` 数据打包在 `physics_spec["reference"]` 中，但 `ReferenceSolverComponent` 目前只接收 `PDEPlan`。需要未来在 source-code 层把 reference 信息从 `PDETaskRequest.physics_spec` 传递到 `ReferenceSolverComponent`。

### `geometry_spec` 形状

```python
{
    "representation": str | None,    # /Geometry/@representation
    "domain": {
        "shape": str | None,
        "bounds": str | None,
    } | None,
    "mesh": {
        "source": str,               # 枚举: generated, file, analytic, external
        "file": str | None,
        "format": str | None,
        "element_type": str | None,
        "curved": bool | None,
    } | None,
}
```

### `data_spec` 形状（M5: Adaptivity 已移出）

```python
{
    "validation": {
        "residual": {"metric": str | None, "target": str | None} | None,
        "constraints": [
            {"kind": str, "target": str | None},   # kind 枚举见 ConstraintKindType
            ...
        ],
    },
    "visualization": {
        "field_outputs": [
            {"format": str, "frequency": int | None, "file": str | None},
            ...
        ],
        "probes": [
            {
                "name": str,
                "point": str | None,    # 单点坐标
                "line": str | None,     # Nektar++ line 语法
                "plane": str | None,    # Nektar++ plane 语法
                "box": str | None,      # Nektar++ box 语法
            },
            ...
        ],
        "derived_fields": [str, ...],
        "plots": [str, ...],
    },
    "checkpoint": {
        "enabled": bool,
        "frequency": int | None,
    },
}
```

### `deliverables` 生成规则

- 默认（始终包含）：`solution_field`, `validation_summary`, `evidence_bundle`
- 每个 `<FieldOutput>`：
  - `format="vtu"` → `vtu_field`
  - `format="png"` → `png_snapshot`
  - 其他格式 → `{format}_field`
- 每个 `<Plot>` → `{type}`（如 `residual_curve`, `drag_lift_curve`）
- 每个 `<DerivedField>` → `derived_field/{name}`（M7: 使用 `/` 分隔符）

---

## 2. 到 PDEPlan 的映射表

目标模型：`MHE/src/metaharness_ai4pde/contracts.py:31` (`PDEPlan`)

| AI4PDECase 路径 | PDEPlan 字段 | 映射方式 |
|---|---|---|
| `/AI4PDECase/@id` | `plan_id` | `plan-{case_id}` |
| `/AI4PDECase/@id` | `task_id` | 与 `PDETaskRequest.task_id` 对齐 |
| `/Discretization/Solver/@family` | `selected_method` | 直接映射到 `SolverFamily` 枚举 |
| `/Discretization/Solver/@templateId` | `template_id` | 直接映射 |
| `/Discretization/Solver/@templateId` 或 `/Runtime/@graphTemplate` | `graph_family` | **M3 优先级**：有 `templateId` 时 → `template::{templateId}`；否则 → `graphTemplate` 的 basename（去掉 `.xml` 后缀） |
| `/Discretization + /Geometry/Mesh + /Execution/Resources + /Adaptivity` | `parameter_overrides` | 组装为 plan-time 参数覆盖（结构见下） |
| `/Validation` | `required_validators` | 从 validation 段推导（见生成规则） |
| `/Visualization` | `expected_artifacts` | 从 visualization 段推导（见生成规则） |
| solver 选择 + backend | `slot_bindings` | **M2 确定性映射表**（见下） |

### M3: `graph_family` 优先级

```
if Solver/@templateId:
    graph_family = f"template::{templateId}"
elif Runtime/@graphTemplate:
    graph_family = Path(graphTemplate).stem   # e.g. "ai4pde-expanded"
else:
    graph_family = "ai4pde-minimal"           # default
```

### M2: `slot_bindings` 确定性映射表

slot ID 来自 `MHE/src/metaharness_ai4pde/slots.py`。

| family | backend | solver_executor.primary | reference_solver.primary | knowledge_adapter.primary |
|--------|---------|------------------------|--------------------------|---------------------------|
| `pinn_strong` | *(any)* | `pinn_strong` | `classical_hybrid` | *(default)* |
| `dem_energy` | *(any)* | `dem_energy` | `classical_hybrid` | *(default)* |
| `operator_learning` | *(any)* | `operator_learning` | `classical_hybrid` | *(default)* |
| `pino` | *(any)* | `pino` | `classical_hybrid` | *(default)* |
| `classical_hybrid` | `nektar++` | `classical_hybrid` | `classical_hybrid` | `nektar_case_library` |
| `classical_hybrid` | *(other)* | `classical_hybrid` | `classical_hybrid` | *(default)* |

`*(default)*` 表示不写 slot_bindings 条目，让 MethodRouter 使用内部默认值。

### `parameter_overrides` 形状

```python
{
    "backend": str | None,            # /Discretization/Solver/@backend
    "nektar_solver": str | None,      # /Discretization/Solver/@nektarSolver
    "driver": str | None,             # /Discretization/Solver/@driver
    "space": {
        "projection": str | None,
        "basis": str | None,
        "order": int | None,
        "quadrature": str | None,
    },
    "time_integration": {
        "method": str | None,
        "variant": str | None,
        "order": int | None,
    },
    "linear_solver": {
        "type": str | None,
        "preconditioner": str | None,
        "tolerance": str | None,
    },
    "mesh": {
        "source": str,
        "file": str | None,
        "format": str | None,
        "element_type": str | None,
        "curved": bool | None,
    },
    # M5: Adaptivity 只进 PDEPlan，不进 data_spec
    "adaptivity": {
        "strategy": str | None,
        "target_error": str | None,
        "max_iters": int | None,
        "stagnation_limit": int | None,
    },
}
```

### `required_validators` 生成规则

按固定逻辑从 `/Validation` 段推导：

| 条件 | 添加 validator |
|------|----------------|
| `<Residual>` 存在 | `residuals` |
| `<Problem/BoundaryConditions>` 非空 | `boundary_conditions` |
| `<Constraint kind="boundary_consistency">` 存在 | `boundary_consistency` |
| `<Constraint kind="mass_conservation">` 存在 | `conservation` |
| `<Constraint kind="energy_conservation">` 存在 | `conservation` |
| `<Constraint kind="momentum_conservation">` 存在 | `conservation` |
| `<Problem/Reference>` 存在 | `reference_compare` |

### `expected_artifacts` 生成规则

| 来源 | 添加 artifact |
|------|---------------|
| 默认 | `solution_field`, `validation_bundle`, `evidence_bundle` |
| `<FieldOutput format="vtu">` | `vtu_field` |
| `<FieldOutput format="png">` | `png_snapshot` |
| `<FieldOutput format="{fmt}">` | `{fmt}_field` |
| `<Plot type="{t}">` | `{t}` |
| `<DerivedField name="{n}">` | `derived_field/{n}` |

---

## 3. 编译结果示意

### PDETaskRequest

```python
PDETaskRequest(
    task_id="cylinder-flow-re100",
    goal="forward:incompressible_navier_stokes:cylinder_in_channel:classical_hybrid/nektar++",
    problem_type=ProblemType.FORWARD,
    physics_spec={
        "equation": {"system": "incompressible_navier_stokes", ...},
        "variables": ["u", "v", "p"],
        "parameters": {"Re": "100", "dt": "0.001", ...},
        "boundary_conditions": [...],
        "reference": {"kind": "literature", ...},
    },
    geometry_spec={
        "representation": "file",
        "domain": {"shape": "cylinder_in_channel", ...},
        "mesh": {"source": "file", "file": "meshes/cylinder_re100.xml", ...},
    },
    data_spec={
        "validation": {"residual": {"metric": "l2", ...}, ...},
        "visualization": {...},
        "checkpoint": {"enabled": True, ...},
    },
    deliverables=[
        "solution_field", "validation_summary", "evidence_bundle",
        "vtu_field", "png_snapshot", "residual_curve", "drag_lift_curve",
        "derived_field/vorticity",
    ],
    budget=BudgetRecord(gpu_hours=0.0, cpu_hours=4.0, walltime_hours=2.0, hpc_quota=0.2),
    risk_level=RiskLevel.YELLOW,
)
```

### PDEPlan

```python
PDEPlan(
    plan_id="plan-cylinder-flow-re100",
    task_id="cylinder-flow-re100",
    selected_method=SolverFamily.CLASSICAL_HYBRID,
    template_id="forward-fluid-mechanics",
    graph_family="template::forward-fluid-mechanics",
    slot_bindings={
        "solver_executor.primary": "classical_hybrid",
        "reference_solver.primary": "classical_hybrid",
        "knowledge_adapter.primary": "nektar_case_library",
    },
    parameter_overrides={
        "backend": "nektar++",
        "nektar_solver": "IncNavierStokesSolver",
        "driver": "Standard",
        "space": {"projection": "DG", "basis": "Modified", "order": 6, ...},
        "time_integration": {"method": "IMEX", ...},
        "linear_solver": {"type": "IterativeStaticCond", ...},
        "mesh": {"source": "file", "file": "meshes/cylinder_re100.xml", ...},
        "adaptivity": {"strategy": "p_refine", "target_error": "1e-5", ...},
    },
    required_validators=["residuals", "boundary_conditions", "conservation", "reference_compare"],
    expected_artifacts=[
        "solution_field", "validation_bundle", "evidence_bundle",
        "vtu_field", "png_snapshot", "residual_curve", "drag_lift_curve",
        "derived_field/vorticity",
    ],
)
```

---

## 4. Parser 层验证责任

以下约束不在 XSD 层表达，由 `case_parser.py` 在运行时检查：

| ID | 约束 | 检查方式 |
|----|------|----------|
| P2 | `<Equation expression="...">` 中引用的参数必须在 `<Parameters>` 中声明 | 扫描 expression 中的标识符，与 Parameters key 集合做差集 |
| P7 | `Runtime/@requiredComponents` 中的 slot ID 必须在 graphTemplate 中存在 | 解析 graph XML，提取 component ID 集合，做子集检查 |
| P10 | `Mesh/@source="file"` 时 `Domain` 应为纯文档作用；`source="analytic"` 时 `Mesh` 可省略 | 条件分支检查 |
| X3 | `Reference` 数据需要传递到 `ReferenceSolverComponent` | 需要源码层修复，不在 parser 层解决 |

---

## 5. 实现顺序建议

1. 新增 `case_parser.py`：`parse_ai4pde_case_xml()` → `PDETaskRequest` + `PDEPlan`
2. 修改 `PDEGatewayComponent`：新增 `issue_task_from_case(path)`
3. 修改 `MethodRouterComponent`：从 case 的 `Discretization` 段选择 solver，不再硬编码 `PINN_STRONG`
4. 未来：增加 `session` 编译器 `NektarSessionCompiler`
5. 新增 `visualization_adapter`：从 `PDERunArtifact` 生成 vtu/png/csv/html
