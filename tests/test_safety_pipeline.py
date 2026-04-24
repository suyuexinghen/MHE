"""Safety-chain pipeline tests."""

from __future__ import annotations

from pathlib import Path

from metaharness.components.policy import PolicyComponent
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet, PromotionContext, ValidationIssue
from metaharness.core.mutation import MutationProposal
from metaharness.core.validators import validate_graph
from metaharness.safety import (
    ABShadowTester,
    AutoRollback,
    GateDecision,
    HookRegistry,
    PolicyVetoGate,
    SafetyPipeline,
    SandboxValidator,
)
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def _registry(manifest_dir: Path, names: list[str]) -> ComponentRegistry:
    registry = ComponentRegistry()
    for name in names:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())
    return registry


def _proposal(manifest_dir: Path, graphs_dir: Path) -> tuple[MutationProposal, ComponentRegistry]:
    registry = _registry(manifest_dir, ["gateway", "runtime", "executor", "evaluation"])
    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    pending = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    proposal = MutationProposal(proposal_id="p-1", description="swap", pending=pending)
    return proposal, registry


def test_level_1_sandbox_validator_allows_valid_candidate(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    gate = SandboxValidator(registry)
    result = gate.evaluate(proposal)
    assert result.decision == GateDecision.ALLOW


def test_level_1_sandbox_validator_rejects_invalid_candidate(manifest_dir: Path) -> None:
    registry = _registry(manifest_dir, ["gateway", "runtime"])
    pending = PendingConnectionSet(nodes=[], edges=[])
    proposal = MutationProposal(proposal_id="p-bad", description="empty", pending=pending)
    gate = SandboxValidator(registry)
    result = gate.evaluate(proposal)
    # Empty graph is trivially valid, so pass a malformed edge instead.
    from metaharness.core.models import ComponentNode, ConnectionEdge

    pending = PendingConnectionSet(
        nodes=[
            ComponentNode(
                component_id="runtime.primary",
                component_type="Runtime",
                implementation="x",
                version="0.1.0",
            )
        ],
        edges=[
            ConnectionEdge(
                connection_id="c1",
                source="ghost.primary.task",
                target="runtime.primary.task",
                payload="TaskRequest",
                mode="sync",
                policy="required",
            )
        ],
    )
    proposal = MutationProposal(proposal_id="p-bad", description="bad", pending=pending)
    result = gate.evaluate(proposal)
    assert result.decision == GateDecision.REJECT


def test_level_2_ab_shadow_allows_matching_runs() -> None:
    gate = ABShadowTester(
        baseline_runner=lambda _p, t: t.get("value"),
        candidate_runner=lambda _p, t: t.get("value"),
    )
    result = gate.evaluate(
        MutationProposal(
            proposal_id="p-ab",
            description="",
            pending=PendingConnectionSet(),
        ),
        context={"trials": [{"value": 1}, {"value": 2}]},
    )
    assert result.decision == GateDecision.ALLOW
    assert len(gate.history) == 2


def test_level_2_ab_shadow_rejects_divergence() -> None:
    gate = ABShadowTester(
        baseline_runner=lambda _p, _t: 1,
        candidate_runner=lambda _p, _t: 2,
    )
    result = gate.evaluate(
        MutationProposal(
            proposal_id="p-ab",
            description="",
            pending=PendingConnectionSet(),
        ),
        context={"trials": [{}]},
    )
    assert result.decision == GateDecision.REJECT


def test_level_2_ab_shadow_defers_without_runners() -> None:
    gate = ABShadowTester()
    result = gate.evaluate(
        MutationProposal(proposal_id="p", description="", pending=PendingConnectionSet())
    )
    assert result.decision == GateDecision.DEFER


def test_level_3_policy_veto_delegates_to_reviewer(manifest_dir: Path, graphs_dir: Path) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    policy = PolicyComponent()
    gate = PolicyVetoGate(policy.review_proposal, registry)
    result = gate.evaluate(proposal)
    assert result.decision == GateDecision.ALLOW
    assert len(policy.proposal_reviews) == 1


def test_level_4_auto_rollback_triggers_on_probe_failure(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())
    # Commit a first graph so rollback has a target.
    _, report_v1 = engine.stage(proposal.pending)
    engine.commit("v1", *engine.stage(proposal.pending))
    # Commit a second graph.
    engine.commit("v2", *engine.stage(proposal.pending))

    rollback = AutoRollback(engine)
    rollback.register_probe("latency", lambda _ctx: (False, "latency spike"))
    result = rollback.check()
    assert result.decision == GateDecision.REJECT
    assert rollback.events and rollback.events[0].probe == "latency"


def test_pipeline_runs_in_order_and_short_circuits(manifest_dir: Path, graphs_dir: Path) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    policy = PolicyComponent()
    pipeline = SafetyPipeline(
        [
            SandboxValidator(registry),
            ABShadowTester(
                baseline_runner=lambda _p, _t: 1,
                candidate_runner=lambda _p, _t: 2,
            ),
            PolicyVetoGate(policy.review_proposal, registry),
        ]
    )
    result = pipeline.evaluate(proposal, context={"trials": [{}]})
    assert result.allowed is False
    assert result.rejected_by == "level_2_ab_shadow"
    # Level 3 must not run once level 2 rejects.
    assert len(result.results) == 2


def test_pipeline_guard_hook_vetoes_before_gates(manifest_dir: Path, graphs_dir: Path) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    hooks = HookRegistry()
    hooks.add_guard(lambda _p: False)
    pipeline = SafetyPipeline([SandboxValidator(registry)], hooks=hooks)
    result = pipeline.evaluate(proposal)
    assert result.allowed is False
    assert result.guard_vetoed is True
    assert result.results == []


def test_pipeline_mutator_transforms_proposal(manifest_dir: Path, graphs_dir: Path) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    hooks = HookRegistry()
    hooks.add_mutator(lambda p: p.model_copy(update={"description": p.description + "!"}))
    pipeline = SafetyPipeline([SandboxValidator(registry)], hooks=hooks)
    result = pipeline.evaluate(proposal)
    assert result.mutated is True
    assert result.proposal.description.endswith("!")


def test_pipeline_evaluate_graph_promotion_delegates_to_reviewer(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    _, registry = _proposal(manifest_dir, graphs_dir)
    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    policy = PolicyComponent()
    pipeline = SafetyPipeline()

    allowed_promotion = PromotionContext(
        candidate_id="candidate-1",
        candidate_snapshot=snapshot,
        validation_report=validate_graph(snapshot, registry),
        proposed_graph_version=1,
    )
    allowed = pipeline.evaluate_graph_promotion(
        allowed_promotion,
        reviewer=policy.review_graph_promotion,
    )
    assert allowed.allowed is True
    assert allowed.results[-1].decision == GateDecision.ALLOW

    blocked_report = validate_graph(snapshot, registry)
    blocked_report.issues.append(
        ValidationIssue(
            code="policy_block",
            message="blocked",
            subject="policy.primary",
            blocks_promotion=True,
        )
    )
    rejected = pipeline.evaluate_graph_promotion(
        allowed_promotion.model_copy(update={"validation_report": blocked_report}),
        reviewer=policy.review_graph_promotion,
    )
    assert rejected.allowed is False
    assert rejected.rejected_by == "policy_review"


def test_pipeline_rejects_promotion_when_protected_components_are_flagged(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    _, registry = _proposal(manifest_dir, graphs_dir)
    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    policy = PolicyComponent()

    report = validate_graph(snapshot, registry)
    report.issues.append(
        ValidationIssue(
            code="protected_component_change",
            message="protected graph segment requires explicit authority",
            subject="policy.primary",
            blocks_promotion=True,
        )
    )
    promotion = PromotionContext(
        candidate_id="candidate-protected",
        candidate_snapshot=snapshot,
        validation_report=report,
        proposed_graph_version=2,
        rollback_target=1,
        affected_protected_components=["policy.primary"],
    )

    result = SafetyPipeline().evaluate_graph_promotion(
        promotion,
        reviewer=policy.review_graph_promotion,
    )

    assert result.allowed is False
    assert result.rejected_by == "policy_review"
    assert "protected_component_change:policy.primary" == result.rejected_reason
    assert result.promotion is promotion
    assert result.results[-1].evidence["decision_id"] == "candidate-protected"


def test_connection_engine_invalid_commit_preserves_active_graph(
    manifest_dir: Path, graphs_dir: Path
) -> None:
    proposal, registry = _proposal(manifest_dir, graphs_dir)
    engine = ConnectionEngine(registry, GraphVersionStore())

    active_snapshot, active_report = engine.stage(proposal.pending)
    committed_version = engine.commit("candidate-active", active_snapshot, active_report)

    assert committed_version == active_snapshot.graph_version
    assert engine.version_store.state.active_graph_version == active_snapshot.graph_version
    assert registry.active_graph == active_snapshot

    from metaharness.core.models import ComponentNode, ConnectionEdge

    bad_pending = PendingConnectionSet(
        nodes=[
            ComponentNode(
                component_id="runtime.primary",
                component_type="Runtime",
                implementation="x",
                version="0.1.0",
            )
        ],
        edges=[
            ConnectionEdge(
                connection_id="broken-edge",
                source="ghost.primary.task",
                target="runtime.primary.task",
                payload="TaskRequest",
                mode="sync",
                policy="required",
            )
        ],
    )
    bad_snapshot, bad_report = engine.stage(bad_pending)

    rejected_version = engine.commit("candidate-invalid", bad_snapshot, bad_report)

    assert bad_report.valid is False
    assert rejected_version == active_snapshot.graph_version
    assert engine.version_store.state.active_graph_version == active_snapshot.graph_version
    assert registry.active_graph == active_snapshot
    assert engine.version_store.candidates[-1].candidate_id == "candidate-invalid"
    assert engine.version_store.candidates[-1].promoted is False
