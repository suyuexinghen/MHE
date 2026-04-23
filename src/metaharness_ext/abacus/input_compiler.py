from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import CAP_ABACUS_CASE_COMPILE
from metaharness_ext.abacus.contracts import (
    AbacusExperimentSpec,
    AbacusMdSpec,
    AbacusNscfSpec,
    AbacusRelaxSpec,
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
        if isinstance(spec, AbacusNscfSpec):
            return self._compile_nscf(spec)
        if isinstance(spec, AbacusRelaxSpec):
            return self._compile_relax(spec)
        if isinstance(spec, AbacusMdSpec):
            return self._compile_md(spec)
        if isinstance(spec, AbacusScfSpec):
            return self._compile_scf(spec)
        raise ValueError(f"ABACUS family not yet supported: {type(spec).__name__}")

    def _compile_scf(self, spec: AbacusScfSpec) -> AbacusRunPlan:
        return self._build_plan(
            spec,
            application_family="scf",
            expected_logs=["running_scf.log"],
            required_runtime_paths=[],
        )

    def _compile_nscf(self, spec: AbacusNscfSpec) -> AbacusRunPlan:
        required_runtime_paths = [
            path for path in [spec.charge_density_path, spec.restart_file_path] if path is not None
        ]
        return self._build_plan(
            spec,
            application_family="nscf",
            expected_logs=["running_nscf.log", "running_scf.log"],
            required_runtime_paths=required_runtime_paths,
        )

    def _compile_relax(self, spec: AbacusRelaxSpec) -> AbacusRunPlan:
        restart_path = spec.relax_controls.get("restart_file_path")
        required_runtime_paths = (
            [restart_path] if isinstance(restart_path, str) and restart_path else []
        )
        return self._build_plan(
            spec,
            application_family="relax",
            expected_logs=["running_relax.log", "running_scf.log"],
            required_runtime_paths=required_runtime_paths,
        )

    def _compile_md(self, spec: AbacusMdSpec) -> AbacusRunPlan:
        return self._build_plan(
            spec,
            application_family="md",
            expected_logs=["running_md.log"],
            required_runtime_paths=[],
        )

    def _build_plan(
        self,
        spec: AbacusScfSpec | AbacusNscfSpec | AbacusRelaxSpec | AbacusMdSpec,
        *,
        application_family: str,
        expected_logs: list[str],
        required_runtime_paths: list[str],
    ) -> AbacusRunPlan:
        run_id = f"run-{spec.task_id}"
        working_directory = spec.working_directory or f"./abacus_runs/{spec.task_id}/{run_id}"
        output_root = f"OUT.{spec.suffix}"

        return AbacusRunPlan(
            task_id=spec.task_id,
            run_id=run_id,
            application_family=application_family,
            command=[],
            working_directory=working_directory,
            input_content=self._render_input(spec),
            structure_content=spec.structure.content,
            kpoints_content=spec.kpoints.content if spec.kpoints else None,
            suffix=spec.suffix,
            output_root=output_root,
            expected_outputs=[f"{output_root}/"],
            expected_logs=expected_logs,
            required_runtime_paths=required_runtime_paths,
            executable=spec.executable,
        )

    def _render_input(self, spec: AbacusExperimentSpec) -> str:
        lines: list[str] = []
        lines.append("INPUT_PARAMETERS")
        lines.append(f"suffix {spec.suffix}")
        lines.append(f"calculation {spec.calculation}")
        lines.append(f"basis_type {spec.basis_type}")
        lines.append(f"esolver_type {spec.esolver_type}")

        for key, value in spec.params.items():
            lines.append(f"{key} {value}")

        if isinstance(spec, AbacusNscfSpec):
            if spec.charge_density_path:
                lines.append(f"charge_density_path {spec.charge_density_path}")
            if spec.restart_file_path:
                lines.append(f"restart_file_path {spec.restart_file_path}")

        if isinstance(spec, AbacusRelaxSpec):
            for key, value in spec.relax_controls.items():
                lines.append(f"{key} {value}")

        if spec.pot_file:
            lines.append(f"pot_file {spec.pot_file}")

        return "\n".join(lines) + "\n"
