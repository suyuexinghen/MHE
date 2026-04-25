from __future__ import annotations

from pathlib import Path

from metaharness.core.models import SessionEventType
from metaharness.observability.events import FileSessionStore, make_session_event
from metaharness.provenance import ArtifactSnapshotStore, ProvGraph, attach_scientific_lineage


def test_file_session_store_round_trip_and_checkpoint_index(tmp_path: Path) -> None:
    store = FileSessionStore(tmp_path / "session.jsonl")
    store.append(make_session_event("s1", SessionEventType.CANDIDATE_CREATED, graph_version=1))
    store.append(make_session_event("s1", SessionEventType.CHECKPOINT_SAVED, graph_version=1))
    store.append(make_session_event("s2", SessionEventType.CHECKPOINT_SAVED, graph_version=2))

    events = store.get_events("s1")

    assert [event.event_type for event in events] == [
        SessionEventType.CANDIDATE_CREATED,
        SessionEventType.CHECKPOINT_SAVED,
    ]
    assert store.latest_checkpoint_index("s1") == 1
    assert store.latest_checkpoint_index("s2") == 0


def test_artifact_snapshot_store_persists_history(tmp_path: Path) -> None:
    store = ArtifactSnapshotStore(path=tmp_path / "artifacts.jsonl")
    first = store.save("run_artifact", "run-1", {"status": "queued"}, graph_version=3)
    second = store.save(
        "run_artifact",
        "run-1",
        {"status": "completed"},
        graph_version=3,
        parent_snapshot_id=first.snapshot_id,
    )

    history = store.history("run-1")

    assert [snapshot.snapshot_id for snapshot in history] == [first.snapshot_id, second.snapshot_id]
    assert history[-1].parent_snapshot_id == first.snapshot_id
    assert (tmp_path / "artifacts.jsonl").exists()


def test_attach_scientific_lineage_creates_expected_chain() -> None:
    graph = ProvGraph()

    attach_scientific_lineage(
        graph,
        experiment_spec_id="exp-1",
        run_plan_id="plan-1",
        run_artifact_id="artifact-1",
        validation_report_id="validation-1",
        evidence_bundle_id="bundle-1",
    )

    data = graph.to_dict()
    assert "exp-1" in data["entities"]
    assert "bundle-1" in data["entities"]
    assert any(
        relation["subject"] == "bundle-1"
        and relation["object"] == "validation-1"
        and relation["kind"] == "wasDerivedFrom"
        for relation in data["relations"]
    )
