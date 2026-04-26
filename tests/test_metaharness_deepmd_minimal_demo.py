import json
from pathlib import Path

import pytest

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.boot import HarnessRuntime
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import (
    ExternalCandidateReview,
    ExternalCandidateReviewState,
    GraphVersionStore,
)
from metaharness.core.models import PendingConnectionSet, SessionEventType
from metaharness.observability.events import InMemorySessionStore
from metaharness.sdk.discovery import ComponentDiscovery
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.contracts import (
    DeepMDExecutableSpec,
    DeepMDMutationAxis,
    DeepMDStudySpec,
    DPGenMachineSpec,
    DPGenSimplifySpec,
)
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
async def test_deepmd_gateway_baseline_train_emits_governance_review_outputs(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    engine.commit("deepmd-baseline-train", candidate, report)

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)

    task = gateway.issue_task(
        train_systems=[str(dataset_dir)],
        type_map=["H", "O"],
        task_id="deepmd-baseline-train-1",
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd=None, text, capture_output, check, timeout):
        if cwd is None:
            return type(
                "_FakeCompletedProcess",
                (),
                {"returncode": 0, "stdout": "deepmd-kit help", "stderr": ""},
            )()
        (cwd / "lcurve.out").write_text("# step rmse_e rmse_f\n100 0.02 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "training ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.environment.subprocess.run", fake_run)
    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
    )

    assert baseline_report.plan.execution_mode == "train"
    assert baseline_report.validation.status == "trained"
    assert baseline_report.policy_report.decision == "allow"
    assert baseline_report.core_validation_report.valid is True
    assert baseline_report.core_validation_report.issues == []
    assert baseline_report.candidate_record.promoted is True
    assert baseline_report.candidate_record.report.valid is True
    assert baseline_report.candidate_record.report.issues == []
    assert baseline_report.candidate_record.candidate_id == baseline_report.run.run_id
    assert baseline_report.candidate_record.report == baseline_report.core_validation_report


@pytest.mark.asyncio
async def test_deepmd_gateway_baseline_surfaces_environment_findings_without_short_circuiting_executor(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    engine.commit("deepmd-baseline-environment-findings", candidate, report)

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)
    working_directory = tmp_path / "not-a-directory"
    working_directory.write_text("block directory creation")

    task = gateway.issue_task(
        train_systems=[str(dataset_dir)],
        type_map=["H", "O"],
        task_id="deepmd-baseline-environment-findings-1",
        working_directory=str(working_directory),
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    executor_calls: list[tuple[str, ...]] = []

    def fake_run(command, *, cwd=None, text, capture_output, check, timeout):
        executor_calls.append(tuple(command))
        if cwd is None:
            return type(
                "_FakeCompletedProcess",
                (),
                {"returncode": 0, "stdout": "deepmd-kit help", "stderr": ""},
            )()
        (cwd / "lcurve.out").write_text("# step rmse_e rmse_f\n100 0.02 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "training ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.environment.subprocess.run", fake_run)
    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
    )

    assert report.valid is True
    assert executor_calls[-1][1:] == ("train", "input.json")
    assert baseline_report.run.status == "completed"
    assert baseline_report.validation.status == "trained"
    assert baseline_report.policy_report.decision == "defer"
    assert baseline_report.policy_report.gates[0].gate == "environment_prerequisites"
    assert baseline_report.evidence_bundle.metadata["environment"]["missing_required_paths"] == [
        str(working_directory)
    ]
    issue_codes = {issue.code for issue in baseline_report.core_validation_report.issues}
    assert "deepmd_gate_environment_prerequisites" in issue_codes
    assert baseline_report.candidate_record.promoted is False


def test_deepmd_gateway_baseline_train_hands_off_to_runtime_consumer(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import asyncio

    runtime = HarnessRuntime(ComponentDiscovery(bundled=examples_dir / "manifests" / "deepmd"))
    runtime.boot()
    session_store = InMemorySessionStore()
    runtime.session_store = session_store

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    asyncio.run(executor.activate(ComponentRuntime(storage_path=tmp_path)))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)
    task = gateway.issue_task(
        train_systems=[str(dataset_dir)],
        type_map=["H", "O"],
        task_id="deepmd-runtime-handoff-train-1",
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd=None, text, capture_output, check, timeout):
        if cwd is None:
            return type(
                "_FakeCompletedProcess",
                (),
                {"returncode": 0, "stdout": "deepmd-kit help", "stderr": ""},
            )()
        (cwd / "lcurve.out").write_text("# step rmse_e rmse_f\n100 0.02 2.50e-02\n")
        (cwd / "checkpoint").write_text("checkpoint-marker")
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "training ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.environment.subprocess.run", fake_run)
    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
        runtime=runtime,
    )

    assert runtime.version_manager.candidates[-1] == baseline_report.candidate_record
    assert runtime.version_manager.candidates[-1].promoted is True
    assert baseline_report.validation.scored_evidence is not None
    assert (
        baseline_report.validation.scored_evidence.attributes["application_family"]
        == "deepmd_train"
    )
    assert any(ref.startswith("deepmd://run/") for ref in baseline_report.validation.evidence_refs)
    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert all(
        event.candidate_id == baseline_report.candidate_record.candidate_id for event in events
    )
    assert len(runtime.audit_log.by_kind("deepmd.governance_handoff")) == 1
    assert (
        f"graph-candidate:{baseline_report.candidate_record.candidate_id}"
        in runtime.provenance_graph.to_dict()["entities"]
    )


@pytest.mark.asyncio
async def test_deepmd_gateway_baseline_missing_binary_rejects_review_outputs(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("deepmd-baseline-missing-binary", candidate, report)

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)

    task = gateway.issue_task(
        train_systems=[str(dataset_dir)],
        type_map=["H", "O"],
        task_id="deepmd-baseline-missing-binary-1",
    )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.shutil.which", lambda binary: None)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
    )

    assert report.valid is True
    assert version == 1
    assert baseline_report.environment is not None
    assert baseline_report.validation.status == "environment_invalid"
    assert baseline_report.policy_report.decision == "reject"
    assert baseline_report.core_validation_report.valid is False
    assert baseline_report.core_validation_report.issues
    assert baseline_report.candidate_record.promoted is False
    assert baseline_report.candidate_record.report.valid is False
    assert baseline_report.candidate_record.report.issues
    assert baseline_report.candidate_record.candidate_id == baseline_report.run.run_id
    assert baseline_report.candidate_record.report == baseline_report.core_validation_report


def test_deepmd_gateway_baseline_missing_binary_records_runtime_rejection(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import asyncio

    runtime = HarnessRuntime(ComponentDiscovery(bundled=examples_dir / "manifests" / "deepmd"))
    runtime.boot()
    session_store = InMemorySessionStore()
    runtime.session_store = session_store

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    asyncio.run(executor.activate(ComponentRuntime(storage_path=tmp_path)))

    dataset_dir = examples_dir / "deepmd-demo-system"
    dataset_dir.mkdir(exist_ok=True)
    task = gateway.issue_task(
        train_systems=[str(dataset_dir)],
        type_map=["H", "O"],
        task_id="deepmd-runtime-handoff-missing-binary-1",
    )

    monkeypatch.setattr("metaharness_ext.deepmd.executor.shutil.which", lambda binary: None)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
        runtime=runtime,
    )

    assert runtime.version_manager.candidates[-1] == baseline_report.candidate_record
    assert runtime.version_manager.candidates[-1].promoted is False
    assert runtime.version_manager.candidates[-1].external_review == ExternalCandidateReview(
        state=ExternalCandidateReviewState.REJECTED,
        reason=runtime.version_manager.candidates[-1].external_review.reason,
    )
    assert runtime.version_manager.candidates[-1].external_review.reason is not None
    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
        SessionEventType.CANDIDATE_REJECTED,
    ]
    assert events[-1].candidate_id == baseline_report.candidate_record.candidate_id
    assert "deepmd_binary_not_found" in events[-1].payload["reason"]
    assert "deepmd_gate_run_status" in events[-1].payload["reason"]


@pytest.mark.asyncio
async def test_deepmd_minimal_study_path_runs(
    examples_dir: Path, monkeypatch, tmp_path: Path
) -> None:
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
        return type(
            "_FakeCompletedProcess", (), {"returncode": 0, "stdout": "training ok", "stderr": ""}
        )()

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


def test_deepmd_gateway_baseline_dpgen_run_hands_off_to_runtime_consumer(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import asyncio

    runtime = HarnessRuntime(ComponentDiscovery(bundled=examples_dir / "manifests" / "deepmd"))
    runtime.boot()
    session_store = InMemorySessionStore()
    runtime.session_store = session_store

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    asyncio.run(executor.activate(ComponentRuntime(storage_path=tmp_path)))

    run_inputs = examples_dir / "dpgen-run-inputs"
    run_inputs.mkdir(exist_ok=True)
    (run_inputs / "input.data").write_text("demo\n")

    task = gateway.issue_dpgen_run_task(
        task_id="deepmd-runtime-handoff-dpgen-run-1",
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=".", python_path="python3"),
        workspace_files=[str(run_inputs)],
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        iter_dir = cwd / "iter.000000"
        (iter_dir / "00.train").mkdir(parents=True)
        (iter_dir / "01.model_devi").mkdir()
        (iter_dir / "02.fp").mkdir()
        (cwd / "record.dpgen").write_text(
            "candidate_count = 2\naccurate_count = 1\nfailed_count = 0\n"
        )
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "dpgen run ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
        runtime=runtime,
    )

    assert baseline_report.validation.status == "baseline_success"
    assert baseline_report.policy_report.decision == "allow"
    assert runtime.version_manager.candidates[-1] == baseline_report.candidate_record
    assert runtime.version_manager.candidates[-1].promoted is True
    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert all(
        event.candidate_id == baseline_report.candidate_record.candidate_id for event in events
    )


@pytest.mark.asyncio
async def test_deepmd_minimal_simplify_path_runs(
    examples_dir: Path, monkeypatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("deepmd-minimal-simplify", candidate, report)

    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    simplify_inputs = examples_dir / "dpgen-simplify-inputs"
    simplify_inputs.mkdir(exist_ok=True)
    (simplify_inputs / "input.data").write_text("demo\n")

    spec = DPGenSimplifySpec(
        task_id="demo-simplify-1",
        executable=DeepMDExecutableSpec(binary_name="dpgen", execution_mode="dpgen_simplify"),
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=".", python_path="python3"),
        training_init_model=["models/model.pb"],
        relabeling={"pick_number": 4},
        workspace_files=[str(simplify_inputs)],
    )
    plan = compiler.build_plan(spec)

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        iter_dir = cwd / "iter.000000"
        (iter_dir / "00.train").mkdir(parents=True)
        (iter_dir / "01.model_devi").mkdir()
        (iter_dir / "02.fp").mkdir()
        (cwd / "record.dpgen").write_text(
            "candidate_count = 0\naccurate_count = 2\nfailed_count = 0\nconverged\n"
        )
        (iter_dir / "02.fp" / "relabel.out").write_text("relabel pick_number = 4\n")
        return type(
            "_FakeCompletedProcess", (), {"returncode": 0, "stdout": "simplify ok", "stderr": ""}
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert plan.execution_mode == "dpgen_simplify"
    assert artifact.status == "completed"
    assert validation.passed is True
    assert validation.status == "converged"


def test_deepmd_gateway_baseline_dpgen_simplify_hands_off_to_runtime_consumer(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import asyncio

    runtime = HarnessRuntime(ComponentDiscovery(bundled=examples_dir / "manifests" / "deepmd"))
    runtime.boot()
    session_store = InMemorySessionStore()
    runtime.session_store = session_store

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    asyncio.run(executor.activate(ComponentRuntime(storage_path=tmp_path)))

    simplify_inputs = examples_dir / "dpgen-simplify-runtime-inputs"
    simplify_inputs.mkdir(exist_ok=True)
    (simplify_inputs / "input.data").write_text("demo\n")

    task = gateway.issue_dpgen_simplify_task(
        task_id="deepmd-runtime-handoff-dpgen-simplify-1",
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=".", python_path="python3"),
        training_init_model=["models/model.pb"],
        relabeling={"pick_number": 4},
        workspace_files=[str(simplify_inputs)],
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        iter_dir = cwd / "iter.000000"
        (iter_dir / "00.train").mkdir(parents=True)
        (iter_dir / "01.model_devi").mkdir()
        (iter_dir / "02.fp").mkdir()
        (cwd / "record.dpgen").write_text(
            "candidate_count = 0\naccurate_count = 2\nfailed_count = 0\nconverged\n"
        )
        (iter_dir / "02.fp" / "relabel.out").write_text("relabel pick_number = 4\n")
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "simplify ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
        runtime=runtime,
    )

    assert baseline_report.validation.status == "converged"
    assert baseline_report.policy_report.decision == "allow"
    assert runtime.version_manager.candidates[-1] == baseline_report.candidate_record
    assert runtime.version_manager.candidates[-1].promoted is True
    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert all(
        event.candidate_id == baseline_report.candidate_record.candidate_id for event in events
    )


@pytest.mark.asyncio
async def test_deepmd_minimal_autotest_path_runs(
    examples_dir: Path, monkeypatch, tmp_path: Path
) -> None:
    manifest_dir = examples_dir / "manifests" / "deepmd"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "deepmd-minimal.xml")
    candidate, report = engine.stage(
        PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    )
    version = engine.commit("deepmd-minimal-autotest", candidate, report)

    gateway = DeepMDGatewayComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    autotest_inputs = examples_dir / "dpgen-autotest-inputs"
    autotest_inputs.mkdir(exist_ok=True)
    (autotest_inputs / "input.data").write_text("demo\n")

    spec = gateway.issue_dpgen_autotest_task(
        task_id="demo-autotest-1",
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=".", python_path="python3"),
        properties=["eos"],
        workspace_files=[str(autotest_inputs)],
    )
    plan = compiler.build_plan(spec)

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "result.json").write_text('{"eos": {"mae": 0.01, "rmse": 0.02}}')
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "autotest ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan)
    validation = validator.validate_run(artifact)

    assert report.valid is True
    assert version == 1
    assert plan.execution_mode == "dpgen_autotest"
    assert artifact.status == "completed"
    assert validation.passed is True
    assert validation.status == "autotest_validated"


def test_deepmd_gateway_baseline_dpgen_autotest_hands_off_to_runtime_consumer(
    examples_dir: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import asyncio

    runtime = HarnessRuntime(ComponentDiscovery(bundled=examples_dir / "manifests" / "deepmd"))
    runtime.boot()
    session_store = InMemorySessionStore()
    runtime.session_store = session_store

    gateway = DeepMDGatewayComponent()
    environment = DeepMDEnvironmentProbeComponent()
    compiler = DeepMDTrainConfigCompilerComponent()
    executor = DeepMDExecutorComponent()
    validator = DeepMDValidatorComponent()
    asyncio.run(executor.activate(ComponentRuntime(storage_path=tmp_path)))

    autotest_inputs = examples_dir / "dpgen-autotest-runtime-inputs"
    autotest_inputs.mkdir(exist_ok=True)
    (autotest_inputs / "input.data").write_text("demo\n")

    task = gateway.issue_dpgen_autotest_task(
        task_id="deepmd-runtime-handoff-dpgen-autotest-1",
        param={"type_map": ["H", "O"], "numb_models": 4},
        machine=DPGenMachineSpec(local_root=".", python_path="python3"),
        properties=["eos"],
        workspace_files=[str(autotest_inputs)],
    )

    monkeypatch.setattr(
        "metaharness_ext.deepmd.executor.shutil.which", lambda binary: f"/usr/bin/{binary}"
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "result.json").write_text('{"eos": {"mae": 0.01, "rmse": 0.02}}')
        return type(
            "_FakeCompletedProcess",
            (),
            {"returncode": 0, "stdout": "autotest ok", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.deepmd.executor.subprocess.run", fake_run)

    baseline_report = gateway.run_baseline(
        task,
        environment=environment,
        compiler=compiler,
        executor=executor,
        validator=validator,
        runtime=runtime,
    )

    assert baseline_report.validation.status == "autotest_validated"
    assert baseline_report.policy_report.decision == "allow"
    assert runtime.version_manager.candidates[-1] == baseline_report.candidate_record
    assert runtime.version_manager.candidates[-1].promoted is True
    events = session_store.get_events(runtime.session_id)
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert all(
        event.candidate_id == baseline_report.candidate_record.candidate_id for event in events
    )
