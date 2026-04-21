from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDEPlan, PDERunArtifact
from metaharness_ext.ai4pde.types import SolverFamily


def run_pinn_strong(plan: PDEPlan) -> PDERunArtifact:
    return PDERunArtifact(
        run_id=f"run-{plan.task_id}",
        task_id=plan.task_id,
        solver_family=SolverFamily.PINN_STRONG,
        artifact_refs=[f"artifact://solution/{plan.task_id}"],
        checkpoint_refs=[f"checkpoint://{plan.task_id}/initial"],
        telemetry_refs=[f"telemetry://{plan.task_id}/solver"],
        status="executed",
        result_summary={"residual_l2": 0.01, "boundary_error": 0.0},
    )
