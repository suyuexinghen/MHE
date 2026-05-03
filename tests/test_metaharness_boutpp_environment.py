from __future__ import annotations

from metaharness_ext.boutpp.contracts import BoutPPProblemSpec
from metaharness_ext.boutpp.environment import BoutPPEnvironmentProbeComponent


def test_probe_reports_missing_root(monkeypatch):
    monkeypatch.delenv("BOUTPP_ROOT", raising=False)
    monkeypatch.delenv("BOUT_ROOT", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    probe = BoutPPEnvironmentProbeComponent()
    report = probe.probe(task_id="env")
    assert report.available is False
    assert any("BOUTPP_ROOT" in item or "BOUT_ROOT" in item for item in report.missing_prerequisites)


def test_probe_finds_absolute_executable_and_optional_reader(tmp_path, monkeypatch):
    root = tmp_path / "bout"
    root.mkdir()
    exe = root / "conduction"
    exe.write_text("#!/bin/sh\nexit 0\n")
    exe.chmod(0o755)
    monkeypatch.setenv("BOUTPP_ROOT", str(root))
    monkeypatch.setattr(
        "shutil.which",
        lambda name: str(root / name)
        if name in {"mpiexec", "cmake", "ncxx4-config", "bout-config"}
        else None,
    )
    probe = BoutPPEnvironmentProbeComponent()
    spec = BoutPPProblemSpec(task_id="env", executable=str(exe), mpi={"launcher_mode": "direct"})
    report = probe.probe(spec=spec)
    assert report.executable_path == str(exe.resolve())
    assert report.nc_config_path == str(root / "ncxx4-config")
    assert report.bout_config_path == str(root / "bout-config")
    assert report.available is True
    assert report.optional_python_readers["netCDF4"] in {True, False}
    assert report.optional_python_readers["boutpp"] in {True, False}
