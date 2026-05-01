from __future__ import annotations

from metaharness_ext.pycfd.contracts import (
    PyCFDFlowSpec,
    PyCFDMeshSpec,
    PyCFDProblemSpec,
    PyCFDSolverSpec,
)
from metaharness_ext.pycfd.types import PyCFDCaseType


def pycfd_case_catalog() -> dict[str, PyCFDProblemSpec]:
    """Return the canonical PyCFD benchmark case catalog.

    Five cases covering the full solver surface:
    - vortex-2d: isentropic vortex convection (unsteady, accuracy)
    - airfoil-2d: NACA 0012 steady flow (engineering)
    - cylinder-2d: inviscid cylinder (steady, benchmark)
    - mms-2d: method of manufactured solutions (verification)
    - shock-diffraction-2d: Mach 5.09 shock over step (shock-capturing)
    """
    cases: dict[str, PyCFDProblemSpec] = {}

    # ── Vortex ──────────────────────────────────────────────────────
    cases["vortex-2d"] = PyCFDProblemSpec(
        task_id="vortex-2d",
        case_type="vortex",
        mesh=PyCFDMeshSpec(mesh_type="tri", nx=64, ny=64, xb=-10.0, xe=10.0, yb=-10.0, ye=10.0),
        flow=PyCFDFlowSpec(M_inf=0.3, aoa=0.0),
        solver=PyCFDSolverSpec(CFL=0.9, second_order=True, use_limiter=False, max_steps=100000),
        t_final=1.0,
        dt=0.01,
        timeout_seconds=300,
    )

    # ── Airfoil ─────────────────────────────────────────────────────
    cases["airfoil-2d"] = PyCFDProblemSpec(
        task_id="airfoil-2d",
        case_type="airfoil",
        mesh=PyCFDMeshSpec(mesh_type="quad", nx=60, ny=20, xb=-5.0, xe=15.0, yb=-5.0, ye=5.0),
        flow=PyCFDFlowSpec(M_inf=0.80, aoa=1.25),
        solver=PyCFDSolverSpec(CFL=0.9, second_order=True, use_limiter=True, max_steps=15000),
        t_final=100.0,
        dt=0.1,
        timeout_seconds=600,
    )

    # ── Cylinder ────────────────────────────────────────────────────
    cases["cylinder-2d"] = PyCFDProblemSpec(
        task_id="cylinder-2d",
        case_type="cylinder",
        mesh=PyCFDMeshSpec(mesh_type="tri", nx=42, ny=21, xb=-10.0, xe=20.0, yb=-10.0, ye=10.0),
        flow=PyCFDFlowSpec(M_inf=0.3, aoa=0.0),
        solver=PyCFDSolverSpec(CFL=0.9, second_order=True, use_limiter=False, max_steps=100000),
        t_final=100.0,
        dt=0.1,
        timeout_seconds=600,
    )

    # ── MMS ─────────────────────────────────────────────────────────
    cases["mms-2d"] = PyCFDProblemSpec(
        task_id="mms-2d",
        case_type="mms",
        mesh=PyCFDMeshSpec(mesh_type="quad", nx=32, ny=32, xb=-1.0, xe=1.0, yb=-1.0, ye=1.0),
        flow=PyCFDFlowSpec(M_inf=0.3, aoa=0.0),
        solver=PyCFDSolverSpec(CFL=0.9, second_order=True, use_limiter=False, max_steps=1000),
        t_final=1.0,
        dt=0.01,
        timeout_seconds=120,
    )

    # ── Shock Diffraction ───────────────────────────────────────────
    cases["shock-diffraction-2d"] = PyCFDProblemSpec(
        task_id="shock-diffraction-2d",
        case_type="shock_diffraction",
        mesh=PyCFDMeshSpec(mesh_type="quad", nx=42, ny=21, xb=0.0, xe=1.0, yb=0.0, ye=1.0),
        flow=PyCFDFlowSpec(M_inf=5.09, aoa=0.0),
        solver=PyCFDSolverSpec(CFL=0.5, second_order=True, use_limiter=True, max_steps=10000),
        t_final=0.7,
        dt=0.01,
        timeout_seconds=600,
    )

    return cases


def get_pycfd_cases(case_types: list[PyCFDCaseType] | None = None) -> dict[str, PyCFDProblemSpec]:
    """Return a filtered subset of the catalog."""
    catalog = pycfd_case_catalog()
    if case_types is None:
        return catalog
    return {k: v for k, v in catalog.items() if v.case_type in case_types}
