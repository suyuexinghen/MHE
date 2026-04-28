from __future__ import annotations

import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference
from metaharness.benchmark_drivers.nektar_cases import nektar_case_catalog
from metaharness.benchmark_drivers.nektar_runner import (
    NektarBenchmarkRunner,
    parse_nektar_error_norms,
    parse_nektar_tst,
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


def test_parse_nektar_tst_extracts_executable_parameters_and_metrics(tmp_path: Path) -> None:
    tst_path = tmp_path / "case.tst"
    tst_path.write_text(
        """
        <test>
          <executable>ADRSolver</executable>
          <parameters>case.xml</parameters>
          <metrics>
            <metric type="L2"><value variable="u" tolerance="1e-8">0.001</value></metric>
            <metric type="Linf"><value variable="u" tolerance="2e-8">0.002</value></metric>
          </metrics>
        </test>
        """
    )

    spec = parse_nektar_tst(tst_path)

    assert spec.executable == "ADRSolver"
    assert spec.parameters == ["case.xml"]
    assert spec.reference_metrics == {
        "l2_error_u": (0.001, 1e-8),
        "linf_error_u": (0.002, 2e-8),
    }


def test_nektar_direct_real_mode_replays_tst_session_xml(tmp_path: Path, monkeypatch) -> None:
    tst_path = tmp_path / "case.tst"
    xml_path = tmp_path / "case.xml"
    xml_path.write_text("<NEKTAR><CONDITIONS /></NEKTAR>\n")
    tst_path.write_text(
        """
        <test>
          <executable>ADRSolver</executable>
          <parameters>case.xml</parameters>
          <metrics>
            <metric type="L2"><value variable="u" tolerance="1e-8">0.00135233</value></metric>
          </metrics>
        </test>
        """
    )
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.nektar_runner.shutil.which", lambda _: "ADRSolver"
    )

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(
            command,
            0,
            "L 2 error (variable u): 0.00135233\n",
            "",
        )

    monkeypatch.setattr("metaharness.benchmark_drivers.nektar_runner.subprocess.run", fake_run)
    case = BenchmarkCaseSpec(
        case_id="fixture",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="fixture case",
        required_capabilities=["nektar_adr_solver"],
        source_reference={"tst": str(tst_path), "xml": str(tmp_path / "fallback.xml")},
        expected_metrics=["l2_error_u"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
        problem_definition={"solver_binary": "FallbackSolver"},
    )
    runner = NektarBenchmarkRunner(
        runs_root=tmp_path / "runs",
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"session_xml": "session.xml"}),
    )

    summary = runner.run_direct(case)

    output_dir = tmp_path / "runs" / "nektar-pde-benchmark" / "direct" / "fixture"
    assert summary.status == "passed"
    assert calls[0][0] == "ADRSolver"
    assert (output_dir / "session.xml").read_text() == xml_path.read_text()
    assert (output_dir / "reference_metrics.json").exists()


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
