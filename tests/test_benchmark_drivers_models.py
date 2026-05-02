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
    metrics: dict[str, float] | None = None,
    metric_diffs: dict[str, float] | None = None,
) -> None:
    summary = LaneSummary(
        case_id=case.case_id,
        suite=case.suite,
        lane=lane,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        passed=passed,
        metrics=metrics or {"error": 0.0},
        metric_diffs=metric_diffs or {},
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


def test_comparator_writes_metric_detail_tables(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="advdiff-2d",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="Nektar metric case",
        required_capabilities=["nektar_adr_solver"],
        source_reference="source.tst",
        expected_metrics=["l2_error_u", "linf_error_u", "elapsed_seconds"],
        reference_metrics={
            "l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8),
            "linf_error_u": MetricReference(value=0.00275937, tolerance=1e-8),
        },
    )
    metrics = {
        "l2_error_u": 0.00135233,
        "linf_error_u": 0.00275937,
        "elapsed_seconds": 2.0,
    }
    for lane in ["extension", "direct", "agent"]:
        _write_lane_summary(
            tmp_path,
            case,
            lane,
            metrics=metrics,
            metric_diffs={"l2_error_u": 0.0, "linf_error_u": 0.0},
        )

    write_comparison_outputs(runs_root=tmp_path, suite="nektar-pde")

    comparison_dir = tmp_path / "nektar-pde-benchmark" / "comparison"
    report = (comparison_dir / "comparison_report.md").read_text()
    analysis = (
        tmp_path / "nektar-pde-benchmark" / "reports" / "nektar-pde-analysis-report.md"
    ).read_text()
    bundle = json.loads((comparison_dir / "result_bundle.json").read_text())
    assert "## Metric details" in report
    assert "| advdiff-2d | direct | l2_error_u | 0.00135233 | 0.0 | passed | True |" in report
    assert "linf_error_u" in analysis
    assert bundle["evidence_context"]["metric_rows"][0]["metric"] == "l2_error_u"
    assert all(
        row["metric"] != "elapsed_seconds" for row in bundle["evidence_context"]["metric_rows"]
    )


def test_comparator_writes_preflight_summary_tables(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="advdiff-2d",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="Nektar preflight case",
        required_capabilities=["nektar_adr_solver"],
        source_reference="source.tst",
        expected_metrics=["l2_error_u"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
    )
    for lane in ["extension", "direct", "agent"]:
        _write_passing_lane_summary(tmp_path, case, lane)
    write_json(
        tmp_path / "nektar-pde-benchmark" / "preflight" / "advdiff-2d" / "tester_summary.json",
        {
            "case_id": "advdiff-2d",
            "status": "ready",
            "preflight_executed": True,
            "tester_available": True,
            "solver_available": True,
            "tst_available": True,
            "reference_metric_count": 2,
            "tester_return_code": 0,
            "alternative_validation": None,
        },
    )

    write_comparison_outputs(runs_root=tmp_path, suite="nektar-pde")

    comparison_dir = tmp_path / "nektar-pde-benchmark" / "comparison"
    report = (comparison_dir / "comparison_report.md").read_text()
    analysis = (
        tmp_path / "nektar-pde-benchmark" / "reports" / "nektar-pde-analysis-report.md"
    ).read_text()
    bundle = json.loads((comparison_dir / "result_bundle.json").read_text())
    assert "## Preflight summaries" in report
    assert "| advdiff-2d | ready | True | True | True | True | 2 | 0 | none |" in report
    assert "## Preflight summaries" in analysis
    assert bundle["evidence_context"]["preflight_rows"][0]["status"] == "ready"


def test_comparator_writes_capability_gate_tables(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="euler-1d",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="Nektar capability gate case",
        required_capabilities=["nektar_compressible_solver"],
        source_reference={"tst": "Euler1D.tst", "xml": "Euler1D.xml"},
        expected_metrics=["l2_error_rho"],
        reference_metrics={"l2_error_rho": MetricReference(value=1.98838e-6, tolerance=1e-8)},
        problem_definition={
            "solver_family": "compressible",
            "solver_binary": "CompressibleFlowSolver",
        },
        capability_gated=True,
    )
    _write_lane_summary(tmp_path, case, "extension", status="skipped", passed=False)
    write_json(
        tmp_path / "nektar-pde-benchmark" / "extension" / "euler-1d" / "source_refs.json",
        {"case_id": "euler-1d", "source_reference": case.source_reference},
    )
    write_json(
        tmp_path / "nektar-pde-benchmark" / "extension" / "euler-1d" / "capability_status.json",
        {
            "case_id": "euler-1d",
            "status": "capability_gated",
            "promotion_ready": False,
            "missing_capabilities": ["nektar_compressible_solver_extension_dispatch"],
            "solver_binary": "CompressibleFlowSolver",
            "solver_family": "compressible",
            "plan_status": "extension_dispatch_unverified",
        },
    )

    write_comparison_outputs(runs_root=tmp_path, suite="nektar-pde")

    comparison_dir = tmp_path / "nektar-pde-benchmark" / "comparison"
    report = (comparison_dir / "comparison_report.md").read_text()
    analysis = (
        tmp_path / "nektar-pde-benchmark" / "reports" / "nektar-pde-analysis-report.md"
    ).read_text()
    bundle = json.loads((comparison_dir / "result_bundle.json").read_text())
    capability_rows = bundle["evidence_context"]["capability_gate_rows"]
    assert "## Capability gates" in report
    assert "## Capability gates" in analysis
    assert "nektar_compressible_solver_extension_dispatch" in report
    assert capability_rows[0]["case_id"] == "euler-1d"
    assert capability_rows[0]["promotion_ready"] is False
    assert capability_rows[0]["source_refs_path"].endswith("source_refs.json")


def test_comparator_reports_malformed_and_missing_capability_status(tmp_path: Path) -> None:
    malformed_case = BenchmarkCaseSpec(
        case_id="malformed-gate",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="Malformed capability gate case",
        required_capabilities=["nektar_unknown_solver"],
        source_reference="malformed.tst",
        expected_metrics=[],
    )
    missing_case = BenchmarkCaseSpec(
        case_id="missing-gate",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="Missing capability gate case",
        required_capabilities=["nektar_unknown_solver"],
        source_reference="missing.tst",
        expected_metrics=[],
    )
    _write_lane_summary(tmp_path, malformed_case, "extension", status="skipped", passed=False)
    _write_lane_summary(tmp_path, missing_case, "extension", status="skipped", passed=False)
    malformed_root = tmp_path / "nektar-pde-benchmark" / "extension" / "malformed-gate"
    missing_root = tmp_path / "nektar-pde-benchmark" / "extension" / "missing-gate"
    (malformed_root / "capability_status.json").write_text("not-json")
    write_json(malformed_root / "source_refs.json", {"case_id": "malformed-gate"})
    write_json(missing_root / "source_refs.json", {"case_id": "missing-gate"})

    write_comparison_outputs(runs_root=tmp_path, suite="nektar-pde")

    comparison_dir = tmp_path / "nektar-pde-benchmark" / "comparison"
    report = (comparison_dir / "comparison_report.md").read_text()
    bundle = json.loads((comparison_dir / "result_bundle.json").read_text())
    rows = {row["case_id"]: row for row in bundle["evidence_context"]["capability_gate_rows"]}
    assert rows["malformed-gate"]["status"] == "schema_failed"
    assert rows["missing-gate"]["status"] == "missing"
    assert rows["missing-gate"]["missing_capabilities"] == ["capability_status_missing"]
    assert "capability_status_unreadable" in report
    assert "capability_status_missing" in report


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
    backlog = (
        tmp_path / "octave-native-benchmark" / "reports" / "octave-native-backlog.md"
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
    assert "## Approval gate blockers" in backlog
    assert "benchmark_promotion_admin_approval_not_approved" in backlog


def test_comparator_writes_approved_approval_gate_from_policy(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="approved-demo",
        suite="octave-native",
        task_family="demo",
        description="approved demo case",
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
                "status": "approved",
                "approved_by": "admin@example.test",
                "approval_role": "benchmark-admin",
                "approved_scope": {"suite": "octave-native"},
                "evidence_refs": ["comparison/result_bundle.json"],
                "approval_decision": "approved",
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
    csv_text = (
        tmp_path / "octave-native-benchmark" / "comparison" / "summary_table.csv"
    ).read_text()
    report = (
        tmp_path / "octave-native-benchmark" / "comparison" / "comparison_report.md"
    ).read_text()
    backlog = (
        tmp_path / "octave-native-benchmark" / "reports" / "octave-native-backlog.md"
    ).read_text()
    assert gate["status"] == "approved"
    assert gate["approval_ready"] is True
    assert gate["missing_evidence_by_category"]["human_approval"] == []
    assert "Approval gate: `approved`" in report
    assert "approval_ready" in csv_text
    assert "## Approval gate blockers" not in backlog


def test_comparator_categorizes_abacus_scientific_approval_blockers(tmp_path: Path) -> None:
    case = BenchmarkCaseSpec(
        case_id="abacus-hs-bridge-pending",
        suite="qcompute-abacus",
        task_family="abacus_bridge",
        description="ABACUS H/S bridge approval case",
        required_capabilities=["abacus_hs_to_fcidump_converter"],
        source_reference="out_mat_hs:1",
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
                        },
                        "abacus_hs_scientific": {
                            "manifest": ".mhe/approvals/abacus_hs_approval.json",
                            "required_fields": [
                                "approved_by",
                                "approval_role",
                                "fixture_refs",
                                "tolerance_table_ref",
                                "reference_observable",
                            ],
                        },
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
                "conditional_approval_profiles": [
                    {
                        "when": {"suite": "qcompute-abacus", "case_id": case.case_id},
                        "requires": ["abacus_hs_scientific"],
                    }
                ],
            }
        )
    )
    (approvals_root / "comparison_benchmark_approval.json").write_text(
        json.dumps(
            {
                "status": "approved",
                "approved_by": "admin@example.test",
                "approval_role": "benchmark-admin",
                "approved_scope": {"suite": "qcompute-abacus"},
                "evidence_refs": ["comparison/result_bundle.json"],
                "approval_decision": "approved",
            }
        )
    )
    abacus_manifest_path = approvals_root / "abacus_hs_approval.json"
    abacus_manifest_path.write_text(
        json.dumps(
            {
                "status": "invalid",
                "approved_by": None,
                "approval_role": None,
                "fixture_refs": [],
                "tolerance_table_ref": None,
                "reference_observable": None,
            }
        )
    )

    write_comparison_outputs(
        runs_root=tmp_path,
        suite="qcompute-abacus",
        approval_config_root=config_root,
    )

    gate = json.loads(
        (tmp_path / "qcompute-abacus-benchmark" / "comparison" / "approval_gate.json").read_text()
    )
    csv_text = (
        tmp_path / "qcompute-abacus-benchmark" / "comparison" / "summary_table.csv"
    ).read_text()
    assert (
        "abacus_hs_scientific_fixture_refs_missing"
        in gate["missing_evidence_by_category"]["scientific_validation"]
    )
    assert (
        "abacus_hs_scientific_fixture_refs_missing"
        not in gate["missing_evidence_by_category"]["human_approval"]
    )
    assert "approval_scientific_missing" in csv_text
    assert "abacus_hs_scientific_fixture_refs_missing" in csv_text

    abacus_manifest_path.write_text(
        json.dumps(
            {
                "status": "approved",
                "approved_by": "scientist@example.test",
                "approval_role": "scientific-reviewer",
                "fixture_refs": ["fixtures/abacus/out_mat_hs"],
                "tolerance_table_ref": "docs/tolerance-table.md",
                "reference_observable": "ground_state_energy",
            }
        )
    )

    write_comparison_outputs(
        runs_root=tmp_path,
        suite="qcompute-abacus",
        approval_config_root=config_root,
    )

    approved_gate = json.loads(
        (tmp_path / "qcompute-abacus-benchmark" / "comparison" / "approval_gate.json").read_text()
    )
    assert approved_gate["status"] == "approved"
    assert approved_gate["approval_ready"] is True


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
