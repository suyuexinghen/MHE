from __future__ import annotations

import shutil
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import CAP_DEEPMD_ENV_PROBE
from metaharness_ext.deepmd.contracts import DeepMDEnvironmentReport, DeepMDTrainSpec
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

    def probe(self, spec: DeepMDTrainSpec) -> DeepMDEnvironmentReport:
        messages: list[str] = []
        dp_available = shutil.which(spec.executable.binary_name) is not None
        python_available = shutil.which("python") is not None or shutil.which("python3") is not None

        required_paths_present = True
        for path_str in spec.dataset.train_systems + spec.dataset.validation_systems:
            path = Path(path_str).expanduser()
            if not path.exists():
                required_paths_present = False
                messages.append(f"Missing dataset path: {path}")

        if spec.working_directory is not None:
            workdir = Path(spec.working_directory).expanduser()
            if workdir.exists() and not workdir.is_dir():
                required_paths_present = False
                messages.append(f"Working directory is not a directory: {workdir}")

        if not dp_available:
            messages.append(f"DeepMD binary not found: {spec.executable.binary_name}")
        if not python_available:
            messages.append("Python interpreter not found on PATH")

        return DeepMDEnvironmentReport(
            dp_available=dp_available,
            python_available=python_available,
            required_paths_present=required_paths_present,
            messages=messages,
        )
