from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from metaharness_ext.boutpp.contracts import BoutPPEnvironmentReport, BoutPPProblemSpec


class BoutPPEnvironmentProbeComponent:
    def __init__(self, boutpp_root: str | None = None, executable_root: str | None = None):
        self._boutpp_root = boutpp_root
        self._executable_root = executable_root

    def _resolve_root(self) -> str | None:
        for candidate in (self._boutpp_root, self._executable_root, os.environ.get("BOUTPP_ROOT"), os.environ.get("BOUT_ROOT")):
            if candidate and Path(candidate).exists():
                return str(Path(candidate).resolve())
        return None

    def _resolve_launcher(self) -> str | None:
        for name in ("mpiexec", "mpirun"):
            launcher = shutil.which(name)
            if launcher:
                return launcher
        return None

    def _resolve_executable(self, root: str | None, executable: str) -> str | None:
        if not executable.strip():
            return None
        if Path(executable).is_absolute() and Path(executable).exists():
            return str(Path(executable).resolve())
        search_roots = [Path.cwd()]
        if root:
            root_path = Path(root)
            search_roots.extend(
                [
                    root_path,
                    root_path / "build",
                    root_path / "build" / "examples",
                    root_path / "examples",
                ]
            )
        if self._executable_root:
            search_roots.extend([Path(self._executable_root), Path(self._executable_root) / "examples"])
        for base in search_roots:
            candidate = base / executable
            if candidate.exists():
                return str(candidate.resolve())
        return shutil.which(executable)

    def _resolve_netcdf_config(self) -> str | None:
        for name in ("ncxx4-config", "nc-config"):
            config = shutil.which(name)
            if config:
                return config
        return None

    def _record_feature_hints(self, report: BoutPPEnvironmentReport, root: str | None) -> None:
        if root is None:
            return
        root_path = Path(root)
        candidates = [
            root_path / "CMakeCache.txt",
            root_path / "build" / "CMakeCache.txt",
            root_path / "build" / "include" / "bout" / "boutconfig.hxx",
        ]
        text = "\n".join(path.read_text(errors="ignore") for path in candidates if path.exists())
        feature_names = {
            "PETSc": "petsc",
            "SUNDIALS": "sundials",
            "OpenMP": "openmp",
            "GPU/RAJA": "raja",
            "3D metrics": "3d",
        }
        hints = [label for label, token in feature_names.items() if token in text.lower()]
        if hints:
            report.messages.append(f"BOUT++ feature hints: {', '.join(hints)}")

    def probe(self, spec: BoutPPProblemSpec | None = None, task_id: str = "boutpp_env_probe") -> BoutPPEnvironmentReport:
        report = BoutPPEnvironmentReport(task_id=task_id)
        report.python_version = sys.version.split()[0]
        root = self._resolve_root()
        if root:
            report.boutpp_root = root
        launcher = self._resolve_launcher()
        if launcher:
            report.mpi_launcher = launcher
        cmake = shutil.which("cmake")
        if cmake:
            report.cmake_path = cmake
        nc_config = self._resolve_netcdf_config()
        if nc_config:
            report.nc_config_path = nc_config
        bout_config = shutil.which("bout-config")
        if bout_config:
            report.bout_config_path = bout_config
        readers = {}
        for module in ("netCDF4", "xarray", "xbout", "boutdata", "boutpp"):
            try:
                __import__(module)
                readers[module] = True
            except Exception:
                readers[module] = False
        report.optional_python_readers = readers
        self._record_feature_hints(report, root)
        if spec is not None:
            report.executable_path = self._resolve_executable(root, spec.executable)
            if spec.source_case_dir:
                source_dir = Path(spec.source_case_dir)
                if source_dir.exists():
                    report.boutpp_build_root = str(source_dir.resolve())
        if root is None:
            report.missing_prerequisites.append("BOUTPP_ROOT or BOUT_ROOT")
        if launcher is None:
            report.missing_prerequisites.append("mpi launcher")
        if spec is not None and not report.executable_path:
            report.missing_prerequisites.append(f"executable '{spec.executable}'")
        if not report.cmake_path:
            report.warnings.append("cmake not found in PATH")
        if not report.nc_config_path:
            report.warnings.append("ncxx4-config or nc-config not found in PATH")
        if not report.bout_config_path:
            report.warnings.append("bout-config not found in PATH")
        if not readers.get("netCDF4", False):
            report.warnings.append("netCDF4 not available")
        report.available = not report.missing_prerequisites
        report.status = "ready" if report.available else "partial"
        report.blocks_promotion = bool(report.missing_prerequisites)
        return report
