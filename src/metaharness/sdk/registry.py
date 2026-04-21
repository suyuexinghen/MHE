"""Staged component registry for Meta-Harness."""

from __future__ import annotations

from pydantic import BaseModel, Field

from metaharness.core.models import GraphSnapshot, PendingMutation
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.models import PendingDeclarations


class RegistrationConflictError(RuntimeError):
    """Raised when registering a component would conflict with an existing one."""

    def __init__(self, component_id: str, reason: str) -> None:
        super().__init__(f"Registration conflict for '{component_id}': {reason}")
        self.component_id = component_id
        self.reason = reason


class RegisteredComponent(BaseModel):
    """A statically declared component in the registry."""

    component_id: str
    manifest: ComponentManifest
    declarations: PendingDeclarations


class ComponentRegistry(BaseModel):
    """Registry holding declared components and graph metadata.

    The registry supports a staged *pending zone* so that boot orchestration
    can validate a full component set before any mutation becomes visible to
    readers of the registry. Call :meth:`stage`, then :meth:`commit_pending`
    or :meth:`abort_pending` to atomically apply or discard a batch.
    """

    components: dict[str, RegisteredComponent] = Field(default_factory=dict)
    slot_bindings: dict[str, list[str]] = Field(default_factory=dict)
    capability_index: dict[str, list[str]] = Field(default_factory=dict)
    candidate_graph: GraphSnapshot | None = None
    active_graph: GraphSnapshot | None = None
    graph_versions: list[int] = Field(default_factory=list)
    pending_mutations: list[PendingMutation] = Field(default_factory=list)
    pending: dict[str, RegisteredComponent] = Field(default_factory=dict)

    # ------------------------------------------------------------------ core

    def register(
        self,
        component_id: str,
        manifest: ComponentManifest,
        declarations: PendingDeclarations,
    ) -> None:
        """Register a component declaration directly into the registry."""

        self._check_no_conflict(component_id, manifest, declarations)
        self._insert(
            RegisteredComponent(
                component_id=component_id,
                manifest=manifest,
                declarations=declarations,
            )
        )

    def unregister(self, component_id: str) -> None:
        """Remove a component declaration and its slot/capability bindings."""

        registered = self.components.pop(component_id, None)
        if registered is None:
            return
        for slot in registered.declarations.slots:
            bound = self.slot_bindings.get(slot.slot)
            if bound and component_id in bound:
                bound.remove(component_id)
                if not bound:
                    self.slot_bindings.pop(slot.slot, None)
        for capability in registered.declarations.provides:
            bound = self.capability_index.get(capability.name)
            if bound and component_id in bound:
                bound.remove(component_id)
                if not bound:
                    self.capability_index.pop(capability.name, None)

    # ---------------------------------------------------------------- staging

    def stage(
        self,
        component_id: str,
        manifest: ComponentManifest,
        declarations: PendingDeclarations,
    ) -> None:
        """Add a component to the pending zone without publishing it."""

        if component_id in self.pending:
            raise RegistrationConflictError(component_id, "already in pending zone")
        self._check_no_conflict(component_id, manifest, declarations, include_pending=True)
        self.pending[component_id] = RegisteredComponent(
            component_id=component_id,
            manifest=manifest,
            declarations=declarations,
        )

    def abort_pending(self) -> None:
        """Discard all pending registrations."""

        self.pending.clear()

    def commit_pending(self) -> list[str]:
        """Move the pending zone into the live registry atomically."""

        committed_ids = sorted(self.pending.keys())
        for component_id, registered in self.pending.items():
            self._insert(registered)
        self.pending.clear()
        return committed_ids

    # -------------------------------------------------------------- lookups

    def components_by_slot(self, slot: str) -> list[str]:
        """Return component ids bound to ``slot``."""

        return list(self.slot_bindings.get(slot, []))

    def components_for_capability(self, capability: str) -> list[str]:
        """Return component ids providing ``capability``."""

        return list(self.capability_index.get(capability, []))

    def is_protected(self, component_id: str) -> bool:
        """Return whether a registered component is protected by its manifest."""

        registered = self.components.get(component_id)
        if registered is None:
            return False
        return bool(registered.manifest.safety.protected)

    def record_graph_version(self, version: int) -> None:
        """Track a new committed graph version."""

        self.graph_versions.append(version)

    def record_pending_mutation(self, mutation: PendingMutation) -> None:
        """Track a pending mutation proposal."""

        self.pending_mutations.append(mutation)

    # ---------------------------------------------------------------- internal

    def _insert(self, registered: RegisteredComponent) -> None:
        self.components[registered.component_id] = registered
        for slot in registered.declarations.slots:
            bound = self.slot_bindings.setdefault(slot.slot, [])
            if registered.component_id not in bound:
                bound.append(registered.component_id)
        for capability in registered.declarations.provides:
            bound = self.capability_index.setdefault(capability.name, [])
            if registered.component_id not in bound:
                bound.append(registered.component_id)

    def _check_no_conflict(
        self,
        component_id: str,
        manifest: ComponentManifest,
        declarations: PendingDeclarations,
        *,
        include_pending: bool = False,
    ) -> None:
        if component_id in self.components:
            raise RegistrationConflictError(component_id, "duplicate component id")
        if include_pending and component_id in self.pending:
            raise RegistrationConflictError(component_id, "duplicate component id in pending zone")
        # Note: multiple components may claim the same primary slot. The
        # semantic validator rejects such overlaps on protected components
        # when staging a candidate graph; registration itself does not block
        # them so the validator can emit richer diagnostics.


def filter_enabled(
    manifests: list[ComponentManifest],
    *,
    config: dict[str, dict[str, object]] | None = None,
) -> list[ComponentManifest]:
    """Return manifests whose config allows them to be booted.

    ``config`` is a map ``component_id -> {"enabled": bool}``. If a manifest is
    absent from ``config`` its own ``manifest.enabled`` field is honoured.
    """

    config = config or {}
    result: list[ComponentManifest] = []
    for manifest in manifests:
        cid = manifest.resolved_id()
        override = config.get(cid)
        if override is not None and override.get("enabled") is False:
            continue
        if not manifest.enabled:
            continue
        result.append(manifest)
    return result
