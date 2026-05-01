from __future__ import annotations

import json
import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.acp_provider import ACPBrainConfig, ACPBrainProvider
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


def test_claude_cli_provider_reports_stdout_error_payload(tmp_path: Path) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            '{"is_error": true, "errors": ["Reached maximum number of turns (2)"]}',
            "",
        )

    provider = ClaudeCLIBrainProvider(ClaudeCLIConfig(binary="gclaude"), command_runner=fake_run)

    result = provider.propose(prompt="hello", output_dir=tmp_path)

    assert result.error == "Reached maximum number of turns (2)"
    assert result.result["is_error"] is True
    assert (tmp_path / "claude_result.json").exists()
    assert not (tmp_path / "proposal.json").exists()


def test_acp_provider_extracts_json_proposal(tmp_path: Path) -> None:
    class StubACPProvider(ACPBrainProvider):
        async def _run_acp_prompt(self, prompt: str) -> dict[str, object]:
            return {
                "transport": "acp",
                "content": '{"proposal": {"script": "solve.m"}}',
                "usage": {},
                "execution_meta": {"acp_session_id": "session-1"},
            }

    provider = StubACPProvider(ACPBrainConfig(command=["agent-acp"], session_key="case-1"))

    result = provider.propose(prompt="hello", output_dir=tmp_path)

    assert result.error is None
    assert result.proposal == {"script": "solve.m"}
    assert result.invocation.command == ["agent-acp"]
    assert (tmp_path / "acp_command.json").exists()
    assert (tmp_path / "proposal.json").exists()


def test_acp_provider_reports_missing_json_proposal(tmp_path: Path) -> None:
    class StubACPProvider(ACPBrainProvider):
        async def _run_acp_prompt(self, prompt: str) -> dict[str, object]:
            return {"transport": "acp", "content": "not json", "usage": {}, "execution_meta": {}}

    result = StubACPProvider().propose(prompt="hello", output_dir=tmp_path)

    assert result.error == "ACP response did not contain a JSON proposal"
    assert result.proposal == {}
    assert (tmp_path / "acp_result.json").exists()


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


def test_comparator_writes_blocked_approval_gate_from_policy(tmp_path: Path) -> None:
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
    config_root = tmp_path / ".mhe"
    approvals_root = config_root / "approvals"
    benchmarks_root = config_root / "benchmarks"
    approvals_root.mkdir(parents=True)
    benchmarks_root.mkdir()
    (config_root / "config.json").write_text(
        json.dumps(
            {
                "approval": {
                    "profiles": {
                        "benchmark_promotion_admin_approval": {
                            "manifest": ".mhe/approvals/comparison_benchmark_approval.json",
                            "required_fields": [
                                "approved_by",
                                "approval_role",
                                "approved_scope",
                                "evidence_refs",
                                "approval_decision",
                            ],
                        }
                    }
                }
            }
        )
    )
    (benchmarks_root / "comparison-approval.json").write_text(
        json.dumps(
            {
                "policy_id": "comparison_benchmarks_require_admin_approval",
                "required_approval_profiles": ["benchmark_promotion_admin_approval"],
            }
        )
    )
    (approvals_root / "comparison_benchmark_approval.json").write_text(
        json.dumps(
            {
                "status": "pending_admin_review",
                "approved_by": None,
                "approval_role": None,
                "approved_scope": {},
                "evidence_refs": [],
                "approval_decision": None,
            }
        )
    )

    write_comparison_outputs(
        runs_root=tmp_path,
        suite="octave-native",
        approval_config_root=config_root,
    )

    gate = json.loads(
        (tmp_path / "octave-native-benchmark" / "comparison" / "approval_gate.json").read_text()
    )
    bundle = json.loads(
        (tmp_path / "octave-native-benchmark" / "comparison" / "result_bundle.json").read_text()
    )
    csv_text = (
        tmp_path / "octave-native-benchmark" / "comparison" / "summary_table.csv"
    ).read_text()
    report = (
        tmp_path / "octave-native-benchmark" / "comparison" / "comparison_report.md"
    ).read_text()
    assert gate["status"] == "blocked"
    assert gate["approval_ready"] is False
    assert (
        "benchmark_promotion_admin_approval_not_approved"
        in gate["missing_evidence_by_category"]["human_approval"]
    )
    assert bundle["evidence_context"]["approval_gate"]["status"] == "blocked"
    assert "approval_gate_status" in csv_text
    assert "benchmark_promotion_admin_approval_not_approved" in csv_text
    assert "## Approval gate" in report
    assert "benchmark_promotion_admin_approval" in report


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


def test_comparator_records_agent_repaired_success_verdict(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="repair-demo",
        suite="octave-native",
        task_family="demo",
        description="repair demo case",
        required_capabilities=["octave-cli"],
        source_reference="source.m:1",
        expected_metrics=["error"],
        reference_metrics={"error": MetricReference(value=0.0, tolerance=1e-9)},
    )
    _write_passing_lane_summary(tmp_path, case, "extension")
    _write_lane_summary(tmp_path, case, "direct", status="failed", passed=False)
    agent_summary = LaneSummary(
        case_id=case.case_id,
        suite=case.suite,
        lane="agent",
        status="passed",
        passed=True,
        metrics={"error": 0.0},
        evidence_files=["evidence.txt"],
        repair_count=1,
        repair_outcome="repaired_success",
        diagnostics_files=["adaptive_diagnostics_1.json"],
    )
    write_json(
        case_dir(tmp_path, case.suite, "agent", case.case_id) / "summary.json", agent_summary
    )

    rows = write_comparison_outputs(runs_root=tmp_path, suite="octave-native")

    assert rows[0].verdict == "agent_repaired_success"
    assert rows[0].agent_repair_outcome == "repaired_success"
    assert rows[0].agent_diagnostics_count == 1


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
