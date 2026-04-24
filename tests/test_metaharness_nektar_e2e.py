from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.contracts import (
    ConvergenceStudySpec,
    FilterOutputSummary,
    NektarMutationAxis,
    NektarProblemSpec,
    NektarRunArtifact,
)
from metaharness_ext.nektar.convergence import ConvergenceStudyComponent
from metaharness_ext.nektar.postprocess import PostprocessComponent
from metaharness_ext.nektar.types import NektarSolverFamily
from metaharness_ext.nektar.validator import NektarValidatorComponent

ADR_ROOT = Path("/home/linden/code/work/Solvers/Nektar/nektar/solvers/ADRSolver/Tests")
INCNS_ROOT = Path(
    "/home/linden/code/work/Solvers/Nektar/nektar/solvers/IncNavierStokesSolver/Tests"
)

HELMHOLTZ_1D = ADR_ROOT / "Helmholtz1D_8modes.xml"
HELMHOLTZ_2D = ADR_ROOT / "Helmholtz2D_DirectFull.xml"
TAYLOR_VORTEX = INCNS_ROOT / "TaylorVor_dt1.xml"

_COORDINATE_VARIABLES = frozenset({"x", "y", "z"})


@pytest.fixture(scope="session")
def nektar_examples_available() -> None:
    required = [HELMHOLTZ_1D, HELMHOLTZ_2D]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        pytest.skip(f"Missing Nektar test cases: {', '.join(missing)}")


@pytest.fixture(scope="session")
def incns_examples_available() -> None:
    if not shutil.which("IncNavierStokesSolver"):
        pytest.skip("IncNavierStokesSolver not available")
    if not TAYLOR_VORTEX.exists():
        pytest.skip(f"Missing IncNS test case: {TAYLOR_VORTEX}")


def _copy_case(tmp_path: Path, task_id: str, source: Path) -> Path:
    run_dir = tmp_path / "nektar_runs" / task_id
    run_dir.mkdir(parents=True, exist_ok=True)
    session_path = run_dir / "session.xml"
    session_path.write_text(source.read_text())
    return session_path


def _copy_case_with_nummodes(tmp_path: Path, task_id: str, source: Path, num_modes: int) -> Path:
    session_path = _copy_case(tmp_path, task_id, source)
    text = session_path.read_text()
    updated = re.sub(r'NUMMODES="\d+"', f'NUMMODES="{num_modes}"', text)
    session_path.write_text(updated)
    return session_path


def _extract_error_norms(stdout_text: str, stderr_text: str) -> dict[str, float]:
    norms: dict[str, float] = {}
    combined = f"{stdout_text}\n{stderr_text}"
    for match in re.finditer(
        r"L\s*(2|inf)\s+error\s+\(variable\s+(\w+)\)\s*:\s*([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)",
        combined,
    ):
        norm_type = "l2" if match.group(1) == "2" else "linf"
        var = match.group(2).lower()
        if var in _COORDINATE_VARIABLES:
            continue
        key = f"{norm_type}_error_{var}"
        norms[key] = float(match.group(3))
    return norms


def _run_real_solver(
    task_id: str,
    session_path: Path,
    *,
    binary_name: str = "ADRSolver",
    solver_family: NektarSolverFamily = NektarSolverFamily.ADR,
) -> NektarRunArtifact:
    solver_binary = shutil.which(binary_name)
    assert solver_binary is not None
    result = subprocess.run(
        [solver_binary, str(session_path)],
        cwd=session_path.parent,
        text=True,
        capture_output=True,
        check=False,
        timeout=600,
    )
    (session_path.parent / "solver.stdout.log").write_text(result.stdout)
    (session_path.parent / "solver.stderr.log").write_text(result.stderr)
    (session_path.parent / "solver.log").write_text(
        result.stdout + ("\n\n" if result.stdout and result.stderr else "") + result.stderr
    )
    field_files = sorted(str(path) for path in session_path.parent.glob("*.fld"))
    checkpoint_files = sorted(str(path) for path in session_path.parent.glob("*.chk"))
    error_norms = _extract_error_norms(result.stdout, result.stderr)
    return NektarRunArtifact(
        run_id=f"run::{task_id}",
        task_id=task_id,
        solver_family=solver_family,
        solver_binary=solver_binary,
        session_files=[str(session_path)],
        field_files=field_files,
        log_files=[
            str(session_path.parent / "solver.log"),
            str(session_path.parent / "solver.stdout.log"),
            str(session_path.parent / "solver.stderr.log"),
        ],
        filter_output=FilterOutputSummary(
            checkpoint_files=checkpoint_files,
            error_norms=error_norms,
        ),
        result_summary={
            "exit_code": result.returncode,
            "timeout_seconds": 600,
            "fallback_reason": None,
        },
        postprocess_plan=[
            {"type": "fieldconvert", "output": "solution.vtu"},
        ],
        status="completed" if result.returncode == 0 else "failed",
    )


class _RealExecutor:
    def __init__(self, tmp_path: Path, source: Path) -> None:
        self.tmp_path = tmp_path
        self.source = source

    def execute_plan(self, plan) -> NektarRunArtifact:
        num_modes = int(plan.parameters["NumModes"])
        session_path = _copy_case_with_nummodes(self.tmp_path, plan.task_id, self.source, num_modes)
        return _run_real_solver(plan.task_id, session_path)


def _assert_solver_artifact(artifact: NektarRunArtifact) -> None:
    assert artifact.status == "completed"
    assert artifact.result_summary["exit_code"] == 0
    assert artifact.field_files


def _assert_error_evaluation_result(
    processed: NektarRunArtifact,
    *,
    expected_l2_u: float,
    expected_linf_u: float,
) -> None:
    error_files = [Path(path) for path in processed.derived_files if path.endswith("error.vtu")]
    assert error_files
    assert error_files[0].exists()
    assert error_files[0].stat().st_size > 0

    norms = processed.filter_output.error_norms
    assert "l2_error_x" not in norms
    assert "linf_error_x" not in norms
    assert "l2_error_y" not in norms
    assert "linf_error_y" not in norms
    assert norms["l2_error_u"] == pytest.approx(expected_l2_u)
    assert norms["linf_error_u"] == pytest.approx(expected_linf_u)


@pytest.mark.nektar
def test_helmholtz_1d_e2e(nektar_examples_available: None, tmp_path: Path) -> None:
    session_path = _copy_case(tmp_path, "helmholtz-1d", HELMHOLTZ_1D)
    artifact = _run_real_solver("helmholtz-1d", session_path)

    _assert_solver_artifact(artifact)

    processed = PostprocessComponent().run_postprocess(artifact)

    assert any(path.endswith("solution.vtu") for path in processed.derived_files)

    report = NektarValidatorComponent().validate_run(processed)
    assert report.passed is True


@pytest.mark.nektar
def test_helmholtz_2d_e2e(nektar_examples_available: None, tmp_path: Path) -> None:
    session_path = _copy_case(tmp_path, "helmholtz-2d", HELMHOLTZ_2D)
    artifact = _run_real_solver("helmholtz-2d", session_path)

    _assert_solver_artifact(artifact)

    processed = PostprocessComponent().run_postprocess(artifact)

    assert any(path.endswith("solution.vtu") for path in processed.derived_files)

    report = NektarValidatorComponent().validate_run(processed)
    assert report.passed is True


@pytest.mark.nektar
def test_helmholtz_1d_convergence_study_e2e(
    nektar_examples_available: None, tmp_path: Path
) -> None:
    component = ConvergenceStudyComponent()
    import asyncio

    asyncio.run(component.activate(ComponentRuntime(storage_path=tmp_path)))
    spec = ConvergenceStudySpec(
        study_id="helmholtz-1d-study",
        task_id="helmholtz-1d-study",
        base_problem=NektarProblemSpec(
            task_id="helmholtz-1d-study",
            title="helmholtz-1d",
            solver_family=NektarSolverFamily.ADR,
            dimension=1,
            variables=["u"],
            domain={"mesh_path": str(HELMHOLTZ_1D)},
        ),
        axis=NektarMutationAxis(kind="num_modes", values=[4, 8, 12]),
        metric_key="l2_error_u",
        target_tolerance=0.3,
        min_points=3,
        convergence_rule="absolute",
    )

    report = component.run_study(
        spec,
        executor=_RealExecutor(tmp_path, HELMHOLTZ_1D),
        postprocessor=PostprocessComponent(),
        validator=NektarValidatorComponent(),
    )

    assert len(report.trials) == 3
    assert report.error_sequence
    assert report.error_sequence[-1] <= report.error_sequence[0]
    assert report.recommended_value is not None
    assert report.observed_order is not None
    assert report.recommended_reason is not None


@pytest.mark.nektar
def test_helmholtz_2d_convergence_study_e2e(
    nektar_examples_available: None, tmp_path: Path
) -> None:
    component = ConvergenceStudyComponent()
    import asyncio

    asyncio.run(component.activate(ComponentRuntime(storage_path=tmp_path)))
    spec = ConvergenceStudySpec(
        study_id="helmholtz-2d-study",
        task_id="helmholtz-2d-study",
        base_problem=NektarProblemSpec(
            task_id="helmholtz-2d-study",
            title="helmholtz-2d",
            solver_family=NektarSolverFamily.ADR,
            dimension=2,
            variables=["u"],
        ),
        axis=NektarMutationAxis(kind="num_modes", values=[4, 8, 12]),
        metric_key="l2_error_u",
        target_tolerance=1.0,
        min_points=3,
        convergence_rule="absolute",
    )

    report = component.run_study(
        spec,
        executor=_RealExecutor(tmp_path, HELMHOLTZ_2D),
        postprocessor=PostprocessComponent(),
        validator=NektarValidatorComponent(),
    )

    assert len(report.trials) == 3
    assert report.error_sequence
    assert report.error_sequence[-1] <= report.error_sequence[0]
    assert report.recommended_value is not None
    assert report.observed_order is not None
    assert report.recommended_reason is not None


@pytest.mark.nektar
def test_fieldconvert_vtu_conversion_e2e(nektar_examples_available: None, tmp_path: Path) -> None:
    session_path = _copy_case(tmp_path, "helmholtz-vtu", HELMHOLTZ_1D)
    artifact = _run_real_solver("helmholtz-vtu", session_path)
    artifact.postprocess_plan = [{"type": "fieldconvert", "output": "solution.vtu"}]

    processed = PostprocessComponent().run_postprocess(artifact)

    vtu_files = [Path(path) for path in processed.derived_files if path.endswith("solution.vtu")]
    assert vtu_files
    assert vtu_files[0].exists()
    assert vtu_files[0].stat().st_size > 0


@pytest.mark.nektar
def test_fieldconvert_error_evaluation_e2e(nektar_examples_available: None, tmp_path: Path) -> None:
    session_path = _copy_case(tmp_path, "helmholtz-error", HELMHOLTZ_1D)
    artifact = _run_real_solver("helmholtz-error", session_path)
    artifact.postprocess_plan = [{"type": "fieldconvert", "output": "error.vtu", "args": ["-e"]}]

    processed = PostprocessComponent().run_postprocess(artifact)

    _assert_error_evaluation_result(
        processed,
        expected_l2_u=1.54954,
        expected_linf_u=1.0,
    )


@pytest.mark.nektar
def test_fieldconvert_error_evaluation_2d_e2e(
    nektar_examples_available: None, tmp_path: Path
) -> None:
    session_path = _copy_case(tmp_path, "helmholtz-error-2d", HELMHOLTZ_2D)
    artifact = _run_real_solver("helmholtz-error-2d", session_path)
    artifact.postprocess_plan = [{"type": "fieldconvert", "output": "error.vtu", "args": ["-e"]}]

    processed = PostprocessComponent().run_postprocess(artifact)

    _assert_error_evaluation_result(
        processed,
        expected_l2_u=0.927214,
        expected_linf_u=0.950874,
    )


@pytest.mark.nektar
def test_taylor_vortex_incns_e2e(incns_examples_available: None, tmp_path: Path) -> None:
    session_path = _copy_case(tmp_path, "taylor-vortex", TAYLOR_VORTEX)
    artifact = _run_real_solver(
        "taylor-vortex",
        session_path,
        binary_name="IncNavierStokesSolver",
        solver_family=NektarSolverFamily.INCNS,
    )

    _assert_solver_artifact(artifact)

    norms = artifact.filter_output.error_norms
    assert "l2_error_u" in norms
    assert "l2_error_v" in norms
    assert "l2_error_p" in norms
    assert norms["l2_error_u"] < 1e-3

    processed = PostprocessComponent().run_postprocess(artifact)
    assert any(path.endswith("solution.vtu") for path in processed.derived_files)

    report = NektarValidatorComponent().validate_run(processed)
    assert report.passed is True
    assert report.error_vs_reference is True
