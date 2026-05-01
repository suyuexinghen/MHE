from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from metaharness.sdk.research import Hypothesis, HypothesisStatus, ResearchQuestion

_TESTABLE_RELATIONS = {"lt", "le", "gt", "ge", "eq", "approx"}


class HypothesisActionKind(StrEnum):
    GENERATE = "GENERATE"
    REFINE = "REFINE"
    SELECT = "SELECT"
    COMBINE = "COMBINE"


class HypothesisAction(BaseModel):
    action_id: str
    kind: HypothesisActionKind
    hypothesis_ids: list[str] = Field(default_factory=list)
    proposed_hypothesis: Hypothesis | None = None
    reasons: list[str] = Field(default_factory=list)


class HypothesisActionSpace:
    """Research-native action space independent of graph mutations."""

    def testable(self, hypothesis: Hypothesis) -> bool:
        if not hypothesis.prediction:
            return False
        for constraint in hypothesis.prediction.values():
            if not isinstance(constraint, dict):
                return False
            relation = constraint.get("relation")
            value = constraint.get("value")
            if relation not in _TESTABLE_RELATIONS or not isinstance(value, int | float):
                return False
        return True

    def generate(
        self, question: ResearchQuestion, candidates: list[Hypothesis]
    ) -> list[HypothesisAction]:
        return [
            HypothesisAction(
                action_id=f"generate-{candidate.hypothesis_id}",
                kind=HypothesisActionKind.GENERATE,
                hypothesis_ids=[],
                proposed_hypothesis=candidate,
                reasons=[f"candidate is testable for {question.question_id}"],
            )
            for candidate in candidates
            if candidate.question_id == question.question_id and self.testable(candidate)
        ]

    def select(self, hypotheses: list[Hypothesis], *, limit: int = 1) -> list[HypothesisAction]:
        selected = sorted(
            [hypothesis for hypothesis in hypotheses if self.testable(hypothesis)],
            key=lambda hypothesis: hypothesis.cost_benefit_ratio,
            reverse=True,
        )[:limit]
        return [
            HypothesisAction(
                action_id=f"select-{hypothesis.hypothesis_id}",
                kind=HypothesisActionKind.SELECT,
                hypothesis_ids=[hypothesis.hypothesis_id],
                proposed_hypothesis=hypothesis,
                reasons=["highest cost-benefit testable hypothesis"],
            )
            for hypothesis in selected
        ]

    def refine(
        self,
        hypothesis: Hypothesis,
        *,
        hypothesis_id: str,
        statement: str,
        prediction: dict[str, dict[str, Any]],
    ) -> HypothesisAction:
        refined = Hypothesis(
            hypothesis_id=hypothesis_id,
            question_id=hypothesis.question_id,
            statement=statement,
            prediction=prediction,
            parent_hypothesis_id=hypothesis.hypothesis_id,
            estimated_information_gain=hypothesis.estimated_information_gain,
            estimated_cost=hypothesis.estimated_cost,
        )
        return HypothesisAction(
            action_id=f"refine-{hypothesis.hypothesis_id}-{hypothesis_id}",
            kind=HypothesisActionKind.REFINE,
            hypothesis_ids=[hypothesis.hypothesis_id],
            proposed_hypothesis=refined,
            reasons=["refined from prior hypothesis"],
        )

    def combine(
        self,
        left: Hypothesis,
        right: Hypothesis,
        *,
        hypothesis_id: str,
        statement: str,
        prediction: dict[str, dict[str, Any]],
    ) -> HypothesisAction:
        combined = Hypothesis(
            hypothesis_id=hypothesis_id,
            question_id=left.question_id,
            statement=statement,
            prediction=prediction,
            estimated_information_gain=max(
                left.estimated_information_gain,
                right.estimated_information_gain,
            ),
            estimated_cost=left.estimated_cost + right.estimated_cost,
        )
        return HypothesisAction(
            action_id=f"combine-{left.hypothesis_id}-{right.hypothesis_id}-{hypothesis_id}",
            kind=HypothesisActionKind.COMBINE,
            hypothesis_ids=[left.hypothesis_id, right.hypothesis_id],
            proposed_hypothesis=combined,
            reasons=["combined from supported hypotheses"],
        )


def supersede(hypothesis: Hypothesis) -> Hypothesis:
    return hypothesis.model_copy(update={"status": HypothesisStatus.SUPERSEDED})
