from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness_ext.ai4pde.components.evidence_manager import EvidenceManagerComponent
from metaharness_ext.ai4pde.components.experiment_memory import ExperimentMemoryComponent
from metaharness_ext.ai4pde.components.method_router import MethodRouterComponent
from metaharness_ext.ai4pde.components.pde_gateway import PDEGatewayComponent
from metaharness_ext.ai4pde.components.physics_validator import PhysicsValidatorComponent
from metaharness_ext.ai4pde.components.problem_formulator import ProblemFormulatorComponent
from metaharness_ext.ai4pde.components.reference_solver import ReferenceSolverComponent
from metaharness_ext.ai4pde.components.solver_executor import SolverExecutorComponent

AI4PDE_COMPONENTS = [
    "pde_gateway",
    "problem_formulator",
    "method_router",
    "solver_executor",
    "reference_solver",
    "physics_validator",
    "evidence_manager",
    "experiment_memory",
]


def _build_registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in AI4PDE_COMPONENTS:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_ai4pde_minimal_path_runs(examples_dir: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "ai4pde"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "ai4pde-minimal.xml")
    candidate, report = engine.stage(PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges))
    version = engine.commit("ai4pde-minimal", candidate, report)

    gateway = PDEGatewayComponent()
    formulator = ProblemFormulatorComponent()
    router = MethodRouterComponent()
    executor = SolverExecutorComponent()
    validator = PhysicsValidatorComponent()
    evidence = EvidenceManagerComponent()

    task = gateway.issue_task("solve Laplace equation", task_id="demo-1")
    formulated = formulator.formulate(task)
    plan = router.build_plan(formulated)
    run_artifact = executor.execute_plan(plan)
    validation_bundle = validator.validate_run(run_artifact, graph_version_id=version)
    evidence_bundle = evidence.assemble_evidence(run_artifact, validation_bundle)

    assert report.valid is True
    assert plan.selected_method.value == "pinn_strong"
    assert plan.template_id == "forward-solid-mechanics"
    assert plan.graph_family == "template::forward-solid-mechanics"
    assert run_artifact.status == "executed"
    assert validation_bundle.summary["status"] == "accept"
    assert evidence_bundle.graph_version_id == 1
    assert evidence_bundle.graph_metadata["graph_family"] == "ai4pde-minimal"


def test_ai4pde_baseline_path_runs(examples_dir: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "ai4pde"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(graphs_dir / "ai4pde-baseline.xml")
    candidate, report = engine.stage(PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges))
    version = engine.commit("ai4pde-baseline", candidate, report)

    gateway = PDEGatewayComponent()
    formulator = ProblemFormulatorComponent()
    router = MethodRouterComponent()
    executor = SolverExecutorComponent()
    reference_solver = ReferenceSolverComponent()
    validator = PhysicsValidatorComponent()
    evidence = EvidenceManagerComponent()
    memory = ExperimentMemoryComponent()

    task = gateway.issue_task("solve Laplace equation with baseline", task_id="demo-2")
    formulated = formulator.formulate(task)
    plan = router.build_plan(formulated)
    run_artifact = executor.execute_plan(plan)
    reference_result = reference_solver.run_reference(plan)
    validation_bundle = validator.validate_run(
        run_artifact,
        graph_version_id=version,
        reference_result=reference_result,
    )
    evidence_bundle = evidence.assemble_evidence(
        run_artifact,
        validation_bundle,
        reference_result=reference_result,
        graph_family="ai4pde-baseline",
    )
    memory_record = memory.remember(validation_bundle, evidence_bundle)

    assert report.valid is True
    assert validation_bundle.reference_comparison["status"] == "better_or_equal"
    assert evidence_bundle.reference_comparison_refs == ["reference://reference-demo-2"]
    assert evidence_bundle.benchmark_snapshot_refs == ["benchmark://demo-2/baseline"]
    assert evidence_bundle.graph_metadata["graph_family"] == "ai4pde-baseline"
    assert memory_record["benchmark_snapshots"] == "1"
    assert memory_record["run_summaries"] == "1"
