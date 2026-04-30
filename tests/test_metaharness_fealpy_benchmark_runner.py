from __future__ import annotations

import json
import subprocess
from pathlib import Path

from metaharness.benchmark_drivers.claude_cli import FakeClaudeCLIBrainProvider
from metaharness.benchmark_drivers.models import BenchmarkCaseSpec
from metaharness_ext.fealpy.benchmark_runner import FealpyBenchmarkRunner
from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyRunArtifact,
    FealpyRunPlan,
    FealpyValidationReport,
)
from metaharness_ext.fealpy.types import FealpyValidationStatus


def _case() -> BenchmarkCaseSpec:
    return BenchmarkCaseSpec(
        case_id="poisson-2d-numpy",
        suite="fealpy-pde",
        task_family="fealpy_pde",
        description="2D Poisson FEALPy benchmark",
        source_reference={},
        expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
        problem_definition={
            "pde_family": "poisson",
            "example_key": 1,
            "backend": "numpy",
            "meshtype": "tri",
            "nx": 8,
            "ny": 8,
            "fe_degree": 1,
        },
    )


def test_fealpy_runner_dry_run_writes_all_lane_summaries(tmp_path: Path) -> None:
    runner = FealpyBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)

    summaries = runner.run_case(_case(), ["extension", "direct", "agent"])

    assert [summary.lane for summary in summaries] == ["extension", "direct", "agent"]
    for lane in ["extension", "direct", "agent"]:
        assert (
            tmp_path / "fealpy-pde-benchmark" / lane / "poisson-2d-numpy" / "summary.json"
        ).exists()
    assert (
        tmp_path / "fealpy-pde-benchmark" / "direct" / "poisson-2d-numpy" / "claude_prompt.txt"
    ).exists()
    assert (
        tmp_path / "fealpy-pde-benchmark" / "agent" / "poisson-2d-numpy" / "proposal_preflight.json"
    ).exists()


def test_fealpy_direct_real_run_uses_proposed_script(tmp_path: Path, monkeypatch) -> None:
    proposal = {
        "solve_py": "import json\nprint(json.dumps({'l2_error': 0.0, 'h1_error': 0.0, 'wall_time': 0.1, 'dof': 81}))\n"
    }
    runner = FealpyBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider(proposal),
    )
    monkeypatch.setattr(runner, "_fealpy_available", lambda: True)

    def fail_compile(*args, **kwargs):
        raise AssertionError("direct lane must not use FealpyCompilerComponent")

    monkeypatch.setattr(
        "metaharness_ext.fealpy.benchmark_runner.FealpyCompilerComponent.compile",
        fail_compile,
    )

    summary = runner.run_direct(_case())

    assert summary.lane == "direct"
    assert summary.status == "passed"
    assert summary.preflight_status == "passed"
    solve_path = tmp_path / "fealpy-pde-benchmark" / "direct" / "poisson-2d-numpy" / "solve.py"
    assert "l2_error" in solve_path.read_text()


def test_fealpy_direct_invalid_proposal_fails_preflight(tmp_path: Path, monkeypatch) -> None:
    runner = FealpyBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"not_script": "x"}),
    )
    monkeypatch.setattr(runner, "_fealpy_available", lambda: True)

    summary = runner.run_direct(_case())

    assert summary.status == "failed"
    assert summary.proposal_contract_status == "invalid"
    assert summary.preflight_status == "failed"
    assert summary.failure_category == "proposal_failure"
    preflight = json.loads(
        (
            tmp_path
            / "fealpy-pde-benchmark"
            / "direct"
            / "poisson-2d-numpy"
            / "proposal_preflight.json"
        ).read_text()
    )
    assert "proposal must include solve_py" in preflight["messages"]


def test_fealpy_direct_invalid_dry_run_proposal_fails_preflight(tmp_path: Path) -> None:
    runner = FealpyBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=False,
        brain_provider=FakeClaudeCLIBrainProvider({"not_script": "x"}),
    )

    summary = runner.run_direct(_case())

    assert summary.status == "failed"
    assert summary.preflight_status == "failed"
    assert summary.failure_category == "proposal_failure"


def test_fealpy_agent_valid_spec_routes_through_extension_pipeline(
    tmp_path: Path, monkeypatch
) -> None:
    runner = FealpyBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"spec_patch": {"nx": 12, "ny": 12}}),
    )
    monkeypatch.setattr(runner, "_fealpy_available", lambda: True)

    class FakeEnvironment:
        def probe(self, spec):
            return FealpyEnvironmentReport(
                task_id=spec.task_id,
                available=True,
                status="available",
                available_backends=["numpy"],
            )

    class FakeCompiler:
        def compile(self, spec, environment=None):
            assert spec.mesh.nx == 12
            return FealpyRunPlan(
                plan_id="plan-1",
                task_id=spec.task_id,
                run_id="run-1",
                spec=spec,
                workspace_dir=str(tmp_path / "workspace"),
                script_source="print('{}')",
            )

    class FakeExecutor:
        def execute_plan(self, plan, environment=None):
            return FealpyRunArtifact(
                artifact_id="artifact-1",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="completed",
                l2_error=0.0,
                h1_error=0.0,
                wall_time_seconds=0.1,
                dof_count=144,
                summary_metrics={"l2_error": 0.0, "h1_error": 0.0, "wall_time": 0.1, "dof": 144},
            )

    class FakeValidator:
        def validate(self, artifact, plan, l2_tolerance=1e-6, h1_tolerance=1e-4):
            return FealpyValidationReport(
                task_id=artifact.task_id,
                plan_ref=plan.plan_id,
                artifact_ref=artifact.artifact_id,
                passed=True,
                status=FealpyValidationStatus.EXECUTED,
                l2_passed=True,
                h1_passed=True,
                summary_metrics={"l2_error": 0.0, "h1_error": 0.0, "wall_time": 0.1, "dof": 144},
            )

    monkeypatch.setattr(
        "metaharness_ext.fealpy.benchmark_runner.FealpyEnvironmentProbeComponent", FakeEnvironment
    )
    monkeypatch.setattr(
        "metaharness_ext.fealpy.benchmark_runner.FealpyCompilerComponent", FakeCompiler
    )
    monkeypatch.setattr(
        "metaharness_ext.fealpy.benchmark_runner.FealpyExecutorComponent", FakeExecutor
    )
    monkeypatch.setattr(
        "metaharness_ext.fealpy.benchmark_runner.FealpyValidatorComponent", FakeValidator
    )

    summary = runner.run_agent(_case())

    assert summary.lane == "agent"
    assert summary.status == "passed"
    assert summary.preflight_status == "passed"
    written = json.loads(
        (
            tmp_path / "fealpy-pde-benchmark" / "agent" / "poisson-2d-numpy" / "summary.json"
        ).read_text()
    )
    assert written["lane"] == "agent"


def test_fealpy_agent_unknown_spec_field_fails_preflight(tmp_path: Path, monkeypatch) -> None:
    runner = FealpyBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"spec_patch": {"unsafe_field": True}}),
    )
    monkeypatch.setattr(runner, "_fealpy_available", lambda: True)

    summary = runner.run_agent(_case())

    assert summary.status == "failed"
    assert summary.preflight_status == "failed"
    assert summary.failure_category == "proposal_failure"
    assert "unknown FealpyProblemSpec fields" in (summary.error_message or "")


def test_fealpy_direct_timeout_is_solver_failure(tmp_path: Path, monkeypatch) -> None:
    runner = FealpyBenchmarkRunner(
        runs_root=tmp_path,
        allow_real_tools=True,
        brain_provider=FakeClaudeCLIBrainProvider({"solve_py": "print('slow')"}),
    )
    monkeypatch.setattr(runner, "_fealpy_available", lambda: True)

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="python solve.py", timeout=1)

    monkeypatch.setattr("metaharness_ext.fealpy.benchmark_runner.subprocess.run", timeout)

    summary = runner.run_direct(_case())

    assert summary.status == "failed"
    assert summary.failure_category == "solver_failure"
