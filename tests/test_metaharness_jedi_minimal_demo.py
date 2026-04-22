from pathlib import Path

import pytest

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.environment import JediEnvironmentProbeComponent
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.gateway import JediGatewayComponent
from metaharness_ext.jedi.validator import JediValidatorComponent

JEDI_COMPONENTS = [
    "jedi_gateway",
    "jedi_environment",
    "jedi_config_compiler",
    "jedi_executor",
    "jedi_validator",
]


def _build_registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in JEDI_COMPONENTS:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


@pytest.mark.asyncio
async def test_jedi_minimal_path_runs(examples_dir: Path, monkeypatch, tmp_path: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "jedi"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "jedi-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("jedi-minimal", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    background = examples_dir / "jedi-demo-background.nc"
    background.write_text("background")

    task = gateway.issue_task(task_id="demo-1", background_path=str(background))
    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", lambda name: None)
    environment_report = environment.probe(task)
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: None,
    )
    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert environment_report.required_paths_present is True
    assert environment_report.binary_available is False
    assert plan.execution_mode == "validate_only"
    assert artifact.status == "unavailable"
    assert validation.passed is False
    assert validation.status == "environment_invalid"
