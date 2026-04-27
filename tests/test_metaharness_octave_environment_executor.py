import os
import shutil
import subprocess
from pathlib import Path

import pytest

from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveExperimentSpec,
    OctaveOutputSpec,
    OctavePackageSpec,
    OctaveScriptSpec,
    OctaveToleranceSpec,
    OctaveWorkspaceSpec,
)
from metaharness_ext.octave.environment import OctaveEnvironmentProbeComponent
from metaharness_ext.octave.executor import OctaveExecutorComponent
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.validator import OctaveValidatorComponent


def _spec() -> OctaveExperimentSpec:
    return OctaveExperimentSpec(
        task_id="runtime-task",
        script=OctaveScriptSpec(mode="inline", inline_source="result = 4;"),
        packages=[OctavePackageSpec(name="control")],
        expected_outputs=[
            OctaveOutputSpec(
                name="result",
                variable_name="result",
                tolerance=OctaveToleranceSpec(expected_value=4.0),
            )
        ],
    )


def test_octave_environment_probe_uses_mocked_binary(monkeypatch, tmp_path: Path) -> None:
    spec = _spec()
    monkeypatch.setattr(
        "metaharness_ext.octave.environment.shutil.which", lambda _: "/bin/octave-cli"
    )
    monkeypatch.setattr(
        "metaharness_ext.octave.environment.tempfile.gettempdir",
        lambda: str(tmp_path),
    )

    def fake_run(command, **kwargs):
        if command == ["/bin/octave-cli", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="GNU Octave 9.1.0\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="control | 4.0.0\n", stderr="")

    monkeypatch.setattr("metaharness_ext.octave.environment.subprocess.run", fake_run)

    report = OctaveEnvironmentProbeComponent().probe(spec)

    assert report.available is True
    assert report.binary_path == "/bin/octave-cli"
    assert report.version == "GNU Octave 9.1.0"
    assert report.packages[0].available is True
    assert report.missing_prerequisites == []


def test_octave_environment_probe_reports_missing_binary(monkeypatch, tmp_path: Path) -> None:
    spec = _spec()
    monkeypatch.setattr("metaharness_ext.octave.environment.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "metaharness_ext.octave.environment.tempfile.gettempdir",
        lambda: str(tmp_path),
    )

    report = OctaveEnvironmentProbeComponent().probe(spec)

    assert report.available is False
    assert report.status == "prerequisite_missing"
    assert report.missing_packages == ["control"]
    assert "Octave binary not found" in report.missing_prerequisites[0]
    assert report.blocks_promotion is True


def test_octave_executor_uses_mocked_subprocess_and_discovers_outputs(
    monkeypatch, tmp_path: Path
) -> None:
    plan = OctaveScriptCompilerComponent().compile(_spec())
    plan = plan.model_copy(update={"workspace_dir": str(tmp_path / "run")})
    executor = OctaveExecutorComponent()
    monkeypatch.setattr(executor, "_resolve_binary", lambda _: "/bin/octave-cli")

    def fake_run_command(command, *, plan, cwd):
        outputs = cwd / "outputs"
        outputs.mkdir(exist_ok=True)
        (outputs / "result.txt").write_text("# name: result\n# type: scalar\n4\n")
        (cwd / "mhe_status.txt").write_text("completed")
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="warning: benign\n")

    monkeypatch.setattr(executor, "_run_command", fake_run_command)

    artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert artifact.return_code == 0
    assert artifact.command[:2] == ["/bin/octave-cli", "--no-gui"]
    assert Path(artifact.wrapper_files[0]).read_text() == plan.wrapper_source
    assert Path(artifact.output_files[0]).name == "result.txt"
    assert artifact.warnings[0].severity == "suspicious"


def test_octave_executor_short_circuits_unavailable_environment(tmp_path: Path) -> None:
    plan = OctaveScriptCompilerComponent().compile(_spec())
    plan = plan.model_copy(update={"workspace_dir": str(tmp_path / "run")})
    environment = OctaveEnvironmentReport(
        task_id=plan.task_id,
        available=False,
        status="prerequisite_missing",
        workspace_writable=True,
        missing_prerequisites=["Octave binary not found"],
    )

    artifact = OctaveExecutorComponent().execute_plan(plan, environment)

    assert artifact.status == "unavailable"
    assert artifact.terminal_error_type == "environment_unavailable"
    assert artifact.return_code is None
    assert artifact.warnings[0].severity == "blocking"


@pytest.mark.octave
@pytest.mark.skipif(
    os.environ.get("MHE_RUN_REAL_OCTAVE") != "1",
    reason="set MHE_RUN_REAL_OCTAVE=1 to run real octave-cli smoke tests",
)
@pytest.mark.skipif(shutil.which("octave-cli") is None, reason="octave-cli is not installed")
def test_octave_cli_smoke_compiles_executes_and_validates(tmp_path: Path) -> None:
    spec = OctaveExperimentSpec(
        task_id="real-octave-smoke",
        script=OctaveScriptSpec(
            mode="inline",
            inline_source=(
                "warning('off', 'Octave:language-extension'); "
                "fid = fopen('outputs/result.txt', 'w'); fprintf(fid, '5\\n'); fclose(fid);"
            ),
        ),
        workspace=OctaveWorkspaceSpec(working_directory=str(tmp_path / "run")),
        expected_outputs=[
            OctaveOutputSpec(name="result-file", kind="text", file_name="result.txt")
        ],
    )
    environment = OctaveEnvironmentProbeComponent().probe(spec)
    assert environment.available, environment.missing_prerequisites

    plan = OctaveScriptCompilerComponent().compile(spec, environment)
    artifact = OctaveExecutorComponent().execute_plan(plan, environment)
    validation = OctaveValidatorComponent().validate_run(artifact, plan)

    assert artifact.status == "completed"
    assert artifact.return_code == 0
    assert Path(artifact.output_files[0]).read_text().strip() == "5"
    assert validation.passed
    assert validation.status.value == "executed"
