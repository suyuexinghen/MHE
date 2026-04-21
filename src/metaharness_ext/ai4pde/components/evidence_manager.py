from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.capabilities import CAP_EVIDENCE_BUNDLING
from metaharness_ext.ai4pde.contracts import (
    PDERunArtifact,
    ReferenceResult,
    ScientificEvidenceBundle,
    ValidationBundle,
)
from metaharness_ext.ai4pde.evidence import build_evidence_bundle
from metaharness_ext.ai4pde.slots import EVIDENCE_MANAGER_SLOT


class EvidenceManagerComponent(HarnessComponent):
    protected = True

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(EVIDENCE_MANAGER_SLOT)
        api.declare_input("run_artifact", "PDERunArtifact")
        api.declare_input("validation_bundle", "ValidationBundle")
        api.declare_output("evidence_bundle", "ScientificEvidenceBundle", mode="async")
        api.provide_capability(CAP_EVIDENCE_BUNDLING)

    def assemble_evidence(
        self,
        run_artifact: PDERunArtifact,
        validation_bundle: ValidationBundle,
        *,
        reference_result: ReferenceResult | None = None,
        graph_family: str = "ai4pde-minimal",
    ) -> ScientificEvidenceBundle:
        return build_evidence_bundle(
            run_artifact,
            validation_bundle,
            graph_metadata={"graph_family": graph_family},
            reference_result=reference_result,
        )
