import xml.etree.ElementTree as ET

from metaharness_ext.nektar import build_session_plan, render_session_xml
from metaharness_ext.nektar.contracts import NektarBoundaryCondition, NektarProblemSpec
from metaharness_ext.nektar.types import (
    NektarAdrEqType,
    NektarBoundaryConditionType,
    NektarIncnsEqType,
    NektarIncnsSolverType,
    NektarSolverFamily,
)


def test_build_session_plan_adr_populates_render_fields() -> None:
    problem = NektarProblemSpec(
        task_id="task-adr",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
        boundary_conditions=[
            NektarBoundaryCondition(
                region="0",
                field="u",
                condition_type=NektarBoundaryConditionType.DIRICHLET,
                value="0",
            )
        ],
    )

    plan = build_session_plan(problem)

    assert plan.solver_binary == "ADRSolver"
    assert plan.equation_type == NektarAdrEqType.HELMHOLTZ
    assert plan.render_geometry_inline is True
    assert plan.boundary_regions
    assert plan.session_file_name == "session.xml"
    assert plan.expected_outputs[0] == "session.xml"
    assert plan.graph_metadata["graph_family"] == "nektar-minimal"
    assert plan.execution_policy.sandbox_profile == "workspace-write"
    assert "ADRSolver" in plan.execution_policy.required_binaries
    assert plan.provenance_refs[-1] == "provenance://nektar/problem/task-adr"


def test_build_session_plan_incns_uses_family_defaults() -> None:
    problem = NektarProblemSpec(
        task_id="task-incns",
        title="incns",
        solver_family=NektarSolverFamily.INCNS,
        dimension=2,
        variables=["u", "v", "p"],
        domain={"mesh_path": "channel.xml"},
    )

    plan = build_session_plan(problem)

    assert plan.equation_type == NektarIncnsEqType.UNSTEADY_NAVIER_STOKES
    assert plan.solver_binary == "IncNavierStokesSolver"
    assert plan.solver_type == NektarIncnsSolverType.VELOCITY_CORRECTION
    assert plan.render_geometry_inline is False
    assert plan.mesh.source_path == "channel.xml"
    assert plan.time_integration == {"METHOD": "IMEX", "ORDER": 1}


def test_build_session_plan_and_render_session_xml_are_connected() -> None:
    problem = NektarProblemSpec(
        task_id="task-render",
        title="reaction diffusion",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
        forcing=[
            {
                "mode": "top_level",
                "type": "Body",
                "body_force": "BodyForce",
                "expressions": [{"var": "u", "value": "0.1*u", "evars": "u"}],
            }
        ],
        reference={"expressions": [{"var": "u", "value": "sin(x)"}]},
    )

    plan = build_session_plan(problem)
    root = ET.fromstring(render_session_xml(plan))

    assert root.tag == "NEKTAR"
    assert root.find("EXPANSIONS") is not None
    assert root.find("FORCING/FORCE/BODYFORCE").text == "BodyForce"
    assert root.find("CONDITIONS/FUNCTION[@NAME='BodyForce']") is not None
    assert root.find("CONDITIONS/FUNCTION[@NAME='ExactSolution']") is not None


def test_build_session_plan_uses_default_postprocess_when_not_provided() -> None:
    problem = NektarProblemSpec(
        task_id="task-default-pp",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )

    plan = build_session_plan(problem)

    assert plan.postprocess_plan == [{"type": "fieldconvert", "output": "solution.vtu"}]


def test_build_session_plan_uses_user_postprocess_plan() -> None:
    problem = NektarProblemSpec(
        task_id="task-custom-pp",
        title="incns",
        solver_family=NektarSolverFamily.INCNS,
        dimension=2,
        variables=["u", "v", "p"],
        domain={"mesh_path": "channel.xml"},
        postprocess_plan=[
            {"type": "fieldconvert", "output": "solution.vtu"},
            {"type": "fieldconvert", "output": "vorticity.fld", "module": "vorticity"},
        ],
    )

    plan = build_session_plan(problem)

    assert len(plan.postprocess_plan) == 2
    assert plan.postprocess_plan[0] == {"type": "fieldconvert", "output": "solution.vtu"}
    assert plan.postprocess_plan[1] == {
        "type": "fieldconvert",
        "output": "vorticity.fld",
        "module": "vorticity",
    }
    assert "FieldConvert" in plan.execution_policy.required_binaries


def test_build_session_plan_preserves_candidate_and_provenance_metadata() -> None:
    problem = NektarProblemSpec(
        task_id="task-metadata",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
        graph_metadata={"graph_family": "nektar-promotion", "candidate_stage": "screening"},
        candidate_identity={"candidate_id": "cand-23", "graph_version_id": 7, "actor": "planner"},
        promotion_metadata={"outcome": "pending", "details": {"source_task": 23}},
        checkpoint_refs=["checkpoint://nektar/task-metadata/base"],
        provenance_refs=["provenance://seed/task-metadata"],
    )

    plan = build_session_plan(problem)

    assert plan.graph_metadata["graph_family"] == "nektar-promotion"
    assert plan.graph_metadata["candidate_stage"] == "screening"
    assert plan.candidate_identity.candidate_id == "cand-23"
    assert plan.candidate_identity.graph_version_id == 7
    assert plan.promotion_metadata.details["source_task"] == 23
    assert plan.checkpoint_refs == ["checkpoint://nektar/task-metadata/base"]
    assert plan.provenance_refs == [
        "provenance://seed/task-metadata",
        "provenance://nektar/problem/task-metadata",
    ]
