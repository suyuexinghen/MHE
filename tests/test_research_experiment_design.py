from __future__ import annotations

from metaharness.research.domains.fealpy import FEALPyRuleBasedExperimentDesigner
from metaharness.sdk.experiment_design import ExperimentDesignerProtocol
from metaharness.sdk.research import Hypothesis, ResearchQuestion


def test_fealpy_rule_based_experiment_designer_is_protocol_compatible() -> None:
    designer = FEALPyRuleBasedExperimentDesigner()

    assert isinstance(designer, ExperimentDesignerProtocol)


def test_fealpy_rule_based_experiment_designer_creates_deterministic_plan() -> None:
    question = ResearchQuestion(
        question_id="rq-fealpy-poisson-l2-threshold",
        statement="Can FEALPy solve Poisson with L2 error below 0.01?",
        formal_spec={"primary_metric": "l2_error", "relation": "lt", "target": 0.01},
    )
    hypothesis = Hypothesis(
        hypothesis_id="h-fealpy-poisson-p1-16x16",
        question_id=question.question_id,
        statement="P1 Lagrange elements produce L2 error below 0.01.",
        prediction={"l2_error": {"relation": "lt", "value": 0.01}},
    )

    plan = FEALPyRuleBasedExperimentDesigner().design(question, hypothesis)

    assert plan.plan_id == "plan-fealpy-pde-poisson-2d-numpy-extension"
    assert plan.hypothesis_id == hypothesis.hypothesis_id
    assert plan.suite == "fealpy-pde"
    assert plan.case_id == "poisson-2d-numpy"
    assert plan.lane == "extension"
    assert plan.controls == {"backend": "numpy", "meshtype": "tri"}
    assert plan.variables == {"nx": 16, "ny": 16, "fe_degree": 1}
    assert plan.expected_outcome == hypothesis.prediction


def test_fealpy_rule_based_experiment_designer_allows_case_override() -> None:
    designer = FEALPyRuleBasedExperimentDesigner(case_id="custom-case", lane="direct")
    question = ResearchQuestion(question_id="rq", statement="test")
    hypothesis = Hypothesis(hypothesis_id="h", question_id="rq", statement="test")

    plan = designer.design(question, hypothesis)

    assert plan.plan_id == "plan-fealpy-pde-custom-case-direct"
    assert plan.case_id == "custom-case"
    assert plan.lane == "direct"
    assert plan.expected_outcome == question.formal_spec
