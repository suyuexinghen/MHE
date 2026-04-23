from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import JediExecutableSpec, JediLocalEnsembleDASpec
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.validator import JediValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.mark.asyncio
async def test_jedi_letkf_real_run_succeeds_with_minimum_ensemble_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ensemble_member_a = tmp_path / "ens.000"
    ensemble_member_a.write_text("member-a")
    ensemble_member_b = tmp_path / "ens.001"
    ensemble_member_b.write_text("member-b")
    background = tmp_path / "background.nc"
    background.write_text("background")
    observations = tmp_path / "obs.ioda"
    observations.write_text("observations")

    spec = JediLocalEnsembleDASpec(
        task_id="letkf-phase3",
        executable=JediExecutableSpec(
            binary_name="qgLETKF.x",
            execution_mode="real_run",
            launcher="mpiexec",
            process_count=8,
        ),
        ensemble_paths=[str(ensemble_member_a), str(ensemble_member_b)],
        background_path=str(background),
        observation_paths=[str(observations)],
        expected_diagnostics=["posterior.out", "observer.out"],
        scientific_check="ensemble_outputs_present",
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "letkf.out").write_text("ensemble output")
        (cwd / "posterior.out").write_text("posterior")
        (cwd / "ensemble_reference.json").write_text('{"baseline": "letkf-reference"}')
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert artifact.command == [
        "/usr/bin/mpiexec",
        "-n",
        "8",
        "/usr/bin/qgLETKF.x",
        "config.yaml",
    ]
    assert any(path.endswith("letkf.out") for path in artifact.output_files)
    assert any(path.endswith("posterior.out") for path in artifact.diagnostic_files)
    assert any(path.endswith("ensemble_reference.json") for path in artifact.reference_files)
    assert report.passed is True
    assert report.status == "executed"
    assert report.summary_metrics["primary_output"].endswith("letkf.out")
    assert report.summary_metrics["diagnostic_count"] == 1.0
    assert report.summary_metrics["reference_count"] == 1.0


@pytest.mark.asyncio
async def test_jedi_letkf_real_run_fails_without_ensemble_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ensemble_member = tmp_path / "ens.000"
    ensemble_member.write_text("member")
    observations = tmp_path / "obs.ioda"
    observations.write_text("observations")

    spec = JediLocalEnsembleDASpec(
        task_id="letkf-phase3-fail",
        executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="real_run"),
        ensemble_paths=[str(ensemble_member)],
        observation_paths=[str(observations)],
        expected_diagnostics=["posterior.out"],
        scientific_check="ensemble_outputs_present",
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "letkf.out").write_text("ensemble output")
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
