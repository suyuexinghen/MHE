from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import JediExecutableSpec, JediRunArtifact, JediVariationalSpec
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.validator import JediValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_spec(*, task_id: str = "jedi-task", execution_mode: str = "validate_only") -> JediVariationalSpec:
    return JediVariationalSpec(
        task_id=task_id,
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode=execution_mode),
    )


@pytest.mark.asyncio
async def test_jedi_executor_requires_runtime_storage_path(tmp_path: Path) -> None:
    spec = _build_spec()
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=None))

    with pytest.raises(RuntimeError, match="runtime.storage_path"):
        executor.execute_plan(plan)


@pytest.mark.asyncio
async def test_jedi_executor_builds_schema_command(tmp_path: Path, monkeypatch) -> None:
    spec = _build_spec(execution_mode="schema")
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{binary_name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "schema.json").write_text("{}")
        return _FakeCompletedProcess(returncode=0, stdout="schema ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.command == ["/usr/bin/qg4DVar.x", "--output-json-schema=schema.json"]
    assert artifact.schema_path is not None
    assert report.passed is True
    assert report.status == "validated"


@pytest.mark.asyncio
async def test_jedi_executor_builds_validate_only_command(tmp_path: Path, monkeypatch) -> None:
    spec = _build_spec(execution_mode="validate_only")
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
            returncode=0, stdout="validate ok", stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.command == ["/usr/bin/qg4DVar.x", "--validate-only", "config.yaml"]
    assert report.passed is True
    assert report.status == "validated"


@pytest.mark.asyncio
async def test_jedi_executor_marks_missing_binary_as_environment_invalid(
    tmp_path: Path, monkeypatch
) -> None:
    spec = _build_spec(execution_mode="validate_only")
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: None,
    )

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "unavailable"
    assert artifact.result_summary["fallback_reason"] == "binary_not_found"
    assert report.status == "environment_invalid"


@pytest.mark.asyncio
async def test_jedi_executor_marks_timeout_as_runtime_failed(tmp_path: Path, monkeypatch) -> None:
    spec = _build_spec(execution_mode="validate_only")
    spec.executable.timeout_seconds = 12
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{binary_name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(command, timeout, output="partial-out", stderr="partial-err")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "failed"
    assert artifact.result_summary["fallback_reason"] == "command_timeout"
    assert report.status == "runtime_failed"


@pytest.mark.asyncio
async def test_jedi_executor_maps_nonzero_validate_only_to_runtime_failed(
    tmp_path: Path, monkeypatch
) -> None:
    spec = _build_spec(execution_mode="validate_only")
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
            returncode=2, stdout="", stderr="invalid config"
        ),
    )

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.return_code == 2
    assert report.passed is False
    assert report.status == "runtime_failed"


@pytest.mark.asyncio
async def test_jedi_executor_rejects_unsafe_task_id(tmp_path: Path) -> None:
    spec = _build_spec(task_id="../unsafe/task", execution_mode="validate_only")
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    with pytest.raises(ValueError, match="Invalid task_id"):
        executor.execute_plan(plan)


def test_jedi_validator_rejects_completed_artifact_without_exit_code() -> None:
    artifact = JediRunArtifact(
        task_id="task-1",
        run_id="run-1",
        application_family="variational",
        execution_mode="validate_only",
        command=["/usr/bin/qg4DVar.x", "--validate-only", "config.yaml"],
        return_code=None,
        config_path="/tmp/config.yaml",
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run-1",
        status="completed",
    )

    report = JediValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "runtime_failed"
    assert "did not report an exit code" in report.messages[0]
