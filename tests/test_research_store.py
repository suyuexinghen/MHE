from __future__ import annotations

from metaharness.research.store import ResearchStore
from metaharness.sdk.research import (
    Decision,
    DecisionOutcome,
    EvidenceBundle,
    EvidenceStatus,
    ExperimentPlan,
    Hypothesis,
    ResearchQuestion,
    ResearchQuestionStatus,
)


def test_research_store_roundtrip_queries(tmp_path) -> None:
    store = ResearchStore(tmp_path)
    question = ResearchQuestion(
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="Can FEALPy solve Poisson with L2 error below 0.01?",
        status=ResearchQuestionStatus.ACTIVE,
    )
    hypothesis = Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id=question.question_id,
        statement="P1 Lagrange elements produce L2 error below 0.01.",
        prediction={"l2_error": {"relation": "lt", "value": 0.01}},
    )
    plan = ExperimentPlan(
        plan_id="plan-fealpy-poisson-extension",
        hypothesis_id=hypothesis.hypothesis_id,
        suite="fealpy-pde",
        case_id="poisson-2d-numpy",
        lane="extension",
    )
    evidence = EvidenceBundle(
        bundle_id="ev-fealpy-poisson-extension",
        experiment_plan_id=plan.plan_id,
        metrics={"l2_error": 0.0024865245884339074},
        status=EvidenceStatus.PASSED,
        confidence=1.0,
        confidence_method="deterministic_metric_threshold",
        supports=[hypothesis.hypothesis_id],
    )
    decision = Decision(
        decision_id="dec-fealpy-poisson-advance",
        hypothesis_id=hypothesis.hypothesis_id,
        evidence_bundle_id=evidence.bundle_id,
        decision=DecisionOutcome.ADVANCE,
        reasoning="metric threshold satisfied",
    )

    store.record_question(question)
    store.record_hypothesis(hypothesis)
    store.record_plan(plan)
    store.record_evidence(evidence)
    store.record_decision(decision)

    reopened = ResearchStore(tmp_path)

    assert reopened.list_hypotheses(question.question_id) == [hypothesis]
    assert reopened.evidence_for(hypothesis.hypothesis_id) == [evidence]
    assert reopened.decision_history(question.question_id) == [decision]
    assert reopened.trace_path.exists()
    assert len(reopened.trace_path.read_text().splitlines()) == 5


def test_research_store_empty_queries(tmp_path) -> None:
    store = ResearchStore(tmp_path)

    assert store.list_hypotheses("missing") == []
    assert store.evidence_for("missing") == []
    assert store.decision_history("missing") == []
