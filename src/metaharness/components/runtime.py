"""Minimal runtime component."""

from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class RuntimeComponent(HarnessComponent):
    """Receives tasks and emits runtime results."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("runtime.primary")
        api.declare_input("task", "TaskRequest")
        api.declare_output("result", "TaskRequest", mode="sync")

    def handle_task(self, payload: dict[str, str]) -> dict[str, str]:
        return {"task": payload["task"], "status": "runtime-ok"}
