from pathlib import Path

import pytest

from metaharness.components.optimizer import Observation, OptimizerComponent, ProposalEvaluation
from metaharness.components.policy import PolicyComponent
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.brain import BrainProvider
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.core.mutation import MutationProposal, MutationSubmitter
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry


def test_optimizer_emits_proposal_only() -> None:
    optimizer = OptimizerComponent()

    proposal = optimizer.propose("try a safer runtime")

    assert isinstance(proposal, MutationProposal)
    assert proposal.proposal_id.startswith("p-")
    assert proposal.description == "try a safer runtime"
    assert proposal.proposer_id == "optimizer"
    assert proposal.domain_payload is None
    assert isinstance(proposal.pending, PendingConnectionSet)

    # Hard invariant: the optimizer must not hold a direct write path into the
    # registry or the connection engine.
    assert not hasattr(optimizer, "write_registry")
    assert not hasattr(optimizer, "engine")
    assert not hasattr(optimizer, "registry")
    assert not hasattr(optimizer, "version_store")


def test_mutation_proposal_accepts_optional_domain_payload() -> None:
    proposal = MutationProposal(
        proposal_id="p-0001",
        description="domain-aware candidate",
        pending=PendingConnectionSet(),
        domain_payload={"study_id": "study-1", "shots": 1024},
    )

    dumped = proposal.model_dump()

    assert dumped["domain_payload"] == {"study_id": "study-1", "shots": 1024}
    restored = MutationProposal.model_validate(dumped)
    assert restored.domain_payload == {"study_id": "study-1", "shots": 1024}


def test_optimizer_commit_requires_submitter() -> None:
    optimizer = OptimizerComponent()
    proposal = optimizer.propose("noop")

    # ``commit`` exists as part of the observe/propose/evaluate/commit
    # lifecycle but it is strictly a pass-through: it must be given a
    # MutationSubmitter which itself routes through governance.
    with pytest.raises(TypeError):
        optimizer.commit(proposal)  # type: ignore[call-arg]


def test_optimizer_ids_are_monotonic() -> None:
    optimizer = OptimizerComponent()
    first = optimizer.propose("a")
    second = optimizer.propose("b")
    assert first.proposal_id != second.proposal_id


def test_optimizer_observe_and_evaluate() -> None:
    optimizer = OptimizerComponent()
    optimizer.observe(Observation(source="runtime", value=0.9, tags=("latency",)))
    assert len(optimizer.observations) == 1

    empty = optimizer.propose("empty")
    eval_empty = optimizer.evaluate(empty)
    assert isinstance(eval_empty, ProposalEvaluation)
    assert eval_empty.score == 0.0
    assert "empty_pending_set" in eval_empty.reasons
    assert eval_empty.evidence is not None
    assert eval_empty.evidence.score == 0.0
    assert eval_empty.evidence.evidence_refs == [empty.proposal_id]


def test_optimizer_commit_routes_through_submitter(manifest_dir: Path, graphs_dir: Path) -> None:
    registry = ComponentRegistry()
    for name in ["gateway", "runtime", "executor", "evaluation"]:
        manifest = load_manifest(manifest_dir / f"{name}.json")
        _, api = declare_component(f"{name}.primary", manifest)
        registry.register(f"{name}.primary", manifest, api.snapshot())

    engine = ConnectionEngine(registry, GraphVersionStore())
    policy = PolicyComponent()
    submitter = MutationSubmitter(engine=engine, reviewer=policy.review_proposal)
    optimizer = OptimizerComponent()

    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    pending = PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges)
    proposal = optimizer.propose("install happy path", pending=pending)
    record = optimizer.commit(proposal, submitter)

    assert record.decision.decision == "allow"
    assert record.graph_version == 1


class _RecordingBrainProvider(BrainProvider):
    def __init__(self) -> None:
        self.propose_calls: list[list[Observation]] = []
        self.evaluate_calls: list[tuple[str, list[Observation]]] = []

    def propose(
        self, optimizer: OptimizerComponent, observations: list[Observation]
    ) -> list[MutationProposal]:
        self.propose_calls.append(list(observations))
        pending = PendingConnectionSet()
        return [optimizer.propose("provider proposal", pending=pending, proposer_id="brain")]

    def evaluate(
        self,
        optimizer: OptimizerComponent,
        proposal: MutationProposal,
        observations: list[Observation],
    ) -> ProposalEvaluation:
        self.evaluate_calls.append((proposal.proposal_id, list(observations)))
        return ProposalEvaluation(proposal_id=proposal.proposal_id, score=0.75, reasons=["brain"])


def test_optimizer_brain_provider_overrides_default_planning_and_evaluation() -> None:
    provider = _RecordingBrainProvider()
    optimizer = OptimizerComponent(brain_provider=provider)
    observation = Observation(source="runtime", value={"latency": 12}, tags=("metrics",))
    optimizer.observe(observation)

    proposals = optimizer.propose_batch()

    assert len(proposals) == 1
    assert proposals[0].description == "provider proposal"
    assert proposals[0].proposer_id == "brain"
    assert provider.propose_calls == [[observation]]

    evaluation = optimizer.evaluate(proposals[0])

    assert evaluation.score == 0.75
    assert evaluation.reasons == ["brain"]
    assert provider.evaluate_calls == [(proposals[0].proposal_id, [observation])]
