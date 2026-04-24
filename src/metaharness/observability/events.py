"""CMA-inspired session event store for Meta-Harness.

Provides an append-only event log that records graph promotions, safety gate
evaluations, checkpoints, and hot-swap transitions.  The store is the single
source of truth for session replay and crash recovery.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from metaharness.core.models import SessionEvent, SessionEventType


class SessionStore(ABC):
    """Interface for append-only session event persistence."""

    @abstractmethod
    def append(self, event: SessionEvent) -> None:
        """Append an immutable event to the session log."""

    @abstractmethod
    def get_events(
        self,
        session_id: str,
        *,
        after_index: int | None = None,
        event_type: SessionEventType | None = None,
    ) -> list[SessionEvent]:
        """Return events for *session_id*, optionally filtered."""

    @abstractmethod
    def latest_checkpoint_index(self, session_id: str) -> int | None:
        """Return the index of the most recent checkpoint event, or ``None``."""


class InMemorySessionStore(SessionStore):
    """In-memory implementation backed by a plain list."""

    def __init__(self) -> None:
        self._events: dict[str, list[SessionEvent]] = {}

    def append(self, event: SessionEvent) -> None:
        self._events.setdefault(event.session_id, []).append(event)

    def get_events(
        self,
        session_id: str,
        *,
        after_index: int | None = None,
        event_type: SessionEventType | None = None,
    ) -> list[SessionEvent]:
        events = self._events.get(session_id, [])
        if after_index is not None:
            events = events[after_index + 1 :]
        if event_type is not None:
            events = [e for e in events if e.event_type == event_type]
        return list(events)

    def latest_checkpoint_index(self, session_id: str) -> int | None:
        events = self._events.get(session_id, [])
        for i in range(len(events) - 1, -1, -1):
            if events[i].event_type == SessionEventType.CHECKPOINT_SAVED:
                return i
        return None


def make_session_event(
    session_id: str,
    event_type: SessionEventType,
    *,
    graph_version: int | None = None,
    candidate_id: str | None = None,
    payload: dict[str, object] | None = None,
) -> SessionEvent:
    """Convenience factory that auto-generates ``event_id`` and ``timestamp``."""

    return SessionEvent(
        event_id=uuid.uuid4().hex[:16],
        session_id=session_id,
        event_type=event_type,
        graph_version=graph_version,
        candidate_id=candidate_id,
        timestamp=datetime.now(timezone.utc),
        payload=payload or {},
    )
