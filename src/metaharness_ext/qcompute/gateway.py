from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.manifest import ComponentManifest
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.qcompute.capabilities import CAP_QCOMPUTE_CASE_COMPILE
from metaharness_ext.qcompute.contracts import QComputeExperimentSpec
from metaharness_ext.qcompute.slots import QCOMPUTE_GATEWAY_SLOT


class QComputeGatewayComponent(HarnessComponent):
    def __init__(self, manifest: ComponentManifest | None = None) -> None:
        self._manifest = manifest
        self._runtime: ComponentRuntime | None = None

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(QCOMPUTE_GATEWAY_SLOT)
        api.declare_output("task", "QComputeExperimentSpec", mode="sync")
        api.provide_capability(CAP_QCOMPUTE_CASE_COMPILE)

    def issue_task(self, *, experiment: QComputeExperimentSpec) -> QComputeExperimentSpec:
        return experiment
