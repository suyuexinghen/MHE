from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.capabilities import CAP_NEKTAR_CASE_COMPILE
from metaharness_ext.nektar.contracts import NektarProblemSpec
from metaharness_ext.nektar.slots import NEKTAR_GATEWAY_SLOT
from metaharness_ext.nektar.types import NektarSolverFamily


class NektarGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(NEKTAR_GATEWAY_SLOT)
        api.declare_output("task", "NektarProblemSpec", mode="sync")
        api.provide_capability(CAP_NEKTAR_CASE_COMPILE)

    def issue_task(
        self,
        title: str,
        *,
        task_id: str = "nektar-task-1",
        solver_family: NektarSolverFamily = NektarSolverFamily.ADR,
    ) -> NektarProblemSpec:
        return NektarProblemSpec(
            task_id=task_id,
            title=title,
            solver_family=solver_family,
            dimension=2,
            variables=["u"],
        )
