import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.discovery import ComponentDiscovery, DiscoverySource
from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness_ext.jedi.capabilities import (
    CAP_JEDI_CASE_COMPILE,
    CAP_JEDI_DIAGNOSTICS,
    CAP_JEDI_ENV_PROBE,
    CAP_JEDI_REAL_RUN,
    CAP_JEDI_SCHEMA,
    CAP_JEDI_SMOKE_POLICY,
    CAP_JEDI_STUDY,
    CAP_JEDI_VALIDATE,
    CAP_JEDI_VALIDATE_ONLY,
)
from metaharness_ext.jedi.slots import (
    JEDI_CONFIG_COMPILER_SLOT,
    JEDI_DIAGNOSTICS_SLOT,
    JEDI_ENVIRONMENT_SLOT,
    JEDI_EXECUTOR_SLOT,
    JEDI_GATEWAY_SLOT,
    JEDI_SMOKE_POLICY_SLOT,
    JEDI_STUDY_SLOT,
    JEDI_VALIDATOR_SLOT,
)

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "src" / "metaharness_ext" / "jedi"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "jedi_gateway",
        "entry": "metaharness_ext.jedi.gateway:JediGatewayComponent",
        "slot": JEDI_GATEWAY_SLOT,
        "output": "task",
        "capabilities": [CAP_JEDI_CASE_COMPILE],
    },
    "environment.json": {
        "name": "jedi_environment",
        "entry": "metaharness_ext.jedi.environment:JediEnvironmentProbeComponent",
        "slot": JEDI_ENVIRONMENT_SLOT,
        "output": "environment",
        "capabilities": [CAP_JEDI_ENV_PROBE],
    },
    "compiler.json": {
        "name": "jedi_config_compiler",
        "entry": "metaharness_ext.jedi.config_compiler:JediConfigCompilerComponent",
        "slot": JEDI_CONFIG_COMPILER_SLOT,
        "output": "plan",
        "capabilities": [CAP_JEDI_CASE_COMPILE],
    },
    "executor.json": {
        "name": "jedi_executor",
        "entry": "metaharness_ext.jedi.executor:JediExecutorComponent",
        "slot": JEDI_EXECUTOR_SLOT,
        "output": "run",
        "capabilities": [CAP_JEDI_SCHEMA, CAP_JEDI_VALIDATE_ONLY, CAP_JEDI_REAL_RUN],
    },
    "validator.json": {
        "name": "jedi_validator",
        "entry": "metaharness_ext.jedi.validator:JediValidatorComponent",
        "slot": JEDI_VALIDATOR_SLOT,
        "output": "validation",
        "capabilities": [CAP_JEDI_VALIDATE],
    },
    "smoke_policy.json": {
        "name": "jedi_smoke_policy",
        "entry": "metaharness_ext.jedi.smoke_policy:JediSmokePolicyComponent",
        "slot": JEDI_SMOKE_POLICY_SLOT,
        "output": "policy",
        "capabilities": [CAP_JEDI_SMOKE_POLICY],
    },
    "diagnostics.json": {
        "name": "jedi_diagnostics",
        "entry": "metaharness_ext.jedi.diagnostics:JediDiagnosticsCollectorComponent",
        "slot": JEDI_DIAGNOSTICS_SLOT,
        "output": "diagnostics",
        "capabilities": [CAP_JEDI_DIAGNOSTICS],
    },
    "study.json": {
        "name": "jedi_study",
        "entry": "metaharness_ext.jedi.study:JediStudyComponent",
        "slot": JEDI_STUDY_SLOT,
        "output": "report",
        "capabilities": [CAP_JEDI_STUDY],
    },
}


def test_metaharness_jedi_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_metaharness_jedi_manifests_are_valid() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )

        assert manifest.name == expected["name"]
        assert manifest.entry == expected["entry"]
        assert manifest.contracts.slots[0].slot == expected["slot"]
        assert manifest.contracts.outputs[0].name == expected["output"]
        assert sorted(manifest.all_provided_capabilities()) == sorted(expected["capabilities"])
        assert manifest.policy is not None
        assert manifest.policy.sandbox is not None
        assert manifest.policy.credentials is not None
        assert manifest.safety.sandbox_profile == manifest.policy.sandbox.tier


def test_metaharness_jedi_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.jedi.gateway": "JediGatewayComponent",
        "metaharness_ext.jedi.environment": "JediEnvironmentProbeComponent",
        "metaharness_ext.jedi.config_compiler": "JediConfigCompilerComponent",
        "metaharness_ext.jedi.executor": "JediExecutorComponent",
        "metaharness_ext.jedi.validator": "JediValidatorComponent",
        "metaharness_ext.jedi.smoke_policy": "JediSmokePolicyComponent",
        "metaharness_ext.jedi.diagnostics": "JediDiagnosticsCollectorComponent",
        "metaharness_ext.jedi.study": "JediStudyComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None




def test_metaharness_jedi_component_declarations_match_manifests() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )
        _, api = declare_component(f"{manifest.name}.primary", manifest)
        snapshot = api.snapshot()

        assert snapshot.slots[0].slot == expected["slot"]
        assert snapshot.outputs[0].name == expected["output"]
        assert sorted(cap.name for cap in snapshot.provides) == sorted(expected["capabilities"])


def test_metaharness_jedi_custom_plugin_path_discovers_and_uses_hofx_slice() -> None:
    discovery = ComponentDiscovery(custom=MANIFEST_DIR)
    result = discovery.resolve()
    discovered = {item.manifest.name: item for item in result.winners}

    assert set(discovered) == {expected["name"] for expected in EXPECTED_MANIFESTS.values()}
    assert discovered["jedi_gateway"].source is DiscoverySource.CUSTOM
    assert discovered["jedi_config_compiler"].source is DiscoverySource.CUSTOM
    assert discovered["jedi_gateway"].path == MANIFEST_DIR / "manifest.json"
    assert discovered["jedi_config_compiler"].path == MANIFEST_DIR / "compiler.json"

    registry = ComponentRegistry()
    gateway_manifest = discovered["jedi_gateway"].manifest
    compiler_manifest = discovered["jedi_config_compiler"].manifest

    gateway, gateway_api = declare_component("jedi_gateway.primary", gateway_manifest)
    compiler, compiler_api = declare_component("jedi_config_compiler.primary", compiler_manifest)
    registry.register("jedi_gateway.primary", gateway_manifest, gateway_api.snapshot())
    registry.register("jedi_config_compiler.primary", compiler_manifest, compiler_api.snapshot())

    task = gateway.issue_hofx_task(
        task_id="hofx-registry-proof",
        execution_mode="validate_only",
        state_path="/tmp/background.nc",
        observation_paths=["/tmp/obs.ioda"],
    )
    plan = compiler.build_plan(task)

    assert registry.components_by_slot(JEDI_GATEWAY_SLOT) == ["jedi_gateway.primary"]
    assert registry.components_by_slot(JEDI_CONFIG_COMPILER_SLOT) == [
        "jedi_config_compiler.primary"
    ]
    assert registry.components_for_capability(CAP_JEDI_CASE_COMPILE) == [
        "jedi_gateway.primary",
        "jedi_config_compiler.primary",
    ]
    assert task.application_family == "hofx"
    assert plan.application_family == "hofx"
    assert plan.command == ["qgHofX4D.x", "validate_only"]
    assert "hofx:" in plan.config_text
    assert "/tmp/background.nc" in plan.required_runtime_paths
    assert "/tmp/obs.ioda" in plan.required_runtime_paths
