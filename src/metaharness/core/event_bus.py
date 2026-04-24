"""Event bus with subscriber management and trace propagation."""

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

EventHandler = Callable[["Event"], Any] | Callable[["Event"], Awaitable[Any]]

# Promotion-related event names used by HarnessRuntime.commit_graph().
BEFORE_COMMIT_GRAPH = "before_commit_graph"
AFTER_COMMIT_GRAPH = "after_commit_graph"
CANDIDATE_REJECTED = "candidate_rejected"


@dataclass(slots=True)
class Event:
    """An event dispatched through the :class:`EventBus`."""

    name: str
    payload: Any
    trace_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


class EventBus:
    """In-process pub/sub with subscriber management and trace propagation.

    The engine uses the bus for ``event``-mode connections; components may
    subscribe directly to observe cross-cutting signals (audit, policy).
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._history: list[Event] = []
        self._trace_enabled = True

    def subscribe(self, name: str, handler: EventHandler) -> Callable[[], None]:
        """Subscribe ``handler`` to ``name``; returns an unsubscribe callable."""

        self._subscribers[name].append(handler)

        def _unsubscribe() -> None:
            if handler in self._subscribers.get(name, []):
                self._subscribers[name].remove(handler)

        return _unsubscribe

    def unsubscribe_all(self, name: str) -> None:
        """Drop every subscription for ``name``."""

        self._subscribers.pop(name, None)

    def subscriber_count(self, name: str) -> int:
        return len(self._subscribers.get(name, []))

    @property
    def history(self) -> list[Event]:
        return list(self._history)

    def publish(
        self,
        name: str,
        payload: Any,
        *,
        trace_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[Any]:
        """Synchronously dispatch ``payload`` to every subscriber of ``name``."""

        event = Event(
            name=name,
            payload=payload,
            trace_id=trace_id,
            headers=dict(headers or {}),
        )
        if self._trace_enabled:
            self._history.append(event)
        results: list[Any] = []
        for handler in list(self._subscribers.get(name, [])):
            value = handler(event)
            if inspect.isawaitable(value):
                value = _run_sync(value)
            results.append(value)
        return results

    async def publish_async(
        self,
        name: str,
        payload: Any,
        *,
        trace_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> list[Any]:
        """Async variant of :meth:`publish`."""

        event = Event(
            name=name,
            payload=payload,
            trace_id=trace_id,
            headers=dict(headers or {}),
        )
        if self._trace_enabled:
            self._history.append(event)
        results: list[Any] = []
        for handler in list(self._subscribers.get(name, [])):
            value = handler(event)
            if inspect.isawaitable(value):
                value = await value
            results.append(value)
        return results


def _run_sync(awaitable: Awaitable[Any]) -> Any:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return awaitable
        return loop.run_until_complete(awaitable)
    except RuntimeError:
        return asyncio.run(awaitable)
