from __future__ import annotations

from unittest.mock import Mock

import pytest

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.fealpy.async_executor import FealpyAsyncExecutor
from metaharness_ext.fealpy.contracts import FealpyProblemSpec, FealpyRunArtifact, FealpyRunPlan


def _plan() -> FealpyRunPlan:
    return FealpyRunPlan(
        plan_id="fealpy-async-test-abc",
        task_id="async-test",
        run_id="run-async-1",
        spec=FealpyProblemSpec(task_id="async-test"),
        workspace_dir=".runs/fealpy/async-test",
        script_source="print('hello')",
    )


def _artifact(status: str = "completed") -> FealpyRunArtifact:
    return FealpyRunArtifact(
        artifact_id="artifact-1",
        run_id="run-async-1",
        task_id="async-test",
        plan_ref="fealpy-async-test-abc",
        status=status,
        l2_error=0.001,
        h1_error=0.01,
        dof_count=81,
    )


@pytest.mark.asyncio
async def test_submit_returns_job_handle() -> None:
    executor = FealpyAsyncExecutor(executor=Mock())
    executor._executor.execute_plan.return_value = _artifact()  # type: ignore[attr-defined]
    handle = await executor.submit(_plan())
    assert isinstance(handle, JobHandle)
    assert handle.job_id == "run-async-1"
    assert handle.backend == "fealpy-local"
    assert handle.status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_submit_stores_result() -> None:
    artifact = _artifact()
    executor = FealpyAsyncExecutor(executor=Mock())
    executor._executor.execute_plan.return_value = artifact  # type: ignore[attr-defined]
    await executor.submit(_plan())
    result = await executor.await_result("run-async-1")
    assert result.artifact_id == artifact.artifact_id


@pytest.mark.asyncio
async def test_poll_returns_status() -> None:
    executor = FealpyAsyncExecutor(executor=Mock())
    executor._executor.execute_plan.return_value = _artifact()  # type: ignore[attr-defined]
    await executor.submit(_plan())
    status = await executor.poll("run-async-1")
    assert status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_updates_status() -> None:
    executor = FealpyAsyncExecutor(executor=Mock())
    # Create a handle manually (without calling submit) so status is RUNNING
    handle = JobHandle(job_id="run-cancel", backend="fealpy-local", status=ExecutionStatus.RUNNING)
    executor._handles[handle.job_id] = handle
    await executor.cancel("run-cancel")
    assert executor._handles["run-cancel"].status == ExecutionStatus.CANCELLED


@pytest.mark.asyncio
async def test_cancel_does_not_overwrite_terminal() -> None:
    executor = FealpyAsyncExecutor(executor=Mock())
    executor._executor.execute_plan.return_value = _artifact()  # type: ignore[attr-defined]
    await executor.submit(_plan())
    # Already COMPLETED — cancel should be a no-op
    await executor.cancel("run-async-1")
    assert executor._handles["run-async-1"].status == ExecutionStatus.COMPLETED


@pytest.mark.asyncio
async def test_await_result_raises_keyerror_for_unknown_job() -> None:
    executor = FealpyAsyncExecutor()
    with pytest.raises(KeyError, match="no result"):
        await executor.await_result("nonexistent")


@pytest.mark.asyncio
async def test_poll_raises_keyerror_for_unknown_job() -> None:
    executor = FealpyAsyncExecutor()
    with pytest.raises(KeyError, match="Unknown Fealpy job"):
        await executor.poll("nonexistent")


def test_artifact_status_mapping() -> None:
    from metaharness_ext.fealpy.async_executor import _artifact_status

    assert _artifact_status(_artifact("completed")) == ExecutionStatus.COMPLETED
    assert _artifact_status(_artifact("timeout")) == ExecutionStatus.TIMEOUT
    assert _artifact_status(_artifact("unavailable")) == ExecutionStatus.FAILED
    assert _artifact_status(_artifact("failed")) == ExecutionStatus.FAILED
