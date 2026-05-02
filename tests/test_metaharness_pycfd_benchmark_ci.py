"""CI-friendly PyCFD benchmark dry-run tests — no real PyCFD or Claude needed."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_EXPECTED_CASES = {
    "vortex-2d",
    "airfoil-2d",
    "cylinder-2d",
    "mms-2d",
    "shock-diffraction-2d",
}

_EXPECTED_METRICS = {
    "residual_l1",
    "residual_l2",
    "wall_time_seconds",
    "iterations",
    "ncells",
    "nnodes",
    "nfaces",
}


def _run_benchmark_dryrun(
    lanes: str = "direct",
    cases: str = "",
    runs_root: str = ".runs/pycfd-ci-test",
) -> dict:
    """Run the PyCFD benchmark CLI and return parsed JSON output."""
    cmd = [
        sys.executable,
        "-m",
        "metaharness.cli",
        "benchmark-run",
        "--suite",
        "pycfd-pde",
        "--lanes",
        lanes,
        "--runs-root",
        runs_root,
    ]
    if cases:
        cmd.extend(["--cases", cases])
    env = {"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"}
    result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=60)
    # stderr may contain harmless SyntaxWarning lines from PyCFD imports
    # when running without real tools — dry-run should be clean
    return json.loads(result.stdout)


class TestPyCFDBenchmarkCI:
    """Dry-run benchmark tests suitable for CI (no real PyCFD, no real Claude)."""

    def test_dryrun_all_cases_produces_valid_json(self):
        """CLI should output valid JSON with all required top-level keys."""
        output = _run_benchmark_dryrun()
        assert "suite" in output
        assert output["suite"] == "pycfd-pde"
        assert "cases" in output
        assert "summaries" in output
        assert "lanes" in output

    def test_dryrun_all_five_cases_present(self):
        """All 5 canonical PyCFD cases should appear in output."""
        output = _run_benchmark_dryrun()
        actual = {s["case_id"] for s in output["summaries"]}
        assert actual == _EXPECTED_CASES

    def test_dryrun_all_cases_pass(self):
        """All cases should pass in dry-run mode."""
        output = _run_benchmark_dryrun()
        for summary in output["summaries"]:
            assert summary["status"] == "passed", (
                f"{summary['case_id']}: expected passed, got {summary['status']}"
            )

    def test_dryrun_all_cases_have_expected_metrics(self):
        """All cases should report expected metric keys (zero values in dry-run)."""
        output = _run_benchmark_dryrun()
        for summary in output["summaries"]:
            metrics = summary.get("metrics", {})
            for metric_name in _EXPECTED_METRICS:
                assert metric_name in metrics, f"{summary['case_id']}: missing metric {metric_name}"

    def test_dryrun_emits_evidence_files(self):
        """Each case should emit evidence files."""
        output = _run_benchmark_dryrun()
        for summary in output["summaries"]:
            assert summary["evidence_count"] > 0, f"{summary['case_id']}: no evidence count"

    def test_dryrun_filter_by_cases(self):
        """Filtering by case IDs should return only matching cases."""
        output = _run_benchmark_dryrun(cases="vortex-2d,mms-2d")
        actual = {s["case_id"] for s in output["summaries"]}
        assert actual == {"vortex-2d", "mms-2d"}

    def test_dryrun_cases_have_spec_files(self, tmp_path: Path):
        """Each case should write a spec file to the output directory."""
        runs_root = tmp_path / "runs"
        _run_benchmark_dryrun(
            cases="vortex-2d",
            runs_root=str(runs_root),
        )
        spec_path = runs_root / "pycfd-pde-benchmark" / "specs" / "vortex-2d.json"
        assert spec_path.exists(), f"Spec file not found at {spec_path}"
        spec = json.loads(spec_path.read_text())
        assert spec["case_id"] == "vortex-2d"
        assert spec["suite"] == "pycfd-pde"
        assert "problem_definition" in spec
        problem = spec["problem_definition"]
        assert problem["case_type"] == "vortex"
        assert "flow" in problem
        assert "solver" in problem

    def test_dryrun_emits_claude_prompt(self, tmp_path: Path):
        """Each case should emit a Claude prompt even in dry-run mode."""
        runs_root = tmp_path / "runs"
        _run_benchmark_dryrun(
            cases="airfoil-2d",
            runs_root=str(runs_root),
        )
        prompt_path = (
            runs_root / "pycfd-pde-benchmark" / "direct" / "airfoil-2d" / "claude_prompt.txt"
        )
        assert prompt_path.exists()
        content = prompt_path.read_text()
        assert "airfoil" in content.lower()
        assert "solve_py" in content.lower()

    def test_dryrun_repeat_count(self):
        """Repeat count should be respected."""
        output = _run_benchmark_dryrun(lanes="direct", cases="mms-2d")
        assert output["repeat_count"] == 1

    def test_dryrun_no_real_claude_flag(self):
        """Without --allow-real-claude, real_claude should be false."""
        output = _run_benchmark_dryrun()
        assert output["real_claude"] is False

    def test_dryrun_no_real_tools_flag(self):
        """Without --allow-real-tools, real_tools should be false."""
        output = _run_benchmark_dryrun()
        assert output["real_tools"] is False
