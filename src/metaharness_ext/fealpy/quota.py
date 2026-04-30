from __future__ import annotations

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.execution import ResourceQuota
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.fealpy.capabilities import CAP_FEALPY_QUOTA_PROVIDE
from metaharness_ext.fealpy.contracts import FealpyProblemSpec
from metaharness_ext.fealpy.slots import FEALPY_QUOTA_PROVIDER_SLOT

_DEFAULT_DOF_LIMIT = 2_000_000
_DEFAULT_MEMORY_MB_LIMIT = 2048.0


def estimate_dofs(spec: FealpyProblemSpec) -> int:
    """Estimate degrees of freedom from mesh and FE parameters.

    Returns an upper-bound approximation without constructing the actual mesh.
    """
    nx = spec.mesh.nx
    ny = spec.mesh.ny or nx
    nz = spec.mesh.nz
    p = spec.fe_degree
    meshtype = spec.mesh.meshtype
    space_type = spec.fe_space_type

    if meshtype in ("interval",):
        nodes_1d = p * nx + 1
        return nodes_1d

    if nz is not None and meshtype in ("tet", "hex", "uniform"):
        nodes_1d = p * nx + 1
        nodes_2d = p * ny + 1
        nodes_3d = p * nz + 1
        base_dofs = nodes_1d * nodes_2d * nodes_3d
    else:
        nodes_x = p * nx + 1
        nodes_y = p * ny + 1
        base_dofs = nodes_x * nodes_y

    if space_type == "Lagrange":
        return base_dofs
    if space_type == "FirstNedelec":
        if nz is not None:
            return base_dofs * 3  # vector edge elements in 3D
        return base_dofs * 2  # 2D edge elements
    if space_type == "RaviartThomas":
        if nz is not None:
            return base_dofs * 3
        return base_dofs * 2
    if space_type == "HuZhang":
        return base_dofs * (3 if nz is not None else 2)
    return base_dofs


def estimate_taylor_hood_dofs(spec: FealpyProblemSpec) -> int:
    """Estimate DOFs for Taylor-Hood (P2/P1) mixed spaces."""
    nx = spec.mesh.nx
    ny = spec.mesh.ny or nx
    nz = spec.mesh.nz
    p_velo = 2  # P2 velocity
    p_pres = 1  # P1 pressure
    if nz is not None:
        velo_dofs = (p_velo * nx + 1) * (p_velo * ny + 1) * (p_velo * nz + 1) * (3 if nz else 2)
        pres_dofs = (p_pres * nx + 1) * (p_pres * ny + 1) * (p_pres * nz + 1)
    else:
        velo_dofs = (p_velo * nx + 1) * (p_velo * ny + 1) * 2
        pres_dofs = (p_pres * nx + 1) * (p_pres * ny + 1)
    return velo_dofs + pres_dofs


def estimate_memory_mb(dofs: int) -> float:
    """Rough memory estimate: 5 matrices of 8-byte floats."""
    return dofs * 8.0 * 5.0 / (1024.0 * 1024.0)


class FealpyResourceQuotaProvider(HarnessComponent):
    """Estimates resource usage for fealpy PDE solves and produces ResourceQuota."""

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(FEALPY_QUOTA_PROVIDER_SLOT)
        api.declare_input("spec", "FealpyProblemSpec")
        api.declare_output("quota", "ResourceQuota", mode="sync")
        api.provide_capability(CAP_FEALPY_QUOTA_PROVIDE)

    def estimate_quota(
        self,
        spec: FealpyProblemSpec,
        *,
        dof_limit: int = _DEFAULT_DOF_LIMIT,
        memory_mb_limit: float = _DEFAULT_MEMORY_MB_LIMIT,
    ) -> ResourceQuota:
        pde_family = spec.pde_family
        if pde_family in ("stokes", "navier_stokes"):
            dofs = estimate_taylor_hood_dofs(spec)
        else:
            dofs = estimate_dofs(spec)

        memory_mb = estimate_memory_mb(dofs)
        exhausted = dofs > dof_limit or memory_mb > memory_mb_limit

        return ResourceQuota(
            quota_id=f"fealpy-{spec.task_id}",
            resource_type="fealpy_mesh",
            provider="fealpy_resource_quota_provider",
            limit=dof_limit,
            used=dofs,
            remaining=max(0, dof_limit - dofs),
            unit="dof",
            scope=spec.task_id,
            exhausted=exhausted,
            metadata={
                "estimated_dofs": dofs,
                "estimated_memory_mb": round(memory_mb, 2),
                "memory_mb_limit": memory_mb_limit,
                "dof_limit": dof_limit,
                "pde_family": spec.pde_family,
                "fe_degree": spec.fe_degree,
                "fe_space_type": spec.fe_space_type,
                "meshtype": spec.mesh.meshtype,
                "nx": spec.mesh.nx,
                "ny": spec.mesh.ny,
                "nz": spec.mesh.nz,
            },
        )
