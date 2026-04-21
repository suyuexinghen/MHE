"""Connection staging, routing, and commit engine for Meta-Harness."""

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from metaharness.core.graph_versions import CandidateRecord, GraphVersionStore
from metaharness.core.models import (
    GraphSnapshot,
    PendingConnectionSet,
    ValidationReport,
)
from metaharness.core.validators import validate_graph
from metaharness.sdk.contracts import ConnectionPolicy, RouteMode
from metaharness.sdk.registry import ComponentRegistry

Handler = Callable[[Any], Any] | Callable[[Any], Awaitable[Any]]


@dataclass(slots=True)
class RouteBinding:
    """Compiled routing binding carrying mode and policy metadata."""

    connection_id: str
    target: str
    payload_type: str
    mode: RouteMode
    policy: ConnectionPolicy


class ConnectionEngine:
    """Stages, validates, commits, and routes graph connections."""

    def __init__(self, registry: ComponentRegistry, version_store: GraphVersionStore) -> None:
        self._registry = registry
        self._version_store = version_store
        self._route_table: dict[str, list[RouteBinding]] = {}
        self._handlers: dict[str, Handler] = {}

    @property
    def registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def version_store(self) -> GraphVersionStore:
        return self._version_store

    # ------------------------------------------------------------------ graph

    def load_graph(self, graph_snapshot: GraphSnapshot) -> None:
        """Load a committed graph into the active route table."""

        route_table: dict[str, list[RouteBinding]] = defaultdict(list)
        for edge in graph_snapshot.edges:
            route_table[edge.source].append(
                RouteBinding(
                    connection_id=edge.connection_id,
                    target=edge.target,
                    payload_type=edge.payload,
                    mode=edge.mode,
                    policy=edge.policy,
                )
            )
        self._route_table = dict(route_table)
        self._registry.active_graph = graph_snapshot

    def stage(self, pending: PendingConnectionSet) -> tuple[GraphSnapshot, ValidationReport]:
        """Build a candidate snapshot and validate it."""

        candidate = GraphSnapshot(
            graph_version=self._version_store.next_version(),
            nodes=pending.nodes,
            edges=pending.edges,
        )
        self._registry.candidate_graph = candidate
        report = validate_graph(candidate, self._registry)
        return candidate, report

    def commit(self, candidate_id: str, snapshot: GraphSnapshot, report: ValidationReport) -> int:
        """Atomically commit a validated graph snapshot.

        Returns the active graph version after the call. If the report is
        invalid, the active graph is preserved and the candidate is recorded
        but not promoted.
        """

        self._version_store.save_candidate(
            CandidateRecord(
                candidate_id=candidate_id, snapshot=snapshot, report=report, promoted=report.valid
            )
        )
        if not report.valid:
            return self._version_store.state.active_graph_version or 0
        self._version_store.commit(snapshot)
        self.load_graph(snapshot)
        return snapshot.graph_version

    def discard_candidate(
        self, candidate_id: str, snapshot: GraphSnapshot, report: ValidationReport
    ) -> None:
        """Record a candidate that was rejected without promotion."""

        self._version_store.save_candidate(
            CandidateRecord(
                candidate_id=candidate_id, snapshot=snapshot, report=report, promoted=False
            )
        )
        self._registry.candidate_graph = None

    def rollback(self) -> GraphSnapshot:
        """Roll the active graph back to the prior committed snapshot."""

        snapshot = self._version_store.rollback()
        self.load_graph(snapshot)
        return snapshot

    # ---------------------------------------------------------------- routing

    def register_handler(self, target: str, handler: Handler) -> None:
        """Register a port handler for routing."""

        self._handlers[target] = handler

    def unregister_handler(self, target: str) -> None:
        """Remove a registered handler, if any."""

        self._handlers.pop(target, None)

    def bindings_for(self, source: str) -> list[RouteBinding]:
        """Return current bindings registered for a source port."""

        return list(self._route_table.get(source, []))

    def emit(self, source: str, payload: Any) -> list[Any]:
        """Synchronously route a payload from a source port.

        Honours routing modes: ``sync`` and ``async`` handlers are executed in
        order; coroutine handlers are scheduled via asyncio if possible.
        ``event`` binds broadcast to all registered handlers and their results
        are accumulated. ``shadow`` bindings are fired but their results are
        excluded from the return value and any exception is swallowed.
        """

        results: list[Any] = []
        for binding in self._route_table.get(source, []):
            handler = self._handlers.get(binding.target)
            if handler is None:
                continue
            try:
                value = self._dispatch_sync(handler, payload)
            except Exception:
                if binding.mode == RouteMode.SHADOW:
                    continue
                raise
            if binding.mode != RouteMode.SHADOW:
                results.append(value)
        return results

    async def emit_async(self, source: str, payload: Any) -> list[Any]:
        """Asynchronously route a payload from a source port."""

        results: list[Any] = []
        for binding in self._route_table.get(source, []):
            handler = self._handlers.get(binding.target)
            if handler is None:
                continue
            try:
                value = await self._dispatch_async(handler, payload)
            except Exception:
                if binding.mode == RouteMode.SHADOW:
                    continue
                raise
            if binding.mode != RouteMode.SHADOW:
                results.append(value)
        return results

    # ---------------------------------------------------------------- internal

    @staticmethod
    def _dispatch_sync(handler: Handler, payload: Any) -> Any:
        result = handler(payload)
        if inspect.isawaitable(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Defer: can't block inside a running loop; return the
                    # awaitable for the caller to await if they choose.
                    return result
                return loop.run_until_complete(result)
            except RuntimeError:
                return asyncio.run(result)
        return result

    @staticmethod
    async def _dispatch_async(handler: Handler, payload: Any) -> Any:
        result = handler(payload)
        if inspect.isawaitable(result):
            return await result
        return result
