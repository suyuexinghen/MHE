"""Saga-style rollback for multi-step migrations.

Each :class:`SagaStep` registers a ``forward`` action plus its
``compensate`` counterpart. :class:`SagaRollback` runs forwards in
order; on failure it invokes the compensations in reverse order,
guaranteeing at-least-best-effort rollback of partial work.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

Action = Callable[[], Any] | Callable[[], Awaitable[Any]]


@dataclass(slots=True)
class SagaStep:
    """A single forward action paired with its compensation."""

    name: str
    forward: Action
    compensate: Action | None = None


@dataclass(slots=True)
class SagaStepResult:
    """Outcome of executing a single saga step."""

    name: str
    success: bool
    output: Any = None
    error: str | None = None
    compensated: bool = False


class SagaRollback:
    """Runs a saga and compensates already-completed steps on failure."""

    def __init__(self, steps: list[SagaStep] | None = None) -> None:
        self.steps: list[SagaStep] = list(steps or [])
        self.results: list[SagaStepResult] = []

    def add_step(self, step: SagaStep) -> None:
        self.steps.append(step)

    async def _run_action(self, action: Action) -> Any:
        outcome = action()
        if asyncio.iscoroutine(outcome):
            outcome = await outcome
        return outcome

    async def run(self) -> tuple[bool, list[SagaStepResult]]:
        self.results = []
        completed: list[SagaStep] = []
        ok = True
        for step in self.steps:
            try:
                value = await self._run_action(step.forward)
                self.results.append(SagaStepResult(name=step.name, success=True, output=value))
                completed.append(step)
            except Exception as exc:
                self.results.append(SagaStepResult(name=step.name, success=False, error=str(exc)))
                ok = False
                break
        if not ok:
            await self._compensate(list(reversed(completed)))
        return ok, list(self.results)

    async def _compensate(self, steps: list[SagaStep]) -> None:
        for step in steps:
            if step.compensate is None:
                continue
            try:
                await self._run_action(step.compensate)
                for r in self.results:
                    if r.name == step.name and r.success:
                        r.compensated = True
                        break
            except Exception:
                # Best effort: a compensation failure does not re-raise; it
                # is recorded on the step result for downstream operators.
                for r in self.results:
                    if r.name == step.name and r.success:
                        r.compensated = False
                        r.error = (r.error or "") + "; compensation_failed"
                        break
