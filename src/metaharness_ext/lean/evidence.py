from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.capabilities import CAP_LEAN_BUILD_EVIDENCE
from metaharness_ext.lean.contracts import (
    LeanBlueprint,
    LeanEnvironmentReport,
    LeanEvidenceBundle,
    LeanProvenance,
    LeanRunArtifact,
    LeanValidationReport,
)
from metaharness_ext.lean.slots import LEAN_EVIDENCE_SLOT


class LeanEvidenceComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_EVIDENCE_SLOT)
        api.declare_input("validation", "LeanValidationReport")
        api.declare_output("evidence", "LeanEvidenceBundle", mode="sync")
        api.provide_capability(CAP_LEAN_BUILD_EVIDENCE)

    def build(
        self,
        *,
        task_ref: str,
        environment_report: LeanEnvironmentReport,
        validation_report: LeanValidationReport,
        artifacts: list[LeanRunArtifact],
        blueprint: LeanBlueprint | None = None,
        provenance: LeanProvenance | None = None,
    ) -> LeanEvidenceBundle:
        return LeanEvidenceBundle(
            bundle_id=f"bundle:{task_ref}",
            task_ref=task_ref,
            environment_report=environment_report,
            blueprint=blueprint,
            artifacts=artifacts,
            validation_report=validation_report,
            provenance=provenance or LeanProvenance(),
        )
