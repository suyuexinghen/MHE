from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.benchmark_drivers.qcompute_abacus_cases import get_qcompute_abacus_cases
from metaharness.benchmark_drivers.qcompute_abacus_runner import QComputeAbacusBenchmarkRunner


def test_qcompute_abacus_catalog_includes_proxy_and_bridge_cases() -> None:
    cases = {case.case_id: case for case in get_qcompute_abacus_cases()}

    assert set(cases) == {
        "h2-fcidump-vqe-proxy",
        "h2-fcidump-jw-vs-bk",
        "abacus-hs-bridge-pending",
    }
    assert cases["h2-fcidump-vqe-proxy"].suite == "qcompute-abacus"
    assert cases["abacus-hs-bridge-pending"].capability_gated is True
    assert "abacus_hs_to_fcidump_bridge" in cases["abacus-hs-bridge-pending"].required_capabilities


def test_qcompute_abacus_dry_run_writes_three_lane_outputs(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["h2-fcidump-vqe-proxy"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    suite_root = tmp_path / "qcompute-abacus-benchmark"
    assert (suite_root / "extension" / case.case_id / "summary.json").exists()
    assert (suite_root / "extension" / case.case_id / "hamiltonian.fcidump").exists()
    assert (suite_root / "direct" / case.case_id / "claude_prompt.txt").exists()
    assert (suite_root / "agent" / case.case_id / "proposal.json").exists()


def test_qcompute_abacus_mapping_case_writes_dry_run_summaries(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["h2-fcidump-jw-vs-bk"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert all(summary.status == "passed" for summary in summaries)
    extension_summary = json.loads(
        (
            tmp_path / "qcompute-abacus-benchmark" / "extension" / case.case_id / "summary.json"
        ).read_text()
    )
    assert extension_summary["metrics"]["jw_num_qubits"] == 2.0
    assert extension_summary["metrics"]["bk_num_qubits"] == 2.0


def test_qcompute_abacus_bridge_case_is_explicitly_skipped(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["abacus-hs-bridge-pending"])[0]
    runner = QComputeAbacusBenchmarkRunner(runs_root=tmp_path)

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert all(summary.status == "skipped" for summary in summaries)
    assert all("unsupported_source_format" in (summary.skip_reason or "") for summary in summaries)
    assert (
        tmp_path / "qcompute-abacus-benchmark" / "extension" / case.case_id / "source_refs.json"
    ).exists()


def test_qcompute_abacus_compare_reuses_generic_comparator(tmp_path: Path) -> None:
    case = get_qcompute_abacus_cases(["h2-fcidump-vqe-proxy"])[0]
    QComputeAbacusBenchmarkRunner(runs_root=tmp_path).run_case(
        case, ["extension", "direct", "agent"]
    )

    rows = write_comparison_outputs(runs_root=tmp_path, suite="qcompute-abacus")

    assert len(rows) == 1
    assert rows[0].case_id == "h2-fcidump-vqe-proxy"
    assert rows[0].verdict == "all_passed"
    assert (tmp_path / "qcompute-abacus-benchmark" / "comparison" / "result_bundle.json").exists()
