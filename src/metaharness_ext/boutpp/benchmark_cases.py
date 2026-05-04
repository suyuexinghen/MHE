from __future__ import annotations

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, MetricReference


def boutpp_usage_case_catalog() -> dict[str, BenchmarkCaseSpec]:
    cases = [
        BenchmarkCaseSpec(
            case_id="conduction-basic",
            suite="boutpp-usage",
            task_family="boutpp_usage",
            description="Basic BOUT++ conduction workflow usage validation",
            source_reference="docs/Tutorial/bout_docs/user_docs/python_boutpp.md",
            expected_metrics=["elapsed_seconds"],
            reference_metrics={"elapsed_seconds": MetricReference(value=0.0, tolerance=0.0)},
            problem_definition={
                "case_name": "conduction-basic",
                "executable": "conduction",
                "source_case_dir": "examples/conduction",
                "data_dir": "data",
                "options": {
                    "solver": {"type": "rk4", "atol": 1e-10, "rtol": 1e-08},
                    "mesh": {"nx": 16, "ny": 8},
                },
                "cli_overrides": ["solver:type=rk4"],
                "mpi": {"processes": 1, "launcher_mode": "direct"},
                "restart": {"mode": "fresh"},
                "output": {"data_dir": "data", "require_logs": True, "require_settings": True},
                "validation": {
                    "required_variables": [],
                    "metric_thresholds": {"elapsed_seconds": 0.0},
                },
                "timeout_seconds": 300,
            },
        )
    ]
    return {case.case_id: case for case in cases}


def get_boutpp_usage_cases(case_ids: list[str] | None = None) -> list[BenchmarkCaseSpec]:
    catalog = boutpp_usage_case_catalog()
    if case_ids is None:
        return list(catalog.values())
    return [catalog[case_id] for case_id in case_ids]
