import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.abacus.capabilities import (
    CAP_ABACUS_CASE_COMPILE,
    CAP_ABACUS_ENV_PROBE,
    CAP_ABACUS_MD_RUN,
    CAP_ABACUS_NSCF_RUN,
    CAP_ABACUS_RELAX_RUN,
    CAP_ABACUS_SCF_RUN,
    CAP_ABACUS_VALIDATE,
)
from metaharness_ext.abacus.slots import (
    ABACUS_ENVIRONMENT_SLOT,
    ABACUS_EXECUTOR_SLOT,
    ABACUS_GATEWAY_SLOT,
    ABACUS_INPUT_COMPILER_SLOT,
    ABACUS_VALIDATOR_SLOT,
)

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "src" / "metaharness_ext" / "abacus"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "abacus",
        "entry": "metaharness_ext.abacus",
        "capabilities": [
            CAP_ABACUS_ENV_PROBE,
            CAP_ABACUS_CASE_COMPILE,
            CAP_ABACUS_SCF_RUN,
            CAP_ABACUS_NSCF_RUN,
            CAP_ABACUS_RELAX_RUN,
            CAP_ABACUS_MD_RUN,
            CAP_ABACUS_VALIDATE,
        ],
    },
    "gateway.json": {
        "name": "abacus_gateway",
        "entry": "metaharness_ext.abacus.gateway:AbacusGatewayComponent",
        "slot": ABACUS_GATEWAY_SLOT,
        "output": "task",
        "capabilities": [CAP_ABACUS_CASE_COMPILE],
    },
    "environment.json": {
        "name": "abacus_environment",
        "entry": "metaharness_ext.abacus.environment:AbacusEnvironmentProbeComponent",
        "slot": ABACUS_ENVIRONMENT_SLOT,
        "output": "environment",
        "capabilities": [CAP_ABACUS_ENV_PROBE],
    },
    "input_compiler.json": {
        "name": "abacus_input_compiler",
        "entry": "metaharness_ext.abacus.input_compiler:AbacusInputCompilerComponent",
        "slot": ABACUS_INPUT_COMPILER_SLOT,
        "output": "plan",
        "capabilities": [CAP_ABACUS_CASE_COMPILE],
    },
    "executor.json": {
        "name": "abacus_executor",
        "entry": "metaharness_ext.abacus.executor:AbacusExecutorComponent",
        "slot": ABACUS_EXECUTOR_SLOT,
        "output": "run",
        "capabilities": [
            CAP_ABACUS_SCF_RUN,
            CAP_ABACUS_NSCF_RUN,
            CAP_ABACUS_RELAX_RUN,
            CAP_ABACUS_MD_RUN,
        ],
    },
    "validator.json": {
        "name": "abacus_validator",
        "entry": "metaharness_ext.abacus.validator:AbacusValidatorComponent",
        "slot": ABACUS_VALIDATOR_SLOT,
        "output": "validation",
        "capabilities": [CAP_ABACUS_VALIDATE],
    },
}


def test_metaharness_abacus_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_metaharness_abacus_manifests_are_valid() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )

        assert manifest.name == expected["name"]
        assert manifest.entry == expected["entry"]
        if "slot" in expected:
            assert manifest.contracts.slots[0].slot == expected["slot"]
        if "output" in expected:
            assert manifest.contracts.outputs[0].name == expected["output"]
        assert sorted(manifest.all_provided_capabilities()) == sorted(expected["capabilities"])


def test_metaharness_abacus_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.abacus.gateway": "AbacusGatewayComponent",
        "metaharness_ext.abacus.environment": "AbacusEnvironmentProbeComponent",
        "metaharness_ext.abacus.input_compiler": "AbacusInputCompilerComponent",
        "metaharness_ext.abacus.executor": "AbacusExecutorComponent",
        "metaharness_ext.abacus.validator": "AbacusValidatorComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_abacus_component_declarations_match_manifests() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        if "slot" not in expected:
            continue
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )
        _, api = declare_component(f"{manifest.name}.primary", manifest)
        snapshot = api.snapshot()

        assert snapshot.slots[0].slot == expected["slot"]
        assert snapshot.outputs[0].name == expected["output"]
        assert sorted(cap.name for cap in snapshot.provides) == sorted(expected["capabilities"])
