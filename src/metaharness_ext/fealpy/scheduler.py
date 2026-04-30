from __future__ import annotations

import asyncio
import inspect
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from metaharness.sdk.execution import ExecutionStatus, JobHandle, ResourceQuota
from metaharness_ext.fealpy.contracts import FealpyRunArtifact, FealpyRunPlan


class FealpySlurmSubmission(BaseModel):
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


class FealpySlurmBackend:
    backend_name = "slurm"

    def __init__(
        self,
        *,
        dry_run: bool = True,
        command_client: SlurmCommandClient | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._command_client = command_client or SubprocessSlurmCommandClient()
        self._plans_by_job_id: dict[str, FealpyRunPlan] = {}

    def build_submission(self, plan: FealpyRunPlan) -> FealpySlurmSubmission:
        workspace = Path(plan.workspace_dir).expanduser()
        script = "\n".join(
            [
                "#!/bin/bash",
                f"#SBATCH --job-name={plan.run_id}",
                f"#SBATCH --output={plan.run_id}.out",
                f"#SBATCH --chdir={shlex.quote(str(workspace))}",
                "set -euo pipefail",
                f"cd {shlex.quote(str(workspace))}",
                f"{shlex.quote(sys.executable)} solve.py",
                "",
            ]
        )
        return FealpySlurmSubmission(
            job_name=plan.run_id,
            script=script,
            command=["sbatch", "--parsable"],
        )

    async def submit(self, plan: FealpyRunPlan) -> JobHandle:
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

    async def await_result(self, job_id: str, timeout: float | None = None) -> FealpyRunArtifact:
        plan = self._plans_by_job_id.get(job_id)
        if plan is None:
            return self._unavailable_artifact(job_id, f"Unknown SLURM fealpy job: {job_id}")

        status = await self.poll(job_id)
        if status not in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED,
        }:
            return self._unavailable_artifact(
                job_id,
                f"SLURM fealpy job is not terminal: {status.value}",
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
        lines = state.splitlines()
        if not lines or not lines[0].strip():
            return ExecutionStatus.COMPLETED
        normalized = lines[0].split("|", maxsplit=1)[0].strip().upper()
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
        self, plan: FealpyRunPlan, status: ExecutionStatus
    ) -> FealpyRunArtifact:
        workspace = Path(plan.workspace_dir).expanduser()
        if not workspace.exists():
            return self._unavailable_artifact(
                f"slurm-{plan.run_id}",
                f"fealpy workspace is unavailable: {workspace}",
                plan=plan,
            )

        output_files = self._files_under(workspace)
        return FealpyRunArtifact(
            artifact_id=f"{plan.plan_id}-remote-artifact",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=self._artifact_status(status),
            evidence_refs=[f"fealpy://run/{plan.task_id}/{plan.run_id}"],
            summary_metrics={"output_count": len(output_files)},
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
        plan: FealpyRunPlan | None = None,
    ) -> FealpyRunArtifact:
        return FealpyRunArtifact(
            artifact_id=f"{job_id}-unavailable-artifact",
            run_id=plan.run_id if plan else job_id,
            task_id=plan.task_id if plan else job_id,
            plan_ref=plan.plan_id if plan else job_id,
            status="unavailable",
            error_message=message,
            evidence_refs=[f"fealpy://remote/{self.backend_name}/{job_id}"],
        )


class FealpyK8sJobSpec(BaseModel):
    job_name: str
    yaml_spec: str


class FealpyK8sBackend:
    backend_name = "k8s"

    def __init__(
        self,
        *,
        dry_run: bool = True,
        command_client: SlurmCommandClient | None = None,
        image: str | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._command_client = command_client or SubprocessSlurmCommandClient()
        self._image = image or "python:3.11"
        self._plans_by_job_id: dict[str, FealpyRunPlan] = {}

    def build_job_spec(self, plan: FealpyRunPlan) -> FealpyK8sJobSpec:
        workspace = str(Path(plan.workspace_dir).expanduser())
        yaml_spec = (
            "apiVersion: batch/v1\n"
            "kind: Job\n"
            "metadata:\n"
            f"  name: {plan.run_id}\n"
            "spec:\n"
            "  template:\n"
            "    spec:\n"
            "      containers:\n"
            "      - name: fealpy\n"
            f"        image: {self._image}\n"
            f"        command: [{sys.executable!r}, 'solve.py']\n"
            f"        workingDir: {workspace!r}\n"
            "      restartPolicy: Never\n"
        )
        return FealpyK8sJobSpec(
            job_name=plan.run_id,
            yaml_spec=yaml_spec,
        )

    async def submit(self, plan: FealpyRunPlan) -> JobHandle:
        if self.dry_run:
            job_id = f"dryrun-k8s-{plan.run_id}"
            self._plans_by_job_id[job_id] = plan
            return JobHandle(
                job_id=job_id, backend=self.backend_name, status=ExecutionStatus.QUEUED
            )

        spec = self.build_job_spec(plan)
        await self._run(["kubectl", "apply", "-f", "-"], spec.yaml_spec)
        job_id = f"k8s-{plan.run_id}"
        self._plans_by_job_id[job_id] = plan
        return JobHandle(job_id=job_id, backend=self.backend_name, status=ExecutionStatus.QUEUED)

    async def poll(self, job_id: str) -> ExecutionStatus:
        if job_id.startswith("dryrun-k8s-"):
            return ExecutionStatus.QUEUED

        k8s_name = self._strip_job_prefix(job_id)
        conditions_json = (
            await self._run(
                [
                    "kubectl",
                    "get",
                    "job",
                    k8s_name,
                    "-o",
                    "jsonpath={.status.conditions}",
                ]
            )
        ).strip()
        return self._map_conditions(conditions_json)

    async def cancel(self, job_id: str) -> None:
        if job_id.startswith("dryrun-k8s-"):
            return None
        await self._run(["kubectl", "delete", "job", self._strip_job_prefix(job_id)])
        return None

    async def await_result(self, job_id: str, timeout: float | None = None) -> FealpyRunArtifact:
        plan = self._plans_by_job_id.get(job_id)
        if plan is None:
            return self._unavailable_artifact(job_id, f"Unknown K8s fealpy job: {job_id}")

        status = await self.poll(job_id)
        if status not in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED,
        }:
            return self._unavailable_artifact(
                job_id,
                f"K8s fealpy job is not terminal: {status.value}",
                plan=plan,
            )
        return self._collect_workspace_artifact(plan, status)

    def _map_conditions(self, conditions_json: str) -> ExecutionStatus:
        import json as _json

        if not conditions_json:
            return ExecutionStatus.QUEUED
        try:
            conditions = _json.loads(conditions_json)
        except _json.JSONDecodeError:
            return ExecutionStatus.RUNNING
        if not isinstance(conditions, list):
            return ExecutionStatus.RUNNING
        for cond in conditions:
            cond_type = cond.get("type", "")
            cond_status = cond.get("status", "")
            if cond_type == "Complete" and cond_status == "True":
                return ExecutionStatus.COMPLETED
            if cond_type == "Failed" and cond_status == "True":
                reason = cond.get("reason", "")
                if reason in ("DeadlineExceeded",):
                    return ExecutionStatus.TIMEOUT
                return ExecutionStatus.FAILED
        return ExecutionStatus.RUNNING

    def _strip_job_prefix(self, job_id: str) -> str:
        if not job_id.startswith("k8s-"):
            raise ValueError(f"Unsupported K8s job id: {job_id}")
        name = job_id.removeprefix("k8s-").strip()
        if not name:
            raise ValueError(f"Unsupported K8s job id: {job_id}")
        return name

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

    def _collect_workspace_artifact(
        self, plan: FealpyRunPlan, status: ExecutionStatus
    ) -> FealpyRunArtifact:
        workspace = Path(plan.workspace_dir).expanduser()
        if not workspace.exists():
            return self._unavailable_artifact(
                f"k8s-{plan.run_id}",
                f"fealpy workspace is unavailable: {workspace}",
                plan=plan,
            )

        output_files = self._files_under(workspace)
        return FealpyRunArtifact(
            artifact_id=f"{plan.plan_id}-remote-artifact",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=self._artifact_status(status),
            evidence_refs=[f"fealpy://run/{plan.task_id}/{plan.run_id}"],
            summary_metrics={"output_count": len(output_files)},
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
        plan: FealpyRunPlan | None = None,
    ) -> FealpyRunArtifact:
        return FealpyRunArtifact(
            artifact_id=f"{job_id}-unavailable-artifact",
            run_id=plan.run_id if plan else job_id,
            task_id=plan.task_id if plan else job_id,
            plan_ref=plan.plan_id if plan else job_id,
            status="unavailable",
            error_message=message,
            evidence_refs=[f"fealpy://remote/{self.backend_name}/{job_id}"],
        )


class FealpySchedulerAdapter:
    def __init__(
        self,
        *,
        slurm: FealpySlurmBackend | None = None,
        k8s: FealpyK8sBackend | None = None,
    ) -> None:
        self._slurm = slurm or FealpySlurmBackend()
        self._k8s = k8s

    async def submit(self, plan: FealpyRunPlan, *, quota: ResourceQuota | None = None) -> JobHandle:
        if quota is not None and quota.exhausted:
            raise ValueError(
                f"Resource quota exhausted for {plan.task_id}: "
                f"{quota.used}/{quota.limit} {quota.unit}"
            )
        return await self._backend(plan).submit(plan)

    async def poll(self, job_id: str) -> ExecutionStatus:
        backend = self._backend_for_job(job_id)
        return await backend.poll(job_id)

    async def cancel(self, job_id: str) -> None:
        backend = self._backend_for_job(job_id)
        await backend.cancel(job_id)

    async def await_result(self, job_id: str, timeout: float | None = None) -> FealpyRunArtifact:
        backend = self._backend_for_job(job_id)
        return await backend.await_result(job_id, timeout=timeout)

    def _backend(self, plan: FealpyRunPlan) -> FealpySlurmBackend | FealpyK8sBackend:
        backend_name = str(plan.graph_metadata.get("target_backend") or "slurm")
        if backend_name == "k8s":
            if self._k8s is None:
                raise ValueError("K8s backend is not configured for fealpy")
            return self._k8s
        if backend_name not in {"slurm"}:
            raise ValueError(f"Unsupported fealpy scheduler backend: {backend_name}")
        return self._slurm

    def _backend_for_job(self, job_id: str) -> FealpySlurmBackend | FealpyK8sBackend:
        if job_id.startswith(("dryrun-k8s-", "k8s-")):
            if self._k8s is None:
                raise ValueError("K8s backend is not configured for fealpy")
            return self._k8s
        if job_id.startswith(("dryrun-slurm-", "slurm-")):
            return self._slurm
        raise ValueError(f"Unsupported fealpy scheduler job id: {job_id}")
