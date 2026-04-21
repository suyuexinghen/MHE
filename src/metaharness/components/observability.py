"""Minimal observability component."""

from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class ObservabilityComponent(HarnessComponent):
    """Captures audit-style events for MVP validation."""

    def __init__(self) -> None:
        self.events: list[dict[str, str]] = []

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("observability.primary")
        api.declare_event("audit", "AuditEvent")

    def record_event(self, event_type: str, subject: str, trace_id: str) -> dict[str, str]:
        event = {"event_type": event_type, "subject": subject, "trace_id": trace_id}
        self.events.append(event)
        return event
