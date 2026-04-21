"""Migration adapter registry for hot-swap state transforms."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

Adapter = (
    Callable[[Mapping[str, Any], Mapping[str, Any] | None], Mapping[str, Any]]
    | Callable[[Mapping[str, Any], Mapping[str, Any] | None], Awaitable[Mapping[str, Any]]]
)

WILDCARD = "*"


@dataclass(frozen=True, slots=True)
class MigrationAdapterKey:
    """Lookup key for a migration adapter."""

    source_type: str
    source_version: int | None
    target_type: str
    target_version: int | None


class MigrationAdapterRegistry:
    """Registry resolving migration adapters by type/version with fallback."""

    def __init__(self) -> None:
        self._adapters: dict[MigrationAdapterKey, Adapter] = {}

    def register(
        self,
        *,
        source_type: str,
        source_version: int | None,
        target_type: str,
        target_version: int | None,
        adapter: Adapter,
    ) -> None:
        """Register a migration adapter for a source/target type pair."""

        key = MigrationAdapterKey(
            source_type=source_type,
            source_version=source_version,
            target_type=target_type,
            target_version=target_version,
        )
        if key in self._adapters:
            raise ValueError(
                "adapter "
                f"{source_type}@{source_version!r} -> {target_type}@{target_version!r} "
                "already registered"
            )
        self._adapters[key] = adapter

    def register_component_adapter(
        self,
        *,
        component_id: str,
        from_version: int,
        to_version: int,
        adapter: Adapter,
    ) -> None:
        """Register a same-component migration adapter from SDK declarations."""

        self.register(
            source_type=component_id,
            source_version=from_version,
            target_type=component_id,
            target_version=to_version,
            adapter=adapter,
        )

    def register_declarations(self, *, component_id: str, declarations: Any) -> None:
        """Register migration declarations collected through ``HarnessAPI``."""

        for record in declarations.migration_adapters:
            self.register_component_adapter(
                component_id=component_id,
                from_version=record.from_version,
                to_version=record.to_version,
                adapter=record.adapter,
            )

    def resolve(
        self,
        *,
        source_type: str,
        source_version: int,
        target_type: str,
        target_version: int,
        source_family: str | None = None,
        target_family: str | None = None,
    ) -> Adapter | None:
        """Resolve the best matching adapter, preferring exact matches first."""

        for candidate in self._candidate_keys(
            source_type=source_type,
            source_version=source_version,
            target_type=target_type,
            target_version=target_version,
            source_family=source_family,
            target_family=target_family,
        ):
            adapter = self._adapters.get(candidate)
            if adapter is not None:
                return adapter
        return None

    async def migrate(
        self,
        *,
        source_type: str,
        source_version: int,
        target_type: str,
        target_version: int,
        state: Mapping[str, Any],
        delta: Mapping[str, Any] | None = None,
        source_family: str | None = None,
        target_family: str | None = None,
    ) -> dict[str, Any] | None:
        """Run the resolved adapter and return migrated state, if present."""

        adapter = self.resolve(
            source_type=source_type,
            source_version=source_version,
            target_type=target_type,
            target_version=target_version,
            source_family=source_family,
            target_family=target_family,
        )
        if adapter is None:
            return None
        result = adapter(state, delta)
        if inspect.isawaitable(result):
            result = await result
        return dict(result)

    def _candidate_keys(
        self,
        *,
        source_type: str,
        source_version: int,
        target_type: str,
        target_version: int,
        source_family: str | None,
        target_family: str | None,
    ) -> list[MigrationAdapterKey]:
        source_types = self._ordered_types(source_type, source_family)
        target_types = self._ordered_types(target_type, target_family)
        source_versions = [source_version, None]
        target_versions = [target_version, None]

        candidates: list[MigrationAdapterKey] = []
        for candidate_source_type in source_types:
            for candidate_target_type in target_types:
                for candidate_source_version in source_versions:
                    for candidate_target_version in target_versions:
                        candidates.append(
                            MigrationAdapterKey(
                                source_type=candidate_source_type,
                                source_version=candidate_source_version,
                                target_type=candidate_target_type,
                                target_version=candidate_target_version,
                            )
                        )
        return candidates

    def _ordered_types(self, exact: str, family: str | None) -> list[str]:
        ordered: list[str] = [exact]
        if family and family not in ordered:
            ordered.append(family)
        if WILDCARD not in ordered:
            ordered.append(WILDCARD)
        return ordered
