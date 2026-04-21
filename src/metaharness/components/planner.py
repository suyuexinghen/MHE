"""Minimal planner component."""

from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class PlannerComponent(HarnessComponent):
    """Turns a task request into a planned task."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("planner.primary")
        api.declare_input("task", "TaskRequest")
        api.declare_output("plan", "TaskRequest", mode="sync")

    def make_plan(self, payload: dict[str, str]) -> dict[str, str]:
        return {"task": payload["task"], "plan": "basic"}
