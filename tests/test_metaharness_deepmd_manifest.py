import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.deepmd.capabilities import (
    CAP_DEEPMD_CASE_COMPILE,
    CAP_DEEPMD_ENV_PROBE,
    CAP_DEEPMD_MODEL_COMPRESS,
    CAP_DEEPMD_MODEL_DEVI,
    CAP_DEEPMD_MODEL_FREEZE,
    CAP_DEEPMD_MODEL_TEST,
    CAP_DEEPMD_NEIGHBOR_STAT,
    CAP_DEEPMD_STUDY,
    CAP_DEEPMD_TRAIN_RUN,
    CAP_DEEPMD_VALIDATE,
    CAP_DPGEN_AUTOTEST,
    CAP_DPGEN_RUN,
    CAP_DPGEN_SIMPLIFY,
)
from metaharness_ext.deepmd.slots import (
    DEEPMD_CONFIG_COMPILER_SLOT,
    DEEPMD_ENVIRONMENT_SLOT,
    DEEPMD_EXECUTOR_SLOT,
    DEEPMD_GATEWAY_SLOT,
    DEEPMD_STUDY_SLOT,
    DEEPMD_VALIDATOR_SLOT,
)

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "src" / "metaharness_ext" / "deepmd"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "deepmd_gateway",
        "entry": "metaharness_ext.deepmd.gateway:DeepMDGatewayComponent",
        "slot": DEEPMD_GATEWAY_SLOT,
        "output": "task",
        "capabilities": [CAP_DEEPMD_CASE_COMPILE],
    },
    "environment.json": {
        "name": "deepmd_environment",
        "entry": "metaharness_ext.deepmd.environment:DeepMDEnvironmentProbeComponent",
        "slot": DEEPMD_ENVIRONMENT_SLOT,
        "output": "environment",
        "capabilities": [CAP_DEEPMD_ENV_PROBE],
    },
    "train_config_compiler.json": {
        "name": "deepmd_train_config_compiler",
        "entry": "metaharness_ext.deepmd.train_config_compiler:DeepMDTrainConfigCompilerComponent",
        "slot": DEEPMD_CONFIG_COMPILER_SLOT,
        "output": "plan",
        "capabilities": [CAP_DEEPMD_CASE_COMPILE],
    },
    "executor.json": {
        "name": "deepmd_executor",
        "entry": "metaharness_ext.deepmd.executor:DeepMDExecutorComponent",
        "slot": DEEPMD_EXECUTOR_SLOT,
        "output": "run",
        "capabilities": [
            CAP_DEEPMD_MODEL_COMPRESS,
            CAP_DEEPMD_MODEL_DEVI,
            CAP_DEEPMD_MODEL_FREEZE,
            CAP_DEEPMD_MODEL_TEST,
            CAP_DEEPMD_NEIGHBOR_STAT,
            CAP_DEEPMD_TRAIN_RUN,
            CAP_DPGEN_AUTOTEST,
            CAP_DPGEN_RUN,
            CAP_DPGEN_SIMPLIFY,
        ],
    },
    "validator.json": {
        "name": "deepmd_validator",
        "entry": "metaharness_ext.deepmd.validator:DeepMDValidatorComponent",
        "slot": DEEPMD_VALIDATOR_SLOT,
        "output": "validation",
        "capabilities": [CAP_DEEPMD_VALIDATE],
    },
    "study.json": {
        "name": "deepmd_study",
        "entry": "metaharness_ext.deepmd.study:DeepMDStudyComponent",
        "slot": DEEPMD_STUDY_SLOT,
        "output": "report",
        "capabilities": [CAP_DEEPMD_STUDY],
    },
}


def test_metaharness_deepmd_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_metaharness_deepmd_manifests_are_valid() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )

        assert manifest.name == expected["name"]
        assert manifest.entry == expected["entry"]
        assert manifest.contracts.slots[0].slot == expected["slot"]
        assert manifest.contracts.outputs[0].name == expected["output"]
        assert sorted(manifest.all_provided_capabilities()) == sorted(expected["capabilities"])


def test_metaharness_deepmd_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.deepmd.gateway": "DeepMDGatewayComponent",
        "metaharness_ext.deepmd.environment": "DeepMDEnvironmentProbeComponent",
        "metaharness_ext.deepmd.train_config_compiler": "DeepMDTrainConfigCompilerComponent",
        "metaharness_ext.deepmd.executor": "DeepMDExecutorComponent",
        "metaharness_ext.deepmd.validator": "DeepMDValidatorComponent",
        "metaharness_ext.deepmd.study": "DeepMDStudyComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_deepmd_component_declarations_match_manifests() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )
        _, api = declare_component(f"{manifest.name}.primary", manifest)
        snapshot = api.snapshot()

        assert snapshot.slots[0].slot == expected["slot"]
        assert snapshot.outputs[0].name == expected["output"]
        assert sorted(cap.name for cap in snapshot.provides) == sorted(expected["capabilities"])
