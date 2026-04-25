"""Dependency resolution (Kahn's algorithm) tests."""

from __future__ import annotations

import pytest

from metaharness.sdk.dependency import (
    CircularDependencyError,
    MissingDependencyError,
    resolve_boot_order,
)
from metaharness.sdk.manifest import (
    ComponentManifest,
    ComponentType,
    ContractSpec,
    DependencySpec,
)


def _manifest(
    name: str,
    *,
    deps: list[str] | None = None,
    provides: list[str] | None = None,
    requires: list[str] | None = None,
) -> ComponentManifest:
    return ComponentManifest(
        name=name,
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="metaharness.components.runtime:RuntimeComponent",
        contracts=ContractSpec(),
        deps=DependencySpec(components=deps or []),
        provides=provides or [],
        requires=requires or [],
    )


def test_topological_order_respects_component_deps() -> None:
    ordered = resolve_boot_order(
        [
            _manifest("c", deps=["b"]),
            _manifest("b", deps=["a"]),
            _manifest("a"),
        ]
    )
    assert [m.name for m in ordered] == ["a", "b", "c"]


def test_capability_deps_are_resolved() -> None:
    ordered = resolve_boot_order(
        [
            _manifest("consumer", requires=["tool.invoke"]),
            _manifest("producer", provides=["tool.invoke"]),
        ]
    )
    assert [m.name for m in ordered] == ["producer", "consumer"]


def test_missing_component_dep_raises() -> None:
    with pytest.raises(MissingDependencyError):
        resolve_boot_order([_manifest("a", deps=["ghost"])])


def test_missing_capability_dep_raises() -> None:
    manifest = ComponentManifest(
        name="a",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="metaharness.components.runtime:RuntimeComponent",
        contracts=ContractSpec(),
        deps=DependencySpec(capabilities=["ghost.cap"]),
    )
    with pytest.raises(MissingDependencyError):
        resolve_boot_order([manifest])


def test_cycle_detection() -> None:
    with pytest.raises(CircularDependencyError):
        resolve_boot_order(
            [
                _manifest("a", deps=["b"]),
                _manifest("b", deps=["a"]),
            ]
        )


def test_dependency_spec_supports_optional_fields_without_affecting_resolution() -> None:
    manifest = ComponentManifest(
        name="consumer",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="metaharness.components.runtime:RuntimeComponent",
        contracts=ContractSpec(),
        deps=DependencySpec(
            components=["producer"],
            optional_components=["debugger"],
            optional_capabilities=["metrics.emit"],
        ),
    )

    ordered = resolve_boot_order([
        manifest,
        _manifest("producer"),
    ])

    assert [m.name for m in ordered] == ["producer", "consumer"]
    assert manifest.deps.optional_components == ["debugger"]
    assert manifest.deps.optional_capabilities == ["metrics.emit"]
