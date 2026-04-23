from __future__ import annotations

import shutil
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_ENV_PROBE
from metaharness_ext.deepmd.contracts import (
    DeepMDEnvironmentReport,
    DeepMDExperimentSpec,
    DeepMDTrainSpec,
    DPGenAutotestSpec,
    DPGenRunSpec,
    DPGenSimplifySpec,
)
from metaharness_ext.deepmd.slots import DEEPMD_ENVIRONMENT_SLOT


class DeepMDEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_ENVIRONMENT_SLOT)
        api.declare_input("task", "DeepMDTrainSpec")
        api.declare_output("environment", "DeepMDEnvironmentReport", mode="sync")
        api.provide_capability(CAP_DEEPMD_ENV_PROBE)

    def probe(self, spec: DeepMDExperimentSpec) -> DeepMDEnvironmentReport:
        messages: list[str] = []
        missing_required_paths: list[str] = []
        environment_prerequisites: list[str] = []
        missing_prerequisites: list[str] = []

        dp_available = shutil.which(spec.executable.binary_name) is not None
        python_binary = self._python_binary(spec)
        python_available = python_binary is not None

        for path_str in self._required_paths(spec):
            path = Path(path_str).expanduser()
            if path.exists():
                continue
            missing_required_paths.append(str(path))
            label = "dataset path" if isinstance(spec, DeepMDTrainSpec) else "workspace path"
            messages.append(f"Missing {label}: {path}")

        required_paths_present = not missing_required_paths
        workspace_ready = required_paths_present

        if spec.working_directory is not None:
            workdir = Path(spec.working_directory).expanduser()
            if workdir.exists() and not workdir.is_dir():
                required_paths_present = False
                workspace_ready = False
                missing_required_paths.append(str(workdir))
                messages.append(f"Working directory is not a directory: {workdir}")

        machine_root_ready = True
        remote_root_configured = True
        scheduler_command_configured = True

        if isinstance(spec, DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec):
            environment_prerequisites = self._environment_prerequisites(spec)
            local_root = Path(spec.machine.local_root).expanduser()
            if not local_root.exists() or not local_root.is_dir():
                machine_root_ready = False
                workspace_ready = False
                messages.append(f"Machine local root is not a directory: {local_root}")
            if spec.machine.context_type != "local" and not spec.machine.remote_root:
                remote_root_configured = False
                missing_prerequisites.append("machine.remote_root")
                messages.append("Missing environment prerequisite: machine.remote_root")
            if spec.machine.batch_type != "shell" and not spec.machine.command:
                scheduler_command_configured = False
                missing_prerequisites.append("machine.command")
                messages.append("Missing environment prerequisite: machine.command")
            if spec.machine.python_path and shutil.which(spec.machine.python_path) is None:
                missing_prerequisites.append("machine.python_path")
                messages.append(
                    f"Configured Python interpreter not found: {spec.machine.python_path}"
                )
                python_available = False

        if isinstance(spec, DeepMDTrainSpec):
            environment_prerequisites = self._environment_prerequisites(spec)

        missing_prerequisites.extend(
            prerequisite
            for prerequisite in environment_prerequisites
            if prerequisite == "python" and not python_available
        )

        if not dp_available:
            binary_label = "DP-GEN" if spec.application_family.startswith("dpgen_") else "DeepMD"
            messages.append(f"{binary_label} binary not found: {spec.executable.binary_name}")
        if not python_available:
            messages.append("Python interpreter not found on PATH")

        return DeepMDEnvironmentReport(
            application_family=spec.application_family,
            execution_mode=spec.executable.execution_mode,
            dp_available=dp_available,
            python_available=python_available,
            required_paths_present=required_paths_present,
            workspace_ready=workspace_ready,
            machine_root_ready=machine_root_ready,
            remote_root_configured=remote_root_configured,
            scheduler_command_configured=scheduler_command_configured,
            missing_required_paths=missing_required_paths,
            environment_prerequisites=environment_prerequisites,
            missing_prerequisites=list(dict.fromkeys(missing_prerequisites)),
            messages=messages,
        )

    def _required_paths(self, spec: DeepMDExperimentSpec) -> list[str]:
        if isinstance(spec, DeepMDTrainSpec):
            return [*spec.dataset.train_systems, *spec.dataset.validation_systems]
        return list(spec.workspace_files)

    def _environment_prerequisites(self, spec: DeepMDExperimentSpec) -> list[str]:
        prerequisites = ["python"]
        if isinstance(spec, DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec):
            prerequisites.append("machine.local_root")
            if spec.machine.context_type != "local":
                prerequisites.append("machine.remote_root")
            if spec.machine.batch_type != "shell":
                prerequisites.append("machine.command")
            if spec.machine.python_path:
                prerequisites.append("machine.python_path")
        return prerequisites

    def _python_binary(self, spec: DeepMDExperimentSpec) -> str | None:
        if isinstance(spec, DPGenRunSpec | DPGenSimplifySpec | DPGenAutotestSpec):
            if spec.machine.python_path:
                return shutil.which(spec.machine.python_path)
        return shutil.which("python") or shutil.which("python3")
