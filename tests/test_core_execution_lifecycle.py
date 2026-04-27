from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from metaharness.core.execution import ExecutionLifecycleService
from metaharness.core.models import SessionEventType
from metaharness.observability.events import InMemorySessionStore
from metaharness.sdk.execution import ExecutionStatus, FibonacciPollingStrategy, JobHandle


@dataclass(slots=True)
class DemoPlan:
    plan_id: str
    experiment_ref: str = "experiment-1"
    target_backend: str = "mock"
    execution_params: dict[str, Any] | None = None


@dataclass(slots=True)
class DemoArtifact:
    artifact_id: str
    plan_ref: str
    status: str = "completed"
    raw_output_path: str | None = None


class ScriptedExecutor:
    def __init__(self, statuses: list[ExecutionStatus]) -> None:
        self.statuses = list(statuses)
        self.cancelled: list[str] = []

    async def submit(self, plan: DemoPlan) -> JobHandle:
        return JobHandle(
            job_id=f"job-{plan.plan_id}", backend="mock", status=ExecutionStatus.QUEUED
        )

    async def poll(self, job_id: str) -> ExecutionStatus:
        return self.statuses.pop(0)

    async def cancel(self, job_id: str) -> None:
        self.cancelled.append(job_id)

    async def await_result(self, job_id: str, timeout: float | None = None) -> DemoArtifact:
        return DemoArtifact(artifact_id=f"artifact-{job_id}", plan_ref="plan-1")


def test_execution_lifecycle_event_type_values_are_stable() -> None:
    assert SessionEventType.TASK_RUNNING.value == "task_running"
    assert SessionEventType.TASK_CANCELLED.value == "task_cancelled"


@pytest.mark.asyncio
async def test_execution_lifecycle_records_submit_running_and_completed_events() -> None:
    store = InMemorySessionStore()
    executor = ScriptedExecutor([ExecutionStatus.RUNNING, ExecutionStatus.COMPLETED])
    service = ExecutionLifecycleService(executor=executor, session_store=store)

    result = await service.run(
        session_id="session-1",
        plan=DemoPlan(plan_id="plan-1"),
        candidate_id="candidate-1",
        graph_version=3,
    )

    events = store.get_events("session-1")
    assert [event.event_type for event in events] == [
        SessionEventType.TASK_SUBMITTED,
        SessionEventType.TASK_RUNNING,
        SessionEventType.TASK_COMPLETED,
    ]
    assert result.run_artifact == DemoArtifact(artifact_id="artifact-job-plan-1", plan_ref="plan-1")
    assert result.job_handle.status == ExecutionStatus.COMPLETED
    assert result.job_handle.completed_at is not None
    assert events[0].payload == {
        "job_id": "job-plan-1",
        "backend": "mock",
        "status": "queued",
        "plan_ref": "plan-1",
    }
    assert events[-1].candidate_id == "candidate-1"
    assert events[-1].graph_version == 3
    assert events[-1].payload["artifact_ref"] == "artifact-job-plan-1"


@pytest.mark.asyncio
async def test_execution_lifecycle_records_failed_terminal_status() -> None:
    store = InMemorySessionStore()
    executor = ScriptedExecutor([ExecutionStatus.FAILED])
    service = ExecutionLifecycleService(executor=executor, session_store=store)

    result = await service.run(session_id="session-1", plan=DemoPlan(plan_id="plan-1"))

    events = store.get_events("session-1")
    assert [event.event_type for event in events] == [
        SessionEventType.TASK_SUBMITTED,
        SessionEventType.TASK_FAILED,
    ]
    assert result.run_artifact is None
    assert result.job_handle.status == ExecutionStatus.FAILED
    assert events[-1].payload["status"] == "failed"


@pytest.mark.asyncio
async def test_execution_lifecycle_records_timeout_when_polling_budget_expires() -> None:
    store = InMemorySessionStore()
    executor = ScriptedExecutor([ExecutionStatus.QUEUED, ExecutionStatus.QUEUED])
    service = ExecutionLifecycleService(
        executor=executor,
        session_store=store,
        polling_strategy=FibonacciPollingStrategy(base_delay=0.01, max_total_wait=0.01),
    )

    result = await service.run(session_id="session-1", plan=DemoPlan(plan_id="plan-1"))

    events = store.get_events("session-1")
    assert [event.event_type for event in events] == [
        SessionEventType.TASK_SUBMITTED,
        SessionEventType.TASK_FAILED,
    ]
    assert result.run_artifact is None
    assert result.job_handle.status == ExecutionStatus.TIMEOUT
    assert events[-1].payload["status"] == "timeout"


@pytest.mark.asyncio
async def test_execution_lifecycle_cancel_records_cancelled_event() -> None:
    store = InMemorySessionStore()
    executor = ScriptedExecutor([])
    service = ExecutionLifecycleService(executor=executor, session_store=store)
    handle = JobHandle(job_id="job-1", backend="mock", status=ExecutionStatus.RUNNING)

    event = await service.cancel(session_id="session-1", job_handle=handle)

    assert executor.cancelled == ["job-1"]
    assert handle.status == ExecutionStatus.CANCELLED
    assert handle.completed_at is not None
    assert event.event_type == SessionEventType.TASK_CANCELLED
    assert store.get_events("session-1") == [event]
