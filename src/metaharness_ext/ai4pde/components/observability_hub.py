from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.contracts import ScientificEvidenceBundle, ValidationBundle
from metaharness_ext.ai4pde.policies import evaluate_observation_window
from metaharness_ext.ai4pde.slots import OBSERVABILITY_HUB_SLOT


class ObservabilityHubComponent(HarnessComponent):
    protected = True

    def __init__(self) -> None:
        self.telemetry: list[dict[str, object]] = []
        self.lifecycle: list[dict[str, object]] = []
        self.scientific_events: list[dict[str, object]] = []

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OBSERVABILITY_HUB_SLOT)
        api.declare_input("validation_bundle", "ValidationBundle")
        api.declare_input("evidence_bundle", "ScientificEvidenceBundle")
        api.declare_output("observation_report", "ObservationReport", mode="async")

    def record(
        self,
        validation_bundle: ValidationBundle,
        evidence_bundle: ScientificEvidenceBundle,
    ) -> dict[str, object]:
        event = {
            "task_id": validation_bundle.task_id,
            "graph_version_id": validation_bundle.graph_version_id,
            "status": validation_bundle.summary.get("status", "unknown"),
            "evidence_refs": len(evidence_bundle.provenance_refs),
        }
        self.scientific_events.append(event)
        self.lifecycle.append(
            {
                "task_id": validation_bundle.task_id,
                "graph_version_id": validation_bundle.graph_version_id,
            }
        )
        self.telemetry.append(
            {
                "task_id": validation_bundle.task_id,
                "residual_l2": validation_bundle.summary.get("residual_l2", 1.0),
            }
        )
        observation = evaluate_observation_window(
            task_count=len(self.scientific_events),
            duration_minutes=max(30, len(self.scientific_events) * 10),
            degrade_ratio=0.0,
        )
        return {**event, **observation}
