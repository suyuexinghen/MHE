from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import JediExecutableSpec, JediVariationalSpec
from metaharness_ext.jedi.environment import JediEnvironmentProbeComponent
from metaharness_ext.jedi.executor import JediExecutorComponent
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

    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", lambda name: "/usr/bin/ldd")

    class _Result:
        returncode = 0
        stdout = ""

    monkeypatch.setattr("metaharness_ext.jedi.environment.subprocess.run", lambda *args, **kwargs: _Result())

    report = probe.probe(spec)

    assert report.required_paths_present is True
    assert report.smoke_ready is True
    assert report.smoke_candidate == "variational"


@pytest.mark.asyncio
async def test_jedi_real_run_succeeds_with_runtime_evidence(
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

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "smoke.log").write_text("completed")
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.command == ["/usr/bin/qg4DVar.x", "config.yaml"]
    assert any(path.endswith("analysis.out") for path in artifact.output_files)
    assert any(path.endswith("smoke.log") for path in artifact.diagnostic_files)
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
