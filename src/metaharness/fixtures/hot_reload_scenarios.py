"""Evaluation scenarios for the hot-reload orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HotReloadScenario:
    """Scenario description for a hot-reload evaluation run."""

    scenario_id: str
    description: str
    outgoing_state: dict[str, Any] = field(default_factory=dict)
    delta: dict[str, Any] | None = None
    incoming_fails: bool = False
    expected_success: bool = True
    expected_outgoing_resumed: bool = False


def all_hot_reload_scenarios() -> list[HotReloadScenario]:
    """Canonical set of hot-reload scenarios bundled with the tree."""

    return [
        HotReloadScenario(
            scenario_id="HR-happy-path",
            description="Clean hand-over preserves state and applies delta.",
            outgoing_state={"counter": 7},
            delta={"added": True},
            expected_success=True,
        ),
        HotReloadScenario(
            scenario_id="HR-migration-failure",
            description="Migration adapter raises; saga restores the outgoing instance.",
            outgoing_state={"counter": 7},
            incoming_fails=True,
            expected_success=False,
            expected_outgoing_resumed=True,
        ),
        HotReloadScenario(
            scenario_id="HR-empty-state",
            description="Swap with no initial state still succeeds.",
            expected_success=True,
        ),
    ]
