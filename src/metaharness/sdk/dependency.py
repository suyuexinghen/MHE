"""Dependency resolution using Kahn's topological sort."""

from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable

from metaharness.sdk.manifest import ComponentManifest


class CircularDependencyError(RuntimeError):
    """Raised when a component dependency graph contains a cycle."""

    def __init__(self, cycle: list[str]) -> None:
        super().__init__(f"Circular dependency detected: {' -> '.join(cycle)}")
        self.cycle = list(cycle)


class MissingDependencyError(RuntimeError):
    """Raised when a declared dependency is not available."""

    def __init__(self, component_id: str, missing: str) -> None:
        super().__init__(f"Component '{component_id}' depends on missing '{missing}'")
        self.component_id = component_id
        self.missing = missing


def _build_capability_index(manifests: Iterable[ComponentManifest]) -> dict[str, list[str]]:
    """Map capability name -> list of manifest ids providing it."""

    index: dict[str, list[str]] = defaultdict(list)
    for manifest in manifests:
        for capability in manifest.all_provided_capabilities():
            index[capability].append(manifest.resolved_id())
    return dict(index)


def resolve_boot_order(manifests: Iterable[ComponentManifest]) -> list[ComponentManifest]:
    """Return manifests in a valid activation order.

    Uses Kahn's algorithm so the result is deterministic and detects cycles
    explicitly. Dependencies are expressed via ``deps.components`` (explicit
    component ids) and ``deps.capabilities`` (capabilities resolved through
    each manifest's ``provides`` set). Missing dependencies raise
    :class:`MissingDependencyError`, cycles raise
    :class:`CircularDependencyError`.
    """

    manifests = list(manifests)
    by_id: dict[str, ComponentManifest] = {m.resolved_id(): m for m in manifests}
    capability_index = _build_capability_index(manifests)

    graph: dict[str, set[str]] = defaultdict(set)
    reverse: dict[str, set[str]] = defaultdict(set)
    for manifest in manifests:
        cid = manifest.resolved_id()
        graph.setdefault(cid, set())
        reverse.setdefault(cid, set())
        for dep in manifest.deps.components:
            if dep not in by_id:
                raise MissingDependencyError(cid, dep)
            graph[dep].add(cid)
            reverse[cid].add(dep)
        for capability in manifest.deps.capabilities:
            providers = capability_index.get(capability)
            if not providers:
                raise MissingDependencyError(cid, capability)
            for provider in providers:
                if provider == cid:
                    continue
                graph[provider].add(cid)
                reverse[cid].add(provider)
        for capability in manifest.all_required_capabilities():
            providers = capability_index.get(capability)
            if not providers:
                continue
            for provider in providers:
                if provider == cid:
                    continue
                graph[provider].add(cid)
                reverse[cid].add(provider)

    queue: deque[str] = deque(sorted(cid for cid, preds in reverse.items() if not preds))
    ordered_ids: list[str] = []
    remaining = dict(reverse)
    while queue:
        cid = queue.popleft()
        ordered_ids.append(cid)
        for succ in sorted(graph.get(cid, set())):
            preds = remaining[succ]
            preds.discard(cid)
            if not preds:
                queue.append(succ)

    if len(ordered_ids) != len(by_id):
        cycle_nodes = [cid for cid, preds in remaining.items() if preds]
        raise CircularDependencyError(cycle_nodes)

    return [by_id[cid] for cid in ordered_ids]
