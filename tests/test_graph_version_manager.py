"""GraphVersionManager lifecycle and retirement tests."""

from __future__ import annotations

from metaharness.core.graph_versions import GraphVersionManager, GraphVersionStore
from metaharness.core.models import GraphSnapshot


def _snapshot(v: int) -> GraphSnapshot:
    return GraphSnapshot(graph_version=v)


def test_cutover_and_rollback_round_trip() -> None:
    mgr = GraphVersionManager()
    mgr.cutover(_snapshot(1))
    mgr.cutover(_snapshot(2))
    assert mgr.active_version == 2
    assert mgr.rollback_target == 1
    restored = mgr.rollback()
    assert restored.graph_version == 1
    assert mgr.active_version == 1


def test_retire_moves_old_versions_to_archive() -> None:
    store = GraphVersionStore(retention=2)
    mgr = GraphVersionManager(store, retention=2)
    mgr.cutover(_snapshot(1))
    mgr.cutover(_snapshot(2))
    mgr.cutover(_snapshot(3))
    # retention=2 keeps active+rollback; older snapshots are archived.
    assert mgr.active_version == 3
    assert mgr.rollback_target == 2
    assert 1 in mgr.archived_versions
    assert 1 not in mgr.snapshots


def test_rollback_rehydrates_archived_snapshot() -> None:
    store = GraphVersionStore(retention=1)
    mgr = GraphVersionManager(store, retention=1)
    mgr.cutover(_snapshot(1))
    mgr.cutover(_snapshot(2))
    # version 1 was archived because retention=1; rollback target still set.
    assert 1 in mgr.archived_versions
    restored = mgr.rollback()
    assert restored.graph_version == 1
