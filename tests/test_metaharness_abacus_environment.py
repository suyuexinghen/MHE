from pathlib import Path

from metaharness_ext.abacus.contracts import (
    AbacusExecutableSpec,
    AbacusKPointSpec,
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
    assert any(str(missing_restart) in message for message in report.messages)
