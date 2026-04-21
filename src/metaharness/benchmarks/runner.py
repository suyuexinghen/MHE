"""Benchmark runner with deterministic, fast microsweeps."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.optimizer.search.bayesian import BayesianOptimizer
from metaharness.provenance.audit_log import AuditLog
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


@dataclass(slots=True)
class BenchmarkResult:
    """Single benchmark timing report."""

    name: str
    iterations: int
    total_seconds: float
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def per_iter_seconds(self) -> float:
        if self.iterations == 0:
            return 0.0
        return self.total_seconds / self.iterations


# --------------------------------------------------------------------- helpers


def _find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "examples").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError("could not locate MHE repository root")


# ------------------------------------------------------------------ benchmarks


def run_connection_engine_benchmark(iterations: int = 256) -> BenchmarkResult:
    """Stage + commit the minimal expanded topology ``iterations`` times."""

    root = _find_repo_root()
    manifest_dir = root / "examples" / "manifests" / "baseline"
    graphs_dir = root / "examples" / "graphs"

    registry = ComponentRegistry()
    for name in ["gateway", "runtime", "planner", "executor", "evaluation", "memory"]:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())

    snapshot = parse_graph_xml(graphs_dir / "minimal-expanded.xml")
    pending = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)

    start = time.perf_counter()
    for _ in range(iterations):
        engine = ConnectionEngine(registry, GraphVersionStore())
        candidate, report = engine.stage(pending)
        assert report.valid
        engine.commit("bench", candidate, report)
    end = time.perf_counter()
    return BenchmarkResult(
        name="connection_engine.stage_commit",
        iterations=iterations,
        total_seconds=end - start,
        attributes={"nodes": len(snapshot.nodes), "edges": len(snapshot.edges)},
    )


def run_bayesian_benchmark(iterations: int = 1024) -> BenchmarkResult:
    """Run the Bayesian optimizer against a small synthetic reward."""

    def reward(action: int) -> float:
        return float(action * 0.1 - ((action - 5) ** 2) * 0.05)

    actions = list(range(10))
    start = time.perf_counter()
    for _ in range(iterations):
        opt = BayesianOptimizer(beta=1.0)
        opt.optimize(actions, reward, budget=16)
    end = time.perf_counter()
    return BenchmarkResult(
        name="optimizer.bayesian.optimize",
        iterations=iterations,
        total_seconds=end - start,
        attributes={"arms": len(actions)},
    )


def run_audit_log_benchmark(iterations: int = 1024) -> BenchmarkResult:
    """Append + verify entries against the Merkle-anchored audit log."""

    log = AuditLog()
    start = time.perf_counter()
    for i in range(iterations):
        log.append("bench.entry", actor="bench", payload={"i": i})
    records = log.records()
    for record in records[-16:]:
        assert log.verify(record)
    end = time.perf_counter()
    return BenchmarkResult(
        name="audit_log.append_verify",
        iterations=iterations,
        total_seconds=end - start,
        attributes={"root": log.root_hash[:8]},
    )


def run_all_benchmarks() -> list[BenchmarkResult]:
    return [
        run_connection_engine_benchmark(),
        run_bayesian_benchmark(),
        run_audit_log_benchmark(),
    ]
