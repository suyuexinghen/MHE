"""Tests for the lifecycle phase tracker."""

from __future__ import annotations

import pytest

from metaharness.core.lifecycle_tracker import LifecyclePhaseError, LifecycleTracker
from metaharness.sdk.lifecycle import ComponentPhase


def test_lifecycle_tracker_allows_canonical_sequence() -> None:
    tracker = LifecycleTracker()
    ordered = [
        ComponentPhase.DISCOVERED,
        ComponentPhase.VALIDATED_STATIC,
        ComponentPhase.ASSEMBLED,
        ComponentPhase.VALIDATED_DYNAMIC,
        ComponentPhase.ACTIVATED,
        ComponentPhase.COMMITTED,
        ComponentPhase.SUSPENDED,
    ]
    for phase in ordered:
        tracker.record("runtime.primary", phase)
    assert tracker.phase("runtime.primary") == ComponentPhase.SUSPENDED


def test_lifecycle_tracker_rejects_invalid_transition() -> None:
    tracker = LifecycleTracker()
    tracker.record("runtime.primary", ComponentPhase.DISCOVERED)
    with pytest.raises(LifecyclePhaseError):
        tracker.record("runtime.primary", ComponentPhase.COMMITTED)


def test_lifecycle_idempotent_same_phase() -> None:
    tracker = LifecycleTracker()
    tracker.record("runtime.primary", ComponentPhase.DISCOVERED)
    tracker.record("runtime.primary", ComponentPhase.DISCOVERED)
    assert tracker.phase("runtime.primary") == ComponentPhase.DISCOVERED
