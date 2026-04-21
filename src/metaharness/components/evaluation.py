"""Minimal evaluation component."""

from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class EvaluationComponent(HarnessComponent):
    """Produces a simple evaluation summary."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("evaluation.primary")
        api.declare_input("task_result", "TaskResult")
        api.declare_output("performance_vector", "PerformanceVector", mode="async")

    def handle_result(self, payload: dict[str, str]) -> dict[str, str]:
        return {"score": "1.0", "source_status": payload["status"]}
