"""Hot-swap orchestration: suspend -> snapshot -> transform -> resume."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from metaharness.hotreload.checkpoint import Checkpoint, CheckpointManager
from metaharness.hotreload.migration import MigrationAdapterRegistry
from metaharness.hotreload.observation import ObservationWindowEvaluator, ObservationWindowReport
from metaharness.hotreload.saga import SagaRollback, SagaStep, SagaStepResult
from metaharness.sdk.base import HarnessComponent


@dataclass(slots=True)
class HotSwapReport:
    """Outcome of a hot-swap attempt."""

    component_id: str
    success: bool
    checkpoint: Checkpoint | None = None
    migrated_state: dict[str, Any] | None = None
    observation: ObservationWindowReport | None = None
    error: str | None = None
    saga_results: list[SagaStepResult] = field(default_factory=list)


class HotSwapOrchestrator:
    """Executes the full hot-swap workflow for one component.

    The orchestrator wraps the workflow in a :class:`SagaRollback` so a
    failure anywhere in the chain rolls the component back to its last
    checkpoint.
    """

    def __init__(
        self,
        checkpoints: CheckpointManager | None = None,
        migration_adapters: MigrationAdapterRegistry | None = None,
        observation_evaluator: ObservationWindowEvaluator | None = None,
    ) -> None:
        self.checkpoints = checkpoints or CheckpointManager()
        self.migration_adapters = migration_adapters or MigrationAdapterRegistry()
        self.observation_evaluator = observation_evaluator

    async def swap(
        self,
        *,
        component_id: str,
        outgoing: HarnessComponent,
        incoming: HarnessComponent,
        delta: Mapping[str, Any] | None = None,
        state_schema_version: int = 1,
        target_state_schema_version: int | None = None,
        observation_metrics: Mapping[str, float] | None = None,
        observation_events: list[Mapping[str, Any] | str] | None = None,
        observation_context: Mapping[str, Any] | None = None,
    ) -> HotSwapReport:
        """Swap ``outgoing`` for ``incoming``, migrating its state.

        Steps:
            1. Capture a checkpoint of ``outgoing`` (suspend first).
            2. Deactivate ``outgoing``.
            3. Ask ``incoming`` to produce migrated state via
               :meth:`HarnessComponent.transform_state`.
            4. Resume ``incoming`` with the migrated state.
        """

        report = HotSwapReport(component_id=component_id, success=False)
        saga = SagaRollback()

        runtime_registry = self._runtime_migration_registry(outgoing, incoming)

        async def capture() -> Checkpoint:
            await outgoing.suspend()
            ckpt = await self.checkpoints.capture(
                outgoing,
                component_id=component_id,
                state_schema_version=state_schema_version,
                label="pre-swap",
            )
            report.checkpoint = ckpt
            return ckpt

        async def compensate_capture() -> None:
            # If later steps fail, resume the outgoing component as-was.
            await outgoing.resume(report.checkpoint.state if report.checkpoint else None)

        async def deactivate_outgoing() -> None:
            await outgoing.deactivate()

        async def reactivate_outgoing() -> None:
            # Compensation for deactivation is a best-effort re-activate.
            # The runtime supplies the ComponentRuntime via the component's
            # stored reference; if unavailable we skip rather than raise.
            try:
                await outgoing.activate(getattr(outgoing, "_runtime", None))
            except TypeError:
                return

        async def migrate_state() -> dict[str, Any]:
            if report.checkpoint is None:
                raise RuntimeError("checkpoint missing before migration")
            resolved_target_version = (
                state_schema_version
                if target_state_schema_version is None
                else target_state_schema_version
            )
            registry = runtime_registry or self.migration_adapters
            migrated = await registry.migrate(
                source_type=component_id,
                source_version=report.checkpoint.state_schema_version,
                target_type=component_id,
                target_version=resolved_target_version,
                state=report.checkpoint.state,
                delta=delta or {},
            )
            if migrated is None:
                migrated = await incoming.transform_state(report.checkpoint.state, delta or {})
            report.migrated_state = migrated
            return migrated

        async def resume_incoming() -> None:
            await incoming.resume(report.migrated_state or {})

        async def deactivate_incoming() -> None:
            await incoming.deactivate()

        async def observe_window() -> ObservationWindowReport:
            if self.observation_evaluator is None:
                return ObservationWindowReport(passed=True)
            observation = self.observation_evaluator.evaluate(
                metrics=observation_metrics,
                events=observation_events,
                context={
                    "component_id": component_id,
                    "checkpoint": report.checkpoint,
                    "migrated_state": report.migrated_state,
                    **dict(observation_context or {}),
                },
            )
            report.observation = observation
            if not observation.passed:
                raise RuntimeError(observation.reason or "observation window rejected swap")
            return observation

        saga.add_step(SagaStep(name="capture", forward=capture, compensate=compensate_capture))
        saga.add_step(
            SagaStep(
                name="deactivate_outgoing",
                forward=deactivate_outgoing,
                compensate=reactivate_outgoing,
            )
        )
        saga.add_step(SagaStep(name="migrate_state", forward=migrate_state))
        saga.add_step(
            SagaStep(
                name="resume_incoming",
                forward=resume_incoming,
                compensate=deactivate_incoming,
            )
        )
        if self.observation_evaluator is not None:
            saga.add_step(SagaStep(name="observe_window", forward=observe_window))

        ok, results = await saga.run()
        report.success = ok
        report.saga_results = results
        if not ok:
            failed = next((r for r in results if not r.success), None)
            report.error = failed.error if failed else "unknown saga failure"
        return report

    def _runtime_migration_registry(
        self,
        outgoing: HarnessComponent,
        incoming: HarnessComponent,
    ) -> MigrationAdapterRegistry | None:
        for component in (incoming, outgoing):
            runtime = getattr(component, "_runtime", None)
            registry = getattr(runtime, "migration_adapters", None)
            if isinstance(registry, MigrationAdapterRegistry):
                return registry
        return None

    def swap_sync(
        self,
        *,
        component_id: str,
        outgoing: HarnessComponent,
        incoming: HarnessComponent,
        delta: Mapping[str, Any] | None = None,
        state_schema_version: int = 1,
        target_state_schema_version: int | None = None,
        observation_metrics: Mapping[str, float] | None = None,
        observation_events: list[Mapping[str, Any] | str] | None = None,
        observation_context: Mapping[str, Any] | None = None,
    ) -> HotSwapReport:
        return asyncio.run(
            self.swap(
                component_id=component_id,
                outgoing=outgoing,
                incoming=incoming,
                delta=delta,
                state_schema_version=state_schema_version,
                target_state_schema_version=target_state_schema_version,
                observation_metrics=observation_metrics,
                observation_events=observation_events,
                observation_context=observation_context,
            )
        )
