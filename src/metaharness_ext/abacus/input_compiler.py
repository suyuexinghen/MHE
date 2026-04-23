from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import CAP_ABACUS_CASE_COMPILE
from metaharness_ext.abacus.contracts import (
    AbacusExperimentSpec,
    AbacusRunPlan,
    AbacusScfSpec,
)
from metaharness_ext.abacus.slots import ABACUS_INPUT_COMPILER_SLOT


class AbacusInputCompilerComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self, runtime: ComponentRuntime) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(ABACUS_INPUT_COMPILER_SLOT)
        api.declare_input("task", "AbacusExperimentSpec")
        api.declare_output("plan", "AbacusRunPlan", mode="sync")
        api.provide_capability(CAP_ABACUS_CASE_COMPILE)

    def compile(self, spec: AbacusExperimentSpec) -> AbacusRunPlan:
        if not isinstance(spec, AbacusScfSpec):
            raise ValueError(f"Phase 0 only supports AbacusScfSpec, got {type(spec).__name__}")

        run_id = f"run-{spec.task_id}"
        working_directory = spec.working_directory or f"./abacus_runs/{spec.task_id}/{run_id}"

        input_content = self._render_input(spec)
        structure_content = spec.structure.content
        kpoints_content = spec.kpoints.content if spec.kpoints else None

        expected_outputs = [f"OUT.{spec.suffix}/"]
        expected_logs = ["running_scf.log"]

        return AbacusRunPlan(
            task_id=spec.task_id,
            run_id=run_id,
            application_family="scf",
            command=[],
            working_directory=working_directory,
            input_content=input_content,
            structure_content=structure_content,
            kpoints_content=kpoints_content,
            suffix=spec.suffix,
            expected_outputs=expected_outputs,
            expected_logs=expected_logs,
            required_runtime_paths=[],
            executable=spec.executable,
        )

    def _render_input(self, spec: AbacusScfSpec) -> str:
        lines: list[str] = []
        lines.append("INPUT_PARAMETERS")
        lines.append(f"suffix {spec.suffix}")
        lines.append(f"calculation {spec.calculation}")
        lines.append(f"basis_type {spec.basis_type}")
        lines.append(f"esolver_type {spec.esolver_type}")

        for key, value in spec.params.items():
            lines.append(f"{key} {value}")

        if spec.pot_file:
            lines.append(f"pot_file {spec.pot_file}")

        return "\n".join(lines) + "\n"
