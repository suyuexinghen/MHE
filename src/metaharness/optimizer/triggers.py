"""Layered trigger mechanism for optimizer runs.

The roadmap mandates five trigger levels so operators can gate
optimization cycles at different granularities. Triggers are registered
with a :class:`LayeredTriggerSystem`; each layer has its own enablement
flag and threshold so cycles can be rate-limited at whichever level is
most stringent.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TriggerKind(str, Enum):
    """The five supported trigger kinds."""

    METRIC = "metric"  # level 1 - metric crossed a threshold
    EVENT = "event"  # level 2 - named event was published on the bus
    SCHEDULE = "schedule"  # level 3 - periodic timer
    MANUAL = "manual"  # level 4 - operator-initiated
    COMPOSITE = "composite"  # level 5 - combination of other triggers


@dataclass(slots=True)
class TriggerThreshold:
    """Threshold configuration for a metric or composite trigger."""

    min_value: float | None = None
    max_value: float | None = None
    min_delta: float | None = None
    min_interval_seconds: float = 0.0

    def crosses(self, current: float, previous: float | None, now: float, last: float) -> bool:
        if self.min_interval_seconds and (now - last) < self.min_interval_seconds:
            return False
        if self.min_value is not None and current < self.min_value:
            return False
        if self.max_value is not None and current > self.max_value:
            return False
        if self.min_delta is not None and previous is not None:
            if abs(current - previous) < self.min_delta:
                return False
        return True


@dataclass(slots=True)
class TriggerEvent:
    """Event emitted when a trigger fires."""

    trigger_id: str
    kind: TriggerKind
    value: Any = None
    reason: str = ""
    timestamp: float = field(default_factory=lambda: time.time())


@dataclass(slots=True)
class Trigger:
    """Declarative trigger definition.

    Triggers are inert data; :class:`LayeredTriggerSystem` evaluates them.
    ``predicate`` is an arbitrary callable for COMPOSITE triggers; other
    kinds use ``threshold`` for numeric evaluation.
    """

    trigger_id: str
    kind: TriggerKind
    enabled: bool = True
    threshold: TriggerThreshold | None = None
    predicate: Callable[[dict[str, Any]], bool] | None = None
    interval_seconds: float = 0.0
    metric_name: str | None = None
    event_name: str | None = None


class LayeredTriggerSystem:
    """Manages triggers across all five layers.

    Each call to :meth:`evaluate` returns the ordered list of events
    fired this tick. Callers feed in a ``context`` dict carrying metric
    readings and named events so the evaluator stays pure.
    """

    def __init__(self) -> None:
        self._triggers: dict[str, Trigger] = {}
        self._last_fire: dict[str, float | None] = {}
        self._last_value: dict[str, float] = {}
        self.history: list[TriggerEvent] = []

    # -------------------------------------------------------- registration

    def register(self, trigger: Trigger) -> None:
        if trigger.trigger_id in self._triggers:
            raise ValueError(f"trigger {trigger.trigger_id!r} already registered")
        self._triggers[trigger.trigger_id] = trigger

    def unregister(self, trigger_id: str) -> None:
        self._triggers.pop(trigger_id, None)
        self._last_fire.pop(trigger_id, None)
        self._last_value.pop(trigger_id, None)

    def triggers(self) -> Iterable[Trigger]:
        return list(self._triggers.values())

    def set_enabled(self, trigger_id: str, enabled: bool) -> None:
        trigger = self._triggers.get(trigger_id)
        if trigger is not None:
            trigger.enabled = enabled

    # ------------------------------------------------------------- evaluate

    def evaluate(self, context: dict[str, Any] | None = None) -> list[TriggerEvent]:
        ctx = context or {}
        metrics: dict[str, float] = dict(ctx.get("metrics") or {})
        events: set[str] = set(ctx.get("events") or [])
        manual: set[str] = set(ctx.get("manual") or [])
        now: float = float(ctx.get("now", time.time()))

        fired: list[TriggerEvent] = []
        for trigger in self._triggers.values():
            if not trigger.enabled:
                continue
            last_fire = self._last_fire.get(trigger.trigger_id)
            last_fire_value = last_fire if last_fire is not None else 0.0
            if trigger.kind == TriggerKind.METRIC and trigger.metric_name:
                value = metrics.get(trigger.metric_name)
                if value is None:
                    continue
                previous = self._last_value.get(trigger.trigger_id)
                if trigger.threshold is None or trigger.threshold.crosses(
                    value, previous, now, last_fire_value
                ):
                    fired.append(
                        TriggerEvent(
                            trigger_id=trigger.trigger_id,
                            kind=trigger.kind,
                            value=value,
                            reason=f"metric {trigger.metric_name}",
                            timestamp=now,
                        )
                    )
                    self._last_fire[trigger.trigger_id] = now
                self._last_value[trigger.trigger_id] = value
            elif trigger.kind == TriggerKind.EVENT and trigger.event_name:
                if trigger.event_name in events:
                    fired.append(
                        TriggerEvent(
                            trigger_id=trigger.trigger_id,
                            kind=trigger.kind,
                            value=trigger.event_name,
                            reason=f"event {trigger.event_name}",
                            timestamp=now,
                        )
                    )
                    self._last_fire[trigger.trigger_id] = now
            elif trigger.kind == TriggerKind.SCHEDULE and trigger.interval_seconds:
                # First tick after registration bootstraps the schedule so
                # cron-style triggers do not silently wait a full interval
                # before emitting.
                if last_fire is None or (now - last_fire) >= trigger.interval_seconds:
                    fired.append(
                        TriggerEvent(
                            trigger_id=trigger.trigger_id,
                            kind=trigger.kind,
                            reason="schedule",
                            timestamp=now,
                        )
                    )
                    self._last_fire[trigger.trigger_id] = now
            elif trigger.kind == TriggerKind.MANUAL:
                if trigger.trigger_id in manual:
                    fired.append(
                        TriggerEvent(
                            trigger_id=trigger.trigger_id,
                            kind=trigger.kind,
                            reason="manual",
                            timestamp=now,
                        )
                    )
                    self._last_fire[trigger.trigger_id] = now
            elif trigger.kind == TriggerKind.COMPOSITE and trigger.predicate:
                if trigger.predicate(ctx):
                    fired.append(
                        TriggerEvent(
                            trigger_id=trigger.trigger_id,
                            kind=trigger.kind,
                            reason="composite",
                            timestamp=now,
                        )
                    )
                    self._last_fire[trigger.trigger_id] = now

        self.history.extend(fired)
        return fired
