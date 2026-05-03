from __future__ import annotations

import uuid
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.moose.capabilities import CAP_MOOSE_TASK_ISSUE
from metaharness_ext.moose.contracts import MooseProblemSpec
from metaharness_ext.moose.slots import MOOSE_GATEWAY_SLOT
from metaharness_ext.moose.types import MooseInputMode


class MooseGatewayComponent(HarnessComponent):
    """Task intake gateway for MOOSE simulations."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(MOOSE_GATEWAY_SLOT)
        api.declare_input("task", "MooseProblemSpec")
        api.declare_output("task", "MooseProblemSpec", mode="sync")
        api.provide_capability(CAP_MOOSE_TASK_ISSUE)

    def issue_task(
        self,
        task_id: str,
        input_source: str | None = None,
        *,
        input_mode: MooseInputMode = "inline",
        overrides: dict[str, Any] | None = None,
    ) -> MooseProblemSpec:
        if input_source is None:
            input_source = (
                "[Mesh]\n"
                "  type = GeneratedMeshGenerator\n"
                "  dim = 1\n"
                "[]\n"
                "[Executioner]\n"
                "  type = Steady\n"
                "[]\n"
            )
        spec = MooseProblemSpec(
            task_id=task_id, input={"mode": input_mode, "inline_source": input_source}
        )
        if overrides:
            for key, value in overrides.items():
                if hasattr(spec, key):
                    setattr(spec, key, value)
                elif "." in key:
                    obj = spec
                    parts = key.split(".")
                    for part in parts[:-1]:
                        obj = getattr(obj, part)
                    setattr(obj, parts[-1], value)
        return spec

    def compile_problem(
        self,
        spec: MooseProblemSpec,
        compiler: Any,
        run_id: str | None = None,
        workspace_dir: str = ".runs/moose",
    ):
        if run_id is None:
            run_id = f"moose-run-{uuid.uuid4().hex[:12]}"
        return compiler.compile(spec, run_id=run_id, workspace_dir=workspace_dir)

    def run_baseline(
        self,
        spec: MooseProblemSpec,
        compiler: Any,
        executor: Any,
        run_id: str | None = None,
        workspace_dir: str = ".runs/moose",
    ):
        plan = self.compile_problem(spec, compiler, run_id=run_id, workspace_dir=workspace_dir)
        artifact = executor.execute_plan(plan)
        return plan, artifact
