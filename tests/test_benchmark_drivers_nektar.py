from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.nektar_cases import nektar_case_catalog
from metaharness.benchmark_drivers.nektar_runner import (
    NektarBenchmarkRunner,
    parse_nektar_error_norms,
)


def test_parse_nektar_error_norms_extracts_l2_linf() -> None:
    metrics = parse_nektar_error_norms(
        """
        L 2 error (variable u): 0.00135233
        L inf error (variable u): 0.00275937
        L 2 error (variable rho): 1.98838e-06
        """
    )

    assert metrics["l2_error_u"] == 0.00135233
    assert metrics["linf_error_u"] == 0.00275937
    assert metrics["l2_error_rho"] == 1.98838e-06


def test_nektar_runner_dry_run_writes_three_lane_outputs(tmp_path: Path) -> None:
    case = nektar_case_catalog()["advdiff-2d"]
    runner = NektarBenchmarkRunner(
        runs_root=tmp_path,
        brain_provider=FakeClaudeCLIBrainProvider({"session_xml": "session.xml"}),
    )

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    assert summaries[1].llm_calls == 1
    assert summaries[2].llm_calls == 1
    base = tmp_path / "nektar-pde-benchmark"
    assert (base / "extension" / "advdiff-2d" / "session.xml").exists()
    assert (base / "direct" / "advdiff-2d" / "solver.stdout.log").exists()
    assert (base / "direct" / "advdiff-2d" / "claude_prompt.txt").exists()
    assert (base / "agent" / "advdiff-2d" / "proposal.json").exists()


def test_nektar_capability_gated_extension_dry_run_is_skipped(tmp_path: Path) -> None:
    case = nektar_case_catalog()["euler-1d"]
    runner = NektarBenchmarkRunner(runs_root=tmp_path)

    summary = runner.run_extension(case)

    assert summary.status == "skipped"
    assert summary.skip_reason == "capability gated for current extension dispatch"
