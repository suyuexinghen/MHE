import json
from importlib import import_module
from pathlib import Path

from metaharness.sdk.loader import declare_component
from metaharness.sdk.manifest import ComponentManifest
from metaharness_ext.nektar.capabilities import (
    CAP_NEKTAR_CASE_COMPILE,
    CAP_NEKTAR_CONVERGENCE_STUDY,
    CAP_NEKTAR_MESH_PREPARE,
    CAP_NEKTAR_POSTPROCESS,
    CAP_NEKTAR_SOLVE_ADR,
    CAP_NEKTAR_SOLVE_INCNS,
    CAP_NEKTAR_VALIDATE,
)
from metaharness_ext.nektar.slots import (
    CONVERGENCE_STUDY_SLOT,
    NEKTAR_GATEWAY_SLOT,
    POSTPROCESS_SLOT,
    SESSION_COMPILER_SLOT,
    SOLVER_EXECUTOR_SLOT,
    VALIDATOR_SLOT,
)

MANIFEST_DIR = Path(__file__).resolve().parent.parent / "src" / "metaharness_ext" / "nektar"
EXPECTED_MANIFESTS = {
    "manifest.json": {
        "name": "nektar_gateway",
        "entry": "metaharness_ext.nektar.nektar_gateway:NektarGatewayComponent",
        "slot": NEKTAR_GATEWAY_SLOT,
        "output": "task",
        "capabilities": [CAP_NEKTAR_CASE_COMPILE],
    },
    "session_compiler.json": {
        "name": "session_compiler",
        "entry": "metaharness_ext.nektar.session_compiler:SessionCompilerComponent",
        "slot": SESSION_COMPILER_SLOT,
        "output": "plan",
        "capabilities": [CAP_NEKTAR_CASE_COMPILE, CAP_NEKTAR_MESH_PREPARE],
    },
    "solver_executor.json": {
        "name": "solver_executor",
        "entry": "metaharness_ext.nektar.solver_executor:SolverExecutorComponent",
        "slot": SOLVER_EXECUTOR_SLOT,
        "output": "run",
        "capabilities": [CAP_NEKTAR_SOLVE_ADR, CAP_NEKTAR_SOLVE_INCNS],
    },
    "postprocess.json": {
        "name": "postprocess",
        "entry": "metaharness_ext.nektar.postprocess:PostprocessComponent",
        "slot": POSTPROCESS_SLOT,
        "output": "postprocessed_run",
        "capabilities": [CAP_NEKTAR_POSTPROCESS],
    },
    "validator.json": {
        "name": "validator",
        "entry": "metaharness_ext.nektar.validator:NektarValidatorComponent",
        "slot": VALIDATOR_SLOT,
        "output": "validation",
        "capabilities": [CAP_NEKTAR_VALIDATE],
    },
    "convergence.json": {
        "name": "convergence_study",
        "entry": "metaharness_ext.nektar.convergence:ConvergenceStudyComponent",
        "slot": CONVERGENCE_STUDY_SLOT,
        "output": "report",
        "capabilities": [CAP_NEKTAR_CONVERGENCE_STUDY],
    },
}


def test_metaharness_nektar_manifest_set_is_complete() -> None:
    manifest_paths = {path.name for path in MANIFEST_DIR.glob("*.json")}
    assert manifest_paths == set(EXPECTED_MANIFESTS)


def test_metaharness_nektar_manifests_are_valid() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )

        assert manifest.name == expected["name"]
        assert manifest.entry == expected["entry"]
        assert manifest.contracts.slots[0].slot == expected["slot"]
        assert manifest.contracts.outputs[0].name == expected["output"]
        assert manifest.all_provided_capabilities() == expected["capabilities"]


def test_metaharness_nektar_manifest_entries_are_importable() -> None:
    modules = {
        "metaharness_ext.nektar.nektar_gateway": "NektarGatewayComponent",
        "metaharness_ext.nektar.session_compiler": "SessionCompilerComponent",
        "metaharness_ext.nektar.solver_executor": "SolverExecutorComponent",
        "metaharness_ext.nektar.postprocess": "PostprocessComponent",
        "metaharness_ext.nektar.validator": "NektarValidatorComponent",
        "metaharness_ext.nektar.convergence": "ConvergenceStudyComponent",
    }
    for module_name, class_name in modules.items():
        module = import_module(module_name)
        assert getattr(module, class_name) is not None


def test_metaharness_nektar_component_declarations_match_manifests() -> None:
    for filename, expected in EXPECTED_MANIFESTS.items():
        manifest = ComponentManifest.model_validate(
            json.loads((MANIFEST_DIR / filename).read_text())
        )
        _, api = declare_component(f"{manifest.name}.primary", manifest)
        snapshot = api.snapshot()

        assert snapshot.slots[0].slot == expected["slot"]
        assert snapshot.outputs[0].name == expected["output"]
        assert [cap.name for cap in snapshot.provides] == expected["capabilities"]
