from __future__ import annotations

from metaharness.sdk.execution import ExecutionStatus, JobHandle
from metaharness_ext.octave.contracts import OctaveRunPlan
from metaharness_ext.octave.scheduler.k8s_backend import OctaveK8sBackend
from metaharness_ext.octave.scheduler.slurm_backend import OctaveSlurmBackend


class OctaveSchedulerAdapter:
    def __init__(
        self,
        *,
        slurm: OctaveSlurmBackend | None = None,
        k8s: OctaveK8sBackend | None = None,
    ) -> None:
        self._backends = {
            "slurm": slurm or OctaveSlurmBackend(),
            "k8s": k8s or OctaveK8sBackend(),
        }

    async def submit(self, plan: OctaveRunPlan) -> JobHandle:
        return await self._backend(plan).submit(plan)

    async def poll(self, job_id: str) -> ExecutionStatus:
        backend = self._backend_for_job(job_id)
        return await backend.poll(job_id)

    async def cancel(self, job_id: str) -> None:
        backend = self._backend_for_job(job_id)
        await backend.cancel(job_id)

    async def await_result(self, job_id: str, timeout: float | None = None) -> None:
        raise NotImplementedError("Dry-run scheduler adapter does not collect remote artifacts")

    def _backend(self, plan: OctaveRunPlan):
        backend_name = str(
            plan.graph_metadata.get("target_backend")
            or plan.executable.env.get("MHE_BACKEND")
            or "slurm"
        )
        if backend_name not in self._backends:
            raise ValueError(f"Unsupported Octave scheduler backend: {backend_name}")
        return self._backends[backend_name]

    def _backend_for_job(self, job_id: str):
        if job_id.startswith("dryrun-k8s-"):
            return self._backends["k8s"]
        return self._backends["slurm"]
