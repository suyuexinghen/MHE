import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness_ext.fealpy.capabilities import (
    CAP_FEALPY_COMPILE,
    CAP_FEALPY_ENV_PROBE,
    CAP_FEALPY_EXECUTE_RUN,
    CAP_FEALPY_TASK_ISSUE,
    CAP_FEALPY_VALIDATE_REPORT,
)
from metaharness_ext.fealpy.slots import (
    FEALPY_COMPILER_SLOT,
    FEALPY_ENVIRONMENT_SLOT,
    FEALPY_EXECUTOR_SLOT,
    FEALPY_GATEWAY_SLOT,
    FEALPY_VALIDATOR_SLOT,
)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "examples" / "manifests" / "fealpy"

EXPECTED_MANIFESTS = {
    "fealpy_gateway.json": {
        "name": "fealpy_gateway",
        "entry": "metaharness_ext.fealpy.gateway:FealpyGatewayComponent",
        "slot": FEALPY_GATEWAY_SLOT,
        "capabilities": [CAP_FEALPY_TASK_ISSUE],
        "sandbox_tier": "workspace-write",
    },
    "fealpy_environment.json": {
        "name": "fealpy_environment",
        "entry": "metaharness_ext.fealpy.environment:FealpyEnvironmentProbeComponent",
        "slot": FEALPY_ENVIRONMENT_SLOT,
        "capabilities": [CAP_FEALPY_ENV_PROBE],
        "sandbox_tier": "read-only",
    },
    "fealpy_compiler.json": {
        "name": "fealpy_compiler",
        "entry": "metaharness_ext.fealpy.compiler:FealpyCompilerComponent",
        "slot": FEALPY_COMPILER_SLOT,
        "capabilities": [CAP_FEALPY_COMPILE],
        "sandbox_tier": "read-only",
    },
    "fealpy_executor.json": {
        "name": "fealpy_executor",
        "entry": "metaharness_ext.fealpy.executor:FealpyExecutorComponent",
        "slot": FEALPY_EXECUTOR_SLOT,
        "capabilities": [CAP_FEALPY_EXECUTE_RUN],
        "sandbox_tier": "workspace-write",
    },
    "fealpy_validator.json": {
        "name": "fealpy_validator",
        "entry": "metaharness_ext.fealpy.validator:FealpyValidatorComponent",
        "slot": FEALPY_VALIDATOR_SLOT,
        "capabilities": [CAP_FEALPY_VALIDATE_REPORT],
        "sandbox_tier": "read-only",
        "protected": True,
    },
}


def _manifest_path(filename: str) -> Path:
    return MANIFEST_DIR / filename


def _load_manifest(filename: str) -> ComponentManifest:
    return load_manifest(_manifest_path(filename))


def _load_json(filename: str) -> dict:
    return json.loads(_manifest_path(filename).read_text())


def test_all_expected_manifests_exist() -> None:
    for filename in EXPECTED_MANIFESTS:
        assert _manifest_path(filename).is_file(), f"Missing manifest: {filename}"


def test_each_manifest_name_matches() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = _load_manifest(filename)
        assert manifest.name == expected["name"]


def test_each_manifest_slot_matches() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        json_data = _load_json(filename)
        slots = json_data["contracts"]["slots"]
        assert len(slots) == 1
        assert slots[0]["slot"] == expected["slot"]


def test_each_manifest_capability_matches() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        json_data = _load_json(filename)
        capabilities = json_data["contracts"]["provides"]
        cap_names = [c["name"] for c in capabilities]
        for expected_cap in expected["capabilities"]:
            assert expected_cap in cap_names, f"{filename}: missing capability {expected_cap}"


def test_each_manifest_sandbox_tier_matches() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        json_data = _load_json(filename)
        actual_tier = json_data.get("policy", {}).get("sandbox", {}).get("tier")
        assert actual_tier == expected["sandbox_tier"]


def test_each_manifest_protected_flag_matches() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        json_data = _load_json(filename)
        is_protected = json_data.get("safety", {}).get("protected", False)
        assert is_protected == expected.get("protected", False)


def test_each_manifest_entry_importable() -> None:
    for filename in EXPECTED_MANIFESTS:
        manifest = _load_manifest(filename)
        if ":" not in manifest.entry:
            continue
        module_name, class_name = manifest.entry.split(":")
        module = import_module(module_name)
        assert hasattr(module, class_name), f"{filename}: {class_name} not found in {module_name}"


def test_each_component_declares_interface() -> None:
    for filename in EXPECTED_MANIFESTS:
        manifest = _load_manifest(filename)
        if ":" not in manifest.entry:
            continue
        component_id = f"fealpy-{manifest.name}"
        component, api = declare_component(component_id, manifest=manifest)
        assert component is not None, f"Failed to instantiate {filename}"
        snapshot = api.snapshot()
        assert len(snapshot.inputs) >= 0


def test_all_manifests_register() -> None:
    registry = ComponentRegistry()
    for filename in EXPECTED_MANIFESTS:
        manifest = _load_manifest(filename)
        if ":" not in manifest.entry:
            continue
        component, api = declare_component(f"fealpy-{manifest.name}", manifest=manifest)
        declarations = api.snapshot()
        registry.register(f"fealpy-{manifest.name}", manifest=manifest, declarations=declarations)
    assert len(registry.components) == 5
