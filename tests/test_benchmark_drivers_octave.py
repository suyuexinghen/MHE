from __future__ import annotations

import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import ClaudeCLIResult, FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.models import ClaudeInvocationRecord
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


def test_octave_direct_records_claude_error_evidence(tmp_path: Path) -> None:
    class FailingBrainProvider:
        def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
            output_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = output_dir / "claude_prompt.txt"
            stdout_path = output_dir / "claude_stdout.json"
            stderr_path = output_dir / "claude_stderr.txt"
            result_path = output_dir / "claude_result.json"
            prompt_path.write_text(prompt)
            stdout_path.write_text('{"is_error": true}')
            stderr_path.write_text("")
            result_path.write_text('{"is_error": true}')
            return ClaudeCLIResult(
                invocation=ClaudeInvocationRecord(
                    binary="claude",
                    command=["claude"],
                    prompt_path=str(prompt_path),
                    stdout_path=str(stdout_path),
                    stderr_path=str(stderr_path),
                    result_path=str(result_path),
                    proposal_path=str(output_dir / "proposal.json"),
                    return_code=1,
                ),
                result={"is_error": True},
                error="Reached maximum number of turns (4)",
            )

    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FailingBrainProvider(),
    )

    summary = runner.run_direct(case)

    assert summary.status == "failed"
    assert "Reached maximum number of turns" in (summary.error_message or "")
    assert summary.proposal_contract_status == "failed"
    assert summary.preflight_status == "failed"
    assert summary.failure_category == "proposal_max_turns"
    assert any(path.endswith("claude_stdout.json") for path in summary.evidence_files)
    assert any(path.endswith("claude_result.json") for path in summary.evidence_files)
    assert any(path.endswith("proposal_preflight.json") for path in summary.evidence_files)


def test_octave_direct_preflight_fails_missing_script(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"notes": "no script"}),
    )

    summary = runner.run_direct(case)

    output_dir = tmp_path / "octave-native-benchmark" / "direct" / "sinc-values"
    preflight = (output_dir / "proposal_preflight.json").read_text()
    assert summary.status == "failed"
    assert summary.proposal_contract_status == "failed"
    assert summary.preflight_status == "failed"
    assert summary.failure_category == "proposal_contract_failed"
    assert "proposal_preflight.json" in "\n".join(summary.evidence_files)
    assert "required_script_fields" in preflight


def test_octave_direct_real_mode_uses_proposal_script(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )

    def fake_run(command, **kwargs):
        output_dir = Path(kwargs["cwd"])
        (output_dir / "metrics.json").write_text('{"max_abs_error": 0, "elapsed_seconds": 0}')
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness.benchmark_drivers.octave_runner.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider(
            {
                "script": "custom_metric = 1;\nmetrics = struct('max_abs_error', 0, 'elapsed_seconds', 0);"
            }
        ),
    )

    summary = runner.run_direct(case)

    script = (
        tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "solve.m"
    ).read_text()
    assert summary.status == "passed"
    assert "custom_metric = 1" in script


def test_octave_direct_real_mode_records_timeout_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )

    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=300, output="partial", stderr="timeout")

    monkeypatch.setattr("metaharness.benchmark_drivers.octave_runner.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"script": "max_abs_error = 0; elapsed_seconds = 0;"}
        ),
    )

    summary = runner.run_direct(case)

    output_dir = tmp_path / "octave-native-benchmark" / "direct" / "sinc-values"
    assert summary.status == "failed"
    assert "timed out" in (summary.error_message or "")
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "stdout.txt").read_text() == "partial"


def test_octave_adaptive_agent_uses_initial_proposal_script(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )

    def fake_run(command, **kwargs):
        output_dir = Path(kwargs["cwd"])
        wrapper = (output_dir / "mhe_wrapper.m").read_text()
        assert "adaptive_marker = 1" in wrapper
        outputs = output_dir / "outputs"
        outputs.mkdir(exist_ok=True)
        (outputs / "max_abs_error.txt").write_text("# name: max_abs_error\n# type: scalar\n0\n")
        (outputs / "elapsed_seconds.txt").write_text("# name: elapsed_seconds\n# type: scalar\n0\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness_ext.octave.executor.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        adaptive_agent=True,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"script": "adaptive_marker = 1;\nmax_abs_error = 0;\nelapsed_seconds = 0;"}
        ),
    )

    summary = runner.run_agent(case)

    assert summary.status == "passed"
    assert summary.llm_calls == 1


def test_octave_adaptive_agent_records_repair_attempt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )
    attempts = {"count": 0}

    def fake_run(command, **kwargs):
        attempts["count"] += 1
        output_dir = Path(kwargs["cwd"])
        outputs = output_dir / "outputs"
        outputs.mkdir(exist_ok=True)
        if attempts["count"] > 1:
            (outputs / "max_abs_error.txt").write_text("# name: max_abs_error\n# type: scalar\n0\n")
            (outputs / "elapsed_seconds.txt").write_text(
                "# name: elapsed_seconds\n# type: scalar\n0\n"
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness_ext.octave.executor.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        adaptive_agent=True,
        max_repair_attempts=1,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"script": "max_abs_error = 0;\nelapsed_seconds = 0;"}
        ),
    )

    summary = runner.run_agent(case)

    assert summary.status == "passed"
    assert summary.repair_count == 1
    assert summary.llm_calls == 2
    assert attempts["count"] == 2


def test_octave_adaptive_agent_records_repaired_success_diagnostics(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )
    attempts = {"count": 0}

    def fake_run(command, **kwargs):
        attempts["count"] += 1
        output_dir = Path(kwargs["cwd"])
        outputs = output_dir / "outputs"
        outputs.mkdir(exist_ok=True)
        if attempts["count"] > 1:
            (outputs / "max_abs_error.txt").write_text("# name: max_abs_error\n# type: scalar\n0\n")
            (outputs / "elapsed_seconds.txt").write_text(
                "# name: elapsed_seconds\n# type: scalar\n0\n"
            )
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness_ext.octave.executor.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        adaptive_agent=True,
        max_repair_attempts=1,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"script": "max_abs_error = 0;\nelapsed_seconds = 0;"}
        ),
    )

    summary = runner.run_agent(case)

    diagnostics_path = (
        tmp_path
        / "octave-native-benchmark"
        / "agent"
        / "sinc-values"
        / "adaptive_diagnostics_1.json"
    )
    assert summary.status == "passed"
    assert summary.repair_outcome == "repaired_success"
    assert summary.diagnostics_files == [str(diagnostics_path)]
    assert summary.repair_count == 1
    assert diagnostics_path.exists()
    assert "before_missing_metrics" in diagnostics_path.read_text()


def test_octave_adaptive_agent_records_unrepaired_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )

    def fake_run(command, **kwargs):
        Path(kwargs["cwd"]).joinpath("outputs").mkdir(exist_ok=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness_ext.octave.executor.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        adaptive_agent=True,
        max_repair_attempts=1,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"script": "max_abs_error = 0;\nelapsed_seconds = 0;"}
        ),
    )

    summary = runner.run_agent(case)

    assert summary.status == "failed"
    assert summary.repair_outcome == "unrepaired_failure"
    assert summary.repair_count == 1
    assert len(summary.diagnostics_files) == 1


def test_octave_adaptive_agent_stops_when_repair_proposal_errors(
    tmp_path: Path, monkeypatch
) -> None:
    class ErrorOnRepairBrainProvider(FakeClaudeCLIBrainProvider):
        def __init__(self) -> None:
            super().__init__({"script": "max_abs_error = 0;\nelapsed_seconds = 0;"})
            self.calls = 0

        def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
            self.calls += 1
            if self.calls == 1:
                return super().propose(prompt=prompt, output_dir=output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = output_dir / "claude_prompt.txt"
            stdout_path = output_dir / "claude_stdout.json"
            stderr_path = output_dir / "claude_stderr.txt"
            result_path = output_dir / "claude_result.json"
            prompt_path.write_text(prompt)
            stdout_path.write_text('{"is_error": true}')
            stderr_path.write_text("repair failed")
            result_path.write_text('{"is_error": true}')
            return ClaudeCLIResult(
                invocation=ClaudeInvocationRecord(
                    binary="fake-claude",
                    command=["fake-claude"],
                    prompt_path=str(prompt_path),
                    stdout_path=str(stdout_path),
                    stderr_path=str(stderr_path),
                    result_path=str(result_path),
                    proposal_path=str(output_dir / "proposal.json"),
                    return_code=1,
                ),
                result={"is_error": True},
                error="Reached maximum number of turns (1)",
            )

    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )

    def fake_run(command, **kwargs):
        Path(kwargs["cwd"]).joinpath("outputs").mkdir(exist_ok=True)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness_ext.octave.executor.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        adaptive_agent=True,
        max_repair_attempts=1,
        brain_provider=ErrorOnRepairBrainProvider(),
    )

    summary = runner.run_agent(case)

    assert summary.status == "failed"
    assert summary.repair_outcome == "unrepaired_failure"
    assert summary.failure_category == "proposal_max_turns"
    assert summary.repair_count == 1


def test_octave_agent_real_mode_writes_agent_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: "octave-cli"
    )

    def fake_run(command, **kwargs):
        output_dir = Path(kwargs["cwd"])
        outputs = output_dir / "outputs"
        outputs.mkdir(exist_ok=True)
        (outputs / "max_abs_error.txt").write_text("# name: max_abs_error\n# type: scalar\n0\n")
        (outputs / "elapsed_seconds.txt").write_text("# name: elapsed_seconds\n# type: scalar\n0\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("metaharness_ext.octave.executor.subprocess.run", fake_run)
    case = octave_case_catalog()["sinc-values"]
    runner = OctaveBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"script": "ignored"}),
    )

    summary = runner.run_agent(case)

    base = tmp_path / "octave-native-benchmark"
    assert summary.lane == "agent"
    assert (base / "agent" / "sinc-values" / "summary.json").exists()
    assert not (base / "extension" / "sinc-values" / "summary.json").exists()


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
