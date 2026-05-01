from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from metaharness.sdk.experiment_design import ExperimentDesignerProtocol
from metaharness.sdk.research import ExperimentPlan, Hypothesis, ResearchQuestion


@dataclass(frozen=True)
class FEALPyRuleBasedExperimentDesigner(ExperimentDesignerProtocol):
    """Rule-based designer for the FEALPy Poisson MVP case."""

    suite: str = "fealpy-pde"
    case_id: str = "poisson-2d-numpy"
    lane: str = "extension"
    controls: dict[str, Any] = field(
        default_factory=lambda: {"backend": "numpy", "meshtype": "tri"}
    )
    variables: dict[str, Any] = field(default_factory=lambda: {"nx": 16, "ny": 16, "fe_degree": 1})

    def design(self, question: ResearchQuestion, hypothesis: Hypothesis) -> ExperimentPlan:
        expected_outcome = hypothesis.prediction or question.formal_spec
        return ExperimentPlan(
            plan_id=f"plan-{self.suite}-{self.case_id}-{self.lane}",
            hypothesis_id=hypothesis.hypothesis_id,
            suite=self.suite,
            case_id=self.case_id,
            lane=self.lane,
            controls=dict(self.controls),
            variables=dict(self.variables),
            expected_outcome=expected_outcome,
        )
