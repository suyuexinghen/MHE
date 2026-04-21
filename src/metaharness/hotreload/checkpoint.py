"""Checkpoint capture and restore for component state."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from metaharness.sdk.base import HarnessComponent


@dataclass(slots=True)
class Checkpoint:
    """Immutable snapshot of component state at a point in time."""

    component_id: str
    state_schema_version: int
    state: dict[str, Any]
    created_at: float = field(default_factory=lambda: time.time())
    label: str | None = None


class CheckpointManager:
    """Captures, stores, and restores component checkpoints.

    Storage is in-memory and bounded by ``retention`` per component. The
    manager is intentionally agnostic to persistence backends - callers
    can wrap it with a persistence adapter later.
    """

    def __init__(self, *, retention: int = 16) -> None:
        self.retention = max(1, retention)
        self._store: dict[str, list[Checkpoint]] = {}

    # ------------------------------------------------------------- capture

    async def capture(
        self,
        component: HarnessComponent,
        *,
        component_id: str,
        state_schema_version: int = 1,
        label: str | None = None,
    ) -> Checkpoint:
        state = await component.export_state()
        checkpoint = Checkpoint(
            component_id=component_id,
            state_schema_version=state_schema_version,
            state=dict(state),
            label=label,
        )
        bucket = self._store.setdefault(component_id, [])
        bucket.append(checkpoint)
        if len(bucket) > self.retention:
            del bucket[: len(bucket) - self.retention]
        return checkpoint

    def capture_sync(
        self,
        component: HarnessComponent,
        *,
        component_id: str,
        state_schema_version: int = 1,
        label: str | None = None,
    ) -> Checkpoint:
        return asyncio.run(
            self.capture(
                component,
                component_id=component_id,
                state_schema_version=state_schema_version,
                label=label,
            )
        )

    # ------------------------------------------------------------- restore

    async def restore(self, component: HarnessComponent, checkpoint: Checkpoint) -> None:
        await component.import_state(checkpoint.state)

    def latest(self, component_id: str) -> Checkpoint | None:
        bucket = self._store.get(component_id) or []
        return bucket[-1] if bucket else None

    def history(self, component_id: str) -> list[Checkpoint]:
        return list(self._store.get(component_id) or [])

    def clear(self, component_id: str | None = None) -> None:
        if component_id is None:
            self._store.clear()
        else:
            self._store.pop(component_id, None)
