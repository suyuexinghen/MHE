"""EventBus subscription and dispatch tests."""

from __future__ import annotations

import asyncio

from metaharness.core.event_bus import Event, EventBus


def test_publish_dispatches_to_all_subscribers() -> None:
    bus = EventBus()
    seen: list[Event] = []
    bus.subscribe("audit", lambda e: seen.append(e))
    bus.subscribe("audit", lambda e: seen.append(e))
    bus.publish("audit", {"x": 1}, trace_id="t1")
    assert len(seen) == 2
    assert all(e.trace_id == "t1" for e in seen)


def test_unsubscribe_callable_removes_subscriber() -> None:
    bus = EventBus()
    seen: list[int] = []
    unsub = bus.subscribe("x", lambda _: seen.append(1))
    bus.publish("x", {})
    unsub()
    bus.publish("x", {})
    assert seen == [1]


def test_subscriber_count_and_history() -> None:
    bus = EventBus()
    bus.subscribe("e", lambda _: None)
    bus.publish("e", "a", trace_id="t")
    bus.publish("e", "b")
    assert bus.subscriber_count("e") == 1
    assert [h.payload for h in bus.history] == ["a", "b"]


def test_publish_async_awaits_coroutine_handlers() -> None:
    bus = EventBus()
    results: list[int] = []

    async def handler(event: Event) -> int:
        await asyncio.sleep(0)
        results.append(event.payload)
        return event.payload

    bus.subscribe("e", handler)
    values = asyncio.run(bus.publish_async("e", 7))
    assert values == [7]
    assert results == [7]
