"""System, component, and task-level metrics."""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import Any


class MetricKind(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class Metric:
    """Base metric record (snapshot-friendly)."""

    name: str
    kind: MetricKind
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class Counter(Metric):
    value: float = 0.0

    def __init__(self, name: str, labels: dict[str, str] | None = None, value: float = 0.0) -> None:
        super().__init__(name=name, kind=MetricKind.COUNTER, labels=dict(labels or {}))
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount


@dataclass
class Gauge(Metric):
    value: float = 0.0

    def __init__(self, name: str, labels: dict[str, str] | None = None, value: float = 0.0) -> None:
        super().__init__(name=name, kind=MetricKind.GAUGE, labels=dict(labels or {}))
        self.value = value

    def set(self, value: float) -> None:
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        self.value -= amount


@dataclass
class Histogram(Metric):
    samples: list[float] = field(default_factory=list)

    def __init__(self, name: str, labels: dict[str, str] | None = None) -> None:
        super().__init__(name=name, kind=MetricKind.HISTOGRAM, labels=dict(labels or {}))
        self.samples = []

    def observe(self, value: float) -> None:
        if math.isnan(value):
            return
        self.samples.append(float(value))

    def summary(self) -> dict[str, float]:
        if not self.samples:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "p50": 0.0, "p95": 0.0}
        sorted_samples = sorted(self.samples)
        return {
            "count": len(sorted_samples),
            "mean": statistics.fmean(sorted_samples),
            "min": sorted_samples[0],
            "max": sorted_samples[-1],
            "p50": _percentile(sorted_samples, 0.50),
            "p95": _percentile(sorted_samples, 0.95),
        }


def _percentile(sorted_samples: list[float], q: float) -> float:
    if not sorted_samples:
        return 0.0
    k = (len(sorted_samples) - 1) * q
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_samples[int(k)]
    d0 = sorted_samples[int(f)] * (c - k)
    d1 = sorted_samples[int(c)] * (k - f)
    return d0 + d1


@dataclass(slots=True)
class _TimerContext:
    """Context manager returned by :meth:`MetricsRegistry.timer`."""

    registry: MetricsRegistry
    name: str
    scope: str
    labels: dict[str, str]
    start: float = 0.0

    def __enter__(self) -> _TimerContext:
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        elapsed = time.perf_counter() - self.start
        self.registry.histogram(self.name, scope=self.scope, labels=self.labels).observe(elapsed)


class MetricsRegistry:
    """Central, in-memory metrics registry.

    The registry namespaces metrics by ``scope`` (``system``, ``component``,
    ``task``) so collectors can be composed independently. All state is
    kept in-process; external exporters can iterate the snapshot.
    """

    def __init__(self) -> None:
        self._metrics: dict[tuple[str, str, tuple[tuple[str, str], ...]], Metric] = {}

    # --------------------------------------------------------- registration

    def counter(
        self, name: str, *, scope: str = "system", labels: dict[str, str] | None = None
    ) -> Counter:
        key = self._key(scope, name, labels)
        existing = self._metrics.get(key)
        if isinstance(existing, Counter):
            return existing
        metric = Counter(name=name, labels=dict(labels or {}))
        self._metrics[key] = metric
        return metric

    def gauge(
        self, name: str, *, scope: str = "system", labels: dict[str, str] | None = None
    ) -> Gauge:
        key = self._key(scope, name, labels)
        existing = self._metrics.get(key)
        if isinstance(existing, Gauge):
            return existing
        metric = Gauge(name=name, labels=dict(labels or {}))
        self._metrics[key] = metric
        return metric

    def histogram(
        self, name: str, *, scope: str = "system", labels: dict[str, str] | None = None
    ) -> Histogram:
        key = self._key(scope, name, labels)
        existing = self._metrics.get(key)
        if isinstance(existing, Histogram):
            return existing
        metric = Histogram(name=name, labels=dict(labels or {}))
        self._metrics[key] = metric
        return metric

    def timer(
        self, name: str, *, scope: str = "system", labels: dict[str, str] | None = None
    ) -> _TimerContext:
        return _TimerContext(registry=self, name=name, scope=scope, labels=dict(labels or {}))

    # ----------------------------------------------------------- inspection

    def snapshot(self) -> dict[str, list[dict[str, object]]]:
        out: dict[str, list[dict[str, object]]] = {}
        for (scope, name, _), metric in self._metrics.items():
            entry: dict[str, object] = {
                "name": name,
                "kind": metric.kind.value,
                "labels": dict(metric.labels),
            }
            if isinstance(metric, Counter | Gauge):
                entry["value"] = metric.value
            elif isinstance(metric, Histogram):
                entry["summary"] = metric.summary()
            out.setdefault(scope, []).append(entry)
        return out

    def scoped(self, scope: str) -> list[Metric]:
        return [metric for (s, _, _), metric in self._metrics.items() if s == scope]

    def all(self) -> Iterable[Metric]:
        return self._metrics.values()

    # --------------------------------------------------------------- helpers

    @staticmethod
    def _key(
        scope: str, name: str, labels: dict[str, str] | None
    ) -> tuple[str, str, tuple[tuple[str, str], ...]]:
        return (scope, name, tuple(sorted((labels or {}).items())))


class AssemblyMetricsService:
    """Aggregates assembly, instantiation, and selection evidence into metrics."""

    schema = "metaharness.assembly_metrics.v1"
    scope = "assembly"
    non_claims = [
        "metrics do not prove scientific validity",
        "dry-run or simulation evidence is not real-world instantiation",
        "unknown evidence is not counted as externally verified execution",
    ]

    def __init__(self, registry: MetricsRegistry | None = None) -> None:
        self.registry = registry or MetricsRegistry()

    def collect(
        self,
        *,
        assembly_ledger: Any | None = None,
        copy_count_index: Any | None = None,
        health_summaries: Sequence[Any] | None = None,
        instantiation_records: Sequence[Any] | None = None,
        selection_lifecycle: Any | None = None,
    ) -> dict[str, Any]:
        records = self._records(assembly_ledger)
        graphs = self._dependency_graphs(assembly_ledger)
        copy_records = self._copy_records(copy_count_index)
        health_items = [self._object(item) for item in health_summaries or []]
        instantiation_items = [self._object(item) for item in instantiation_records or []]
        selection_states = self._selection_states(selection_lifecycle)

        self._record_assembly_records(records)
        self._record_dependency_graphs(graphs)
        self._record_copy_counts(copy_records)
        self._record_health_summaries(health_items)
        self._record_instantiation_records(instantiation_items)
        self._record_selection_states(selection_states)

        return {
            "schema": self.schema,
            "summary": self._summary(
                records=records,
                graphs=graphs,
                copy_records=copy_records,
                health_summaries=health_items,
                instantiation_records=instantiation_items,
                selection_states=selection_states,
            ),
            "metrics": self.registry.snapshot(),
            "non_claims": list(self.non_claims),
        }

    def render_markdown(self, report: dict[str, Any]) -> str:
        summary = report.get("summary", {})
        lines = [
            "# Assembly Metrics Report",
            "",
            "## Summary",
            "",
            f"- Assembly records: {summary.get('assembly_record_count', 0)}",
            f"- Dependency graph snapshots: {summary.get('dependency_graph_count', 0)}",
            f"- Copy-count records: {summary.get('copy_count_record_count', 0)}",
            f"- Max assembly index: {summary.get('max_assembly_index', 0)}",
            f"- External verified instantiations: "
            f"{summary.get('external_verified_instantiation_count', 0)}",
            "",
            "## Evidence Boundaries",
            "",
        ]
        lines.extend(f"- {claim}" for claim in report.get("non_claims", self.non_claims))
        return "\n".join(lines) + "\n"

    def write_markdown_report(self, report: dict[str, Any], path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_markdown(report))
        return path

    def _record_assembly_records(self, records: list[Any]) -> None:
        counts: dict[tuple[str, str], int] = {}
        for record in records:
            key = (str(record.artifact_kind), str(record.lineage_status))
            counts[key] = counts.get(key, 0) + 1
        for (artifact_kind, lineage_status), count in counts.items():
            self._gauge(
                "assembly_records_total",
                count,
                {"artifact_kind": artifact_kind, "lineage_status": lineage_status},
            )

    def _record_dependency_graphs(self, graphs: list[Any]) -> None:
        self._gauge("dependency_graph_snapshots_total", len(graphs), {})
        for graph in graphs:
            labels = self._candidate_labels(graph)
            labels["lineage_status"] = str(graph.lineage_status)
            self._gauge("dependency_graph_assembly_index", graph.assembly_index, labels)
            self._gauge("dependency_graph_lineage_completeness", graph.lineage_completeness, labels)
            self._gauge(
                "dependency_graph_history_folding_ratio", graph.history_folding_ratio, labels
            )
            self._gauge(
                "dependency_graph_low_copy_critical_dependencies",
                graph.low_copy_critical_dependency_count,
                labels,
            )

    def _record_copy_counts(self, copy_records: list[Any]) -> None:
        self._gauge("copy_count_records_total", len(copy_records), {})
        for record in copy_records:
            labels = {"artifact_ref": str(record.artifact_ref)}
            self._gauge("copy_count_graph_reuse", record.graph_reuse_count, labels)
            self._gauge("copy_count_invocations", record.invoked_count, labels)
            self._gauge("copy_count_external_verified", record.external_verified_count, labels)

    def _record_health_summaries(self, health_summaries: list[Any]) -> None:
        self._gauge("assembly_health_summaries_total", len(health_summaries), {})
        for summary in health_summaries:
            labels = self._candidate_labels(summary)
            labels["lineage_status"] = str(summary.lineage_status)
            self._gauge("assembly_health_component_count", summary.component_count, labels)
            self._gauge("assembly_health_edge_count", summary.edge_count, labels)
            self._gauge("assembly_health_assembly_index", summary.assembly_index, labels)
            self._gauge(
                "assembly_health_history_folding_ratio", summary.history_folding_ratio, labels
            )
            self._gauge(
                "assembly_health_low_copy_critical_dependencies",
                summary.low_copy_critical_dependency_count,
                labels,
            )

    def _record_instantiation_records(self, instantiation_records: list[Any]) -> None:
        counts: dict[tuple[str, str], int] = {}
        external_verified = 0
        for record in instantiation_records:
            mode = self._execution_mode(record)
            status = self._text(record, "reconciliation_status", "unknown")
            counts[(mode, status)] = counts.get((mode, status), 0) + 1
            if self._is_externally_verified(record):
                external_verified += 1
        for (mode, status), count in counts.items():
            self._gauge(
                "instantiation_records_total",
                count,
                {"execution_mode": mode, "reconciliation_status": status},
            )
        self._gauge("instantiation_external_verified_records_total", external_verified, {})

    def _record_selection_states(self, selection_states: list[Any]) -> None:
        counts: dict[str, int] = {}
        for state in selection_states:
            state_value = str(getattr(state.state, "value", state.state))
            counts[state_value] = counts.get(state_value, 0) + 1
        for state, count in counts.items():
            self._gauge("selection_states_total", count, {"state": state})

    def _summary(
        self,
        *,
        records: list[Any],
        graphs: list[Any],
        copy_records: list[Any],
        health_summaries: list[Any],
        instantiation_records: list[Any],
        selection_states: list[Any],
    ) -> dict[str, Any]:
        selection_counts: dict[str, int] = {}
        for selection_state in selection_states:
            state = str(getattr(selection_state.state, "value", selection_state.state))
            selection_counts[state] = selection_counts.get(state, 0) + 1
        lineage_counts: dict[str, int] = {}
        for graph in graphs:
            lineage_counts[str(graph.lineage_status)] = (
                lineage_counts.get(str(graph.lineage_status), 0) + 1
            )
        externally_verified = [
            record for record in instantiation_records if self._is_externally_verified(record)
        ]
        unknown_instantiations = [
            record for record in instantiation_records if self._execution_mode(record) == "unknown"
        ]
        return {
            "assembly_record_count": len(records),
            "dependency_graph_count": len(graphs),
            "copy_count_record_count": len(copy_records),
            "assembly_health_summary_count": len(health_summaries),
            "instantiation_record_count": len(instantiation_records),
            "selection_state_count": len(selection_states),
            "selection_state_counts": selection_counts,
            "lineage_status_counts": lineage_counts,
            "max_assembly_index": max((graph.assembly_index for graph in graphs), default=0),
            "average_history_folding_ratio": statistics.fmean(
                [graph.history_folding_ratio for graph in graphs]
            )
            if graphs
            else 0.0,
            "external_verified_instantiation_count": len(externally_verified),
            "unknown_instantiation_count": len(unknown_instantiations),
        }

    def _gauge(self, name: str, value: float, labels: dict[str, str]) -> None:
        self.registry.gauge(name, scope=self.scope, labels=labels).set(float(value))

    def _records(self, assembly_ledger: Any | None) -> list[Any]:
        if assembly_ledger is None:
            return []
        return list(getattr(assembly_ledger, "records", []))

    def _dependency_graphs(self, assembly_ledger: Any | None) -> list[Any]:
        if assembly_ledger is None or not hasattr(assembly_ledger, "dependency_graphs"):
            return []
        return list(assembly_ledger.dependency_graphs())

    def _copy_records(self, copy_count_index: Any | None) -> list[Any]:
        if copy_count_index is None or not hasattr(copy_count_index, "records_for"):
            return []
        return list(copy_count_index.records_for())

    def _selection_states(self, selection_lifecycle: Any | None) -> list[Any]:
        if selection_lifecycle is None or not hasattr(selection_lifecycle, "states"):
            return []
        return list(selection_lifecycle.states())

    def _candidate_labels(self, item: Any) -> dict[str, str]:
        return {
            "candidate_id": str(item.candidate_id or ""),
            "graph_version": str(item.graph_version or ""),
        }

    def _execution_mode(self, item: Any) -> str:
        mode = getattr(item, "execution_mode", "unknown")
        return str(getattr(mode, "value", mode))

    def _is_externally_verified(self, item: Any) -> bool:
        return self._execution_mode(item) == "external_verified" and bool(
            getattr(item, "external_evidence_refs", [])
        )

    def _text(self, item: Any, name: str, default: str) -> str:
        return str(getattr(item, name, default) or default)

    def _object(self, item: Any) -> Any:
        if isinstance(item, dict):
            return SimpleNamespace(**item)
        return item
