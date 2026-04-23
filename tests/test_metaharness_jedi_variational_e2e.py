from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.contracts import JediExecutableSpec, JediVariationalSpec
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.validator import JediValidatorComponent


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.mark.asyncio
async def test_jedi_variational_real_run_requires_minimum_scientific_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    background_error = tmp_path / "background_error.nc"
    background_error.write_text("background-error")
    observations = tmp_path / "obs.ioda"
    observations.write_text("observations")

    spec = JediVariationalSpec(
        task_id="variational-phase2",
        executable=JediExecutableSpec(
            binary_name="qg4DVar.x",
            execution_mode="real_run",
            launcher="mpiexec",
            process_count=4,
        ),
        background_path=str(background),
        background_error_path=str(background_error),
        observation_paths=[str(observations)],
        expected_diagnostics=["departures.json"],
        scientific_check="rms_improves",
    )
    plan = JediConfigCompilerComponent().build_plan(spec)
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    def fake_resolve_binary(self, binary_name: str) -> str | None:
        return f"/usr/bin/{Path(binary_name).name}"

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        fake_resolve_binary,
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "departures.json").write_text('{"rms_observation_minus_analysis": 0.7, "rms_observation_minus_background": 1.2}')
        (cwd / "reference.json").write_text('{"baseline": "toy-reference"}')
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    report = validator.validate_run(artifact)

    assert artifact.command == [
        "/usr/bin/mpiexec",
        "-n",
        "4",
        "/usr/bin/qg4DVar.x",
        "config.yaml",
    ]
    assert any(path.endswith("analysis.out") for path in artifact.output_files)
    assert any(path.endswith("departures.json") for path in artifact.diagnostic_files)
    assert any(path.endswith("reference.json") for path in artifact.reference_files)
    assert report.passed is True
    assert report.status == "executed"
    assert report.summary_metrics["primary_output"].endswith("analysis.out")
    assert report.summary_metrics["rms_observation_minus_analysis"] == 0.7
    assert report.summary_metrics["rms_observation_minus_background"] == 1.2


@pytest.mark.asyncio
async def test_jedi_variational_real_run_fails_when_scientific_check_does_not_improve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    background = tmp_path / "background.nc"
    background.write_text("background")
    observations = tmp_path / "obs.ioda"
    observations.write_text("observations")

    spec = JediVariationalSpec(
        task_id="variational-phase2-fail",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="real_run"),
        background_path=str(background),
        observation_paths=[str(observations)],
        expected_diagnostics=["departures.json"],
        scientific_check="rms_improves",
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
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "departures.json").write_text('{"rms_observation_minus_analysis": 1.4, "rms_observation_minus_background": 1.1}')
        return _FakeCompletedProcess(returncode=0, stdout="run ok", stderr="")

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)

    report = validator.validate_run(artifact)

    assert report.passed is False
    assert report.status == "validation_failed"
