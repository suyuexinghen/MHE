from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.capabilities import CAP_NEKTAR_CASE_COMPILE, CAP_NEKTAR_MESH_PREPARE
from metaharness_ext.nektar.contracts import (
    NektarBoundaryCondition,
    NektarExpansionSpec,
    NektarGeometrySection,
    NektarMeshSpec,
    NektarProblemSpec,
    NektarSessionPlan,
)
from metaharness_ext.nektar.slots import SESSION_COMPILER_SLOT
from metaharness_ext.nektar.types import (
    NektarAdrEqType,
    NektarBoundaryConditionType,
    NektarGeometryMode,
    NektarIncnsEqType,
    NektarIncnsSolverType,
    NektarProjection,
    NektarSolverFamily,
)
from metaharness_ext.nektar.xml_renderer import render_session_xml


def _default_equation_type(
    problem: NektarProblemSpec,
) -> NektarAdrEqType | NektarIncnsEqType:
    if problem.equation_type is not None:
        return problem.equation_type
    if problem.solver_family == NektarSolverFamily.ADR:
        return NektarAdrEqType.HELMHOLTZ
    if problem.solver_family == NektarSolverFamily.INCNS:
        return NektarIncnsEqType.UNSTEADY_NAVIER_STOKES
    raise NotImplementedError(f"Unsupported solver family: {problem.solver_family}")


def _default_time_integration(
    equation_type: NektarAdrEqType | NektarIncnsEqType,
) -> dict[str, object]:
    if equation_type in {
        NektarAdrEqType.UNSTEADY_ADVECTION_DIFFUSION,
        NektarAdrEqType.UNSTEADY_REACTION_DIFFUSION,
    }:
        return {"METHOD": "IMEX", "ORDER": 3}
    if equation_type in {
        NektarIncnsEqType.UNSTEADY_STOKES,
        NektarIncnsEqType.UNSTEADY_NAVIER_STOKES,
    }:
        return {"METHOD": "IMEX", "ORDER": 1}
    return {}


def _normalize_region_id(region: str) -> str:
    text = region.strip()
    if text.startswith("B[") and text.endswith("]"):
        return text[2:-1]
    return text


def _default_geometry(problem: NektarProblemSpec) -> NektarGeometrySection:
    if problem.dimension != 2:
        raise NotImplementedError("Phase 1 inline geometry defaults only support 2D cases")
    return NektarGeometrySection(
        dimension=2,
        space_dimension=problem.space_dimension or 2,
        vertices=[
            {"id": 0, "coords": [0.0, 0.0, 0.0]},
            {"id": 1, "coords": [1.0, 0.0, 0.0]},
            {"id": 2, "coords": [1.0, 1.0, 0.0]},
            {"id": 3, "coords": [0.0, 1.0, 0.0]},
        ],
        edges=[
            {"id": 0, "vertices": [0, 1]},
            {"id": 1, "vertices": [1, 2]},
            {"id": 2, "vertices": [2, 3]},
            {"id": 3, "vertices": [3, 0]},
        ],
        elements=[{"id": 0, "type": "Q", "edges": [0, 1, 2, 3]}],
        composites=[
            {"id": 0, "text": "Q[0]"},
            {"id": 1, "text": "E[0]"},
            {"id": 2, "text": "E[1]"},
            {"id": 3, "text": "E[2]"},
            {"id": 4, "text": "E[3]"},
        ],
        domain=["C[0]"],
    )


def _default_variables(problem: NektarProblemSpec) -> list[str]:
    if problem.variables:
        return list(problem.variables)
    if problem.solver_family == NektarSolverFamily.INCNS:
        return ["u", "v", "p"]
    return ["u"]


def _default_boundary_conditions(variables: list[str]) -> list[NektarBoundaryCondition]:
    return [
        NektarBoundaryCondition(
            region="0",
            field=variable,
            condition_type=NektarBoundaryConditionType.DIRICHLET,
            value="0",
        )
        for variable in variables
    ]


def _build_boundary_regions(
    geometry: NektarGeometrySection,
    boundary_conditions: list[NektarBoundaryCondition],
) -> list[dict[str, str]]:
    region_ids: list[str] = []
    for condition in boundary_conditions:
        region_id = _normalize_region_id(condition.region)
        if region_id not in region_ids:
            region_ids.append(region_id)
    if not region_ids:
        region_ids.append("0")

    available_boundary_composites = [
        composite for composite in geometry.composites if int(composite["id"]) != 0
    ]
    if available_boundary_composites and len(region_ids) > len(available_boundary_composites):
        raise NotImplementedError("Default inline geometry only supports up to 4 boundary regions")

    boundary_regions: list[dict[str, str]] = []
    for index, region_id in enumerate(region_ids):
        if available_boundary_composites:
            composite_id = str(available_boundary_composites[index]["id"])
            composite = f"C[{composite_id}]"
        else:
            composite = f"C[{index + 1}]"
        boundary_regions.append({"id": region_id, "composite": composite})
    return boundary_regions


def _build_functions(problem: NektarProblemSpec, variables: list[str]) -> list[dict[str, object]]:
    functions: list[dict[str, object]] = []
    if problem.initial_conditions:
        functions.append(
            {
                "name": "InitialConditions",
                "expressions": [dict(entry) for entry in problem.initial_conditions],
            }
        )
    elif problem.solver_family == NektarSolverFamily.INCNS:
        functions.append(
            {
                "name": "InitialConditions",
                "expressions": [{"var": var, "value": "0"} for var in variables],
            }
        )

    if problem.reference:
        if "file_ref" in problem.reference:
            functions.append(
                {
                    "name": "ExactSolution",
                    "file_ref": str(problem.reference["file_ref"]),
                    "vars": ",".join(variables),
                }
            )
        elif "expressions" in problem.reference:
            functions.append(
                {
                    "name": "ExactSolution",
                    "expressions": [dict(entry) for entry in problem.reference["expressions"]],
                }
            )

    for forcing in problem.forcing:
        mode = forcing.get("mode", "function")
        if mode == "function":
            functions.append(
                {
                    "name": forcing.get("name", "Forcing"),
                    "expressions": [dict(entry) for entry in forcing.get("expressions", [])],
                }
            )
        elif mode == "top_level" and forcing.get("expressions"):
            functions.append(
                {
                    "name": forcing.get("body_force", forcing.get("name", "BodyForce")),
                    "expressions": [dict(entry) for entry in forcing.get("expressions", [])],
                }
            )
    return functions


def _build_top_level_forcing(problem: NektarProblemSpec) -> list[dict[str, str]]:
    forcing_blocks: list[dict[str, str]] = []
    for forcing in problem.forcing:
        if forcing.get("mode") != "top_level":
            continue
        forcing_blocks.append(
            {
                "type": str(forcing.get("type", "Body")),
                "body_force": str(forcing.get("body_force", forcing.get("name", "BodyForce"))),
            }
        )
    return forcing_blocks


class SessionCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(SESSION_COMPILER_SLOT)
        api.declare_input("task", "NektarProblemSpec")
        api.declare_output("plan", "NektarSessionPlan", mode="sync")
        api.provide_capability(CAP_NEKTAR_CASE_COMPILE)
        api.provide_capability(CAP_NEKTAR_MESH_PREPARE)

    def build_plan(self, problem: NektarProblemSpec) -> NektarSessionPlan:
        variables = _default_variables(problem)
        equation_type = _default_equation_type(problem)
        if problem.solver_family == NektarSolverFamily.ADR:
            solver_binary = "ADRSolver"
            solver_type = None
            time_integration = _default_time_integration(equation_type)
            solver_info = {
                "EQTYPE": equation_type.value,
                "Projection": NektarProjection.CONTINUOUS.value,
            }
        elif problem.solver_family == NektarSolverFamily.INCNS:
            solver_binary = "IncNavierStokesSolver"
            solver_type = NektarIncnsSolverType.VELOCITY_CORRECTION
            time_integration = _default_time_integration(equation_type)
            solver_info = {
                "SolverType": solver_type.value,
                "EQTYPE": equation_type.value,
                "Projection": NektarProjection.CONTINUOUS.value,
            }
        else:
            raise NotImplementedError(f"Unsupported solver family: {problem.solver_family}")

        geometry_mode = (
            NektarGeometryMode.DIM_3D if problem.dimension == 3 else NektarGeometryMode.DIM_2D
        )
        mesh_path = problem.domain.get("mesh_path") or problem.domain.get("source_path")
        render_geometry_inline = mesh_path is None
        if problem.domain.get("geometry"):
            geometry = NektarGeometrySection.model_validate(problem.domain["geometry"])
            render_geometry_inline = True
        elif render_geometry_inline:
            geometry = _default_geometry(problem)
        else:
            geometry = NektarGeometrySection(
                dimension=problem.dimension,
                space_dimension=problem.space_dimension or problem.dimension,
            )

        mesh = NektarMeshSpec(
            source_mode="existing_xml",
            source_path=str(mesh_path) if mesh_path else None,
            geometry_mode=geometry_mode,
            geometry=geometry,
        )
        boundary_conditions = list(problem.boundary_conditions) or _default_boundary_conditions(variables)
        boundary_regions = _build_boundary_regions(geometry, boundary_conditions)
        functions = _build_functions(problem, variables)
        top_level_forcing = _build_top_level_forcing(problem)
        parameters = dict(problem.parameters)
        if time_integration:
            parameters.setdefault("TimeStep", 0.001)
            parameters.setdefault("NumSteps", 100)
        expansions = [
            NektarExpansionSpec(
                field=",".join(variables),
                composite_ids=["0"],
                basis_type="MODIFIED",
                num_modes=int(problem.parameters.get("NumModes", 4)),
            )
        ]
        session_file_name = str(problem.domain.get("session_file_name", "session.xml"))
        expected_outputs = [session_file_name, "solution.fld"]

        return NektarSessionPlan(
            plan_id=f"plan::{problem.task_id}",
            task_id=problem.task_id,
            solver_family=problem.solver_family,
            solver_binary=solver_binary,
            equation_type=equation_type,
            projection=NektarProjection.CONTINUOUS,
            solver_type=solver_type,
            mesh=mesh,
            variables=variables,
            expansions=expansions,
            solver_info=solver_info,
            parameters=parameters,
            time_integration=time_integration,
            boundary_regions=boundary_regions,
            boundary_conditions=boundary_conditions,
            functions=functions,
            forcing=top_level_forcing,
            filters=list(problem.domain.get("filters", [])),
            expected_outputs=expected_outputs,
            validation_targets=[
                "solver_exited_cleanly",
                "field_files_exist",
                "error_vs_reference",
            ],
            render_geometry_inline=render_geometry_inline,
            session_file_name=session_file_name,
            postprocess_plan=list(problem.postprocess_plan)
            or [{"type": "fieldconvert", "output": "solution.vtu"}],
        )

    def render_session(self, plan: NektarSessionPlan) -> str:
        return render_session_xml(plan)


def build_session_plan(problem: NektarProblemSpec) -> NektarSessionPlan:
    return SessionCompilerComponent().build_plan(problem)
