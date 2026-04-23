import json
from pathlib import Path

import pytest

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import DeepMDMutationAxis, DeepMDStudySpec
from metaharness_ext.deepmd.environment import DeepMDEnvironmentProbeComponent
from metaharness_ext.deepmd.executor import DeepMDExecutorComponent
from metaharness_ext.deepmd.gateway import DeepMDGatewayComponent
from metaharness_ext.deepmd.study import DeepMDStudyComponent
from metaharness_ext.deepmd.train_config_compiler import DeepMDTrainConfigCompilerComponent
from metaharness_ext.deepmd.validator import DeepMDValidatorComponent

DEEPMD_COMPONENTS = [
    "deepmd_gateway",
    "deepmd_environment",
    "deepmd_train_config_compiler",
    "deepmd_executor",
    "deepmd_validator",
    "deepmd_study",
]


def _build_registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in DEEPMD_COMPONENTS:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


@pytest.mark.asyncio
async def test_deepmd_minimal_path_runs(examples_dir: Path, monkeypatch, tmp_path: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("deepmd-minimal", candidate, report)

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)

    task = gateway.issue_task(
        train_systems=[str(dataset_dir)], type_map=["H", "O"], task_id="demo-1"
    )
    environment_report = environment.probe(task)
    plan = compiler.build_plan(task)

    monkeypatch.setattr("metaharness_ext.deepmd.executor.shutil.which", lambda binary: None)
    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert environment_report.required_paths_present is True
    assert plan.execution_mode == "train"
    assert artifact.status == "unavailable"
    assert validation.passed is False
    assert validation.status == "environment_invalid"


@pytest.mark.asyncio
async def test_deepmd_minimal_study_path_runs(examples_dir: Path, monkeypatch, tmp_path: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("deepmd-minimal-study", candidate, report)

    gateway = DeepMDGatewayComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    study = DeepMDStudyComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))
    await study.activate(ComponentRuntime(storage_path=tmp_path))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)

    base_task = gateway.issue_task(
        train_systems=[str(dataset_dir)], type_map=["H", "O"], task_id="demo-study-1"
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        input_json = json.loads((cwd / "input.json").read_text())
        rcut = input_json["model"]["descriptor"]["rcut"]
        rmse = 0.015 if rcut == 7.0 else 0.045
        (cwd / "lcurve.out").write_text(f"# step rmse_e rmse_f\n100 {rmse} 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return type("_FakeCompletedProcess", (), {"returncode": 0, "stdout": "training ok", "stderr": ""})()

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    study_spec = DeepMDStudySpec(
        study_id="deepmd-minimal-study",
        task_id="demo-study-1",
        base_task=base_task,
        axis=DeepMDMutationAxis(kind="rcut", values=[6.0, 7.0]),
        metric_key="rmse_e_trn",
        goal="minimize",
    )

    study_report = study.run_study(
        study_spec,
        compiler=compiler,
        executor=executor,
        validator=validator,
    )

    assert report.valid is True
    assert version == 1
    assert [trial.axis_value for trial in study_report.trials] == [6.0, 7.0]
    assert study_report.recommended_value == pytest.approx(7.0)
    assert study_report.summary_metrics["best_rmse_e_trn"] == pytest.approx(0.015)
    assert all(trial.validation.status == "trained" for trial in study_report.trials)
