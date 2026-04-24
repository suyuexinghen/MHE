from metaharness.core.models import ScoredEvidence
from metaharness_ext.ai4pde import (
    BudgetRecord,
    PDEPlan,
    PDERunArtifact,
    PDETaskRequest,
    ScientificEvidenceBundle,
    ValidationBundle,
)
from metaharness_ext.ai4pde.types import (
    NextAction,
    ProblemType,
    PromotionOutcome,
    RiskLevel,
    SafetyOutcome,
    SolverFamily,
)


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
        scored_evidence=ScoredEvidence(score=0.95, evidence_refs=["validation://validation-1"]),
        provenance={"candidate_id": "run-1"},
    )
    evidence = ScientificEvidenceBundle(
        bundle_id="bundle-1",
        task_id=request.task_id,
        graph_version_id=1,
        scored_evidence=ScoredEvidence(score=0.95, evidence_refs=["validation://validation-1"]),
        provenance={"candidate_id": "run-1"},
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
    validation = ValidationBundle(
        validation_id="validation-defaults",
        task_id=request.task_id,
        graph_version_id=2,
    )
    evidence = ScientificEvidenceBundle(
        bundle_id="bundle-defaults",
        task_id=request.task_id,
        graph_version_id=2,
    )

    assert request.physics_spec == {}
    assert request.geometry_spec == {}
    assert request.data_spec == {}
    assert request.deliverables == []
    assert request.budget.token_budget == 0
    assert validation.promotion_metadata.outcome == PromotionOutcome.PENDING
    assert validation.safety_evaluation.outcome == SafetyOutcome.UNKNOWN
    assert validation.rollback_context.rollback_recommended is False
    assert validation.scored_evidence is None
    assert validation.session_events == []
    assert validation.provenance == {}
    assert evidence.candidate_identity.candidate_id is None
    assert evidence.scored_evidence is None
    assert evidence.session_events == []
    assert evidence.provenance == {}


def test_ai4pde_contracts_preserve_unified_promotion_and_evidence_linkage() -> None:
    validation = ValidationBundle.model_validate(
        {
            "validation_id": "validation-3",
            "task_id": "task-3",
            "graph_version_id": 7,
            "promotion_metadata": {
                "outcome": PromotionOutcome.PROMOTED,
                "affected_protected_components": ["policy.primary"],
                "candidate_identity": {
                    "candidate_id": "candidate-7",
                    "proposed_graph_version": 7,
                    "graph_version_id": 7,
                    "actor": "policy.primary",
                },
            },
            "candidate_identity": {
                "candidate_id": "candidate-7",
                "proposed_graph_version": 7,
                "graph_version_id": 7,
                "actor": "policy.primary",
            },
            "safety_evaluation": {
                "outcome": SafetyOutcome.ALLOWED,
                "protection": {
                    "protected_components": ["policy.primary"],
                    "allowed": True,
                },
            },
            "rollback_context": {
                "rollback_target": 6,
                "rollback_recommended": False,
            },
            "scored_evidence": {
                "score": 0.9,
                "evidence_refs": ["session-event:e-1", "audit-record:a-1"],
                "reasons": ["promotion approved"],
            },
            "session_events": [
                {
                    "event_id": "e-1",
                    "session_id": "session-1",
                    "event_type": "graph_committed",
                    "graph_version": 7,
                    "candidate_id": "candidate-7",
                    "payload": {"rollback_target": 6},
                }
            ],
            "provenance": {"checkpoint": "checkpoint:c-1"},
        }
    )
    evidence = ScientificEvidenceBundle.model_validate(
        {
            "bundle_id": "bundle-3",
            "task_id": "task-3",
            "graph_version_id": 7,
            "promotion_metadata": validation.promotion_metadata.model_dump(),
            "candidate_identity": validation.candidate_identity.model_dump(),
            "safety_evaluation": validation.safety_evaluation.model_dump(),
            "rollback_context": validation.rollback_context.model_dump(),
            "scored_evidence": validation.scored_evidence.model_dump(),
            "session_events": [event.model_dump() for event in validation.session_events],
            "provenance": validation.provenance,
        }
    )

    assert validation.promotion_metadata.candidate_identity.candidate_id == "candidate-7"
    assert validation.candidate_identity.graph_version_id == 7
    assert validation.safety_evaluation.protection.protected_components == ["policy.primary"]
    assert validation.scored_evidence is not None
    assert validation.scored_evidence.evidence_refs == ["session-event:e-1", "audit-record:a-1"]
    assert validation.session_events[0].candidate_id == "candidate-7"
    assert evidence.promotion_metadata.affected_protected_components == ["policy.primary"]
    assert evidence.scored_evidence == validation.scored_evidence
    assert evidence.session_events[0].payload["rollback_target"] == 6
