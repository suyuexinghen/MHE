import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.octave.capabilities import (
    CAP_OCTAVE_ENV_PROBE,
    CAP_OCTAVE_EXECUTE_RUN,
    CAP_OCTAVE_SCRIPT_COMPILE,
    CAP_OCTAVE_STUDY_RUN,
    CAP_OCTAVE_TASK_ISSUE,
    CAP_OCTAVE_VALIDATE_REPORT,
)
from metaharness_ext.octave.slots import (
    OCTAVE_ENVIRONMENT_SLOT,
    OCTAVE_EXECUTOR_SLOT,
    OCTAVE_GATEWAY_SLOT,
    OCTAVE_SCRIPT_COMPILER_SLOT,
    OCTAVE_STUDY_SLOT,
    OCTAVE_VALIDATOR_SLOT,
)

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_DIR = ROOT / "src" / "metaharness_ext" / "octave"
EXAMPLE_MANIFEST_DIR = ROOT / "examples" / "manifests" / "octave"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "octave",
        "entry": "metaharness_ext.octave",
        "capabilities": [
            CAP_OCTAVE_TASK_ISSUE,
            CAP_OCTAVE_ENV_PROBE,
            CAP_OCTAVE_SCRIPT_COMPILE,
            CAP_OCTAVE_EXECUTE_RUN,
            CAP_OCTAVE_VALIDATE_REPORT,
            "octave.evidence.bundle",
            "octave.policy.evaluate",
            CAP_OCTAVE_STUDY_RUN,
        ],
        "sandbox_tier": "workspace-write",
    },
    "gateway.json": {
        "name": "octave_gateway",
        "entry": "metaharness_ext.octave.gateway:OctaveGatewayComponent",
        "slot": OCTAVE_GATEWAY_SLOT,
        "output": "task",
        "capabilities": [CAP_OCTAVE_TASK_ISSUE],
        "sandbox_tier": "workspace-write",
    },
    "environment.json": {
        "name": "octave_environment",
        "entry": "metaharness_ext.octave.environment:OctaveEnvironmentProbeComponent",
        "slot": OCTAVE_ENVIRONMENT_SLOT,
        "output": "environment",
        "capabilities": [CAP_OCTAVE_ENV_PROBE],
        "sandbox_tier": "read-only",
    },
    "script_compiler.json": {
        "name": "octave_script_compiler",
        "entry": "metaharness_ext.octave.script_compiler:OctaveScriptCompilerComponent",
        "slot": OCTAVE_SCRIPT_COMPILER_SLOT,
        "output": "plan",
        "capabilities": [CAP_OCTAVE_SCRIPT_COMPILE],
        "sandbox_tier": "workspace-write",
    },
    "executor.json": {
        "name": "octave_executor",
        "entry": "metaharness_ext.octave.executor:OctaveExecutorComponent",
        "slot": OCTAVE_EXECUTOR_SLOT,
        "output": "run",
        "capabilities": [CAP_OCTAVE_EXECUTE_RUN],
        "sandbox_tier": "workspace-write",
    },
    "validator.json": {
        "name": "octave_validator",
        "entry": "metaharness_ext.octave.validator:OctaveValidatorComponent",
        "slot": OCTAVE_VALIDATOR_SLOT,
        "output": "validation",
        "capabilities": [CAP_OCTAVE_VALIDATE_REPORT],
        "sandbox_tier": "read-only",
        "protected": True,
    },
    "study.json": {
        "name": "octave_study",
        "entry": "metaharness_ext.octave.study:OctaveStudyComponent",
        "slot": OCTAVE_STUDY_SLOT,
        "output": "report",
        "capabilities": [CAP_OCTAVE_STUDY_RUN],
        "sandbox_tier": "workspace-write",
    },
}


def test_metaharness_octave_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_metaharness_octave_manifests_are_valid() -> None:
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


def test_metaharness_octave_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.octave.gateway": "OctaveGatewayComponent",
        "metaharness_ext.octave.environment": "OctaveEnvironmentProbeComponent",
        "metaharness_ext.octave.script_compiler": "OctaveScriptCompilerComponent",
        "metaharness_ext.octave.executor": "OctaveExecutorComponent",
        "metaharness_ext.octave.validator": "OctaveValidatorComponent",
        "metaharness_ext.octave.study": "OctaveStudyComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_octave_component_declarations_match_manifests() -> None:
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


def test_metaharness_octave_example_manifests_match_current_schema() -> None:
    expected_files = {
        "octave_gateway.json",
        "octave_environment.json",
        "octave_script_compiler.json",
        "octave_executor.json",
        "octave_validator.json",
        "octave_study.json",
    }
    assert {path.name for path in EXAMPLE_MANIFEST_DIR.glob("*.json")} == expected_files
    for path in EXAMPLE_MANIFEST_DIR.glob("*.json"):
        manifest = ComponentManifest.model_validate(json.loads(path.read_text()))
        assert manifest.policy.sandbox.tier == manifest.safety.sandbox_profile
        assert manifest.policy.credentials.requires_subject is False
        assert manifest.policy.credentials.allow_inline_credentials is False
        assert manifest.policy.credentials.required_claims == []
