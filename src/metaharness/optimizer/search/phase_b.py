"""Phase B: topology and template search.

Swaps components, adds/removes connections, or substitutes templates.
Uses the contract pruner from Phase 3 to stay within legal territory,
and scores each candidate via a caller-supplied evaluator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from metaharness.core.models import (
    ComponentNode,
    ConnectionEdge,
    PendingConnectionSet,
)

if TYPE_CHECKING:  # pragma: no cover
    from metaharness.core.contract_pruner import ContractPruner


Objective = Callable[[PendingConnectionSet], float]


@dataclass(slots=True)
class TopologyMove:
    """A single move considered during Phase B search."""

    kind: str  # "add_edge" | "remove_edge" | "swap_component"
    payload: dict[str, Any]


@dataclass(slots=True)
class TopologyTrial:
    """Result of evaluating a topology move."""

    move: TopologyMove
    pending: PendingConnectionSet
    score: float


@dataclass(slots=True)
class TopologyTemplateSearch:
    """Enumerates legal topology mutations and scores them.

    Each iteration produces the set of moves (``add_edge``,
    ``remove_edge``, ``swap_component``) legal under the supplied
    :class:`ContractPruner` and evaluates the resulting pending set via
    ``objective``. The top-``k`` results are returned.
    """

    pruner: ContractPruner
    objective: Objective
    top_k: int = 5
    history: list[TopologyTrial] = field(default_factory=list)

    def run(
        self,
        baseline: PendingConnectionSet,
        *,
        templates: list[PendingConnectionSet] | None = None,
    ) -> list[TopologyTrial]:
        moves: list[TopologyMove] = []

        # --- add_edge moves: for every source port, ask the pruner for legal targets.
        for node in baseline.nodes:
            registered = self.pruner.registry.components.get(node.component_id)
            if registered is None:
                continue
            for out_port in registered.declarations.outputs:
                src_fqid = f"{node.component_id}.{out_port.name}"
                for target in self.pruner.legal_targets(src_fqid):
                    if any(
                        edge.source == src_fqid and edge.target == target.fqid
                        for edge in baseline.edges
                    ):
                        continue
                    moves.append(
                        TopologyMove(
                            kind="add_edge",
                            payload={
                                "source": src_fqid,
                                "target": target.fqid,
                                "payload_type": out_port.type,
                            },
                        )
                    )

        # --- remove_edge moves: each existing non-required edge may be removed.
        for edge in baseline.edges:
            moves.append(
                TopologyMove(kind="remove_edge", payload={"connection_id": edge.connection_id})
            )

        # --- template swaps: each provided template becomes a candidate whole graph.
        for template in templates or []:
            moves.append(
                TopologyMove(
                    kind="swap_template",
                    payload={"template": template.model_dump()},
                )
            )

        trials: list[TopologyTrial] = []
        for move in moves:
            candidate = self._apply(baseline, move)
            score = self.objective(candidate)
            trial = TopologyTrial(move=move, pending=candidate, score=score)
            self.history.append(trial)
            trials.append(trial)

        trials.sort(key=lambda t: t.score, reverse=True)
        return trials[: self.top_k]

    def _apply(self, baseline: PendingConnectionSet, move: TopologyMove) -> PendingConnectionSet:
        nodes: list[ComponentNode] = list(baseline.nodes)
        edges: list[ConnectionEdge] = list(baseline.edges)
        if move.kind == "add_edge":
            new_id = f"auto-{len(edges) + 1}"
            edges.append(
                ConnectionEdge(
                    connection_id=new_id,
                    source=move.payload["source"],
                    target=move.payload["target"],
                    payload=move.payload["payload_type"],
                    mode="async",
                    policy="optional",
                )
            )
        elif move.kind == "remove_edge":
            edges = [e for e in edges if e.connection_id != move.payload["connection_id"]]
        elif move.kind == "swap_template":
            data = move.payload["template"]
            return PendingConnectionSet.model_validate(data)
        return PendingConnectionSet(nodes=nodes, edges=edges)
