from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
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
    assert (base / "direct" / "conduction-basic" / "claude_prompt.txt").exists()
    assert (base / "direct" / "conduction-basic" / "proposal_preflight.json").exists()
    assert (base / "agent" / "conduction-basic" / "agent_prompt.txt").exists()
    assert (base / "agent" / "conduction-basic" / "proposal_preflight.json").exists()
    direct_summary = json.loads((base / "direct" / "conduction-basic" / "summary.json").read_text())
    assert direct_summary["proposal_contract_status"] == "not_checked"
    assert direct_summary["preflight_status"] == "passed"
    assert direct_summary["llm_calls"] == 1
    assert (
        "solver:type=rk4"
        in (base / "extension" / "conduction-basic" / "usage_validation.md").read_text()
    )


def test_boutpp_direct_lane_fails_invalid_proposal(tmp_path: Path) -> None:
    runner = BoutPPUsageValidationRunner(
        runs_root=tmp_path,
        brain_provider=FakeClaudeCLIBrainProvider({"unexpected": True}),
    )
    case = boutpp_usage_case_catalog()["conduction-basic"]

    summary = runner.run_direct(case)

    assert summary.status == "failed"
    assert summary.proposal_contract_status == "invalid"
    assert summary.preflight_status == "failed"
    attempt_log = json.loads(
        (
            tmp_path / "boutpp-usage-benchmark" / "direct" / "conduction-basic" / "attempt_log.json"
        ).read_text()
    )
    assert attempt_log["attempts"][0]["status"] == "failed"
    preflight = json.loads(
        (
            tmp_path
            / "boutpp-usage-benchmark"
            / "direct"
            / "conduction-basic"
            / "proposal_preflight.json"
        ).read_text()
    )
    assert preflight["messages"] == ["proposal must include command or bout_inp"]


def test_boutpp_agent_lane_accepts_valid_spec_proposal(tmp_path: Path) -> None:
    case = boutpp_usage_case_catalog()["conduction-basic"]
    runner = BoutPPUsageValidationRunner(
        runs_root=tmp_path,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"boutpp_spec": {"task_id": case.case_id, **case.problem_definition}}
        ),
    )

    summary = runner.run_agent(case)

    assert summary.status == "passed"
    assert summary.proposal_contract_status == "valid"
    assert summary.preflight_status == "passed"
    preflight = json.loads(
        (
            tmp_path
            / "boutpp-usage-benchmark"
            / "agent"
            / "conduction-basic"
            / "proposal_preflight.json"
        ).read_text()
    )
    assert preflight["boutpp_spec"]["task_id"] == "conduction-basic"
