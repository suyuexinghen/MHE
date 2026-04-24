"""Extended ComponentManifest field coverage."""

from __future__ import annotations

from pathlib import Path

import pytest

from metaharness.sdk.loader import (
    ManifestValidationError,
    ensure_manifest_valid,
    load_manifest,
    validate_manifest_static,
)
from metaharness.sdk.manifest import (
    ComponentManifest,
    ComponentType,
    ContractSpec,
)


def test_bundled_manifest_loads_with_new_fields(manifest_dir: Path) -> None:
    manifest = load_manifest(manifest_dir / "runtime.json")
    assert manifest.resolved_id() == "runtime"
    assert manifest.harness_version.startswith(">=")
    assert manifest.enabled is True


def test_manifest_provides_and_requires_union() -> None:
    manifest = ComponentManifest(
        name="m",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
        provides=["cap.a"],
        requires=["cap.b"],
    )
    assert "cap.a" in manifest.all_provided_capabilities()
    assert "cap.b" in manifest.all_required_capabilities()


def test_validate_manifest_static_detects_missing_bin() -> None:
    manifest = ComponentManifest(
        name="m",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
        bins=["definitely-not-a-real-binary-xyz"],
    )
    issues = validate_manifest_static(manifest)
    assert any("binary" in issue for issue in issues)
    with pytest.raises(ManifestValidationError):
        ensure_manifest_valid(manifest)


def test_validate_manifest_static_version_mismatch() -> None:
    manifest = ComponentManifest(
        name="m",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
        harness_version=">=99.0.0",
    )
    issues = validate_manifest_static(manifest)
    assert any("harness_version" in issue for issue in issues)


def test_component_type_backward_compat_alias() -> None:
    from metaharness.sdk.manifest import ComponentKind

    assert ComponentKind is ComponentType
    assert ComponentType.META.value == "meta"
    assert ComponentType.GOVERNANCE.value == "governance"


def test_manifest_policy_defaults_are_backward_compatible() -> None:
    manifest = ComponentManifest(
        name="m",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
    )

    assert manifest.policy.credentials.requires_subject is False
    assert manifest.policy.credentials.allow_inline_credentials is True
    assert manifest.policy.credentials.required_claims == []
    assert manifest.policy.sandbox.tier is None


def test_manifest_policy_inherits_legacy_sandbox_profile() -> None:
    manifest = ComponentManifest(
        name="m",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="x:X",
        contracts=ContractSpec(),
        safety={"sandbox_profile": "gvisor"},
    )

    assert manifest.safety.sandbox_profile == "gvisor"
    assert manifest.policy.sandbox.tier == "gvisor"
