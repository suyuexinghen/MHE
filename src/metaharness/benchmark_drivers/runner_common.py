from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.io import case_dir, write_json
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    BenchmarkLane,
    LaneStatus,
    LaneSummary,
)


def expected_reference_metrics(case: BenchmarkCaseSpec) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for metric in case.expected_metrics:
        reference = case.metric_references.get(metric)
        if reference is not None and isinstance(reference.value, int | float):
            metrics[metric] = float(reference.value)
        else:
            metrics[metric] = 0.0
    return metrics


def evaluate_metrics(
    case: BenchmarkCaseSpec,
    metrics: dict[str, Any],
) -> tuple[bool, dict[str, float], list[str]]:
    missing = [metric for metric in case.expected_metrics if metric not in metrics]
    diffs: dict[str, float] = {}
    passed = not missing
    for name, reference in case.metric_references.items():
        if name not in metrics:
            continue
        actual = metrics[name]
        if not isinstance(actual, int | float | list):
            continue
        diff = reference.diff(actual)
        if diff is not None:
            diffs[name] = diff
        metric_passed = reference.passed(actual)
        if metric_passed is False:
            passed = False
    return passed, diffs, missing


def write_lane_outputs(
    *,
    runs_root: Path,
    case: BenchmarkCaseSpec,
    lane: BenchmarkLane,
    status: LaneStatus,
    metrics: dict[str, Any] | None = None,
    evidence_files: list[str] | None = None,
    attempt_log: AttemptLog | None = None,
    skip_reason: str | None = None,
    error_message: str | None = None,
    started_at: float | None = None,
) -> LaneSummary:
    output_dir = case_dir(runs_root, case.suite, lane, case.case_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = metrics or {}
    evidence_files = evidence_files or []
    attempt_log = attempt_log or AttemptLog(
        attempts=[
            AttemptRecord(
                attempt_id=1,
                lane=lane,
                status=status,
                message=skip_reason or error_message,
            )
        ]
    )
    passed, diffs, missing = evaluate_metrics(case, metrics)
    if status != "passed":
        passed = False
    elapsed = None if started_at is None else time.perf_counter() - started_at
    summary = LaneSummary(
        case_id=case.case_id,
        suite=case.suite,
        lane=lane,
        status=status,
        passed=passed,
        metrics=metrics,
        metric_diffs=diffs,
        missing_metrics=missing,
        evidence_files=evidence_files,
        attempt_count=attempt_log.attempt_count,
        repair_count=attempt_log.repair_count,
        llm_calls=attempt_log.llm_calls,
        elapsed_seconds=metrics.get("elapsed_seconds")
        if isinstance(metrics.get("elapsed_seconds"), int | float)
        else None,
        driver_time_seconds=elapsed,
        skip_reason=skip_reason,
        error_message=error_message,
    )
    write_json(output_dir / "case_spec.json", case)
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "attempt_log.json", attempt_log)
    write_json(output_dir / "summary.json", summary)
    return summary


def dry_run_summary(
    *,
    runs_root: Path,
    case: BenchmarkCaseSpec,
    lane: BenchmarkLane,
    evidence_factory: Callable[[Path], list[str]] | None = None,
) -> LaneSummary:
    started_at = time.perf_counter()
    output_dir = case_dir(runs_root, case.suite, lane, case.case_id)
    metrics = expected_reference_metrics(case)
    if "elapsed_seconds" in case.expected_metrics:
        metrics["elapsed_seconds"] = 0.0
    evidence_files = evidence_factory(output_dir) if evidence_factory else []
    status: LaneStatus = "skipped" if case.capability_gated and lane == "extension" else "passed"
    skip_reason = "capability gated for current extension dispatch" if status == "skipped" else None
    return write_lane_outputs(
        runs_root=runs_root,
        case=case,
        lane=lane,
        status=status,
        metrics=metrics,
        evidence_files=evidence_files,
        skip_reason=skip_reason,
        started_at=started_at,
    )
