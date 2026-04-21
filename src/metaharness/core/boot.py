"""HarnessRuntime boot orchestrator.

Wires discovery -> static validation -> dependency resolution ->
registration -> graph staging into a single entry point.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.event_bus import EventBus
from metaharness.core.graph_versions import GraphVersionManager, GraphVersionStore
from metaharness.core.lifecycle_tracker import LifecycleTracker
from metaharness.core.models import PendingConnectionSet
from metaharness.core.mutation import MutationSubmitter
from metaharness.core.port_index import PortIndex, RouteTable
from metaharness.hotreload.migration import MigrationAdapterRegistry
from metaharness.identity import InMemoryIdentityBoundary
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.dependency import resolve_boot_order
from metaharness.sdk.discovery import ComponentDiscovery, DiscoveryResult
from metaharness.sdk.lifecycle import ComponentPhase
from metaharness.sdk.loader import declare_component, validate_manifest_static
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.registry import ComponentRegistry, filter_enabled
from metaharness.sdk.runtime import ComponentRuntime


@dataclass(slots=True)
class BootReport:
    """Summary of a single boot run."""

    discovery: DiscoveryResult
    booted_ids: list[str]
    skipped_ids: list[str] = field(default_factory=list)
    overridden_ids: list[str] = field(default_factory=list)
    validation_issues: dict[str, list[str]] = field(default_factory=dict)
    active_graph_version: int | None = None


class HarnessRuntime:
    """Top-level orchestrator that turns discovery results into a running graph.

    The runtime itself remains deliberately thin: it composes discovery,
    loader, dependency resolver, registry, connection engine, graph version
    manager, and the mutation submitter. Components wired by :meth:`boot`
    are ready to participate in candidate graph staging immediately.
    """

    def __init__(
        self,
        discovery: ComponentDiscovery,
        *,
        registry: ComponentRegistry | None = None,
        version_store: GraphVersionStore | None = None,
        event_bus: EventBus | None = None,
        runtime_factory: Callable[[ComponentManifest], ComponentRuntime] | None = None,
        enabled_overrides: dict[str, dict[str, object]] | None = None,
        instance_suffix: str = ".primary",
    ) -> None:
        self.discovery = discovery
        self.registry = registry or ComponentRegistry()
        self.version_manager = GraphVersionManager(version_store or GraphVersionStore())
        self.engine = ConnectionEngine(self.registry, self.version_manager.store)
        self.event_bus = event_bus or EventBus()
        self.lifecycle = LifecycleTracker()
        self.submitter = MutationSubmitter(engine=self.engine)
        self.migration_adapters = MigrationAdapterRegistry()
        self.components: dict[str, HarnessComponent] = {}
        self._default_identity_boundary = InMemoryIdentityBoundary()
        self._runtime_factory = runtime_factory
        self._enabled_overrides = enabled_overrides or {}
        self._instance_suffix = instance_suffix

    def _instance_id(self, manifest: ComponentManifest) -> str:
        base = manifest.resolved_id()
        if not self._instance_suffix or base.endswith(self._instance_suffix):
            return base
        return f"{base}{self._instance_suffix}"

    # ------------------------------------------------------------------ boot

    def boot(self) -> BootReport:
        """Run the full discovery -> registration pipeline.

        Returns a :class:`BootReport` summarising what happened. Does not
        commit a graph - callers use :meth:`commit_graph` afterwards to
        stage and commit a specific topology.
        """

        resolution = self.discovery.resolve()
        winners = [found.manifest for found in resolution.winners]
        overridden_ids = [found.identity for found in resolution.overridden]
        enabled = filter_enabled(winners, config=self._enabled_overrides)
        skipped_ids = [m.resolved_id() for m in winners if m not in enabled]

        validation_issues: dict[str, list[str]] = {}
        valid_manifests: list[ComponentManifest] = []
        for manifest in enabled:
            issues = validate_manifest_static(manifest)
            if issues:
                validation_issues[manifest.resolved_id()] = issues
                continue
            valid_manifests.append(manifest)

        ordered = resolve_boot_order(valid_manifests)

        booted_ids: list[str] = []
        for manifest in ordered:
            component_id = self._instance_id(manifest)
            runtime = (
                self._runtime_factory(manifest)
                if self._runtime_factory
                else ComponentRuntime(
                    event_bus=self.event_bus,
                    identity_boundary=self._default_identity_boundary,
                )
            )
            if runtime.identity_boundary is None:
                runtime.identity_boundary = self._default_identity_boundary
            if runtime.migration_adapters is None:
                runtime.migration_adapters = self.migration_adapters
            component, api = declare_component(component_id, manifest, runtime=runtime)
            declarations = api._commit()
            self.registry.register(component_id, manifest, declarations)
            self.migration_adapters.register_declarations(
                component_id=component_id,
                declarations=declarations,
            )
            asyncio.run(component.activate(runtime))
            self.components[component_id] = component
            for record in declarations.connection_handlers:
                handler = record.handler
                if callable(handler):
                    self.engine.register_handler(record.target, handler)
            self.lifecycle.record(component_id, ComponentPhase.DISCOVERED)
            self.lifecycle.record(component_id, ComponentPhase.VALIDATED_STATIC)
            self.lifecycle.record(component_id, ComponentPhase.ASSEMBLED)
            booted_ids.append(component_id)

        return BootReport(
            discovery=resolution,
            booted_ids=booted_ids,
            skipped_ids=skipped_ids,
            overridden_ids=overridden_ids,
            validation_issues=validation_issues,
            active_graph_version=self.version_manager.active_version,
        )

    def commit_graph(
        self, pending: PendingConnectionSet, *, candidate_id: str = "boot-graph"
    ) -> int:
        """Stage, validate, and commit a graph using the booted registry."""

        candidate, report = self.engine.stage(pending)
        if not report.valid:
            self.engine.discard_candidate(candidate_id, candidate, report)
            raise ValueError(
                f"Candidate graph '{candidate_id}' failed validation: "
                + "; ".join(f"{i.code}:{i.subject}" for i in report.issues)
            )
        version = self.engine.commit(candidate_id, candidate, report)
        self.registry.record_graph_version(version)
        for node in candidate.nodes:
            self.lifecycle.record(node.component_id, ComponentPhase.VALIDATED_DYNAMIC)
            self.lifecycle.record(node.component_id, ComponentPhase.ACTIVATED)
            self.lifecycle.record(node.component_id, ComponentPhase.COMMITTED)
        return version

    # ---------------------------------------------------------------- indexes

    def build_port_index(self) -> PortIndex:
        return PortIndex.from_registry(self.registry)

    def build_route_table(self) -> RouteTable | None:
        snapshot = self.version_manager.active_snapshot()
        if snapshot is None:
            return None
        return RouteTable.build(snapshot, self.build_port_index())


def bundled_discovery(root: Path) -> ComponentDiscovery:
    """Convenience factory for a discovery instance pointed at ``root``."""

    return ComponentDiscovery(bundled=root)
