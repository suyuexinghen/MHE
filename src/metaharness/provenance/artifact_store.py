"""Artifact snapshot persistence for run outputs and evidence bundles."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ArtifactSnapshot:
    snapshot_id: str
    artifact_kind: str
    artifact_ref: str
    payload: dict[str, Any]
    created_at: float = field(default_factory=lambda: time.time())
    graph_version: int | None = None
    candidate_id: str | None = None
    parent_snapshot_id: str | None = None


class ArtifactSnapshotStore:
    """Stores immutable artifact snapshots, optionally as append-only JSONL."""

    def __init__(self, *, path: Path | None = None) -> None:
        self.path = path
        self._snapshots: dict[str, ArtifactSnapshot] = {}
        self._history: dict[str, list[str]] = {}

    def save(
        self,
        artifact_kind: str,
        artifact_ref: str,
        payload: dict[str, Any],
        *,
        graph_version: int | None = None,
        candidate_id: str | None = None,
        parent_snapshot_id: str | None = None,
    ) -> ArtifactSnapshot:
        snapshot = ArtifactSnapshot(
            snapshot_id=uuid.uuid4().hex[:16],
            artifact_kind=artifact_kind,
            artifact_ref=artifact_ref,
            payload=dict(payload),
            graph_version=graph_version,
            candidate_id=candidate_id,
            parent_snapshot_id=parent_snapshot_id,
        )
        self._snapshots[snapshot.snapshot_id] = snapshot
        self._history.setdefault(artifact_ref, []).append(snapshot.snapshot_id)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(snapshot)) + "\n")
        return snapshot

    def get(self, snapshot_id: str) -> ArtifactSnapshot | None:
        return self._snapshots.get(snapshot_id)

    def history(self, artifact_ref: str) -> list[ArtifactSnapshot]:
        return [self._snapshots[sid] for sid in self._history.get(artifact_ref, [])]
