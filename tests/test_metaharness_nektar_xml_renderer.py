import xml.etree.ElementTree as ET

import pytest

from metaharness_ext.nektar.contracts import (
    NektarBoundaryCondition,
    NektarExpansionSpec,
    NektarGeometrySection,
    NektarMeshSpec,
    NektarSessionPlan,
)
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


def _minimal_geometry() -> NektarGeometrySection:
    return NektarGeometrySection(
        dimension=2,
        space_dimension=2,
        vertices=[
            {"id": 0, "coords": [0.0, 0.0, 0.0]},
            {"id": 1, "coords": [1.0, 0.0, 0.0]},
        ],
        edges=[{"id": 0, "vertices": [0, 1]}],
        composites=[{"id": 0, "text": "E[0]"}, {"id": 1, "text": "E[0]"}],
        domain=["C[0]"],
    )


def test_render_adr_session_uses_normative_section_order() -> None:
    plan = NektarSessionPlan(
        plan_id="plan-adr",
        task_id="task-adr",
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
        equation_type=NektarAdrEqType.HELMHOLTZ,
        projection=NektarProjection.CONTINUOUS,
        mesh=NektarMeshSpec(
            source_mode="existing_xml",
            geometry_mode=NektarGeometryMode.DIM_2D,
            geometry=_minimal_geometry(),
        ),
        variables=["u"],
        expansions=[
            NektarExpansionSpec(field="u", composite_ids=["0"], basis_type="MODIFIED", num_modes=4)
        ],
        solver_info={"EQTYPE": "Helmholtz", "Projection": "Continuous"},
        parameters={"Lambda": 1},
        boundary_regions=[{"id": "0", "composite": "C[1]"}],
        boundary_conditions=[
            NektarBoundaryCondition(
                region="0",
                field="u",
                condition_type=NektarBoundaryConditionType.DIRICHLET,
                value="0",
            )
        ],
        render_geometry_inline=True,
    )

    root = ET.fromstring(render_session_xml(plan))

    assert [child.tag for child in root] == ["GEOMETRY", "EXPANSIONS", "CONDITIONS"]
    assert [child.tag for child in root.find("CONDITIONS")] == [
        "PARAMETERS",
        "SOLVERINFO",
        "VARIABLES",
        "BOUNDARYREGIONS",
        "BOUNDARYCONDITIONS",
    ]


def test_render_incns_unsteady_overlay_omits_geometry_and_includes_timeintegration() -> None:
    plan = NektarSessionPlan(
        plan_id="plan-incns",
        task_id="task-incns",
        solver_family=NektarSolverFamily.INCNS,
        solver_binary="IncNavierStokesSolver",
        equation_type=NektarIncnsEqType.UNSTEADY_NAVIER_STOKES,
        projection=NektarProjection.CONTINUOUS,
        solver_type=NektarIncnsSolverType.VELOCITY_CORRECTION,
        mesh=NektarMeshSpec(
            source_mode="existing_xml",
            source_path="mesh.xml",
            geometry_mode=NektarGeometryMode.DIM_2D,
        ),
        variables=["u", "v", "p"],
        expansions=[
            NektarExpansionSpec(
                field="u,v,p",
                composite_ids=["0"],
                basis_type="MODIFIED",
                num_modes=3,
            )
        ],
        solver_info={
            "SolverType": "VelocityCorrectionScheme",
            "EQTYPE": "UnsteadyNavierStokes",
            "Projection": "Continuous",
        },
        parameters={"TimeStep": 0.001, "NumSteps": 10},
        time_integration={"METHOD": "IMEX", "ORDER": 1},
        boundary_regions=[{"id": "0", "composite": "C[1]"}],
        boundary_conditions=[
            NektarBoundaryCondition(
                region="0",
                field="u",
                condition_type=NektarBoundaryConditionType.DIRICHLET,
                value="0",
            )
        ],
    )

    root = ET.fromstring(render_session_xml(plan))
    conditions = root.find("CONDITIONS")

    assert [child.tag for child in root] == ["EXPANSIONS", "CONDITIONS"]
    assert conditions[1].tag == "TIMEINTEGRATIONSCHEME"


def test_render_robin_boundary_condition_includes_primcoeff() -> None:
    plan = NektarSessionPlan(
        plan_id="plan-robin",
        task_id="task-robin",
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
        equation_type=NektarAdrEqType.HELMHOLTZ,
        projection=NektarProjection.CONTINUOUS,
        mesh=NektarMeshSpec(
            source_mode="existing_xml",
            geometry_mode=NektarGeometryMode.DIM_2D,
            geometry=_minimal_geometry(),
        ),
        variables=["u"],
        expansions=[
            NektarExpansionSpec(field="u", composite_ids=["0"], basis_type="MODIFIED", num_modes=4)
        ],
        solver_info={"EQTYPE": "Helmholtz", "Projection": "Continuous"},
        parameters={"Lambda": 1},
        boundary_regions=[{"id": "1", "composite": "C[1]"}],
        boundary_conditions=[
            NektarBoundaryCondition(
                region="B[1]",
                field="u",
                condition_type=NektarBoundaryConditionType.ROBIN,
                value="sin(x)",
                prim_coeff="1",
            )
        ],
        render_geometry_inline=True,
    )

    root = ET.fromstring(render_session_xml(plan))
    robin = root.find("CONDITIONS/BOUNDARYCONDITIONS/REGION/R")

    assert robin is not None
    assert robin.attrib["PRIMCOEFF"] == "1"


def test_render_supports_top_level_forcing_and_function_forcing_together() -> None:
    plan = NektarSessionPlan(
        plan_id="plan-force",
        task_id="task-force",
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
        equation_type=NektarAdrEqType.UNSTEADY_REACTION_DIFFUSION,
        projection=NektarProjection.CONTINUOUS,
        mesh=NektarMeshSpec(
            source_mode="existing_xml",
            geometry_mode=NektarGeometryMode.DIM_2D,
            geometry=_minimal_geometry(),
        ),
        variables=["u"],
        expansions=[
            NektarExpansionSpec(field="u", composite_ids=["0"], basis_type="MODIFIED", num_modes=4)
        ],
        solver_info={"EQTYPE": "UnsteadyReactionDiffusion", "Projection": "Continuous"},
        parameters={"TimeStep": 0.001},
        time_integration={"METHOD": "IMEX", "ORDER": 1},
        boundary_regions=[{"id": "0", "composite": "C[1]"}],
        boundary_conditions=[
            NektarBoundaryCondition(
                region="0",
                field="u",
                condition_type=NektarBoundaryConditionType.DIRICHLET,
                value="0",
            )
        ],
        functions=[
            {"name": "Forcing", "expressions": [{"var": "u", "value": "sin(x)"}]},
            {"name": "BodyForce", "expressions": [{"var": "u", "value": "0.1*u", "evars": "u"}]},
            {"name": "InitialConditions", "file_ref": "restart.rst", "vars": "u"},
        ],
        forcing=[{"type": "Body", "body_force": "BodyForce"}],
        render_geometry_inline=True,
    )

    root = ET.fromstring(render_session_xml(plan))

    assert root.find("FORCING/FORCE/BODYFORCE").text == "BodyForce"
    function_names = [element.attrib["NAME"] for element in root.findall("CONDITIONS/FUNCTION")]
    assert function_names == ["Forcing", "BodyForce", "InitialConditions"]
    assert root.find("CONDITIONS/FUNCTION/F") is not None


def test_renderer_rejects_globalsyssolninfo_in_phase1() -> None:
    plan = NektarSessionPlan(
        plan_id="plan-bad",
        task_id="task-bad",
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
        equation_type=NektarAdrEqType.HELMHOLTZ,
        mesh=NektarMeshSpec(source_mode="existing_xml", source_path="mesh.xml"),
        variables=["u"],
        expansions=[
            NektarExpansionSpec(field="u", composite_ids=["0"], basis_type="MODIFIED", num_modes=4)
        ],
        solver_info={"EQTYPE": "Helmholtz", "Projection": "Continuous"},
        parameters={"Lambda": 1},
        boundary_regions=[{"id": "0", "composite": "C[1]"}],
        boundary_conditions=[
            NektarBoundaryCondition(
                region="0",
                field="u",
                condition_type=NektarBoundaryConditionType.DIRICHLET,
                value="0",
            )
        ],
        global_system_solution_info={"u": {"solver": "Direct"}},
    )

    with pytest.raises(NotImplementedError, match="GLOBALSYSSOLNINFO"):
        render_session_xml(plan)
