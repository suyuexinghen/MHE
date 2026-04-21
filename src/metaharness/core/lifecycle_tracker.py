"""Explicit lifecycle phase tracking for components and graphs."""

from __future__ import annotations

from metaharness.sdk.lifecycle import ComponentPhase

_ALLOWED_TRANSITIONS: dict[ComponentPhase, set[ComponentPhase]] = {
    ComponentPhase.DISCOVERED: {ComponentPhase.VALIDATED_STATIC, ComponentPhase.FAILED},
    ComponentPhase.VALIDATED_STATIC: {ComponentPhase.ASSEMBLED, ComponentPhase.FAILED},
    ComponentPhase.ASSEMBLED: {ComponentPhase.VALIDATED_DYNAMIC, ComponentPhase.FAILED},
    ComponentPhase.VALIDATED_DYNAMIC: {ComponentPhase.ACTIVATED, ComponentPhase.FAILED},
    ComponentPhase.ACTIVATED: {
        ComponentPhase.COMMITTED,
        ComponentPhase.SUSPENDED,
        ComponentPhase.FAILED,
    },
    ComponentPhase.COMMITTED: {ComponentPhase.SUSPENDED, ComponentPhase.FAILED},
    ComponentPhase.SUSPENDED: {ComponentPhase.ACTIVATED, ComponentPhase.FAILED},
    ComponentPhase.FAILED: set(),
}


class LifecyclePhaseError(RuntimeError):
    """Raised when an invalid lifecycle transition is attempted."""


class LifecycleTracker:
    """Track and enforce lifecycle phase transitions per component id."""

    def __init__(self) -> None:
        self._phases: dict[str, ComponentPhase] = {}

    def record(self, component_id: str, phase: ComponentPhase) -> None:
        """Record or advance a component into a new phase."""

        current = self._phases.get(component_id)
        if current is None:
            self._phases[component_id] = phase
            return
        if current == phase:
            return
        if phase not in _ALLOWED_TRANSITIONS.get(current, set()):
            raise LifecyclePhaseError(
                f"Illegal transition for {component_id}: {current.value} -> {phase.value}"
            )
        self._phases[component_id] = phase

    def phase(self, component_id: str) -> ComponentPhase | None:
        """Return the current phase for a component id."""

        return self._phases.get(component_id)

    def snapshot(self) -> dict[str, ComponentPhase]:
        """Return a copy of all tracked component phases."""

        return dict(self._phases)

    def reset(self, component_id: str) -> None:
        """Remove a component from tracking."""

        self._phases.pop(component_id, None)
