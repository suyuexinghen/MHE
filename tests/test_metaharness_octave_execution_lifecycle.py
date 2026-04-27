import pytest

from metaharness.sdk.execution import ExecutionStatus
from metaharness_ext.octave.async_executor import OctaveAsyncExecutor
from metaharness_ext.octave.contracts import (
    OctaveExecutableSpec,
    OctaveExecutionParams,
    OctaveRunArtifact,
    OctaveRunPlan,
)
from metaharness_ext.octave.scheduler import (
    OctaveK8sBackend,
    OctaveSchedulerAdapter,
    OctaveSlurmBackend,
)


def _plan() -> OctaveRunPlan:
    executable = OctaveExecutableSpec(binary_name="octave-cli")
    return OctaveRunPlan(
        plan_id="plan-1",
        task_id="task-1",
        run_id="run-1",
        executable=executable,
        wrapper_source="result = 1;",
        workspace_dir=".runs/octave/task-1/run-1",
        execution_params=OctaveExecutionParams(
            argv=["octave-cli", "--no-init-file", "mhe_wrapper.m"],
            workspace_dir=".runs/octave/task-1/run-1",
        ),
    )


class FakeExecutor:
    def execute_plan(self, plan: OctaveRunPlan) -> OctaveRunArtifact:
        return OctaveRunArtifact(
            artifact_id="artifact-1",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status="completed",
            working_directory=plan.workspace_dir,
        )


@pytest.mark.asyncio
async def test_octave_async_executor_records_terminal_result() -> None:
    executor = OctaveAsyncExecutor(executor=FakeExecutor())

    handle = await executor.submit(_plan())
    status = await executor.poll(handle.job_id)
    artifact = await executor.await_result(handle.job_id)

    assert handle.status == ExecutionStatus.COMPLETED
    assert status == ExecutionStatus.COMPLETED
    assert artifact.artifact_id == "artifact-1"


@pytest.mark.asyncio
async def test_octave_scheduler_adapter_dry_run_routes_backend() -> None:
    adapter = OctaveSchedulerAdapter()
    plan = _plan().model_copy(update={"graph_metadata": {"target_backend": "k8s"}})

    handle = await adapter.submit(plan)

    assert handle.backend == "k8s"
    assert handle.job_id == "dryrun-k8s-run-1"


def test_octave_slurm_and_k8s_build_dry_run_specs() -> None:
    plan = _plan()

    slurm = OctaveSlurmBackend().build_submission(plan)
    k8s = OctaveK8sBackend().build_manifest(plan)

    assert "#SBATCH --job-name=run-1" in slurm.script
    assert k8s.manifest["kind"] == "Job"
