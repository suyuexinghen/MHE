"""Registry staging, conflict detection, and enabled filtering tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.manifest import ComponentManifest, ComponentType, ContractSpec
from metaharness.sdk.models import PendingDeclarations
from metaharness.sdk.registry import (
    ComponentRegistry,
    RegistrationConflictError,
    filter_enabled,
)


def test_duplicate_component_id_raises(manifest_dir: Path) -> None:
    registry = ComponentRegistry()
    manifest = load_manifest(manifest_dir / "runtime.json")
    _, api = declare_component("runtime.primary", manifest)
    registry.register("runtime.primary", manifest, api.snapshot())

    _, api2 = declare_component("runtime.primary", manifest)
    with pytest.raises(RegistrationConflictError):
        registry.register("runtime.primary", manifest, api2.snapshot())


def test_staged_commit_pending(manifest_dir: Path) -> None:
    registry = ComponentRegistry()
    manifest = load_manifest(manifest_dir / "runtime.json")
    _, api = declare_component("runtime.primary", manifest)

    registry.stage("runtime.primary", manifest, api.snapshot())
    assert "runtime.primary" in registry.pending
    assert "runtime.primary" not in registry.components

    committed = registry.commit_pending()
    assert committed == ["runtime.primary"]
    assert "runtime.primary" in registry.components
    assert registry.pending == {}


def test_staged_abort_pending(manifest_dir: Path) -> None:
    registry = ComponentRegistry()
    manifest = load_manifest(manifest_dir / "runtime.json")
    _, api = declare_component("runtime.primary", manifest)

    registry.stage("runtime.primary", manifest, api.snapshot())
    registry.abort_pending()
    assert registry.pending == {}
    assert "runtime.primary" not in registry.components


def test_filter_enabled_respects_override() -> None:
    manifest_a = ComponentManifest(
        name="a",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
    )
    manifest_b = ComponentManifest(
        name="b",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
        enabled=False,
    )
    manifest_c = ComponentManifest(
        name="c",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
    )

    result = filter_enabled(
        [manifest_a, manifest_b, manifest_c],
        config={"c": {"enabled": False}},
    )
    assert [m.name for m in result] == ["a"]


def test_registry_tracks_graph_version_and_mutations() -> None:
    registry = ComponentRegistry()
    registry.register(
        "x",
        ComponentManifest(
            name="x",
            version="0.1.0",
            kind=ComponentType.CORE,
            entry="x:X",
            contracts=ContractSpec(),
        ),
        PendingDeclarations(),
    )
    registry.record_graph_version(7)
    assert registry.graph_versions == [7]
