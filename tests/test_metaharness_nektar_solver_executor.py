from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness.provenance import ArtifactSnapshotStore
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.contracts import NektarProblemSpec
from metaharness_ext.nektar.postprocess import PostprocessComponent
from metaharness_ext.nektar.session_compiler import build_session_plan
from metaharness_ext.nektar.solver_executor import SolverExecutorComponent
from metaharness_ext.nektar.types import NektarAdrEqType, NektarSolverFamily
from metaharness_ext.nektar.validator import NektarValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.mark.asyncio
async def test_solver_executor_requires_runtime_storage_path(tmp_path: Path) -> None:
    problem = NektarProblemSpec(
        task_id="task-no-runtime",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=None))

    with pytest.raises(RuntimeError, match="runtime.storage_path"):
        executor.execute_plan(plan)


def test_build_session_plan_adds_time_integration_for_unsteady_adr() -> None:
    problem = NektarProblemSpec(
        task_id="task-unsteady-adr",
        title="reaction diffusion",
        solver_family=NektarSolverFamily.ADR,
        equation_type=NektarAdrEqType.UNSTEADY_REACTION_DIFFUSION,
        dimension=2,
        variables=["u"],
    )

    plan = build_session_plan(problem)

    assert plan.equation_type == NektarAdrEqType.UNSTEADY_REACTION_DIFFUSION
    assert plan.time_integration == {"METHOD": "IMEX", "ORDER": 3}
    assert plan.parameters["TimeStep"] == 0.001
    assert plan.parameters["NumSteps"] == 100


@pytest.mark.asyncio
async def test_solver_executor_runs_inline_session_and_collects_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-inline",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    calls: list[dict[str, object]] = []

    def fake_which(binary: str) -> str:
        return f"/usr/bin/{binary}"

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: float,
    ) -> _FakeCompletedProcess:
        calls.append(
            {
                "command": command,
                "cwd": cwd,
                "text": text,
                "capture_output": capture_output,
                "check": check,
            }
        )
        (cwd / "solution.fld").write_text("field-data")
        return _FakeCompletedProcess(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.solver_executor.shutil.which", fake_which)
    monkeypatch.setattr("metaharness_ext.nektar.solver_executor.subprocess.run", fake_run)

    run_artifact = executor.execute_plan(plan)

    session_path = tmp_path / "nektar_runs" / problem.task_id / plan.session_file_name
    assert session_path.exists()
    assert calls[0]["command"] == ["/usr/bin/ADRSolver", str(session_path)]
    assert calls[0]["cwd"] == session_path.parent
    assert run_artifact.field_files == [str(session_path.parent / "solution.fld")]
    assert run_artifact.status == "completed"
    assert run_artifact.result_summary["ran_solver"] is True
    assert run_artifact.result_summary["exit_code"] == 0
    assert run_artifact.graph_metadata["plan_id"] == plan.plan_id
    assert run_artifact.execution_policy.sandbox_profile == "workspace-write"
    assert any(
        ref == f"provenance://nektar/run/{plan.task_id}" for ref in run_artifact.provenance_refs
    )
    assert any(ref == f"trace://nektar/task/{plan.task_id}" for ref in run_artifact.trace_refs)
    assert run_artifact.scored_evidence is not None
    assert run_artifact.scored_evidence.score == pytest.approx(1.0)
    assert f"trace://nektar/task/{plan.task_id}" in run_artifact.scored_evidence.evidence_refs
    assert run_artifact.result_summary["scored_evidence"]["score"] == pytest.approx(1.0)
    assert set(Path(path).name for path in run_artifact.log_files) == {
        "solver.log",
        "solver.stdout.log",
        "solver.stderr.log",
    }


@pytest.mark.asyncio
async def test_solver_executor_runs_external_mesh_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mesh_path = tmp_path / "channel.xml"
    mesh_path.write_text("<NEKTAR />")
    problem = NektarProblemSpec(
        task_id="task-overlay",
        title="incns",
        solver_family=NektarSolverFamily.INCNS,
        dimension=2,
        variables=["u", "v", "p"],
        domain={"mesh_path": str(mesh_path)},
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    calls: list[list[str]] = []

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: float,
    ) -> _FakeCompletedProcess:
        calls.append(command)
        (cwd / "session.chk").write_text("checkpoint")
        return _FakeCompletedProcess(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.solver_executor.subprocess.run", fake_run)

    run_artifact = executor.execute_plan(plan)

    session_path = tmp_path / "nektar_runs" / problem.task_id / plan.session_file_name
    assert calls[0] == ["/usr/bin/IncNavierStokesSolver", str(mesh_path), str(session_path)]
    assert run_artifact.mesh_files == [str(mesh_path)]
    assert run_artifact.filter_output.checkpoint_files == [str(session_path.parent / "session.chk")]
    assert run_artifact.checkpoint_refs == [str(session_path.parent / "session.chk")]
    assert any(ref == f"trace://nektar/task/{plan.task_id}" for ref in run_artifact.trace_refs)
    assert run_artifact.scored_evidence is not None
    assert str(session_path.parent / "session.chk") in run_artifact.scored_evidence.evidence_refs
    assert run_artifact.status == "completed"


@pytest.mark.asyncio
async def test_solver_executor_marks_binary_missing_as_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-missing-bin",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr("metaharness_ext.nektar.solver_executor.shutil.which", lambda binary: None)

    run_artifact = executor.execute_plan(plan)

    assert run_artifact.status == "unavailable"
    assert run_artifact.result_summary["fallback_reason"] == "solver_binary_not_found"
    assert run_artifact.result_summary["ran_solver"] is False
    assert Path(run_artifact.log_files[0]).read_text() == "Solver binary not found: ADRSolver"


@pytest.mark.asyncio
async def test_solver_executor_marks_nonzero_exit_as_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-failed",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=7,
            stdout="",
            stderr="boom",
        ),
    )

    run_artifact = executor.execute_plan(plan)

    assert run_artifact.status == "failed"
    assert run_artifact.result_summary["exit_code"] == 7
    assert Path(run_artifact.log_files[0]).read_text() == "boom"


@pytest.mark.asyncio
async def test_solver_executor_marks_timeout_as_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-timeout",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
        parameters={"SolverTimeout": 12},
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(
            command, timeout, output="partial-out", stderr="partial-err"
        )

    monkeypatch.setattr("metaharness_ext.nektar.solver_executor.subprocess.run", fake_run)

    run_artifact = executor.execute_plan(plan)

    assert run_artifact.status == "failed"
    assert run_artifact.result_summary["fallback_reason"] == "solver_timeout"
    assert run_artifact.result_summary["timeout_seconds"] == 12.0
    assert "timed out after 12.0 seconds" in Path(run_artifact.log_files[0]).read_text()


@pytest.mark.asyncio
async def test_solver_executor_rejects_unsafe_task_id(tmp_path: Path) -> None:
    problem = NektarProblemSpec(
        task_id="../unsafe/task",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    with pytest.raises(ValueError, match="Invalid task_id"):
        executor.execute_plan(plan)


def test_postprocess_prefers_field_then_checkpoint() -> None:
    problem = NektarProblemSpec(
        task_id="task-postprocess",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    artifact = SolverExecutorComponent()._build_run_artifact(
        plan,
        session_path=Path("/tmp/session.xml"),
        mesh_path=None,
        field_files=["/tmp/solution.fld"],
        checkpoint_files=["/tmp/session.chk"],
        log_files=["/tmp/solver.log"],
        status="completed",
        result_summary={"exit_code": 0},
    )

    updated = PostprocessComponent().run_postprocess(artifact)

    step = updated.result_summary["postprocess"]["steps"][0]
    if "command" in step:
        assert step["command"][-2] == "/tmp/solution.fld"
    else:
        assert step["fallback_reason"] == "fieldconvert_binary_not_found"


def test_postprocess_falls_back_to_checkpoint_when_no_field_files() -> None:
    problem = NektarProblemSpec(
        task_id="task-postprocess-checkpoint",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    artifact = SolverExecutorComponent()._build_run_artifact(
        plan,
        session_path=Path("/tmp/session.xml"),
        mesh_path=None,
        field_files=[],
        checkpoint_files=["/tmp/b.chk", "/tmp/a.chk"],
        log_files=["/tmp/solver.log"],
        status="completed",
        result_summary={"exit_code": 0},
    )

    updated = PostprocessComponent().run_postprocess(artifact)

    step = updated.result_summary["postprocess"]["steps"][0]
    if "command" in step:
        assert step["command"][-2] == "/tmp/b.chk"
    else:
        assert step["fallback_reason"] == "fieldconvert_binary_not_found"


def test_validator_uses_real_execution_metadata() -> None:
    problem = NektarProblemSpec(
        task_id="task-validate",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    artifact = SolverExecutorComponent()._build_run_artifact(
        plan,
        session_path=Path("/tmp/session.xml"),
        mesh_path=None,
        field_files=["/tmp/solution.fld"],
        checkpoint_files=[],
        log_files=["/tmp/solver.log"],
        status="completed",
        result_summary={"exit_code": 0, "fallback_reason": None},
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.passed is True
    assert report.solver_exited_cleanly is True
    assert report.field_files_exist is True
    assert report.error_vs_reference is None
    assert report.scored_evidence is not None
    assert report.scored_evidence.score == pytest.approx(1.0)
    assert report.trace_refs == artifact.trace_refs


def test_validator_reports_missing_binary_as_failure() -> None:
    problem = NektarProblemSpec(
        task_id="task-validate-fallback",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    artifact = SolverExecutorComponent()._build_run_artifact(
        plan,
        session_path=Path("/tmp/session.xml"),
        mesh_path=None,
        field_files=[],
        checkpoint_files=[],
        log_files=["/tmp/solver.log"],
        status="unavailable",
        result_summary={"exit_code": None, "fallback_reason": "solver_binary_not_found"},
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.solver_exited_cleanly is False
    assert report.field_files_exist is False
    assert any("solver_binary_not_found" in message for message in report.messages)


def test_validator_fails_when_solver_succeeds_without_outputs() -> None:
    problem = NektarProblemSpec(
        task_id="task-validate-no-outputs",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    artifact = SolverExecutorComponent()._build_run_artifact(
        plan,
        session_path=Path("/tmp/session.xml"),
        mesh_path=None,
        field_files=[],
        checkpoint_files=[],
        log_files=["/tmp/solver.log"],
        status="completed",
        result_summary={"exit_code": 0, "fallback_reason": None},
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.solver_exited_cleanly is True
    assert report.field_files_exist is False
    assert any(
        "No field or checkpoint outputs were produced." in message for message in report.messages
    )


@pytest.mark.asyncio
async def test_solver_executor_extracts_error_norms_from_adr_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-adr-norms",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    adr_output = (
        'Writing: "session.fld" (0.000123s, XML)\n'
        "-------------------------------------------\n"
        "Total Computation Time = 0.000123s\n"
        "-------------------------------------------\n"
        "L 2 error (variable u) : 1.11262e-05\n"
        "L inf error (variable u) : 1.28659e-05\n"
    )

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0,
            stdout=adr_output,
            stderr="",
        ),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.filter_output.error_norms["l2_error_u"] == pytest.approx(1.11262e-05)
    assert artifact.filter_output.error_norms["linf_error_u"] == pytest.approx(1.28659e-05)


@pytest.mark.asyncio
async def test_solver_executor_extracts_error_norms_from_incns_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-incns-norms",
        title="taylor vortex",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    incns_output = (
        "Steps: 50       Time: 0.5          CPU Time: 0.194524s\n"
        "Time-integration  : 0.194524s\n"
        "L 2 error (variable u) : 5.9519e-06\n"
        "L inf error (variable u) : 4.15477e-06\n"
        "L 2 error (variable v) : 4.99594e-06\n"
        "L inf error (variable v) : 4.51605e-06\n"
        "L 2 error (variable p) : 0.000232626\n"
        "L inf error (variable p) : 0.000162441\n"
    )

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0,
            stdout=incns_output,
            stderr="",
        ),
    )

    artifact = executor.execute_plan(plan)

    norms = artifact.filter_output.error_norms
    assert norms["l2_error_u"] == pytest.approx(5.9519e-06)
    assert norms["l2_error_v"] == pytest.approx(4.99594e-06)
    assert norms["l2_error_p"] == pytest.approx(0.000232626)
    assert norms["linf_error_p"] == pytest.approx(0.000162441)
    assert len(norms) == 6


@pytest.mark.asyncio
async def test_solver_executor_extracts_norms_on_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-timeout-norms",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
        parameters={"SolverTimeout": 5},
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(
            command, timeout, output="L 2 error (variable u) : 1e-03", stderr=""
        )

    monkeypatch.setattr("metaharness_ext.nektar.solver_executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    assert artifact.status == "failed"
    assert artifact.filter_output.error_norms["l2_error_u"] == pytest.approx(1e-03)


@pytest.mark.asyncio
async def test_solver_executor_omits_norms_when_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-no-norms",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout="no error norms here", stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.filter_output.error_norms == {}


@pytest.mark.asyncio
async def test_solver_executor_extracts_norms_on_nonzero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-failed-norms",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=1,
            stdout="L 2 error (variable u) : 2.5e-02\n",
            stderr="solver error",
        ),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.status == "failed"
    assert artifact.filter_output.error_norms["l2_error_u"] == pytest.approx(2.5e-02)


@pytest.mark.asyncio
async def test_solver_executor_extracts_step_metrics_from_incns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-step-metrics",
        title="taylor vortex",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    incns_output = (
        "Steps: 10       Time: 0.1          CPU Time: 0.05s\n"
        "Steps: 20       Time: 0.2          CPU Time: 0.10s\n"
        "Steps: 50       Time: 0.5          CPU Time: 0.25s\n"
        "Time-integration  : 0.25s\n"
        "-------------------------------------------\n"
        "Total Computation Time = 0.256s\n"
    )

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout=incns_output, stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)

    metrics = artifact.filter_output.metrics
    assert metrics["total_steps"] == 50
    assert metrics["final_time"] == pytest.approx(0.5)
    assert metrics["cpu_time"] == pytest.approx(0.25)
    assert metrics["wall_time"] == pytest.approx(0.256)


@pytest.mark.asyncio
async def test_solver_executor_extracts_wall_time_from_adr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-adr-walltime",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )

    adr_output = (
        'Writing: "session.fld" (0.000123s, XML)\n'
        "-------------------------------------------\n"
        "Total Computation Time = 0.000456s\n"
    )

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout=adr_output, stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)

    metrics = artifact.filter_output.metrics
    assert "total_steps" not in metrics
    assert metrics["wall_time"] == pytest.approx(0.000456)


@pytest.mark.asyncio
async def test_solver_executor_step_metrics_empty_when_no_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-no-metrics",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout="", stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)

    assert artifact.filter_output.metrics == {}


@pytest.mark.asyncio
async def test_solver_executor_records_run_artifact_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    problem = NektarProblemSpec(
        task_id="task-persist",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    executor = SolverExecutorComponent()
    artifact_store = ArtifactSnapshotStore()
    await executor.activate(ComponentRuntime(storage_path=tmp_path, artifact_store=artifact_store))

    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.shutil.which",
        lambda binary: f"/usr/bin/{binary}",
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.solver_executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout="ok", stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)

    history = artifact_store.history(artifact.run_id)
    assert len(history) == 1
    assert history[0].artifact_kind == "run_artifact"
    assert history[0].payload["run_id"] == artifact.run_id


def test_nektar_validator_records_validation_snapshot(tmp_path: Path) -> None:
    problem = NektarProblemSpec(
        task_id="task-validate-persist",
        title="helmholtz",
        solver_family=NektarSolverFamily.ADR,
        dimension=2,
        variables=["u"],
    )
    plan = build_session_plan(problem)
    artifact = SolverExecutorComponent()._build_run_artifact(
        plan,
        session_path=tmp_path / "session.xml",
        mesh_path=None,
        field_files=[str(tmp_path / "solution.fld")],
        checkpoint_files=[],
        log_files=[str(tmp_path / "solver.log")],
        status="completed",
        result_summary={"exit_code": 0, "fallback_reason": None},
    )

    validator = NektarValidatorComponent()
    import asyncio

    artifact_store = ArtifactSnapshotStore()
    asyncio.run(validator.activate(ComponentRuntime(artifact_store=artifact_store)))
    report = validator.validate_run(artifact)

    history = artifact_store.history(report.task_id)
    assert len(history) == 1
    assert history[0].artifact_kind == "validation_outcome"
    assert history[0].payload["task_id"] == report.task_id
