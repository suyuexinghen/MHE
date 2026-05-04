"""Assembly lineage and copy-count companion service tests."""

from __future__ import annotations

from metaharness.core.assembly import AssemblyLedger, AssemblyRecord, CopyCountIndex


def test_assembly_ledger_appends_and_queries_records() -> None:
    ledger = AssemblyLedger()
    component = ledger.record_component_registered(
        "runtime.primary",
        manifest_id="runtime",
        graph_version=1,
        source_refs=["entry:runtime:RuntimeComponent"],
    )
    candidate = ledger.record_graph_candidate(
        "candidate-1",
        graph_version=2,
        component_refs=["runtime.primary"],
        edge_refs=["edge-1"],
        parent_refs=["graph-version:1"],
        validation_refs=["validation:valid"],
    )

    assert component.artifact_kind == "component"
    assert component.lineage_status == "component_registered"
    assert component.source_refs == ["entry:runtime:RuntimeComponent", "manifest:runtime"]
    assert candidate.artifact_ref == "graph-candidate:candidate-1"
    assert candidate.assembly_context["edge_refs"] == ["edge-1"]
    assert ledger.records_for_candidate("candidate-1") == [candidate]
    assert ledger.records_for_graph_version(2) == [candidate]
    assert ledger.records_for_artifact("runtime.primary") == [component]
    assert ledger.records == [component, candidate]


def test_copy_count_index_isolates_artifact_counters() -> None:
    index = CopyCountIndex()

    index.mark_registered("runtime.primary")
    index.mark_candidate_member("runtime.primary")
    index.mark_committed_member("runtime.primary")
    index.mark_dependency("policy.primary")

    runtime = index.record_for("runtime.primary")
    policy = index.record_for("policy.primary")
    assert runtime.registered_count == 1
    assert runtime.candidate_membership_count == 1
    assert runtime.committed_membership_count == 1
    assert runtime.graph_reuse_count == 1
    assert policy.dependency_count == 1
    assert policy.registered_count == 0


def test_health_summary_reports_missing_lineage_and_low_copy_refs() -> None:
    ledger = AssemblyLedger()
    index = CopyCountIndex()
    ledger.record_component_registered("runtime.primary", manifest_id="runtime")
    index.mark_committed_member("runtime.primary")

    summary = ledger.health_summary(
        candidate_id="candidate-1",
        graph_version=2,
        component_refs=["runtime.primary", "policy.primary"],
        edge_count=1,
        copy_count_index=index,
    )

    assert summary.component_count == 2
    assert summary.edge_count == 1
    assert summary.lineage_completeness == 0.5
    assert summary.lineage_status == "partial"
    assert summary.new_component_refs == ["policy.primary"]
    assert summary.low_copy_component_refs == ["policy.primary"]
    assert summary.warnings == [
        "assembly_lineage_missing",
        "low_copy_components",
        "assembly_lineage_partial",
    ]


def test_dependency_graph_snapshot_scores_longest_path_and_reuse() -> None:
    ledger = AssemblyLedger()
    index = CopyCountIndex()
    for component_ref in ["a.primary", "b.primary", "c.primary"]:
        ledger.record_component_registered(component_ref)
    index.mark_committed_member("a.primary")
    index.mark_committed_member("b.primary")

    snapshot = ledger.record_dependency_graph(
        candidate_id="candidate-dag",
        graph_version=3,
        component_refs=["a.primary", "b.primary", "c.primary"],
        dependency_edges=[("a.primary", "b.primary"), ("b.primary", "c.primary")],
        parent_refs=["graph-version:2"],
        evidence_refs=["validation:valid"],
        copy_count_index=index,
    )

    assert snapshot.assembly_index == 3
    assert snapshot.lineage_completeness == 1.0
    assert snapshot.lineage_status == "complete"
    assert snapshot.history_folding_ratio == 2 / 3
    assert snapshot.low_copy_critical_dependency_count == 1
    assert [edge.source_ref for edge in snapshot.edges] == ["a.primary", "b.primary"]
    assert ledger.dependency_graphs_for_candidate("candidate-dag") == [snapshot]
    assert ledger.dependency_graphs_for_graph_version(3) == [snapshot]


def test_health_summary_includes_dependency_graph_evidence() -> None:
    ledger = AssemblyLedger()
    index = CopyCountIndex()
    for component_ref in ["a.primary", "b.primary"]:
        ledger.record_component_registered(component_ref)
    snapshot = ledger.record_dependency_graph(
        candidate_id="candidate-dag",
        graph_version=3,
        component_refs=["a.primary", "b.primary"],
        dependency_edges=[("a.primary", "b.primary")],
        evidence_refs=["validation:valid"],
        copy_count_index=index,
    )
    persisted = ledger.mark_dependency_graph_persisted(snapshot.snapshot_id, "snapshot-1")

    summary = ledger.health_summary(
        candidate_id="candidate-dag",
        graph_version=3,
        component_refs=["a.primary", "b.primary"],
        edge_count=1,
        copy_count_index=index,
        dependency_graph_snapshot=persisted,
    )

    assert summary.assembly_index == 2
    assert summary.dependency_graph_ref == snapshot.snapshot_id
    assert summary.evidence_refs == ["validation:valid", "artifact-snapshot:snapshot-1"]
    assert summary.low_copy_critical_dependency_count == 2
    assert "low_copy_critical_dependencies" in summary.warnings


def test_assembly_ledger_accepts_prebuilt_records() -> None:
    ledger = AssemblyLedger()
    record = ledger.append(AssemblyRecord(artifact_ref="custom", artifact_kind="note"))

    assert ledger.records == [record]
