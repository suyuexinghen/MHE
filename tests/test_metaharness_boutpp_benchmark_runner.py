from __future__ import annotations

from pathlib import Path

from metaharness_ext.boutpp.benchmark_cases import boutpp_usage_case_catalog
from metaharness_ext.boutpp.benchmark_runner import BoutPPUsageValidationRunner


def test_boutpp_usage_case_catalog_exposes_expected_case() -> None:
    catalog = boutpp_usage_case_catalog()

    assert set(catalog) == {"conduction-basic"}
    case = catalog["conduction-basic"]
    assert case.suite == "boutpp-usage"
    assert case.expected_metrics == ["elapsed_seconds"]
    assert case.problem_definition["executable"] == "conduction"


def test_boutpp_usage_runner_writes_lane_evidence(tmp_path: Path) -> None:
    runner = BoutPPUsageValidationRunner(runs_root=tmp_path)
    case = boutpp_usage_case_catalog()["conduction-basic"]

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    base = tmp_path / "boutpp-usage-benchmark"
    assert (base / "extension" / "conduction-basic" / "BOUT.inp").exists()
    assert (base / "direct" / "conduction-basic" / "manual_cli_workflow.txt").exists()
    assert (base / "agent" / "conduction-basic" / "agent_prompt.txt").exists()
    assert (
        base / "direct" / "conduction-basic" / "usage_validation_summary.json"
    ).exists()
    assert "solver:type=rk4" in (base / "extension" / "conduction-basic" / "usage_validation.md").read_text()
