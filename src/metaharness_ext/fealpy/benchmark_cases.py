from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference


def fealpy_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        BenchmarkCaseSpec(
            case_id="poisson-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Poisson equation, P1 Lagrange, numpy backend",
            required_capabilities=["fealpy_numpy"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            reference_metrics={
                "l2_error": MetricReference(value=0.002, tolerance=0.1),
            },
            problem_definition={
                "pde_family": "poisson",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "tri",
                "nx": 16,
                "ny": 16,
                "fe_degree": 1,
            },
        ),
        BenchmarkCaseSpec(
            case_id="poisson-2d-pytorch",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Poisson equation, P1 Lagrange, pytorch backend",
            required_capabilities=["fealpy_pytorch"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            reference_metrics={
                "l2_error": MetricReference(value=0.002, tolerance=0.1),
            },
            problem_definition={
                "pde_family": "poisson",
                "example_key": 1,
                "backend": "pytorch",
                "meshtype": "tri",
                "nx": 16,
                "ny": 16,
                "fe_degree": 1,
            },
            capability_gated=True,
        ),
        BenchmarkCaseSpec(
            case_id="poisson-2d-jax",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Poisson equation, P1 Lagrange, jax backend",
            required_capabilities=["fealpy_jax"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            reference_metrics={
                "l2_error": MetricReference(value=0.002, tolerance=0.1),
            },
            problem_definition={
                "pde_family": "poisson",
                "example_key": 1,
                "backend": "jax",
                "meshtype": "tri",
                "nx": 16,
                "ny": 16,
                "fe_degree": 1,
            },
            capability_gated=True,
        ),
        BenchmarkCaseSpec(
            case_id="poisson-3d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="3D Poisson equation, P1 Lagrange uniform mesh, numpy backend",
            required_capabilities=["fealpy_numpy"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            reference_metrics={
                "l2_error": MetricReference(value=0.01, tolerance=0.1),
            },
            problem_definition={
                "pde_family": "poisson",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "uniform",
                "nx": 8,
                "ny": 8,
                "nz": 8,
                "fe_degree": 1,
            },
            capability_gated=True,
        ),
        BenchmarkCaseSpec(
            case_id="stokes-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Stokes flow, Taylor-Hood P2/P1, numpy backend",
            required_capabilities=["fealpy_numpy"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            problem_definition={
                "pde_family": "stokes",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "tri",
                "nx": 8,
                "ny": 8,
                "fe_degree": 2,
            },
        ),
        BenchmarkCaseSpec(
            case_id="darcy-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Darcy flow, Raviart-Thomas P0/P0 mixed, numpy backend",
            required_capabilities=["fealpy_numpy"],
            source_reference={},
            expected_metrics=["wall_time", "dof"],
            problem_definition={
                "pde_family": "darcy",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "tri",
                "nx": 8,
                "ny": 8,
                "fe_degree": 0,
            },
        ),
        BenchmarkCaseSpec(
            case_id="linear_elasticity-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D linear elasticity, Hu-Zhang elements, numpy backend",
            required_capabilities=["fealpy_numpy"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            problem_definition={
                "pde_family": "linear_elasticity",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "tri",
                "nx": 8,
                "ny": 8,
                "fe_degree": 1,
            },
        ),
        BenchmarkCaseSpec(
            case_id="curlcurl-2d-numpy",
            suite="fealpy-pde",
            task_family="fealpy_pde",
            description="2D Maxwell curl-curl, Nedelec edge elements, numpy backend",
            required_capabilities=["fealpy_numpy"],
            source_reference={},
            expected_metrics=["l2_error", "h1_error", "wall_time", "dof"],
            problem_definition={
                "pde_family": "curlcurl",
                "example_key": 1,
                "backend": "numpy",
                "meshtype": "tri",
                "nx": 8,
                "ny": 8,
                "fe_degree": 1,
            },
        ),
    ]
    return {case.case_id: case for case in cases}


def get_fealpy_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = fealpy_case_catalog()
    if not case_ids:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
