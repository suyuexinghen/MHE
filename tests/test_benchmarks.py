"""Tests for the benchmark runner."""

from __future__ import annotations

from metaharness.benchmarks import (
    BenchmarkResult,
    run_all_benchmarks,
    run_audit_log_benchmark,
    run_bayesian_benchmark,
    run_connection_engine_benchmark,
)


def test_connection_engine_benchmark_runs_quickly() -> None:
    result = run_connection_engine_benchmark(iterations=8)
    assert isinstance(result, BenchmarkResult)
    assert result.iterations == 8
    assert result.total_seconds >= 0.0
    assert result.per_iter_seconds >= 0.0


def test_bayesian_benchmark_runs_quickly() -> None:
    result = run_bayesian_benchmark(iterations=4)
    assert isinstance(result, BenchmarkResult)
    assert result.iterations == 4
    assert "arms" in result.attributes


def test_audit_log_benchmark_runs_quickly() -> None:
    result = run_audit_log_benchmark(iterations=16)
    assert isinstance(result, BenchmarkResult)
    assert result.iterations == 16
    assert result.attributes["root"]


def test_run_all_benchmarks_returns_results() -> None:
    results = run_all_benchmarks()
    assert len(results) == 3
    assert all(isinstance(r, BenchmarkResult) for r in results)
