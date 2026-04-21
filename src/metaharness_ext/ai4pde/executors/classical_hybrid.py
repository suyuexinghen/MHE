from __future__ import annotations

from metaharness_ext.ai4pde.contracts import PDEPlan, PDERunArtifact
from metaharness_ext.ai4pde.types import SolverFamily


def run_classical_hybrid(plan: PDEPlan) -> PDERunArtifact:
    requested_artifacts = plan.expected_artifacts or ["solution_field"]
    artifact_refs = [f"artifact://{artifact.replace('/', '_')}/{plan.task_id}" for artifact in requested_artifacts]
    return PDERunArtifact(
        run_id=f"run-{plan.task_id}",
        task_id=plan.task_id,
        solver_family=SolverFamily.CLASSICAL_HYBRID,
        artifact_refs=artifact_refs,
        checkpoint_refs=[f"checkpoint://{plan.task_id}/classical-hybrid"],
        telemetry_refs=[f"telemetry://{plan.task_id}/classical-hybrid"],
        status="executed",
        result_summary={
            "residual_l2": 0.008,
            "boundary_error": 0.0,
            "backend": plan.parameter_overrides.get("backend"),
            "nektar_solver": plan.parameter_overrides.get("nektar_solver"),
            "driver": plan.parameter_overrides.get("driver"),
            "requested_artifacts": requested_artifacts,
        },
    )
