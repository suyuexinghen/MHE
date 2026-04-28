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
