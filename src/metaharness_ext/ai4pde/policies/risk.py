from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDEPlan, PDETaskRequest
from metaharness_ext.ai4pde.types import RiskLevel, SolverFamily


def classify_risk(request: PDETaskRequest, plan: PDEPlan | None = None) -> RiskLevel:
    if request.budget.hpc_quota > 0 or request.budget.gpu_hours > 8.0:
        return RiskLevel.RED
    selected_method = plan.selected_method if plan is not None else None
    if request.problem_type.value == "inverse" or selected_method == SolverFamily.CLASSICAL_HYBRID:
        return RiskLevel.YELLOW
    return request.risk_level
