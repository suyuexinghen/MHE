"""Minimal memory component."""

from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class MemoryComponent(HarnessComponent):
    """Stores a simple in-memory event log."""

    def __init__(self) -> None:
        self.records: list[dict[str, str]] = []

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("memory.primary")
        api.declare_input("task_result", "TaskResult")
        api.declare_output("memory_record", "MemoryRecord", mode="async")

    def remember(self, payload: dict[str, str]) -> dict[str, str]:
        self.records.append(payload)
        return {"count": str(len(self.records))}
