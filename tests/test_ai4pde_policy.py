from metaharness.core.models import ScoredEvidence, SessionEvent
from metaharness_ext.ai4pde.components.observability_hub import ObservabilityHubComponent
from metaharness_ext.ai4pde.components.risk_policy import RiskPolicyComponent
from metaharness_ext.ai4pde.contracts import (
    BudgetRecord,
    PDEPlan,
    PDETaskRequest,
    ScientificEvidenceBundle,
    ValidationBundle,
)
from metaharness_ext.ai4pde.policies import (
    check_budget,
    check_reproducibility,
    classify_budget,
    classify_risk,
    evaluate_observation_window,
)
from metaharness_ext.ai4pde.types import ProblemType, RiskLevel, SolverFamily


def test_budget_and_risk_helpers_classify_expected_levels() -> None:
    request = PDETaskRequest(
        task_id="task-red",
        goal="expensive solve",
        problem_type=ProblemType.INVERSE,
        budget=BudgetRecord(gpu_hours=10.0, hpc_quota=2.0),
        risk_level=RiskLevel.GREEN,
    )
    plan = PDEPlan(
        plan_id="plan-red",
        task_id=request.task_id,
        selected_method=SolverFamily.CLASSICAL_HYBRID,
    )

    assert check_budget(request.budget)["within_limits"] is False
    assert classify_budget(request.budget) == "red"
    assert classify_risk(request, plan) == RiskLevel.RED


def test_reproducibility_and_observation_helpers_return_governance_signals() -> None:
    validation = ValidationBundle(
        validation_id="validation-1",
        task_id="task-1",
        graph_version_id=1,
        residual_metrics={"residual_l2": 0.01},
        bc_ic_metrics={"boundary_error": 0.0},
    )

    reproducibility = check_reproducibility(validation)
    observation = evaluate_observation_window(task_count=3, duration_minutes=30, degrade_ratio=0.02)

    assert reproducibility["meets_threshold"] is True
    assert observation["meets_minimums"] is True
    assert observation["rollback_recommended"] is False


def test_risk_policy_and_observability_components_record_state() -> None:
    request = PDETaskRequest(
        task_id="task-2",
        goal="governed run",
        problem_type=ProblemType.FORWARD,
        budget=BudgetRecord(gpu_hours=1.0),
        risk_level=RiskLevel.GREEN,
    )
    plan = PDEPlan(
        plan_id="plan-2",
        task_id=request.task_id,
        selected_method=SolverFamily.PINN_STRONG,
    )
    validation = ValidationBundle(
        validation_id="validation-2",
        task_id=request.task_id,
        graph_version_id=2,
        residual_metrics={"residual_l2": 0.01},
        bc_ic_metrics={"boundary_error": 0.0},
        summary={"status": "accept", "residual_l2": 0.01},
    )
    evidence = ScientificEvidenceBundle(
        bundle_id="bundle-2",
        task_id=request.task_id,
        graph_version_id=2,
        provenance_refs=["provenance://task-2"],
    )
    validation.scored_evidence = ScoredEvidence(score=0.99, metrics={"residual_l2": 0.01})
    validation.session_events = [
        SessionEvent(
            event_id="evt-1",
            session_id=request.task_id,
            event_type="candidate_validated",
            graph_version=2,
            candidate_id="run-2",
            payload={},
        )
    ]
    evidence.scored_evidence = validation.scored_evidence
    evidence.session_events = validation.session_events

    policy = RiskPolicyComponent()
    observability = ObservabilityHubComponent()
    decision = policy.classify(request, plan=plan, validation_bundle=validation)
    report = observability.record(validation, evidence)

    assert decision["risk_level"] == "green"
    assert decision["budget_level"] == "green"
    assert decision["promotion_outcome"] == "pending"
    assert decision["safety_outcome"] == "unknown"
    assert decision["rollback_recommended"] is False
    assert decision["evidence_score"] == 0.99
    assert decision["session_event_count"] == 1
    assert report["meets_minimums"] is False
    assert report["evidence_refs"] == 1
    assert report["promotion_outcome"] == "pending"
    assert report["safety_outcome"] == "unknown"
    assert report["rollback_recommended"] is False
    assert report["session_event_count"] == 1
    assert report["scored_evidence"] == 0.99
