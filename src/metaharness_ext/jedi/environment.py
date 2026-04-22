from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import CAP_JEDI_ENV_PROBE
from metaharness_ext.jedi.contracts import (
    JediEnvironmentReport,
    JediExperimentSpec,
    JediForecastSpec,
    JediHofXSpec,
    JediLocalEnsembleDASpec,
    JediVariationalSpec,
)
from metaharness_ext.jedi.slots import JEDI_ENVIRONMENT_SLOT


class JediEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_ENVIRONMENT_SLOT)
        api.declare_input("task", "JediExperimentSpec")
        api.declare_output("environment", "JediEnvironmentReport", mode="sync")
        api.provide_capability(CAP_JEDI_ENV_PROBE)

    def probe(self, spec: JediExperimentSpec) -> JediEnvironmentReport:
        messages: list[str] = []
        binary_path = self._resolve_binary(spec.executable.binary_name)
        binary_available = binary_path is not None
        launcher_path: str | None = None
        launcher_available = True
        if spec.executable.launcher != "direct":
            launcher_path = self._resolve_binary(spec.executable.launcher)
            launcher_available = launcher_path is not None
            if not launcher_available:
                messages.append(f"Launcher not found: {spec.executable.launcher}")

        shared_libraries_resolved = True
        if binary_path is not None:
            shared_libraries_resolved = self._check_shared_libraries(binary_path, messages)
        else:
            messages.append(f"JEDI binary not found: {spec.executable.binary_name}")

        required_paths_present = True
        for path_str in self._required_paths(spec):
            path = Path(path_str).expanduser()
            if not path.exists():
                required_paths_present = False
                messages.append(f"Missing required path: {path}")

        return JediEnvironmentReport(
            binary_available=binary_available,
            launcher_available=launcher_available,
            shared_libraries_resolved=shared_libraries_resolved,
            required_paths_present=required_paths_present,
            binary_path=binary_path,
            launcher_path=launcher_path,
            messages=messages,
        )

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _check_shared_libraries(self, binary_path: str, messages: list[str]) -> bool:
        if shutil.which("ldd") is None:
            messages.append("ldd not found; skipping shared library resolution check")
            return True
        result = subprocess.run(
            ["ldd", binary_path],
            text=True,
            capture_output=True,
            check=False,
        )
        unresolved = [line.strip() for line in result.stdout.splitlines() if "not found" in line]
        if unresolved:
            messages.extend(f"Unresolved library: {line}" for line in unresolved)
            return False
        return result.returncode == 0

    def _required_paths(self, spec: JediExperimentSpec) -> list[str]:
        if isinstance(spec, JediVariationalSpec):
            return [
                *([spec.background_path] if spec.background_path else []),
                *([spec.background_error_path] if spec.background_error_path else []),
                *spec.observation_paths,
                *spec.required_paths,
            ]
        if isinstance(spec, JediLocalEnsembleDASpec):
            return [*spec.ensemble_paths, *spec.observation_paths, *spec.required_paths]
        if isinstance(spec, JediHofXSpec):
            return [
                *([spec.state_path] if spec.state_path else []),
                *spec.observation_paths,
                *spec.required_paths,
            ]
        if isinstance(spec, JediForecastSpec):
            return [
                *([spec.initial_condition_path] if spec.initial_condition_path else []),
                *spec.required_paths,
            ]
        return []
