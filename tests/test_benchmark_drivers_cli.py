from __future__ import annotations

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
