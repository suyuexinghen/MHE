from __future__ import annotations

import os
import shutil
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.capabilities import CAP_LEAN_PROBE_ENVIRONMENT
from metaharness_ext.lean.contracts import LeanEnvironmentReport, LeanProjectSpec, LeanTaskSpec
from metaharness_ext.lean.slots import LEAN_ENVIRONMENT_SLOT


def find_lean_project_root(target: str | Path) -> Path | None:
    path = Path(target).expanduser()
    current = path.parent if path.suffix else path
    for candidate in [current, *current.parents]:
        has_toolchain = (candidate / "lean-toolchain").exists()
        has_lakefile = (candidate / "lakefile.lean").exists() or (
            candidate / "lakefile.toml"
        ).exists()
        if has_toolchain and has_lakefile:
            return candidate
    return None


def find_lakefile(project_root: Path) -> Path | None:
    for filename in ["lakefile.lean", "lakefile.toml"]:
        path = project_root / filename
        if path.exists():
            return path
    return None


class LeanEnvironmentComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_ENVIRONMENT_SLOT)
        api.declare_input("task", "LeanTaskSpec")
        api.declare_output("environment", "LeanEnvironmentReport", mode="sync")
        api.provide_capability(CAP_LEAN_PROBE_ENVIRONMENT)

    def probe(self, task: LeanTaskSpec) -> LeanEnvironmentReport:
        if task.execution_policy.mode == "dry_run":
            return self._dry_run_report(task)

        if os.environ.get("MHE_RUN_REAL_LEAN") != "1":
            return LeanEnvironmentReport(blocks_promotion=True)

        project_root = (
            Path(task.project.project_root)
            if task.project
            else find_lean_project_root(task.target_file)
        )
        lean_available = shutil.which("lean") is not None
        lake_available = shutil.which("lake") is not None
        lakefile = find_lakefile(project_root) if project_root else None
        toolchain = self._read_toolchain(project_root) if project_root else None

        return LeanEnvironmentReport(
            lean_available=lean_available,
            lake_available=lake_available,
            project_root_found=project_root is not None,
            build_status="unknown",
            toolchain_version=toolchain,
            lakefile_path=str(lakefile) if lakefile else None,
            optional_tools={
                "loogle": shutil.which("loogle") is not None,
                "leanexplore": shutil.which("leanexplore") is not None,
                "leandex": shutil.which("leandex") is not None,
            },
            blocks_promotion=not (lean_available and lake_available and project_root is not None),
        )

    def _dry_run_report(self, task: LeanTaskSpec) -> LeanEnvironmentReport:
        project = task.project or self._discover_project_spec(task.target_file)
        return LeanEnvironmentReport(
            lean_available=True,
            lake_available=True,
            project_root_found=project is not None,
            build_status=project.build_status if project else "mock",
            toolchain_version=project.toolchain_version if project else "mock",
            lakefile_path=project.lakefile_path if project else None,
            optional_tools={"loogle": False, "leanexplore": False, "leandex": False},
            blocks_promotion=False,
        )

    def _discover_project_spec(self, target_file: str) -> LeanProjectSpec | None:
        root = find_lean_project_root(target_file)
        if root is None:
            return None
        lakefile = find_lakefile(root)
        return LeanProjectSpec(
            project_root=str(root),
            toolchain_version=self._read_toolchain(root),
            lakefile_path=str(lakefile) if lakefile else None,
        )

    def _read_toolchain(self, project_root: Path | None) -> str | None:
        if project_root is None:
            return None
        path = project_root / "lean-toolchain"
        if not path.exists():
            return None
        return path.read_text().strip() or None
