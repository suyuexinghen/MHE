from __future__ import annotations

from pathlib import Path

import pytest

from metaharness_ext.nektar.analyzers import (
    parse_filter_outputs,
    parse_solver_log,
    summarize_reference_error,
)


def test_parse_solver_log_returns_missing_state_for_absent_file(tmp_path: Path) -> None:
    summary = parse_solver_log(tmp_path / "missing.log")

    assert summary.exists is False
    assert summary.warning_count == 0
    assert summary.error_count == 0
    assert summary.incns_metrics == {}


def test_parse_solver_log_extracts_step_and_time_metrics(tmp_path: Path) -> None:
    log_path = tmp_path / "solver.log"
    log_path.write_text(
        "Steps: 10       Time: 0.1          CPU Time: 0.05s\n"
        "Steps: 50       Time: 0.5          CPU Time: 0.25s\n"
        "Total Computation Time = 0.256s\n"
        "L 2 error (variable u) : 5.9519e-06\n"
        "L inf error (variable u) : 4.15477e-06\n"
    )

    summary = parse_solver_log(log_path)

    assert summary.exists is True
    assert summary.total_steps == 50
    assert summary.final_time == pytest.approx(0.5)
    assert summary.cpu_time == pytest.approx(0.25)
    assert summary.wall_time == pytest.approx(0.256)
    assert summary.l2_error_keys == ["l2_error_u"]
    assert summary.linf_error_keys == ["linf_error_u"]


def test_parse_solver_log_extracts_warning_and_error_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "solver.log"
    log_path.write_text("Warning: CFL nearing threshold\nRuntime Error: solver diverged\n")

    summary = parse_solver_log(log_path)

    assert summary.warning_count == 1
    assert summary.error_count == 1
    assert summary.warnings == ["Warning: CFL nearing threshold"]
    assert summary.errors == ["Runtime Error: solver diverged"]


def test_parse_solver_log_ignores_scientific_error_norm_lines_as_runtime_errors(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / "solver.log"
    log_path.write_text("L 2 error (variable u) : 1.2e-05\nL inf error (variable u) : 2.4e-05\n")

    summary = parse_solver_log(log_path)

    assert summary.error_count == 0
    assert summary.errors == []
    assert summary.l2_error_keys == ["l2_error_u"]
    assert summary.linf_error_keys == ["linf_error_u"]


def test_parse_solver_log_extracts_incns_convergence_metrics(tmp_path: Path) -> None:
    log_path = tmp_path / "solver.log"
    log_path.write_text(
        "Pressure system (mapping) converged in 7 iterations with error = 1.25e-09\n"
        "Velocity system (mapping) converged in 4 iterations with error = 3.5e-07\n"
        "We have done 5 iteration(s) in 0.1 minute(s).\n"
        "L2Norm[0] = 1.1e-02\n"
        "InfNorm[0] = 2.0e-02\n"
    )

    summary = parse_solver_log(log_path)

    assert summary.incns_metrics["incns_pressure_iterations"] == pytest.approx(7.0)
    assert summary.incns_metrics["incns_pressure_error"] == pytest.approx(1.25e-09)
    assert summary.incns_metrics["incns_velocity_iterations"] == pytest.approx(4.0)
    assert summary.incns_metrics["incns_velocity_error"] == pytest.approx(3.5e-07)
    assert summary.incns_metrics["incns_newton_iterations"] == pytest.approx(5.0)
    assert summary.incns_metrics["incns_l2norm_0"] == pytest.approx(1.1e-02)
    assert summary.incns_metrics["incns_infnorm_0"] == pytest.approx(2.0e-02)


def test_parse_solver_log_detects_timeout_marker(tmp_path: Path) -> None:
    log_path = tmp_path / "solver.log"
    log_path.write_text("Solver timed out after 12.0 seconds.\n")

    summary = parse_solver_log(log_path)

    assert summary.has_timeout_marker is True


def test_parse_filter_outputs_summarizes_existing_and_missing_files(tmp_path: Path) -> None:
    existing = tmp_path / "solution.vtu"
    existing.write_text("mesh")
    missing = tmp_path / "missing.dat"

    summary = parse_filter_outputs([str(existing), str(missing)])

    assert summary.files == [str(existing), str(missing)]
    assert summary.existing_files == [str(existing)]
    assert summary.missing_files == [str(missing)]
    assert summary.nonempty_count == 1
    assert summary.has_vtu is True
    assert summary.has_dat is True


def test_parse_filter_outputs_detects_formats_and_sizes(tmp_path: Path) -> None:
    fld = tmp_path / "session.fld"
    fld.write_text("fld")
    pvtu = tmp_path / "solution.pvtu"
    pvtu.write_text("")
    chk = tmp_path / "session.chk"
    chk.write_text("chk")

    summary = parse_filter_outputs([str(fld), str(pvtu), str(chk)])

    assert summary.formats[str(fld)] == "fld"
    assert summary.formats[str(pvtu)] == "pvtu"
    assert summary.formats[str(chk)] == "chk"
    assert summary.file_sizes[str(fld)] == 3
    assert summary.file_sizes[str(pvtu)] == 0
    assert summary.file_sizes[str(chk)] == 3
    assert summary.has_fld is True
    assert summary.has_vtu is True
    assert summary.nonempty_count == 2


def test_parse_filter_outputs_handles_empty_input() -> None:
    summary = parse_filter_outputs()

    assert summary.files == []
    assert summary.existing_files == []
    assert summary.missing_files == []
    assert summary.formats == {}
    assert summary.file_sizes == {}
    assert summary.nonempty_count == 0


def test_summarize_reference_error_returns_no_reference_error_for_empty_metrics() -> None:
    summary = summarize_reference_error()

    assert summary.status == "no_reference_error"
    assert summary.max_l2 is None
    assert summary.messages == ["No reference error metrics were found."]


def test_summarize_reference_error_extracts_l2_and_linf_extrema() -> None:
    summary = summarize_reference_error(
        {
            "l2_error_u": 1.0e-04,
            "l2_error_v": 2.5e-04,
            "linf_error_u": 2.0e-04,
            "linf_error_v": 3.0e-04,
        }
    )

    assert summary.l2_keys == ["l2_error_u", "l2_error_v"]
    assert summary.linf_keys == ["linf_error_u", "linf_error_v"]
    assert summary.max_l2 == pytest.approx(2.5e-04)
    assert summary.max_linf == pytest.approx(3.0e-04)
    assert summary.primary_variable == "v"
    assert summary.primary_l2 == pytest.approx(2.5e-04)
    assert summary.status == "reference_error_present"


def test_summarize_reference_error_marks_within_tolerance_when_available() -> None:
    summary = summarize_reference_error(
        {
            "l2_error_u": 1.0e-04,
            "linf_error_u": 2.0e-04,
            "error_tolerance": 1.0e-03,
        }
    )

    assert summary.status == "reference_error_within_tolerance"
    assert any("within tolerance" in message for message in summary.messages)


def test_summarize_reference_error_marks_exceeds_tolerance_when_available() -> None:
    summary = summarize_reference_error(
        {
            "l2_error_u": 5.0e-03,
            "linf_error_u": 6.0e-03,
            "error_tolerance": 1.0e-03,
        }
    )

    assert summary.status == "reference_error_exceeds_tolerance"
    assert any("exceeds tolerance" in message for message in summary.messages)
