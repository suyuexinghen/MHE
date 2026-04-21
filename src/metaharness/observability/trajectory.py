"""Execution trajectory persistence.

A :class:`Trajectory` captures every observable step a task went through
(component ids, phases, outputs, timestamps). The :class:`TrajectoryStore`
persists them in memory with simple flush-to-disk support so SRE tooling
and the optimizer can both consume the same record shape.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TrajectoryStep:
    """A single step in a task trajectory."""

    timestamp: float
    component_id: str
    phase: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Trajectory:
    """All steps recorded for one task execution."""

    trajectory_id: str
    trace_id: str | None = None
    steps: list[TrajectoryStep] = field(default_factory=list)
    started_at: float = field(default_factory=lambda: time.time())
    finished_at: float | None = None

    def append(
        self, component_id: str, phase: str, detail: dict[str, Any] | None = None
    ) -> TrajectoryStep:
        step = TrajectoryStep(
            timestamp=time.time(),
            component_id=component_id,
            phase=phase,
            detail=dict(detail or {}),
        )
        self.steps.append(step)
        return step

    def finish(self) -> None:
        self.finished_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "trace_id": self.trace_id,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "steps": [
                {
                    "timestamp": step.timestamp,
                    "component_id": step.component_id,
                    "phase": step.phase,
                    "detail": step.detail,
                }
                for step in self.steps
            ],
        }


class TrajectoryStore:
    """In-memory trajectory store with optional file persistence."""

    def __init__(self, *, capacity: int = 1024, path: Path | None = None) -> None:
        self.capacity = max(1, capacity)
        self.path = path
        self._trajectories: dict[str, Trajectory] = {}
        self._order: list[str] = []

    def start(self, *, trace_id: str | None = None) -> Trajectory:
        tid = uuid.uuid4().hex
        traj = Trajectory(trajectory_id=tid, trace_id=trace_id)
        self._trajectories[tid] = traj
        self._order.append(tid)
        while len(self._order) > self.capacity:
            dropped = self._order.pop(0)
            self._trajectories.pop(dropped, None)
        return traj

    def get(self, trajectory_id: str) -> Trajectory | None:
        return self._trajectories.get(trajectory_id)

    def all(self) -> list[Trajectory]:
        return [self._trajectories[tid] for tid in self._order]

    def by_trace(self, trace_id: str) -> list[Trajectory]:
        return [t for t in self.all() if t.trace_id == trace_id]

    def flush(self, path: Path | None = None) -> Path:
        """Serialize all trajectories to a JSONL file."""

        target = path or self.path
        if target is None:
            raise ValueError("no path provided for trajectory flush")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w") as fh:
            for traj in self.all():
                fh.write(json.dumps(traj.to_dict()) + "\n")
        return target
