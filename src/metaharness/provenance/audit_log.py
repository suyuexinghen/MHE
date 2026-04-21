"""Append-only audit log with Merkle anchoring."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metaharness.provenance.merkle import MerkleTree


@dataclass(slots=True)
class AuditRecord:
    """Single audit entry."""

    record_id: str
    timestamp: float
    kind: str
    actor: str
    payload: dict[str, Any] = field(default_factory=dict)
    merkle_index: int | None = None
    merkle_root: str | None = None

    def canonical(self) -> str:
        return json.dumps(
            {
                "record_id": self.record_id,
                "timestamp": self.timestamp,
                "kind": self.kind,
                "actor": self.actor,
                "payload": self.payload,
            },
            sort_keys=True,
        )


class AuditLog:
    """In-memory audit log with optional JSONL persistence.

    Every ``append`` anchors the canonical JSON of the record into the
    internal Merkle tree, so callers can produce inclusion proofs and
    verify log integrity against a published root hash.
    """

    def __init__(self, *, path: Path | None = None) -> None:
        self._records: list[AuditRecord] = []
        self._tree = MerkleTree()
        self.path = path

    # ---------------------------------------------------------------- mutate

    def append(
        self,
        kind: str,
        *,
        actor: str,
        payload: dict[str, Any] | None = None,
        timestamp: float | None = None,
    ) -> AuditRecord:
        record = AuditRecord(
            record_id=uuid.uuid4().hex,
            timestamp=timestamp if timestamp is not None else time.time(),
            kind=kind,
            actor=actor,
            payload=dict(payload or {}),
        )
        self._tree.append(record.canonical())
        record.merkle_index = len(self._records)
        record.merkle_root = self._tree.root_hash()
        self._records.append(record)
        if self.path is not None:
            self._write_one(record)
        return record

    def _write_one(self, record: AuditRecord) -> None:
        assert self.path is not None
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            fh.write(
                json.dumps(
                    {
                        "record_id": record.record_id,
                        "timestamp": record.timestamp,
                        "kind": record.kind,
                        "actor": record.actor,
                        "payload": record.payload,
                        "merkle_index": record.merkle_index,
                        "merkle_root": record.merkle_root,
                    }
                )
                + "\n"
            )

    # --------------------------------------------------------------- query

    def __len__(self) -> int:
        return len(self._records)

    def records(self) -> list[AuditRecord]:
        return list(self._records)

    def by_kind(self, kind: str) -> list[AuditRecord]:
        return [r for r in self._records if r.kind == kind]

    def by_actor(self, actor: str) -> list[AuditRecord]:
        return [r for r in self._records if r.actor == actor]

    # ----------------------------------------------------- proof / verify

    @property
    def root_hash(self) -> str:
        return self._tree.root_hash()

    def proof_for(self, record: AuditRecord) -> list[tuple[str, str]]:
        if record.merkle_index is None:
            raise ValueError("record not yet anchored")
        return self._tree.proof_for(record.merkle_index)

    def verify(self, record: AuditRecord) -> bool:
        """Verify ``record`` is present in the log under the *current* root.

        Because the log is append-only, the root hash grows monotonically;
        each entry's saved ``merkle_root`` is the historical root at the
        moment of insertion. The integrity check therefore re-runs the
        inclusion proof against the *current* root, which always includes
        the past.
        """

        if record.merkle_index is None:
            return False
        proof = self.proof_for(record)
        return MerkleTree.verify(record.canonical(), proof, self.root_hash)
