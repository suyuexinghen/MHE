from __future__ import annotations

from datetime import datetime, timezone

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.octave.contracts import OctaveRunArtifact, OctaveRunPlan
from metaharness_ext.octave.executor import OctaveExecutorComponent


class OctaveAsyncExecutor:
    def __init__(self, executor: OctaveExecutorComponent | None = None) -> None:
        self._executor = executor or OctaveExecutorComponent()
        self._handles: dict[str, JobHandle] = {}
        self._results: dict[str, OctaveRunArtifact] = {}

    async def submit(self, plan: OctaveRunPlan) -> JobHandle:
        handle = JobHandle(
            job_id=plan.run_id, backend="octave-local", status=ExecutionStatus.RUNNING
        )
        self._handles[handle.job_id] = handle
        artifact = self._executor.execute_plan(plan)
        status = _artifact_status(artifact)
        self._results[handle.job_id] = artifact
        self._handles[handle.job_id] = handle.model_copy(
            update={"status": status, "completed_at": datetime.now(timezone.utc)}
        )
        return self._handles[handle.job_id]

    async def poll(self, job_id: str) -> ExecutionStatus:
        return self._require_handle(job_id).status

    async def cancel(self, job_id: str) -> None:
        handle = self._require_handle(job_id)
        if handle.status not in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
        }:
            self._handles[job_id] = handle.model_copy(
                update={
                    "status": ExecutionStatus.CANCELLED,
                    "completed_at": datetime.now(timezone.utc),
                }
            )

    async def await_result(self, job_id: str, timeout: float | None = None) -> OctaveRunArtifact:
        if job_id not in self._results:
            raise KeyError(f"Octave job has no result: {job_id}")
        return self._results[job_id]

    def _require_handle(self, job_id: str) -> JobHandle:
        try:
            return self._handles[job_id]
        except KeyError as error:
            raise KeyError(f"Unknown Octave job: {job_id}") from error


def _artifact_status(artifact: OctaveRunArtifact) -> ExecutionStatus:
    if artifact.status == "completed":
        return ExecutionStatus.COMPLETED
    if artifact.status == "timeout":
        return ExecutionStatus.TIMEOUT
    if artifact.status == "unavailable":
        return ExecutionStatus.FAILED
    return ExecutionStatus.FAILED
