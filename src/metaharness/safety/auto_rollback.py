"""Level 4 post-commit auto-rollback.

Observes the post-commit system, and if any health probe fails within
the configured window, instructs the :class:`ConnectionEngine` to roll
back to the previous graph version.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from metaharness.safety.gates import GateDecision, GateResult

if TYPE_CHECKING:  # pragma: no cover
    from metaharness.core.connection_engine import ConnectionEngine
    from metaharness.core.mutation import MutationProposal

HealthProbe = Callable[[dict[str, Any]], tuple[bool, str]]


@dataclass(slots=True)
class RollbackEvent:
    """Record of a single rollback action."""

    reason: str
    from_version: int
    to_version: int | None
    probe: str


class AutoRollback:
    """Level 4 safety gate.

    Unlike gates 1-3 it runs *after* the candidate commits. Callers invoke
    :meth:`check` with the fresh post-commit context; any failing probe
    triggers an immediate rollback on the shared :class:`ConnectionEngine`.
    ``evaluate`` exists for pipeline symmetry and always allows by default
    (health probes determine actual behaviour).
    """

    name: str = "level_4_auto_rollback"

    def __init__(
        self,
        engine: ConnectionEngine,
        *,
        probes: list[tuple[str, HealthProbe]] | None = None,
    ) -> None:
        self._engine = engine
        self._probes: list[tuple[str, HealthProbe]] = list(probes or [])
        self.events: list[RollbackEvent] = []

    def register_probe(self, name: str, probe: HealthProbe) -> None:
        self._probes.append((name, probe))

    def evaluate(
        self, proposal: MutationProposal, context: dict[str, Any] | None = None
    ) -> GateResult:
        return GateResult(
            gate=self.name,
            decision=GateDecision.ALLOW,
            reason="post-commit gate; checks run via AutoRollback.check()",
        )

    def check(self, context: dict[str, Any] | None = None) -> GateResult:
        ctx = context or {}
        for probe_name, probe in self._probes:
            healthy, detail = probe(ctx)
            if healthy:
                continue
            from_version = self._engine.version_store.state.active_graph_version or 0
            try:
                snapshot = self._engine.rollback()
                to_version: int | None = snapshot.graph_version
            except ValueError:
                to_version = None
            self.events.append(
                RollbackEvent(
                    reason=detail or "probe_failed",
                    from_version=from_version,
                    to_version=to_version,
                    probe=probe_name,
                )
            )
            return GateResult(
                gate=self.name,
                decision=GateDecision.REJECT,
                reason=detail or "probe_failed",
                evidence={
                    "rolled_back_to": to_version,
                    "rolled_back_from": from_version,
                    "probe": probe_name,
                },
            )
        return GateResult(
            gate=self.name,
            decision=GateDecision.ALLOW,
            evidence={"probes": [name for name, _ in self._probes]},
        )


@dataclass(slots=True)
class HealthProbeResult:
    """Structured probe result for callers that prefer not to use tuples."""

    healthy: bool
    detail: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)

    def as_tuple(self) -> tuple[bool, str]:
        return self.healthy, self.detail
