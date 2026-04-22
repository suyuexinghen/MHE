from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import (
    DeepMDDatasetSpec,
    DeepMDDescriptorSpec,
    DeepMDExecutableSpec,
    DeepMDFittingNetSpec,
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
    tmp_path: Path, *, task_id: str = "deepmd-task", execution_mode: str = "train"
) -> DeepMDTrainSpec:
    train_system = tmp_path / "train_system"
    train_system.mkdir()
    return DeepMDTrainSpec(
        task_id=task_id,
        executable=DeepMDExecutableSpec(execution_mode=execution_mode),
        dataset=DeepMDDatasetSpec(
            dataset_id=task_id,
            train_systems=[str(train_system)],
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
    )


@pytest.mark.asyncio
async def test_deepmd_executor_requires_runtime_storage_path(tmp_path: Path) -> None:
    spec = _build_spec(tmp_path)
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

    run_dir = tmp_path / "deepmd_runs" / spec.task_id / plan.run_id
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

    assert artifact.status == "completed"
    assert any(path.endswith("frozen_model.pb") for path in artifact.model_files)
    assert artifact.command == ["/usr/bin/dp", "freeze", "-o", "frozen_model.pb"]


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
