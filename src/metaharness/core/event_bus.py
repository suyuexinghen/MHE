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
CANDIDATE_DEFERRED = "candidate_deferred"


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
        self._drain_epoch_id: str | None = None
        self._drain_buffer: list[Event] = []
        self._drain_max_buffered = 0

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

    @property
    def drain_active(self) -> bool:
        return self._drain_epoch_id is not None

    @property
    def buffered_event_count(self) -> int:
        return len(self._drain_buffer)

    def begin_drain(self, epoch_id: str, *, max_buffered: int) -> None:
        if self._drain_epoch_id is not None:
            raise RuntimeError(f"event drain '{self._drain_epoch_id}' is already active")
        self._drain_epoch_id = epoch_id
        self._drain_max_buffered = max_buffered
        self._drain_buffer = []

    def end_drain(self, *, replay: bool) -> int:
        buffered = list(self._drain_buffer)
        self._drain_epoch_id = None
        self._drain_buffer = []
        self._drain_max_buffered = 0
        if replay:
            for event in buffered:
                headers = dict(event.headers)
                headers.setdefault(
                    "replayed_from_drain_epoch", event.headers.get("drain_epoch", "")
                )
                self.publish(event.name, event.payload, trace_id=event.trace_id, headers=headers)
        return len(buffered)

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
        if self._buffer_event_if_draining(event):
            return []
        return self._dispatch_event_sync(event)

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
        if self._buffer_event_if_draining(event):
            return []
        return await self._dispatch_event_async(event)

    def _buffer_event_if_draining(self, event: Event) -> bool:
        if self._drain_epoch_id is None:
            return False
        if len(self._drain_buffer) >= self._drain_max_buffered:
            raise RuntimeError(f"event drain '{self._drain_epoch_id}' buffer is full")
        event.headers.setdefault("drain_epoch", self._drain_epoch_id)
        self._drain_buffer.append(event)
        return True

    def _dispatch_event_sync(self, event: Event) -> list[Any]:
        if self._trace_enabled:
            self._history.append(event)
        results: list[Any] = []
        for handler in list(self._subscribers.get(event.name, [])):
            value = handler(event)
            if inspect.isawaitable(value):
                value = _run_sync(value)
            results.append(value)
        return results

    async def _dispatch_event_async(self, event: Event) -> list[Any]:
        if self._trace_enabled:
            self._history.append(event)
        results: list[Any] = []
        for handler in list(self._subscribers.get(event.name, [])):
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
