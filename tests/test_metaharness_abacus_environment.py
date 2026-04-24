from pathlib import Path

from metaharness_ext.abacus.contracts import (
    AbacusExecutableSpec,
    AbacusKPointSpec,
    AbacusMdSpec,
    AbacusNscfSpec,
    AbacusRelaxSpec,
    AbacusScfSpec,
    AbacusStructureSpec,
)
from metaharness_ext.abacus.environment import AbacusEnvironmentProbeComponent


def test_abacus_environment_reports_missing_binary() -> None:
    spec = AbacusScfSpec(
        task_id="task-1",
        executable=AbacusExecutableSpec(binary_name="nonexistent_abacus"),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
    )
    probe = AbacusEnvironmentProbeComponent()

    report = probe.probe(spec)

    assert report.abacus_available is False
    assert any("ABACUS binary not found" in message for message in report.messages)


def test_abacus_environment_checks_nscf_required_paths(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "abacus"
    binary.write_text("binary")
    charge = tmp_path / "charge.cube"
    charge.write_text("density")
    missing_restart = tmp_path / "restart.dat"
    spec = AbacusNscfSpec(
        task_id="task-nscf",
        executable=AbacusExecutableSpec(binary_name=str(binary)),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        kpoints=AbacusKPointSpec(content="K_POINTS\n1\n0.0 0.0 0.0 1\n"),
        charge_density_path=str(charge),
        restart_file_path=str(missing_restart),
    )
    probe = AbacusEnvironmentProbeComponent()

    monkeypatch.setattr("metaharness_ext.abacus.environment.shutil.which", lambda name: None)
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: "cpu build")
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")

    report = probe.probe(spec)

    assert report.abacus_available is True
    assert report.required_paths_present is False
    assert report.required_path_groups.charge_density_path == str(charge)
    assert report.required_path_groups.restart_inputs == [str(missing_restart)]
    assert report.missing_path_groups.restart_inputs == [str(missing_restart)]
    assert any(str(missing_restart) in message for message in report.messages)


def test_abacus_environment_checks_relax_restart_path(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "abacus"
    binary.write_text("binary")
    missing_restart = tmp_path / "relax.restart"
    spec = AbacusRelaxSpec(
        task_id="task-relax",
        executable=AbacusExecutableSpec(binary_name=str(binary)),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        relax_controls={"restart_file_path": str(missing_restart)},
    )
    probe = AbacusEnvironmentProbeComponent()

    monkeypatch.setattr("metaharness_ext.abacus.environment.shutil.which", lambda name: None)
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: "cpu build")
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")

    report = probe.probe(spec)

    assert report.abacus_available is True
    assert report.required_paths_present is False
    assert report.required_path_groups.restart_inputs == [str(missing_restart)]
    assert report.missing_path_groups.restart_inputs == [str(missing_restart)]
    assert any(str(missing_restart) in message for message in report.messages)


def test_abacus_environment_accepts_md_dp_with_deepmd_support(tmp_path: Path, monkeypatch) -> None:
    binary = tmp_path / "abacus"
    binary.write_text("binary")
    pot = tmp_path / "model.pb"
    pot.write_text("model")
    spec = AbacusMdSpec(
        task_id="task-md-dp",
        executable=AbacusExecutableSpec(binary_name=str(binary)),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file=str(pot),
    )
    probe = AbacusEnvironmentProbeComponent()

    monkeypatch.setattr("metaharness_ext.abacus.environment.shutil.which", lambda name: None)
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: "DeepMD enabled build")
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")

    report = probe.probe(spec)

    assert report.deeppmd_probe_supported is True
    assert report.deeppmd_probe_succeeded is True
    assert report.deeppmd_support_detected is True
    assert report.required_paths_present is True
    assert report.missing_prerequisites == []


def test_abacus_environment_blocks_md_dp_without_deepmd_support(
    tmp_path: Path, monkeypatch
) -> None:
    binary = tmp_path / "abacus"
    binary.write_text("binary")
    pot = tmp_path / "model.pb"
    pot.write_text("model")
    spec = AbacusMdSpec(
        task_id="task-md-dp",
        executable=AbacusExecutableSpec(binary_name=str(binary)),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file=str(pot),
    )
    probe = AbacusEnvironmentProbeComponent()

    monkeypatch.setattr("metaharness_ext.abacus.environment.shutil.which", lambda name: None)
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: "cpu build")
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")

    report = probe.probe(spec)

    assert report.deeppmd_support_detected is False
    assert report.missing_prerequisites == ["deeppmd_support"]


def test_abacus_environment_blocks_md_dp_when_deepmd_support_unknown(
    tmp_path: Path, monkeypatch
) -> None:
    binary = tmp_path / "abacus"
    binary.write_text("binary")
    pot = tmp_path / "model.pb"
    pot.write_text("model")
    spec = AbacusMdSpec(
        task_id="task-md-dp",
        executable=AbacusExecutableSpec(binary_name=str(binary)),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file=str(pot),
    )
    probe = AbacusEnvironmentProbeComponent()

    monkeypatch.setattr("metaharness_ext.abacus.environment.shutil.which", lambda name: None)
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: None)
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")

    report = probe.probe(spec)

    assert report.deeppmd_probe_supported is True
    assert report.deeppmd_probe_succeeded is False
    assert report.deeppmd_support_detected is None
    assert report.missing_prerequisites == ["deeppmd_support"]


def test_abacus_environment_reports_missing_md_dp_pot_file_path(
    tmp_path: Path, monkeypatch
) -> None:
    binary = tmp_path / "abacus"
    binary.write_text("binary")
    missing_pot = tmp_path / "missing.pb"
    spec = AbacusMdSpec(
        task_id="task-md-dp",
        executable=AbacusExecutableSpec(binary_name=str(binary)),
        structure=AbacusStructureSpec(content="ATOMIC_SPECIES\nSi 28.0 Si.upf\n"),
        esolver_type="dp",
        pot_file=str(missing_pot),
    )
    probe = AbacusEnvironmentProbeComponent()

    monkeypatch.setattr("metaharness_ext.abacus.environment.shutil.which", lambda name: None)
    monkeypatch.setattr(probe, "_probe_version", lambda binary_path: "abacus 1.0")
    monkeypatch.setattr(probe, "_probe_info", lambda binary_path: "DeepMD enabled build")
    monkeypatch.setattr(probe, "_probe_check_input", lambda binary_path: "ok")

    report = probe.probe(spec)

    assert report.required_paths_present is False
    assert report.required_path_groups.pot_file == str(missing_pot)
    assert report.missing_path_groups.pot_file == str(missing_pot)
    assert str(missing_pot) in report.missing_required_paths
