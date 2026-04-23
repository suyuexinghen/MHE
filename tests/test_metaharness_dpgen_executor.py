from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import (
    DeepMDExecutableSpec,
    DPGenMachineSpec,
    DPGenRunSpec,
)
from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_dpgen_spec(tmp_path: Path) -> DPGenRunSpec:
    source_dir = tmp_path / "source-inputs"
    source_dir.mkdir()
    (source_dir / "input.data").write_text("mock-data\n")
    return DPGenRunSpec(
        task_id="dpgen-task",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=".", python_path="python3"),
        workspace_files=[str(source_dir)],
        workspace_inline_files={"templates/run.sh": "#!/bin/sh\n"},
    )


@pytest.mark.asyncio
async def test_dpgen_executor_prepares_workspace_and_collects_iterations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_dpgen_spec(tmp_path)
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        iter_dir = cwd / "iter.000000"
        (iter_dir / "00.train").mkdir(parents=True)
        (iter_dir / "01.model_devi").mkdir()
        (iter_dir / "02.fp").mkdir()
        (cwd / "record.dpgen").write_text(
            "candidate_count = 2\naccurate_count = 1\nfailed_count = 0\n"
        )
        (iter_dir / "01.model_devi" / "stats.out").write_text(
            "candidate_count = 2\naccurate_count = 1\nfailed_count = 0\n"
        )
        return _FakeCompletedProcess(returncode=0, stdout="dpgen ok\n", stderr="")

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)
    run_dir = tmp_path / "deepmd_runs" / spec.task_id / plan.run_id

    assert artifact.command == ["/usr/bin/dpgen", "run", "param.json", "machine.json"]
    assert (run_dir / "param.json").exists()
    assert (run_dir / "machine.json").exists()
    assert (run_dir / "source-inputs" / "input.data").exists()
    assert (run_dir / "templates" / "run.sh").exists()
    assert artifact.summary.dpgen_collection is not None
    assert len(artifact.summary.dpgen_collection.iterations) == 1
    assert artifact.summary.dpgen_collection.candidate_count == 2
    assert report.passed is True
    assert report.status == "baseline_success"


@pytest.mark.asyncio
async def test_dpgen_executor_distinguishes_workspace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = DPGenRunSpec(
        task_id="dpgen-task",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_run"),
        param={"type_map": ["H", "O"]},
        machine=DPGenMachineSpec(local_root="."),
        workspace_files=[str(tmp_path / "missing-source")],
    )
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.result_summary["fallback_reason"] == "workspace_prepare_failed"
    assert report.status == "workspace_failed"


@pytest.mark.asyncio
async def test_dpgen_executor_distinguishes_run_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = _build_dpgen_spec(tmp_path)
    plan = DeepMDTrainConfigCompilerComponent().build_plan(spec)
    executor = DeepMDExecutorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )
    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=2, stdout="", stderr="dpgen failed"
        ),
    )

    artifact = executor.execute_plan(plan)
    report = DeepMDValidatorComponent().validate_run(artifact)

    assert artifact.status == "failed"
    assert artifact.return_code == 2
    assert report.status == "run_failed"
