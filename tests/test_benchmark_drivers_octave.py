from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.octave_cases import octave_case_catalog
from metaharness.benchmark_drivers.octave_runner import OctaveBenchmarkRunner
from metaharness.benchmark_drivers.octave_scripts import build_octave_case_script


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


def test_octave_script_builder_emits_expected_metrics() -> None:
    catalog = octave_case_catalog()

    for case in catalog.values():
        script = build_octave_case_script(case)
        assert "elapsed_seconds = toc" in script
        for metric in case.expected_metrics:
            assert metric in script


def test_octave_extension_spec_declares_all_expected_outputs(tmp_path: Path) -> None:
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(runs_root=tmp_path)

    spec = runner._build_extension_spec(case, tmp_path)

    assert [output.metric_key for output in spec.expected_outputs] == case.expected_metrics
    assert "max_abs_error" in spec.script.inline_source


def test_octave_metric_output_parser_reads_scalar_files(tmp_path: Path) -> None:
    output_dir = tmp_path / "workspace"
    outputs = output_dir / "outputs"
    outputs.mkdir(parents=True)
    (outputs / "max_abs_error.txt").write_text("# name: max_abs_error\n# type: scalar\n0\n")
    (outputs / "ignored.txt").write_text("not-a-number\n")
    runner = OctaveBenchmarkRunner(runs_root=tmp_path)

    metrics = runner._read_metric_output_files(output_dir)

    assert metrics == {"max_abs_error": 0.0}
