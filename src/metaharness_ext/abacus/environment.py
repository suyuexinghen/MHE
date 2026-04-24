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
    AbacusNscfSpec,
    AbacusRelaxSpec,
    AbacusRuntimeAssets,
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

        deeppmd_probe_supported = info_probe_supported
        deeppmd_probe_succeeded = info_probe_succeeded
        deeppmd_support_detected: bool | None = None
        gpu_support_detected: bool | None = None
        if info_probe_succeeded and info_output:
            lowered_info = info_output.lower()
            deeppmd_support_detected = "deepmd" in lowered_info or "dp" in lowered_info
            gpu_support_detected = "cuda" in lowered_info or "gpu" in lowered_info

        required_path_groups = self._required_path_groups(spec)
        missing_path_groups = self._missing_path_groups(required_path_groups)
        required_paths_present = not bool(missing_path_groups.all_paths())
        missing_required_paths = list(missing_path_groups.all_paths())
        for path_str in missing_required_paths:
            path = Path(path_str).expanduser()
            messages.append(f"Missing required path: {path}")

        if spec.working_directory is not None:
            workdir = Path(spec.working_directory).expanduser()
            if workdir.exists() and not workdir.is_dir():
                required_paths_present = False
                missing_required_paths.append(str(workdir))
                messages.append(f"Working directory is not a directory: {workdir}")

        environment_prerequisites = self._environment_prerequisites(spec)
        missing_prerequisites: list[str] = []
        if "deeppmd_support" in environment_prerequisites and deeppmd_support_detected is not True:
            missing_prerequisites.append("deeppmd_support")
            messages.append("DeePMD support is required for md + esolver_type=dp")

        evidence_refs = [
            f"abacus://environment/{spec.task_id}",
        ]
        if abacus_path:
            evidence_refs.append(f"abacus://binary/{Path(abacus_path).name}")
        if launcher_path:
            evidence_refs.append(f"abacus://launcher/{Path(launcher_path).name}")
        evidence_refs.extend(
            f"abacus://missing-path/{Path(path).name}" for path in missing_required_paths
        )
        evidence_refs.extend(
            f"abacus://missing-prerequisite/{item}" for item in dict.fromkeys(missing_prerequisites)
        )

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
            deeppmd_probe_supported=deeppmd_probe_supported,
            deeppmd_probe_succeeded=deeppmd_probe_succeeded,
            deeppmd_support_detected=deeppmd_support_detected,
            gpu_support_detected=gpu_support_detected,
            required_paths_present=required_paths_present,
            required_path_groups=required_path_groups,
            missing_path_groups=missing_path_groups,
            missing_required_paths=missing_required_paths,
            environment_prerequisites=environment_prerequisites,
            missing_prerequisites=list(dict.fromkeys(missing_prerequisites)),
            messages=messages,
            evidence_refs=list(dict.fromkeys(evidence_refs)),
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

    def _required_path_groups(self, spec: AbacusExperimentSpec) -> AbacusRuntimeAssets:
        restart_inputs: list[str] = []
        charge_density_path: str | None = None

        if isinstance(spec, AbacusNscfSpec):
            charge_density_path = spec.charge_density_path
            if spec.restart_file_path:
                restart_inputs.append(spec.restart_file_path)
        if isinstance(spec, AbacusRelaxSpec):
            restart_path = spec.relax_controls.get("restart_file_path")
            if isinstance(restart_path, str) and restart_path:
                restart_inputs.append(restart_path)

        return AbacusRuntimeAssets(
            explicit_required_paths=list(spec.required_paths),
            pseudo_files=list(spec.pseudo_files),
            orbital_files=list(spec.orbital_files),
            restart_inputs=restart_inputs,
            charge_density_path=charge_density_path,
            pot_file=spec.pot_file,
        )

    def _missing_path_groups(self, assets: AbacusRuntimeAssets) -> AbacusRuntimeAssets:
        def missing(paths: list[str]) -> list[str]:
            result: list[str] = []
            for path_str in paths:
                path = Path(path_str).expanduser()
                if not path.exists():
                    result.append(str(path))
            return result

        charge_density_path = assets.charge_density_path
        if charge_density_path is not None and Path(charge_density_path).expanduser().exists():
            charge_density_path = None

        pot_file = assets.pot_file
        if pot_file is not None and Path(pot_file).expanduser().exists():
            pot_file = None

        return AbacusRuntimeAssets(
            explicit_required_paths=missing(assets.explicit_required_paths),
            pseudo_files=missing(assets.pseudo_files),
            orbital_files=missing(assets.orbital_files),
            restart_inputs=missing(assets.restart_inputs),
            charge_density_path=charge_density_path,
            pot_file=pot_file,
        )

    def _environment_prerequisites(self, spec: AbacusExperimentSpec) -> list[str]:
        if isinstance(spec, AbacusMdSpec) and spec.esolver_type == "dp":
            return ["deeppmd_support"]
        return []
