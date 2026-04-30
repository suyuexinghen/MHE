from __future__ import annotations

import json
from pathlib import Path

from metaharness.benchmark_drivers.acp_provider import ACPBrainProvider
from metaharness.cli import main


def test_benchmark_run_cli_writes_dry_run_outputs(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    output = capsys.readouterr().out
    assert "sinc-values" in output
    assert (tmp_path / "octave-native-benchmark" / "specs" / "sinc-values.json").exists()
    assert (
        tmp_path / "octave-native-benchmark" / "agent" / "sinc-values" / "summary.json"
    ).exists()


def test_benchmark_run_cli_allows_real_claude_without_real_tools(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "direct",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
            "--allow-real-claude",
            "--claude-binary",
            "missing-claude-for-test",
            "--claude-max-turns",
            "2",
            "--claude-extra-arg",
            "--test-extra",
        ]
    )

    assert status == 0
    command_path = (
        tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "claude_command.json"
    )
    command = json.loads(command_path.read_text())
    assert command["max_turns"] == 2
    assert command["permission_mode"] == "bypassPermissions"
    assert command["extra_args"] == ["--test-extra"]
    summary = json.loads(
        (
            tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "summary.json"
        ).read_text()
    )
    assert summary["status"] == "failed"
    assert not (
        tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "solve.m"
    ).exists()


def test_acp_provider_json_diagnostic_classifies_json_proposal() -> None:
    provider = ACPBrainProvider()
    prompt = provider.build_json_diagnostic_prompt("Return benchmark review status.")
    diagnostic = provider.diagnose_json_response(
        {
            "content": '{"proposal":{"decision":"approve"},"diagnostic_status":"ok"}',
            "execution_meta": {"stop_reason": "end_turn"},
        }
    )

    assert "Do not use tools" in prompt
    assert "Return only a JSON object" in prompt
    assert diagnostic["diagnostic_status"] == "ok"
    assert diagnostic["json_proposal_available"] is True
    assert diagnostic["proposal"] == {"decision": "approve"}


def test_acp_provider_json_diagnostic_classifies_empty_content() -> None:
    diagnostic = ACPBrainProvider().diagnose_json_response(
        {"content": "", "execution_meta": {"stop_reason": "end_turn"}}
    )

    assert diagnostic["diagnostic_status"] == "blocked"
    assert diagnostic["json_proposal_available"] is False
    assert diagnostic["content_empty"] is True
    assert diagnostic["stop_reason"] == "end_turn"


def test_benchmark_run_cli_can_select_acp_provider(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "direct",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
            "--allow-real-claude",
            "--brain-provider",
            "acp",
            "--acp-command",
            "missing-acp-for-test",
            "--acp-session-key",
            "test-session",
        ]
    )

    assert status == 0
    case_dir = tmp_path / "octave-native-benchmark" / "direct" / "sinc-values"
    command = json.loads((case_dir / "acp_command.json").read_text())
    prompt = (case_dir / "acp_prompt.txt").read_text()
    assert command["command"] == ["missing-acp-for-test"]
    assert command["session_key"] == "test-session"
    assert "Return only a JSON object" in prompt
    assert "solve_m" in prompt
    summary = json.loads(
        (
            tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "summary.json"
        ).read_text()
    )
    assert summary["status"] == "failed"


def test_benchmark_run_cli_preserves_explicit_claude_permission_mode(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "direct",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
            "--allow-real-claude",
            "--claude-binary",
            "missing-claude-for-test",
            "--claude-permission-mode",
            "auto",
        ]
    )

    assert status == 0
    command = json.loads(
        (
            tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "claude_command.json"
        ).read_text()
    )
    assert command["permission_mode"] == "auto"


def test_benchmark_run_cli_real_tools_do_not_imply_real_claude(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr("metaharness.benchmark_drivers.octave_runner.shutil.which", lambda _: None)

    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "direct",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
            "--allow-real-tools",
            "--claude-binary",
            "missing-claude-for-test",
        ]
    )

    assert status == 0
    command_path = (
        tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "claude_command.json"
    )
    command = json.loads(command_path.read_text())
    summary = json.loads(
        (
            tmp_path / "octave-native-benchmark" / "direct" / "sinc-values" / "summary.json"
        ).read_text()
    )
    output = json.loads(capsys.readouterr().out)
    assert command["command"][0] == "fake-claude"
    assert output["real_claude"] is False
    assert output["real_tools"] is True
    assert summary["status"] == "skipped"
    assert summary["skip_reason"] == "octave-cli not found"


def test_benchmark_run_cli_writes_repeat_summary(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "extension",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
            "--repeat",
            "2",
        ]
    )

    assert status == 0
    repeat_summary = json.loads(
        (tmp_path / "octave-native-benchmark" / "comparison" / "repeat_summary.json").read_text()
    )
    assert repeat_summary["rows"][0]["run_count"] == 2
    assert "min_elapsed_seconds" in repeat_summary["rows"][0]
    assert "max_elapsed_seconds" in repeat_summary["rows"][0]
    assert "iqr_elapsed_seconds" in repeat_summary["rows"][0]
    assert (
        tmp_path
        / "repeat-02"
        / "octave-native-benchmark"
        / "extension"
        / "sinc-values"
        / "summary.json"
    ).exists()


def test_benchmark_run_cli_forwards_octave_adaptive_agent_options(
    tmp_path: Path, monkeypatch
) -> None:
    captured = {}

    class FakeOctaveBenchmarkRunner:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.runs_root = kwargs["runs_root"]

        def run_case(self, case, lanes):
            return []

    monkeypatch.setattr("metaharness.cli.OctaveBenchmarkRunner", FakeOctaveBenchmarkRunner)

    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "agent",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
            "--adaptive-agent",
            "--max-repair-attempts",
            "3",
        ]
    )

    assert status == 0
    assert captured["adaptive_agent"] is True
    assert captured["max_repair_attempts"] == 3


def test_benchmark_run_cli_forwards_nektar_adaptive_agent_options(
    tmp_path: Path, monkeypatch
) -> None:
    captured = {}

    class FakeNektarBenchmarkRunner:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.runs_root = kwargs["runs_root"]

        def run_case(self, case, lanes):
            return []

    monkeypatch.setattr("metaharness.cli.NektarBenchmarkRunner", FakeNektarBenchmarkRunner)

    status = main(
        [
            "benchmark-run",
            "--suite",
            "nektar-pde",
            "--lanes",
            "agent",
            "--cases",
            "advdiff-2d",
            "--runs-root",
            str(tmp_path),
            "--adaptive-agent",
            "--max-repair-attempts",
            "3",
        ]
    )

    assert status == 0
    assert captured["adaptive_agent"] is True
    assert captured["max_repair_attempts"] == 3


def test_benchmark_run_cli_forwards_fealpy_brain_provider(tmp_path: Path, monkeypatch) -> None:
    captured = {}

    class FakeFealpyBenchmarkRunner:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.runs_root = kwargs["runs_root"]

        def run_case(self, case, lanes):
            return []

    monkeypatch.setattr("metaharness.cli.FealpyBenchmarkRunner", FakeFealpyBenchmarkRunner)

    status = main(
        [
            "benchmark-run",
            "--suite",
            "fealpy-pde",
            "--lanes",
            "agent",
            "--cases",
            "poisson-2d-numpy",
            "--runs-root",
            str(tmp_path),
            "--allow-real-claude",
            "--claude-binary",
            "missing-claude-for-test",
        ]
    )

    assert status == 0
    assert captured["brain_provider"] is not None
    assert captured["adaptive_agent"] is False


def test_fealpy_benchmark_run_cli_can_select_acp_provider(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "fealpy-pde",
            "--lanes",
            "direct",
            "--cases",
            "poisson-2d-numpy",
            "--runs-root",
            str(tmp_path),
            "--allow-real-claude",
            "--brain-provider",
            "acp",
            "--acp-command",
            "missing-acp-for-test",
            "--acp-session-key",
            "fealpy-test-session",
        ]
    )

    assert status == 0
    case_dir = tmp_path / "fealpy-pde-benchmark" / "direct" / "poisson-2d-numpy"
    command = json.loads((case_dir / "acp_command.json").read_text())
    prompt = (case_dir / "acp_prompt.txt").read_text()
    summary = json.loads((case_dir / "summary.json").read_text())
    assert command["command"] == ["missing-acp-for-test"]
    assert command["session_key"] == "fealpy-test-session"
    assert "solve_py" in prompt
    assert summary["status"] == "failed"


def test_benchmark_run_cli_rejects_unknown_lane(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "extension,bogus",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 2
    assert "invalid benchmark lanes: bogus" in capsys.readouterr().err


def test_benchmark_run_cli_rejects_empty_lanes(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "",
            "--cases",
            "sinc-values",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 2
    assert "at least one benchmark lane is required" in capsys.readouterr().err


def test_benchmark_run_cli_rejects_unknown_case(tmp_path: Path, capsys) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "octave-native",
            "--lanes",
            "extension",
            "--cases",
            "missing-case",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 2
    assert "unknown benchmark case: missing-case" in capsys.readouterr().err


def test_qcompute_abacus_benchmark_run_cli_writes_dry_run_outputs(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "qcompute-abacus",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "h2-fcidump-vqe-proxy",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert (tmp_path / "qcompute-abacus-benchmark" / "specs" / "h2-fcidump-vqe-proxy.json").exists()
    assert (
        tmp_path
        / "qcompute-abacus-benchmark"
        / "extension"
        / "h2-fcidump-vqe-proxy"
        / "hamiltonian.fcidump"
    ).exists()
    assert (
        tmp_path / "qcompute-abacus-benchmark" / "agent" / "h2-fcidump-vqe-proxy" / "proposal.json"
    ).exists()


def test_nektar_benchmark_run_cli_writes_dry_run_outputs(tmp_path: Path) -> None:
    status = main(
        [
            "benchmark-run",
            "--suite",
            "nektar-pde",
            "--lanes",
            "extension,direct,agent",
            "--cases",
            "advdiff-2d",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert (tmp_path / "nektar-pde-benchmark" / "specs" / "advdiff-2d.json").exists()
    assert (
        tmp_path / "nektar-pde-benchmark" / "preflight" / "advdiff-2d" / "tester_summary.json"
    ).exists()
    assert (
        tmp_path / "nektar-pde-benchmark" / "direct" / "advdiff-2d" / "claude_prompt.txt"
    ).exists()


def test_benchmark_compare_cli_writes_reports(tmp_path: Path) -> None:
    assert (
        main(
            [
                "benchmark-run",
                "--suite",
                "octave-native",
                "--lanes",
                "extension,direct,agent",
                "--cases",
                "sinc-values",
                "--runs-root",
                str(tmp_path),
            ]
        )
        == 0
    )

    status = main(
        [
            "benchmark-compare",
            "--suite",
            "octave-native",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    comparison_dir = tmp_path / "octave-native-benchmark" / "comparison"
    assert (comparison_dir / "result_bundle.json").exists()
    assert (comparison_dir / "comparison_report.md").exists()
    bundle = json.loads((comparison_dir / "result_bundle.json").read_text())
    report = (comparison_dir / "comparison_report.md").read_text()
    csv_text = (comparison_dir / "summary_table.csv").read_text()
    assert bundle["evidence_context"]["real_tools"] is False
    assert bundle["evidence_context"]["real_claude"] is False
    assert "Real tools: `False`" in report
    assert "Direct proposal" in report
    assert "Direct preflight" in report
    assert "direct_proposal_source" in csv_text
    assert "direct_preflight_status" in csv_text


def test_benchmark_compare_manifest_records_observed_lanes(tmp_path: Path) -> None:
    assert (
        main(
            [
                "benchmark-run",
                "--suite",
                "octave-native",
                "--lanes",
                "extension",
                "--cases",
                "sinc-values",
                "--runs-root",
                str(tmp_path),
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "benchmark-compare",
                "--suite",
                "octave-native",
                "--runs-root",
                str(tmp_path),
            ]
        )
        == 0
    )

    manifest_path = tmp_path / "octave-native-benchmark" / "comparison" / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["lanes"] == ["extension"]


def test_qcompute_abacus_benchmark_compare_cli_writes_reports(tmp_path: Path) -> None:
    assert (
        main(
            [
                "benchmark-run",
                "--suite",
                "qcompute-abacus",
                "--lanes",
                "extension,direct,agent",
                "--cases",
                "h2-fcidump-vqe-proxy",
                "--runs-root",
                str(tmp_path),
            ]
        )
        == 0
    )

    status = main(
        [
            "benchmark-compare",
            "--suite",
            "qcompute-abacus",
            "--runs-root",
            str(tmp_path),
        ]
    )

    assert status == 0
    assert (tmp_path / "qcompute-abacus-benchmark" / "comparison" / "result_bundle.json").exists()
