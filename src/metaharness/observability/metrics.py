"""System, component, and task-level metrics."""

from __future__ import annotations

import math
import statistics
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum


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
