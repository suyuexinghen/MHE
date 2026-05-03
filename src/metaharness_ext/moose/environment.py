from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.moose.capabilities import CAP_MOOSE_ENV_PROBE
from metaharness_ext.moose.contracts import MooseEnvironmentReport, MooseProblemSpec
from metaharness_ext.moose.slots import MOOSE_ENVIRONMENT_SLOT


class MooseEnvironmentProbeComponent(HarnessComponent):
    def __init__(self, source_root: str | None = None):
        self._source_root = source_root

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(MOOSE_ENVIRONMENT_SLOT)
        api.declare_input("task", "MooseProblemSpec")
        api.declare_output("environment", "MooseEnvironmentReport", mode="sync")
        api.provide_capability(CAP_MOOSE_ENV_PROBE)

    def probe(self, spec: MooseProblemSpec) -> MooseEnvironmentReport:
        warnings: list[str] = []
        missing_prerequisites: list[str] = []
        binary_path = shutil.which(spec.executable.binary_name)
        version: str | None = None
        source_root = self._resolve_source_root(spec)
        source_tree_detected = source_root is not None

        if binary_path is None:
            missing_prerequisites.append(f"MOOSE binary not found: {spec.executable.binary_name}")
        else:
            version = self._probe_version(binary_path, warnings)

        workspace_writable = self._workspace_writable(spec)
        if not workspace_writable:
            missing_prerequisites.append("MOOSE workspace is not writable")

        available = not missing_prerequisites
        return MooseEnvironmentReport(
            task_id=spec.task_id,
            available=available,
            status="available" if available else "prerequisite_missing",
            binary_path=binary_path,
            version=version,
            minimum_version=spec.executable.minimum_version,
            source_root=source_root,
            source_tree_detected=source_tree_detected,
            workspace_writable=workspace_writable,
            missing_prerequisites=missing_prerequisites,
            prerequisite_errors=list(missing_prerequisites),
            messages=[],
            warnings=warnings,
            evidence_refs=[f"moose://environment/{spec.task_id}"],
            blocks_promotion=not available,
        )

    def _resolve_source_root(self, spec: MooseProblemSpec) -> str | None:
        candidate = spec.executable.source_root or self._source_root
        if not candidate:
            return None
        path = Path(candidate).expanduser()
        if path.exists():
            return str(path)
        return None

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
            warnings.append(f"Unable to probe MOOSE version: {error}")
            return None
        first_line = (result.stdout or result.stderr).splitlines()[0:1]
        return first_line[0] if first_line else None

    def _workspace_writable(self, spec: MooseProblemSpec) -> bool:
        workspace = spec.workspace.working_directory if spec.workspace is not None else None
        runtime = getattr(self, "_runtime", None)
        if workspace:
            probe_dir = Path(workspace).expanduser()
        elif runtime is not None and runtime.storage_path is not None:
            probe_dir = runtime.storage_path / ".runs" / "moose" / spec.task_id / "probe"
        else:
            probe_dir = Path(tempfile.gettempdir()) / "metaharness-moose" / spec.task_id / "probe"
        try:
            probe_dir.mkdir(parents=True, exist_ok=True)
            probe_file = probe_dir / ".mhe-write-probe"
            probe_file.write_text("ok")
            probe_file.unlink(missing_ok=True)
        except OSError:
            return False
        return True
