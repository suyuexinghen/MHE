from __future__ import annotations

from metaharness.core.research import ResearchOrchestrator
from metaharness.research.store import ResearchStore
from metaharness.sdk.research import (
    DecisionOutcome,
    ExperimentPlan,
    Hypothesis,
    HypothesisStatus,
    ResearchBudget,
    ResearchQuestion,
    ResearchQuestionStatus,
)


def _question() -> ResearchQuestion:
    return ResearchQuestion(
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="Can FEALPy solve Poisson with L2 error below 0.01?",
        formal_spec={"primary_metric": "l2_error", "relation": "lt", "target": 0.01},
        status=ResearchQuestionStatus.ACTIVE,
        created_from="benchmark:fealpy-pde:poisson-2d-numpy",
    )


def _hypothesis(threshold: float = 0.01) -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="P1 Lagrange elements produce L2 error below threshold.",
        prediction={"l2_error": {"relation": "lt", "value": threshold}},
    )


def _plan(hypothesis: Hypothesis) -> ExperimentPlan:
    return ExperimentPlan(
        plan_id="plan-fealpy-poisson-extension",
        hypothesis_id=hypothesis.hypothesis_id,
        suite="fealpy-pde",
        case_id="poisson-2d-numpy",
        lane="extension",
        controls={"backend": "numpy"},
        variables={"nx": 16, "ny": 16, "fe_degree": 1},
        expected_outcome=hypothesis.prediction,
    )


def test_research_orchestrator_advances_supported_hypothesis(tmp_path) -> None:
    hypothesis = _hypothesis()
    plan = _plan(hypothesis)
    store = ResearchStore(tmp_path)
    orchestrator = ResearchOrchestrator(store, budget=ResearchBudget(max_experiments=1))

    run = orchestrator.pursue(
        _question(),
        hypotheses=[hypothesis],
        plans=[plan],
        summaries={plan.plan_id: {"status": "passed", "metrics": {"l2_error": 0.002}, "failure_category": None}},
        artifact_refs={plan.plan_id: "summary.json"},
    )

    assert run.decisions[0].decision == DecisionOutcome.ADVANCE
    assert run.hypotheses[0].status == HypothesisStatus.SUPPORTED
    assert run.conclusion.status == ResearchQuestionStatus.ANSWERED
    assert run.conclusion.supported_hypotheses == [hypothesis.hypothesis_id]
    assert run.budget.experiments_used == 1
    assert store.list_hypotheses(_question().question_id)[0].status == HypothesisStatus.SUPPORTED
    assert store.decision_history(_question().question_id) == run.decisions


def test_research_orchestrator_refines_refuted_hypothesis(tmp_path) -> None:
    hypothesis = _hypothesis(threshold=0.001)
    plan = _plan(hypothesis)
    orchestrator = ResearchOrchestrator(ResearchStore(tmp_path), budget=ResearchBudget(max_experiments=1))

    run = orchestrator.pursue(
        _question(),
        hypotheses=[hypothesis],
        plans=[plan],
        summaries={plan.plan_id: {"status": "passed", "metrics": {"l2_error": 0.002}, "failure_category": None}},
    )

    assert run.decisions[0].decision == DecisionOutcome.REFINE
    assert run.hypotheses[0].status == HypothesisStatus.REFUTED
    assert run.conclusion.refuted_hypotheses == [hypothesis.hypothesis_id]


def test_research_orchestrator_stops_at_experiment_budget(tmp_path) -> None:
    hypothesis = _hypothesis()
    plan = _plan(hypothesis)
    second_plan = plan.model_copy(update={"plan_id": "plan-fealpy-poisson-direct", "lane": "direct"})
    orchestrator = ResearchOrchestrator(ResearchStore(tmp_path), budget=ResearchBudget(max_experiments=1))

    run = orchestrator.pursue(
        _question(),
        hypotheses=[hypothesis],
        plans=[plan, second_plan],
        summaries={
            plan.plan_id: {"status": "passed", "metrics": {"l2_error": 0.002}, "failure_category": None},
            second_plan.plan_id: {"status": "passed", "metrics": {"l2_error": 0.003}, "failure_category": None},
        },
    )

    assert len(run.evidence) == 1
    assert len(run.decisions) == 1
    assert run.budget.exhausted is True
    assert run.conclusion.status == ResearchQuestionStatus.STALE
