from __future__ import annotations

import asyncio
import inspect
import shlex
import subprocess
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.octave.contracts import OctaveRunArtifact, OctaveRunPlan


class OctaveSlurmSubmission(BaseModel):
    job_name: str
    script: str
    command: list[str] = Field(default_factory=list)


class SlurmCommandClient(Protocol):
    def run(self, command: list[str], input_text: str | None = None) -> object: ...


class SubprocessSlurmCommandClient:
    async def run(self, command: list[str], input_text: str | None = None) -> str:
        return await asyncio.to_thread(self._run_sync, command, input_text)

    def _run_sync(self, command: list[str], input_text: str | None) -> str:
        result = subprocess.run(
            command,
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"SLURM command failed: {command[0]}")
        return result.stdout


class OctaveSlurmBackend:
    backend_name = "slurm"

    def __init__(
        self,
        *,
        dry_run: bool = True,
        command_client: SlurmCommandClient | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._command_client = command_client or SubprocessSlurmCommandClient()
        self._plans_by_job_id: dict[str, OctaveRunPlan] = {}

    def build_submission(self, plan: OctaveRunPlan) -> OctaveSlurmSubmission:
        workspace = Path(plan.execution_params.workspace_dir).expanduser()
        script = "\n".join(
            [
                "#!/bin/bash",
                f"#SBATCH --job-name={plan.run_id}",
                f"#SBATCH --output={plan.run_id}.out",
                f"#SBATCH --chdir={shlex.quote(str(workspace))}",
                "set -euo pipefail",
                f"cd {shlex.quote(str(workspace))}",
                shlex.join(plan.execution_params.argv),
                "",
            ]
        )
        return OctaveSlurmSubmission(
            job_name=plan.run_id,
            script=script,
            command=["sbatch", "--parsable"],
        )

    async def submit(self, plan: OctaveRunPlan) -> JobHandle:
        if self.dry_run:
            job_id = f"dryrun-slurm-{plan.run_id}"
            self._plans_by_job_id[job_id] = plan
            return JobHandle(
                job_id=job_id, backend=self.backend_name, status=ExecutionStatus.QUEUED
            )

        submission = self.build_submission(plan)
        output = await self._run(submission.command, submission.script)
        scheduler_id = self._parse_submit_output(output)
        job_id = f"slurm-{scheduler_id}"
        self._plans_by_job_id[job_id] = plan
        return JobHandle(job_id=job_id, backend=self.backend_name, status=ExecutionStatus.QUEUED)

    async def poll(self, job_id: str) -> ExecutionStatus:
        if job_id.startswith("dryrun-slurm-"):
            return ExecutionStatus.QUEUED

        scheduler_id = self._strip_job_prefix(job_id)
        state = (await self._run(["squeue", "-h", "-j", scheduler_id, "-o", "%T"])).strip()
        if not state:
            state = (
                await self._run(["sacct", "-n", "-j", scheduler_id, "-o", "State", "-P"])
            ).strip()
        return self._map_state(state)

    async def cancel(self, job_id: str) -> None:
        if job_id.startswith("dryrun-slurm-"):
            return None
        await self._run(["scancel", self._strip_job_prefix(job_id)])
        return None

    async def await_result(self, job_id: str, timeout: float | None = None) -> OctaveRunArtifact:
        plan = self._plans_by_job_id.get(job_id)
        if plan is None:
            return self._unavailable_artifact(job_id, f"Unknown SLURM Octave job: {job_id}")

        status = await self.poll(job_id)
        if status not in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED,
        }:
            return self._unavailable_artifact(
                job_id,
                f"SLURM Octave job is not terminal: {status.value}",
                plan=plan,
            )
        return self._collect_workspace_artifact(plan, status)

    async def _run(self, command: list[str], input_text: str | None = None) -> str:
        result = self._command_client.run(command, input_text)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, str):
            return result
        stdout = getattr(result, "stdout", None)
        if stdout is not None:
            return str(stdout)
        return str(result)

    def _parse_submit_output(self, output: str) -> str:
        scheduler_id = output.strip().splitlines()[0].split(";", maxsplit=1)[0].strip()
        if not scheduler_id:
            raise RuntimeError("SLURM submission did not return a job id")
        return scheduler_id

    def _strip_job_prefix(self, job_id: str) -> str:
        if not job_id.startswith("slurm-"):
            raise ValueError(f"Unsupported SLURM job id: {job_id}")
        scheduler_id = job_id.removeprefix("slurm-").strip()
        if not scheduler_id:
            raise ValueError(f"Unsupported SLURM job id: {job_id}")
        return scheduler_id

    def _map_state(self, state: str) -> ExecutionStatus:
        normalized = state.splitlines()[0].split("|", maxsplit=1)[0].strip().upper()
        if not normalized:
            return ExecutionStatus.COMPLETED
        if normalized in {"PENDING", "CONFIGURING", "RESIZING", "SUSPENDED"}:
            return ExecutionStatus.QUEUED
        if normalized in {"RUNNING", "COMPLETING"}:
            return ExecutionStatus.RUNNING
        if normalized == "COMPLETED":
            return ExecutionStatus.COMPLETED
        if normalized in {"TIMEOUT", "DEADLINE"}:
            return ExecutionStatus.TIMEOUT
        if normalized in {"CANCELLED", "CANCELLED+"}:
            return ExecutionStatus.CANCELLED
        return ExecutionStatus.FAILED

    def _collect_workspace_artifact(
        self, plan: OctaveRunPlan, status: ExecutionStatus
    ) -> OctaveRunArtifact:
        workspace = Path(plan.workspace_dir).expanduser()
        if not workspace.exists():
            return self._unavailable_artifact(
                f"slurm-{plan.run_id}",
                f"Octave workspace is unavailable: {workspace}",
                plan=plan,
            )

        output_dir = workspace / plan.execution_params.output_directory
        output_files = self._files_under(output_dir) if output_dir.exists() else []
        log_files = sorted(
            str(path)
            for pattern in ("*.log", "*.out", "*.err")
            for path in workspace.glob(pattern)
            if path.is_file()
        )
        status_path = workspace / plan.execution_params.status_file
        return OctaveRunArtifact(
            artifact_id=f"{plan.plan_id}-remote-artifact",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=self._artifact_status(status),
            command=plan.execution_params.argv,
            working_directory=str(workspace),
            output_files=output_files,
            log_files=log_files,
            stdout_path=str(workspace / "stdout.log")
            if (workspace / "stdout.log").exists()
            else None,
            stderr_path=str(workspace / "stderr.log")
            if (workspace / "stderr.log").exists()
            else None,
            status_path=str(status_path) if status_path.exists() else None,
            summary_metrics={"output_count": len(output_files)},
            evidence_refs=[f"octave://run/{plan.task_id}/{plan.run_id}"],
        )

    def _files_under(self, directory: Path) -> list[str]:
        return sorted(str(path) for path in directory.rglob("*") if path.is_file())

    def _artifact_status(self, status: ExecutionStatus) -> str:
        if status == ExecutionStatus.COMPLETED:
            return "completed"
        if status == ExecutionStatus.TIMEOUT:
            return "timeout"
        return "failed"

    def _unavailable_artifact(
        self,
        job_id: str,
        message: str,
        *,
        plan: OctaveRunPlan | None = None,
    ) -> OctaveRunArtifact:
        return OctaveRunArtifact(
            artifact_id=f"{job_id}-unavailable-artifact",
            run_id=plan.run_id if plan else job_id,
            task_id=plan.task_id if plan else job_id,
            plan_ref=plan.plan_id if plan else job_id,
            status="unavailable",
            command=plan.execution_params.argv if plan else [],
            working_directory=plan.workspace_dir if plan else "",
            error_message=message,
            evidence_refs=[f"octave://remote/{self.backend_name}/{job_id}"],
        )
