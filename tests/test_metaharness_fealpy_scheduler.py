from __future__ import annotations

import sys
from unittest.mock import AsyncMock, patch

import pytest

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.fealpy.contracts import FealpyProblemSpec, FealpyRunPlan
from metaharness_ext.fealpy.scheduler import (
    FealpyK8sBackend,
    FealpyK8sJobSpec,
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


def _make_k8s_backend(*, dry_run: bool = True) -> FealpyK8sBackend:
    return FealpyK8sBackend(dry_run=dry_run)


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


class TestK8sBuildJobSpec:
    def test_generates_k8s_job_yaml(self):
        backend = _make_k8s_backend()
        plan = _make_plan()
        spec = backend.build_job_spec(plan)
        assert isinstance(spec, FealpyK8sJobSpec)
        assert spec.job_name == "run-001"
        assert "apiVersion: batch/v1" in spec.yaml_spec
        assert "kind: Job" in spec.yaml_spec
        assert f"name: {plan.run_id}" in spec.yaml_spec
        assert "restartPolicy: Never" in spec.yaml_spec


class TestK8sSubmit:
    @pytest.mark.asyncio
    async def test_dry_run_returns_queued_handle(self):
        backend = _make_k8s_backend(dry_run=True)
        plan = _make_plan()
        handle = await backend.submit(plan)
        assert isinstance(handle, JobHandle)
        assert handle.job_id == "dryrun-k8s-run-001"
        assert handle.backend == "k8s"
        assert handle.status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_dry_run_stores_plan(self):
        backend = _make_k8s_backend(dry_run=True)
        plan = _make_plan(run_id="k8s-store-test")
        handle = await backend.submit(plan)
        assert handle.job_id in backend._plans_by_job_id


class TestK8sPoll:
    @pytest.mark.asyncio
    async def test_dry_run_returns_queued(self):
        backend = _make_k8s_backend(dry_run=True)
        status = await backend.poll("dryrun-k8s-run-001")
        assert status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_raises_for_unknown_prefix(self):
        backend = _make_k8s_backend()
        with pytest.raises(ValueError, match="Unsupported K8s job id"):
            await backend.poll("slurm-unknown")


class TestK8sCancel:
    @pytest.mark.asyncio
    async def test_dry_run_is_noop(self):
        backend = _make_k8s_backend(dry_run=True)
        await backend.cancel("dryrun-k8s-run-001")


class TestK8sAwaitResult:
    @pytest.mark.asyncio
    async def test_unknown_job_returns_unavailable(self):
        backend = _make_k8s_backend()
        artifact = await backend.await_result("k8s-unknown")
        assert artifact.status == "unavailable"
        assert "Unknown K8s fealpy job" in (artifact.error_message or "")


class TestK8sMapConditions:
    @pytest.mark.parametrize(
        "conditions_json,expected",
        [
            ("", ExecutionStatus.QUEUED),
            ("invalid_json", ExecutionStatus.RUNNING),
            ('[{"type":"Complete","status":"True"}]', ExecutionStatus.COMPLETED),
            (
                '[{"type":"Failed","status":"True","reason":"DeadlineExceeded"}]',
                ExecutionStatus.TIMEOUT,
            ),
            ('[{"type":"Failed","status":"True"}]', ExecutionStatus.FAILED),
            ("[]", ExecutionStatus.RUNNING),
        ],
    )
    def test_map_conditions(self, conditions_json, expected):
        backend = _make_k8s_backend()
        assert backend._map_conditions(conditions_json) == expected


class TestAdapter:
    @pytest.mark.asyncio
    async def test_submit_dispatches_to_slurm(self):
        plan = _make_plan(graph_metadata={"target_backend": "slurm"})
        adapter = FealpySchedulerAdapter(slurm=_make_backend(dry_run=True))
        handle = await adapter.submit(plan)
        assert handle.backend == "slurm"
        assert handle.status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_submit_dispatches_to_k8s(self):
        plan = _make_plan(graph_metadata={"target_backend": "k8s"})
        adapter = FealpySchedulerAdapter(k8s=_make_k8s_backend(dry_run=True))
        handle = await adapter.submit(plan)
        assert handle.backend == "k8s"
        assert handle.status == ExecutionStatus.QUEUED

    @pytest.mark.asyncio
    async def test_raises_for_unsupported_backend(self):
        plan = _make_plan(graph_metadata={"target_backend": "unsupported"})
        adapter = FealpySchedulerAdapter()
        with pytest.raises(ValueError, match="Unsupported fealpy scheduler backend"):
            await adapter.submit(plan)

    @pytest.mark.asyncio
    async def test_backend_for_job_prefix_matching(self):
        adapter = FealpySchedulerAdapter(k8s=_make_k8s_backend())
        backend = adapter._backend_for_job("slurm-12345")
        assert isinstance(backend, FealpySlurmBackend)
        backend = adapter._backend_for_job("dryrun-slurm-test")
        assert isinstance(backend, FealpySlurmBackend)
        backend = adapter._backend_for_job("k8s-12345")
        assert isinstance(backend, FealpyK8sBackend)
        backend = adapter._backend_for_job("dryrun-k8s-test")
        assert isinstance(backend, FealpyK8sBackend)

    @pytest.mark.asyncio
    async def test_k8s_not_configured_raises(self):
        plan = _make_plan(graph_metadata={"target_backend": "k8s"})
        adapter = FealpySchedulerAdapter()
        with pytest.raises(ValueError, match="K8s backend is not configured"):
            await adapter.submit(plan)


class TestAdapterQuota:
    @pytest.mark.asyncio
    async def test_exhausted_quota_raises(self):
        from metaharness.sdk.execution import ResourceQuota

        plan = _make_plan()
        quota = ResourceQuota(
            quota_id="test-quota",
            resource_type="fealpy_mesh",
            limit=100,
            used=100,
            remaining=0,
            exhausted=True,
        )
        adapter = FealpySchedulerAdapter(slurm=_make_backend(dry_run=True))
        with pytest.raises(ValueError, match="Resource quota exhausted"):
            await adapter.submit(plan, quota=quota)

    @pytest.mark.asyncio
    async def test_non_exhausted_quota_proceeds(self):
        from metaharness.sdk.execution import ResourceQuota

        plan = _make_plan()
        quota = ResourceQuota(
            quota_id="test-quota",
            resource_type="fealpy_mesh",
            limit=2000000,
            used=1000,
            remaining=1999000,
            exhausted=False,
        )
        adapter = FealpySchedulerAdapter(slurm=_make_backend(dry_run=True))
        handle = await adapter.submit(plan, quota=quota)
        assert handle.status == ExecutionStatus.QUEUED
