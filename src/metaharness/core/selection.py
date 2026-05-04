"""Selection lifecycle records for component promotion state."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SelectionStateKind(str, Enum):
    """Lifecycle states for component selection."""

    PROMOTED = "promoted"
    DEPRECATED = "deprecated"
    SUSPENDED = "suspended"
    GRAVEYARD = "graveyard"


class SelectionState(BaseModel):
    """Recorded lifecycle state for a selected component."""

    state_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    component_ref: str
    state: SelectionStateKind
    candidate_id: str | None = None
    graph_version: int | None = None
    reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SelectionLifecycle:
    """In-memory lifecycle service for selection-state evidence."""

    def __init__(self) -> None:
        self._states: dict[str, list[SelectionState]] = {}

    def record(
        self,
        component_ref: str,
        state: SelectionStateKind,
        *,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        reason: str = "",
        evidence_refs: list[str] | None = None,
    ) -> SelectionState:
        selection_state = SelectionState(
            component_ref=component_ref,
            state=state,
            candidate_id=candidate_id,
            graph_version=graph_version,
            reason=reason,
            evidence_refs=list(evidence_refs or []),
        )
        self._states.setdefault(component_ref, []).append(selection_state)
        return selection_state

    def promote(
        self,
        component_ref: str,
        *,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        reason: str = "graph_committed",
        evidence_refs: list[str] | None = None,
    ) -> SelectionState:
        return self.record(
            component_ref,
            SelectionStateKind.PROMOTED,
            candidate_id=candidate_id,
            graph_version=graph_version,
            reason=reason,
            evidence_refs=evidence_refs,
        )

    def deprecate(
        self,
        component_ref: str,
        *,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        reason: str = "deprecated",
        evidence_refs: list[str] | None = None,
    ) -> SelectionState:
        return self.record(
            component_ref,
            SelectionStateKind.DEPRECATED,
            candidate_id=candidate_id,
            graph_version=graph_version,
            reason=reason,
            evidence_refs=evidence_refs,
        )

    def suspend(
        self,
        component_ref: str,
        *,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        reason: str = "suspended",
        evidence_refs: list[str] | None = None,
    ) -> SelectionState:
        return self.record(
            component_ref,
            SelectionStateKind.SUSPENDED,
            candidate_id=candidate_id,
            graph_version=graph_version,
            reason=reason,
            evidence_refs=evidence_refs,
        )

    def graveyard(
        self,
        component_ref: str,
        *,
        candidate_id: str | None = None,
        graph_version: int | None = None,
        reason: str = "graveyard",
        evidence_refs: list[str] | None = None,
    ) -> SelectionState:
        return self.record(
            component_ref,
            SelectionStateKind.GRAVEYARD,
            candidate_id=candidate_id,
            graph_version=graph_version,
            reason=reason,
            evidence_refs=evidence_refs,
        )

    def states_for(self, component_ref: str) -> list[SelectionState]:
        return list(self._states.get(component_ref, []))

    def states(self) -> list[SelectionState]:
        return [state for states in self._states.values() for state in states]

    def latest(self, component_ref: str) -> SelectionState | None:
        states = self._states.get(component_ref, [])
        return states[-1] if states else None
