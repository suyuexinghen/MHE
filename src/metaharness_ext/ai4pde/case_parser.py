from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from metaharness.config.xml_parser import parse_graph_xml
from metaharness_ext.ai4pde.contracts import BudgetRecord, PDEPlan, PDETaskRequest
from metaharness_ext.ai4pde.slots import (
    KNOWLEDGE_ADAPTER_SLOT,
    REFERENCE_SOLVER_SLOT,
    SOLVER_EXECUTOR_SLOT,
)
from metaharness_ext.ai4pde.types import ProblemType, RiskLevel, SolverFamily

_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_KNOWN_EXPR_TOKENS = frozenset({"and", "cos", "e", "exp", "log", "pi", "pow", "sin", "sqrt", "tan"})
_CONSERVATION_KINDS = frozenset(
    {"mass_conservation", "energy_conservation", "momentum_conservation"}
)


class Ai4PdeCaseXmlError(ValueError):
    def __init__(self, issues: list[str]) -> None:
        message = "; ".join(issues) if issues else "invalid AI4PDECase document"
        super().__init__(message)
        self.issues = list(issues)


def parse_ai4pde_case_xml(
    path: str | Path,
    *,
    validate_schema: bool = True,
) -> tuple[PDETaskRequest, PDEPlan]:
    case_path = Path(path).resolve()
    return parse_ai4pde_case_xml_text(
        case_path.read_text(),
        validate_schema=validate_schema,
        base_dir=case_path.parent,
    )


def parse_ai4pde_case_xml_text(
    xml_text: str,
    *,
    validate_schema: bool = True,
    base_dir: str | Path | None = None,
) -> tuple[PDETaskRequest, PDEPlan]:
    root = ET.fromstring(xml_text.lstrip())
    resolved_base_dir = Path(base_dir).resolve() if base_dir is not None else None
    if validate_schema:
        _validate_ai4pde_case_document(root, base_dir=resolved_base_dir)
    return _compile_case(root, base_dir=resolved_base_dir)


def _compile_case(root: ET.Element, *, base_dir: Path | None) -> tuple[PDETaskRequest, PDEPlan]:
    case_id = root.attrib["id"]
    problem = _required_child(root, "Problem")
    discretization = _required_child(root, "Discretization")
    execution = root.find("Execution")
    geometry = root.find("Geometry")
    validation = root.find("Validation")
    visualization = root.find("Visualization")
    runtime = root.find("Runtime")
    adaptivity = root.find("Adaptivity")

    problem_type = ProblemType(problem.attrib["type"])
    solver = _required_child(discretization, "Solver")
    solver_family = SolverFamily(solver.attrib["family"])
    backend = solver.attrib.get("backend") or "default"
    domain_shape = _extract_domain_shape(geometry)
    equation = _required_child(problem, "Equation")
    goal = f"{problem_type.value}:{equation.attrib['system']}:{domain_shape}:{solver_family.value}/{backend}"

    physics_spec = _build_physics_spec(problem)
    geometry_spec = _build_geometry_spec(geometry, base_dir=base_dir)
    budget = _build_budget(execution)
    runtime_metadata = _build_runtime_metadata(runtime, base_dir=base_dir)
    data_spec = _build_data_spec(validation, visualization, execution, runtime_metadata)
    plan = _build_plan(
        case_id=case_id,
        solver=solver,
        geometry=geometry,
        discretization=discretization,
        validation=validation,
        visualization=visualization,
        adaptivity=adaptivity,
        runtime_metadata=runtime_metadata,
        reference=physics_spec.get("reference"),
    )
    data_spec["planning"] = plan.model_dump(mode="json")

    task = PDETaskRequest(
        task_id=case_id,
        goal=goal,
        problem_type=problem_type,
        physics_spec=physics_spec,
        geometry_spec=geometry_spec,
        data_spec=data_spec,
        deliverables=_build_deliverables(visualization),
        budget=budget,
        risk_level=_parse_risk_level(execution),
    )
    return task, plan


def _validate_ai4pde_case_document(root: ET.Element, *, base_dir: Path | None) -> None:
    issues: list[str] = []
    if root.tag != "AI4PDECase":
        raise Ai4PdeCaseXmlError([f"root element must be <AI4PDECase>, got <{root.tag}>"])
    for attr in ["id", "version"]:
        if not root.attrib.get(attr):
            issues.append(f"<AI4PDECase> missing required attribute '{attr}'")
    problem = root.find("Problem")
    if problem is None:
        issues.append("<AI4PDECase> missing required child <Problem>")
    discretization = root.find("Discretization")
    if discretization is None:
        issues.append("<AI4PDECase> missing required child <Discretization>")
    if issues:
        raise Ai4PdeCaseXmlError(issues)
    assert problem is not None

    _validate_expression_parameters(problem, issues)
    _validate_geometry(geometry=root.find("Geometry"), issues=issues)
    _validate_runtime(root.find("Runtime"), base_dir=base_dir, issues=issues)
    if issues:
        raise Ai4PdeCaseXmlError(issues)


def _validate_expression_parameters(problem: ET.Element, issues: list[str]) -> None:
    equation = problem.find("Equation")
    expression = None if equation is None else equation.attrib.get("expression")
    if not expression:
        return
    parameter_names = {
        parameter.attrib["name"]
        for parameter in problem.findall("./Parameters/P")
        if parameter.attrib.get("name")
    }
    unknown = sorted(
        {
            token
            for token in _IDENTIFIER_RE.findall(expression)
            if token not in parameter_names and token not in _KNOWN_EXPR_TOKENS
        }
    )
    if unknown:
        issues.append(
            f"Equation/@expression references undeclared parameters: {', '.join(unknown)}"
        )


def _validate_geometry(*, geometry: ET.Element | None, issues: list[str]) -> None:
    if geometry is None:
        return
    mesh = geometry.find("Mesh")
    domain = geometry.find("Domain")
    if mesh is None:
        return
    source = mesh.attrib.get("source")
    if source == "file" and not mesh.attrib.get("file"):
        issues.append("Geometry/Mesh@source='file' requires Mesh@file")
    if source == "analytic" and domain is None:
        issues.append("Geometry/Mesh@source='analytic' requires a Domain element")
    if source == "generated" and domain is None:
        issues.append("Geometry/Mesh@source='generated' requires a Domain element")


def _validate_runtime(
    runtime: ET.Element | None, *, base_dir: Path | None, issues: list[str]
) -> None:
    if runtime is None:
        return
    raw_graph_template = runtime.attrib.get("graphTemplate")
    raw_required = runtime.attrib.get("requiredComponents", "")
    if not raw_required.strip():
        return
    required_components = [
        component.strip() for component in raw_required.split(",") if component.strip()
    ]
    if not raw_graph_template:
        issues.append("Runtime@requiredComponents requires Runtime@graphTemplate")
        return
    if base_dir is None:
        return
    graph_template = _resolve_case_path(raw_graph_template, base_dir, search_examples=True)
    if not graph_template.exists():
        issues.append(f"graphTemplate does not exist: {graph_template}")
        return
    snapshot = parse_graph_xml(graph_template)
    component_ids = {node.component_id for node in snapshot.nodes}
    missing = [component for component in required_components if component not in component_ids]
    if missing:
        issues.append(
            f"Runtime@requiredComponents missing from graphTemplate: {', '.join(missing)}"
        )


def _required_child(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(tag)
    if child is None:
        raise Ai4PdeCaseXmlError([f"<{parent.tag}> missing required child <{tag}>"])
    return child


def _build_physics_spec(problem: ET.Element) -> dict[str, Any]:
    equation = _required_child(problem, "Equation")
    return {
        "equation": {
            "system": equation.attrib.get("system"),
            "form": equation.attrib.get("form"),
            "expression": equation.attrib.get("expression"),
            "stationary": _parse_bool(equation.attrib.get("stationary"), default=False),
            "domain_dim": int(problem.attrib["domainDim"]),
            "space_dim": int(problem.attrib["spaceDim"]),
        },
        "variables": [variable.text or "" for variable in problem.findall("./Variables/V")],
        "parameters": {
            parameter.attrib["name"]: parameter.text or ""
            for parameter in problem.findall("./Parameters/P")
            if parameter.attrib.get("name")
        },
        "initial_conditions": [
            {
                "var": field.attrib["var"],
                "value": field.attrib.get("value"),
                "file": field.attrib.get("file"),
            }
            for field in problem.findall("./InitialConditions/F")
            if field.attrib.get("var")
        ],
        "boundary_conditions": [
            {
                "name": region.attrib["name"],
                "selector": region.attrib.get("selector"),
                "conditions": [
                    {
                        "kind": boundary.attrib["kind"],
                        "var": boundary.attrib["var"],
                        "value": boundary.attrib.get("value"),
                        "file": boundary.attrib.get("file"),
                    }
                    for boundary in region.findall("BC")
                    if boundary.attrib.get("kind") and boundary.attrib.get("var")
                ],
            }
            for region in problem.findall("./BoundaryConditions/Region")
            if region.attrib.get("name")
        ],
        "reference": _build_reference(problem.find("Reference")),
    }


def _build_reference(reference: ET.Element | None) -> dict[str, str | None] | None:
    if reference is None:
        return None
    return {
        "kind": reference.attrib.get("kind"),
        "source": reference.attrib.get("source"),
        "metric": reference.attrib.get("metric"),
    }


def _build_geometry_spec(geometry: ET.Element | None, *, base_dir: Path | None) -> dict[str, Any]:
    if geometry is None:
        return {}
    domain = geometry.find("Domain")
    mesh = geometry.find("Mesh")
    mesh_file = None if mesh is None else mesh.attrib.get("file")
    resolved_mesh_file = (
        str(_resolve_case_path(mesh_file, base_dir))
        if mesh_file is not None and base_dir is not None
        else mesh_file
    )
    return {
        "representation": geometry.attrib.get("representation"),
        "domain": None
        if domain is None
        else {"shape": domain.attrib.get("shape"), "bounds": domain.attrib.get("bounds")},
        "mesh": None
        if mesh is None
        else {
            "source": mesh.attrib.get("source"),
            "file": resolved_mesh_file,
            "format": mesh.attrib.get("format"),
            "element_type": mesh.attrib.get("elementType"),
            "curved": _parse_optional_bool(mesh.attrib.get("curved")),
        },
    }


def _build_budget(execution: ET.Element | None) -> BudgetRecord:
    resources = None if execution is None else execution.find("Resources")
    return BudgetRecord(
        gpu_hours=_parse_float(None if resources is None else resources.attrib.get("gpuHours")),
        cpu_hours=_parse_float(None if resources is None else resources.attrib.get("cpuHours")),
        walltime_hours=_parse_float(
            None if resources is None else resources.attrib.get("walltimeHours")
        ),
        hpc_quota=_parse_float(None if resources is None else resources.attrib.get("hpcQuota")),
    )


def _build_runtime_metadata(runtime: ET.Element | None, *, base_dir: Path | None) -> dict[str, Any]:
    if runtime is None:
        return {}
    required_components = [
        component.strip()
        for component in runtime.attrib.get("requiredComponents", "").split(",")
        if component.strip()
    ]
    graph_template = runtime.attrib.get("graphTemplate")
    manifest_dir = runtime.attrib.get("manifestDir")
    output_dir = runtime.attrib.get("outputDir")
    metadata: dict[str, Any] = {"required_components": required_components}
    if graph_template is not None:
        metadata["graph_template"] = str(
            _resolve_case_path(graph_template, base_dir, search_examples=True)
            if base_dir is not None
            else Path(graph_template)
        )
    if manifest_dir is not None:
        metadata["manifest_dir"] = str(
            _resolve_case_path(manifest_dir, base_dir, search_examples=True)
            if base_dir is not None
            else Path(manifest_dir)
        )
    if output_dir is not None:
        metadata["output_dir"] = str(
            _resolve_case_path(output_dir, base_dir) if base_dir is not None else Path(output_dir)
        )
    return metadata


def _build_data_spec(
    validation: ET.Element | None,
    visualization: ET.Element | None,
    execution: ET.Element | None,
    runtime_metadata: dict[str, Any],
) -> dict[str, Any]:
    constraints = [
        {"kind": constraint.attrib["kind"], "target": constraint.attrib.get("target")}
        for constraint in ([] if validation is None else validation.findall("Constraint"))
        if constraint.attrib.get("kind")
    ]
    residual = None
    if validation is not None:
        residual_node = validation.find("Residual")
        if residual_node is not None:
            residual = {
                "metric": residual_node.attrib.get("metric"),
                "target": residual_node.attrib.get("target"),
            }
    checkpoint = None if execution is None else execution.find("Checkpoint")
    return {
        "validation": {"residual": residual, "constraints": constraints},
        "visualization": _build_visualization_spec(visualization),
        "checkpoint": {
            "enabled": _parse_bool(
                None if checkpoint is None else checkpoint.attrib.get("enabled")
            ),
            "frequency": _parse_optional_int(
                None if checkpoint is None else checkpoint.attrib.get("frequency")
            ),
        },
        "runtime": runtime_metadata,
    }


def _build_visualization_spec(visualization: ET.Element | None) -> dict[str, Any]:
    if visualization is None:
        return {"field_outputs": [], "probes": [], "derived_fields": [], "plots": []}
    return {
        "field_outputs": [
            {
                "format": output.attrib["format"],
                "frequency": _parse_optional_int(output.attrib.get("frequency")),
                "file": output.attrib.get("file"),
            }
            for output in visualization.findall("FieldOutput")
            if output.attrib.get("format")
        ],
        "probes": [
            {
                "name": probe.attrib["name"],
                "point": probe.attrib.get("point"),
                "line": probe.attrib.get("line"),
                "plane": probe.attrib.get("plane"),
                "box": probe.attrib.get("box"),
            }
            for probe in visualization.findall("Probe")
            if probe.attrib.get("name")
        ],
        "derived_fields": [
            derived.attrib["name"]
            for derived in visualization.findall("DerivedField")
            if derived.attrib.get("name")
        ],
        "plots": [
            plot.attrib["type"] for plot in visualization.findall("Plot") if plot.attrib.get("type")
        ],
    }


def _build_plan(
    *,
    case_id: str,
    solver: ET.Element,
    geometry: ET.Element | None,
    discretization: ET.Element,
    validation: ET.Element | None,
    visualization: ET.Element | None,
    adaptivity: ET.Element | None,
    runtime_metadata: dict[str, Any],
    reference: dict[str, str | None] | None,
) -> PDEPlan:
    selected_method = SolverFamily(solver.attrib["family"])
    template_id = solver.attrib.get("templateId")
    runtime_graph_template = runtime_metadata.get("graph_template")
    graph_family = "ai4pde-minimal"
    if template_id:
        graph_family = f"template::{template_id}"
    elif runtime_graph_template:
        graph_family = Path(str(runtime_graph_template)).stem
    parameter_overrides = {
        "backend": solver.attrib.get("backend"),
        "nektar_solver": solver.attrib.get("nektarSolver"),
        "driver": solver.attrib.get("driver"),
        "space": _build_space_overrides(discretization.find("Space")),
        "time_integration": _build_time_integration_overrides(
            discretization.find("TimeIntegration")
        ),
        "linear_solver": _build_linear_solver_overrides(discretization.find("LinearSolver")),
        "mesh": _build_mesh_overrides(geometry),
        "adaptivity": _build_adaptivity_overrides(adaptivity),
        "runtime": runtime_metadata,
    }
    if reference is not None:
        parameter_overrides["reference"] = reference
    return PDEPlan(
        plan_id=f"plan-{case_id}",
        task_id=case_id,
        selected_method=selected_method,
        template_id=template_id,
        graph_family=graph_family,
        slot_bindings=_build_slot_bindings(selected_method, solver.attrib.get("backend")),
        parameter_overrides=parameter_overrides,
        required_validators=_build_required_validators(validation, reference=reference),
        expected_artifacts=_build_expected_artifacts(visualization),
    )


def _build_space_overrides(space: ET.Element | None) -> dict[str, Any]:
    return {
        "projection": None if space is None else space.attrib.get("projection"),
        "basis": None if space is None else space.attrib.get("basis"),
        "order": _parse_optional_int(None if space is None else space.attrib.get("order")),
        "quadrature": None if space is None else space.attrib.get("quadrature"),
    }


def _build_time_integration_overrides(time_integration: ET.Element | None) -> dict[str, Any]:
    return {
        "method": None if time_integration is None else time_integration.attrib.get("method"),
        "variant": None if time_integration is None else time_integration.attrib.get("variant"),
        "order": _parse_optional_int(
            None if time_integration is None else time_integration.attrib.get("order")
        ),
    }


def _build_linear_solver_overrides(linear_solver: ET.Element | None) -> dict[str, Any]:
    return {
        "type": None if linear_solver is None else linear_solver.attrib.get("type"),
        "preconditioner": None
        if linear_solver is None
        else linear_solver.attrib.get("preconditioner"),
        "tolerance": None if linear_solver is None else linear_solver.attrib.get("tolerance"),
    }


def _build_mesh_overrides(geometry: ET.Element | None) -> dict[str, Any]:
    mesh = None if geometry is None else geometry.find("Mesh")
    return {
        "source": None if mesh is None else mesh.attrib.get("source"),
        "file": None if mesh is None else mesh.attrib.get("file"),
        "format": None if mesh is None else mesh.attrib.get("format"),
        "element_type": None if mesh is None else mesh.attrib.get("elementType"),
        "curved": _parse_optional_bool(None if mesh is None else mesh.attrib.get("curved")),
    }


def _build_adaptivity_overrides(adaptivity: ET.Element | None) -> dict[str, Any]:
    return {
        "strategy": None if adaptivity is None else adaptivity.attrib.get("strategy"),
        "target_error": None if adaptivity is None else adaptivity.attrib.get("targetError"),
        "max_iters": _parse_optional_int(
            None if adaptivity is None else adaptivity.attrib.get("maxIters")
        ),
        "stagnation_limit": _parse_optional_int(
            None if adaptivity is None else adaptivity.attrib.get("stagnationLimit")
        ),
    }


def _build_slot_bindings(
    solver_family: SolverFamily,
    backend: str | None,
) -> dict[str, str]:
    bindings = {
        SOLVER_EXECUTOR_SLOT: solver_family.value,
        REFERENCE_SOLVER_SLOT: SolverFamily.CLASSICAL_HYBRID.value,
    }
    if solver_family == SolverFamily.CLASSICAL_HYBRID and backend == "nektar++":
        bindings[KNOWLEDGE_ADAPTER_SLOT] = "nektar_case_library"
    return bindings


def _build_required_validators(
    validation: ET.Element | None,
    *,
    reference: dict[str, str | None] | None,
) -> list[str]:
    validators: list[str] = []
    if validation is not None and validation.find("Residual") is not None:
        validators.append("residuals")
    if validation is not None:
        constraints = [
            constraint.attrib.get("kind") for constraint in validation.findall("Constraint")
        ]
        if "boundary_consistency" in constraints:
            validators.append("boundary_consistency")
        if any(kind in _CONSERVATION_KINDS for kind in constraints):
            validators.append("conservation")
    validators.append("boundary_conditions")
    if reference is not None:
        validators.append("reference_compare")
    return _unique(validators)


def _build_deliverables(visualization: ET.Element | None) -> list[str]:
    deliverables = ["solution_field", "validation_summary", "evidence_bundle"]
    if visualization is None:
        return deliverables
    for output in visualization.findall("FieldOutput"):
        deliverables.append(_field_artifact_name(output.attrib.get("format")))
    for plot in visualization.findall("Plot"):
        plot_type = plot.attrib.get("type")
        if plot_type:
            deliverables.append(plot_type)
    for derived in visualization.findall("DerivedField"):
        name = derived.attrib.get("name")
        if name:
            deliverables.append(f"derived_field/{name}")
    return _unique(deliverables)


def _build_expected_artifacts(visualization: ET.Element | None) -> list[str]:
    artifacts = ["solution_field", "validation_bundle", "evidence_bundle"]
    if visualization is None:
        return artifacts
    for output in visualization.findall("FieldOutput"):
        artifacts.append(_field_artifact_name(output.attrib.get("format")))
    for plot in visualization.findall("Plot"):
        plot_type = plot.attrib.get("type")
        if plot_type:
            artifacts.append(plot_type)
    for derived in visualization.findall("DerivedField"):
        name = derived.attrib.get("name")
        if name:
            artifacts.append(f"derived_field/{name}")
    return _unique(artifacts)


def _field_artifact_name(output_format: str | None) -> str:
    if output_format == "vtu":
        return "vtu_field"
    if output_format == "png":
        return "png_snapshot"
    if output_format:
        return f"{output_format}_field"
    return "field_output"


def _extract_domain_shape(geometry: ET.Element | None) -> str:
    if geometry is None:
        return "unknown"
    domain = geometry.find("Domain")
    if domain is None:
        return "unknown"
    return domain.attrib.get("shape") or "unknown"


def _resolve_case_path(
    raw_path: str | None,
    base_dir: Path | None,
    *,
    search_examples: bool = False,
) -> Path:
    if raw_path is None:
        return Path()
    path = Path(raw_path)
    if path.is_absolute() or base_dir is None:
        return path.resolve(strict=False)
    direct = (base_dir / path).resolve(strict=False)
    if direct.exists() or not search_examples:
        return direct
    for parent in [base_dir, *base_dir.parents]:
        candidate = (parent / path).resolve(strict=False)
        if candidate.exists():
            return candidate
        candidate = (parent / "examples" / path).resolve(strict=False)
        if candidate.exists():
            return candidate
    return direct


def _parse_risk_level(execution: ET.Element | None) -> RiskLevel:
    if execution is None or execution.attrib.get("riskLevel") is None:
        return RiskLevel.GREEN
    return RiskLevel(execution.attrib["riskLevel"])


def _parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value in {"true", "1", "True"}


def _parse_optional_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    return _parse_bool(value)


def _parse_float(value: str | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
