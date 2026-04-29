from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference

NEKTAR_ROOT = "/home/linden/code/work/Solvers/Nektar/nektar/solvers"


def _source(solver_dir: str, name: str) -> dict[str, str]:
    base = f"{NEKTAR_ROOT}/{solver_dir}/Tests/{name}"
    return {"tst": f"{base}.tst", "xml": f"{base}.xml"}


def nektar_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        BenchmarkCaseSpec(
            case_id="advection-1d",
            suite="nektar-pde",
            task_family="nektar_pde",
            description="1D unsteady advection ADRSolver regression case",
            required_capabilities=["nektar_adr_solver"],
            source_reference=_source("ADRSolver", "Advection1D_WeakDG_GLL_LAGRANGE"),
            expected_metrics=["l2_error_u", "linf_error_u", "elapsed_seconds"],
            reference_metrics={
                "l2_error_u": MetricReference(value=0.00960004, tolerance=1e-8),
            },
            problem_definition={
                "solver_family": "adr",
                "solver_binary": "ADRSolver",
                "pde_type": "unsteady_advection",
                "dimension": 1,
            },
        ),
        BenchmarkCaseSpec(
            case_id="diffusion-2d",
            suite="nektar-pde",
            task_family="nektar_pde",
            description="2D unsteady diffusion DiffusionSolver regression case",
            required_capabilities=["nektar_diffusion_solver"],
            source_reference=_source("DiffusionSolver", "ImDiffusion_m6"),
            expected_metrics=["l2_error_u", "linf_error_u", "elapsed_seconds"],
            reference_metrics={"l2_error_u": MetricReference(value=0.0020082, tolerance=1e-8)},
            problem_definition={
                "solver_family": "diffusion",
                "solver_binary": "DiffusionSolver",
                "pde_type": "unsteady_diffusion",
                "dimension": 2,
            },
        ),
        BenchmarkCaseSpec(
            case_id="advdiff-2d",
            suite="nektar-pde",
            task_family="nektar_pde",
            description="2D unsteady advection-diffusion ADRSolver regression case",
            required_capabilities=["nektar_adr_solver"],
            source_reference=_source("ADRSolver", "UnsteadyAdvectionDiffusion_Order1_001"),
            expected_metrics=["l2_error_u", "linf_error_u", "elapsed_seconds"],
            reference_metrics={
                "l2_error_u": MetricReference(value=0.00135233, tolerance=1e-8),
                "linf_error_u": MetricReference(value=0.00275937, tolerance=1e-8),
            },
            problem_definition={
                "solver_family": "adr",
                "solver_binary": "ADRSolver",
                "pde_type": "unsteady_advection_diffusion",
                "dimension": 2,
            },
        ),
        BenchmarkCaseSpec(
            case_id="advdiff-imex-2d",
            suite="nektar-pde",
            task_family="nektar_pde",
            description="2D high-order IMEX advection-diffusion ADRSolver regression case",
            required_capabilities=["nektar_adr_solver"],
            source_reference=_source("ADRSolver", "UnsteadyAdvectionDiffusion2D_IMEXdirk_2_3_3"),
            expected_metrics=["l2_error_u", "linf_error_u", "elapsed_seconds"],
            reference_metrics={"l2_error_u": MetricReference(value=1.85112e-7, tolerance=1e-10)},
            problem_definition={
                "solver_family": "adr",
                "solver_binary": "ADRSolver",
                "pde_type": "unsteady_advection_diffusion",
                "dimension": 2,
            },
        ),
        BenchmarkCaseSpec(
            case_id="taylor-vortex-2d",
            suite="nektar-pde",
            task_family="nektar_pde",
            description="2D Taylor vortex IncNavierStokesSolver regression case",
            required_capabilities=["nektar_incns_solver"],
            source_reference=_source("IncNavierStokesSolver", "TaylorVor_dt1"),
            expected_metrics=["l2_error_u", "linf_error_u", "elapsed_seconds"],
            reference_metrics={"l2_error_u": MetricReference(value=5.9519e-6, tolerance=1e-8)},
            problem_definition={
                "solver_family": "incns",
                "solver_binary": "IncNavierStokesSolver",
                "pde_type": "unsteady_navier_stokes",
                "dimension": 2,
            },
        ),
        BenchmarkCaseSpec(
            case_id="euler-1d",
            suite="nektar-pde",
            task_family="nektar_pde",
            description="1D Euler CompressibleFlowSolver regression case",
            required_capabilities=["nektar_compressible_solver"],
            source_reference=_source("CompressibleFlowSolver", "Euler1D"),
            expected_metrics=["l2_error_rho", "linf_error_rho", "elapsed_seconds"],
            reference_metrics={"l2_error_rho": MetricReference(value=1.98838e-6, tolerance=1e-8)},
            problem_definition={
                "solver_family": "compressible",
                "solver_binary": "CompressibleFlowSolver",
                "pde_type": "euler_cfe",
                "dimension": 1,
            },
            capability_gated=True,
        ),
    ]
    return {case.case_id: case for case in cases}


def get_nektar_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = nektar_case_catalog()
    if not case_ids:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
