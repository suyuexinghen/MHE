import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_CASE_COMPILE
from metaharness_ext.qcompute.slots import QCOMPUTE_GATEWAY_SLOT

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "src" / "metaharness_ext" / "qcompute"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "qcompute_gateway",
        "entry": "metaharness_ext.qcompute.gateway:QComputeGatewayComponent",
        "slot": QCOMPUTE_GATEWAY_SLOT,
        "output": "task",
        "output_type": "QComputeExperimentSpec",
        "capabilities": [CAP_QCOMPUTE_CASE_COMPILE],
        "sandbox_tier": "workspace-read",
    },
    "environment.json": {
        "name": "qcompute_environment",
        "entry": "metaharness_ext.qcompute.environment:QComputeEnvironmentProbeComponent",
        "slot": "qcompute_environment.primary",
        "output": "environment",
        "output_type": "QComputeEnvironmentReport",
        "capabilities": ["qcompute.environment.probe"],
        "sandbox_tier": "workspace-read",
    },
    "config_compiler.json": {
        "name": "qcompute_config_compiler",
        "entry": "metaharness_ext.qcompute.config_compiler:QComputeConfigCompilerComponent",
        "slot": "qcompute_config_compiler.primary",
        "output": "plan",
        "output_type": "QComputeRunPlan",
        "capabilities": ["qcompute.circuit.compile", CAP_QCOMPUTE_CASE_COMPILE],
        "sandbox_tier": "workspace-write",
    },
    "executor.json": {
        "name": "qcompute_executor",
        "entry": "metaharness_ext.qcompute.executor:QComputeExecutorComponent",
        "slot": "qcompute_executor.primary",
        "output": "run",
        "output_type": "QComputeRunArtifact",
        "capabilities": ["qcompute.circuit.run"],
        "sandbox_tier": "workspace-write",
    },
    "validator.json": {
        "name": "qcompute_validator",
        "entry": "metaharness_ext.qcompute.validator:QComputeValidatorComponent",
        "slot": "qcompute_validator.primary",
        "output": "validation",
        "output_type": "QComputeValidationReport",
        "capabilities": ["qcompute.result.validate"],
        "sandbox_tier": "workspace-read",
        "protected": True,
        "kind": "governance",
    },
    "study.json": {
        "name": "qcompute_study",
        "entry": "metaharness_ext.qcompute.study:QComputeStudyComponent",
        "slot": "qcompute_study.primary",
        "output": "report",
        "output_type": "QComputeStudyReport",
        "capabilities": ["qcompute.study.run"],
        "sandbox_tier": "workspace-read",
        "protected": False,
        "kind": "core",
    },
}


def test_metaharness_qcompute_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_qcompute_manifests_load() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )

        assert manifest.name == expected["name"]
        assert manifest.entry == expected["entry"]
        assert manifest.kind == expected.get("kind", "core")
        assert manifest.safety.protected is expected.get("protected", False)
        assert manifest.contracts.slots[0].slot == expected["slot"]
        assert manifest.contracts.outputs[0].name == expected["output"]
        assert manifest.contracts.outputs[0].type == expected["output_type"]
        assert sorted(manifest.all_provided_capabilities()) == sorted(expected["capabilities"])
        assert manifest.policy.sandbox.tier == expected["sandbox_tier"]
        assert manifest.safety.sandbox_profile == manifest.policy.sandbox.tier


def test_metaharness_qcompute_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.qcompute.gateway": "QComputeGatewayComponent",
        "metaharness_ext.qcompute.environment": "QComputeEnvironmentProbeComponent",
        "metaharness_ext.qcompute.config_compiler": "QComputeConfigCompilerComponent",
        "metaharness_ext.qcompute.executor": "QComputeExecutorComponent",
        "metaharness_ext.qcompute.validator": "QComputeValidatorComponent",
        "metaharness_ext.qcompute.study": "QComputeStudyComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_qcompute_component_declarations_match_manifest() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )
        _, api = declare_component(f"{manifest.name}.primary", manifest)
        snapshot = api.snapshot()

        assert snapshot.slots[0].slot == expected["slot"]
        assert snapshot.outputs[0].name == expected["output"]
        assert snapshot.outputs[0].type == expected["output_type"]
        assert sorted(cap.name for cap in snapshot.provides) == sorted(expected["capabilities"])
