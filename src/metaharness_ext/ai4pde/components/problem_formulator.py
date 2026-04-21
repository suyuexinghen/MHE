from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.contracts import PDETaskRequest
from metaharness_ext.ai4pde.slots import PROBLEM_FORMULATOR_SLOT


class ProblemFormulatorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(PROBLEM_FORMULATOR_SLOT)
        api.declare_input("task", "PDETaskRequest")
        api.declare_output("formulated_task", "PDETaskRequest", mode="sync")

    def formulate(self, request: PDETaskRequest) -> PDETaskRequest:
        enriched = request.model_copy(deep=True)
        enriched.physics_spec.setdefault("boundary_conditions", [])
        enriched.physics_spec.setdefault("regime", "steady")
        enriched.geometry_spec.setdefault("resolution", "coarse")
        return enriched
