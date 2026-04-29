from __future__ import annotations

import sys

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.fealpy.capabilities import CAP_FEALPY_ENV_PROBE
from metaharness_ext.fealpy.contracts import FealpyEnvironmentReport, FealpyProblemSpec
from metaharness_ext.fealpy.slots import FEALPY_ENVIRONMENT_SLOT

_FEALPY_PDE_FAMILIES = [
    "poisson",
    "stokes",
    "navier_stokes",
    "parabolic",
    "hyperbolic",
    "helmholtz",
    "curlcurl",
    "diffusion",
    "diffusion_convection",
    "diffusion_convection_reaction",
    "diffusion_reaction",
    "darcyforchheimer",
    "linear_elasticity",
    "interface_poisson",
    "surface_poisson",
    "wave",
    "allen_cahn",
    "polyharmonic",
    "quasilinear_elliptic",
    "optimal_control",
    "ion_flow",
    "dld_microfluidic_chip",
    "mgtensor_possion",
]

_BACKEND_IMPORT_PATHS = {
    "numpy": "numpy",
    "pytorch": "torch",
    "jax": "jax",
}


class FealpyEnvironmentProbeComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(FEALPY_ENVIRONMENT_SLOT)
        api.declare_input("task", "FealpyProblemSpec")
        api.declare_output("environment", "FealpyEnvironmentReport", mode="sync")
        api.provide_capability(CAP_FEALPY_ENV_PROBE)

    def probe(self, spec: FealpyProblemSpec) -> FealpyEnvironmentReport:
        warnings: list[str] = []
        missing: list[str] = []

        fealpy_version = self._probe_fealpy_version(warnings, missing)
        backend_status = self._probe_backends(warnings)
        available_backends = [k for k, v in backend_status.items() if v]
        python_version = sys.version.split()[0]

        if spec.backend not in available_backends:
            missing.append(f"Requested backend '{spec.backend}' is not available")

        available = not missing

        return FealpyEnvironmentReport(
            task_id=spec.task_id,
            available=available,
            status="available" if available else "prerequisite_missing",
            fealpy_version=fealpy_version,
            python_version=python_version,
            available_backends=available_backends,
            available_pde_families=list(_FEALPY_PDE_FAMILIES),
            backend_status=backend_status,
            missing_prerequisites=missing,
            messages=[],
            warnings=warnings,
            evidence_refs=[f"fealpy://environment/{spec.task_id}"],
            blocks_promotion=not available,
        )

    def _probe_fealpy_version(self, warnings: list[str], missing: list[str]) -> str | None:
        try:
            import fealpy  # noqa: PLC0415
        except ImportError:
            missing.append("fealpy package is not installed")
            return None
        version = getattr(fealpy, "__version__", None)
        if version is None:
            warnings.append("fealpy does not expose __version__")
        return version

    def _probe_backends(self, warnings: list[str]) -> dict[str, bool]:
        status: dict[str, bool] = {}
        for name, import_path in _BACKEND_IMPORT_PATHS.items():
            try:
                __import__(import_path)
                status[name] = True
            except ImportError:
                status[name] = False
                if name == "numpy":
                    warnings.append(
                        "numpy is not available; fealpy requires numpy as minimum backend"
                    )
        return status

    @staticmethod
    def pde_families() -> list[str]:
        return list(_FEALPY_PDE_FAMILIES)
