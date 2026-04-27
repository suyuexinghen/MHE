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


class FakeSlurmClient:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def run(self, command: list[str], input_text: str | None = None) -> str:
        self.commands.append(command)
        if command[0] == "sbatch":
            assert input_text is not None
            return "12345\n"
        if command[0] == "squeue":
            return "COMPLETED\n"
        if command[0] == "sacct":
            return ""
        if command[0] == "scancel":
            return ""
        raise AssertionError(f"unexpected command: {command}")


class FakeK8sClient:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []
        self.deleted: list[str] = []

    def create_job(self, manifest: dict[str, object]) -> str:
        self.created.append(manifest)
        return "run-1"

    def get_job_status(self, job_name: str) -> str:
        assert job_name == "run-1"
        return "succeeded"

    def delete_job(self, job_name: str) -> None:
        self.deleted.append(job_name)


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


def test_octave_slurm_builds_workspace_bound_submission() -> None:
    plan = _plan()

    slurm = OctaveSlurmBackend().build_submission(plan)

    assert "#SBATCH --job-name=run-1" in slurm.script
    assert "#SBATCH --chdir=.runs/octave/task-1/run-1" in slurm.script
    assert "cd .runs/octave/task-1/run-1" in slurm.script
    assert "octave-cli --no-init-file mhe_wrapper.m" in slurm.script
    assert slurm.command == ["sbatch", "--parsable"]


def test_octave_k8s_rejects_relative_workspace_manifests() -> None:
    with pytest.raises(ValueError, match="absolute node-visible workspace"):
        OctaveK8sBackend().build_manifest(_plan())


def test_octave_k8s_builds_shared_workspace_manifest(tmp_path) -> None:
    plan = _plan().model_copy(
        update={
            "workspace_dir": str(tmp_path),
            "execution_params": _plan().execution_params.model_copy(
                update={"workspace_dir": str(tmp_path)}
            ),
        }
    )

    k8s = OctaveK8sBackend().build_manifest(plan)

    assert k8s.manifest["kind"] == "Job"
    container = k8s.manifest["spec"]["template"]["spec"]["containers"][0]
    assert container["workingDir"] == str(tmp_path)
    assert container["volumeMounts"] == [{"name": "octave-workspace", "mountPath": str(tmp_path)}]
    assert k8s.manifest["spec"]["template"]["spec"]["volumes"] == [
        {
            "name": "octave-workspace",
            "hostPath": {"path": str(tmp_path), "type": "DirectoryOrCreate"},
        }
    ]


@pytest.mark.asyncio
async def test_octave_slurm_real_mode_uses_fake_command_client(tmp_path) -> None:
    client = FakeSlurmClient()
    backend = OctaveSlurmBackend(dry_run=False, command_client=client)
    workspace = tmp_path / "run-1"
    workspace.mkdir()
    (workspace / "stdout.log").write_text("ok")
    plan = _plan().model_copy(
        update={
            "workspace_dir": str(workspace),
            "execution_params": _plan().execution_params.model_copy(
                update={"workspace_dir": str(workspace)}
            ),
        }
    )

    handle = await backend.submit(plan)
    status = await backend.poll(handle.job_id)
    artifact = await backend.await_result(handle.job_id)
    await backend.cancel(handle.job_id)

    assert handle.job_id == "slurm-12345"
    assert status == ExecutionStatus.COMPLETED
    assert artifact.status == "completed"
    assert artifact.stdout_path == str(workspace / "stdout.log")
    assert [command[0] for command in client.commands] == ["sbatch", "squeue", "squeue", "scancel"]


@pytest.mark.asyncio
async def test_octave_k8s_real_mode_uses_fake_job_client(tmp_path) -> None:
    client = FakeK8sClient()
    backend = OctaveK8sBackend(dry_run=False, job_client=client)
    workspace = tmp_path / "run-1"
    output_dir = workspace / "outputs"
    output_dir.mkdir(parents=True)
    (output_dir / "result.json").write_text("{}")
    plan = _plan().model_copy(
        update={
            "workspace_dir": str(workspace),
            "execution_params": _plan().execution_params.model_copy(
                update={"workspace_dir": str(workspace)}
            ),
        }
    )

    handle = await backend.submit(plan)
    status = await backend.poll(handle.job_id)
    artifact = await backend.await_result(handle.job_id)
    await backend.cancel(handle.job_id)

    assert handle.job_id == "k8s-run-1"
    assert status == ExecutionStatus.COMPLETED
    assert artifact.status == "completed"
    assert artifact.output_files == [str(output_dir / "result.json")]
    assert client.created[0]["kind"] == "Job"
    assert client.deleted == ["run-1"]


@pytest.mark.asyncio
async def test_octave_scheduler_adapter_routes_real_and_dry_run_prefixes(tmp_path) -> None:
    slurm = OctaveSlurmBackend(dry_run=False, command_client=FakeSlurmClient())
    k8s = OctaveK8sBackend(dry_run=False, job_client=FakeK8sClient())
    adapter = OctaveSchedulerAdapter(slurm=slurm, k8s=k8s)
    workspace = tmp_path / "run-1"
    workspace.mkdir()
    k8s_plan = _plan().model_copy(
        update={
            "graph_metadata": {"target_backend": "k8s"},
            "workspace_dir": str(workspace),
            "execution_params": _plan().execution_params.model_copy(
                update={"workspace_dir": str(workspace)}
            ),
        }
    )

    slurm_handle = await adapter.submit(_plan())
    k8s_handle = await adapter.submit(k8s_plan)

    assert slurm_handle.job_id == "slurm-12345"
    assert await adapter.poll(slurm_handle.job_id) == ExecutionStatus.COMPLETED
    assert k8s_handle.job_id == "k8s-run-1"
    assert await adapter.poll(k8s_handle.job_id) == ExecutionStatus.COMPLETED
    assert await OctaveSchedulerAdapter().poll("dryrun-k8s-run-1") == ExecutionStatus.QUEUED


@pytest.mark.asyncio
async def test_octave_scheduler_collect_returns_unavailable_artifact() -> None:
    adapter = OctaveSchedulerAdapter()

    artifact = await adapter.await_result("dryrun-slurm-run-1")

    assert artifact.status == "unavailable"
    assert "Unknown SLURM Octave job" in artifact.error_message
