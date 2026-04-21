from metaharness_ext.ai4pde import (
    BudgetRecord,
    PDEPlan,
    PDERunArtifact,
    PDETaskRequest,
    ScientificEvidenceBundle,
    ValidationBundle,
)
from metaharness_ext.ai4pde.types import NextAction, ProblemType, RiskLevel, SolverFamily


def test_ai4pde_contracts_round_trip() -> None:
    budget = BudgetRecord(token_budget=1000, gpu_hours=1.5)
    request = PDETaskRequest(
        task_id="task-1",
        goal="solve a PDE",
        problem_type=ProblemType.FORWARD,
        budget=budget,
        risk_level=RiskLevel.GREEN,
    )
    plan = PDEPlan(
        plan_id="plan-1",
        task_id=request.task_id,
        selected_method=SolverFamily.PINN_STRONG,
    )
    run_artifact = PDERunArtifact(
        run_id="run-1",
        task_id=request.task_id,
        solver_family=SolverFamily.PINN_STRONG,
    )
    validation = ValidationBundle(
        validation_id="validation-1",
        task_id=request.task_id,
        graph_version_id=1,
        next_action=NextAction.ACCEPT,
    )
    evidence = ScientificEvidenceBundle(
        bundle_id="bundle-1",
        task_id=request.task_id,
        graph_version_id=1,
    )

    assert PDETaskRequest.model_validate(request.model_dump()) == request
    assert PDEPlan.model_validate(plan.model_dump()) == plan
    assert PDERunArtifact.model_validate(run_artifact.model_dump()) == run_artifact
    assert ValidationBundle.model_validate(validation.model_dump()) == validation
    assert ScientificEvidenceBundle.model_validate(evidence.model_dump()) == evidence


def test_ai4pde_contracts_have_required_defaults() -> None:
    request = PDETaskRequest(
        task_id="task-2",
        goal="benchmark",
        problem_type=ProblemType.FORWARD,
    )

    assert request.physics_spec == {}
    assert request.geometry_spec == {}
    assert request.data_spec == {}
    assert request.deliverables == []
    assert request.budget.token_budget == 0
