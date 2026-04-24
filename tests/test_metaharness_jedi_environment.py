from pathlib import Path

from metaharness_ext.jedi.contracts import (
    JediExecutableSpec,
    JediForecastSpec,
    JediHofXSpec,
    JediLocalEnsembleDASpec,
    JediVariationalSpec,
)
from metaharness_ext.jedi.environment import JediEnvironmentProbeComponent


def test_jedi_environment_reports_missing_binary(tmp_path: Path) -> None:
    spec = JediVariationalSpec(
        task_id="task-1",
        executable=JediExecutableSpec(binary_name="qg4DVar.x", execution_mode="validate_only"),
    )
    probe = JediEnvironmentProbeComponent()

    report = probe.probe(spec)

    assert report.binary_available is False
    assert report.data_prerequisites_ready is True
    assert report.smoke_candidate == "variational"
    assert any("JEDI binary not found" in message for message in report.messages)


def test_jedi_environment_local_ensemble_missing_binary_keeps_family_candidate(
    tmp_path: Path,
) -> None:
    spec = JediLocalEnsembleDASpec(
        task_id="task-letkf-missing",
        executable=JediExecutableSpec(binary_name="qgLETKF.x", execution_mode="real_run"),
        ensemble_paths=[str(tmp_path / "ens.000")],
    )
    probe = JediEnvironmentProbeComponent()

    report = probe.probe(spec)

    assert report.binary_available is False
    assert report.smoke_candidate == "local_ensemble_da"


def test_jedi_environment_reports_missing_launcher(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "qg4DVar.x"
    binary.write_text("binary")
    spec = JediVariationalSpec(
        task_id="task-1",
        executable=JediExecutableSpec(
            binary_name=str(binary),
            launcher="mpiexec",
            execution_mode="validate_only",
        ),
    )
    probe = JediEnvironmentProbeComponent()

    def fake_which(name: str) -> str | None:
        if name == "mpiexec":
            return None
        if name == "ldd":
            return "/usr/bin/ldd"
        return None

    class _Result:
        returncode = 0
        stdout = ""

    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", fake_which)
    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run", lambda *args, **kwargs: _Result()
    )

    report = probe.probe(spec)

    assert report.binary_available is True
    assert report.launcher_available is False
    assert report.launcher_path is None
    assert any("Launcher not found" in message for message in report.messages)


def test_jedi_environment_reports_unresolved_libraries(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "qg4DVar.x"
    binary.write_text("binary")
    spec = JediVariationalSpec(
        task_id="task-1",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="validate_only"),
    )
    probe = JediEnvironmentProbeComponent()

    class _Result:
        returncode = 0
        stdout = "liboops.so => not found\n"

    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.shutil.which", lambda name: "/usr/bin/ldd"
    )
    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run", lambda *args, **kwargs: _Result()
    )

    report = probe.probe(spec)

    assert report.shared_libraries_resolved is False
    assert any("Unresolved library" in message for message in report.messages)


def test_jedi_environment_checks_family_required_paths(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "qgLETKF.x"
    binary.write_text("binary")
    ensemble_member = tmp_path / "ens.000"
    ensemble_member.write_text("member")
    missing_obs = tmp_path / "obs.odb"
    missing_background = tmp_path / "background.nc"
    spec = JediLocalEnsembleDASpec(
        task_id="task-ens",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="validate_only"),
        ensemble_paths=[str(ensemble_member)],
        background_path=str(missing_background),
        observation_paths=[str(missing_obs)],
    )
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

    assert report.required_paths_present is False
    assert report.data_paths_present is False
    assert str(missing_obs) in report.missing_required_paths
    assert str(missing_background) in report.missing_required_paths
    assert "ctest -R get_ or equivalent observation data preparation" in report.missing_prerequisites
    assert "ctest -R qg_get_data or equivalent QG data preparation" in report.missing_prerequisites
    assert report.data_prerequisites_ready is False
    assert any(str(missing_obs) in message for message in report.messages)
    assert any(str(missing_background) in message for message in report.messages)


def test_jedi_environment_direct_mode_does_not_require_launcher(
    tmp_path: Path, monkeypatch
) -> None:
    binary = tmp_path / "qgForecast.x"
    binary.write_text("binary")
    init = tmp_path / "init.nc"
    init.write_text("init")
    spec = JediForecastSpec(
        task_id="task-forecast",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="validate_only"),
        initial_condition_path=str(init),
    )
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

    assert report.launcher_available is True
    assert report.required_paths_present is True
    assert report.data_prerequisites_ready is True
    assert "model initial-condition data prepared" in report.environment_prerequisites
    assert "model initial-condition data prepared" in report.ready_prerequisites
    assert report.prerequisite_evidence["model initial-condition data prepared"] == [
        str(init.resolve())
    ]


def test_jedi_environment_checks_hofx_state_and_observations(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "qgHofX3D.x"
    binary.write_text("binary")
    state = tmp_path / "state.nc"
    state.write_text("state")
    obs = tmp_path / "obs.ioda"
    spec = JediHofXSpec(
        task_id="task-hofx",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="validate_only"),
        state_path=str(state),
        observation_paths=[str(obs)],
    )
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

    assert report.required_paths_present is False
    assert report.data_paths_present is False
    assert any(str(obs) in message for message in report.messages)


def test_jedi_environment_hofx_without_observation_paths_does_not_invent_obs_prerequisites(
    tmp_path: Path, monkeypatch
) -> None:
    binary = tmp_path / "qgHofX4D.x"
    binary.write_text("binary")
    state = tmp_path / "state.nc"
    state.write_text("state")
    spec = JediHofXSpec(
        task_id="task-hofx-no-obs",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="validate_only"),
        state_path=str(state),
    )
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
    assert report.data_paths_present is True
    assert report.data_prerequisites_ready is True
    assert report.environment_prerequisites == []
    assert report.missing_prerequisites == []
    assert report.smoke_candidate == "hofx"


def test_jedi_environment_detects_workspace_testinput_and_ready_prerequisites(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "jedi-workspace"
    workspace.mkdir()
    (workspace / "testinput").mkdir()
    binary = workspace / "qg4DVar.x"
    binary.write_text("binary")
    obs = workspace / "obs.ioda"
    obs.write_text("obs")
    background = workspace / "background.nc"
    background.write_text("bg")

    spec = JediVariationalSpec(
        task_id="task-workspace",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="real_run"),
        background_path=str(background),
        observation_paths=[str(obs)],
    )
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

    assert report.workspace_root == str(workspace)
    assert report.workspace_testinput_present is True
    assert "workspace testinput" in report.environment_prerequisites
    assert "workspace testinput" in report.ready_prerequisites
    assert "ctest -R get_ or equivalent observation data preparation" in report.ready_prerequisites
    assert "ctest -R qg_get_data or equivalent QG data preparation" in report.ready_prerequisites
    assert report.prerequisite_evidence["workspace testinput"] == [
        str((workspace / "testinput").resolve())
    ]
    assert report.prerequisite_evidence[
        "ctest -R get_ or equivalent observation data preparation"
    ] == [str(obs.resolve())]
    assert report.prerequisite_evidence[
        "ctest -R qg_get_data or equivalent QG data preparation"
    ] == [str(background.resolve())]
    assert report.missing_prerequisites == []
    assert report.data_prerequisites_ready is True
    assert report.smoke_ready is True


def test_jedi_environment_marks_qg_data_prerequisite_missing_when_background_error_is_absent(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "jedi-workspace"
    workspace.mkdir()
    (workspace / "testinput").mkdir()
    binary = workspace / "qg4DVar.x"
    binary.write_text("binary")
    obs = workspace / "obs.ioda"
    obs.write_text("obs")
    background = workspace / "background.nc"
    background.write_text("bg")
    missing_background_error = workspace / "background_error.nc"

    spec = JediVariationalSpec(
        task_id="task-missing-qg-data",
        executable=JediExecutableSpec(binary_name=str(binary), execution_mode="real_run"),
        background_path=str(background),
        background_error_path=str(missing_background_error),
        observation_paths=[str(obs)],
    )
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

    assert "ctest -R get_ or equivalent observation data preparation" in report.ready_prerequisites
    assert "ctest -R qg_get_data or equivalent QG data preparation" in report.missing_prerequisites
    assert report.prerequisite_evidence[
        "ctest -R get_ or equivalent observation data preparation"
    ] == [str(obs.resolve())]
    assert report.data_prerequisites_ready is False
    assert report.smoke_ready is False
