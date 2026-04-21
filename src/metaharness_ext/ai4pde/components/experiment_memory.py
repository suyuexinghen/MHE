from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.contracts import ScientificEvidenceBundle, ValidationBundle
from metaharness_ext.ai4pde.slots import EXPERIMENT_MEMORY_SLOT


class ExperimentMemoryComponent(HarnessComponent):
    def __init__(self) -> None:
        self.benchmark_snapshots: list[dict[str, object]] = []
        self.run_summaries: list[dict[str, object]] = []
        self.failure_summaries: list[dict[str, object]] = []

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(EXPERIMENT_MEMORY_SLOT)
        api.declare_input("validation_bundle", "ValidationBundle")
        api.declare_input("evidence_bundle", "ScientificEvidenceBundle")
        api.declare_output("memory_record", "MemoryRecord", mode="async")

    def remember(
        self,
        validation_bundle: ValidationBundle,
        evidence_bundle: ScientificEvidenceBundle,
    ) -> dict[str, str]:
        self.benchmark_snapshots.extend(
            {"ref": ref, "task_id": validation_bundle.task_id}
            for ref in evidence_bundle.benchmark_snapshot_refs
        )
        self.run_summaries.append(validation_bundle.summary)
        if validation_bundle.violations:
            self.failure_summaries.append(
                {"task_id": validation_bundle.task_id, "violations": validation_bundle.violations}
            )
        return {
            "benchmark_snapshots": str(len(self.benchmark_snapshots)),
            "run_summaries": str(len(self.run_summaries)),
            "failure_summaries": str(len(self.failure_summaries)),
        }
