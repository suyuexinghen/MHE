from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import CAP_REFERENCE_BASELINE
from metaharness_ext.ai4pde.contracts import PDEPlan, ReferenceResult
from metaharness_ext.ai4pde.slots import REFERENCE_SOLVER_SLOT


class ReferenceSolverComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(REFERENCE_SOLVER_SLOT)
        api.declare_input("plan", "PDEPlan")
        api.declare_output("reference_result", "ReferenceResult", mode="sync")
        api.provide_capability(CAP_REFERENCE_BASELINE)

    def run_reference(self, plan: PDEPlan) -> ReferenceResult:
        reference_metadata = plan.parameter_overrides.get("reference", {})
        summary = {
            "residual_l2": 0.02,
            "boundary_error": 0.0,
            "solver": "classical_baseline",
        }
        if isinstance(reference_metadata, dict):
            summary.update(reference_metadata)
        return ReferenceResult(
            reference_id=f"reference-{plan.task_id}",
            task_id=plan.task_id,
            artifact_refs=[f"artifact://baseline/{plan.task_id}"],
            benchmark_snapshot_refs=[f"benchmark://{plan.task_id}/baseline"],
            summary=summary,
        )
