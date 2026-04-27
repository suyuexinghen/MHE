from __future__ import annotations

from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.octave.contracts import OctaveRunArtifact, OctaveRunPlan


class OctaveK8sJobManifest(BaseModel):
    name: str
    manifest: dict[str, object] = Field(default_factory=dict)


class K8sJobClient(Protocol):
    def create_job(self, manifest: dict[str, object]) -> str: ...

    def get_job_status(self, job_name: str) -> str: ...

    def delete_job(self, job_name: str) -> None: ...


class KubernetesBatchJobClient:
    def __init__(self, *, namespace: str = "default") -> None:
        self.namespace = namespace
        self._batch_api = None

    def create_job(self, manifest: dict[str, object]) -> str:
        batch_api = self._api()
        batch_api.create_namespaced_job(namespace=self.namespace, body=manifest)
        metadata = manifest.get("metadata", {})
        if not isinstance(metadata, dict):
            raise RuntimeError("Kubernetes job manifest metadata is invalid")
        name = str(metadata.get("name") or "").strip()
        if not name:
            raise RuntimeError("Kubernetes job manifest did not include a name")
        return name

    def get_job_status(self, job_name: str) -> str:
        job = self._api().read_namespaced_job_status(name=job_name, namespace=self.namespace)
        status = getattr(job, "status", None)
        if getattr(status, "succeeded", 0):
            return "succeeded"
        if getattr(status, "failed", 0):
            return "failed"
        if getattr(status, "active", 0):
            return "active"
        return "pending"

    def delete_job(self, job_name: str) -> None:
        self._api().delete_namespaced_job(name=job_name, namespace=self.namespace)

    def _api(self):
        if self._batch_api is None:
            from kubernetes import client, config

            config.load_kube_config()
            self._batch_api = client.BatchV1Api()
        return self._batch_api


class OctaveK8sBackend:
    backend_name = "k8s"

    def __init__(
        self,
        *,
        dry_run: bool = True,
        job_client: K8sJobClient | None = None,
        namespace: str = "default",
    ) -> None:
        self.dry_run = dry_run
        self._job_client = job_client or KubernetesBatchJobClient(namespace=namespace)
        self._plans_by_job_id: dict[str, OctaveRunPlan] = {}

    def build_manifest(self, plan: OctaveRunPlan) -> OctaveK8sJobManifest:
        workspace = self._shared_workspace(plan)
        return OctaveK8sJobManifest(
            name=plan.run_id,
            manifest={
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {"name": plan.run_id},
                "spec": {
                    "template": {
                        "spec": {
                            "restartPolicy": "Never",
                            "containers": [
                                {
                                    "name": "octave",
                                    "image": "gnuoctave/octave:latest",
                                    "command": plan.execution_params.argv,
                                    "workingDir": str(workspace),
                                    "env": [
                                        {"name": key, "value": value}
                                        for key, value in sorted(
                                            plan.execution_params.environment.items()
                                        )
                                    ],
                                    "volumeMounts": [
                                        {"name": "octave-workspace", "mountPath": str(workspace)}
                                    ],
                                }
                            ],
                            "volumes": [
                                {
                                    "name": "octave-workspace",
                                    "hostPath": {
                                        "path": str(workspace),
                                        "type": "DirectoryOrCreate",
                                    },
                                }
                            ],
                        }
                    }
                },
            },
        )

    async def submit(self, plan: OctaveRunPlan) -> JobHandle:
        if self.dry_run:
            job_id = f"dryrun-k8s-{plan.run_id}"
            self._plans_by_job_id[job_id] = plan
            return JobHandle(
                job_id=job_id, backend=self.backend_name, status=ExecutionStatus.QUEUED
            )

        built = self.build_manifest(plan)
        job_name = self._job_client.create_job(built.manifest)
        job_id = f"k8s-{job_name}"
        self._plans_by_job_id[job_id] = plan
        return JobHandle(job_id=job_id, backend=self.backend_name, status=ExecutionStatus.QUEUED)

    async def poll(self, job_id: str) -> ExecutionStatus:
        if job_id.startswith("dryrun-k8s-"):
            return ExecutionStatus.QUEUED
        return self._map_status(self._job_client.get_job_status(self._strip_job_prefix(job_id)))

    async def cancel(self, job_id: str) -> None:
        if job_id.startswith("dryrun-k8s-"):
            return None
        self._job_client.delete_job(self._strip_job_prefix(job_id))
        return None

    async def await_result(self, job_id: str, timeout: float | None = None) -> OctaveRunArtifact:
        plan = self._plans_by_job_id.get(job_id)
        if plan is None:
            return self._unavailable_artifact(job_id, f"Unknown Kubernetes Octave job: {job_id}")

        status = await self.poll(job_id)
        if status not in {
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.CANCELLED,
        }:
            return self._unavailable_artifact(
                job_id,
                f"Kubernetes Octave job is not terminal: {status.value}",
                plan=plan,
            )
        return self._collect_workspace_artifact(plan, status)

    def _strip_job_prefix(self, job_id: str) -> str:
        if not job_id.startswith("k8s-"):
            raise ValueError(f"Unsupported Kubernetes job id: {job_id}")
        job_name = job_id.removeprefix("k8s-").strip()
        if not job_name:
            raise ValueError(f"Unsupported Kubernetes job id: {job_id}")
        return job_name

    def _shared_workspace(self, plan: OctaveRunPlan) -> Path:
        workspace = Path(plan.execution_params.workspace_dir).expanduser()
        if not workspace.is_absolute():
            raise ValueError(
                "Kubernetes Octave execution requires an absolute node-visible workspace path"
            )
        return workspace

    def _map_status(self, status: str) -> ExecutionStatus:
        normalized = status.strip().lower()
        if normalized in {"succeeded", "complete", "completed"}:
            return ExecutionStatus.COMPLETED
        if normalized in {"failed", "error"}:
            return ExecutionStatus.FAILED
        if normalized in {"active", "running"}:
            return ExecutionStatus.RUNNING
        if normalized in {"cancelled", "canceled"}:
            return ExecutionStatus.CANCELLED
        return ExecutionStatus.QUEUED

    def _collect_workspace_artifact(
        self, plan: OctaveRunPlan, status: ExecutionStatus
    ) -> OctaveRunArtifact:
        workspace = self._shared_workspace(plan)
        if not workspace.exists():
            return self._unavailable_artifact(
                f"k8s-{plan.run_id}",
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
