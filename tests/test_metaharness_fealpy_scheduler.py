from __future__ import annotations

import sys
from unittest.mock import AsyncMock, patch

import pytest

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.fealpy.contracts import FealpyProblemSpec, FealpyRunPlan
from metaharness_ext.fealpy.scheduler import (
    FealpySchedulerAdapter,
    FealpySlurmBackend,
    FealpySlurmSubmission,
)


def _make_plan(
    run_id: str = "run-001",
    workspace_dir: str = "/tmp/fealpy-test",
    script_source: str = "print('hello')",
    graph_metadata: dict | None = None,
) -> FealpyRunPlan:
    return FealpyRunPlan(
        plan_id=f"plan-{run_id}",
        task_id="task-001",
        run_id=run_id,
        spec=FealpyProblemSpec(task_id="task-001"),
        workspace_dir=workspace_dir,
        script_source=script_source,
        graph_metadata=graph_metadata or {},
    )


def _make_backend(*, dry_run: bool = True) -> FealpySlurmBackend:
    return FealpySlurmBackend(dry_run=dry_run)


class TestBuildSubmission:
    def test_generates_sbatch_script(self):
        backend = _make_backend()
        plan = _make_plan()
        submission = backend.build_submission(plan)
        assert isinstance(submission, FealpySlurmSubmission)
        assert submission.job_name == "run-001"
        assert "#!/bin/bash" in submission.script
        assert "#SBATCH --job-name=run-001" in submission.script
        assert f"{sys.executable} solve.py" in submission.script


class TestSubmit:
    @pytest.mark.asyncio
    async def test_dry_run_returns_queued_handle(self):
        backend = _make_backend(dry_run=True)
        plan = _make_plan()
        handle = await backend.submit(plan)
        assert isinstance(handle, JobHandle)
        assert handle.job_id == "dryrun-slurm-run-001"
        assert handle.backend == "slurm"
        assert handle.status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_dry_run_stores_plan(self):
        backend = _make_backend(dry_run=True)
        plan = _make_plan(run_id="store-test")
        handle = await backend.submit(plan)
        assert handle.job_id in backend._plans_by_job_id
        assert backend._plans_by_job_id[handle.job_id].run_id == "store-test"


class TestPoll:
    @pytest.mark.asyncio
    async def test_dry_run_returns_queued(self):
        backend = _make_backend(dry_run=True)
        status = await backend.poll("dryrun-slurm-run-001")
        assert status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_raises_for_unknown_prefix(self):
        backend = _make_backend()
        with pytest.raises(ValueError, match="Unsupported SLURM job id"):
            await backend.poll("unknown-job-123")


class TestCancel:
    @pytest.mark.asyncio
    async def test_dry_run_is_noop(self):
        backend = _make_backend(dry_run=True)
        # Should not raise
        await backend.cancel("dryrun-slurm-run-001")


class TestAwaitResult:
    @pytest.mark.asyncio
    async def test_dry_run_collects_artifact(self, tmp_path):  # noqa: N803
        backend = _make_backend(dry_run=True)
        plan = _make_plan(workspace_dir=str(tmp_path))
        handle = await backend.submit(plan)

        with patch.object(backend, "poll", AsyncMock(return_value=ExecutionStatus.COMPLETED)):
            artifact = await backend.await_result(handle.job_id)
        assert artifact.task_id == "task-001"
        assert artifact.run_id == "run-001"
        assert artifact.status == "completed"
        assert any("fealpy://run/task-001/run-001" in ref for ref in artifact.evidence_refs)

    @pytest.mark.asyncio
    async def test_unknown_job_returns_unavailable(self):
        backend = _make_backend()
        artifact = await backend.await_result("slurm-unknown")
        assert artifact.status == "unavailable"
        assert "Unknown SLURM fealpy job" in (artifact.error_message or "")


class TestMapState:
    @pytest.mark.parametrize(
        "slurm_state,expected",
        [
            ("PENDING", ExecutionStatus.QUEUED),
            ("CONFIGURING", ExecutionStatus.QUEUED),
            ("RUNNING", ExecutionStatus.RUNNING),
            ("COMPLETING", ExecutionStatus.RUNNING),
            ("COMPLETED", ExecutionStatus.COMPLETED),
            ("TIMEOUT", ExecutionStatus.TIMEOUT),
            ("CANCELLED", ExecutionStatus.CANCELLED),
            ("FAILED", ExecutionStatus.FAILED),
            ("NODE_FAIL", ExecutionStatus.FAILED),
            ("", ExecutionStatus.COMPLETED),
        ],
    )
    def test_map_state(self, slurm_state, expected):
        backend = _make_backend()
        assert backend._map_state(slurm_state) == expected


class TestAdapter:
    @pytest.mark.asyncio
    async def test_submit_dispatches_to_slurm(self):
        plan = _make_plan(graph_metadata={"target_backend": "slurm"})
        adapter = FealpySchedulerAdapter(slurm=_make_backend(dry_run=True))
        handle = await adapter.submit(plan)
        assert handle.backend == "slurm"
        assert handle.status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_raises_for_unsupported_backend(self):
        plan = _make_plan(graph_metadata={"target_backend": "unsupported"})
        adapter = FealpySchedulerAdapter()
        with pytest.raises(ValueError, match="Unsupported fealpy scheduler backend"):
            await adapter.submit(plan)

    @pytest.mark.asyncio
    async def test_backend_for_job_prefix_matching(self):
        adapter = FealpySchedulerAdapter()
        backend = adapter._backend_for_job("slurm-12345")
        assert isinstance(backend, FealpySlurmBackend)
        backend = adapter._backend_for_job("dryrun-slurm-test")
        assert isinstance(backend, FealpySlurmBackend)

    @pytest.mark.asyncio
    async def test_k8s_not_implemented_raises(self):
        plan = _make_plan(graph_metadata={"target_backend": "k8s"})
        adapter = FealpySchedulerAdapter()
        with pytest.raises(ValueError, match="K8s backend is not implemented"):
            await adapter.submit(plan)
