from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.moose.capabilities import (
    CAP_MOOSE_ENV_PROBE,
    CAP_MOOSE_EXECUTE_RUN,
    CAP_MOOSE_INPUT_COMPILE,
    CAP_MOOSE_STUDY_RUN,
    CAP_MOOSE_TASK_ISSUE,
    CAP_MOOSE_VALIDATE_REPORT,
)
from metaharness_ext.moose.slots import (
    MOOSE_ENVIRONMENT_SLOT,
    MOOSE_EXECUTOR_SLOT,
    MOOSE_GATEWAY_SLOT,
    MOOSE_INPUT_COMPILER_SLOT,
    MOOSE_STUDY_SLOT,
    MOOSE_VALIDATOR_SLOT,
)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "src" / "metaharness_ext" / "moose"
EXAMPLE_MANIFEST_DIR = ROOT / "examples" / "manifests" / "moose"

EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "moose",
        "entry": "metaharness_ext.moose",
        "capabilities": [
            CAP_MOOSE_TASK_ISSUE,
            CAP_MOOSE_ENV_PROBE,
            CAP_MOOSE_INPUT_COMPILE,
            CAP_MOOSE_EXECUTE_RUN,
            CAP_MOOSE_VALIDATE_REPORT,
            "moose.evidence.bundle",
            "moose.policy.evaluate",
            CAP_MOOSE_STUDY_RUN,
        ],
        "sandbox_tier": "workspace-write",
    },
    "gateway.json": {
        "name": "moose_gateway",
        "entry": "metaharness_ext.moose.gateway:MooseGatewayComponent",
        "slot": MOOSE_GATEWAY_SLOT,
        "output": "task",
        "capabilities": [CAP_MOOSE_TASK_ISSUE],
        "sandbox_tier": "workspace-write",
    },
    "environment.json": {
        "name": "moose_environment",
        "entry": "metaharness_ext.moose.environment:MooseEnvironmentProbeComponent",
        "slot": MOOSE_ENVIRONMENT_SLOT,
        "output": "environment",
        "capabilities": [CAP_MOOSE_ENV_PROBE],
        "sandbox_tier": "workspace-write",
    },
    "input_compiler.json": {
        "name": "moose_input_compiler",
        "entry": "metaharness_ext.moose.input_compiler:MooseInputCompilerComponent",
        "slot": MOOSE_INPUT_COMPILER_SLOT,
        "output": "plan",
        "capabilities": [CAP_MOOSE_INPUT_COMPILE],
        "sandbox_tier": "workspace-write",
    },
    "executor.json": {
        "name": "moose_executor",
        "entry": "metaharness_ext.moose.executor:MooseExecutorComponent",
        "slot": MOOSE_EXECUTOR_SLOT,
        "output": "run",
        "capabilities": [CAP_MOOSE_EXECUTE_RUN],
        "sandbox_tier": "workspace-write",
    },
    "validator.json": {
        "name": "moose_validator",
        "entry": "metaharness_ext.moose.validator:MooseValidatorComponent",
        "slot": MOOSE_VALIDATOR_SLOT,
        "output": "validation",
        "capabilities": [CAP_MOOSE_VALIDATE_REPORT],
        "sandbox_tier": "read-only",
        "protected": True,
    },
    "study.json": {
        "name": "moose_study",
        "entry": "metaharness_ext.moose.study:MooseStudyComponent",
        "slot": MOOSE_STUDY_SLOT,
        "output": "report",
        "capabilities": [CAP_MOOSE_STUDY_RUN],
        "sandbox_tier": "workspace-write",
    },
}


def test_metaharness_moose_manifest_set_is_complete() -> None:
    assert {path.name for path in MANIFEST_DIR.glob("*.json")} == set(EXPECTED_MANIFESTS)


def test_metaharness_moose_manifests_are_valid() -> None:
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
        assert manifest.policy.sandbox.tier == expected["sandbox_tier"]
        assert manifest.policy.sandbox.tier == manifest.safety.sandbox_profile
        assert manifest.policy.credentials.requires_subject is False
        assert manifest.policy.credentials.allow_inline_credentials is False
        assert manifest.policy.credentials.required_claims == []
        if "protected" in expected:
            assert manifest.safety.protected is expected["protected"]


def test_metaharness_moose_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.moose.gateway": "MooseGatewayComponent",
        "metaharness_ext.moose.environment": "MooseEnvironmentProbeComponent",
        "metaharness_ext.moose.input_compiler": "MooseInputCompilerComponent",
        "metaharness_ext.moose.executor": "MooseExecutorComponent",
        "metaharness_ext.moose.validator": "MooseValidatorComponent",
        "metaharness_ext.moose.study": "MooseStudyComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_moose_component_declarations_match_manifests() -> None:
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


def test_metaharness_moose_example_manifests_match_current_schema() -> None:
    expected_files = {
        "moose_gateway.json",
        "moose_environment.json",
        "moose_input_compiler.json",
        "moose_executor.json",
        "moose_validator.json",
        "moose_study.json",
    }
    assert {path.name for path in EXAMPLE_MANIFEST_DIR.glob("*.json")} == expected_files
    for path in EXAMPLE_MANIFEST_DIR.glob("*.json"):
        manifest = ComponentManifest.model_validate(json.loads(path.read_text()))
        assert manifest.name.startswith("moose_")
