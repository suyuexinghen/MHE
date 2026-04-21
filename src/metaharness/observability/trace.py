"""Trace collection, query, and replay."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Span:
    """A single span in a trace."""

    span_id: str
    trace_id: str
    parent_id: str | None
    name: str
    start: float
    end: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        if self.end is None:
            return 0.0
        return max(0.0, self.end - self.start)

    def finish(self, *, end: float | None = None, **attributes: Any) -> None:
        self.end = end if end is not None else time.time()
        if attributes:
            self.attributes.update(attributes)

    def add_event(self, name: str, **fields: Any) -> None:
        self.events.append({"name": name, "timestamp": time.time(), **fields})


@dataclass(slots=True)
class Trace:
    """All spans recorded under a single trace id."""

    trace_id: str
    spans: list[Span] = field(default_factory=list)
    started_at: float = field(default_factory=lambda: time.time())

    def root(self) -> Span | None:
        for span in self.spans:
            if span.parent_id is None:
                return span
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "started_at": self.started_at,
            "spans": [span.__dict__ for span in self.spans],
        }


class TraceCollector:
    """In-memory trace collector.

    Supports starting and finishing spans, automatic persistence to a
    per-trace dict, and an optional eviction policy based on trace
    count. A pluggable ``sink`` callable can forward each finished span
    to an external backend.
    """

    def __init__(
        self,
        *,
        capacity: int = 1024,
        sink: Callable[[Span], None] | None = None,
    ) -> None:
        self.capacity = max(1, capacity)
        self._traces: dict[str, Trace] = {}
        self._order: list[str] = []
        self._sink = sink

    # ----------------------------------------------------------- mutations

    def start_span(
        self,
        name: str,
        *,
        trace_id: str | None = None,
        parent_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        tid = trace_id or uuid.uuid4().hex
        span = Span(
            span_id=uuid.uuid4().hex,
            trace_id=tid,
            parent_id=parent_id,
            name=name,
            start=time.time(),
            attributes=dict(attributes or {}),
        )
        trace = self._traces.get(tid)
        if trace is None:
            trace = Trace(trace_id=tid)
            self._traces[tid] = trace
            self._order.append(tid)
            while len(self._order) > self.capacity:
                dropped = self._order.pop(0)
                self._traces.pop(dropped, None)
        trace.spans.append(span)
        return span

    def finish_span(self, span: Span, **attributes: Any) -> None:
        span.finish(**attributes)
        if self._sink is not None:
            self._sink(span)

    # ------------------------------------------------------------- queries

    def get_trace(self, trace_id: str) -> Trace | None:
        return self._traces.get(trace_id)

    def traces(self) -> list[Trace]:
        return [self._traces[tid] for tid in self._order]


@dataclass(slots=True)
class TraceQuery:
    """Declarative query over a :class:`TraceCollector`."""

    collector: TraceCollector

    def by_span_name(self, name: str) -> list[Span]:
        return [s for trace in self.collector.traces() for s in trace.spans if s.name == name]

    def by_attribute(self, key: str, value: Any) -> list[Span]:
        return [
            s
            for trace in self.collector.traces()
            for s in trace.spans
            if s.attributes.get(key) == value
        ]

    def slowest(self, n: int = 5) -> list[Span]:
        spans = [span for trace in self.collector.traces() for span in trace.spans]
        spans.sort(key=lambda span: span.duration, reverse=True)
        return spans[:n]

    def filter(self, predicate: Callable[[Span], bool]) -> list[Span]:
        return [s for trace in self.collector.traces() for s in trace.spans if predicate(s)]


class TraceReplay:
    """Replay a trace by re-emitting each span into a callback.

    The replay preserves timestamp ordering and can optionally speed up
    or slow down real time via ``rate``.
    """

    def __init__(self, trace: Trace) -> None:
        self.trace = trace

    def spans_in_order(self) -> Iterable[Span]:
        return sorted(self.trace.spans, key=lambda span: span.start)

    def replay(
        self,
        handler: Callable[[Span], None],
        *,
        rate: float | None = None,
    ) -> list[Span]:
        spans = list(self.spans_in_order())
        if not spans:
            return []
        if rate is None:
            for span in spans:
                handler(span)
            return spans
        base = spans[0].start
        wall_start = time.time()
        replayed: list[Span] = []
        for span in spans:
            offset = (span.start - base) / max(rate, 1e-9)
            target = wall_start + offset
            sleep_for = max(0.0, target - time.time())
            if sleep_for:
                time.sleep(sleep_for)
            handler(span)
            replayed.append(span)
        return replayed
