from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from metaharness_ext.nektar.contracts import NektarBoundaryCondition, NektarSessionPlan
from metaharness_ext.nektar.types import NektarBoundaryConditionType, NektarSolverFamily


def _normalize_composite_id(composite_id: str) -> str:
    text = str(composite_id).strip()
    if text.startswith("C["):
        return text
    return f"C[{text}]"


def _normalize_region_ref(region: str) -> str:
    text = str(region).strip()
    if text.startswith("B[") and text.endswith("]"):
        return text[2:-1]
    return text


def _normalize_output_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)


def _indent_xml(element: ET.Element) -> None:
    ET.indent(element, space="    ")


def _validate_renderable(plan: NektarSessionPlan) -> None:
    if plan.solver_family not in {NektarSolverFamily.ADR, NektarSolverFamily.INCNS}:
        raise NotImplementedError(f"Unsupported solver family: {plan.solver_family}")
    if plan.global_system_solution_info:
        raise NotImplementedError("GLOBALSYSSOLNINFO is not supported in Phase 1 renderer")
    if not plan.render_geometry_inline and not plan.mesh.source_path:
        raise ValueError("External mesh overlay mode requires mesh.source_path")
    if not plan.boundary_regions:
        raise ValueError("Nektar session rendering requires boundary_regions")
    if not plan.variables:
        raise ValueError("Nektar session rendering requires variables")
    if not plan.expansions:
        raise ValueError("Nektar session rendering requires expansions")


def _render_geometry(plan: NektarSessionPlan) -> ET.Element:
    geometry = plan.mesh.geometry
    geometry_element = ET.Element(
        "GEOMETRY",
        {
            "DIM": str(geometry.dimension),
            "SPACE": str(geometry.space_dimension or geometry.dimension),
        },
    )

    if geometry.vertices:
        vertex_element = ET.SubElement(geometry_element, "VERTEX")
        for vertex in geometry.vertices:
            coords = vertex.get("coords", vertex.get("points", vertex.get("value", [])))
            child = ET.SubElement(vertex_element, "V", {"ID": str(vertex["id"])})
            child.text = vertex.get("text", _normalize_output_text(coords))

    if geometry.edges:
        edge_element = ET.SubElement(geometry_element, "EDGE")
        for edge in geometry.edges:
            vertices = edge.get("vertices", edge.get("value", []))
            child = ET.SubElement(edge_element, "E", {"ID": str(edge["id"])})
            child.text = edge.get("text", _normalize_output_text(vertices))

    if geometry.faces:
        face_element = ET.SubElement(geometry_element, "FACE")
        for face in geometry.faces:
            tag = str(face.get("tag", face.get("type", "T")))
            child = ET.SubElement(face_element, tag, {"ID": str(face["id"])})
            child.text = face.get("text", _normalize_output_text(face.get("entities", [])))

    if geometry.elements:
        element_element = ET.SubElement(geometry_element, "ELEMENT")
        for item in geometry.elements:
            tag = str(item.get("type", item.get("tag", "Q")))
            child = ET.SubElement(element_element, tag, {"ID": str(item["id"])})
            child.text = item.get(
                "text",
                _normalize_output_text(
                    item.get("edges", item.get("faces", item.get("vertices", [])))
                ),
            )

    if geometry.curved:
        curved_element = ET.SubElement(geometry_element, "CURVED")
        for item in geometry.curved:
            child = ET.SubElement(curved_element, "E", {"ID": str(item["id"])})
            child.text = item.get("text", _normalize_output_text(item.get("data", [])))

    if geometry.composites:
        composite_element = ET.SubElement(geometry_element, "COMPOSITE")
        for composite in geometry.composites:
            child = ET.SubElement(composite_element, "C", {"ID": str(composite["id"])})
            child.text = str(composite.get("text", "")).strip() or _normalize_output_text(
                composite.get("items", [])
            )

    if geometry.domain:
        domain_element = ET.SubElement(geometry_element, "DOMAIN")
        domain_element.text = " ".join(str(item) for item in geometry.domain)

    return geometry_element


def _render_expansions(plan: NektarSessionPlan) -> ET.Element:
    expansions_element = ET.Element("EXPANSIONS")
    for expansion in plan.expansions:
        if not isinstance(expansion.num_modes, int):
            raise NotImplementedError("Phase 1 renderer only supports integer NUMMODES")
        attributes = {
            "COMPOSITE": ",".join(
                _normalize_composite_id(item) for item in expansion.composite_ids
            ),
            "NUMMODES": str(expansion.num_modes),
            "FIELDS": expansion.field,
            "TYPE": expansion.basis_type,
        }
        if expansion.points_type is not None:
            attributes["POINTSTYPE"] = expansion.points_type
        if expansion.homogeneous_length is not None:
            attributes["HOMOGENEOUSLENGTH"] = str(expansion.homogeneous_length)
        ET.SubElement(expansions_element, "E", attributes)
    return expansions_element


def _render_parameters(plan: NektarSessionPlan) -> ET.Element:
    parameters_element = ET.Element("PARAMETERS")
    for name, value in plan.parameters.items():
        child = ET.SubElement(parameters_element, "P")
        child.text = f"{name} = {value}"
    return parameters_element


def _render_time_integration(plan: NektarSessionPlan) -> ET.Element:
    time_integration = ET.Element("TIMEINTEGRATIONSCHEME")
    for tag, value in plan.time_integration.items():
        child = ET.SubElement(time_integration, str(tag))
        child.text = str(value)
    return time_integration


def _render_solver_info(plan: NektarSessionPlan) -> ET.Element:
    solver_info_element = ET.Element("SOLVERINFO")
    for name, value in plan.solver_info.items():
        ET.SubElement(solver_info_element, "I", {"PROPERTY": name, "VALUE": str(value)})
    return solver_info_element


def _render_variables(plan: NektarSessionPlan) -> ET.Element:
    variables_element = ET.Element("VARIABLES")
    for index, variable in enumerate(plan.variables):
        child = ET.SubElement(variables_element, "V", {"ID": str(index)})
        child.text = variable
    return variables_element


def _render_boundary_regions(plan: NektarSessionPlan) -> ET.Element:
    regions_element = ET.Element("BOUNDARYREGIONS")
    for region in plan.boundary_regions:
        child = ET.SubElement(regions_element, "B", {"ID": str(region["id"])})
        child.text = str(region["composite"])
    return regions_element


def _render_bc_entry(region_element: ET.Element, condition: NektarBoundaryCondition) -> None:
    attributes = {"VAR": condition.field}
    if condition.value is not None:
        attributes["VALUE"] = condition.value
    if condition.user_defined_type is not None:
        attributes["USERDEFINEDTYPE"] = condition.user_defined_type
    if condition.condition_type == NektarBoundaryConditionType.ROBIN:
        attributes["PRIMCOEFF"] = str(condition.prim_coeff)
    ET.SubElement(region_element, condition.condition_type.value, attributes)


def _render_boundary_conditions(plan: NektarSessionPlan) -> ET.Element:
    boundary_conditions_element = ET.Element("BOUNDARYCONDITIONS")
    grouped: dict[str, list[NektarBoundaryCondition]] = {}
    for condition in plan.boundary_conditions:
        region_ref = _normalize_region_ref(condition.region)
        grouped.setdefault(region_ref, []).append(condition)
    for region in plan.boundary_regions:
        region_id = str(region["id"])
        region_element = ET.SubElement(boundary_conditions_element, "REGION", {"REF": region_id})
        for condition in grouped.get(region_id, []):
            _render_bc_entry(region_element, condition)
    return boundary_conditions_element


def _render_functions(plan: NektarSessionPlan) -> list[ET.Element]:
    function_elements: list[ET.Element] = []
    for function in plan.functions:
        function_element = ET.Element("FUNCTION", {"NAME": str(function["name"])})
        for expression in function.get("expressions", []):
            attributes = {"VAR": str(expression["var"]), "VALUE": str(expression["value"])}
            if "evars" in expression:
                attributes["EVARS"] = str(expression["evars"])
            ET.SubElement(function_element, "E", attributes)
        if "file_ref" in function:
            attributes = {
                "VAR": str(function.get("vars", ",".join(plan.variables))),
                "FILE": str(function["file_ref"]),
            }
            ET.SubElement(function_element, "F", attributes)
        function_elements.append(function_element)
    return function_elements


def _render_forcing(plan: NektarSessionPlan) -> ET.Element:
    forcing_element = ET.Element("FORCING")
    for forcing in plan.forcing:
        force_element = ET.SubElement(forcing_element, "FORCE", {"TYPE": str(forcing["type"])})
        body_force = ET.SubElement(force_element, "BODYFORCE")
        body_force.text = str(forcing["body_force"])
    return forcing_element


def _render_filters(plan: NektarSessionPlan) -> ET.Element:
    filters_element = ET.Element("FILTERS")
    for filter_spec in plan.filters:
        filter_element = ET.SubElement(
            filters_element,
            "FILTER",
            {"TYPE": str(filter_spec.get("type", filter_spec.get("name", "Unknown")))},
        )
        for name, value in filter_spec.get("parameters", {}).items():
            parameter = ET.SubElement(filter_element, "PARAM", {"NAME": str(name)})
            parameter.text = str(value)
    return filters_element


def render_session_element(plan: NektarSessionPlan) -> ET.Element:
    _validate_renderable(plan)
    root = ET.Element("NEKTAR")
    if plan.render_geometry_inline:
        root.append(_render_geometry(plan))
    root.append(_render_expansions(plan))
    if plan.forcing:
        root.append(_render_forcing(plan))

    conditions = ET.Element("CONDITIONS")
    conditions.append(_render_parameters(plan))
    if plan.time_integration:
        conditions.append(_render_time_integration(plan))
    conditions.append(_render_solver_info(plan))
    conditions.append(_render_variables(plan))
    conditions.append(_render_boundary_regions(plan))
    conditions.append(_render_boundary_conditions(plan))
    for function_element in _render_functions(plan):
        conditions.append(function_element)
    root.append(conditions)

    if plan.filters:
        root.append(_render_filters(plan))
    return root


def render_session_xml(plan: NektarSessionPlan) -> str:
    root = render_session_element(plan)
    _indent_xml(root)
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def write_session_xml(plan: NektarSessionPlan, path: str | Path) -> Path:
    target = Path(path)
    xml_text = render_session_xml(plan)
    target.write_text(xml_text)
    return target
