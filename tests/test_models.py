from pathlib import Path

from metaharness.config.xml_parser import parse_graph_xml
from metaharness.core.graph_versions import CandidateRecord, GraphVersionStore
from metaharness.core.models import GraphSnapshot, ValidationReport
from metaharness.sdk.loader import load_manifest


def test_manifest_round_trip(manifest_dir: Path) -> None:
    manifest = load_manifest(manifest_dir / "runtime.json")
    payload = manifest.model_dump()
    assert payload["name"] == "runtime"
    assert payload["contracts"]["inputs"][0]["name"] == "task"


def test_xml_to_internal_graph_round_trip(graphs_dir: Path) -> None:
    snapshot = parse_graph_xml(graphs_dir / "minimal-happy-path.xml")
    assert snapshot.graph_version == 1
    assert len(snapshot.nodes) == 4
    assert snapshot.edges[0].source == "gateway.primary.task"


def test_graph_version_store_commit_and_rollback() -> None:
    store = GraphVersionStore()
    first = GraphSnapshot(graph_version=1)
    second = GraphSnapshot(graph_version=2)
    report = ValidationReport(valid=True)
    store.save_candidate(
        CandidateRecord(candidate_id="c1", snapshot=first, report=report, promoted=True)
    )
    store.commit(first)
    store.save_candidate(
        CandidateRecord(candidate_id="c2", snapshot=second, report=report, promoted=True)
    )
    store.commit(second)

    rolled_back = store.rollback()

    assert rolled_back.graph_version == 1
    assert store.state.active_graph_version == 1
