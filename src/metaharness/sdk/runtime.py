"""Runtime dependency surface exposed to components."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from metaharness.core.brain import BrainProvider
from metaharness.safety import SandboxTier, parse_sandbox_tier

if TYPE_CHECKING:
    from metaharness.hotreload.migration import MigrationAdapterRegistry


@dataclass(slots=True)
class ComponentRuntime:
    """Controlled runtime injection for component activation and graph access.

    Mirrors the full roadmap / wiki surface. All fields are optional so the
    SDK stays usable in bare tests while production harnesses inject real
    implementations during boot.
    """

    logger: Any | None = None
    config: dict[str, Any] = field(default_factory=dict)
    storage_path: Path | None = None
    metrics: Any | None = None
    trace_store: Any | None = None
    event_bus: Any | None = None
    graph_reader: Any | None = None
    mutation_submitter: Any | None = None
    brain_provider: BrainProvider | None = None
    llm: BrainProvider | Any | None = None
    sandbox_client: Any | None = None
    process_direct: Any | None = None
    tool_execute: Any | None = None
    identity_boundary: Any | None = None
    migration_adapters: "MigrationAdapterRegistry | None" = None

    def resolved_brain_provider(self) -> BrainProvider | Any | None:
        """Return the configured brain provider, preserving current llm fallback."""

        return self.brain_provider or self.llm

    def require_credentials(
        self,
        *,
        subject_id: str | None,
        credentials: dict[str, str] | None,
        requires_subject: bool = False,
        allow_inline_credentials: bool = True,
    ) -> None:
        """Enforce credential policy at the direct task ingress surface."""

        if requires_subject and subject_id is None:
            raise ValueError("credential policy requires subject_id")
        if not allow_inline_credentials and credentials:
            raise ValueError("credential policy forbids inline credentials")

    def require_sandbox_tier(self, declared_tier: SandboxTier | str | None) -> SandboxTier | None:
        """Return a normalized sandbox tier after checking runtime availability."""

        if declared_tier is None:
            return None
        tier = parse_sandbox_tier(declared_tier)
        client = self.sandbox_client
        if client is None:
            return tier
        if hasattr(client, "supports_tier") and not client.supports_tier(tier):
            raise ValueError(f"sandbox policy requires tier '{tier.value}'")
        return tier
