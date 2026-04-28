from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference


def octave_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        BenchmarkCaseSpec(
            case_id="ode45-vanderpol",
            suite="octave-native",
            task_family="ode",
            description="Van der Pol ODE case from Octave ode45 BIST/demo references",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/ode/ode45.m",
            expected_metrics=["endpoint_inf_error", "elapsed_seconds"],
            reference_metrics={"endpoint_inf_error": MetricReference(value=0.0, tolerance=1e-6)},
            problem_definition={"solver_function": "ode45"},
        ),
        BenchmarkCaseSpec(
            case_id="ode45-exp-decay",
            suite="octave-native",
            task_family="ode",
            description="Exponential decay ODE solved with ode45",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/ode/ode45.m",
            expected_metrics=["max_error", "endpoint_error", "elapsed_seconds"],
            reference_metrics={
                "max_error": MetricReference(value=0.0, tolerance=1e-6),
                "endpoint_error": MetricReference(value=0.0, tolerance=1e-6),
            },
            problem_definition={"solver_function": "ode45", "analytic_solution": "exp(-t)"},
        ),
        BenchmarkCaseSpec(
            case_id="ode23-exp-decay",
            suite="octave-native",
            task_family="ode",
            description="Exponential decay ODE solved with ode23",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/ode/ode23.m",
            expected_metrics=["max_error", "endpoint_error", "elapsed_seconds"],
            reference_metrics={
                "max_error": MetricReference(value=0.0, tolerance=1e-5),
                "endpoint_error": MetricReference(value=0.0, tolerance=1e-5),
            },
            problem_definition={"solver_function": "ode23", "analytic_solution": "exp(-t)"},
        ),
        BenchmarkCaseSpec(
            case_id="ode23s-linear-stiff",
            suite="octave-native",
            task_family="stiff_ode",
            description="Linear stiff/semi-stiff ODE solved with ode23s",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/ode/ode23s.m",
            expected_metrics=["endpoint_error", "elapsed_seconds"],
            reference_metrics={"endpoint_error": MetricReference(value=0.0, tolerance=1e-5)},
            problem_definition={"solver_function": "ode23s"},
        ),
        BenchmarkCaseSpec(
            case_id="fsolve-3x3",
            suite="octave-native",
            task_family="nonlinear_solve",
            description="3x3 nonlinear system from Octave fsolve BIST",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fsolve.m",
            expected_metrics=["solution_inf_error", "residual_norm", "elapsed_seconds"],
            reference_metrics={
                "solution_inf_error": MetricReference(value=0.0, tolerance=1e-5),
                "residual_norm": MetricReference(value=0.0, tolerance=1e-8),
            },
            problem_definition={"solver_function": "fsolve"},
        ),
        BenchmarkCaseSpec(
            case_id="fsolve-exp-fit",
            suite="octave-native",
            task_family="curve_fit",
            description="Synthetic exponential fit from Octave fsolve BIST",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fsolve.m",
            expected_metrics=["parameter_inf_error", "residual_norm", "elapsed_seconds"],
            reference_metrics={
                "parameter_inf_error": MetricReference(value=0.0, tolerance=1e-5),
                "residual_norm": MetricReference(value=0.0, tolerance=1e-5),
            },
            problem_definition={"true_parameters": [0.2, 3.0], "initial_guess": [0.0, 0.0]},
        ),
        BenchmarkCaseSpec(
            case_id="fminunc-rosenbrock-2d",
            suite="octave-native",
            task_family="optimization",
            description="Rosenbrock 2D minimization from Octave fminunc references",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/optimization/fminunc.m",
            expected_metrics=["solution_inf_error", "objective_error", "elapsed_seconds"],
            reference_metrics={
                "solution_inf_error": MetricReference(value=0.0, tolerance=1e-5),
                "objective_error": MetricReference(value=0.0, tolerance=1e-8),
            },
            problem_definition={"solver_function": "fminunc", "reference_solution": [1.0, 1.0]},
        ),
        BenchmarkCaseSpec(
            case_id="expm-jordan-2x2",
            suite="octave-native",
            task_family="linear_algebra",
            description="Jordan block matrix exponential from Octave expm references",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/linear-algebra/expm.m",
            expected_metrics=["matrix_norm_error", "elapsed_seconds"],
            reference_metrics={"matrix_norm_error": MetricReference(value=0.0, tolerance=1e-10)},
            problem_definition={"solver_function": "expm"},
        ),
        BenchmarkCaseSpec(
            case_id="roots-cubic",
            suite="octave-native",
            task_family="polynomial",
            description="Known cubic roots from Octave roots references",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/polynomial/roots.m",
            expected_metrics=["root_inf_error", "elapsed_seconds"],
            reference_metrics={"root_inf_error": MetricReference(value=0.0, tolerance=1e-10)},
            problem_definition={"polynomial_roots": [1.0, 2.0, 3.0]},
        ),
        BenchmarkCaseSpec(
            case_id="sinc-values",
            suite="octave-native",
            task_family="signal",
            description="Known sinc values from Octave sinc references",
            required_capabilities=["octave-cli"],
            source_reference="/home/myfile/distfiles/octave-9.2.0/scripts/signal/sinc.m",
            expected_metrics=["max_abs_error", "elapsed_seconds"],
            reference_metrics={"max_abs_error": MetricReference(value=0.0, tolerance=1e-12)},
            problem_definition={"points": [0.0, 0.5, 1.0]},
        ),
    ]
    return {case.case_id: case for case in cases}


def get_octave_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = octave_case_catalog()
    if not case_ids:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
