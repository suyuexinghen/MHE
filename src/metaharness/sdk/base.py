"""Base component interface for Meta-Harness."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.runtime import ComponentRuntime


class HarnessComponent(ABC):
    """Abstract component base class.

    Implements the full staged lifecycle hook surface described in the
    master roadmap and the wiki: ``declare_interface``, ``activate``,
    ``deactivate``, ``export_state``, ``import_state``, ``transform_state``,
    and ``health_check``. Concrete components only need to override the
    abstract hooks; the defaults are safe no-ops for the rest.
    """

    protected: bool = False

    @abstractmethod
    def declare_interface(self, api: HarnessAPI) -> None:
        """Declare contracts and intents without I/O."""

    @abstractmethod
    async def activate(self, runtime: ComponentRuntime) -> None:
        """Start the component and acquire runtime resources."""

    @abstractmethod
    async def deactivate(self) -> None:
        """Stop the component and release runtime resources."""

    async def export_state(self) -> dict[str, Any]:
        """Export component state for replacement or checkpointing."""

        return {}

    async def import_state(self, state: Mapping[str, Any]) -> None:
        """Import previously exported component state."""

        return None

    async def suspend(self) -> None:
        """Pause input processing in preparation for a hot swap.

        Default implementation is a no-op. Concrete components should stop
        reading from their inputs, drain in-flight work, and leave the
        component in a quiesced state where ``export_state`` is safe to
        call.
        """

        return None

    async def resume(self, new_state: Mapping[str, Any] | None = None) -> None:
        """Resume processing, optionally rehydrating from ``new_state``.

        The default calls :meth:`import_state` when a state mapping is
        provided, then returns. Concrete components typically re-arm
        timers / re-open connections in addition to rehydrating state.
        """

        if new_state is not None:
            await self.import_state(new_state)
        return None

    async def transform_state(
        self,
        old_state: Mapping[str, Any],
        delta: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Apply a state migration ``tau: S_old x deltaP -> S_new``.

        The default implementation shallow-merges ``delta`` onto
        ``old_state``; migration adapters override this to perform
        component-specific transformations.
        """

        merged: dict[str, Any] = dict(old_state)
        if delta:
            merged.update(delta)
        return merged

    def health_check(self) -> dict[str, Any]:
        """Return lightweight health information."""

        return {"status": "unknown"}
