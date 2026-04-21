"""Contract-driven connection pruning for optimizer search-space reduction."""

from __future__ import annotations

from collections.abc import Iterable

from metaharness.core.port_index import PortIndex, PortRef
from metaharness.sdk.registry import ComponentRegistry


class ContractPruner:
    """Prune candidate connection proposals that cannot possibly be legal.

    The pruner is the defense against search-space explosion in the optimizer:
    given a source output port it returns the subset of input ports whose
    contract/type actually matches, respecting protected components and
    optional deny-listed edges.
    """

    def __init__(
        self,
        registry: ComponentRegistry,
        index: PortIndex | None = None,
        *,
        denied_pairs: Iterable[tuple[str, str]] = (),
    ) -> None:
        self._registry = registry
        self._index = index or PortIndex.from_registry(registry)
        self._denied = {(a, b) for a, b in denied_pairs}

    @property
    def registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def index(self) -> PortIndex:
        return self._index

    def legal_targets(self, source_fqid: str) -> list[PortRef]:
        """Return input ports the optimizer may legally propose as targets."""

        source = self._index.lookup(source_fqid)
        if source is None or source.direction != "output":
            return []
        candidates: list[PortRef] = []
        for target in self._index.all_inputs():
            if target.component_id == source.component_id:
                continue
            if (source.fqid, target.fqid) in self._denied:
                continue
            if not self._type_compatible(source, target):
                continue
            if self._violates_protection(target):
                continue
            candidates.append(target)
        return candidates

    def legal_pairs(self) -> list[tuple[PortRef, PortRef]]:
        """Return all (source, target) pairs the optimizer may propose."""

        pairs: list[tuple[PortRef, PortRef]] = []
        for source in self._index.all_outputs():
            for target in self.legal_targets(source.fqid):
                pairs.append((source, target))
        return pairs

    # ------------------------------------------------------------------ rules

    @staticmethod
    def _type_compatible(source: PortRef, target: PortRef) -> bool:
        return source.payload_type == target.payload_type

    def _violates_protection(self, target: PortRef) -> bool:
        registered = self._registry.components.get(target.component_id)
        if registered is None:
            return False
        if not registered.manifest.safety.protected:
            return False
        # A protected component's primary input is write-gated: the default
        # implementation of contract pruning treats rebinding a protected
        # input as illegal unless the optimizer explicitly requests an
        # override via a proposal reviewed by governance.
        for port in registered.declarations.inputs:
            if port.name == target.port:
                return True
        return False
