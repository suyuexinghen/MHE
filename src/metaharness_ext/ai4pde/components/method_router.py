from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import CAP_PINN_STRONG
from metaharness_ext.ai4pde.contracts import PDEPlan, PDETaskRequest
from metaharness_ext.ai4pde.slots import METHOD_ROUTER_SLOT, SOLVER_EXECUTOR_SLOT
from metaharness_ext.ai4pde.templates.instantiation import (
    apply_template_to_plan,
    instantiate_template_for_task,
)
from metaharness_ext.ai4pde.types import SolverFamily


class MethodRouterComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(METHOD_ROUTER_SLOT)
        api.declare_input("task", "PDETaskRequest")
        api.declare_output("plan", "PDEPlan", mode="sync")
        api.require_capability(CAP_PINN_STRONG)

    def build_plan(self, request: PDETaskRequest) -> PDEPlan:
        planning_data = request.data_spec.get("planning", {})
        compiled_plan = PDEPlan.model_validate(planning_data) if planning_data else None
        base_plan = compiled_plan or PDEPlan(
            plan_id=f"plan-{request.task_id}",
            task_id=request.task_id,
            selected_method=SolverFamily.PINN_STRONG,
            graph_family="ai4pde-minimal",
            slot_bindings={SOLVER_EXECUTOR_SLOT: SolverFamily.PINN_STRONG.value},
            required_validators=["residuals", "boundary_conditions"],
            expected_artifacts=["solution_field", "validation_bundle", "evidence_bundle"],
        )
        template, template_data = instantiate_template_for_task(request)
        return apply_template_to_plan(base_plan, template, template_data)
