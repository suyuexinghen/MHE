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
async def test_jedi_minimal_graph_wiring_surfaces_environment_invalid(
    examples_dir: Path, monkeypatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "jedi"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "jedi-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("jedi-minimal-foundation", candidate, report)

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


@pytest.mark.asyncio
async def test_jedi_schema_happy_path_runs(examples_dir: Path, monkeypatch, tmp_path: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "jedi"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "jedi-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("jedi-schema-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    background = examples_dir / "jedi-schema-background.nc"
    background.write_text("background")

    task = gateway.issue_task(
        task_id="schema-demo-1",
        execution_mode="schema",
        binary_name="qg4DVar.x",
        background_path=str(background),
    )

    def fake_which(name: str) -> str | None:
        if name == "ldd":
            return "/usr/bin/ldd"
        if name == "qg4DVar.x":
            return "/usr/bin/qg4DVar.x"
        return None

    class _LddResult:
        returncode = 0
        stdout = ""

    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", fake_which)
    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run",
        lambda *args, **kwargs: _LddResult(),
    )
    environment_report = environment.probe(task)
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "schema.json").write_text("{}")
        return type(
            "_SchemaCompletedProcess",
            (),
            {"returncode": 0, "stdout": "schema ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert environment_report.required_paths_present is True
    assert environment_report.binary_available is True
    assert environment_report.shared_libraries_resolved is True
    assert plan.execution_mode == "schema"
    assert artifact.status == "completed"
    assert artifact.command == ["/usr/bin/qg4DVar.x", "--output-json-schema=schema.json"]
    assert artifact.schema_path is not None
    assert validation.passed is True
    assert validation.status == "validated"


@pytest.mark.asyncio
async def test_jedi_validate_only_happy_path_runs(
    examples_dir: Path, monkeypatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "jedi"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "jedi-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("jedi-validate-only-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    background = examples_dir / "jedi-validate-background.nc"
    background.write_text("background")

    task = gateway.issue_task(
        task_id="validate-demo-1",
        execution_mode="validate_only",
        binary_name="qg4DVar.x",
        background_path=str(background),
    )

    def fake_which(name: str) -> str | None:
        if name == "ldd":
            return "/usr/bin/ldd"
        if name == "qg4DVar.x":
            return "/usr/bin/qg4DVar.x"
        return None

    class _LddResult:
        returncode = 0
        stdout = ""

    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", fake_which)
    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run",
        lambda *args, **kwargs: _LddResult(),
    )
    environment_report = environment.probe(task)
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        return type(
            "_ValidateCompletedProcess",
            (),
            {"returncode": 0, "stdout": "validate ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert environment_report.required_paths_present is True
    assert environment_report.binary_available is True
    assert environment_report.shared_libraries_resolved is True
    assert environment_report.smoke_ready is True
    assert plan.execution_mode == "validate_only"
    assert artifact.status == "completed"
    assert artifact.command == ["/usr/bin/qg4DVar.x", "--validate-only", "config.yaml"]
    assert artifact.schema_path is None
    assert validation.passed is True
    assert validation.status == "validated"


@pytest.mark.asyncio
async def test_jedi_real_run_happy_path_runs(examples_dir: Path, monkeypatch, tmp_path: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "jedi"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "jedi-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("jedi-real-run-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    background = examples_dir / "jedi-real-run-background.nc"
    background.write_text("background")

    task = gateway.issue_task(
        task_id="real-run-demo-1",
        execution_mode="real_run",
        binary_name="qg4DVar.x",
        background_path=str(background),
    )

    def fake_which(name: str) -> str | None:
        if name == "ldd":
            return "/usr/bin/ldd"
        if name == "qg4DVar.x":
            return "/usr/bin/qg4DVar.x"
        return None

    class _LddResult:
        returncode = 0
        stdout = ""

    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", fake_which)
    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run",
        lambda *args, **kwargs: _LddResult(),
    )
    environment_report = environment.probe(task)
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "departures.json").write_text('{"rms_observation_minus_analysis": 0.6, "rms_observation_minus_background": 1.1}')
        (cwd / "reference.json").write_text('{"baseline": "toy-reference"}')
        return type(
            "_RealRunCompletedProcess",
            (),
            {"returncode": 0, "stdout": "run ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert environment_report.smoke_ready is True
    assert environment_report.smoke_candidate == "variational"
    assert plan.execution_mode == "real_run"
    assert artifact.status == "completed"
    assert artifact.command == ["/usr/bin/qg4DVar.x", "config.yaml"]
    assert any(path.endswith("analysis.out") for path in artifact.output_files)
    assert any(path.endswith("departures.json") for path in artifact.diagnostic_files)
    assert any(path.endswith("reference.json") for path in artifact.reference_files)
    assert validation.passed is True
    assert validation.status == "executed"


@pytest.mark.asyncio
async def test_jedi_local_ensemble_real_run_happy_path_runs(
    examples_dir: Path, monkeypatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "jedi"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "jedi-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("jedi-letkf-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    ensemble_member = examples_dir / "jedi-ensemble-member.000"
    ensemble_member.write_text("member")
    background = examples_dir / "jedi-letkf-background.nc"
    background.write_text("background")
    observations = examples_dir / "jedi-letkf-obs.ioda"
    observations.write_text("obs")

    task = gateway.issue_local_ensemble_task(
        task_id="letkf-demo-1",
        execution_mode="real_run",
        binary_name="qgLETKF.x",
        ensemble_paths=[str(ensemble_member)],
        background_path=str(background),
        observation_paths=[str(observations)],
        scientific_check="ensemble_outputs_present",
    )

    def fake_which(name: str) -> str | None:
        if name == "ldd":
            return "/usr/bin/ldd"
        if name == "qgLETKF.x":
            return "/usr/bin/qgLETKF.x"
        return None

    class _LddResult:
        returncode = 0
        stdout = ""

    monkeypatch.setattr("metaharness_ext.jedi.environment.shutil.which", fake_which)
    monkeypatch.setattr(
        "metaharness_ext.jedi.environment.subprocess.run",
        lambda *args, **kwargs: _LddResult(),
    )
    environment_report = environment.probe(task)
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "letkf.out").write_text("ensemble output")
        (cwd / "posterior.out").write_text("posterior")
        (cwd / "ensemble_reference.json").write_text('{"baseline": "letkf-reference"}')
        return type(
            "_LetkfCompletedProcess",
            (),
            {"returncode": 0, "stdout": "run ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert environment_report.smoke_ready is True
    assert environment_report.smoke_candidate == "local_ensemble_da"
    assert plan.execution_mode == "real_run"
    assert artifact.status == "completed"
    assert artifact.command == ["/usr/bin/qgLETKF.x", "config.yaml"]
    assert any(path.endswith("letkf.out") for path in artifact.output_files)
    assert any(path.endswith("posterior.out") for path in artifact.diagnostic_files)
    assert any(path.endswith("ensemble_reference.json") for path in artifact.reference_files)
    assert validation.passed is True
    assert validation.status == "executed"
