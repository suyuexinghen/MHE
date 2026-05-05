from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.benchmark_drivers.moose_cases import get_moose_cases
from metaharness.benchmark_drivers.moose_runner import MooseBenchmarkRunner
from metaharness.cli import main


def test_moose_catalog_includes_usage_and_repair_cases() -> None:
    cases = {case.case_id: case for case in get_moose_cases()}

    assert set(cases) == {"simple-diffusion-hit", "malformed-hit-proposal"}
    assert cases["simple-diffusion-hit"].suite == "moose-usage"
    assert cases["simple-diffusion-hit"].problem_definition["expected_output"] == "input_out.e"
    assert cases["malformed-hit-proposal"].metadata["malformed_direct_challenge"] is True


def test_moose_dry_run_writes_three_lane_outputs(tmp_path: Path) -> None:
    case = get_moose_cases(["simple-diffusion-hit"])[0]
    runner = MooseBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    suite_root = tmp_path / "moose-usage-benchmark"
    assert (suite_root / "extension" / case.case_id / "moose_run_plan.json").exists()
    assert (suite_root / "direct" / case.case_id / "moose_proposal_contract.json").exists()
    assert (suite_root / "agent" / case.case_id / "agent_workflow_evidence.json").exists()

    write_comparison_outputs(
        runs_root=tmp_path,
        suite="moose-usage",
        cases=[case.case_id],
        lanes=["extension", "direct", "agent"],
    )
    bundle = json.loads((suite_root / "comparison" / "result_bundle.json").read_text())
    assert (
        bundle["evidence_context"]["proposal_sources"][case.case_id]["direct"]
        == "fallback_compiler"
    )
    assert bundle["rows"][0]["direct_repair_outcome"] == "fallback_from_case_defaults"


def test_moose_malformed_proposal_records_agent_repair_advantage(tmp_path: Path) -> None:
    case = get_moose_cases(["malformed-hit-proposal"])[0]
    runner = MooseBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])
    rows = write_comparison_outputs(
        runs_root=tmp_path,
        suite="moose-usage",
        cases=[case.case_id],
        lanes=["extension", "direct", "agent"],
    )

    assert {summary.lane: summary.status for summary in summaries} == {
        "extension": "passed",
        "direct": "failed",
        "agent": "passed",
    }
    assert rows[0].direct_proposal_contract_status == "invalid"
    assert rows[0].agent_repair_outcome == "repaired_from_case_defaults"
    bundle = json.loads(
        (tmp_path / "moose-usage-benchmark" / "comparison" / "result_bundle.json").read_text()
    )
    repair_rows = bundle["evidence_context"]["repair_rows"]
    assert repair_rows[0]["repair_advantage"] == "agent_repaired_direct_failure"


def test_moose_cli_runs_dry_run_suite(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "moose-usage",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "simple-diffusion-hit",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["suite"] == "moose-usage"
    assert payload["cases"] == ["simple-diffusion-hit"]
    assert (
        tmp_path / "moose-usage-benchmark" / "extension" / "simple-diffusion-hit" / "summary.json"
    ).exists()


def test_moose_real_tool_extension_lane_skips_without_binary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MHE_MOOSE_BINARY", str(tmp_path / "missing-moose_test-opt"))
    case = get_moose_cases(["simple-diffusion-hit"])[0]
    runner = MooseBenchmarkRunner(runs_root=tmp_path, allow_real_tools=True)

    summary = runner.run_extension(case)

    assert summary.status == "skipped"
    assert summary.preflight_status == "blocked"
    capability = json.loads(
        (
            tmp_path
            / "moose-usage-benchmark"
            / "extension"
            / case.case_id
            / "capability_status.json"
        ).read_text()
    )
    assert capability["promotion_ready"] is False
    assert capability["missing_capabilities"] == ["moose_test_app_binary"]
