"""Level 1 sandbox validator.

Runs all structural / compatibility checks on the candidate graph in a
dry sandbox without commit. Deterministic and purely local; catches
connection-type errors, orphans, and missing required inputs before we
spend resources on shadow execution or policy review.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from metaharness.core.models import GraphSnapshot, PendingConnectionSet
from metaharness.core.validators import validate_graph
from metaharness.safety.gates import GateDecision, GateResult

if TYPE_CHECKING:  # pragma: no cover
    from metaharness.core.mutation import MutationProposal
    from metaharness.sdk.registry import ComponentRegistry


class SandboxValidator:
    """Level 1 safety gate.

    Snapshots the proposal as a candidate graph, runs the full validator
    chain against the caller-supplied registry, and returns a gate
    decision. A failing validation immediately short-circuits the rest of
    the pipeline.
    """

    name: str = "level_1_sandbox_validator"

    def __init__(self, registry: ComponentRegistry) -> None:
        self._registry = registry

    def evaluate(
        self, proposal: MutationProposal, context: dict[str, Any] | None = None
    ) -> GateResult:
        pending = proposal.pending
        assert isinstance(pending, PendingConnectionSet)
        snapshot = GraphSnapshot(graph_version=0, nodes=pending.nodes, edges=pending.edges)
        report = validate_graph(snapshot, self._registry)
        if report.valid:
            return GateResult(
                gate=self.name,
                decision=GateDecision.ALLOW,
                evidence={"validated_nodes": len(snapshot.nodes)},
            )
        return GateResult(
            gate=self.name,
            decision=GateDecision.REJECT,
            reason="; ".join(f"{i.code}:{i.subject}" for i in report.issues) or "validation_failed",
            evidence={"issues": [i.model_dump() for i in report.issues]},
        )
