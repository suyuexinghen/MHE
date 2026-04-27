from __future__ import annotations

from pydantic import BaseModel, Field

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.octave.contracts import OctaveRunPlan


class OctaveSlurmSubmission(BaseModel):
    job_name: str
    script: str
    command: list[str] = Field(default_factory=list)


class OctaveSlurmBackend:
    backend_name = "slurm"

    def build_submission(self, plan: OctaveRunPlan) -> OctaveSlurmSubmission:
        script = "\n".join(
            [
                "#!/bin/bash",
                f"#SBATCH --job-name={plan.run_id}",
                f"#SBATCH --output={plan.run_id}.out",
                "set -euo pipefail",
                " ".join(plan.execution_params.argv),
                "",
            ]
        )
        return OctaveSlurmSubmission(
            job_name=plan.run_id,
            script=script,
            command=["sbatch", f"{plan.run_id}.slurm"],
        )

    async def submit(self, plan: OctaveRunPlan) -> JobHandle:
        return JobHandle(job_id=f"dryrun-slurm-{plan.run_id}", backend=self.backend_name)

    async def poll(self, job_id: str) -> ExecutionStatus:
        return ExecutionStatus.QUEUED

    async def cancel(self, job_id: str) -> None:
        return None
