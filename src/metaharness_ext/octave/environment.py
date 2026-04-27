from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.octave.capabilities import CAP_OCTAVE_ENV_PROBE
from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveExperimentSpec,
    OctavePackageFact,
)
from metaharness_ext.octave.slots import OCTAVE_ENVIRONMENT_SLOT


class OctaveEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OCTAVE_ENVIRONMENT_SLOT)
        api.declare_input("task", "OctaveExperimentSpec")
        api.declare_output("environment", "OctaveEnvironmentReport", mode="sync")
        api.provide_capability(CAP_OCTAVE_ENV_PROBE)

    def probe(self, spec: OctaveExperimentSpec) -> OctaveEnvironmentReport:
        warnings: list[str] = []
        missing_prerequisites: list[str] = []
        binary_path = shutil.which(spec.executable.binary_name)
        version: str | None = None
        package_versions: dict[str, str | None] = {}

        if binary_path is None:
            missing_prerequisites.append(f"Octave binary not found: {spec.executable.binary_name}")
        else:
            version = self._probe_version(binary_path, warnings)
            package_versions = self._probe_packages(binary_path, warnings)

        package_facts = [
            OctavePackageFact(
                name=package.name,
                version=package_versions.get(package.name),
                available=package.name in package_versions,
                required=package.required,
            )
            for package in spec.packages
        ]
        missing_packages = [
            fact.name for fact in package_facts if fact.required and not fact.available
        ]
        missing_prerequisites.extend(
            f"Required Octave package not installed: {package_name}"
            for package_name in missing_packages
        )
        workspace_writable = self._workspace_writable(spec)
        if not workspace_writable:
            missing_prerequisites.append("Octave workspace is not writable")

        available = not missing_prerequisites
        return OctaveEnvironmentReport(
            task_id=spec.task_id,
            available=available,
            status="available" if available else "prerequisite_missing",
            binary_path=binary_path,
            version=version,
            minimum_version=spec.executable.minimum_version,
            workspace_writable=workspace_writable,
            packages=package_facts,
            messages=[],
            warnings=warnings,
            missing_prerequisites=missing_prerequisites,
            missing_packages=missing_packages,
            prerequisite_errors=list(missing_prerequisites),
            evidence_refs=[f"octave://environment/{spec.task_id}"],
            blocks_promotion=not available,
        )

    def _probe_version(self, binary_path: str, warnings: list[str]) -> str | None:
        try:
            result = subprocess.run(
                [binary_path, "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            warnings.append(f"Unable to probe Octave version: {error}")
            return None
        first_line = (result.stdout or result.stderr).splitlines()[0:1]
        return first_line[0] if first_line else None

    def _probe_packages(self, binary_path: str, warnings: list[str]) -> dict[str, str | None]:
        try:
            result = subprocess.run(
                [binary_path, "--no-gui", "--quiet", "--no-init-file", "--eval", "pkg list"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            warnings.append(f"Unable to probe Octave packages: {error}")
            return {}
        if result.returncode != 0:
            warnings.append("Octave package probe returned non-zero status")
        return self._parse_pkg_list(result.stdout)

    def _parse_pkg_list(self, output: str) -> dict[str, str | None]:
        packages: dict[str, str | None] = {}
        for line in output.splitlines():
            match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*\|\s*([^|\s]+)", line)
            if match:
                packages[match.group(1)] = match.group(2)
        return packages

    def _workspace_writable(self, spec: OctaveExperimentSpec) -> bool:
        workspace = spec.workspace.working_directory if spec.workspace is not None else None
        runtime = getattr(self, "_runtime", None)
        if workspace:
            probe_dir = Path(workspace).expanduser()
        elif runtime is not None and runtime.storage_path is not None:
            probe_dir = runtime.storage_path / ".runs" / "octave" / spec.task_id / "probe"
        else:
            probe_dir = Path(tempfile.gettempdir()) / "metaharness-octave" / spec.task_id / "probe"
        try:
            probe_dir.mkdir(parents=True, exist_ok=True)
            probe_file = probe_dir / ".mhe-write-probe"
            probe_file.write_text("ok")
            probe_file.unlink(missing_ok=True)
        except OSError:
            return False
        return True
