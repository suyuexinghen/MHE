from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "src" / "metaharness_ext" / "lean"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "lean_gateway",
        "entry": "metaharness_ext.lean.gateway:LeanGatewayComponent",
        "slot": "lean_gateway.primary",
        "output": "task",
        "output_type": "LeanTaskSpec",
        "capabilities": ["lean.orchestrate.workflow"],
        "sandbox_tier": "workspace-read",
    },
    "gateway.json": {
        "name": "lean_gateway",
        "entry": "metaharness_ext.lean.gateway:LeanGatewayComponent",
        "slot": "lean_gateway.primary",
        "output": "task",
        "output_type": "LeanTaskSpec",
        "capabilities": ["lean.orchestrate.workflow"],
        "sandbox_tier": "workspace-read",
    },
    "environment.json": {
        "name": "lean_environment",
        "entry": "metaharness_ext.lean.environment:LeanEnvironmentComponent",
        "slot": "lean_environment.primary",
        "output": "environment",
        "output_type": "LeanEnvironmentReport",
        "capabilities": ["lean.probe.environment"],
        "sandbox_tier": "workspace-read",
    },
    "blueprint_compiler.json": {
        "name": "lean_blueprint_compiler",
        "entry": "metaharness_ext.lean.blueprint_compiler:LeanBlueprintCompilerComponent",
        "slot": "lean_blueprint_compiler.primary",
        "output": "blueprint",
        "output_type": "LeanBlueprint",
        "capabilities": ["lean.compile.blueprint"],
        "sandbox_tier": "workspace-read",
    },
    "proof_workspace.json": {
        "name": "lean_proof_workspace",
        "entry": "metaharness_ext.lean.proof_workspace:LeanProofWorkspaceComponent",
        "slot": "lean_proof_workspace.primary",
        "output": "plan",
        "output_type": "LeanRunPlan",
        "capabilities": ["lean.prepare.workspace"],
        "sandbox_tier": "workspace-write",
    },
    "executor.json": {
        "name": "lean_executor",
        "entry": "metaharness_ext.lean.executor:LeanExecutorComponent",
        "slot": "lean_executor.primary",
        "output": "run",
        "output_type": "LeanRunArtifact",
        "capabilities": ["lean.execute.proof"],
        "sandbox_tier": "workspace-write",
    },
    "validator.json": {
        "name": "lean_validator",
        "entry": "metaharness_ext.lean.validator:LeanValidatorComponent",
        "slot": "lean_validator.primary",
        "output": "validation",
        "output_type": "LeanValidationReport",
        "capabilities": ["lean.evaluate.policy", "lean.validate.result"],
        "sandbox_tier": "workspace-read",
        "protected": True,
        "kind": "governance",
    },
    "evidence.json": {
        "name": "lean_evidence",
        "entry": "metaharness_ext.lean.evidence:LeanEvidenceComponent",
        "slot": "lean_evidence.primary",
        "output": "evidence",
        "output_type": "LeanEvidenceBundle",
        "capabilities": ["lean.build.evidence"],
        "sandbox_tier": "workspace-read",
    },
}


def test_metaharness_lean_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_lean_manifests_load() -> None:
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


def test_metaharness_lean_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.lean.gateway": "LeanGatewayComponent",
        "metaharness_ext.lean.environment": "LeanEnvironmentComponent",
        "metaharness_ext.lean.blueprint_compiler": "LeanBlueprintCompilerComponent",
        "metaharness_ext.lean.proof_workspace": "LeanProofWorkspaceComponent",
        "metaharness_ext.lean.executor": "LeanExecutorComponent",
        "metaharness_ext.lean.validator": "LeanValidatorComponent",
        "metaharness_ext.lean.evidence": "LeanEvidenceComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_lean_component_declarations_match_manifest() -> None:
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
