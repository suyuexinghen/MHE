"""Run-oriented protocols and execution primitives for Meta-Harness."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field, field_validator


class ExecutionStatus(str, Enum):
    """Lifecycle states for asynchronous execution."""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class JobHandle(BaseModel):
    """Stable handle returned by an executor after submission."""

    job_id: str
    backend: str
    status: ExecutionStatus = ExecutionStatus.CREATED
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @field_validator("job_id", "backend")
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("job handle fields must not be empty")
        return stripped


@runtime_checkable
class RunPlanProtocol(Protocol):
    """Compiled execution plan exposed by an extension."""

    plan_id: str
    experiment_ref: str
    target_backend: Any
    execution_params: Any


@runtime_checkable
class RunArtifactProtocol(Protocol):
    """Execution artifact produced by an extension."""

    artifact_id: str
    plan_ref: str
    status: Any
    raw_output_path: str | None


@runtime_checkable
class EnvironmentReportProtocol(Protocol):
    """Backend readiness report exposed before execution."""

    task_id: str
    available: bool
    blocks_promotion: bool


@runtime_checkable
class ValidationOutcomeProtocol(Protocol):
    """Domain validation result exposed after execution."""

    task_id: str
    status: Any


@runtime_checkable
class EvidenceBundleProtocol(Protocol):
    """Minimal protocol for bundled execution evidence."""

    bundle_id: str


@runtime_checkable
class PollingStrategy(Protocol):
    """Pure delay strategy used by async executors."""

    max_total_wait: float

    def next_delay(self, attempt: int) -> float:
        """Return the delay in seconds for the given attempt number."""


@runtime_checkable
class AsyncExecutorProtocol(Protocol):
    """Minimal async execution surface shared by runtime-backed executors."""

    async def submit(self, plan: RunPlanProtocol | Any) -> JobHandle:
        """Submit a run plan and return a stable job handle."""

    async def poll(self, job_id: str) -> ExecutionStatus:
        """Return the latest execution status for a submitted job."""

    async def cancel(self, job_id: str) -> None:
        """Cancel a submitted job if the backend supports it."""

    async def await_result(
        self, job_id: str, timeout: float | None = None
    ) -> RunArtifactProtocol | Any:
        """Wait for terminal completion and return the final artifact."""


class FibonacciPollingStrategy(BaseModel):
    """Deterministic Fibonacci backoff with per-delay and total wait caps."""

    base_delay: float = 1.0
    max_delay: float = 60.0
    max_total_wait: float = 600.0

    @field_validator("base_delay", "max_delay", "max_total_wait")
    @classmethod
    def validate_positive_floats(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("polling strategy values must be positive")
        return value

    def next_delay(self, attempt: int) -> float:
        if attempt <= 0:
            raise ValueError("attempt must be positive")
        return min(self.base_delay * self._fib(attempt), self.max_delay)

    def schedule(self, max_attempts: int) -> list[float]:
        if max_attempts < 0:
            raise ValueError("max_attempts must not be negative")
        delays: list[float] = []
        total_wait = 0.0
        for attempt in range(1, max_attempts + 1):
            remaining = self.max_total_wait - total_wait
            if remaining <= 0:
                break
            delay = min(self.next_delay(attempt), remaining)
            delays.append(delay)
            total_wait += delay
        return delays

    @staticmethod
    def _fib(attempt: int) -> int:
        if attempt <= 2:
            return 1
        previous = 1
        current = 1
        for _ in range(3, attempt + 1):
            previous, current = current, previous + current
        return current


__all__ = [
    "AsyncExecutorProtocol",
    "EnvironmentReportProtocol",
    "EvidenceBundleProtocol",
    "ExecutionStatus",
    "FibonacciPollingStrategy",
    "JobHandle",
    "PollingStrategy",
    "RunArtifactProtocol",
    "RunPlanProtocol",
    "ValidationOutcomeProtocol",
]
