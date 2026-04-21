import pytest

from metaharness_ext.nektar import (
    CANONICAL_CAPABILITIES,
    CAP_NEKTAR_CASE_COMPILE,
    CAP_NEKTAR_CONVERGENCE_STUDY,
    CAP_NEKTAR_MESH_PREPARE,
    ConvergenceStudyComponent,
    ConvergenceStudyReport,
    ConvergenceStudySpec,
    NektarAdrEqType,
    NektarBoundaryCondition,
    NektarBoundaryConditionType,
    NektarGeometrySection,
    NektarIncnsEqType,
    NektarMutationAxis,
    NektarProblemSpec,
    NektarRunArtifact,
    NektarSessionPlan,
    NektarSolverFamily,
    NektarValidationReport,
    SolverExecutorComponent,
    build_session_plan,
    render_session_xml,
    write_session_xml,
)
from metaharness_ext.nektar.contracts import NektarMeshSpec
from metaharness_ext.nektar.types import (
    NektarGeometryMode,
    NektarIncnsSolverType,
    NektarProjection,
)


def test_metaharness_nektar_contracts_round_trip() -> None:
    problem = NektarProblemSpec(
        task_id="task-1",
        title="helmholtz benchmark",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = NektarSessionPlan(
        plan_id="plan-1",
        task_id=problem.task_id,
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
        equation_type=NektarAdrEqType.HELMHOLTZ,
        projection=NektarProjection.CONTINUOUS,
        mesh=NektarMeshSpec(source_mode="existing_xml", geometry_mode=NektarGeometryMode.DIM_2D),
    )
    run_artifact = NektarRunArtifact(
        run_id="run-1",
        task_id=problem.task_id,
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
    )
    validation = NektarValidationReport(task_id=problem.task_id, passed=True)

    assert NektarProblemSpec.model_validate(problem.model_dump()) == problem
    assert NektarSessionPlan.model_validate(plan.model_dump()) == plan
    assert NektarRunArtifact.model_validate(run_artifact.model_dump()) == run_artifact
    assert NektarValidationReport.model_validate(validation.model_dump()) == validation


def test_metaharness_nektar_exports_exist() -> None:
    assert CAP_NEKTAR_CASE_COMPILE in CANONICAL_CAPABILITIES
    assert CAP_NEKTAR_MESH_PREPARE in CANONICAL_CAPABILITIES
    assert CAP_NEKTAR_CONVERGENCE_STUDY in CANONICAL_CAPABILITIES
    assert callable(render_session_xml)
    assert callable(write_session_xml)
    assert SolverExecutorComponent is not None
    assert ConvergenceStudyComponent is not None
    assert ConvergenceStudySpec is not None
    assert ConvergenceStudyReport is not None
    assert NektarMutationAxis is not None


def test_build_session_plan_uses_family_specific_defaults() -> None:
    adr_problem = NektarProblemSpec(
        task_id="task-adr",
        title="adr",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    incns_problem = NektarProblemSpec(
        task_id="task-incns",
        title="incns",
        solver_family=NektarSolverFamily.INCNS,
        dimension=2,
        variables=["u", "v", "p"],
    )

    adr_plan = build_session_plan(adr_problem)
    incns_plan = build_session_plan(incns_problem)

    assert adr_plan.equation_type == NektarAdrEqType.HELMHOLTZ
    assert adr_plan.solver_binary == "ADRSolver"
    assert incns_plan.equation_type == NektarIncnsEqType.UNSTEADY_NAVIER_STOKES
    assert incns_plan.solver_binary == "IncNavierStokesSolver"
    assert incns_plan.solver_type == NektarIncnsSolverType.VELOCITY_CORRECTION


def test_robin_boundary_condition_requires_prim_coeff() -> None:
    with pytest.raises(ValueError, match="prim_coeff"):
        NektarBoundaryCondition(
            region="B[0]",
            field="u",
            condition_type=NektarBoundaryConditionType.ROBIN,
            value="sin(x)",
        )


def test_geometry_section_validates_dimension_constraints() -> None:
    with pytest.raises(ValueError, match="requires edges"):
        NektarGeometrySection(dimension=2, vertices=[{"id": 0}])

    valid = NektarGeometrySection(
        dimension=2,
        space_dimension=2,
        vertices=[{"id": 0}, {"id": 1}],
        edges=[{"id": "E0", "vertices": [0, 1]}],
    )

    assert valid.dimension == 2


def test_session_plan_rejects_family_equation_type_mismatch() -> None:
    with pytest.raises(ValueError, match="IncNS plans require"):
        NektarSessionPlan(
            plan_id="plan-bad",
            task_id="task-bad",
            solver_family=NektarSolverFamily.INCNS,
            solver_binary="IncNavierStokesSolver",
            equation_type=NektarAdrEqType.HELMHOLTZ,
            mesh=NektarMeshSpec(source_mode="existing_xml"),
        )
