"""Counter-factual diagnosis.

Given a provenance graph and a failure event, score hypotheses of the
form "what if evidence ``E`` had not been used?". The scoring is a
minimal removal-delta over a caller-supplied evaluator so we never
hard-code the failure semantics.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from metaharness.provenance.evidence import ProvGraph, RelationKind

Evaluator = Callable[[ProvGraph], float]


@dataclass(slots=True)
class CounterFactualHypothesis:
    """Remove a single entity/activity and observe the delta."""

    target_id: str
    description: str = ""


@dataclass(slots=True)
class CounterFactualResult:
    """Scored hypothesis result."""

    target_id: str
    description: str
    baseline_score: float
    counter_score: float

    @property
    def delta(self) -> float:
        return self.counter_score - self.baseline_score


class CounterFactualDiagnosis:
    """Score a list of counter-factual hypotheses against a PROV graph.

    ``baseline_evaluator`` scores the full graph. For each hypothesis we
    produce a pruned graph copy with the target removed and re-run the
    evaluator. The delta is returned; callers rank by magnitude to find
    the most influential evidence.
    """

    def __init__(
        self,
        graph: ProvGraph,
        evaluator: Evaluator,
    ) -> None:
        self.graph = graph
        self.evaluator = evaluator
        self.history: list[CounterFactualResult] = []

    def score(self, hypotheses: list[CounterFactualHypothesis]) -> list[CounterFactualResult]:
        baseline = self.evaluator(self.graph)
        results: list[CounterFactualResult] = []
        for hyp in hypotheses:
            pruned = self._prune(hyp.target_id)
            counter = self.evaluator(pruned)
            result = CounterFactualResult(
                target_id=hyp.target_id,
                description=hyp.description,
                baseline_score=baseline,
                counter_score=counter,
            )
            results.append(result)
        self.history.extend(results)
        return results

    def _prune(self, target_id: str) -> ProvGraph:
        pruned = ProvGraph()
        for entity in self.graph.entities.values():
            if entity.id == target_id:
                continue
            pruned.entities[entity.id] = entity
        for activity in self.graph.activities.values():
            if activity.id == target_id:
                continue
            pruned.activities[activity.id] = activity
        for agent in self.graph.agents.values():
            if agent.id == target_id:
                continue
            pruned.agents[agent.id] = agent
        for relation in self.graph.relations:
            if relation.subject == target_id or relation.object == target_id:
                continue
            pruned.relations.append(relation)
        return pruned

    @staticmethod
    def size_evaluator() -> Evaluator:
        """A simple evaluator counting entity+activity+agent+relation nodes."""

        def _score(graph: ProvGraph) -> float:
            return float(
                len(graph.entities)
                + len(graph.activities)
                + len(graph.agents)
                + len(graph.relations)
            )

        return _score

    @staticmethod
    def derivation_depth_evaluator(root: str) -> Evaluator:
        """Evaluator: depth of the deepest wasDerivedFrom chain rooted at ``root``."""

        def _score(graph: ProvGraph) -> float:
            if root not in graph.entities:
                return 0.0
            # BFS on derivation edges.
            depth: dict[str, int] = {root: 0}
            queue = [root]
            while queue:
                current = queue.pop(0)
                for relation in graph.relations:
                    if (
                        relation.kind == RelationKind.WAS_DERIVED_FROM
                        and relation.subject == current
                        and relation.object not in depth
                    ):
                        depth[relation.object] = depth[current] + 1
                        queue.append(relation.object)
            return float(max(depth.values()))

        return _score
