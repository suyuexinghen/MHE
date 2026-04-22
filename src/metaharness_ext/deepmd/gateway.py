from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_CASE_COMPILE
from metaharness_ext.deepmd.contracts import (
    DeepMDDatasetSpec,
    DeepMDDescriptorSpec,
    DeepMDExecutableSpec,
    DeepMDFittingNetSpec,
    DeepMDTrainSpec,
)
from metaharness_ext.deepmd.slots import DEEPMD_GATEWAY_SLOT


class DeepMDGatewayComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_GATEWAY_SLOT)
        api.declare_output("task", "DeepMDTrainSpec", mode="sync")
        api.provide_capability(CAP_DEEPMD_CASE_COMPILE)

    def issue_task(
        self,
        *,
        train_systems: list[str],
        type_map: list[str],
        task_id: str = "deepmd-task-1",
        working_directory: str | None = None,
    ) -> DeepMDTrainSpec:
        return DeepMDTrainSpec(
            task_id=task_id,
            executable=DeepMDExecutableSpec(execution_mode="train"),
            dataset=DeepMDDatasetSpec(
                dataset_id=task_id,
                train_systems=train_systems,
                validation_systems=[],
                type_map=type_map,
                labels_present=["energy", "force"],
            ),
            type_map=type_map,
            descriptor=DeepMDDescriptorSpec(
                descriptor_type="se_e2_a",
                rcut=6.0,
                rcut_smth=5.5,
                sel=[32],
                neuron=[25, 50, 100],
            ),
            fitting_net=DeepMDFittingNetSpec(neuron=[240, 240, 240]),
            training={"numb_steps": 1000, "save_freq": 100, "disp_freq": 100},
            learning_rate={"type": "exp", "start_lr": 0.001, "decay_steps": 1000},
            loss={"type": "ener", "start_pref_e": 0.02, "start_pref_f": 1000.0},
            working_directory=working_directory,
        )
