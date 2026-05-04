"""Metrics, trace, and trajectory tests."""

from __future__ import annotations

import json
from pathlib import Path

from metaharness.cli import main
from metaharness.core.assembly import AssemblyLedger, CopyCountIndex
from metaharness.core.execution_modes import ExecutionMode, InstantiationRecord
from metaharness.core.selection import SelectionLifecycle
from metaharness.observability import (
    AssemblyMetricsService,
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


def test_assembly_metrics_service_collects_evidence_boundaries() -> None:
    ledger = AssemblyLedger()
    copy_counts = CopyCountIndex()
    ledger.record_component_registered("solver.primary")
    ledger.record_component_registered("validator.primary")
    copy_counts.mark_committed_member("solver.primary")
    graph = ledger.record_dependency_graph(
        candidate_id="candidate-1",
        graph_version=1,
        component_refs=["solver.primary", "validator.primary"],
        dependency_edges=[("solver.primary", "validator.primary")],
        copy_count_index=copy_counts,
    )
    health = ledger.health_summary(
        candidate_id="candidate-1",
        graph_version=1,
        component_refs=["solver.primary", "validator.primary"],
        edge_count=1,
        copy_count_index=copy_counts,
        dependency_graph_snapshot=graph,
    )
    selection = SelectionLifecycle()
    selection.promote("solver.primary", candidate_id="candidate-1", graph_version=1)
    report = AssemblyMetricsService().collect(
        assembly_ledger=ledger,
        copy_count_index=copy_counts,
        health_summaries=[health],
        instantiation_records=[
            {"execution_mode": "unknown"},
            InstantiationRecord(
                execution_mode=ExecutionMode.EXTERNAL_VERIFIED,
                external_evidence_refs=["receipt:external"],
            ),
        ],
        selection_lifecycle=selection,
    )

    assert report["summary"]["dependency_graph_count"] == 1
    assert report["summary"]["max_assembly_index"] == 2
    assert report["summary"]["external_verified_instantiation_count"] == 1
    assert report["summary"]["unknown_instantiation_count"] == 1
    assert report["summary"]["selection_state_counts"] == {"promoted": 1}
    metrics = report["metrics"]["assembly"]
    assert any(metric["name"] == "dependency_graph_assembly_index" for metric in metrics)
    markdown = AssemblyMetricsService().render_markdown(report)
    assert "dry-run or simulation evidence is not real-world instantiation" in markdown


def test_assembly_metrics_cli_reports_json_and_markdown(tmp_path: Path, capsys) -> None:
    markdown_path = tmp_path / "assembly-metrics.md"
    instantiation_path = tmp_path / "instantiation.json"
    instantiation_path.write_text(
        json.dumps(
            {
                "execution_mode": "external_verified",
                "reconciliation_status": "externally_verified",
                "external_evidence_refs": ["receipt:external"],
            }
        )
    )
    status = main(
        [
            "metrics",
            "assembly",
            "--graph",
            "examples/graphs/minimal-happy-path.xml",
            "--manifests",
            "examples/manifests/baseline",
            "--instantiation-record",
            str(instantiation_path),
            "--markdown-report",
            str(markdown_path),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "metaharness.assembly_metrics.v1"
    assert payload["source"]["graph_version"] == 1
    assert payload["summary"]["dependency_graph_count"] >= 1
    assert payload["summary"]["selection_state_counts"]["promoted"] >= 1
    assert payload["summary"]["external_verified_instantiation_count"] == 1
    assert markdown_path.exists()
    assert (
        "unknown evidence is not counted as externally verified execution"
        in markdown_path.read_text()
    )


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
