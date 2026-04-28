from __future__ import annotations

import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import ClaudeCLIBrainProvider, ClaudeCLIConfig
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


def test_claude_cli_provider_writes_command_evidence(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, '{"proposal": {"ok": true}}', "")

    provider = ClaudeCLIBrainProvider(
        ClaudeCLIConfig(binary="gclaude", model="cc-gpt-5.5", max_turns=3),
        command_runner=fake_run,
    )

    result = provider.propose(prompt="hello", output_dir=tmp_path)

    assert result.error is None
    assert calls[0][:3] == ["gclaude", "-p", "hello"]
    assert "--model" in calls[0]
    assert "cc-gpt-5.5" in calls[0]
    assert (tmp_path / "claude_command.json").exists()
    assert (tmp_path / "proposal.json").exists()


def _write_lane_summary(
    tmp_path: Path,
    case: BenchmarkCaseSpec,
    lane: str,
    *,
    status: str = "passed",
    passed: bool = True,
) -> None:
    summary = LaneSummary(
        case_id=case.case_id,
        suite=case.suite,
        lane=lane,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        passed=passed,
        metrics={"error": 0.0},
        evidence_files=["evidence.txt"],
    )
    write_json(case_dir(tmp_path, case.suite, lane, case.case_id) / "summary.json", summary)


def _write_passing_lane_summary(tmp_path: Path, case: BenchmarkCaseSpec, lane: str) -> None:
    _write_lane_summary(tmp_path, case, lane)


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
        _write_passing_lane_summary(tmp_path, case, lane)

    rows = write_comparison_outputs(runs_root=tmp_path, suite="octave-native")

    assert rows[0].verdict == "all_passed"
    assert (tmp_path / "octave-native-benchmark" / "comparison" / "summary_table.csv").exists()
    assert (
        tmp_path / "octave-native-benchmark" / "reports" / "octave-native-analysis-report.md"
    ).exists()


def test_comparator_records_schema_failed_summary(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="broken",
        suite="octave-native",
        task_family="demo",
        description="broken summary case",
        required_capabilities=["octave-cli"],
        source_reference="source.m:1",
        expected_metrics=["error"],
        reference_metrics={"error": MetricReference(value=0.0, tolerance=1e-9)},
    )
    _write_passing_lane_summary(tmp_path, case, "extension")
    _write_passing_lane_summary(tmp_path, case, "agent")
    broken_dir = case_dir(tmp_path, case.suite, "direct", case.case_id)
    broken_dir.mkdir(parents=True, exist_ok=True)
    (broken_dir / "summary.json").write_text("{not-json")

    rows = write_comparison_outputs(runs_root=tmp_path, suite="octave-native")

    assert rows[0].direct_status == "schema_failed"
    assert rows[0].verdict == "schema_failed"
    assert (broken_dir / "schema_validation.json").exists()


def test_comparator_records_incomplete_when_lane_missing(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="partial",
        suite="octave-native",
        task_family="demo",
        description="partial summary case",
        required_capabilities=["octave-cli"],
        source_reference="source.m:1",
        expected_metrics=["error"],
        reference_metrics={"error": MetricReference(value=0.0, tolerance=1e-9)},
    )
    _write_passing_lane_summary(tmp_path, case, "extension")
    _write_passing_lane_summary(tmp_path, case, "direct")

    rows = write_comparison_outputs(runs_root=tmp_path, suite="octave-native")

    assert rows[0].agent_status is None
    assert rows[0].verdict == "incomplete"


def test_comparator_records_capability_skip(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="gated",
        suite="nektar-pde",
        task_family="demo",
        description="capability-gated summary case",
        required_capabilities=["nektar_diffusion_solver"],
        source_reference="source.tst:1",
        expected_metrics=["error"],
        reference_metrics={"error": MetricReference(value=0.0, tolerance=1e-9)},
    )
    _write_lane_summary(tmp_path, case, "extension", status="skipped", passed=False)
    _write_passing_lane_summary(tmp_path, case, "direct")
    _write_passing_lane_summary(tmp_path, case, "agent")

    rows = write_comparison_outputs(runs_root=tmp_path, suite="nektar-pde")

    assert rows[0].extension_status == "skipped"
    assert rows[0].verdict == "capability_skip"
