"""Tests for the layered trigger mechanism."""

from __future__ import annotations

import pytest

from metaharness.optimizer.triggers import (
    LayeredTriggerSystem,
    Trigger,
    TriggerKind,
    TriggerThreshold,
)


def test_metric_trigger_fires_once_threshold_crossed() -> None:
    system = LayeredTriggerSystem()
    system.register(
        Trigger(
            trigger_id="t-latency",
            kind=TriggerKind.METRIC,
            metric_name="latency",
            threshold=TriggerThreshold(max_value=100.0, min_interval_seconds=0),
        )
    )
    assert system.evaluate({"metrics": {"latency": 200.0}, "now": 0}) == []
    events = system.evaluate({"metrics": {"latency": 50.0}, "now": 1})
    assert len(events) == 1
    assert events[0].kind == TriggerKind.METRIC
    assert events[0].value == 50.0


def test_event_trigger_fires_on_named_event() -> None:
    system = LayeredTriggerSystem()
    system.register(Trigger(trigger_id="t-drift", kind=TriggerKind.EVENT, event_name="graph.drift"))
    events = system.evaluate({"events": {"graph.drift"}, "now": 0})
    assert [e.trigger_id for e in events] == ["t-drift"]


def test_schedule_trigger_respects_interval() -> None:
    system = LayeredTriggerSystem()
    system.register(Trigger(trigger_id="t-cron", kind=TriggerKind.SCHEDULE, interval_seconds=60))
    events = system.evaluate({"now": 0.0})
    assert len(events) == 1
    # Too soon.
    events = system.evaluate({"now": 30.0})
    assert events == []
    # After the interval.
    events = system.evaluate({"now": 70.0})
    assert len(events) == 1


def test_manual_trigger_requires_explicit_set() -> None:
    system = LayeredTriggerSystem()
    system.register(Trigger(trigger_id="t-op", kind=TriggerKind.MANUAL))
    assert system.evaluate({"manual": set(), "now": 0}) == []
    events = system.evaluate({"manual": {"t-op"}, "now": 1})
    assert len(events) == 1


def test_composite_trigger_uses_predicate() -> None:
    system = LayeredTriggerSystem()
    system.register(
        Trigger(
            trigger_id="t-composite",
            kind=TriggerKind.COMPOSITE,
            predicate=lambda ctx: ctx.get("force", False),
        )
    )
    assert system.evaluate({"force": False, "now": 0}) == []
    events = system.evaluate({"force": True, "now": 1})
    assert [e.reason for e in events] == ["composite"]


def test_disabled_trigger_does_not_fire() -> None:
    system = LayeredTriggerSystem()
    system.register(Trigger(trigger_id="t-off", kind=TriggerKind.MANUAL))
    system.set_enabled("t-off", False)
    assert system.evaluate({"manual": {"t-off"}, "now": 0}) == []


def test_duplicate_registration_raises() -> None:
    system = LayeredTriggerSystem()
    system.register(Trigger(trigger_id="t", kind=TriggerKind.MANUAL))
    with pytest.raises(ValueError):
        system.register(Trigger(trigger_id="t", kind=TriggerKind.MANUAL))
