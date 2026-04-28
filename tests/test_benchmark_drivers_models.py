from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.benchmark_drivers.io import case_dir, write_json
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    LaneSummary,
    MetricReference,
)
from metaharness.benchmark_drivers.octave_cases import octave_case_catalog


def test_metric_reference_accepts_scalar_tolerance() -> None:
    reference = MetricReference(value=1.0, tolerance=0.1)

    assert reference.diff(1.05) == 0.050000000000000044
    assert reference.passed(1.05)
    assert not reference.passed(1.2)


def test_attempt_log_counts_repairs_and_llm_calls() -> None:
    log = AttemptLog(
        attempts=[
            AttemptRecord(attempt_id=1, lane="agent", status="failed", llm_call=True),
            AttemptRecord(attempt_id=2, lane="agent", status="passed", llm_call=True, repair=True),
        ]
    )

    assert log.attempt_count == 2
    assert log.repair_count == 1
    assert log.llm_calls == 2


def test_octave_catalog_contains_documented_cases() -> None:
    catalog = octave_case_catalog()

    assert set(catalog) == {
        "ode45-vanderpol",
        "ode45-exp-decay",
        "ode23-exp-decay",
        "ode23s-linear-stiff",
        "fsolve-3x3",
        "fsolve-exp-fit",
        "fminunc-rosenbrock-2d",
        "expm-jordan-2x2",
        "roots-cubic",
        "sinc-values",
    }
    assert all(case.expected_metrics for case in catalog.values())
    assert all(case.required_capabilities for case in catalog.values())


def test_comparator_writes_reports_from_synthetic_summaries(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="demo",
        suite="octave-native",
        task_family="demo",
        description="demo case",
        required_capabilities=["octave-cli"],
        source_reference="source.m:1",
        expected_metrics=["error"],
        reference_metrics={"error": MetricReference(value=0.0, tolerance=1e-9)},
    )
    for lane in ["extension", "direct", "agent"]:
        summary = LaneSummary(
            case_id=case.case_id,
            suite=case.suite,
            lane=lane,
            status="passed",
            passed=True,
            metrics={"error": 0.0},
            evidence_files=["evidence.txt"],
        )
        write_json(case_dir(tmp_path, case.suite, lane, case.case_id) / "summary.json", summary)

    rows = write_comparison_outputs(runs_root=tmp_path, suite="octave-native")

    assert rows[0].verdict == "all_passed"
    assert (tmp_path / "octave-native-benchmark" / "comparison" / "summary_table.csv").exists()
    assert (
        tmp_path / "octave-native-benchmark" / "reports" / "octave-native-analysis-report.md"
    ).exists()
