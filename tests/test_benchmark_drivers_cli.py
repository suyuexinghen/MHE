from __future__ import annotations

import json
from pathlib import Path

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
            "--claude-permission-mode",
            "auto",
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
    assert command["permission_mode"] == "auto"
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
    assert (
        tmp_path
        / "repeat-02"
        / "octave-native-benchmark"
        / "extension"
        / "sinc-values"
        / "summary.json"
    ).exists()


def test_benchmark_run_cli_forwards_adaptive_agent_options(tmp_path: Path, monkeypatch) -> None:
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
    assert (tmp_path / "octave-native-benchmark" / "comparison" / "result_bundle.json").exists()
    assert (tmp_path / "octave-native-benchmark" / "comparison" / "comparison_report.md").exists()


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
