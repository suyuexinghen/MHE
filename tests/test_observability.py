"""Metrics, trace, and trajectory tests."""

from __future__ import annotations

import json
from pathlib import Path

from metaharness.observability import (
    MetricsRegistry,
    TraceCollector,
    TraceQuery,
    TraceReplay,
    TrajectoryStore,
)


def test_metrics_registry_counter_gauge_histogram() -> None:
    registry = MetricsRegistry()
    c = registry.counter("events", scope="system")
    c.inc()
    c.inc(2)
    g = registry.gauge("queue_depth", scope="component", labels={"cid": "runtime"})
    g.set(10)
    g.inc(3)
    h = registry.histogram("latency", scope="task")
    for value in (1.0, 2.0, 3.0, 4.0):
        h.observe(value)
    snap = registry.snapshot()
    assert snap["system"][0]["value"] == 3.0
    assert snap["component"][0]["value"] == 13.0
    summary = snap["task"][0]["summary"]
    assert summary["count"] == 4
    assert summary["min"] == 1.0
    assert summary["max"] == 4.0


def test_metrics_timer_records_histogram() -> None:
    registry = MetricsRegistry()
    with registry.timer("op", scope="component"):
        pass
    snap = registry.snapshot()
    assert snap["component"][0]["summary"]["count"] == 1


def test_metrics_scope_isolation() -> None:
    registry = MetricsRegistry()
    registry.counter("x", scope="system")
    registry.counter("x", scope="component")
    assert {m.name for m in registry.scoped("system")} == {"x"}
    assert {m.name for m in registry.scoped("component")} == {"x"}


def test_trace_collector_and_query() -> None:
    collector = TraceCollector()
    root = collector.start_span("handle", attributes={"component": "runtime"})
    child = collector.start_span("inner", trace_id=root.trace_id, parent_id=root.span_id)
    collector.finish_span(child)
    collector.finish_span(root, status="ok")

    trace = collector.get_trace(root.trace_id)
    assert trace is not None
    assert trace.root() is root
    assert root.duration >= 0.0
    assert root.attributes["status"] == "ok"

    query = TraceQuery(collector)
    assert query.by_span_name("inner") == [child]
    assert query.by_attribute("component", "runtime") == [root]
    assert query.slowest(1)  # at least one span


def test_trace_collector_capacity_eviction() -> None:
    collector = TraceCollector(capacity=2)
    for _ in range(5):
        collector.start_span("s")
    assert len(collector.traces()) == 2


def test_trace_replay_preserves_order() -> None:
    collector = TraceCollector()
    root = collector.start_span("a")
    child = collector.start_span("b", trace_id=root.trace_id, parent_id=root.span_id)
    collector.finish_span(child)
    collector.finish_span(root)
    trace = collector.get_trace(root.trace_id)
    assert trace is not None

    seen: list[str] = []
    TraceReplay(trace).replay(lambda span: seen.append(span.name))
    assert seen == ["a", "b"]


def test_trajectory_store_round_trip(tmp_path: Path) -> None:
    store = TrajectoryStore(path=tmp_path / "traj.jsonl")
    traj = store.start(trace_id="t-1")
    traj.append("runtime.primary", "activated")
    traj.append("executor.primary", "committed", detail={"score": 0.9})
    traj.finish()

    assert store.by_trace("t-1") == [traj]
    path = store.flush()
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert lines[0]["steps"][1]["detail"]["score"] == 0.9
