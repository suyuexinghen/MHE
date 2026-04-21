"""Multi-source component manifest discovery."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from metaharness.sdk.manifest import ComponentManifest


class DiscoverySource(IntEnum):
    """Source of a discovered manifest, ordered by priority (higher wins)."""

    BUNDLED = 10
    TEMPLATE = 20
    MARKET = 30
    CUSTOM = 40


@dataclass(slots=True)
class DiscoveredManifest:
    """A manifest found at a specific path with source/priority info."""

    manifest: ComponentManifest
    path: Path
    source: DiscoverySource

    @property
    def identity(self) -> str:
        return self.manifest.resolved_id()


@dataclass(slots=True)
class DiscoveryResult:
    """Result of a discovery pass.

    ``winners`` is the deduplicated list of highest-priority manifests per
    identity. ``overridden`` lists manifests that were replaced by a
    higher-priority source (useful for audit/debug output).
    """

    winners: list[DiscoveredManifest]
    overridden: list[DiscoveredManifest]


def discover_manifest_paths(root: Path) -> list[Path]:
    """Return sorted JSON manifest paths under a root directory."""

    if not root.exists():
        return []
    return sorted(root.rglob("*.json"))


async def discover_manifest_paths_async(root: Path) -> list[Path]:
    """Async variant of :func:`discover_manifest_paths`."""

    return await asyncio.to_thread(discover_manifest_paths, root)


def _load_manifest(path: Path) -> ComponentManifest | None:
    try:
        return ComponentManifest.model_validate(json.loads(path.read_text()))
    except (json.JSONDecodeError, ValueError):
        return None


class ComponentDiscovery:
    """Multi-source discovery with priority-override conflict resolution.

    The four canonical sources from the roadmap map to explicit roots:

    - ``bundled``  - components shipped inside the package/product
    - ``templates`` - template library entries
    - ``market``   - third-party marketplace components
    - ``custom``   - workspace or user-defined components

    Custom sources have the highest priority, so a workspace override cleanly
    replaces a bundled default without edits to the package.
    """

    def __init__(
        self,
        *,
        bundled: Path | None = None,
        templates: Path | None = None,
        market: Path | None = None,
        custom: Path | None = None,
    ) -> None:
        self._roots: dict[DiscoverySource, Path | None] = {
            DiscoverySource.BUNDLED: bundled,
            DiscoverySource.TEMPLATE: templates,
            DiscoverySource.MARKET: market,
            DiscoverySource.CUSTOM: custom,
        }

    def sources(self) -> dict[DiscoverySource, Path | None]:
        return dict(self._roots)

    def scan_bundled(self) -> list[DiscoveredManifest]:
        return self._scan(DiscoverySource.BUNDLED)

    def scan_templates(self) -> list[DiscoveredManifest]:
        return self._scan(DiscoverySource.TEMPLATE)

    def scan_market(self) -> list[DiscoveredManifest]:
        return self._scan(DiscoverySource.MARKET)

    def scan_custom(self) -> list[DiscoveredManifest]:
        return self._scan(DiscoverySource.CUSTOM)

    def scan_all(self) -> list[DiscoveredManifest]:
        found: list[DiscoveredManifest] = []
        for source in DiscoverySource:
            found.extend(self._scan(source))
        return found

    def resolve(self) -> DiscoveryResult:
        """Deduplicate by manifest identity using source priority."""

        winners: dict[str, DiscoveredManifest] = {}
        overridden: list[DiscoveredManifest] = []
        for found in self.scan_all():
            identity = found.identity
            existing = winners.get(identity)
            if existing is None or found.source > existing.source:
                if existing is not None:
                    overridden.append(existing)
                winners[identity] = found
            else:
                overridden.append(found)
        return DiscoveryResult(
            winners=sorted(winners.values(), key=lambda d: d.identity),
            overridden=overridden,
        )

    def _scan(self, source: DiscoverySource) -> list[DiscoveredManifest]:
        root = self._roots.get(source)
        if root is None:
            return []
        results: list[DiscoveredManifest] = []
        for path in discover_manifest_paths(root):
            manifest = _load_manifest(path)
            if manifest is None:
                continue
            results.append(DiscoveredManifest(manifest=manifest, path=path, source=source))
        return results
