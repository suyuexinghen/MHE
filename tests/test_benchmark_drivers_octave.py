from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.octave_cases import octave_case_catalog
from metaharness.benchmark_drivers.octave_runner import OctaveBenchmarkRunner


def test_octave_runner_dry_run_writes_three_lane_outputs(tmp_path: Path) -> None:
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        brain_provider=FakeClaudeCLIBrainProvider({"script": "solve.m"}),
    )

    summaries = runner.run_case(case, ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    assert all(summary.status == "passed" for summary in summaries)
    assert summaries[1].llm_calls == 1
    assert summaries[2].llm_calls == 1
    base = tmp_path / "octave-native-benchmark"
    assert (base / "extension" / "sinc-values" / "summary.json").exists()
    assert (base / "direct" / "sinc-values" / "solve.m").exists()
    assert (base / "direct" / "sinc-values" / "claude_prompt.txt").exists()
    assert (base / "agent" / "sinc-values" / "proposal.json").exists()


def test_octave_direct_real_mode_skips_when_binary_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: None)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"script": "solve.m"}),
    )

    summary = runner.run_direct(case)

    assert summary.status == "skipped"
    assert summary.skip_reason == "octave-cli not found"
