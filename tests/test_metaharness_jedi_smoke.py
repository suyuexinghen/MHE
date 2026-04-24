from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import (
    JediEnvironmentReport,
    JediExecutableSpec,
    JediVariationalSpec,
)
from metaharness_ext.jedi.environment import JediEnvironmentProbeComponent
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.gateway import JediGatewayComponent
from metaharness_ext.jedi.validator import JediValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_spec(tmp_path: Path, *, execution_mode: str = "real_run") -> JediVariationalSpec:
    background = tmp_path / "background.nc"
    background.write_text("background")
    return JediVariationalSpec(
        task_id="jedi-smoke",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode=execution_mode),
        background_path=str(background),
        output={"filename": "analysis.out"},
    )


def test_jedi_gateway_issues_smoke_task_only_when_environment_ready() -> None:
    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent().probe(
        JediVariationalSpec(
            task_id="task-smoke-ready",
            executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        )
    )
    environment.binary_available = True
    environment.shared_libraries_resolved = True
    environment.required_paths_present = True
    environment.workspace_testinput_present = True
    environment.data_prerequisites_ready = True
    environment.smoke_candidate = "variational"
    environment.smoke_ready = True

    task = gateway.issue_smoke_task(environment, background_path="/tmp/background.nc")

    assert task.application_family == "variational"
    assert task.executable.binary_name == "qg4DVar.x"


def test_jedi_gateway_issues_hofx_smoke_task_when_observation_stack_is_ready() -> None:
    gateway = JediGatewayComponent()
    environment = JediEnvironmentReport(
        binary_available=True,
        launcher_available=True,
        shared_libraries_resolved=True,
        required_paths_present=True,
        workspace_testinput_present=True,
        data_paths_present=True,
        data_prerequisites_ready=True,
        smoke_candidate="hofx",
        smoke_ready=True,
    )

    task = gateway.issue_smoke_task(
        environment,
        background_path="/tmp/state.nc",
        observation_paths=["/tmp/obs.ioda"],
    )

    assert task.application_family == "hofx"
    assert task.executable.binary_name == "qgHofX4D.x"
    assert task.state_path == "/tmp/state.nc"


def test_jedi_gateway_falls_back_to_forecast_smoke_task() -> None:
    gateway = JediGatewayComponent()
    environment = JediEnvironmentReport(
        binary_available=True,
        launcher_available=True,
        shared_libraries_resolved=True,
        required_paths_present=True,
        workspace_testinput_present=True,
        data_paths_present=True,
        data_prerequisites_ready=False,
        smoke_candidate="variational",
        smoke_ready=True,
    )

    task = gateway.issue_smoke_task(environment, background_path="/tmp/init.nc")

    assert task.application_family == "forecast"
    assert task.executable.binary_name == "qgForecast.x"
    assert task.initial_condition_path == "/tmp/init.nc"


def test_jedi_gateway_rejects_smoke_task_when_environment_not_ready() -> None:
    gateway = JediGatewayComponent()
    environment = JediEnvironmentReport(
        binary_available=False,
        launcher_available=True,
        shared_libraries_resolved=True,
        required_paths_present=True,
        workspace_testinput_present=True,
        data_paths_present=True,
        data_prerequisites_ready=True,
        smoke_candidate="variational",
        smoke_ready=False,
        messages=["JEDI binary not found: qg4DVar.x"],
    )

    with pytest.raises(ValueError, match="Environment not smoke-ready"):
        gateway.issue_smoke_task(environment, background_path="/tmp/background.nc")


def test_jedi_environment_marks_smoke_ready_when_runtime_prereqs_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    binary = tmp_path / "qg4DVar.x"
    binary.write_text("binary")
    spec = JediVariationalSpec(
        task_id="task-env",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="real_run"),
        background_path=str(tmp_path / "background.nc"),
    )
    Path(spec.background_path).write_text("background")
    probe = JediEnvironmentProbeComponent()

    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.shutil.which", lambda name: "/usr/bin/ldd"
    )

    class _Result:
        returncode = 0
        stdout = ""

    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run", lambda *args, **kwargs: _Result()
    )

    report = probe.probe(spec)

    assert report.required_paths_present is True
    assert report.smoke_ready is True
    assert report.smoke_candidate == "variational"


@pytest.mark.asyncio
async def test_jedi_real_run_succeeds_with_runtime_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path)
    spec.expected_diagnostics = ["runtime-foundation.log"]
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{binary_name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "runtime-foundation.log").write_text("completed")
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.command == ["/usr/bin/qg4DVar.x", "config.yaml"]
    assert any(path.endswith("analysis.out") for path in artifact.output_files)
    assert any(path.endswith("runtime-foundation.log") for path in artifact.diagnostic_files)
    assert report.passed is True
    assert report.status == "executed"
    assert report.summary_metrics["primary_output"].endswith("analysis.out")


@pytest.mark.asyncio
async def test_jedi_real_run_without_runtime_evidence_fails_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path)
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{binary_name}",
    )
    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout="run ok", stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "completed"
    assert artifact.output_files == []
    assert report.passed is False
    assert report.status == "validation_failed"


@pytest.mark.asyncio
async def test_jedi_real_run_timeout_maps_to_runtime_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path)
    spec.executable.timeout_seconds = 5
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{binary_name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(command, timeout, output="partial", stderr="timeout")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "failed"
    assert report.passed is False
    assert report.status == "runtime_failed"
