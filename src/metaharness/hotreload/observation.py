"""Post-swap observation-window evaluation for hot-reload.

The evaluator stays intentionally small and in-memory: callers provide the
metrics/events observed during a swap window, and registered probes decide
whether the swap is healthy enough to keep or should be rolled back.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

MetricMap = Mapping[str, float]
EventList = Sequence[Mapping[str, Any] | str]
ObservationProbe = Callable[[MetricMap, EventList, dict[str, Any]], "ObservationProbeResult"]


@dataclass(slots=True)
class ObservationProbeResult:
    """Outcome of one observation probe."""

    passed: bool
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ObservationWindowReport:
    """Aggregated evaluation over a supplied observation window."""

    passed: bool
    probe_results: list[tuple[str, ObservationProbeResult]] = field(default_factory=list)
    rejected_by: str | None = None
    reason: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


class ObservationWindowEvaluator:
    """Evaluates a post-swap observation window using registered probes."""

    def __init__(self, probes: list[tuple[str, ObservationProbe]] | None = None) -> None:
        self._probes: list[tuple[str, ObservationProbe]] = list(probes or [])

    def register_probe(self, name: str, probe: ObservationProbe) -> None:
        self._probes.append((name, probe))

    def evaluate(
        self,
        *,
        metrics: MetricMap | None = None,
        events: EventList | None = None,
        context: dict[str, Any] | None = None,
    ) -> ObservationWindowReport:
        metric_map: MetricMap = metrics or {}
        event_list: EventList = events or ()
        probe_context = dict(context or {})
        results: list[tuple[str, ObservationProbeResult]] = []
        for probe_name, probe in self._probes:
            result = probe(metric_map, event_list, probe_context)
            results.append((probe_name, result))
            if result.passed:
                continue
            evidence = dict(result.evidence)
            evidence.setdefault("probe", probe_name)
            return ObservationWindowReport(
                passed=False,
                probe_results=results,
                rejected_by=probe_name,
                reason=result.reason or "observation probe failed",
                evidence=evidence,
            )
        return ObservationWindowReport(
            passed=True,
            probe_results=results,
            evidence={"probes": [name for name, _ in self._probes]},
        )


def max_metric_probe(metric_name: str, threshold: float) -> ObservationProbe:
    """Create a probe that rejects when a metric exceeds ``threshold``."""

    def probe(
        metrics: MetricMap,
        events: EventList,
        context: dict[str, Any],
    ) -> ObservationProbeResult:
        del events, context
        value = metrics.get(metric_name)
        if value is None:
            return ObservationProbeResult(
                passed=False,
                reason=f"missing metric: {metric_name}",
                evidence={"metric": metric_name},
            )
        if value <= threshold:
            return ObservationProbeResult(
                passed=True,
                evidence={"metric": metric_name, "value": value, "threshold": threshold},
            )
        return ObservationProbeResult(
            passed=False,
            reason=f"metric {metric_name} exceeded threshold",
            evidence={"metric": metric_name, "value": value, "threshold": threshold},
        )

    return probe


def forbidden_event_probe(forbidden_events: set[str]) -> ObservationProbe:
    """Create a probe that rejects when a forbidden event is present."""

    def probe(
        metrics: MetricMap,
        events: EventList,
        context: dict[str, Any],
    ) -> ObservationProbeResult:
        del metrics, context
        seen: list[str] = []
        for event in events:
            name = event if isinstance(event, str) else str(event.get("name", ""))
            if name in forbidden_events:
                seen.append(name)
        if not seen:
            return ObservationProbeResult(
                passed=True, evidence={"forbidden_events": sorted(forbidden_events)}
            )
        return ObservationProbeResult(
            passed=False,
            reason="forbidden event observed",
            evidence={"forbidden_events": sorted(forbidden_events), "seen": seen},
        )

    return probe
