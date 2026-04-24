"""Minimal gateway component."""

from __future__ import annotations

from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.runtime import ComponentRuntime


class GatewayComponent(HarnessComponent):
    """Entry point that emits inbound task requests."""

    def __init__(self, manifest: ComponentManifest | None = None) -> None:
        self._manifest = manifest
        self._runtime: ComponentRuntime | None = None

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
        runtime = getattr(self, "_runtime", None)
        manifest = getattr(self, "_manifest", None)
        if runtime is not None and manifest is not None:
            runtime.require_credentials(
                subject_id=subject_id,
                credentials=credentials,
                requires_subject=manifest.policy.credentials.requires_subject,
                allow_inline_credentials=manifest.policy.credentials.allow_inline_credentials,
            )
            required_claims = manifest.policy.credentials.required_claims
            if required_claims:
                present_claims = set((claims or {}).keys())
                missing = [claim for claim in required_claims if claim not in present_claims]
                if missing:
                    raise ValueError(
                        "credential policy missing required claims: " + ", ".join(missing)
                    )
        boundary = getattr(runtime, "identity_boundary", None)
        if boundary is None or subject_id is None:
            return payload
        attestation = boundary.issue_attestation(
            subject_id,
            claims=claims,
            credentials=credentials,
        )
        return boundary.expose_payload(payload, attestation=attestation)
