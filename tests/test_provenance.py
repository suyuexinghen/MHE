"""Provenance, audit log, and counter-factual tests."""

from __future__ import annotations

from pathlib import Path

from metaharness.provenance import (
    AuditLog,
    CounterFactualDiagnosis,
    CounterFactualHypothesis,
    MerkleTree,
    ProvenanceQuery,
    ProvGraph,
    RelationKind,
)


def _sample_graph() -> ProvGraph:
    graph = ProvGraph()
    plan = graph.add_entity(id="plan-1", kind="plan")
    intermediate = graph.add_entity(id="intermediate-1", kind="plan")
    result = graph.add_entity(id="result-1", kind="task_result")
    activity = graph.add_activity(id="exec-1", kind="executor_run")
    agent = graph.add_agent(id="executor.primary", kind="component")

    graph.relate(result.id, RelationKind.WAS_GENERATED_BY, activity.id)
    graph.relate(activity.id, RelationKind.USED, plan.id)
    graph.relate(activity.id, RelationKind.USED, intermediate.id)
    graph.relate(activity.id, RelationKind.WAS_ASSOCIATED_WITH, agent.id)
    graph.relate(intermediate.id, RelationKind.WAS_DERIVED_FROM, plan.id)
    graph.relate(result.id, RelationKind.WAS_DERIVED_FROM, intermediate.id)
    return graph


def test_prov_graph_round_trip_to_dict() -> None:
    graph = _sample_graph()
    data = graph.to_dict()
    assert "plan-1" in data["entities"]
    assert any(r["kind"] == "wasGeneratedBy" for r in data["relations"])


def test_provenance_query_helpers() -> None:
    graph = _sample_graph()
    query = ProvenanceQuery(graph)
    assert query.activity_for("result-1") == "exec-1"
    assert query.agents_for("exec-1") == ["executor.primary"]
    assert set(query.inputs_of("exec-1")) == {"plan-1", "intermediate-1"}
    assert "plan-1" in query.ancestors_of("result-1")
    assert "result-1" in query.descendants_of("plan-1")
    summary = query.summarize("result-1")
    assert summary["activity"] == "exec-1"


def test_merkle_tree_append_and_root_hash_are_deterministic() -> None:
    tree_a = MerkleTree()
    tree_b = MerkleTree()
    for payload in ("a", "b", "c"):
        tree_a.append(payload)
        tree_b.append(payload)
    assert tree_a.root_hash() == tree_b.root_hash()
    assert len(tree_a) == 3


def test_merkle_proof_verifies_inclusion() -> None:
    tree = MerkleTree()
    for payload in ("a", "b", "c", "d"):
        tree.append(payload)
    proof = tree.proof_for(2)
    assert MerkleTree.verify("c", proof, tree.root_hash())
    assert not MerkleTree.verify("x", proof, tree.root_hash())


def test_audit_log_round_trip_and_verify(tmp_path: Path) -> None:
    log = AuditLog(path=tmp_path / "audit.jsonl")
    r1 = log.append("graph.commit", actor="harness", payload={"version": 1})
    r2 = log.append("graph.commit", actor="harness", payload={"version": 2})
    assert log.verify(r1)
    assert log.verify(r2)
    assert len(log.by_kind("graph.commit")) == 2
    # File written as JSONL.
    lines = (tmp_path / "audit.jsonl").read_text().splitlines()
    assert len(lines) == 2


def test_counter_factual_diagnosis_size_evaluator() -> None:
    graph = _sample_graph()
    diagnosis = CounterFactualDiagnosis(graph, CounterFactualDiagnosis.size_evaluator())
    results = diagnosis.score(
        [
            CounterFactualHypothesis(target_id="plan-1", description="no plan"),
            CounterFactualHypothesis(target_id="exec-1", description="no activity"),
        ]
    )
    by_target = {r.target_id: r for r in results}
    # Removing plan-1 drops one entity + two relations (used by exec + derived-from).
    assert by_target["plan-1"].delta < 0
    assert by_target["exec-1"].delta < 0


def test_counter_factual_derivation_depth_evaluator() -> None:
    graph = _sample_graph()
    evaluator = CounterFactualDiagnosis.derivation_depth_evaluator("result-1")
    baseline = evaluator(graph)
    assert baseline == 2.0
