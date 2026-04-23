from __future__ import annotations

from typing import Literal

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_CASE_COMPILE
from metaharness_ext.jedi.contracts import (
    JediExecutableSpec,
    JediLocalEnsembleDASpec,
    JediVariationalSpec,
)
from metaharness_ext.jedi.slots import JEDI_GATEWAY_SLOT
from metaharness_ext.jedi.types import JediExecutionMode


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
        execution_mode: JediExecutionMode = "validate_only",
        binary_name: str = "qg4DVar.x",
        launcher: str = "direct",
        process_count: int | None = None,
        background_path: str | None = None,
        background_error_path: str | None = None,
        observation_paths: list[str] | None = None,
        working_directory: str | None = None,
        scientific_check: Literal["runtime_only", "rms_improves"] = "runtime_only",
    ) -> JediVariationalSpec:
        return JediVariationalSpec(
            task_id=task_id,
            executable=JediExecutableSpec(
                binary_name=binary_name,
                launcher=launcher,
                execution_mode=execution_mode,
                process_count=process_count,
            ),
            background_path=background_path,
            background_error_path=background_error_path,
            observation_paths=list(observation_paths or []),
            working_directory=working_directory,
            variational={"minimizer": {"algorithm": "RPCG", "iterations": 20}},
            output={"filename": "analysis.out"},
            final={"diagnostics": {"filename": "departures.json"}},
            test={"reference": {"filename": "reference.json"}},
            expected_diagnostics=["departures.json"],
            scientific_check=scientific_check,
        )

    def issue_local_ensemble_task(
        self,
        *,
        task_id: str = "jedi-letkf-task-1",
        execution_mode: JediExecutionMode = "validate_only",
        binary_name: str = "qgLETKF.x",
        launcher: str = "direct",
        process_count: int | None = None,
        ensemble_paths: list[str] | None = None,
        background_path: str | None = None,
        observation_paths: list[str] | None = None,
        working_directory: str | None = None,
        scientific_check: Literal["runtime_only", "ensemble_outputs_present"] = "runtime_only",
    ) -> JediLocalEnsembleDASpec:
        return JediLocalEnsembleDASpec(
            task_id=task_id,
            executable=JediExecutableSpec(
                binary_name=binary_name,
                launcher=launcher,
                execution_mode=execution_mode,
                process_count=process_count,
            ),
            ensemble_paths=list(ensemble_paths or []),
            background_path=background_path,
            observation_paths=list(observation_paths or []),
            working_directory=working_directory,
            driver={"task": "local_ensemble_da"},
            ensemble={"solver": {"algorithm": "LETKF", "iterations": 5}},
            output={"filename": "letkf.out"},
            final={"diagnostics": {"filename": "posterior.out"}},
            test={"reference": {"filename": "ensemble_reference.json"}},
            expected_diagnostics=["posterior.out"],
            scientific_check=scientific_check,
        )
