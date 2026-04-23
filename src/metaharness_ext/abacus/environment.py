from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import CAP_ABACUS_ENV_PROBE
from metaharness_ext.abacus.contracts import (
    AbacusEnvironmentReport,
    AbacusExperimentSpec,
    AbacusMdSpec,
)
from metaharness_ext.abacus.slots import ABACUS_ENVIRONMENT_SLOT


class AbacusEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self, runtime: ComponentRuntime) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(ABACUS_ENVIRONMENT_SLOT)
        api.declare_input("task", "AbacusExperimentSpec")
        api.declare_output("environment", "AbacusEnvironmentReport", mode="sync")
        api.provide_capability(CAP_ABACUS_ENV_PROBE)

    def probe(self, spec: AbacusExperimentSpec) -> AbacusEnvironmentReport:
        messages: list[str] = []

        abacus_path = self._resolve_binary(spec.executable.binary_name)
        abacus_available = abacus_path is not None
        if not abacus_available:
            messages.append(f"ABACUS binary not found: {spec.executable.binary_name}")

        version_probe_supported = False
        version_probe_succeeded = False
        version_output: str | None = None
        info_probe_supported = False
        info_probe_succeeded = False
        info_output: str | None = None
        check_input_probe_supported = False
        check_input_probe_succeeded = False
        check_input_output: str | None = None

        if abacus_available:
            version_output = self._probe_version(abacus_path)
            version_probe_supported = True
            version_probe_succeeded = version_output is not None
            if not version_probe_succeeded:
                messages.append("abacus --version probe failed")

            info_output = self._probe_info(abacus_path)
            info_probe_supported = True
            info_probe_succeeded = info_output is not None
            if not info_probe_succeeded:
                messages.append("abacus --info probe failed")

            check_input_output = self._probe_check_input(abacus_path)
            check_input_probe_supported = True
            check_input_probe_succeeded = check_input_output is not None
            if not check_input_probe_succeeded:
                messages.append("abacus --check-input probe failed")

        launcher_path: str | None = None
        launcher_available = True
        requested_launcher = spec.executable.launcher
        if requested_launcher != "direct":
            launcher_path = self._resolve_binary(requested_launcher)
            launcher_available = launcher_path is not None
            if not launcher_available:
                messages.append(f"Launcher not found: {requested_launcher}")

        deeppmd_support_detected = False
        gpu_support_detected = False
        if info_probe_succeeded and info_output:
            deeppmd_support_detected = (
                "deepmd" in info_output.lower() or "dp" in info_output.lower()
            )
            gpu_support_detected = "cuda" in info_output.lower() or "gpu" in info_output.lower()

        required_paths_present = True
        for path_str in self._required_paths(spec):
            path = Path(path_str).expanduser()
            if not path.exists():
                required_paths_present = False
                messages.append(f"Missing required path: {path}")

        if spec.working_directory is not None:
            workdir = Path(spec.working_directory).expanduser()
            if workdir.exists() and not workdir.is_dir():
                required_paths_present = False
                messages.append(f"Working directory is not a directory: {workdir}")

        if (
            isinstance(spec, AbacusMdSpec)
            and spec.esolver_type == "dp"
            and not deeppmd_support_detected
        ):
            messages.append("DeePMD support not detected but esolver_type=dp requested")

        return AbacusEnvironmentReport(
            abacus_available=abacus_available,
            abacus_path=abacus_path,
            version_probe_supported=version_probe_supported,
            version_probe_succeeded=version_probe_succeeded,
            version_output=version_output,
            info_probe_supported=info_probe_supported,
            info_probe_succeeded=info_probe_succeeded,
            info_output=info_output,
            check_input_probe_supported=check_input_probe_supported,
            check_input_probe_succeeded=check_input_probe_succeeded,
            check_input_output=check_input_output,
            requested_launcher=requested_launcher,
            launcher_available=launcher_available,
            launcher_path=launcher_path,
            deeppmd_support_detected=deeppmd_support_detected,
            gpu_support_detected=gpu_support_detected,
            required_paths_present=required_paths_present,
            messages=messages,
        )

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _probe_version(self, binary_path: str) -> str | None:
        try:
            result = subprocess.run(
                [binary_path, "--version"],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None

    def _probe_info(self, binary_path: str) -> str | None:
        try:
            result = subprocess.run(
                [binary_path, "--info"],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None

    def _probe_check_input(self, binary_path: str) -> str | None:
        try:
            result = subprocess.run(
                [binary_path, "--check-input"],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
            return result.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            pass
        return None

    def _required_paths(self, spec: AbacusExperimentSpec) -> list[str]:
        paths: list[str] = []
        paths.extend(spec.required_paths)
        paths.extend(spec.pseudo_files)
        paths.extend(spec.orbital_files)
        if spec.pot_file:
            paths.append(spec.pot_file)
        return paths
