from __future__ import annotations

from metaharness_ext.ai4pde.contracts import BudgetRecord


def check_budget(budget: BudgetRecord) -> dict[str, float | bool]:
    within_limits = (
        budget.gpu_hours <= 8.0
        and budget.cpu_hours <= 48.0
        and budget.walltime_hours <= 24.0
        and budget.hpc_quota <= 1.0
    )
    return {
        "within_limits": within_limits,
        "gpu_hours": budget.gpu_hours,
        "cpu_hours": budget.cpu_hours,
        "walltime_hours": budget.walltime_hours,
        "hpc_quota": budget.hpc_quota,
    }


def classify_budget(budget: BudgetRecord) -> str:
    if budget.gpu_hours > 8.0 or budget.hpc_quota > 1.0:
        return "red"
    if budget.gpu_hours > 2.0 or budget.walltime_hours > 8.0:
        return "yellow"
    return "green"
