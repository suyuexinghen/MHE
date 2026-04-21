"""Minimal gateway component."""

from __future__ import annotations

from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class GatewayComponent(HarnessComponent):
    """Entry point that emits inbound task requests."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot("gateway.primary")
        api.declare_output("task", "TaskRequest", mode="sync")

    def issue_task(
        self,
        task: str,
        *,
        subject_id: str | None = None,
        credentials: dict[str, str] | None = None,
        claims: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"task": task}
        boundary = getattr(getattr(self, "_runtime", None), "identity_boundary", None)
        if boundary is None or subject_id is None:
            return payload
        attestation = boundary.issue_attestation(
            subject_id,
            claims=claims,
            credentials=credentials,
        )
        return boundary.expose_payload(payload, attestation=attestation)
