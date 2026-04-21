from pathlib import Path

from metaharness.components.optimizer import OptimizerComponent
from metaharness.components.policy import PolicyComponent
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.core.mutation import MutationSubmitter
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness_ext.ai4pde.benchmarks import run_candidate_benchmark
from metaharness_ext.ai4pde.components.reference_solver import ReferenceSolverComponent
from metaharness_ext.ai4pde.contracts import (
    BudgetRecord,
    PDEPlan,
    ScientificEvidenceBundle,
    ValidationBundle,
)
from metaharness_ext.ai4pde.executors import run_pinn_strong
from metaharness_ext.ai4pde.mutations import build_proposals_from_signals, evaluate_triggers
from metaharness_ext.ai4pde.types import NextAction, SolverFamily

AI4PDE_COMPONENTS = [
    "pde_gateway",
    "problem_formulator",
    "method_router",
    "solver_executor",
    "reference_solver",
    "physics_validator",
    "evidence_manager",
    "experiment_memory",
    "risk_policy",
    "observability_hub",
    "knowledge_adapter",
]


def _build_registry(manifest_dir: Path) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in AI4PDE_COMPONENTS:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def test_ai4pde_mutation_proposals_remain_proposal_only(examples_dir: Path) -> None:
    manifest_dir = examples_dir / "manifests" / "ai4pde"
    graphs_dir = examples_dir / "graphs"
    registry = _build_registry(manifest_dir)
    store = GraphVersionStore()
    engine = ConnectionEngine(registry, store)
    policy = PolicyComponent()
    submitter = MutationSubmitter(engine=engine, reviewer=policy.review_proposal)
    optimizer = OptimizerComponent()

    baseline_snapshot = parse_graph_xml(graphs_dir / "ai4pde-expanded.xml")
    active_pending = PendingConnectionSet(nodes=baseline_snapshot.nodes, edges=baseline_snapshot.edges)
    candidate, report = engine.stage(active_pending)
    version = engine.commit("ai4pde-expanded", candidate, report)

    validation = ValidationBundle(
        validation_id="validation-m5",
        task_id="task-m5",
        graph_version_id=version,
        reference_comparison={"status": "worse_than_baseline"},
        violations=["baseline_divergence_exceeded"],
        next_action=NextAction.RETRY,
        summary={"status": "retry"},
    )
    evidence = ScientificEvidenceBundle(
        bundle_id="bundle-m5",
        task_id="task-m5",
        graph_version_id=version,
        graph_metadata={"graph_family": "ai4pde-expanded"},
    )
    signals = evaluate_triggers(
        validation_bundle=validation,
        evidence_bundle=evidence,
        budget=BudgetRecord(gpu_hours=10.0, hpc_quota=2.0),
        repeated_partial_count=2,
        repeated_failure_count=2,
    )
    proposals = build_proposals_from_signals(signals)

    assert store.state.active_graph_version == 1
    assert proposals
    assert all(not proposal.pending.nodes and not proposal.pending.edges for proposal in proposals)
    assert all(proposal.pending.mutations for proposal in proposals)

    record = optimizer.commit(proposals[0], submitter)

    assert record.decision.decision == "allow"
    assert record.graph_version == 2
    assert store.state.active_graph_version == 2
    assert record.proposal.pending.mutations
    assert not record.proposal.pending.nodes
    assert not record.proposal.pending.edges


def test_ai4pde_benchmark_runner_compares_candidate_and_active() -> None:
    plan = PDEPlan(
        plan_id="plan-bench",
        task_id="task-bench",
        selected_method=SolverFamily.PINN_STRONG,
    )
    active_run = run_pinn_strong(plan)
    candidate_run = active_run.model_copy(deep=True)
    candidate_run.run_id = "run-task-bench-candidate"
    candidate_run.result_summary["residual_l2"] = 0.005

    reference = ReferenceSolverComponent().run_reference(plan)
    validation = ValidationBundle(
        validation_id="validation-bench",
        task_id=plan.task_id,
        graph_version_id=1,
        reference_comparison={"status": "better_or_equal", "baseline_residual_l2": reference.summary["residual_l2"]},
        summary={"status": "accept"},
    )
    evidence = ScientificEvidenceBundle(
        bundle_id="bundle-bench",
        task_id=plan.task_id,
        graph_version_id=1,
        graph_metadata={"graph_family": "template::forward-solid-mechanics"},
    )

    snapshot = run_candidate_benchmark(
        active_run=active_run,
        candidate_run=candidate_run,
        validation_bundle=validation,
        evidence_bundle=evidence,
    )

    assert snapshot["improved"] is True
    assert snapshot["candidate_residual_l2"] == 0.005
    assert snapshot["graph_family"] == "template::forward-solid-mechanics"
    assert str(snapshot["evaluation_snapshot"]).startswith("evaluation://")
