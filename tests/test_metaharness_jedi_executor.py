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
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.preprocessor import JediRunPreprocessor
from metaharness_ext.jedi.validator import JediValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_spec(
    *, task_id: str = "jedi-task", execution_mode: str = "validate_only"
) -> JediVariationalSpec:
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
    assert report.blocking_reasons == []
    assert report.policy_decision == "allow"


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
    assert report.blocking_reasons == []
    assert report.policy_decision == "allow"


@pytest.mark.asyncio
async def test_jedi_executor_threads_orchestration_ids_into_artifact_summary(
    tmp_path: Path, monkeypatch
) -> None:
    spec = JediVariationalSpec(
        task_id="jedi-orch-ids",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        candidate_id="candidate-99",
        graph_version_id=12,
        session_id="session-99",
        audit_refs=["audit-record:xyz"],
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
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

    assert artifact.result_summary["candidate_id"] == "candidate-99"
    assert artifact.result_summary["graph_version_id"] == 12
    assert artifact.result_summary["session_id"] == "session-99"
    assert artifact.result_summary["audit_refs"] == ["audit-record:xyz"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("launcher", "launcher_args", "expected_command"),
    [
        (
            "mpiexec",
            ["--bind-to", "core"],
            [
                "/usr/bin/mpiexec",
                "-n",
                "4",
                "--bind-to",
                "core",
                "/usr/bin/qg4DVar.x",
                "config.yaml",
            ],
        ),
        (
            "mpirun",
            ["--bind-to", "core"],
            [
                "/usr/bin/mpirun",
                "-n",
                "4",
                "--bind-to",
                "core",
                "/usr/bin/qg4DVar.x",
                "config.yaml",
            ],
        ),
        (
            "srun",
            ["--cpu-bind=cores"],
            [
                "/usr/bin/srun",
                "-n",
                "4",
                "--cpu-bind=cores",
                "/usr/bin/qg4DVar.x",
                "config.yaml",
            ],
        ),
        (
            "jsrun",
            ["--stdio_mode", "individual"],
            [
                "/usr/bin/jsrun",
                "-n",
                "4",
                "--stdio_mode",
                "individual",
                "/usr/bin/qg4DVar.x",
                "config.yaml",
            ],
        ),
    ],
)
async def test_jedi_executor_builds_launcher_specific_real_run_command(
    tmp_path: Path,
    monkeypatch,
    launcher: str,
    launcher_args: list[str],
    expected_command: list[str],
) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    spec = JediVariationalSpec(
        task_id=f"jedi-{launcher}",
        executable=JediExecutableSpec(
            binary_name="qg4DVar.x",
            launcher=launcher,
            launcher_args=launcher_args,
            process_count=4,
            execution_mode="real_run",
        ),
        background_path=str(background),
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "departures.json").write_text("{}")
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    assert artifact.command == expected_command


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("launcher", "launcher_arg"),
    [
        ("mpiexec", "-n"),
        ("mpiexec", "-np"),
        ("mpirun", "-n4"),
        ("mpirun", "-np=4"),
        ("srun", "--ntasks=4"),
        ("jsrun", "-n"),
    ],
)
async def test_jedi_executor_rejects_duplicate_launcher_process_count_flags(
    tmp_path: Path,
    launcher: str,
    launcher_arg: str,
) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    plan = JediConfigCompilerComponent().build_plan(
        JediVariationalSpec(
            task_id=f"duplicate-{launcher}",
            executable=JediExecutableSpec(
                binary_name="qg4DVar.x",
                launcher=launcher,
                launcher_args=[launcher_arg, "4"],
                process_count=4,
                execution_mode="real_run",
            ),
            background_path=str(background),
        )
    )
    executor = JediExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    with pytest.raises(
        ValueError,
        match="launcher_args must not include process-count flags; use executable.process_count",
    ):
        executor._build_launcher_command(plan, f"/usr/bin/{launcher}")


@pytest.mark.asyncio
async def test_jedi_executor_reports_missing_required_runtime_path(tmp_path: Path) -> None:
    missing_background = tmp_path / "missing-background.nc"
    spec = JediVariationalSpec(
        task_id="missing-runtime-path",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        background_path=str(missing_background),
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "unavailable"
    assert artifact.return_code is None
    assert artifact.prepared_inputs == []
    assert artifact.result_summary["fallback_reason"] == "missing_required_runtime_path"
    assert report.passed is False
    assert report.status == "environment_invalid"
    assert report.blocking_reasons == report.messages
    assert report.policy_decision == "reject"


@pytest.mark.asyncio
async def test_jedi_executor_reports_missing_binary_as_environment_invalid(
    tmp_path: Path,
) -> None:
    spec = _build_spec(execution_mode="validate_only")
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "unavailable"
    assert artifact.return_code is None
    assert artifact.result_summary["fallback_reason"] == "binary_not_found"
    assert report.passed is False
    assert report.status == "environment_invalid"
    assert report.blocking_reasons == report.messages
    assert report.policy_decision == "reject"


@pytest.mark.asyncio
async def test_jedi_executor_reports_missing_launcher_as_environment_invalid(
    tmp_path: Path, monkeypatch
) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    plan = JediConfigCompilerComponent().build_plan(
        JediVariationalSpec(
            task_id="missing-launcher",
            executable=JediExecutableSpec(
                binary_name="qg4DVar.x",
                launcher="mpiexec",
                process_count=2,
                execution_mode="real_run",
            ),
            background_path=str(background),
        )
    )
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    def fake_resolve(self, binary_name: str) -> str | None:
        if binary_name == "qg4DVar.x":
            return "/usr/bin/qg4DVar.x"
        return None

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        fake_resolve,
    )

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "unavailable"
    assert artifact.return_code is None
    assert artifact.result_summary["fallback_reason"] == "launcher_not_found"
    assert report.passed is False
    assert report.status == "environment_invalid"
    assert report.blocking_reasons == report.messages
    assert report.policy_decision == "reject"


@pytest.mark.asyncio
async def test_jedi_executor_threads_environment_prerequisite_handoff_into_artifact_summary(
    tmp_path: Path, monkeypatch
) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    spec = JediVariationalSpec(
        task_id="jedi-prereq-handoff",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        background_path=str(background),
    )
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

    environment_report = JediEnvironmentReport(
        binary_available=True,
        launcher_available=True,
        shared_libraries_resolved=True,
        required_paths_present=True,
        data_prerequisites_ready=True,
        ready_prerequisites=["workspace testinput", "ctest -R qg_get_data or equivalent QG data preparation"],
        prerequisite_evidence={
            "workspace testinput": [str((tmp_path / "testinput").resolve())],
            "ctest -R qg_get_data or equivalent QG data preparation": [str(background.resolve())],
        },
    )

    artifact = executor.execute_plan(plan, environment_report=environment_report)
    report = validator.validate_run(artifact)

    assert artifact.result_summary["prerequisite_evidence"] == environment_report.prerequisite_evidence
    assert report.prerequisite_evidence == environment_report.prerequisite_evidence
    assert report.checkpoint_refs == [
        "checkpoint://jedi/prerequisite/workspace-testinput",
        "checkpoint://jedi/prerequisite/ctest-r-qg-get-data-or-equivalent-qg-data-preparation",
    ]


@pytest.mark.asyncio
async def test_jedi_executor_times_out_and_returns_runtime_failed(
    tmp_path: Path, monkeypatch
) -> None:
    spec = _build_spec(execution_mode="validate_only")
    plan = JediConfigCompilerComponent().build_plan(
        spec.model_copy(update={"executable": spec.executable.model_copy(update={"timeout_seconds": 5})})
    )
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{binary_name}",
    )

    timeout_error = subprocess.TimeoutExpired(cmd=["/usr/bin/qg4DVar.x"], timeout=5)
    timeout_error.stdout = b"partial stdout"
    timeout_error.stderr = b"partial stderr"

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise timeout_error

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.status == "failed"
    assert artifact.return_code is None
    assert artifact.result_summary["fallback_reason"] == "command_timeout"
    assert report.passed is False
    assert report.status == "runtime_failed"
    assert report.blocking_reasons == report.messages
    assert report.policy_decision == "defer"


def test_jedi_preprocessor_materializes_config_and_checks_required_runtime_paths(tmp_path: Path) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    spec = JediVariationalSpec(
        task_id="preprocessor-demo",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        background_path=str(background),
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    prepared_inputs = JediRunPreprocessor().prepare(plan, run_dir)

    assert run_dir.joinpath("config.yaml").exists()
    assert prepared_inputs == [str(background)]


def test_jedi_preprocessor_rejects_missing_required_runtime_path(tmp_path: Path) -> None:
    missing_background = tmp_path / "missing-background.nc"
    spec = JediVariationalSpec(
        task_id="preprocessor-missing",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
        background_path=str(missing_background),
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    with pytest.raises(ValueError, match="Missing required runtime path"):
        JediRunPreprocessor().prepare(plan, run_dir)
