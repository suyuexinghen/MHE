"""Graph version storage, lifecycle, and retirement."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from metaharness.core.models import GraphSnapshot, GraphState, ValidationReport


class ExternalCandidateReviewState(str, Enum):
    """Runtime review outcome for an externally-produced candidate."""

    ADOPTED = "adopted"
    REJECTED = "rejected"


class ExternalCandidateReview(BaseModel):
    """Higher-level runtime review state for external candidates."""

    state: ExternalCandidateReviewState
    reviewer: str = "extension_governance"
    source: str = "external_candidate_record"
    reason: str | None = None


class CandidateRecord(BaseModel):
    """Stored candidate evaluation result."""

    candidate_id: str
    snapshot: GraphSnapshot
    report: ValidationReport
    promoted: bool = False
    external_review: ExternalCandidateReview | None = None


class GraphVersionStore(BaseModel):
    """In-memory graph version store for early milestones.

    Maintains the ``candidate -> active -> rollback_target -> archived``
    lifecycle required by the roadmap. Retirement is driven by
    ``retention``: when the number of live snapshots exceeds the retention
    window the oldest non-active / non-rollback snapshot is archived.
    """

    state: GraphState = Field(default_factory=GraphState)
    snapshots: dict[int, GraphSnapshot] = Field(default_factory=dict)
    archived: dict[int, GraphSnapshot] = Field(default_factory=dict)
    candidates: list[CandidateRecord] = Field(default_factory=list)
    retention: int = 50

    def next_version(self) -> int:
        """Return the next available graph version."""

        known = set(self.snapshots) | set(self.archived)
        if not known:
            return 1
        return max(known) + 1

    def save_candidate(self, candidate: CandidateRecord) -> None:
        """Store a candidate validation result."""

        self.candidates.append(candidate)

    def commit(self, snapshot: GraphSnapshot) -> None:
        """Promote a validated snapshot to active state."""

        previous = self.state.active_graph_version
        if previous is not None:
            self.state.rollback_graph_version = previous
        self.snapshots[snapshot.graph_version] = snapshot
        self.state.active_graph_version = snapshot.graph_version
        self._retire()

    def rollback(self) -> GraphSnapshot:
        """Restore the previous committed snapshot."""

        rollback_version = self.state.rollback_graph_version
        if rollback_version is None:
            raise ValueError("No rollback graph version is available")
        rollback_snapshot = self.snapshots.get(rollback_version) or self.archived.get(
            rollback_version
        )
        if rollback_snapshot is None:
            raise ValueError(f"Rollback graph version {rollback_version} missing from store")
        # Restore snapshot into the active pool if it had been archived.
        self.snapshots[rollback_version] = rollback_snapshot
        self.archived.pop(rollback_version, None)
        self.state.active_graph_version = rollback_version
        # The version we were on becomes a rollback candidate for the next
        # failed commit. Clear the slot so we don't double-rollback.
        self.state.rollback_graph_version = None
        return rollback_snapshot

    # ------------------------------------------------------------------ intent

    def _retire(self) -> None:
        """Archive snapshots outside the retention window.

        The active version and the current rollback target are always kept.
        """

        if self.retention <= 0:
            return
        # The active version must always stay live; the rollback target may
        # be archived because rollback() rehydrates it on demand.
        protected = (
            {self.state.active_graph_version}
            if self.state.active_graph_version is not None
            else set()
        )
        live = sorted(self.snapshots.keys())
        while len(live) > self.retention:
            victim = next((v for v in live if v not in protected), None)
            if victim is None:
                break
            snapshot = self.snapshots.pop(victim)
            self.archived[victim] = snapshot
            if victim not in self.state.archived_graph_versions:
                self.state.archived_graph_versions.append(victim)
            live.remove(victim)

    def retire_to(self, keep: int) -> None:
        """Force retention window to ``keep`` and archive extras."""

        self.retention = max(0, keep)
        self._retire()


class GraphVersionManager:
    """High-level wrapper tracking candidate/active/rollback/archived graphs.

    This is the public surface called for by the roadmap. It sits on top of
    :class:`GraphVersionStore` and exposes a minimal ergonomic API for the
    HarnessRuntime boot orchestrator and the ConnectionEngine.
    """

    def __init__(self, store: GraphVersionStore | None = None, *, retention: int = 50) -> None:
        self._store = store or GraphVersionStore()
        if self._store.retention != retention:
            self._store.retention = retention

    # ------------------------------------------------------------------ delegates

    @property
    def store(self) -> GraphVersionStore:
        return self._store

    @property
    def state(self) -> GraphState:
        return self._store.state

    @property
    def active_version(self) -> int | None:
        return self._store.state.active_graph_version

    @property
    def rollback_target(self) -> int | None:
        return self._store.state.rollback_graph_version

    @property
    def archived_versions(self) -> list[int]:
        return list(self._store.state.archived_graph_versions)

    @property
    def snapshots(self) -> dict[int, GraphSnapshot]:
        return dict(self._store.snapshots)

    @property
    def candidates(self) -> list[CandidateRecord]:
        return list(self._store.candidates)

    # --------------------------------------------------------------- actions

    def next_version(self) -> int:
        return self._store.next_version()

    def save_candidate(self, record: CandidateRecord) -> None:
        self._store.save_candidate(record)

    def cutover(self, snapshot: GraphSnapshot) -> int:
        """Atomically promote ``snapshot`` to the active version."""

        self._store.commit(snapshot)
        return snapshot.graph_version

    def rollback(self) -> GraphSnapshot:
        return self._store.rollback()

    def retire_to(self, keep: int) -> None:
        self._store.retire_to(keep)

    def active_snapshot(self) -> GraphSnapshot | None:
        version = self.active_version
        if version is None:
            return None
        return self._store.snapshots.get(version) or self._store.archived.get(version)
