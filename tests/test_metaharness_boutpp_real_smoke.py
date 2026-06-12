from __future__ import annotations

import os
from pathlib import Path

import pytest

from metaharness_ext.boutpp.real_smoke import (
    boutpp_real_smoke_case_catalog,
    build_boutpp_real_smoke_spec,
    preflight_boutpp_real_smoke_case,
    run_repeated_boutpp_real_smoke,
)


def test_boutpp_real_smoke_catalog_tracks_positive_and_candidate_cases() -> None:
    catalog = boutpp_real_smoke_case_catalog()

    assert set(catalog) == {
        "conduction-real",
        "boutpp-python-runexample",
        "staggered-grid-wrapper",
    }
    assert catalog["conduction-real"].default_enabled is True
    assert catalog["conduction-real"].output.require_dumps is True
    assert catalog["conduction-real"].output.require_restarts is True
    assert catalog["conduction-real"].validation.required_variables == ["T"]
    assert catalog["conduction-real"].validation.required_dimensions == {
        "t": 101,
        "x": 1,
        "y": 54,
        "z": 1,
    }
    assert catalog["conduction-real"].validation.required_variable_dimensions == {
        "T": ["t", "x", "y", "z"]
    }
    assert catalog["boutpp-python-runexample"].default_enabled is False
    assert catalog["staggered-grid-wrapper"].skip_reason is not None


def test_boutpp_real_smoke_spec_uses_absolute_local_build_paths(tmp_path: Path) -> None:
    build_root = tmp_path / "build"
    case = boutpp_real_smoke_case_catalog()["conduction-real"]

    spec = build_boutpp_real_smoke_spec(case, build_root, "mpirun")

    assert spec.task_id == "conduction-real"
    assert spec.executable == str((build_root / "examples/conduction/conduction").resolve())
    assert spec.source_case_dir == str((build_root / "examples/conduction").resolve())
    assert spec.top_level_options == {"MXG": 0}
    assert spec.mpi.launcher == "mpirun"
    assert spec.mpi.processes == 2


def test_boutpp_real_smoke_preflight_reports_missing_prerequisites(tmp_path: Path) -> None:
    case = boutpp_real_smoke_case_catalog()["conduction-real"]

    preflight = preflight_boutpp_real_smoke_case(case, tmp_path / "missing", "mpirun")

    assert preflight["promotion_ready"] is False
    assert "build_root" in preflight["missing_prerequisites"]
    assert "executable" in preflight["missing_prerequisites"]
    assert preflight["skip_reason"].startswith("Missing prerequisites")


def test_boutpp_real_smoke_preflight_requires_netcdf_for_domain_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    build_root = tmp_path / "build"
    source_data = build_root / "examples/conduction/data"
    executable = build_root / "examples/conduction/conduction"
    source_data.mkdir(parents=True)
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    (source_data / "BOUT.inp").write_text("[mesh]\nny = 100\n")
    monkeypatch.setattr("metaharness_ext.boutpp.real_smoke.netcdf4_reader_available", lambda: False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/mpirun")

    preflight = preflight_boutpp_real_smoke_case(
        boutpp_real_smoke_case_catalog()["conduction-real"],
        build_root,
        "mpirun",
    )

    assert preflight["promotion_ready"] is False
    assert preflight["missing_prerequisites"] == ["netcdf4_reader"]


def test_boutpp_repeated_smoke_writes_skipped_candidate_summary(tmp_path: Path) -> None:
    summary = run_repeated_boutpp_real_smoke(
        build_root=tmp_path / "missing-build",
        runs_root=tmp_path / "runs",
        case_ids=["conduction-real", "boutpp-python-runexample"],
        repeat_count=2,
        launcher="missing-mpirun",
    )

    assert summary["real_tools"] is True
    assert summary["repeat_count"] == 2
    assert summary["claim_boundary"].startswith("Local opt-in BOUT++ smoke only")
    assert [case["status"] for case in summary["case_summaries"]] == ["skipped", "skipped"]
    assert (tmp_path / "runs" / "boutpp_real_repeated_smoke_summary.json").exists()
    assert (tmp_path / "runs" / "conduction-real" / "preflight.json").exists()
    assert (tmp_path / "runs" / "boutpp-python-runexample" / "preflight.json").exists()


@pytest.mark.boutpp
def test_boutpp_real_repeated_conduction_smoke(tmp_path: Path) -> None:
    if os.environ.get("MHE_RUN_REAL_BOUTPP") != "1":
        pytest.skip("set MHE_RUN_REAL_BOUTPP=1 to run real BOUT++ smoke")
    build_root_value = os.environ.get("BOUTPP_ROOT")
    if not build_root_value:
        pytest.skip("set BOUTPP_ROOT to the local BOUT++ build root")

    repeat_count = int(os.environ.get("MHE_BOUTPP_REPEAT", "2"))
    summary = run_repeated_boutpp_real_smoke(
        build_root=Path(build_root_value),
        runs_root=tmp_path / "boutpp-real-repeated-smoke",
        case_ids=["conduction-real"],
        repeat_count=repeat_count,
    )

    case_summary = summary["case_summaries"][0]
    assert case_summary["status"] == "passed"
    assert case_summary["repeat_count"] == repeat_count
    assert case_summary["passed_count"] == repeat_count
    assert all(repeat["validation_passed"] for repeat in case_summary["repeats"])
    assert all(repeat["evidence_ref_count"] >= 5 for repeat in case_summary["repeats"])
