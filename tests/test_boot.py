"""Full discovery -> boot orchestration tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime
from metaharness.core.models import PendingConnectionSet
from metaharness.hotreload import HotSwapOrchestrator
from metaharness.identity import InMemoryIdentityBoundary
from metaharness.sdk.discovery import ComponentDiscovery
from metaharness.sdk.runtime import ComponentRuntime


def test_boot_registers_discovered_components(manifest_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    report = runtime.boot()

    assert "runtime.primary" in [cid for cid in report.booted_ids]
    # All discovered manifests should be registered.
    assert len(report.booted_ids) >= 8
    assert "runtime.primary" in runtime.registry.components


def test_boot_commits_default_topology(manifest_dir: Path, graphs_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()
    snapshot = parse_graph_xml(graphs_dir / "default-topology.xml")
    version = runtime.commit_graph(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges),
        candidate_id="default",
    )
    assert version == 1
    assert runtime.version_manager.active_version == 1
    index = runtime.build_port_index()
    assert index.lookup("policy.primary.decision") is not None
    table = runtime.build_route_table()
    assert table is not None
    assert any(r.connection_id == "c1" for r in table.all_routes())


def test_boot_filters_disabled_components(manifest_dir: Path) -> None:
    runtime = HarnessRuntime(
        ComponentDiscovery(bundled=manifest_dir),
        enabled_overrides={"memory": {"enabled": False}},
    )
    report = runtime.boot()
    assert "memory.primary" not in runtime.registry.components
    assert "memory" in report.skipped_ids


def test_boot_injects_default_identity_boundary(manifest_dir: Path) -> None:
    runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
    runtime.boot()

    gateway = runtime.components["gateway.primary"]
    policy = runtime.components["policy.primary"]

    payload = gateway.issue_task(
        "fetch dataset",
        subject_id="service:gateway",
        credentials={"api_key": "top-secret"},
    )
    record = policy.record(
        "allow",
        payload["subject"],
        attestation_id=payload["attestation"]["attestation_id"],
    )

    assert gateway._runtime.identity_boundary is not None
    assert policy._runtime.identity_boundary is not None
    assert payload["subject"] == "service:gateway"
    assert record["credential_bound"] == "true"


def test_boot_preserves_explicit_identity_boundary(manifest_dir: Path) -> None:
    boundary = InMemoryIdentityBoundary()
    runtime = HarnessRuntime(
        ComponentDiscovery(bundled=manifest_dir),
        runtime_factory=lambda manifest: ComponentRuntime(identity_boundary=boundary),
    )
    runtime.boot()

    gateway = runtime.components["gateway.primary"]
    policy = runtime.components["policy.primary"]

    assert gateway._runtime.identity_boundary is boundary
    assert policy._runtime.identity_boundary is boundary


def test_boot_registers_declared_migration_adapters_into_runtime_registry(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir()
    component_module = tmp_path / "boot_migration_component.py"
    component_module.write_text(
        """
from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime


class BootMigrationComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(\"boot-migrator.primary\")
        api.register_migration_adapter(
            from_version=1,
            to_version=2,
            adapter=lambda old, delta: {**old, \"migrated\": True, **(delta or {})},
        )
""".strip()
    )
    manifest = {
        "name": "boot-migrator",
        "version": "0.1.0",
        "kind": "core",
        "entry": "boot_migration_component:BootMigrationComponent",
        "contracts": {
            "inputs": [],
            "outputs": [],
            "events": [],
            "provides": [],
            "requires": [],
            "slots": [
                {"slot": "boot-migrator.primary", "binding": "primary", "required": True}
            ],
        },
        "safety": {"protected": False, "mutability": "mutable", "hot_swap": True},
        "state_schema_version": 1,
    }
    (manifest_dir / "boot-migrator.json").write_text(json.dumps(manifest))

    sys.path.insert(0, str(tmp_path))
    try:
        runtime = HarnessRuntime(ComponentDiscovery(bundled=manifest_dir))
        runtime.boot()

        component = runtime.components["boot-migrator.primary"]
        assert component._runtime.migration_adapters is runtime.migration_adapters

        resolved = runtime.migration_adapters.resolve(
            source_type="boot-migrator.primary",
            source_version=1,
            target_type="boot-migrator.primary",
            target_version=2,
        )
        assert resolved is not None

        orchestrator = HotSwapOrchestrator(migration_adapters=runtime.migration_adapters)
        report = orchestrator.swap_sync(
            component_id="boot-migrator.primary",
            outgoing=_TestStatefulComponent(initial={"count": 1}),
            incoming=_TestStatefulComponent(),
            delta={"delta": 2},
            state_schema_version=1,
            target_state_schema_version=2,
        )

        assert report.success is True
        assert report.migrated_state == {"count": 1, "migrated": True, "delta": 2}
    finally:
        sys.path.remove(str(tmp_path))


def test_boot_reports_manifest_validation_issues(tmp_path: Path, manifest_dir: Path) -> None:
    # Copy one manifest but replace its entry with a broken class to force
    # an import failure at instantiation. Static validation uses
    # harness_version / bins / env only; we instead exercise the happy path
    # with unreachable bins requirement.

    broken_dir = tmp_path / "manifests"
    broken_dir.mkdir()
    src = manifest_dir / "memory.json"
    manifest = json.loads(src.read_text())
    manifest["bins"] = ["definitely-not-a-real-binary-xyz"]
    (broken_dir / "memory.json").write_text(json.dumps(manifest))

    runtime = HarnessRuntime(ComponentDiscovery(bundled=broken_dir))
    report = runtime.boot()
    assert "memory" in report.validation_issues
    assert "memory.primary" not in runtime.registry.components


class _TestStatefulComponent:
    def __init__(self, *, initial: dict[str, object] | None = None) -> None:
        self.state = dict(initial or {})

    async def suspend(self) -> None:
        return None

    async def deactivate(self) -> None:
        return None

    async def activate(self, runtime: ComponentRuntime | None) -> None:
        self._runtime = runtime

    async def export_state(self) -> dict[str, object]:
        return dict(self.state)

    async def import_state(self, state: dict[str, object]) -> None:
        self.state = dict(state)

    async def resume(self, new_state: dict[str, object] | None = None) -> None:
        if new_state is not None:
            self.state = dict(new_state)

    async def transform_state(
        self, old_state: dict[str, object], delta: dict[str, object] | None = None
    ) -> dict[str, object]:
        return {**old_state, **(delta or {})}
