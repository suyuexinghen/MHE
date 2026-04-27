"""Coordinated graph cutover drain support."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.event_bus import EventBus
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.lifecycle import ComponentPhase


class DrainState(str, Enum):
    """Lifecycle state for a graph cutover drain epoch."""

    OPEN = "open"
    DRAINING = "draining"
    QUIESCED = "quiesced"
    CUTTING_OVER = "cutting_over"
    REPLAYING = "replaying"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass(slots=True)
class DrainPolicy:
    """Bounded behavior for a graph cutover drain."""

    timeout_seconds: float = 1.0
    max_buffered_routes: int = 128
    max_buffered_events: int = 128
    replay_buffered: bool = True


@dataclass(slots=True)
class DrainEpoch:
    """One coordinated drain session around graph promotion."""

    epoch_id: str
    candidate_id: str
    graph_version: int
    state: DrainState = DrainState.OPEN
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    affected_components: list[str] = field(default_factory=list)
    suspended_components: list[str] = field(default_factory=list)
    previous_phases: dict[str, ComponentPhase] = field(default_factory=dict)
    buffered_routes: int = 0
    buffered_events: int = 0


@dataclass(slots=True)
class DrainReport:
    """Final accounting for a drain epoch."""

    epoch: DrainEpoch
    success: bool
    error: str | None = None


class DrainCoordinator:
    """Coordinates routing, event, and component quiescence for graph cutover."""

    def __init__(
        self,
        *,
        engine: ConnectionEngine,
        event_bus: EventBus,
        components: Mapping[str, HarnessComponent],
        lifecycle: Any | None = None,
        policy: DrainPolicy | None = None,
    ) -> None:
        self.engine = engine
        self.event_bus = event_bus
        self.components = components
        self.lifecycle = lifecycle
        self.policy = policy or DrainPolicy()
        self.current_epoch: DrainEpoch | None = None
        self.reports: list[DrainReport] = []

    def begin(
        self,
        *,
        candidate_id: str,
        graph_version: int,
        affected_components: list[str],
    ) -> DrainEpoch:
        if self.current_epoch is not None:
            raise RuntimeError(f"drain epoch '{self.current_epoch.epoch_id}' is already active")
        epoch = DrainEpoch(
            epoch_id=f"drain-{candidate_id}-{graph_version}",
            candidate_id=candidate_id,
            graph_version=graph_version,
            affected_components=list(dict.fromkeys(affected_components)),
        )
        epoch.state = DrainState.DRAINING
        self.current_epoch = epoch
        self.engine.begin_drain(
            epoch.epoch_id,
            max_buffered=self.policy.max_buffered_routes,
        )
        self.event_bus.begin_drain(
            epoch.epoch_id,
            max_buffered=self.policy.max_buffered_events,
        )
        self.engine.wait_for_inflight(timeout=self.policy.timeout_seconds)
        epoch.state = DrainState.QUIESCED
        self._suspend_components(epoch)
        epoch.state = DrainState.CUTTING_OVER
        return epoch

    def complete(self, epoch: DrainEpoch) -> DrainReport:
        self._ensure_current(epoch)
        try:
            self._resume_components(epoch)
            epoch.state = DrainState.REPLAYING
            route_results = self.engine.end_drain(replay=self.policy.replay_buffered)
            event_results = self.event_bus.end_drain(replay=self.policy.replay_buffered)
            epoch.buffered_routes = route_results
            epoch.buffered_events = event_results
            epoch.state = DrainState.COMPLETED
            epoch.completed_at = datetime.now(timezone.utc)
            report = DrainReport(epoch=epoch, success=True)
            self.reports.append(report)
            return report
        finally:
            self.current_epoch = None

    def abort(self, epoch: DrainEpoch, error: str | None = None) -> DrainReport:
        self._ensure_current(epoch)
        try:
            self._resume_components(epoch)
            self.engine.end_drain(replay=False)
            self.event_bus.end_drain(replay=False)
            epoch.state = DrainState.ABORTED
            epoch.completed_at = datetime.now(timezone.utc)
            report = DrainReport(epoch=epoch, success=False, error=error)
            self.reports.append(report)
            return report
        finally:
            self.current_epoch = None

    def _suspend_components(self, epoch: DrainEpoch) -> None:
        for component_id in epoch.affected_components:
            component = self.components.get(component_id)
            if component is None:
                continue
            previous_phase = None if self.lifecycle is None else self.lifecycle.phase(component_id)
            if previous_phase is not None:
                epoch.previous_phases[component_id] = previous_phase
            self._run_sync(component.suspend())
            epoch.suspended_components.append(component_id)
            if previous_phase in {ComponentPhase.ACTIVATED, ComponentPhase.COMMITTED}:
                self.lifecycle.record(component_id, ComponentPhase.SUSPENDED)

    def _resume_components(self, epoch: DrainEpoch) -> None:
        for component_id in reversed(epoch.suspended_components):
            component = self.components.get(component_id)
            if component is None:
                continue
            self._run_sync(component.resume())
            if (
                self.lifecycle is not None
                and self.lifecycle.phase(component_id) == ComponentPhase.SUSPENDED
            ):
                target_phase = epoch.previous_phases.get(component_id, ComponentPhase.ACTIVATED)
                self.lifecycle.record(component_id, ComponentPhase.ACTIVATED)
                if target_phase == ComponentPhase.COMMITTED:
                    self.lifecycle.record(component_id, ComponentPhase.COMMITTED)

    def _ensure_current(self, epoch: DrainEpoch) -> None:
        if self.current_epoch is not epoch:
            raise RuntimeError(f"drain epoch '{epoch.epoch_id}' is not active")

    @staticmethod
    def _run_sync(awaitable: Any) -> Any:
        if not asyncio.iscoroutine(awaitable):
            return awaitable
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        if loop.is_running():
            raise RuntimeError("drain coordinator cannot block inside a running event loop")
        return loop.run_until_complete(awaitable)
