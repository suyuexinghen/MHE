"""Minimal executor component."""

from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class ExecutorComponent(HarnessComponent):
    """Executes a prepared task payload."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("executor.primary")
        api.declare_input("task", "TaskRequest")
        api.declare_output("result", "TaskResult", mode="sync")

    def handle_task(self, payload: dict[str, str]) -> dict[str, str]:
        return {"task": payload["task"], "status": "executed"}
