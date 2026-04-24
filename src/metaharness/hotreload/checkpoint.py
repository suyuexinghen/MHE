"""Checkpoint capture and restore for component state."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from metaharness.core.models import SessionEventType
from metaharness.observability.events import SessionStore, make_session_event
from metaharness.provenance import AuditLog, ProvGraph, RelationKind
from metaharness.sdk.base import HarnessComponent


@dataclass(slots=True)
class Checkpoint:
    """Immutable snapshot of component state at a point in time."""

    checkpoint_id: str
    component_id: str
    state_schema_version: int
    state: dict[str, Any]
    created_at: float = field(default_factory=lambda: time.time())
    label: str | None = None
    parent_checkpoint_id: str | None = None
    evidence_refs: list[str] = field(default_factory=list)


class CheckpointManager:
    """Captures, stores, and restores component checkpoints.

    Storage is in-memory and bounded by ``retention`` per component. The
    manager is intentionally agnostic to persistence backends - callers
    can wrap it with a persistence adapter later.
    """

    def __init__(self, *, retention: int = 16) -> None:
        self.retention = max(1, retention)
        self._store: dict[str, list[Checkpoint]] = {}
        self.session_id: str | None = None
        self.session_store: SessionStore | None = None
        self.audit_log: AuditLog | None = None
        self.provenance_graph: ProvGraph | None = None

    def bind_evidence_runtime(
        self,
        *,
        session_id: str,
        session_store: SessionStore | None = None,
        audit_log: AuditLog | None = None,
        provenance_graph: ProvGraph | None = None,
    ) -> None:
        """Attach optional session-evidence sinks for checkpoint capture."""

        self.session_id = session_id
        self.session_store = session_store
        self.audit_log = audit_log
        self.provenance_graph = provenance_graph

    # ------------------------------------------------------------- capture

    async def capture(
        self,
        component: HarnessComponent,
        *,
        component_id: str,
        state_schema_version: int = 1,
        label: str | None = None,
        graph_version: int | None = None,
        candidate_id: str | None = None,
    ) -> Checkpoint:
        state = await component.export_state()
        parent = self.latest(component_id)
        checkpoint = Checkpoint(
            checkpoint_id=uuid.uuid4().hex[:16],
            component_id=component_id,
            state_schema_version=state_schema_version,
            state=dict(state),
            label=label,
            parent_checkpoint_id=None if parent is None else parent.checkpoint_id,
        )
        bucket = self._store.setdefault(component_id, [])
        bucket.append(checkpoint)
        if len(bucket) > self.retention:
            del bucket[: len(bucket) - self.retention]
        self._record_capture_evidence(
            checkpoint,
            graph_version=graph_version,
            candidate_id=candidate_id,
        )
        return checkpoint

    def capture_sync(
        self,
        component: HarnessComponent,
        *,
        component_id: str,
        state_schema_version: int = 1,
        label: str | None = None,
        graph_version: int | None = None,
        candidate_id: str | None = None,
    ) -> Checkpoint:
        return asyncio.run(
            self.capture(
                component,
                component_id=component_id,
                state_schema_version=state_schema_version,
                label=label,
                graph_version=graph_version,
                candidate_id=candidate_id,
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

    def _record_capture_evidence(
        self,
        checkpoint: Checkpoint,
        *,
        graph_version: int | None,
        candidate_id: str | None,
    ) -> None:
        if self.session_id is not None and self.session_store is not None:
            event = make_session_event(
                self.session_id,
                SessionEventType.CHECKPOINT_SAVED,
                graph_version=graph_version,
                candidate_id=candidate_id,
                payload={
                    "component_id": checkpoint.component_id,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "parent_checkpoint_id": checkpoint.parent_checkpoint_id,
                    "state_schema_version": checkpoint.state_schema_version,
                    "label": checkpoint.label,
                },
            )
            self.session_store.append(event)
            checkpoint.evidence_refs.append(f"session-event:{event.event_id}")

            if self.provenance_graph is not None:
                checkpoint_entity = self.provenance_graph.add_entity(
                    id=f"checkpoint:{checkpoint.checkpoint_id}",
                    kind="checkpoint",
                    component_id=checkpoint.component_id,
                    checkpoint_id=checkpoint.checkpoint_id,
                    parent_checkpoint_id=checkpoint.parent_checkpoint_id,
                    state_schema_version=checkpoint.state_schema_version,
                    label=checkpoint.label,
                )
                event_entity = self.provenance_graph.add_entity(
                    id=f"session-event:{event.event_id}",
                    kind="session_event",
                    event_type=event.event_type.value,
                    session_id=event.session_id,
                    candidate_id=event.candidate_id,
                    graph_version=event.graph_version,
                    payload=event.payload,
                    timestamp=event.timestamp.isoformat(),
                )
                self.provenance_graph.relate(
                    event_entity.id,
                    RelationKind.WAS_DERIVED_FROM,
                    checkpoint_entity.id,
                )
                if checkpoint.parent_checkpoint_id is not None:
                    self.provenance_graph.relate(
                        checkpoint_entity.id,
                        RelationKind.WAS_DERIVED_FROM,
                        f"checkpoint:{checkpoint.parent_checkpoint_id}",
                    )

        if self.audit_log is not None:
            record = self.audit_log.append(
                "session.checkpoint_saved",
                actor="hotreload",
                payload={
                    "component_id": checkpoint.component_id,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "parent_checkpoint_id": checkpoint.parent_checkpoint_id,
                    "graph_version": graph_version,
                    "candidate_id": candidate_id,
                },
            )
            checkpoint.evidence_refs.append(f"audit-record:{record.record_id}")
