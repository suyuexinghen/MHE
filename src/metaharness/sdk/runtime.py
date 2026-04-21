"""Runtime dependency surface exposed to components."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

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
    llm: Any | None = None
    sandbox_client: Any | None = None
    process_direct: Any | None = None
    tool_execute: Any | None = None
    identity_boundary: Any | None = None
    migration_adapters: "MigrationAdapterRegistry | None" = None
