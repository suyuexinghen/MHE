from __future__ import annotations

import os
import sys

from metaharness_ext.pycfd.contracts import PyCFDEnvironmentReport


class PyCFDEnvironmentProbeComponent:
    """Probes the runtime for PyCFD availability.

    PyCFD is not a pip package — it lives at a filesystem path. This probe
    verifies the source directory exists, checks numpy availability, and
    identifies which case types are supported.
    """

    def __init__(self, pycfd_src_path: str | None = None):
        self._pycfd_src_path = pycfd_src_path

    def _resolve_pycfd_path(self) -> str | None:
        if self._pycfd_src_path and os.path.isdir(self._pycfd_src_path):
            return os.path.abspath(self._pycfd_src_path)
        env_path = os.environ.get("PYCFD_SRC_PATH", "")
        if env_path and os.path.isdir(env_path):
            return os.path.abspath(env_path)
        return None

    def probe(self, task_id: str = "pycfd_env_probe") -> PyCFDEnvironmentReport:
        report = PyCFDEnvironmentReport(task_id=task_id)
        report.python_version = sys.version.split()[0]

        src_path = self._resolve_pycfd_path()
        if not src_path:
            report.available = False
            report.status = "pycfd_source_not_found"
            report.missing_prerequisites.append(
                "PyCFD source directory not found. Set PYCFD_SRC_PATH or pass pycfd_src_path."
            )
            report.blocks_promotion = True
            return report

        report.pycfd_src_path = src_path

        # Check numpy
        try:
            import numpy

            report.numpy_version = numpy.__version__
        except ImportError:
            report.missing_prerequisites.append("numpy")
            report.blocks_promotion = True

        # Check Solvers.py exists
        solvers_path = os.path.join(src_path, "Solvers.py")
        if not os.path.isfile(solvers_path):
            report.available = False
            report.status = "solvers_py_not_found"
            report.missing_prerequisites.append(f"Solvers.py not found at {solvers_path}")
            report.blocks_promotion = True
            return report

        # Probe for importability
        try:
            _saved = sys.path.copy()
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            try:
                import Solvers  # noqa: F401
            finally:
                sys.path[:] = _saved
        except Exception as e:
            report.missing_prerequisites.append(f"Failed to import Solvers: {e}")
            report.blocks_promotion = True

        # Determine available case types based on mesh file existence
        report.available_case_types = self._probe_case_types(src_path)

        if report.missing_prerequisites:
            report.available = False
            report.status = "partial"
        else:
            report.available = True
            report.status = "ready"

        return report

    def _probe_case_types(self, src_path: str) -> list[str]:
        """Check which case types have mesh files available."""
        cases_dir = os.path.join(os.path.dirname(src_path), "cases")
        if not os.path.isdir(cases_dir):
            # Cases not available — only structured generated meshes work
            return ["vortex", "shock_diffraction", "mms"]

        available: list[str] = []
        case_dirs = {
            "vortex": "case_unsteady_vortex",
            "airfoil": "case_steady_airfoil",
            "cylinder": "case_steady_cylinder",
            "mms": "case_verification_te",
            "shock_diffraction": "case_shock_diffraction",
        }
        for case_name, dir_name in case_dirs.items():
            case_path = os.path.join(cases_dir, dir_name)
            if os.path.isdir(case_path):
                available.append(case_name)
        return available
