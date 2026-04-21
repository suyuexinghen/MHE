"""Performance benchmarks for Meta-Harness subsystems.

These benchmarks focus on deterministic microsweeps that run in under
a second so they are safe to invoke from CI. They report wall-clock
time and a small set of summary statistics.
"""

from metaharness.benchmarks.runner import (
    BenchmarkResult,
    run_all_benchmarks,
    run_audit_log_benchmark,
    run_bayesian_benchmark,
    run_connection_engine_benchmark,
)

__all__ = [
    "BenchmarkResult",
    "run_all_benchmarks",
    "run_audit_log_benchmark",
    "run_bayesian_benchmark",
    "run_connection_engine_benchmark",
]
