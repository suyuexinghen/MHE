from __future__ import annotations

from metaharness.research.hypotheses import (
    HypothesisActionKind,
    HypothesisActionSpace,
    supersede,
)
from metaharness.sdk.research import Hypothesis, HypothesisStatus, ResearchQuestion


def _question() -> ResearchQuestion:
    return ResearchQuestion(question_id="rq", statement="Can the metric be improved?")


def _hypothesis(
    hypothesis_id: str,
    *,
    metric: str = "l2_error",
    relation: str = "lt",
    value: float | str = 0.01,
    information_gain: float = 1.0,
    cost: float = 1.0,
) -> Hypothesis:
    return Hypothesis(
        hypothesis_id=hypothesis_id,
        question_id="rq",
        statement=f"{hypothesis_id} is testable",
        prediction={metric: {"relation": relation, "value": value}},
        estimated_information_gain=information_gain,
        estimated_cost=cost,
    )


def test_hypothesis_action_space_filters_untestable_candidates() -> None:
    action_space = HypothesisActionSpace()
    testable = _hypothesis("h-testable")
    missing_prediction = Hypothesis(hypothesis_id="h-empty", question_id="rq", statement="empty")
    bad_relation = _hypothesis("h-bad-relation", relation="unknown")
    bad_value = _hypothesis("h-bad-value", value="small")

    actions = action_space.generate(
        _question(),
        [testable, missing_prediction, bad_relation, bad_value],
    )

    assert [
        action.proposed_hypothesis.hypothesis_id for action in actions if action.proposed_hypothesis
    ] == ["h-testable"]
    assert actions[0].kind == HypothesisActionKind.GENERATE


def test_hypothesis_action_space_selects_by_cost_benefit_ratio() -> None:
    action_space = HypothesisActionSpace()
    low_value = _hypothesis("h-low", information_gain=1.0, cost=10.0)
    high_value = _hypothesis("h-high", information_gain=3.0, cost=1.0)

    actions = action_space.select([low_value, high_value], limit=1)

    assert len(actions) == 1
    assert actions[0].kind == HypothesisActionKind.SELECT
    assert actions[0].hypothesis_ids == ["h-high"]
    assert actions[0].proposed_hypothesis == high_value


def test_hypothesis_action_space_refines_with_parent_link() -> None:
    action_space = HypothesisActionSpace()
    original = _hypothesis("h-original", information_gain=2.0, cost=4.0)

    action = action_space.refine(
        original,
        hypothesis_id="h-refined",
        statement="Refined threshold",
        prediction={"l2_error": {"relation": "lt", "value": 0.005}},
    )

    assert action.kind == HypothesisActionKind.REFINE
    assert action.hypothesis_ids == ["h-original"]
    assert action.proposed_hypothesis is not None
    assert action.proposed_hypothesis.parent_hypothesis_id == "h-original"
    assert action.proposed_hypothesis.cost_benefit_ratio == original.cost_benefit_ratio


def test_hypothesis_action_space_combines_supported_hypotheses() -> None:
    action_space = HypothesisActionSpace()
    left = _hypothesis("h-left", information_gain=2.0, cost=1.0)
    right = _hypothesis("h-right", information_gain=1.0, cost=1.0)

    action = action_space.combine(
        left,
        right,
        hypothesis_id="h-combined",
        statement="Combined claim",
        prediction={"l2_error": {"relation": "lt", "value": 0.004}},
    )

    assert action.kind == HypothesisActionKind.COMBINE
    assert action.hypothesis_ids == ["h-left", "h-right"]
    assert action.proposed_hypothesis is not None
    assert action.proposed_hypothesis.estimated_information_gain == 2.0
    assert action.proposed_hypothesis.estimated_cost == 2.0


def test_supersede_marks_hypothesis_without_mutating_original() -> None:
    original = _hypothesis("h-original")

    updated = supersede(original)

    assert original.status == HypothesisStatus.PROPOSED
    assert updated.status == HypothesisStatus.SUPERSEDED
