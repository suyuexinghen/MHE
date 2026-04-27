from __future__ import annotations

from pydantic import BaseModel, Field

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.octave.contracts import OctaveRunPlan


class OctaveK8sJobManifest(BaseModel):
    name: str
    manifest: dict[str, object] = Field(default_factory=dict)


class OctaveK8sBackend:
    backend_name = "k8s"

    def build_manifest(self, plan: OctaveRunPlan) -> OctaveK8sJobManifest:
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
                                }
                            ],
                        }
                    }
                },
            },
        )

    async def submit(self, plan: OctaveRunPlan) -> JobHandle:
        return JobHandle(job_id=f"dryrun-k8s-{plan.run_id}", backend=self.backend_name)

    async def poll(self, job_id: str) -> ExecutionStatus:
        return ExecutionStatus.QUEUED

    async def cancel(self, job_id: str) -> None:
        return None
