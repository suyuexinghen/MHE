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
    from metaharness.hotreload.observation import (
        ObservationWindowEvaluator,
        ObservationWindowReport,
    )

HealthProbe = Callable[[dict[str, Any]], tuple[bool, str]]
ObservationProbeType = Callable[[Any, Any, dict[str, Any]], Any]


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
        observation_evaluator: "ObservationWindowEvaluator | None" = None,
    ) -> None:
        from metaharness.hotreload.observation import ObservationWindowEvaluator

        self._engine = engine
        self._probes: list[tuple[str, HealthProbe]] = list(probes or [])
        self.observation_evaluator = observation_evaluator or ObservationWindowEvaluator()
        self.events: list[RollbackEvent] = []

    def register_probe(self, name: str, probe: HealthProbe) -> None:
        self._probes.append((name, probe))

    def register_observation_probe(self, name: str, probe: ObservationProbeType) -> None:
        self.observation_evaluator.register_probe(name, probe)

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
            return self._rollback_result(probe_name, detail or "probe_failed")
        return GateResult(
            gate=self.name,
            decision=GateDecision.ALLOW,
            evidence={"probes": [name for name, _ in self._probes]},
        )

    def check_observation_window(
        self,
        *,
        metrics: Any | None = None,
        events: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> tuple[GateResult, ObservationWindowReport]:
        report = self.observation_evaluator.evaluate(
            metrics=metrics,
            events=events,
            context=context,
        )
        if report.passed:
            return (
                GateResult(
                    gate=self.name,
                    decision=GateDecision.ALLOW,
                    evidence={"observation": self._observation_evidence(report)},
                ),
                report,
            )
        return (
            self._rollback_result(
                report.rejected_by or "observation_window",
                report.reason or "observation window rejected promotion",
                evidence={"observation": self._observation_evidence(report)},
            ),
            report,
        )

    def _rollback_result(
        self,
        probe_name: str,
        reason: str,
        *,
        evidence: dict[str, Any] | None = None,
    ) -> GateResult:
        from_version = self._engine.version_store.state.active_graph_version or 0
        try:
            snapshot = self._engine.rollback()
            to_version: int | None = snapshot.graph_version
        except ValueError:
            to_version = None
        self.events.append(
            RollbackEvent(
                reason=reason,
                from_version=from_version,
                to_version=to_version,
                probe=probe_name,
            )
        )
        result_evidence = {
            "rolled_back_to": to_version,
            "rolled_back_from": from_version,
            "probe": probe_name,
        }
        if evidence:
            result_evidence.update(evidence)
        return GateResult(
            gate=self.name,
            decision=GateDecision.REJECT,
            reason=reason,
            evidence=result_evidence,
        )

    @staticmethod
    def _observation_evidence(report: Any) -> dict[str, Any]:
        return {
            "passed": report.passed,
            "rejected_by": report.rejected_by,
            "reason": report.reason,
            "evidence": dict(report.evidence),
            "probes": [name for name, _ in report.probe_results],
        }


@dataclass(slots=True)
class HealthProbeResult:
    """Structured probe result for callers that prefer not to use tuples."""

    healthy: bool
    detail: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)

    def as_tuple(self) -> tuple[bool, str]:
        return self.healthy, self.detail
