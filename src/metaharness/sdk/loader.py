"""Manifest and component loading helpers."""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import re
import shutil
from pathlib import Path
from typing import Any

from metaharness import __version__
from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.runtime import ComponentRuntime


class ManifestValidationError(ValueError):
    """Raised when a manifest fails static validation."""

    def __init__(self, component_id: str, issues: list[str]) -> None:
        super().__init__(f"Manifest '{component_id}' failed static validation: {'; '.join(issues)}")
        self.component_id = component_id
        self.issues = list(issues)


def load_manifest(path: Path) -> ComponentManifest:
    """Load a component manifest from JSON."""

    return ComponentManifest.model_validate(json.loads(path.read_text()))


async def load_manifest_async(path: Path) -> ComponentManifest:
    """Async variant of :func:`load_manifest`."""

    return await asyncio.to_thread(load_manifest, path)


def instantiate_component(manifest: ComponentManifest) -> HarnessComponent:
    """Import and instantiate a component class from its manifest entry."""

    module_name, _, class_name = manifest.entry.partition(":")
    if not module_name or not class_name:
        raise ValueError(f"Invalid component entry: {manifest.entry}")
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise ImportError(
            f"Failed to import component module '{module_name}' for manifest '{manifest.name}': {exc}"
        ) from exc
    component_type = getattr(module, class_name, None)
    if component_type is None:
        raise AttributeError(f"Component class '{class_name}' not found in module '{module_name}'")
    try:
        return component_type(manifest=manifest)
    except TypeError:
        return component_type()


def declare_component(
    component_id: str,
    manifest: ComponentManifest,
    *,
    runtime: ComponentRuntime | None = None,
    config: dict[str, Any] | None = None,
) -> tuple[HarnessComponent, HarnessAPI]:
    """Instantiate a component and collect its declarations."""

    component = instantiate_component(manifest)
    api = HarnessAPI(
        component_id=component_id,
        version=manifest.version,
        config=config or {},
        runtime=runtime or ComponentRuntime(),
    )
    component.declare_interface(api)
    return component, api


# ---------------------------------------------------------------------------
# Static validation
# ---------------------------------------------------------------------------

_VERSION_TOKEN = re.compile(r"^(>=|<=|==|>|<)?\s*(\d+(?:\.\d+){0,2})$")


def _compare_versions(a: str, b: str) -> int:
    parts_a = [int(p) for p in a.split(".")]
    parts_b = [int(p) for p in b.split(".")]
    length = max(len(parts_a), len(parts_b))
    parts_a.extend([0] * (length - len(parts_a)))
    parts_b.extend([0] * (length - len(parts_b)))
    if parts_a < parts_b:
        return -1
    if parts_a > parts_b:
        return 1
    return 0


def _check_version_spec(spec: str, actual: str) -> bool:
    match = _VERSION_TOKEN.match(spec.strip())
    if match is None:
        # Non-parseable spec: accept permissively.
        return True
    op = match.group(1) or ">="
    target = match.group(2)
    cmp = _compare_versions(actual, target)
    return {
        ">=": cmp >= 0,
        "<=": cmp <= 0,
        "==": cmp == 0,
        ">": cmp > 0,
        "<": cmp < 0,
    }[op]


def _runtime_version_base() -> str:
    # Strip pre-release suffixes like ``0.1.0.dev1``.
    match = re.match(r"^(\d+(?:\.\d+){0,2})", __version__)
    return match.group(1) if match else "0.0.0"


def validate_manifest_static(
    manifest: ComponentManifest, *, runtime_version: str | None = None
) -> list[str]:
    """Return a list of static validation issues for ``manifest``.

    Checks the manifest's declared ``harness_version`` constraint against the
    running runtime version, verifies that required binaries are discoverable
    on ``PATH``, and checks that required environment variables are set.
    """

    issues: list[str] = []
    actual = runtime_version or _runtime_version_base()
    if not _check_version_spec(manifest.harness_version, actual):
        issues.append(
            f"harness_version '{manifest.harness_version}' unsatisfied by runtime {actual}"
        )
    for binary in manifest.bins:
        if shutil.which(binary) is None:
            issues.append(f"required binary '{binary}' not found on PATH")
    for env in manifest.env:
        if env not in os.environ:
            issues.append(f"required env var '{env}' is not set")
    return issues


def ensure_manifest_valid(
    manifest: ComponentManifest, *, runtime_version: str | None = None
) -> None:
    """Raise :class:`ManifestValidationError` if static validation fails."""

    issues = validate_manifest_static(manifest, runtime_version=runtime_version)
    if issues:
        raise ManifestValidationError(manifest.resolved_id(), issues)
