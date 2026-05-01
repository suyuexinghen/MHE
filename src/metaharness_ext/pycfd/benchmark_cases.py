from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec


def pycfd_case_catalog(
    case_ids: list[str] | None = None,
) -> dict[str, BenchmarkCaseSpec]:
    """Return the canonical PyCFD benchmark case catalog, optionally filtered.

    Five cases covering the full solver surface:
    - vortex-2d: isentropic vortex convection (unsteady, accuracy)
    - airfoil-2d: NACA 0012 steady flow (engineering)
    - cylinder-2d: inviscid cylinder (steady, benchmark)
    - mms-2d: method of manufactured solutions (verification)
    - shock-diffraction-2d: Mach 5.09 shock over step (shock-capturing)
    """
    cases: list[BenchmarkCaseSpec] = []

    _vortex_problem = {
        "case_type": "vortex",
        "mesh": {"mesh_type": "tri", "nx": 64, "ny": 64,
                 "xb": -10.0, "xe": 10.0, "yb": -10.0, "ye": 10.0},
        "flow": {"M_inf": 0.3, "aoa": 0.0},
        "solver": {"CFL": 0.5, "second_order": True, "use_limiter": True, "max_steps": 5000},
        "t_final": 0.2, "dt": 0.05, "timeout_seconds": 600,
    }
    cases.append(
        BenchmarkCaseSpec(
            case_id="vortex-2d",
            suite="pycfd-pde",
            task_family="pycfd_vortex",
            description="Isentropic vortex convection (2D Euler, unsteady)",
            source_reference="PyCFD vortex case: isentropic vortex advection, structured tri mesh",
            expected_metrics=["residual_l1", "residual_l2", "wall_time_seconds", "iterations", "ncells", "nnodes", "nfaces"],
            tolerance={"residual_l1": 1e-4, "residual_l2": 1e-4},
            problem_definition=_vortex_problem,
        )
    )

    _airfoil_problem = {
        "case_type": "airfoil",
        "mesh": {"mesh_type": "quad", "nx": 60, "ny": 20,
                 "xb": -5.0, "xe": 15.0, "yb": -5.0, "ye": 5.0},
        "flow": {"M_inf": 0.80, "aoa": 1.25},
        "solver": {"CFL": 0.9, "second_order": True, "use_limiter": True, "max_steps": 15000},
        "t_final": 100.0, "dt": 0.1, "timeout_seconds": 600,
    }
    cases.append(
        BenchmarkCaseSpec(
            case_id="airfoil-2d",
            suite="pycfd-pde",
            task_family="pycfd_airfoil",
            description="NACA 0012 steady inviscid flow (2D Euler, M=0.80)",
            source_reference="PyCFD airfoil case: NACA 0012, unstructured quad mesh, M=0.80",
            expected_metrics=["residual_l1", "residual_l2", "wall_time_seconds", "iterations", "ncells", "nnodes", "nfaces"],
            tolerance={"residual_l1": 1e-3, "residual_l2": 1e-3},
            problem_definition=_airfoil_problem,
        )
    )

    _cylinder_problem = {
        "case_type": "cylinder",
        "mesh": {"mesh_type": "tri", "nx": 42, "ny": 21,
                 "xb": -10.0, "xe": 20.0, "yb": -10.0, "ye": 10.0},
        "flow": {"M_inf": 0.3, "aoa": 0.0},
        "solver": {"CFL": 0.5, "second_order": True, "use_limiter": True, "max_steps": 100000},
        "t_final": 100.0, "dt": 0.1, "timeout_seconds": 600,
    }
    cases.append(
        BenchmarkCaseSpec(
            case_id="cylinder-2d",
            suite="pycfd-pde",
            task_family="pycfd_cylinder",
            description="Inviscid flow over circular cylinder (2D Euler, M=0.3)",
            source_reference="PyCFD cylinder case: inviscid cylinder, structured tri mesh, M=0.3",
            expected_metrics=["residual_l1", "residual_l2", "wall_time_seconds", "iterations", "ncells", "nnodes", "nfaces"],
            tolerance={"residual_l1": 1e-3, "residual_l2": 1e-3},
            problem_definition=_cylinder_problem,
        )
    )

    _mms_problem = {
        "case_type": "mms",
        "mesh": {"mesh_type": "quad", "nx": 32, "ny": 32,
                 "xb": -1.0, "xe": 1.0, "yb": -1.0, "ye": 1.0},
        "flow": {"M_inf": 0.3, "aoa": 0.0},
        "solver": {"CFL": 0.9, "second_order": True, "use_limiter": False, "max_steps": 1000},
        "t_final": 1.0, "dt": 0.01, "timeout_seconds": 120,
    }
    cases.append(
        BenchmarkCaseSpec(
            case_id="mms-2d",
            suite="pycfd-pde",
            task_family="pycfd_mms",
            description="Method of manufactured solutions (2D Euler, MMS verification)",
            source_reference="PyCFD MMS case: manufactured solutions, structured quad mesh",
            expected_metrics=["residual_l1", "residual_l2", "wall_time_seconds", "iterations", "ncells", "nnodes", "nfaces"],
            tolerance={"residual_l1": 1e-6, "residual_l2": 1e-6},
            problem_definition=_mms_problem,
        )
    )

    _shock_problem = {
        "case_type": "shock_diffraction",
        "mesh": {"mesh_type": "quad", "nx": 42, "ny": 21,
                 "xb": 0.0, "xe": 1.0, "yb": 0.0, "ye": 1.0},
        "flow": {"M_inf": 5.09, "aoa": 0.0},
        "solver": {"CFL": 0.5, "second_order": True, "use_limiter": True, "max_steps": 10000},
        "t_final": 0.7, "dt": 0.01, "timeout_seconds": 600,
    }
    cases.append(
        BenchmarkCaseSpec(
            case_id="shock-diffraction-2d",
            suite="pycfd-pde",
            task_family="pycfd_shock",
            description="Mach 5.09 shock diffraction over step (2D Euler, shock-capturing)",
            source_reference="PyCFD shock diffraction case: M=5.09 shock over step, structured quad mesh",
            expected_metrics=["residual_l1", "residual_l2", "wall_time_seconds", "iterations", "ncells", "nnodes", "nfaces"],
            tolerance={"residual_l1": 1e-3, "residual_l2": 1e-3},
            problem_definition=_shock_problem,
        )
    )

    result = {case.case_id: case for case in cases}
    if case_ids is not None:
        result = {k: v for k, v in result.items() if k in case_ids}
    return result
