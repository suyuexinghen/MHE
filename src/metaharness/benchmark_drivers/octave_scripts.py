from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec


def build_octave_case_script(case: BenchmarkCaseSpec) -> str:
    scripts = {
        "ode45-vanderpol": _ode45_vanderpol,
        "ode45-exp-decay": _ode_exp_decay,
        "ode23-exp-decay": _ode_exp_decay,
        "ode23s-linear-stiff": _ode23s_linear_stiff,
        "fsolve-3x3": _fsolve_3x3,
        "fsolve-exp-fit": _fsolve_exp_fit,
        "fminunc-rosenbrock-2d": _fminunc_rosenbrock_2d,
        "expm-jordan-2x2": _expm_jordan_2x2,
        "roots-cubic": _roots_cubic,
        "sinc-values": _sinc_values,
    }
    try:
        return scripts[case.case_id](case)
    except KeyError as exc:
        raise ValueError(f"No Octave script builder for case: {case.case_id}") from exc


def _with_timer(body: str) -> str:
    return "tic;\n" + body.strip() + "\nelapsed_seconds = toc;\n"


def _ode45_vanderpol(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        f = @(t, y) [y(2); (1 - y(1)^2) * y(2) - y(1)];
        [~, y] = ode45(f, [0 2], [2; 0]);
        endpoint_inf_error = norm(y(end, :) - [0.32331666704577, -1.83297456798624], Inf);
        """
    )


def _ode_exp_decay(case: BenchmarkCaseSpec) -> str:
    solver = str(case.problem_definition.get("solver_function", "ode45"))
    return _with_timer(
        f"""
        f = @(t, y) -y;
        [t, y] = {solver}(f, linspace(0, 2, 21), 1);
        expected = exp(-t);
        max_error = max(abs(y(:) - expected(:)));
        endpoint_error = abs(y(end) - exp(-2));
        """
    )


def _ode23s_linear_stiff(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        f = @(t, y) -15 * y;
        [~, y] = ode23s(f, [0 1], 1);
        endpoint_error = abs(y(end) - exp(-15));
        """
    )


def _fsolve_3x3(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        f = @(x) [x(1)^2 + x(2) - 37; x(1) - x(2)^2 - 5; x(1) + x(2) + x(3) - 3];
        reference = [6; 1; -4];
        solution = fsolve(f, [6; 1; -4]);
        solution_inf_error = norm(solution - reference, Inf);
        residual_norm = norm(f(solution));
        """
    )


def _fsolve_exp_fit(case: BenchmarkCaseSpec) -> str:
    true_parameters = case.problem_definition.get("true_parameters", [0.2, 3.0])
    initial_guess = case.problem_definition.get("initial_guess", [0.0, 0.0])
    return _with_timer(
        f"""
        xdata = (0:0.1:1)';
        true_parameters = [{float(true_parameters[0])}; {float(true_parameters[1])}];
        ydata = true_parameters(1) * exp(true_parameters(2) * xdata);
        residual = @(p) p(1) * exp(p(2) * xdata) - ydata;
        solution = fsolve(residual, [{float(initial_guess[0])}; {float(initial_guess[1])}]);
        parameter_inf_error = norm(solution - true_parameters, Inf);
        residual_norm = norm(residual(solution));
        """
    )


def _fminunc_rosenbrock_2d(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        objective = @(x) 100 * (x(2) - x(1)^2)^2 + (1 - x(1))^2;
        solution = fminunc(objective, [-1.2; 1]);
        solution_inf_error = norm(solution - [1; 1], Inf);
        objective_error = abs(objective(solution));
        """
    )


def _expm_jordan_2x2(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        matrix = [1 1; 0 1];
        expected = exp(1) * [1 1; 0 1];
        matrix_norm_error = norm(expm(matrix) - expected, Inf);
        """
    )


def _roots_cubic(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        computed = sort(roots(poly([1 2 3])));
        expected = [1; 2; 3];
        root_inf_error = norm(computed - expected, Inf);
        """
    )


def _sinc_values(_: BenchmarkCaseSpec) -> str:
    return _with_timer(
        """
        points = [0, 0.5, 1];
        expected = [1, 2 / pi, 0];
        max_abs_error = max(abs(sinc(points) - expected));
        """
    )
