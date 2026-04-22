from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_CASE_COMPILE
from metaharness_ext.jedi.contracts import JediExecutableSpec, JediVariationalSpec
from metaharness_ext.jedi.slots import JEDI_GATEWAY_SLOT


class JediGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_GATEWAY_SLOT)
        api.declare_output("task", "JediExperimentSpec", mode="sync")
        api.provide_capability(CAP_JEDI_CASE_COMPILE)

    def issue_task(
        self,
        *,
        task_id: str = "jedi-task-1",
        execution_mode: str = "validate_only",
        binary_name: str = "qg4DVar.x",
        launcher: str = "direct",
        background_path: str | None = None,
        observation_paths: list[str] | None = None,
        working_directory: str | None = None,
    ) -> JediVariationalSpec:
        return JediVariationalSpec(
            task_id=task_id,
            executable=JediExecutableSpec(
                binary_name=binary_name,
                launcher=launcher,
                execution_mode=execution_mode,
            ),
            background_path=background_path,
            observation_paths=list(observation_paths or []),
            working_directory=working_directory,
            variational={"minimizer": "RPCG"},
            output={"filename": "analysis.out"},
        )
