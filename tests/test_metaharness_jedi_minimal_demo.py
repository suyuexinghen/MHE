from pathlib import Path

import pytest

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet, SessionEventType
from metaharness.observability.events import InMemorySessionStore
from metaharness.provenance import AuditLog, ProvGraph
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.manifest import ComponentManifest, ComponentType, ContractSpec
from metaharness.sdk.registry import ComponentRegistry
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.config_compiler import JediConfigCompilerComponent
from metaharness_ext.jedi.diagnostics import JediDiagnosticsCollectorComponent
from metaharness_ext.jedi.environment import JediEnvironmentProbeComponent
from metaharness_ext.jedi.evidence import build_evidence_bundle
from metaharness_ext.jedi.executor import JediExecutorComponent
from metaharness_ext.jedi.gateway import JediGatewayComponent
from metaharness_ext.jedi.governance import JediGovernanceAdapter
from metaharness_ext.jedi.policy import JediEvidencePolicy
from metaharness_ext.jedi.validator import JediValidatorComponent

JEDI_COMPONENTS = [
    "jedi_gateway",
    "jedi_environment",
    "jedi_config_compiler",
    "jedi_executor",
    "jedi_validator",
]


def _jedi_gateway_manifest(**policy: object) -> ComponentManifest:
    return ComponentManifest(
        name="jedi_gateway",
        version="0.1.0",
        kind=ComponentType.CORE,
        entry="metaharness_ext.jedi.gateway:JediGatewayComponent",
        contracts=ContractSpec(),
        policy=policy,
    )


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
async def test_jedi_real_run_happy_path_runs(
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
        candidate_id="candidate-real-1",
        graph_version_id=9,
        session_id="runtime-session-1",
        audit_refs=["audit-record:real-run-1"],
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
        (cwd / "departures.json").write_text(
            '{"rms_observation_minus_analysis": 0.6, "rms_observation_minus_background": 1.1}'
        )
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
    assert artifact.result_summary["candidate_id"] == "candidate-real-1"
    assert artifact.result_summary["graph_version_id"] == 9
    assert artifact.result_summary["session_id"] == "runtime-session-1"
    assert artifact.result_summary["audit_refs"] == ["audit-record:real-run-1"]
    assert validation.passed is True
    assert validation.status == "executed"
    assert validation.candidate_id == "candidate-real-1"
    assert validation.graph_version_id == 9
    assert validation.session_id == "runtime-session-1"
    assert validation.audit_refs == ["audit-record:real-run-1"]


@pytest.mark.asyncio
async def test_jedi_orchestration_happy_path_wires_runtime_evidence_policy_and_governance(
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
    version = engine.commit("jedi-orchestration-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    diagnostics = JediDiagnosticsCollectorComponent()
    policy = JediEvidencePolicy()
    governance = JediGovernanceAdapter()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance_graph = ProvGraph()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    workspace = tmp_path / "jedi-workspace"
    (workspace / "testinput").mkdir(parents=True)
    background = workspace / "background.nc"
    observations = workspace / "obs.ioda"
    background.write_text("background")
    observations.write_text("observations")

    task = gateway.issue_task(
        task_id="jedi-orchestration-1",
        execution_mode="real_run",
        binary_name="qg4DVar.x",
        background_path=str(background),
        observation_paths=[str(observations)],
        working_directory=str(workspace),
        scientific_check="rms_improves",
        candidate_id="candidate-orchestration-1",
        graph_version_id=version,
        session_id="jedi-orchestration-session",
        audit_refs=["audit-record:orchestration-seed"],
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
    smoke_task = gateway.issue_smoke_task(
        environment_report,
        task_id="jedi-smoke-orchestration-1",
        execution_mode="validate_only",
        background_path=str(background),
        observation_paths=[str(observations)],
    )
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "analysis.out").write_text("analysis")
        (cwd / "departures.json").write_text(
            '{"MetaData": {"nlocs": 1}, '
            '"ObsValue": {"temperature": [280.0]}, '
            '"HofX": {"temperature": [279.5]}, '
            '"rms_observation_minus_analysis": 0.5, '
            '"rms_observation_minus_background": 1.2}'
        )
        (cwd / "reference.json").write_text('{"baseline": "orchestration-reference"}')
        return type(
            "_OrchestrationCompletedProcess",
            (),
            {
                "returncode": 0,
                "stdout": (
                    "run ok\n"
                    "Outer iteration: 1\n"
                    "Inner iteration: 3\n"
                    "Minimizer iteration: 4\n"
                    "Cost function: 12.5\n"
                    "Gradient norm: 8.0\n"
                    "Outer iteration: 2\n"
                    "Inner iteration: 5\n"
                    "Cost function: 3.125\n"
                    "Gradient norm: 0.5\n"
                    "observer summary available\n"
                ),
                "stderr": "",
            },
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan, environment_report=environment_report)
    diagnostic_summary = diagnostics.collect(artifact)
    validation = validator.validate_run_with_diagnostics(artifact, diagnostic_summary)
    bundle = build_evidence_bundle(artifact, validation, diagnostic_summary)
    policy_report = policy.evaluate(bundle)
    governance_refs = governance.emit_runtime_evidence(
        bundle,
        policy_report,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )
    candidate_record = governance.build_candidate_record(bundle, policy_report)

    assert report.valid is True
    assert version == 1
    assert smoke_task.application_family == "variational"
    assert smoke_task.executable.binary_name == "qg4DVar.x"
    assert environment_report.binary_available is True
    assert environment_report.workspace_root == str(workspace)
    assert environment_report.workspace_testinput_present is True
    assert environment_report.data_prerequisites_ready is True
    assert environment_report.ready_prerequisites == [
        "workspace testinput",
        "ctest -R get_ or equivalent observation data preparation",
        "ctest -R qg_get_data or equivalent QG data preparation",
    ]
    assert plan.execution_mode == "real_run"
    assert artifact.status == "completed"
    assert artifact.result_summary["checkpoint_refs"] == [
        "checkpoint://jedi/prerequisite/workspace-testinput",
        "checkpoint://jedi/prerequisite/ctest-r-get-or-equivalent-observation-data-preparation",
        "checkpoint://jedi/prerequisite/ctest-r-qg-get-data-or-equivalent-qg-data-preparation",
    ]
    assert validation.passed is True
    assert validation.status == "executed"
    assert validation.policy_decision == "allow"
    assert validation.summary_metrics["primary_output"].endswith("analysis.out")
    assert validation.summary_metrics["rms_observation_minus_analysis"] == 0.5
    assert validation.summary_metrics["rms_observation_minus_background"] == 1.2
    assert validation.summary_metrics["ioda_groups_found"] == 3
    assert validation.summary_metrics["gradient_norm_reduction"] == 0.0625
    assert validation.summary_metrics["observer_output_detected"] == "True"
    assert "IODA groups detected: HofX, MetaData, ObsValue." in validation.messages
    assert "Gradient norm reduction: 0.062500." in validation.messages
    assert diagnostic_summary.files_scanned == [
        artifact.diagnostic_files[0],
        artifact.stdout_path,
    ]
    assert bundle.validation is validation
    assert bundle.summary is diagnostic_summary
    assert artifact.diagnostic_files[0] in bundle.evidence_files
    assert artifact.stdout_path in bundle.evidence_files
    assert bundle.metadata["diagnostic_files_scanned"] == 2
    assert bundle.metadata["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert "ObsError" in bundle.metadata["ioda_groups_missing"]
    assert "PreQC" in bundle.metadata["ioda_groups_missing"]
    assert bundle.metadata["minimizer_iterations"] == 4
    assert bundle.metadata["outer_iterations"] == 2
    assert bundle.metadata["inner_iterations"] == 5
    assert bundle.metadata["initial_cost_function"] == 12.5
    assert bundle.metadata["final_cost_function"] == 3.125
    assert bundle.metadata["initial_gradient_norm"] == 8.0
    assert bundle.metadata["final_gradient_norm"] == 0.5
    assert bundle.metadata["gradient_norm_reduction"] == 0.0625
    assert policy_report.passed is True
    assert policy_report.decision == "allow"
    assert policy_report.evidence["diagnostic_files_scanned"] == 2
    assert policy_report.evidence["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert "ObsError" in policy_report.evidence["ioda_groups_missing"]
    assert "PreQC" in policy_report.evidence["ioda_groups_missing"]
    assert policy_report.evidence["minimizer_iterations"] == 4
    assert policy_report.evidence["outer_iterations"] == 2
    assert policy_report.evidence["inner_iterations"] == 5
    assert policy_report.evidence["initial_cost_function"] == 12.5
    assert policy_report.evidence["final_cost_function"] == 3.125
    assert policy_report.evidence["initial_gradient_norm"] == 8.0
    assert policy_report.evidence["final_gradient_norm"] == 0.5
    assert policy_report.evidence["gradient_norm_reduction"] == 0.0625
    assert candidate_record.promoted is True
    assert candidate_record.candidate_id == "candidate-orchestration-1"
    events = session_store.get_events("jedi-orchestration-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    safety_gate_event = next(
        event for event in events if event.event_type == SessionEventType.SAFETY_GATE_EVALUATED
    )
    assert safety_gate_event.payload["diagnostic_files_scanned"] == 2
    assert safety_gate_event.payload["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert "ObsError" in safety_gate_event.payload["ioda_groups_missing"]
    assert "PreQC" in safety_gate_event.payload["ioda_groups_missing"]
    assert safety_gate_event.payload["minimizer_iterations"] == 4
    assert safety_gate_event.payload["outer_iterations"] == 2
    assert safety_gate_event.payload["inner_iterations"] == 5
    assert safety_gate_event.payload["initial_cost_function"] == 12.5
    assert safety_gate_event.payload["final_cost_function"] == 3.125
    assert safety_gate_event.payload["initial_gradient_norm"] == 8.0
    assert safety_gate_event.payload["final_gradient_norm"] == 0.5
    assert safety_gate_event.payload["gradient_norm_reduction"] == 0.0625
    assert len(audit_log.by_kind("session.candidate_validated")) == 1
    assert len(audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert len(audit_log.by_kind("jedi.governance_handoff")) == 1
    handoff_record = audit_log.by_kind("jedi.governance_handoff")[0]
    assert handoff_record.payload["diagnostic_files_scanned"] == 2
    assert handoff_record.payload["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert "ObsError" in handoff_record.payload["ioda_groups_missing"]
    assert "PreQC" in handoff_record.payload["ioda_groups_missing"]
    assert handoff_record.payload["minimizer_iterations"] == 4
    assert handoff_record.payload["outer_iterations"] == 2
    assert handoff_record.payload["inner_iterations"] == 5
    assert handoff_record.payload["initial_cost_function"] == 12.5
    assert handoff_record.payload["final_cost_function"] == 3.125
    assert handoff_record.payload["initial_gradient_norm"] == 8.0
    assert handoff_record.payload["final_gradient_norm"] == 0.5
    assert handoff_record.payload["gradient_norm_reduction"] == 0.0625
    assert "graph-candidate:candidate-orchestration-1" in provenance_graph.to_dict()["entities"]
    assert all(ref.startswith("audit-record:") for ref in governance_refs["audit_refs"])
    assert "graph-version:1" in governance_refs["provenance_refs"]


@pytest.mark.asyncio
async def test_jedi_hofx_orchestration_happy_path_wires_runtime_evidence_policy_and_governance(
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
    version = engine.commit("jedi-hofx-orchestration-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    diagnostics = JediDiagnosticsCollectorComponent()
    policy = JediEvidencePolicy()
    governance = JediGovernanceAdapter()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance_graph = ProvGraph()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    workspace = tmp_path / "jedi-hofx-workspace"
    (workspace / "testinput").mkdir(parents=True)
    state = workspace / "hofx-state.nc"
    observations = workspace / "hofx-obs.ioda"
    state.write_text("state")
    observations.write_text("observations")

    task = gateway.issue_hofx_task(
        task_id="jedi-hofx-orchestration-1",
        execution_mode="real_run",
        binary_name="qgHofX4D.x",
        state_path=str(state),
        observation_paths=[str(observations)],
        working_directory=str(workspace),
        candidate_id="candidate-hofx-orchestration-1",
        graph_version_id=version,
        session_id="jedi-hofx-orchestration-session",
        audit_refs=["audit-record:hofx-orchestration-seed"],
    )

    def fake_which(name: str) -> str | None:
        if name == "ldd":
            return "/usr/bin/ldd"
        if name == "qgHofX4D.x":
            return "/usr/bin/qgHofX4D.x"
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
    smoke_task = gateway.issue_smoke_task(
        environment_report,
        task_id="jedi-hofx-smoke-orchestration-1",
        execution_mode="validate_only",
        background_path=str(state),
        observation_paths=[str(observations)],
    )
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "hofx.out").write_text("hofx output")
        (cwd / "hofx_reference.json").write_text('{"baseline": "hofx-reference"}')
        return type(
            "_HofXCompletedProcess",
            (),
            {
                "returncode": 0,
                "stdout": (
                    "run ok\n"
                    "MetaData group present\n"
                    "ObsValue group present\n"
                    "HofX group present\n"
                    "observer summary available\n"
                ),
                "stderr": "",
            },
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan, environment_report=environment_report)
    diagnostic_summary = diagnostics.collect(artifact)
    validation = validator.validate_run_with_diagnostics(artifact, diagnostic_summary)
    bundle = build_evidence_bundle(artifact, validation, diagnostic_summary)
    policy_report = policy.evaluate(bundle)
    governance_refs = governance.emit_runtime_evidence(
        bundle,
        policy_report,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )
    candidate_record = governance.build_candidate_record(bundle, policy_report)

    assert report.valid is True
    assert version == 1
    assert task.application_family == "hofx"
    assert task.executable.binary_name == "qgHofX4D.x"
    assert smoke_task.application_family == "hofx"
    assert smoke_task.executable.binary_name == "qgHofX4D.x"
    assert environment_report.binary_available is True
    assert environment_report.workspace_root == str(workspace)
    assert environment_report.workspace_testinput_present is True
    assert environment_report.data_prerequisites_ready is True
    assert environment_report.smoke_ready is True
    assert environment_report.smoke_candidate == "hofx"
    assert environment_report.ready_prerequisites == [
        "workspace testinput",
        "ctest -R get_ or equivalent observation data preparation",
    ]
    assert plan.application_family == "hofx"
    assert plan.execution_mode == "real_run"
    assert plan.expected_outputs == ["hofx.out"]
    assert plan.expected_references == ["hofx_reference.json"]
    assert artifact.status == "completed"
    assert artifact.command == ["/usr/bin/qgHofX4D.x", "config.yaml"]
    assert any(path.endswith("hofx.out") for path in artifact.output_files)
    assert any(path.endswith("hofx_reference.json") for path in artifact.reference_files)
    assert artifact.result_summary["checkpoint_refs"] == [
        "checkpoint://jedi/prerequisite/workspace-testinput",
        "checkpoint://jedi/prerequisite/ctest-r-get-or-equivalent-observation-data-preparation",
    ]
    assert validation.passed is True
    assert validation.status == "executed"
    assert validation.policy_decision == "allow"
    assert validation.candidate_id == "candidate-hofx-orchestration-1"
    assert validation.graph_version_id == 1
    assert validation.session_id == "jedi-hofx-orchestration-session"
    assert validation.audit_refs == ["audit-record:hofx-orchestration-seed"]
    assert validation.summary_metrics["primary_output"].endswith("hofx.out")
    assert validation.summary_metrics["ioda_groups_found"] == 3
    assert validation.summary_metrics["observer_output_detected"] == "True"
    assert "IODA groups detected: HofX, MetaData, ObsValue." in validation.messages
    assert diagnostic_summary.files_scanned == [artifact.stdout_path]
    assert bundle.validation is validation
    assert bundle.summary is diagnostic_summary
    assert artifact.output_files[0] in bundle.evidence_files
    assert artifact.reference_files[0] in bundle.evidence_files
    assert artifact.stdout_path in bundle.evidence_files
    assert bundle.metadata["diagnostic_files_scanned"] == 1
    assert bundle.metadata["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert policy_report.passed is True
    assert policy_report.decision == "allow"
    assert policy_report.evidence["diagnostic_files_scanned"] == 1
    assert policy_report.evidence["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert candidate_record.promoted is True
    assert candidate_record.candidate_id == "candidate-hofx-orchestration-1"
    events = session_store.get_events("jedi-hofx-orchestration-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    safety_gate_event = next(
        event for event in events if event.event_type == SessionEventType.SAFETY_GATE_EVALUATED
    )
    assert safety_gate_event.payload["diagnostic_files_scanned"] == 1
    assert safety_gate_event.payload["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert len(audit_log.by_kind("session.candidate_validated")) == 1
    assert len(audit_log.by_kind("session.safety_gate_evaluated")) == 1
    assert len(audit_log.by_kind("jedi.governance_handoff")) == 1
    handoff_record = audit_log.by_kind("jedi.governance_handoff")[0]
    assert handoff_record.payload["diagnostic_files_scanned"] == 1
    assert handoff_record.payload["ioda_groups_found"] == ["HofX", "MetaData", "ObsValue"]
    assert (
        "graph-candidate:candidate-hofx-orchestration-1" in provenance_graph.to_dict()["entities"]
    )
    assert all(ref.startswith("audit-record:") for ref in governance_refs["audit_refs"])
    assert "graph-version:1" in governance_refs["provenance_refs"]


@pytest.mark.asyncio
async def test_jedi_forecast_orchestration_happy_path_wires_real_run_evidence(
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
    version = engine.commit("jedi-forecast-orchestration-happy", candidate, report)

    gateway = JediGatewayComponent()
    environment = JediEnvironmentProbeComponent()
    compiler = JediConfigCompilerComponent()
    executor = JediExecutorComponent()
    validator = JediValidatorComponent()
    diagnostics = JediDiagnosticsCollectorComponent()
    policy = JediEvidencePolicy()
    governance = JediGovernanceAdapter()
    session_store = InMemorySessionStore()
    audit_log = AuditLog()
    provenance_graph = ProvGraph()
    await executor.activate(ComponentRuntime(storage_path=tmp_path))

    workspace = tmp_path / "jedi-forecast-workspace"
    (workspace / "testinput").mkdir(parents=True)
    initial_condition = workspace / "forecast-initial.nc"
    initial_condition.write_text("initial condition")

    task = gateway.issue_forecast_task(
        task_id="jedi-forecast-orchestration-1",
        execution_mode="real_run",
        binary_name="qgForecast.x",
        initial_condition_path=str(initial_condition),
        working_directory=str(workspace),
        candidate_id="candidate-forecast-orchestration-1",
        graph_version_id=version,
        session_id="jedi-forecast-orchestration-session",
        audit_refs=["audit-record:forecast-orchestration-seed"],
    )

    def fake_which(name: str) -> str | None:
        if name == "ldd":
            return "/usr/bin/ldd"
        if name == "qgForecast.x":
            return "/usr/bin/qgForecast.x"
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
    smoke_task = gateway.issue_smoke_task(
        environment_report,
        task_id="jedi-forecast-smoke-orchestration-1",
        execution_mode="validate_only",
        background_path=str(initial_condition),
    )
    plan = compiler.build_plan(task)

    monkeypatch.setattr(
        "metaharness_ext.jedi.executor.JediExecutorComponent._resolve_binary",
        lambda self, binary_name: f"/usr/bin/{Path(binary_name).name}",
    )

    def fake_run(command, *, cwd, text, capture_output, check, timeout):
        (cwd / "forecast.out").write_text("forecast output")
        (cwd / "forecast_reference.json").write_text('{"baseline": "forecast-reference"}')
        return type(
            "_ForecastCompletedProcess",
            (),
            {"returncode": 0, "stdout": "run ok\nforecast complete\n", "stderr": ""},
        )()

    monkeypatch.setattr("metaharness_ext.jedi.executor.subprocess.run", fake_run)

    artifact = executor.execute_plan(plan, environment_report=environment_report)
    diagnostic_summary = diagnostics.collect(artifact)
    validation = validator.validate_run_with_diagnostics(artifact, diagnostic_summary)
    bundle = build_evidence_bundle(artifact, validation, diagnostic_summary)
    policy_report = policy.evaluate(bundle)
    governance_refs = governance.emit_runtime_evidence(
        bundle,
        policy_report,
        session_store=session_store,
        audit_log=audit_log,
        provenance_graph=provenance_graph,
    )
    candidate_record = governance.build_candidate_record(bundle, policy_report)

    assert report.valid is True
    assert version == 1
    assert task.application_family == "forecast"
    assert task.executable.binary_name == "qgForecast.x"
    assert smoke_task.application_family == "forecast"
    assert smoke_task.executable.binary_name == "qgForecast.x"
    assert environment_report.binary_available is True
    assert environment_report.workspace_root == str(workspace)
    assert environment_report.workspace_testinput_present is True
    assert environment_report.data_prerequisites_ready is True
    assert environment_report.smoke_ready is True
    assert environment_report.smoke_candidate == "forecast"
    assert environment_report.ready_prerequisites == [
        "workspace testinput",
        "model initial-condition data prepared",
    ]
    assert plan.application_family == "forecast"
    assert plan.execution_mode == "real_run"
    assert plan.expected_outputs == ["forecast.out"]
    assert plan.expected_references == ["forecast_reference.json"]
    assert artifact.status == "completed"
    assert artifact.command == ["/usr/bin/qgForecast.x", "config.yaml"]
    assert any(path.endswith("forecast.out") for path in artifact.output_files)
    assert any(path.endswith("forecast_reference.json") for path in artifact.reference_files)
    assert artifact.result_summary["checkpoint_refs"] == [
        "checkpoint://jedi/prerequisite/workspace-testinput",
        "checkpoint://jedi/prerequisite/model-initial-condition-data-prepared",
    ]
    assert validation.passed is True
    assert validation.status == "executed"
    assert validation.policy_decision == "allow"
    assert validation.candidate_id == "candidate-forecast-orchestration-1"
    assert validation.graph_version_id == 1
    assert validation.session_id == "jedi-forecast-orchestration-session"
    assert validation.audit_refs == ["audit-record:forecast-orchestration-seed"]
    assert validation.summary_metrics["primary_output"].endswith("forecast.out")
    assert validation.summary_metrics["reference_count"] == 1.0
    assert diagnostic_summary.files_scanned == [artifact.stdout_path]
    assert bundle.validation is validation
    assert artifact.output_files[0] in bundle.evidence_files
    assert artifact.reference_files[0] in bundle.evidence_files
    assert artifact.stdout_path in bundle.evidence_files
    assert policy_report.passed is True
    assert policy_report.decision == "allow"
    assert policy_report.evidence["diagnostic_files_scanned"] == 1
    assert candidate_record.promoted is True
    assert candidate_record.candidate_id == "candidate-forecast-orchestration-1"
    events = session_store.get_events("jedi-forecast-orchestration-session")
    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_VALIDATED,
        SessionEventType.SAFETY_GATE_EVALUATED,
    ]
    assert len(audit_log.by_kind("jedi.governance_handoff")) == 1
    assert (
        "graph-candidate:candidate-forecast-orchestration-1"
        in provenance_graph.to_dict()["entities"]
    )
    assert all(ref.startswith("audit-record:") for ref in governance_refs["audit_refs"])
    assert "graph-version:1" in governance_refs["provenance_refs"]


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


@pytest.mark.asyncio
async def test_jedi_gateway_enforces_subject_claims_and_sandbox_policy() -> None:
    class _SandboxClient:
        def supports_tier(self, tier) -> bool:
            return tier.value == "gvisor"

    gateway = JediGatewayComponent(
        manifest=_jedi_gateway_manifest(
            credentials={"requires_subject": True, "required_claims": ["scope"]},
            sandbox={"tier": "gvisor"},
        )
    )
    await gateway.activate(ComponentRuntime(sandbox_client=_SandboxClient()))

    with pytest.raises(ValueError, match="requires subject_id"):
        gateway.issue_task(background_path="/tmp/background.nc")

    with pytest.raises(ValueError, match="missing required claims: scope"):
        gateway.issue_task(
            background_path="/tmp/background.nc",
            subject_id="service:jedi",
        )


@pytest.mark.asyncio
async def test_jedi_gateway_rejects_unsupported_sandbox_tier() -> None:
    class _SandboxClient:
        def supports_tier(self, tier) -> bool:
            return False

    gateway = JediGatewayComponent(manifest=_jedi_gateway_manifest(sandbox={"tier": "gvisor"}))
    await gateway.activate(ComponentRuntime(sandbox_client=_SandboxClient()))

    with pytest.raises(ValueError, match="sandbox policy requires tier 'gvisor'"):
        gateway.issue_local_ensemble_task(background_path="/tmp/background.nc")
