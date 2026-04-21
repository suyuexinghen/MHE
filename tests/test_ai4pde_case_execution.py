from pathlib import Path

from metaharness_ext.ai4pde.components.evidence_manager import EvidenceManagerComponent
from metaharness_ext.ai4pde.components.method_router import MethodRouterComponent
from metaharness_ext.ai4pde.components.pde_gateway import PDEGatewayComponent
from metaharness_ext.ai4pde.components.physics_validator import PhysicsValidatorComponent
from metaharness_ext.ai4pde.components.problem_formulator import ProblemFormulatorComponent
from metaharness_ext.ai4pde.components.reference_solver import ReferenceSolverComponent
from metaharness_ext.ai4pde.components.solver_executor import SolverExecutorComponent
from metaharness_ext.ai4pde.types import SolverFamily

CASE_XML = Path(__file__).parent.parent / "docs" / "xml-pro" / "cylinder-flow-re100.xml"


def test_case_driven_flow_uses_compiled_plan() -> None:
    gateway = PDEGatewayComponent()
    formulator = ProblemFormulatorComponent()
    router = MethodRouterComponent()
    executor = SolverExecutorComponent()
    reference_solver = ReferenceSolverComponent()
    validator = PhysicsValidatorComponent()
    evidence = EvidenceManagerComponent()

    task, compiled_plan = gateway.issue_task_from_case(CASE_XML)
    formulated = formulator.formulate(task)
    routed_plan = router.build_plan(formulated)
    run_artifact = executor.execute_plan(routed_plan)
    reference_result = reference_solver.run_reference(routed_plan)
    validation_bundle = validator.validate_run(
        run_artifact,
        graph_version_id=1,
        reference_result=reference_result,
    )
    evidence_bundle = evidence.assemble_evidence(
        run_artifact,
        validation_bundle,
        reference_result=reference_result,
        graph_family=routed_plan.graph_family,
    )

    assert compiled_plan.selected_method == SolverFamily.CLASSICAL_HYBRID
    assert routed_plan.selected_method == SolverFamily.CLASSICAL_HYBRID
    assert routed_plan.template_id == "forward-fluid-mechanics"
    assert routed_plan.graph_family == "template::forward-fluid-mechanics"
    assert routed_plan.parameter_overrides["reference"]["source"] == "Kovasznay/NACA benchmark"
    assert run_artifact.solver_family == SolverFamily.CLASSICAL_HYBRID
    assert run_artifact.result_summary["backend"] == "nektar++"
    assert run_artifact.result_summary["nektar_solver"] == "IncNavierStokesSolver"
    assert "artifact://vtu_field/cylinder-flow-re100" in run_artifact.artifact_refs
    assert reference_result.summary["kind"] == "literature"
    assert reference_result.summary["metric"] == "drag_lift_residual"
    assert validation_bundle.reference_comparison["status"] == "better_or_equal"
    assert evidence_bundle.reference_comparison_refs == ["reference://reference-cylinder-flow-re100"]
    assert evidence_bundle.benchmark_snapshot_refs == ["benchmark://cylinder-flow-re100/baseline"]


def test_issue_task_demo_path_still_works() -> None:
    gateway = PDEGatewayComponent()

    task = gateway.issue_task("solve Laplace equation", task_id="demo-case")

    assert task.task_id == "demo-case"
    assert task.deliverables == ["solution_field", "validation_summary", "evidence_bundle"]
