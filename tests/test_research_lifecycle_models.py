from __future__ import annotations

import pytest
from pydantic import ValidationError

from metaharness.sdk.research import (
    Decision,
    DecisionOutcome,
    EvidenceBundle,
    EvidenceStatus,
    ExperimentPlan,
    Hypothesis,
    HypothesisStatus,
    ResearchConclusion,
    ResearchQuestion,
    ResearchQuestionStatus,
    ValidationStrategy,
)


def test_research_question_roundtrip() -> None:
    question = ResearchQuestion(
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="Can FEALPy solve Poisson with L2 error below 0.01?",
        formal_spec={"primary_metric": "l2_error", "relation": "lt", "target": 0.01},
        status=ResearchQuestionStatus.ACTIVE,
        created_from="benchmark:fealpy-pde:poisson-2d-numpy",
    )

    restored = ResearchQuestion.model_validate_json(question.model_dump_json())

    assert restored == question
    assert restored.validation_strategy == ValidationStrategy.GROUND_TRUTH


def test_hypothesis_and_experiment_plan_bind_to_benchmark_case() -> None:
    hypothesis = Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="P1 Lagrange elements produce L2 error below 0.01.",
        prediction={"l2_error": {"relation": "lt", "value": 0.01}},
    )
    plan = ExperimentPlan(
        plan_id="plan-fealpy-poisson-extension",
        hypothesis_id=hypothesis.hypothesis_id,
        suite="fealpy-pde",
        case_id="poisson-2d-numpy",
        lane="extension",
        controls={"backend": "numpy", "mesh": "tri"},
        variables={"nx": 16, "ny": 16, "fe_degree": 1},
        expected_outcome=hypothesis.prediction,
    )

    assert hypothesis.status == HypothesisStatus.PROPOSED
    assert plan.hypothesis_id == hypothesis.hypothesis_id
    assert plan.suite == "fealpy-pde"


def test_passing_evidence_can_support_hypothesis() -> None:
    evidence = EvidenceBundle(
        bundle_id="ev-fealpy-poisson-extension-final3",
        experiment_plan_id="plan-fealpy-poisson-extension",
        artifact_refs=[
            ".runs/fealpy-final3-20260501/fealpy-pde-benchmark/extension/poisson-2d-numpy/summary.json"
        ],
        metrics={"l2_error": 0.0024865245884339074, "h1_error": 2.2250025132790325},
        status=EvidenceStatus.PASSED,
        failure_category=None,
        confidence=1.0,
        confidence_method="deterministic_metric_threshold",
        domain_tags={"suite": "fealpy-pde", "case_id": "poisson-2d-numpy", "lane": "extension"},
        supports=["h-fealpy-poisson-p1-16x16"],
    )

    restored = EvidenceBundle.model_validate_json(evidence.model_dump_json())

    assert restored == evidence
    assert restored.supports == ["h-fealpy-poisson-p1-16x16"]
    assert restored.refutes == []


def test_failed_evidence_cannot_support_or_refute_hypothesis() -> None:
    with pytest.raises(ValidationError, match="non-passing evidence cannot support or refute"):
        EvidenceBundle(
            bundle_id="ev-failed",
            experiment_plan_id="plan-fealpy-poisson-extension",
            metrics={},
            status=EvidenceStatus.FAILED,
            failure_category="solver_failure",
            confidence=0.0,
            confidence_method="execution_failed",
            supports=["h-fealpy-poisson-p1-16x16"],
        )


def test_decision_and_conclusion_roundtrip() -> None:
    decision = Decision(
        decision_id="dec-advance-poisson",
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        evidence_bundle_id="ev-fealpy-poisson-extension-final3",
        decision=DecisionOutcome.ADVANCE,
        reasoning="l2_error is below the hypothesis threshold.",
    )
    conclusion = ResearchConclusion(
        question_id="rq-fealpy-poisson-l2-threshold",
        decision_ids=[decision.decision_id],
        supported_hypotheses=[decision.hypothesis_id],
        status=ResearchQuestionStatus.ANSWERED,
    )

    assert Decision.model_validate_json(decision.model_dump_json()) == decision
    assert ResearchConclusion.model_validate_json(conclusion.model_dump_json()) == conclusion
    assert decision.requires_approval is False
