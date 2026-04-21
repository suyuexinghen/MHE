from __future__ import annotations

from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import CAP_PINN_STRONG
from metaharness_ext.ai4pde.case_parser import parse_ai4pde_case_xml
from metaharness_ext.ai4pde.contracts import PDEPlan, PDETaskRequest
from metaharness_ext.ai4pde.slots import PDE_GATEWAY_SLOT
from metaharness_ext.ai4pde.types import ProblemType, RiskLevel


class PDEGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(PDE_GATEWAY_SLOT)
        api.declare_output("task", "PDETaskRequest", mode="sync")
        api.provide_capability(CAP_PINN_STRONG)

    def issue_task(self, goal: str, *, task_id: str = "pde-task-1") -> PDETaskRequest:
        return PDETaskRequest(
            task_id=task_id,
            goal=goal,
            problem_type=ProblemType.FORWARD,
            physics_spec={"equation": "-∇²u = 0", "dimension": 2},
            geometry_spec={"domain": "unit-square", "representation": "analytic"},
            data_spec={"observations": []},
            deliverables=["solution_field", "validation_summary", "evidence_bundle"],
            risk_level=RiskLevel.GREEN,
        )

    def issue_task_from_case(self, path: str | Path) -> tuple[PDETaskRequest, PDEPlan]:
        return parse_ai4pde_case_xml(path)
