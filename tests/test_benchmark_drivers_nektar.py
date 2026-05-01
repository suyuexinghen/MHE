from __future__ import annotations

import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import ClaudeCLIResult, FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.io import read_json, write_json, write_text
from metaharness.benchmark_drivers.models import (
    BenchmarkCaseSpec,
    ClaudeInvocationRecord,
    MetricReference,
)
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


def test_nektar_preflight_executes_tester_when_real_tools_are_allowed(
    tmp_path: Path, monkeypatch
) -> None:
    tst_path = tmp_path / "case.tst"
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
        "metaharness.benchmark_drivers.nektar_runner.shutil.which",
        lambda binary: binary,
    )
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, "tester ok\n", "")

    monkeypatch.setattr("metaharness.benchmark_drivers.nektar_runner.subprocess.run", fake_run)
    case = BenchmarkCaseSpec(
        case_id="fixture",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="fixture case",
        required_capabilities=["nektar_adr_solver"],
        source_reference={"tst": str(tst_path)},
        expected_metrics=["l2_error_u"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
    )
    runner = NektarBenchmarkRunner(runs_root=tmp_path / "runs", allow_real_tools=True)

    runner.run_case(case, [])

    summary = read_json(
        tmp_path / "runs" / "nektar-pde-benchmark" / "preflight" / "fixture" / "tester_summary.json"
    )
    assert calls[0][0] == ["Tester", str(tst_path)]
    assert calls[0][1]["cwd"] == tst_path.parent
    assert summary["preflight_executed"] is True
    assert summary["tester_return_code"] == 0
    assert summary["status"] == "ready"
    assert (
        tmp_path / "runs" / "nektar-pde-benchmark" / "preflight" / "fixture" / "tester.stdout.log"
    ).read_text() == "tester ok\n"


def test_nektar_preflight_dry_run_only_probes_tools(tmp_path: Path, monkeypatch) -> None:
    tst_path = tmp_path / "case.tst"
    tst_path.write_text("<test><executable>ADRSolver</executable></test>")
    monkeypatch.setattr(
        "metaharness.benchmark_drivers.nektar_runner.shutil.which",
        lambda binary: binary,
    )

    def fake_run(command, **kwargs):
        raise AssertionError("dry-run preflight must not execute Tester")

    monkeypatch.setattr("metaharness.benchmark_drivers.nektar_runner.subprocess.run", fake_run)
    case = BenchmarkCaseSpec(
        case_id="fixture",
        suite="nektar-pde",
        task_family="nektar_pde",
        description="fixture case",
        required_capabilities=["nektar_adr_solver"],
        source_reference={"tst": str(tst_path)},
        expected_metrics=[],
    )
    runner = NektarBenchmarkRunner(runs_root=tmp_path / "runs")

    runner.run_case(case, [])

    summary = read_json(
        tmp_path / "runs" / "nektar-pde-benchmark" / "preflight" / "fixture" / "tester_summary.json"
    )
    assert summary["preflight_executed"] is False
    assert summary["status"] == "available"
    assert (
        tmp_path / "runs" / "nektar-pde-benchmark" / "preflight" / "fixture" / "tester.stdout.log"
    ).read_text() == ""


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


def test_nektar_extension_real_mode_replays_tst_session_xml(tmp_path: Path, monkeypatch) -> None:
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

    def fake_run(command, **kwargs):
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
        source_reference={"tst": str(tst_path)},
        expected_metrics=["l2_error_u", "elapsed_seconds"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
        problem_definition={"solver_binary": "FallbackSolver"},
    )
    runner = NektarBenchmarkRunner(runs_root=tmp_path / "runs", allow_real_tools=True)

    summary = runner.run_extension(case)

    output_dir = tmp_path / "runs" / "nektar-pde-benchmark" / "extension" / "fixture"
    assert summary.status == "passed"
    assert summary.passed
    assert (output_dir / "session.xml").read_text() == xml_path.read_text()
    assert (output_dir / "validation.json").exists()
    assert (output_dir / "evidence.json").exists()


def test_nektar_agent_real_mode_replays_with_proposal_evidence(tmp_path: Path, monkeypatch) -> None:
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

    def fake_run(command, **kwargs):
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
        source_reference={"tst": str(tst_path)},
        expected_metrics=["l2_error_u", "elapsed_seconds"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
        problem_definition={"solver_binary": "FallbackSolver"},
    )
    runner = NektarBenchmarkRunner(
        runs_root=tmp_path / "runs",
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"session_xml": "session.xml"}),
    )

    summary = runner.run_agent(case)

    output_dir = tmp_path / "runs" / "nektar-pde-benchmark" / "agent" / "fixture"
    assert summary.status == "passed"
    assert summary.llm_calls == 1
    assert (output_dir / "proposal.json").exists()
    assert (output_dir / "session.xml").read_text() == xml_path.read_text()


def test_nektar_agent_real_mode_applies_safe_proposal_solver_args(
    tmp_path: Path, monkeypatch
) -> None:
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
        source_reference={"tst": str(tst_path)},
        expected_metrics=["l2_error_u", "elapsed_seconds"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
        problem_definition={"solver_binary": "FallbackSolver"},
    )
    runner = NektarBenchmarkRunner(
        runs_root=tmp_path / "runs",
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider(
            {"extra_solver_args": ["--verbose", "unsafe.xml"], "rationale": "trace run"}
        ),
    )

    summary = runner.run_agent(case)

    validation = (
        tmp_path / "runs" / "nektar-pde-benchmark" / "agent" / "fixture" / "validation.json"
    ).read_text()
    assert summary.status == "passed"
    assert calls[0][-1] == "--verbose"
    assert "unsafe.xml" not in calls[0]
    assert "trace run" in validation


def test_nektar_adaptive_agent_records_repair_attempt(tmp_path: Path, monkeypatch) -> None:
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
    attempts = {"count": 0}

    def fake_run(command, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            return subprocess.CompletedProcess(command, 0, "", "")
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
        source_reference={"tst": str(tst_path)},
        expected_metrics=["l2_error_u", "elapsed_seconds"],
        reference_metrics={"l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8)},
        problem_definition={"solver_binary": "FallbackSolver"},
    )
    runner = NektarBenchmarkRunner(
        runs_root=tmp_path / "runs",
        allow_real_tools=True,
        adaptive_agent=True,
        max_repair_attempts=1,
        brain_provider=FakeClaudeCLIBrainProvider({"extra_solver_args": ["--verbose"]}),
    )

    summary = runner.run_agent(case)

    assert summary.status == "passed"
    assert summary.repair_count == 1
    assert summary.llm_calls == 2
    assert attempts["count"] == 2


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
    assert summaries[1].preflight_status == "passed"
    assert summaries[2].llm_calls == 1
    assert summaries[2].preflight_status == "passed"
    base = tmp_path / "nektar-pde-benchmark"
    assert (base / "extension" / "advdiff-2d" / "session.xml").exists()
    assert (base / "direct" / "advdiff-2d" / "solver.stdout.log").exists()
    direct_prompt = (base / "direct" / "advdiff-2d" / "claude_prompt.txt").read_text()
    assert "no tool calls" in direct_prompt
    assert "the benchmark runner materializes the trusted reference XML" in direct_prompt
    assert (base / "agent" / "advdiff-2d" / "proposal_preflight.json").exists()
    assert (base / "agent" / "advdiff-2d" / "proposal.json").exists()


def test_nektar_claude_turn_limit_failure_is_categorized(tmp_path: Path) -> None:
    class TurnLimitProvider:
        def propose(self, *, prompt: str, output_dir: Path) -> ClaudeCLIResult:
            output_dir.mkdir(parents=True, exist_ok=True)
            prompt_path = write_text(output_dir / "claude_prompt.txt", prompt)
            stdout_path = write_json(
                output_dir / "claude_stdout.json",
                {"is_error": True, "terminal_reason": "Reached maximum number of turns (5)"},
            )
            stderr_path = write_text(output_dir / "claude_stderr.txt", "")
            result_path = write_json(
                output_dir / "claude_result.json",
                {"is_error": True, "terminal_reason": "Reached maximum number of turns (5)"},
            )
            proposal_path = write_json(output_dir / "proposal.json", {})
            invocation = ClaudeInvocationRecord(
                binary="claude",
                command=["claude", "--max-turns", "5"],
                prompt_path=str(prompt_path),
                stdout_path=str(stdout_path),
                stderr_path=str(stderr_path),
                result_path=str(result_path),
                proposal_path=str(proposal_path),
                return_code=1,
            )
            return ClaudeCLIResult(
                invocation=invocation,
                error="Reached maximum number of turns (5)",
            )

    case = nektar_case_catalog()["advection-1d"]
    runner = NektarBenchmarkRunner(runs_root=tmp_path, brain_provider=TurnLimitProvider())

    summary = runner.run_direct(case)

    assert summary.status == "failed"
    assert summary.failure_category == "proposal_max_turns"
    assert summary.proposal_contract_status == "failed"
    assert summary.preflight_status == "failed"
    assert summary.evidence_count == 6
    assert (
        tmp_path / "nektar-pde-benchmark" / "direct" / "advection-1d" / "proposal_preflight.json"
    ).exists()


def test_nektar_diffusion_case_is_replay_enabled() -> None:
    case = nektar_case_catalog()["diffusion-2d"]

    assert not case.capability_gated
    assert case.problem_definition["solver_binary"] == "DiffusionSolver"


def test_nektar_capability_gated_extension_dry_run_is_skipped(tmp_path: Path) -> None:
    case = nektar_case_catalog()["euler-1d"]
    runner = NektarBenchmarkRunner(runs_root=tmp_path)

    summary = runner.run_extension(case)

    output_dir = tmp_path / "nektar-pde-benchmark" / "extension" / "euler-1d"
    capability_status = read_json(output_dir / "capability_status.json")
    source_refs = read_json(output_dir / "source_refs.json")
    assert summary.status == "skipped"
    assert summary.skip_reason == "capability gated for current extension dispatch"
    assert str(output_dir / "capability_status.json") in summary.evidence_files
    assert str(output_dir / "source_refs.json") in summary.evidence_files
    assert capability_status["promotion_ready"] is False
    assert capability_status["missing_capabilities"] == [
        "nektar_compressible_solver_extension_dispatch"
    ]
    assert capability_status["plan_status"] == "extension_dispatch_unverified"
    assert capability_status["solver_binary"] == "CompressibleFlowSolver"
    assert source_refs["source_reference"] == case.source_reference
