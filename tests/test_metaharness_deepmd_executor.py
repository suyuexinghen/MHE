from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import (
    DeepMDDatasetSpec,
    DeepMDDescriptorSpec,
    DeepMDDiagnosticSummary,
    DeepMDExecutableSpec,
    DeepMDFittingNetSpec,
    DeepMDModeInputSpec,
    DeepMDRunArtifact,
    DeepMDTrainSpec,
)
from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_spec(
    tmp_path: Path,
    *,
    task_id: str = "deepmd-task",
    execution_mode: str = "train",
    train_systems: list[str] | None = None,
    mode_inputs: DeepMDModeInputSpec | None = None,
) -> DeepMDTrainSpec:
    if train_systems is None:
        train_system = tmp_path / "train_system"
        train_system.mkdir()
        train_systems = [str(train_system)]
    return DeepMDTrainSpec(
        task_id=task_id,
        executable=DeepMDExecutableSpec(execution_mode=execution_mode),
        dataset=DeepMDDatasetSpec(
            dataset_id=task_id,
            train_systems=train_systems,
            validation_systems=[],
            type_map=["H", "O"],
            labels_present=["energy", "force"],
        ),
        type_map=["H", "O"],
        descriptor=DeepMDDescriptorSpec(
            descriptor_type="se_e2_a",
            rcut=6.0,
            rcut_smth=5.5,
            sel=[32],
            neuron=[25, 50, 100],
        ),
        fitting_net=DeepMDFittingNetSpec(neuron=[240, 240, 240]),
        training={"numb_steps": 1000, "save_freq": 100, "disp_freq": 100},
        learning_rate={"type": "exp", "start_lr": 0.001, "decay_steps": 1000},
        loss={"type": "ener", "start_pref_e": 0.02, "start_pref_f": 1000.0},
        mode_inputs=mode_inputs or DeepMDModeInputSpec(),
    )


@pytest.mark.asyncio
async def test_deepmd_executor_requires_runtime_storage_path(test_runs_dir: Path) -> None:
    spec = _build_spec(test_runs_dir)
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=None))

    with pytest.raises(RuntimeError, match="runtime.storage_path"):
        executor.execute_plan(plan)


@pytest.mark.asyncio
async def test_deepmd_executor_marks_binary_missing_as_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path)
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr("metaharness_ext.deepmd.executor.shutil.which", lambda binary: None)

    artifact = executor.execute_plan(plan)

    assert artifact.status == "unavailable"
    assert artifact.result_summary["fallback_reason"] == "binary_not_found"
    assert Path(artifact.stderr_path).read_text() == "DeepMD binary not found: dp"


@pytest.mark.asyncio
async def test_deepmd_executor_marks_binary_missing_as_unavailable_without_dataset_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path, execution_mode="test")
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    plan.dataset_paths = []
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr("metaharness_ext.deepmd.executor.shutil.which", lambda binary: None)

    artifact = executor.execute_plan(plan)

    assert artifact.status == "unavailable"
    assert artifact.command == ["dp", "test"]
    assert artifact.result_summary["fallback_reason"] == "binary_not_found"


@pytest.mark.asyncio
async def test_deepmd_executor_rejects_unsafe_task_id(tmp_path: Path) -> None:
    spec = _build_spec(tmp_path, task_id="../unsafe/task")
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    with pytest.raises(ValueError, match="Invalid task_id"):
        executor.execute_plan(plan)


@pytest.mark.asyncio
async def test_deepmd_executor_writes_input_json_and_collects_train_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path, execution_mode="train")
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: int | None,
    ):
        calls.append({"command": command, "cwd": cwd, "timeout": timeout})
        (cwd / "lcurve.out").write_text("# step rmse_e rmse_f\n100 1.25e-03 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return _FakeCompletedProcess(returncode=0, stdout="training ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    run_dir = tmp_path / ".runs" / "deepmd" / spec.task_id / plan.run_id
    assert (run_dir / "input.json").exists()
    assert calls[0]["command"] == ["/usr/bin/dp", "train", "input.json"]
    assert calls[0]["cwd"] == run_dir
    assert artifact.status == "completed"
    assert str(run_dir / "checkpoint") in artifact.checkpoint_files
    assert artifact.summary.learning_curve_path == str(run_dir / "lcurve.out")
    assert artifact.summary.last_step == 100
    assert artifact.summary.rmse_e_trn == pytest.approx(1.25e-03)
    assert artifact.summary.rmse_f_trn == pytest.approx(2.50e-02)


@pytest.mark.asyncio
async def test_deepmd_executor_collects_freeze_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path, execution_mode="freeze")
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: int | None,
    ):
        (cwd / "frozen_model.pb").write_text("model")
        return _FakeCompletedProcess(returncode=0, stdout="freeze ok", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.status == "completed"
    assert any(path.endswith("frozen_model.pb") for path in artifact.model_files)
    assert artifact.command == ["/usr/bin/dp", "freeze", "-o", "frozen_model.pb"]
    assert report.status == "frozen"


@pytest.mark.asyncio
async def test_deepmd_executor_collects_test_metrics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path, execution_mode="test")
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: int | None,
    ):
        (cwd / "frozen_model.pb").write_text("model")
        return _FakeCompletedProcess(
            returncode=0, stdout="rmse_e = 1.2e-03\nrmse_f = 3.4e-02\n", stderr=""
        )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.command[0] == "/usr/bin/dp"
    assert artifact.command[1:] == [
        "test",
        "-m",
        "frozen_model.pb",
        "-s",
        spec.dataset.train_systems[0],
        "-n",
        "10",
    ]
    assert artifact.summary.test_metrics["rmse_e"] == pytest.approx(1.2e-03)
    assert artifact.summary.test_metrics["rmse_f"] == pytest.approx(3.4e-02)
    assert report.passed is True
    assert report.status == "tested"


@pytest.mark.asyncio
async def test_deepmd_executor_rejects_test_mode_without_dataset_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path, execution_mode="test")
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    plan.dataset_paths = []
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    with pytest.raises(ValueError, match="test mode requires at least one dataset path"):
        executor.execute_plan(plan)


@pytest.mark.asyncio
async def test_deepmd_executor_collects_compress_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(
        tmp_path,
        execution_mode="compress",
        mode_inputs=DeepMDModeInputSpec(model_path="frozen_model.pb"),
    )
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: int | None,
    ):
        (cwd / "compressed_model.pb").write_text("compressed-model")
        return _FakeCompletedProcess(
            returncode=0,
            stdout="Compression finished. Saved compressed graph to compressed_model.pb\n",
            stderr="",
        )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.command == [
        "/usr/bin/dp",
        "compress",
        "-i",
        "frozen_model.pb",
        "-o",
        "compressed_model.pb",
    ]
    assert any(path.endswith("compressed_model.pb") for path in artifact.model_files)
    assert (
        artifact.summary.compressed_model_path
        == str(tmp_path / ".runs" / "deepmd" / spec.task_id / plan.run_id / "compressed_model.pb")
        or artifact.summary.compressed_model_path == "compressed_model.pb"
    )
    assert report.passed is True
    assert report.status == "compressed"
    assert "compressed_model_path" in report.summary_metrics


@pytest.mark.asyncio
async def test_deepmd_executor_collects_model_devi_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    system_dir = tmp_path / "devi_system"
    system_dir.mkdir()
    spec = _build_spec(
        tmp_path,
        execution_mode="model_devi",
        mode_inputs=DeepMDModeInputSpec(model_path="frozen_model.pb", system_path=str(system_dir)),
    )
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: int | None,
    ):
        (cwd / "model_devi.out").write_text(
            "# step max_devi_f avg_devi_f\n0 2.31e-01 1.05e-01\nrest_accurate.000.out\n"
        )
        return _FakeCompletedProcess(
            returncode=0,
            stdout="max_devi_f = 2.31e-01\navg_devi_f = 1.05e-01\ncandidate.shuffled.000.out\n",
            stderr="",
        )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.command == [
        "/usr/bin/dp",
        "model_devi",
        "-m",
        "frozen_model.pb",
        "-s",
        str(system_dir),
    ]
    assert any(path.endswith("model_devi.out") for path in artifact.diagnostic_files)
    assert artifact.summary.model_devi_metrics["max_devi_f"] == pytest.approx(2.31e-01)
    assert artifact.summary.model_devi_metrics["avg_devi_f"] == pytest.approx(1.05e-01)
    assert any("candidate" in message.lower() for message in artifact.summary.messages)
    assert any("accurate" in message.lower() for message in artifact.summary.messages)
    assert report.passed is True
    assert report.status == "model_devi_computed"
    assert report.summary_metrics["max_devi_f"] == pytest.approx(2.31e-01)
    assert report.summary_metrics["avg_devi_f"] == pytest.approx(1.05e-01)


@pytest.mark.asyncio
async def test_deepmd_executor_collects_neighbor_stat_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    system_dir = tmp_path / "neighbor_system"
    system_dir.mkdir()
    spec = _build_spec(
        tmp_path,
        execution_mode="neighbor_stat",
        mode_inputs=DeepMDModeInputSpec(system_path=str(system_dir)),
    )
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        text: bool,
        capture_output: bool,
        check: bool,
        timeout: int | None,
    ):
        (cwd / "neighbor_stat.out").write_text(
            "min_nbor_dist = 1.24\nmax_nbor_size = 87\nsel = [24, 48]\n"
        )
        return _FakeCompletedProcess(
            returncode=0,
            stdout="min_nbor_dist = 1.24\nmax_nbor_size = 87\nsel = [24, 48]\n",
            stderr="",
        )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.command == ["/usr/bin/dp", "neighbor_stat", "-s", str(system_dir)]
    assert any(path.endswith("neighbor_stat.out") for path in artifact.diagnostic_files)
    assert artifact.summary.neighbor_stat_metrics["min_nbor_dist"] == pytest.approx(1.24)
    assert artifact.summary.neighbor_stat_metrics["max_nbor_size"] == pytest.approx(87.0)
    assert any("suggested sel" in message.lower() for message in artifact.summary.messages)
    assert report.passed is True
    assert report.status == "neighbor_stat_computed"
    assert report.summary_metrics["min_nbor_dist"] == pytest.approx(1.24)
    assert report.summary_metrics["max_nbor_size"] == pytest.approx(87.0)


@pytest.mark.asyncio
async def test_deepmd_validator_fails_phase_two_without_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(
        tmp_path,
        execution_mode="compress",
        mode_inputs=DeepMDModeInputSpec(model_path="frozen_model.pb"),
    )
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )
    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=0, stdout="", stderr=""
        ),
    )

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.status == "completed"
    assert report.passed is False
    assert report.status == "validation_failed"


def test_deepmd_validator_does_not_treat_frozen_model_as_compress_success() -> None:
    artifact = DeepMDRunArtifact(
        task_id="deepmd-task",
        run_id="run-1",
        execution_mode="compress",
        command=["dp", "compress", "-i", "frozen_model.pb", "-o", "compressed_model.pb"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        checkpoint_files=[],
        model_files=["/tmp/run/frozen_model.pb"],
        diagnostic_files=[],
        summary=DeepMDDiagnosticSummary(),
        status="completed",
        result_summary={"exit_code": 0},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"


def test_deepmd_validator_requires_parsed_phase_two_diagnostics() -> None:
    artifact = DeepMDRunArtifact(
        task_id="deepmd-task",
        run_id="run-2",
        execution_mode="model_devi",
        command=["dp", "model_devi"],
        return_code=0,
        stdout_path="/tmp/stdout.log",
        stderr_path="/tmp/stderr.log",
        working_directory="/tmp/run",
        checkpoint_files=[],
        model_files=[],
        diagnostic_files=[],
        summary=DeepMDDiagnosticSummary(model_devi_metrics={"max_devi_f": 0.123}),
        status="completed",
        result_summary={"exit_code": "0"},
    )

    report = DeepMDValidatorComponent().validate_run(artifact)

    assert report.passed is True
    assert report.status == "model_devi_computed"
    assert report.summary_metrics["max_devi_f"] == pytest.approx(0.123)


@pytest.mark.asyncio
async def test_deepmd_executor_marks_timeout_as_failed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_spec(tmp_path, execution_mode="train")
    spec.executable.timeout_seconds = 12
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(
            command, timeout, output="partial-out", stderr="partial-err"
        )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.status == "failed"
    assert artifact.result_summary["fallback_reason"] == "command_timeout"
    assert "timed out after 12 seconds" in Path(artifact.stderr_path).read_text()
    assert report.status == "runtime_failed"
