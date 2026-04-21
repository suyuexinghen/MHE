from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from metaharness_ext.nektar.contracts import (
    FilterOutputSummary,
    NektarRunArtifact,
)
from metaharness_ext.nektar.postprocess import PostprocessComponent
from metaharness_ext.nektar.types import NektarSolverFamily
from metaharness_ext.nektar.validator import NektarValidatorComponent


def _make_solver_artifact(
    tmp_path: Path,
    *,
    field_files: list[str] | None = None,
    checkpoint_files: list[str] | None = None,
    postprocess_plan: list[dict[str, object]] | None = None,
    result_summary: dict[str, object] | None = None,
) -> NektarRunArtifact:
    run_dir = tmp_path / "nektar_runs" / "task-pp"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "session.xml").write_text("<NEKTAR />")
    fld_files = field_files or []
    chk_files = checkpoint_files or []
    for name in fld_files:
        (run_dir / name).write_text("fld")
    for name in chk_files:
        (run_dir / name).write_text("chk")
    return NektarRunArtifact(
        run_id="run::task-pp",
        task_id="task-pp",
        solver_family=NektarSolverFamily.ADR,
        solver_binary="ADRSolver",
        session_files=[str(run_dir / "session.xml")],
        field_files=[str(run_dir / name) for name in fld_files],
        log_files=[],
        filter_output=FilterOutputSummary(checkpoint_files=[str(run_dir / name) for name in chk_files]),
        result_summary=result_summary or {"exit_code": 0, "timeout_seconds": 600},
        postprocess_plan=postprocess_plan if postprocess_plan is not None else [{"type": "fieldconvert", "output": "solution.vtu"}],
        status="completed",
    )


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_postprocess_runs_fieldconvert_for_field_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        output_path = Path(command[-1])
        output_path.write_text("vtu-data")
        return _FakeCompletedProcess(returncode=0, stdout="done", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    pp = result.result_summary["postprocess"]
    assert pp["status"] == "completed"
    assert pp["ran_fieldconvert"] is True
    step = pp["steps"][0]
    assert step["command"][0] == "/usr/bin/FieldConvert"
    assert step["exit_code"] == 0
    vtu_path = str(tmp_path / "nektar_runs" / "task-pp" / "solution.vtu")
    assert vtu_path in result.derived_files
    assert vtu_path in result.filter_output.fieldconvert_intermediates


def test_postprocess_prefers_fld_over_chk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        checkpoint_files=["session.chk"],
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    commands: list[list[str]] = []

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        commands.append(command)
        Path(command[-1]).write_text("vtu")
        return _FakeCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    PostprocessComponent().run_postprocess(artifact)

    assert "solution.fld" in commands[0][-2]


def test_postprocess_falls_back_to_latest_checkpoint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        checkpoint_files=["a.chk", "b.chk"],
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        Path(command[-1]).write_text("vtu")
        return _FakeCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    input_file = step["command"][-2]
    assert input_file.endswith("b.chk")


def test_postprocess_marks_missing_binary_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    monkeypatch.setattr("metaharness_ext.nektar.postprocess.shutil.which", lambda name: None)

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "unavailable"
    assert step["fallback_reason"] == "fieldconvert_binary_not_found"
    assert step["ran_fieldconvert"] is False


def test_postprocess_skips_when_no_input_exists(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(tmp_path)

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "skipped"
    assert step["fallback_reason"] == "postprocess_input_not_found"


def test_postprocess_marks_nonzero_exit_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.subprocess.run",
        lambda command, *, cwd, text, capture_output, check, timeout: _FakeCompletedProcess(
            returncode=3,
            stdout="",
            stderr="convert error",
        ),
    )

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "failed"
    assert step["exit_code"] == 3
    run_dir = tmp_path / "nektar_runs" / "task-pp"
    assert "convert error" in (run_dir / "fieldconvert.log").read_text()


def test_postprocess_marks_timeout_failed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        raise subprocess.TimeoutExpired(command, timeout, output="", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "failed"
    assert step["fallback_reason"] == "fieldconvert_timeout"


def test_postprocess_ignores_unknown_step_type(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[{"type": "magic_transform"}],
    )

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "skipped"
    assert step["fallback_reason"] == "unsupported_postprocess_type"


def test_postprocess_skips_invalid_step_without_output(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[{"type": "fieldconvert"}],
    )

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "skipped"
    assert step["fallback_reason"] == "invalid_postprocess_step"


def test_postprocess_skips_when_no_postprocess_plan(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(tmp_path, postprocess_plan=[])

    result = PostprocessComponent().run_postprocess(artifact)

    assert result.result_summary["postprocess"]["status"] == "skipped"
    assert result.result_summary["postprocess"]["fallback_reason"] == "no_postprocess_plan"


def test_postprocess_surfaces_error_norms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        Path(command[-1]).write_text("vtu")
        return _FakeCompletedProcess(
            returncode=0,
            stdout=(
                "Written file: \"out.dat\"\n"
                "L 2 error (variable u) : 1.11262e-05\n"
                "L inf error (variable u) : 1.28659e-05\n"
            ),
            stderr="",
        )

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    assert "l2_error_u" in result.filter_output.error_norms
    assert result.filter_output.error_norms["l2_error_u"] == pytest.approx(1.11262e-05)
    assert "linf_error_u" in result.filter_output.error_norms
    assert result.filter_output.error_norms["linf_error_u"] == pytest.approx(1.28659e-05)


def test_validator_notes_postprocess_completion(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={
            "exit_code": 0,
            "fallback_reason": None,
            "postprocess": {"status": "completed"},
        },
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert any("completed successfully" in m for m in report.messages)


def test_validator_notes_postprocess_failure(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={
            "exit_code": 0,
            "fallback_reason": None,
            "postprocess": {"status": "failed", "fallback_reason": "fieldconvert_timeout"},
        },
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert any("failed" in m and "fieldconvert_timeout" in m for m in report.messages)


def test_validator_mirrors_error_norms_to_metrics(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None},
    )
    artifact.filter_output.error_norms = {"l2_error_u": 0.000123}

    report = NektarValidatorComponent().validate_run(artifact)

    assert "l2_error_u" in report.metrics
    assert report.metrics["l2_error_u"] == pytest.approx(0.000123)


def test_validator_error_vs_reference_passes_when_l2_below_tolerance(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None, "error_tolerance": 1e-3},
    )
    artifact.filter_output.error_norms = {"l2_error_u": 1e-4}

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.error_vs_reference is True
    assert report.passed is True
    assert any("within tolerance" in m for m in report.messages)


def test_validator_error_vs_reference_fails_when_l2_above_tolerance(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None, "error_tolerance": 1e-4},
    )
    artifact.filter_output.error_norms = {"l2_error_u": 5e-4}

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.error_vs_reference is False
    assert report.passed is False
    assert any("exceeds tolerance" in m for m in report.messages)


def test_validator_error_vs_reference_none_when_no_norms(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None},
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.error_vs_reference is None


def test_validator_passed_remains_true_when_no_norms_present(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None},
    )

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.error_vs_reference is None
    assert report.passed is True


def test_postprocess_extracts_error_norms_from_real_fieldconvert_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[{"type": "fieldconvert", "output": "out.vtu", "args": ["-e"]}],
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )
    real_output = (
        "Writing: \"/tmp/out.vtu\"\n"
        "Written file: /tmp/out.vtu\n"
        "L 2 error (variable x) : 6.45495\n"
        "L inf error (variable x) : 5\n"
        "L 2 error (variable y) : 2.21359\n"
        "L inf error (variable y) : 1\n"
        "L 2 error (variable u) : 1.54954\n"
        "L inf error (variable u) : 1\n"
    )
    commands: list[list[str]] = []

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        commands.append(command)
        Path(command[-1]).write_text("vtu")
        return _FakeCompletedProcess(returncode=0, stdout=real_output, stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    norms = result.filter_output.error_norms
    assert commands[0][1] == "-e"
    assert commands[0][-1].endswith("out.vtu")
    assert "l2_error_x" not in norms
    assert "linf_error_y" not in norms
    assert norms["l2_error_u"] == pytest.approx(1.54954)
    assert norms["linf_error_u"] == pytest.approx(1.0)
    assert len(norms) == 2


def test_postprocess_skips_error_evaluation_without_session_file(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[{"type": "fieldconvert", "output": "out.vtu", "args": ["-e"]}],
    )
    artifact.session_files = []

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "skipped"
    assert step["fallback_reason"] == "fieldconvert_session_not_found"


def test_postprocess_extracts_error_norms_from_solver_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )
    solver_style_output = (
        "Writing: \"Helmholtz2D.fld\" (0.000166556s, XML)\n"
        "-------------------------------------------\n"
        "Total Computation Time = 0.00107107s\n"
        "-------------------------------------------\n"
        "L 2 error (variable u) : 1.58061e-05\n"
        "L inf error (variable u) : 1.80329e-05\n"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        Path(command[-1]).write_text("vtu")
        return _FakeCompletedProcess(returncode=0, stdout="", stderr=solver_style_output)

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    norms = result.filter_output.error_norms
    assert norms["l2_error_u"] == pytest.approx(1.58061e-05)
    assert norms["linf_error_u"] == pytest.approx(1.80329e-05)
    assert len(norms) == 2


def test_validator_uses_default_tolerance_when_not_specified(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None},
    )
    artifact.filter_output.error_norms = {"l2_error_u": 5e-4}

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.error_vs_reference is True
    assert report.passed is True


def test_validator_ignores_coordinate_variables_in_error_check(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None, "error_tolerance": 1e-3},
    )
    artifact.filter_output.error_norms = {
        "l2_error_u": 1e-6,
    }

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.error_vs_reference is True
    assert report.passed is True


def test_postprocess_runs_fieldconvert_with_vorticity_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[{"type": "fieldconvert", "output": "vorticity.fld", "module": "vorticity"}],
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    commands: list[list[str]] = []

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        commands.append(command)
        Path(command[-1]).write_text("fld")
        return _FakeCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "completed"
    assert step["ran_fieldconvert"] is True
    cmd = commands[0]
    assert cmd[1] == "-m"
    assert cmd[2] == "vorticity"


def test_postprocess_runs_fieldconvert_with_extract_boundary_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[{"type": "fieldconvert", "output": "boundary_b0.dat", "module": "extract:bnd=0"}],
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    commands: list[list[str]] = []

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        commands.append(command)
        Path(command[-1]).write_text("dat")
        return _FakeCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    step = result.result_summary["postprocess"]["steps"][0]
    assert step["status"] == "completed"
    cmd = commands[0]
    assert cmd[1] == "-m"
    assert cmd[2] == "extract:bnd=0"


def test_postprocess_handles_multi_step_plan_with_modules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        postprocess_plan=[
            {"type": "fieldconvert", "output": "solution.vtu"},
            {"type": "fieldconvert", "output": "vorticity.fld", "module": "vorticity"},
        ],
    )
    monkeypatch.setattr(
        "metaharness_ext.nektar.postprocess.shutil.which",
        lambda name: "/usr/bin/FieldConvert",
    )

    commands: list[list[str]] = []

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        commands.append(command)
        Path(command[-1]).write_text("data")
        return _FakeCompletedProcess(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("metaharness_ext.nektar.postprocess.subprocess.run", fake_run)

    result = PostprocessComponent().run_postprocess(artifact)

    pp = result.result_summary["postprocess"]
    assert pp["status"] == "completed"
    assert pp["ran_fieldconvert"] is True
    assert len(pp["steps"]) == 2

    cmd1, cmd2 = commands
    assert "-m" not in cmd1
    assert cmd2[1] == "-m"
    assert cmd2[2] == "vorticity"


def test_postprocess_extracts_incns_mapping_convergence_metrics(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    artifact.solver_family = NektarSolverFamily.INCNS
    run_dir = Path(artifact.session_files[0]).parent
    (run_dir / "solver.log").write_text(
        " Pressure system (mapping) converged in 7 iterations with error = 1.25e-09\n"
        " Velocity system (mapping) converged in 4 iterations with error = 3.5e-07\n"
    )
    artifact.log_files = [str(run_dir / "solver.log")]

    result = PostprocessComponent().run_postprocess(artifact)

    metrics = result.filter_output.metrics
    assert metrics["incns_pressure_iterations"] == pytest.approx(7.0)
    assert metrics["incns_pressure_error"] == pytest.approx(1.25e-09)
    assert metrics["incns_velocity_iterations"] == pytest.approx(4.0)
    assert metrics["incns_velocity_error"] == pytest.approx(3.5e-07)



def test_postprocess_extracts_incns_newton_norm_metrics(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(tmp_path, field_files=["solution.fld"])
    artifact.solver_family = NektarSolverFamily.INCNS
    run_dir = Path(artifact.session_files[0]).parent
    (run_dir / "solver.stdout.log").write_text(
        "L2Norm[0] = 1.1e-02\n"
        "L2Norm[1] = 9.5e-03\n"
        "InfNorm[0] = 2.0e-02\n"
        "We have done 5 iteration(s) in 0.1 minute(s).\n"
    )
    artifact.log_files = [str(run_dir / "solver.stdout.log")]

    result = PostprocessComponent().run_postprocess(artifact)

    metrics = result.filter_output.metrics
    assert metrics["incns_l2norm_0"] == pytest.approx(1.1e-02)
    assert metrics["incns_l2norm_1"] == pytest.approx(9.5e-03)
    assert metrics["incns_infnorm_0"] == pytest.approx(2.0e-02)
    assert metrics["incns_newton_iterations"] == pytest.approx(5.0)



def test_validator_surfaces_incns_convergence_metrics(tmp_path: Path) -> None:
    artifact = _make_solver_artifact(
        tmp_path,
        field_files=["solution.fld"],
        result_summary={"exit_code": 0, "fallback_reason": None},
    )
    artifact.solver_family = NektarSolverFamily.INCNS
    artifact.filter_output.metrics = {
        "incns_velocity_iterations": 4.0,
        "incns_pressure_iterations": 7.0,
        "incns_newton_iterations": 5.0,
    }

    report = NektarValidatorComponent().validate_run(artifact)

    assert report.metrics["incns_velocity_iterations"] == pytest.approx(4.0)
    assert report.metrics["incns_pressure_iterations"] == pytest.approx(7.0)
    assert report.metrics["incns_newton_iterations"] == pytest.approx(5.0)
    assert any("velocity system convergence" in m.lower() for m in report.messages)
    assert any("pressure system convergence" in m.lower() for m in report.messages)
    assert any("newton iteration metrics" in m.lower() for m in report.messages)
