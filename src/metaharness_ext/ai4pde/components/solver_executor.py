from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import CAP_PINN_STRONG, CAP_REFERENCE_BASELINE
from metaharness_ext.ai4pde.contracts import PDEPlan, PDERunArtifact
from metaharness_ext.ai4pde.executors import run_classical_hybrid, run_pinn_strong
from metaharness_ext.ai4pde.slots import SOLVER_EXECUTOR_SLOT
from metaharness_ext.ai4pde.types import SolverFamily


class SolverExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(SOLVER_EXECUTOR_SLOT)
        api.declare_input("plan", "PDEPlan")
        api.declare_output("run_artifact", "PDERunArtifact", mode="sync")
        api.provide_capability(CAP_PINN_STRONG)
        api.provide_capability(CAP_REFERENCE_BASELINE)

    def execute_plan(self, plan: PDEPlan) -> PDERunArtifact:
        if plan.selected_method == SolverFamily.PINN_STRONG:
            return run_pinn_strong(plan)
        if plan.selected_method == SolverFamily.CLASSICAL_HYBRID:
            return run_classical_hybrid(plan)
        raise ValueError(f"Unsupported solver family: {plan.selected_method.value}")
