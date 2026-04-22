from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_CASE_COMPILE
from metaharness_ext.deepmd.contracts import DeepMDRunPlan, DeepMDTrainSpec
from metaharness_ext.deepmd.slots import DEEPMD_CONFIG_COMPILER_SLOT


def build_train_input_json(spec: DeepMDTrainSpec) -> dict[str, Any]:
    systems = list(spec.dataset.train_systems)
    systems.extend(spec.dataset.validation_systems)
    return {
        "model": {
            "type_map": spec.type_map,
            "descriptor": {
                "type": spec.descriptor.descriptor_type,
                "rcut": spec.descriptor.rcut,
                "rcut_smth": spec.descriptor.rcut_smth,
                "sel": spec.descriptor.sel,
                **({"neuron": spec.descriptor.neuron} if spec.descriptor.neuron else {}),
                **({"seed": spec.descriptor.seed} if spec.descriptor.seed is not None else {}),
            },
            "fitting_net": {
                "neuron": spec.fitting_net.neuron,
                "resnet_dt": spec.fitting_net.resnet_dt,
                **({"seed": spec.fitting_net.seed} if spec.fitting_net.seed is not None else {}),
            },
        },
        "training": {
            "training_data": {
                "systems": systems,
                "batch_size": spec.training.get("batch_size", "auto"),
            },
            **spec.training,
        },
        "learning_rate": spec.learning_rate,
        "loss": spec.loss,
    }


class DeepMDTrainConfigCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_CONFIG_COMPILER_SLOT)
        api.declare_input("task", "DeepMDTrainSpec")
        api.declare_output("plan", "DeepMDRunPlan", mode="sync")
        api.provide_capability(CAP_DEEPMD_CASE_COMPILE)

    def build_plan(self, spec: DeepMDTrainSpec) -> DeepMDRunPlan:
        run_id = f"{spec.task_id}-{uuid.uuid4().hex[:8]}"
        if spec.working_directory is not None:
            working_directory = str(Path(spec.working_directory).expanduser())
        else:
            working_directory = run_id
        input_json = build_train_input_json(spec)
        input_json_path = str(Path(working_directory) / "input.json")
        return DeepMDRunPlan(
            task_id=spec.task_id,
            run_id=run_id,
            execution_mode=spec.executable.execution_mode,
            command=[spec.executable.binary_name, spec.executable.execution_mode, "input.json"],
            working_directory=working_directory,
            input_json_path=input_json_path,
            expected_outputs=["lcurve.out", "checkpoint"],
            expected_logs=["stdout.log", "stderr.log"],
            dataset_paths=list(spec.dataset.train_systems) + list(spec.dataset.validation_systems),
            input_json=input_json,
            executable=spec.executable,
        )
