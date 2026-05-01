from __future__ import annotations

from typing import Protocol, runtime_checkable

from metaharness.sdk.research import ExperimentPlan, Hypothesis, ResearchQuestion


@runtime_checkable
class ExperimentDesignerProtocol(Protocol):
    """Designs a benchmark-backed experiment plan from a fixed hypothesis."""

    def design(self, question: ResearchQuestion, hypothesis: Hypothesis) -> ExperimentPlan: ...
