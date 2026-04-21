"""Append-only Merkle tree for provenance evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(slots=True)
class MerkleNode:
    """A single node in a binary Merkle tree."""

    hash: str
    left: MerkleNode | None = None
    right: MerkleNode | None = None
    payload: bytes | None = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class MerkleTree:
    """Append-only Merkle tree.

    Leaves store arbitrary payload bytes; internal nodes pair-wise hash
    their children. The tree is recomputed lazily on ``root_hash``.
    Suitable for audit-log anchoring of evidence records.
    """

    def __init__(self) -> None:
        self._leaves: list[MerkleNode] = []
        self._cached_root: str | None = None

    # ------------------------------------------------------------- append

    def append(self, payload: bytes | str) -> MerkleNode:
        data = payload.encode() if isinstance(payload, str) else bytes(payload)
        node = MerkleNode(hash=_hash(data), payload=data)
        self._leaves.append(node)
        self._cached_root = None
        return node

    def append_many(self, payloads: list[bytes | str]) -> list[MerkleNode]:
        return [self.append(p) for p in payloads]

    # --------------------------------------------------------------- roots

    def root_hash(self) -> str:
        if not self._leaves:
            return _hash(b"")
        if self._cached_root is not None:
            return self._cached_root

        level: list[MerkleNode] = list(self._leaves)
        while len(level) > 1:
            nxt: list[MerkleNode] = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                combined = (left.hash + right.hash).encode()
                node = MerkleNode(hash=_hash(combined), left=left, right=right)
                nxt.append(node)
            level = nxt
        self._cached_root = level[0].hash
        return self._cached_root

    # ----------------------------------------------------------- inspection

    @property
    def leaves(self) -> list[MerkleNode]:
        return list(self._leaves)

    def __len__(self) -> int:
        return len(self._leaves)

    def proof_for(self, index: int) -> list[tuple[str, str]]:
        """Return a Merkle inclusion proof for the leaf at ``index``.

        Each tuple is ``(sibling_hash, direction)`` where direction is
        ``"left"`` or ``"right"`` describing where the sibling sits relative
        to the hashing pair.
        """

        if not 0 <= index < len(self._leaves):
            raise IndexError("leaf index out of range")
        level_hashes = [leaf.hash for leaf in self._leaves]
        proof: list[tuple[str, str]] = []
        idx = index
        while len(level_hashes) > 1:
            pair_idx = idx ^ 1
            if pair_idx >= len(level_hashes):
                pair_idx = idx
            direction = "right" if idx % 2 == 0 else "left"
            proof.append((level_hashes[pair_idx], direction))
            nxt_hashes: list[str] = []
            for i in range(0, len(level_hashes), 2):
                left = level_hashes[i]
                right = level_hashes[i + 1] if i + 1 < len(level_hashes) else left
                nxt_hashes.append(_hash((left + right).encode()))
            idx //= 2
            level_hashes = nxt_hashes
        return proof

    @staticmethod
    def verify(
        leaf_payload: bytes | str,
        proof: list[tuple[str, str]],
        expected_root: str,
    ) -> bool:
        data = leaf_payload.encode() if isinstance(leaf_payload, str) else bytes(leaf_payload)
        current = _hash(data)
        for sibling, direction in proof:
            if direction == "right":
                current = _hash((current + sibling).encode())
            else:
                current = _hash((sibling + current).encode())
        return current == expected_root
