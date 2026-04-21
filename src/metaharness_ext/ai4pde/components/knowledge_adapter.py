from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.ai4pde.contracts import PDETaskRequest
from metaharness_ext.ai4pde.slots import KNOWLEDGE_ADAPTER_SLOT


class KnowledgeAdapterComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(KNOWLEDGE_ADAPTER_SLOT)
        api.declare_input("task", "PDETaskRequest")
        api.declare_output("knowledge_context", "KnowledgeContext", mode="async")

    def enrich(self, request: PDETaskRequest) -> dict[str, object]:
        return {
            "task_id": request.task_id,
            "recommended_templates": ["ValidationBundleTemplate"],
            "physics_domain": request.physics_spec.get("equation", "unknown"),
        }
