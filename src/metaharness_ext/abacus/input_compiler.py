from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import CAP_ABACUS_CASE_COMPILE
from metaharness_ext.abacus.contracts import (
    AbacusControlFiles,
    AbacusEnvironmentReport,
    AbacusExperimentSpec,
    AbacusLifecycleState,
    AbacusMdSpec,
    AbacusNscfSpec,
    AbacusOutputExpectations,
    AbacusRelaxSpec,
    AbacusRunPlan,
    AbacusRuntimeAssets,
    AbacusScfSpec,
    AbacusWorkspaceLayout,
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
        api.declare_input("environment", "AbacusEnvironmentReport", required=False)
        api.declare_output("plan", "AbacusRunPlan", mode="sync")
        api.provide_capability(CAP_ABACUS_CASE_COMPILE)

    def compile(
        self,
        spec: AbacusExperimentSpec,
        environment: AbacusEnvironmentReport | None = None,
    ) -> AbacusRunPlan:
        if isinstance(spec, AbacusNscfSpec):
            return self._compile_nscf(spec, environment)
        if isinstance(spec, AbacusRelaxSpec):
            return self._compile_relax(spec, environment)
        if isinstance(spec, AbacusMdSpec):
            return self._compile_md(spec, environment)
        if isinstance(spec, AbacusScfSpec):
            return self._compile_scf(spec, environment)
        raise ValueError(f"ABACUS family not yet supported: {type(spec).__name__}")

    def _compile_scf(
        self,
        spec: AbacusScfSpec,
        environment: AbacusEnvironmentReport | None,
    ) -> AbacusRunPlan:
        return self._build_plan(
            spec,
            environment=environment,
            application_family="scf",
            expected_logs=["running_scf.log"],
            required_runtime_paths=[],
        )

    def _compile_nscf(
        self,
        spec: AbacusNscfSpec,
        environment: AbacusEnvironmentReport | None,
    ) -> AbacusRunPlan:
        required_runtime_paths = [
            path for path in [spec.charge_density_path, spec.restart_file_path] if path is not None
        ]
        return self._build_plan(
            spec,
            environment=environment,
            application_family="nscf",
            expected_logs=["running_nscf.log", "running_scf.log"],
            required_runtime_paths=required_runtime_paths,
        )

    def _compile_relax(
        self,
        spec: AbacusRelaxSpec,
        environment: AbacusEnvironmentReport | None,
    ) -> AbacusRunPlan:
        required_runtime_paths = [spec.restart_file_path] if spec.restart_file_path else []
        return self._build_plan(
            spec,
            environment=environment,
            application_family="relax",
            expected_logs=["running_relax.log", "running_scf.log"],
            required_runtime_paths=required_runtime_paths,
        )

    def _compile_md(
        self,
        spec: AbacusMdSpec,
        environment: AbacusEnvironmentReport | None,
    ) -> AbacusRunPlan:
        required_runtime_paths = (
            [spec.pot_file] if spec.esolver_type == "dp" and spec.pot_file else []
        )
        return self._build_plan(
            spec,
            environment=environment,
            application_family="md",
            expected_logs=["running_md.log"],
            required_runtime_paths=required_runtime_paths,
        )

    def _build_plan(
        self,
        spec: AbacusScfSpec | AbacusNscfSpec | AbacusRelaxSpec | AbacusMdSpec,
        *,
        environment: AbacusEnvironmentReport | None,
        application_family: str,
        expected_logs: list[str],
        required_runtime_paths: list[str],
    ) -> AbacusRunPlan:
        run_id = f"run-{spec.task_id}"
        working_directory = spec.working_directory or f"./abacus_runs/{spec.task_id}/{run_id}"
        output_root = f"OUT.{spec.suffix}"
        control_files = AbacusControlFiles(
            input_content=self._render_input(spec),
            structure_content=spec.structure.content,
            kpoints_name="KPT" if spec.kpoints else None,
            kpoints_content=spec.kpoints.content if spec.kpoints else None,
        )
        runtime_assets = self._build_runtime_assets(spec, required_runtime_paths)
        workspace_layout = AbacusWorkspaceLayout(
            working_directory=working_directory,
            output_root=output_root,
        )
        output_expectations = AbacusOutputExpectations(
            expected_outputs=[f"{output_root}/"],
            expected_logs=expected_logs,
        )

        return AbacusRunPlan(
            task_id=spec.task_id,
            run_id=run_id,
            application_family=application_family,
            command=[],
            working_directory=working_directory,
            input_content=control_files.input_content,
            structure_content=control_files.structure_content,
            kpoints_content=control_files.kpoints_content,
            control_files=control_files,
            runtime_assets=runtime_assets,
            workspace_layout=workspace_layout,
            output_expectations=output_expectations,
            lifecycle_state=AbacusLifecycleState(compiled=True),
            suffix=spec.suffix,
            esolver_type=spec.esolver_type,
            pot_file=spec.pot_file,
            environment_prerequisites=(
                list(environment.environment_prerequisites)
                if environment is not None
                else self._environment_prerequisites(spec)
            ),
            environment_evidence_refs=(
                list(environment.evidence_refs)
                if environment is not None
                else [f"abacus://environment/{spec.task_id}"]
            ),
            output_root=output_root,
            expected_outputs=[f"{output_root}/"],
            expected_logs=expected_logs,
            required_runtime_paths=required_runtime_paths,
            executable=spec.executable,
        )

    def _build_runtime_assets(
        self,
        spec: AbacusExperimentSpec,
        required_runtime_paths: list[str],
    ) -> AbacusRuntimeAssets:
        restart_inputs: list[str] = []
        charge_density_path: str | None = None

        if isinstance(spec, AbacusNscfSpec):
            charge_density_path = spec.charge_density_path
            if spec.restart_file_path:
                restart_inputs.append(spec.restart_file_path)
        if isinstance(spec, AbacusRelaxSpec) and spec.restart_file_path:
            restart_inputs.append(spec.restart_file_path)

        return AbacusRuntimeAssets(
            explicit_required_paths=list(spec.required_paths),
            pseudo_files=list(spec.pseudo_files),
            orbital_files=list(spec.orbital_files),
            restart_inputs=restart_inputs,
            charge_density_path=charge_density_path,
            pot_file=spec.pot_file,
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
            if spec.restart_file_path:
                lines.append(f"restart_file_path {spec.restart_file_path}")

        if spec.pot_file:
            lines.append(f"pot_file {spec.pot_file}")

        return "\n".join(lines) + "\n"

    def _environment_prerequisites(self, spec: AbacusExperimentSpec) -> list[str]:
        if isinstance(spec, AbacusMdSpec) and spec.esolver_type == "dp":
            return ["deeppmd_support"]
        return []
