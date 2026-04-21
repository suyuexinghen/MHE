from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import (
    CAP_BOUNDARY_VALIDATION,
    CAP_REFERENCE_BASELINE,
    CAP_RESIDUAL_VALIDATION,
)
from metaharness_ext.ai4pde.contracts import PDERunArtifact, ReferenceResult, ValidationBundle
from metaharness_ext.ai4pde.slots import PHYSICS_VALIDATOR_SLOT
from metaharness_ext.ai4pde.types import NextAction
from metaharness_ext.ai4pde.validation import (
    compare_against_reference,
    summarize_boundary_conditions,
    summarize_residuals,
)


class PhysicsValidatorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(PHYSICS_VALIDATOR_SLOT)
        api.declare_input("run_artifact", "PDERunArtifact")
        api.declare_output("validation_bundle", "ValidationBundle", mode="sync")
        api.provide_capability(CAP_RESIDUAL_VALIDATION)
        api.provide_capability(CAP_BOUNDARY_VALIDATION)
        api.require_capability(CAP_REFERENCE_BASELINE)

    def validate_run(
        self,
        run_artifact: PDERunArtifact,
        *,
        graph_version_id: int = 1,
        reference_result: ReferenceResult | None = None,
    ) -> ValidationBundle:
        residual_metrics = summarize_residuals(run_artifact)
        boundary_metrics = summarize_boundary_conditions(run_artifact)
        reference_comparison = (
            compare_against_reference(run_artifact, reference_result)
            if reference_result is not None
            else {}
        )
        violations: list[str] = []
        if residual_metrics["residual_ok"] < 1.0:
            violations.append("residual_threshold_exceeded")
        if boundary_metrics["boundary_ok"] < 1.0:
            violations.append("boundary_conditions_failed")
        if reference_comparison.get("status") == "worse_than_baseline":
            violations.append("baseline_divergence_exceeded")
        next_action = NextAction.ACCEPT if not violations else NextAction.RETRY
        return ValidationBundle(
            validation_id=f"validation-{run_artifact.task_id}",
            task_id=run_artifact.task_id,
            graph_version_id=graph_version_id,
            residual_metrics=residual_metrics,
            bc_ic_metrics=boundary_metrics,
            reference_comparison=reference_comparison,
            violations=violations,
            next_action=next_action,
            summary={
                "status": next_action.value,
                "residual_l2": residual_metrics["residual_l2"],
                "boundary_error": boundary_metrics["boundary_error"],
                "reference_status": reference_comparison.get("status", "not_run"),
            },
        )
