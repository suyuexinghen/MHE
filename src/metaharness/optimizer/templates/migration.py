"""Migration adapter system.

Keeps a directed graph of schema migrations so the runtime can evolve
``state_schema_version`` across versions without writing ad-hoc
adapters at every call site. Adapters are callables
``adapter(old_state, delta) -> new_state``; the system finds a path
from ``from_version`` to ``to_version`` and chains them.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

Adapter = Callable[[Mapping[str, Any], Mapping[str, Any] | None], dict[str, Any]]


@dataclass(slots=True)
class MigrationAdapter:
    """A directed adapter between two schema versions."""

    component_id: str
    from_version: int
    to_version: int
    adapter: Adapter


class MigrationAdapterSystem:
    """Registry + chain executor for migration adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, dict[tuple[int, int], MigrationAdapter]] = {}

    # ------------------------------------------------------------- register

    def register(self, adapter: MigrationAdapter) -> None:
        bucket = self._adapters.setdefault(adapter.component_id, {})
        key = (adapter.from_version, adapter.to_version)
        if key in bucket:
            raise ValueError(
                f"adapter {adapter.component_id} {adapter.from_version}->{adapter.to_version} "
                "already registered"
            )
        bucket[key] = adapter

    def adapters_for(self, component_id: str) -> list[MigrationAdapter]:
        return list(self._adapters.get(component_id, {}).values())

    # ------------------------------------------------------------- resolve

    def find_path(
        self, component_id: str, from_version: int, to_version: int
    ) -> list[MigrationAdapter] | None:
        if from_version == to_version:
            return []
        bucket = self._adapters.get(component_id, {})
        if not bucket:
            return None
        # BFS on (from, to) edges.
        queue: deque[tuple[int, list[MigrationAdapter]]] = deque([(from_version, [])])
        seen: set[int] = {from_version}
        while queue:
            version, path = queue.popleft()
            for (src, dst), adapter in bucket.items():
                if src != version or dst in seen:
                    continue
                new_path = [*path, adapter]
                if dst == to_version:
                    return new_path
                seen.add(dst)
                queue.append((dst, new_path))
        return None

    def migrate(
        self,
        component_id: str,
        from_version: int,
        to_version: int,
        state: Mapping[str, Any],
        delta: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = self.find_path(component_id, from_version, to_version)
        if path is None:
            raise LookupError(f"no migration path for {component_id} {from_version}->{to_version}")
        current = dict(state)
        for adapter in path:
            current = adapter.adapter(current, delta)
        return current

    def steps(self, component_id: str, from_version: int, to_version: int) -> list[tuple[int, int]]:
        """Return the (from, to) pairs along the resolved path."""

        path = self.find_path(component_id, from_version, to_version)
        if path is None:
            return []
        return [(a.from_version, a.to_version) for a in path]
