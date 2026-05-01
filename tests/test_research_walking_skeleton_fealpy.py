from __future__ import annotations

from metaharness.research.decision import decision_from_evidence
from metaharness.research.mappers import evidence_to_scored_evidence, summary_to_evidence_bundle
from metaharness.research.store import ResearchStore
from metaharness.sdk.research import (
    DecisionOutcome,
    ExperimentPlan,
    Hypothesis,
    HypothesisStatus,
    ResearchConclusion,
    ResearchQuestion,
    ResearchQuestionStatus,
)


def test_fealpy_poisson_summary_drives_minimal_research_loop(tmp_path) -> None:
    question = ResearchQuestion(
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="Can the FEALPy Poisson 2D numpy benchmark solve with L2 error below 0.01?",
        formal_spec={"primary_metric": "l2_error", "relation": "lt", "target": 0.01},
        status=ResearchQuestionStatus.ACTIVE,
        created_from="benchmark:fealpy-pde:poisson-2d-numpy",
    )
    hypothesis = Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id=question.question_id,
        statement="P1 Lagrange elements on the 16x16 case produce L2 error below 0.01.",
        prediction={"l2_error": {"relation": "lt", "value": 0.01}},
    )
    plan = ExperimentPlan(
        plan_id="plan-fealpy-poisson-extension",
        hypothesis_id=hypothesis.hypothesis_id,
        suite="fealpy-pde",
        case_id="poisson-2d-numpy",
        lane="extension",
        controls={"backend": "numpy", "meshtype": "tri"},
        variables={"nx": 16, "ny": 16, "fe_degree": 1},
        expected_outcome=hypothesis.prediction,
    )
    summary = {
        "suite": "fealpy-pde",
        "case_id": "poisson-2d-numpy",
        "lane": "extension",
        "status": "passed",
        "metrics": {
            "dof": 289,
            "h1_error": 2.2250025132790325,
            "l2_error": 0.0024865245884339074,
            "wall_time": 0.0045,
        },
        "failure_category": None,
    }

    evidence = summary_to_evidence_bundle(
        summary,
        plan=plan,
        hypothesis=hypothesis,
        artifact_ref="summary.json",
    )
    decision = decision_from_evidence(evidence, hypothesis)
    hypothesis.status = HypothesisStatus.SUPPORTED
    conclusion = ResearchConclusion(
        question_id=question.question_id,
        decision_ids=[decision.decision_id],
        supported_hypotheses=[hypothesis.hypothesis_id],
        status=ResearchQuestionStatus.ANSWERED,
    )

    store = ResearchStore(tmp_path)
    store.record_question(question)
    store.record_hypothesis(hypothesis)
    store.record_plan(plan)
    store.record_evidence(evidence)
    store.record_decision(decision)
    scored = evidence_to_scored_evidence(evidence)

    assert evidence.metrics["l2_error"] < 0.01
    assert evidence.supports == [hypothesis.hypothesis_id]
    assert decision.decision == DecisionOutcome.ADVANCE
    assert conclusion.supported_hypotheses == [hypothesis.hypothesis_id]
    assert scored.score == 1.0
    assert store.list_hypotheses(question.question_id) == [hypothesis]
    assert store.evidence_for(hypothesis.hypothesis_id) == [evidence]
    assert store.decision_history(question.question_id) == [decision]
    assert len(store.trace_path.read_text().splitlines()) == 5


def test_fealpy_failed_summary_records_execution_failure_not_refutation(tmp_path) -> None:
    question = ResearchQuestion(
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="Can FEALPy solve Poisson with L2 error below 0.01?",
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

    evidence = summary_to_evidence_bundle(
        {"status": "failed", "metrics": {}, "failure_category": "solver_failure"},
        plan=plan,
        hypothesis=hypothesis,
        artifact_ref="summary.json",
    )
    decision = decision_from_evidence(evidence, hypothesis)
    store = ResearchStore(tmp_path)
    store.record_question(question)
    store.record_hypothesis(hypothesis)
    store.record_plan(plan)
    store.record_evidence(evidence)
    store.record_decision(decision)

    assert evidence.supports == []
    assert evidence.refutes == []
    assert decision.decision == DecisionOutcome.REFINE
    assert decision.reasoning == "evidence is inconclusive for the hypothesis"
    assert store.evidence_for(hypothesis.hypothesis_id) == []
