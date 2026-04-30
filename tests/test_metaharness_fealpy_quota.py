from __future__ import annotations

from metaharness.sdk.execution import ResourceQuota
from metaharness_ext.fealpy.contracts import FealpyMeshSpec, FealpyProblemSpec
from metaharness_ext.fealpy.quota import (
    FealpyResourceQuotaProvider,
    estimate_dofs,
    estimate_memory_mb,
    estimate_taylor_hood_dofs,
)


def _spec(**overrides) -> FealpyProblemSpec:
    mesh_fields = {"meshtype", "nx", "ny", "nz", "h"}
    mesh_overrides = {k: overrides.pop(k) for k in list(overrides) if k in mesh_fields}
    mesh = FealpyMeshSpec(meshtype="tri", nx=8, ny=8).model_copy(update=mesh_overrides)
    return FealpyProblemSpec(task_id="quota-test", mesh=mesh, **overrides)  # type: ignore[arg-type]


class TestEstimateDofs:
    def test_2d_triangle_p1(self):
        dofs = estimate_dofs(_spec(meshtype="tri", nx=8, ny=8, fe_degree=1))
        assert dofs == (1 * 8 + 1) * (1 * 8 + 1)  # 9*9 = 81

    def test_2d_triangle_p2(self):
        dofs = estimate_dofs(_spec(meshtype="tri", nx=4, ny=4, fe_degree=2))
        assert dofs == (2 * 4 + 1) * (2 * 4 + 1)  # 9*9 = 81

    def test_2d_quad_p1(self):
        dofs = estimate_dofs(_spec(meshtype="quad", nx=10, ny=10, fe_degree=1))
        assert dofs == 11 * 11  # 121

    def test_3d_tet_p1(self):
        spec = _spec(meshtype="tet", nx=4, ny=4, nz=4, fe_degree=1)
        dofs = estimate_dofs(spec)
        assert dofs == 5 * 5 * 5  # 125

    def test_3d_hex_p2(self):
        spec = _spec(meshtype="hex", nx=4, ny=4, nz=4, fe_degree=2)
        dofs = estimate_dofs(spec)
        assert dofs == (2 * 4 + 1) ** 3  # 9^3 = 729

    def test_interval_1d(self):
        dofs = estimate_dofs(_spec(meshtype="interval", nx=16, fe_degree=1))
        assert dofs == 1 * 16 + 1  # 17

    def test_nedelec_2d(self):
        spec = _spec(meshtype="tri", nx=4, ny=4, fe_space_type="FirstNedelec")
        dofs = estimate_dofs(spec)
        base = 5 * 5  # 25
        assert dofs == base * 2

    def test_rt_2d(self):
        spec = _spec(meshtype="tri", nx=4, ny=4, fe_space_type="RaviartThomas")
        dofs = estimate_dofs(spec)
        base = 5 * 5
        assert dofs == base * 2

    def test_huzhang_2d(self):
        spec = _spec(meshtype="tri", nx=4, ny=4, fe_space_type="HuZhang")
        dofs = estimate_dofs(spec)
        base = 5 * 5
        assert dofs == base * 2


class TestEstimateTaylorHoodDofs:
    def test_2d(self):
        spec = _spec(meshtype="tri", nx=4, ny=4)
        dofs = estimate_taylor_hood_dofs(spec)
        velo = (2 * 4 + 1) * (2 * 4 + 1) * 2  # 9*9*2 = 162
        pres = (1 * 4 + 1) * (1 * 4 + 1)  # 5*5 = 25
        assert dofs == velo + pres  # 187

    def test_3d(self):
        spec = _spec(meshtype="tet", nx=4, ny=4, nz=4)
        dofs = estimate_taylor_hood_dofs(spec)
        velo = (9) * (9) * (9) * 3  # 2187
        pres = 5 * 5 * 5  # 125
        assert dofs == velo + pres


class TestEstimateMemoryMb:
    def test_small_mesh(self):
        mb = estimate_memory_mb(1000)
        assert 0.03 < mb < 0.05  # ~0.038 MB

    def test_large_mesh(self):
        mb = estimate_memory_mb(2_000_000)
        assert 70 < mb < 80  # ~76.3 MB


class TestQuotaProvider:
    def test_small_2d_not_exhausted(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec(nx=8, ny=8))
        assert not quota.exhausted
        assert quota.resource_type == "fealpy_mesh"
        assert quota.remaining > 0

    def test_very_large_3d_exhausted(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec(meshtype="tet", nx=200, ny=200, nz=200, fe_degree=2))
        assert quota.exhausted
        assert quota.remaining == 0

    def test_near_limit_but_not_exhausted(self):
        provider = FealpyResourceQuotaProvider()
        spec = _spec(meshtype="tet", nx=100, ny=100, nz=20, fe_degree=1)
        quota = provider.estimate_quota(spec)
        assert not quota.exhausted

    def test_stokes_pde_family_uses_taylor_hood(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec(pde_family="stokes", nx=4, ny=4))
        dofs = quota.metadata["estimated_dofs"]
        assert dofs == estimate_taylor_hood_dofs(_spec(pde_family="stokes", nx=4, ny=4))

    def test_navier_stokes_uses_taylor_hood(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec(pde_family="navier_stokes", nx=4, ny=4))
        dofs = quota.metadata["estimated_dofs"]
        assert dofs == estimate_taylor_hood_dofs(_spec(pde_family="navier_stokes", nx=4, ny=4))

    def test_metadata_contains_key_fields(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec())
        meta = quota.metadata
        assert "estimated_dofs" in meta
        assert "estimated_memory_mb" in meta
        assert "pde_family" in meta
        assert "fe_degree" in meta
        assert "meshtype" in meta
        assert "nx" in meta

    def test_returns_resource_quota_model(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec())
        assert isinstance(quota, ResourceQuota)
        assert quota.quota_id is not None
        assert quota.limit is not None
        assert quota.used is not None
        assert quota.remaining is not None
        assert quota.unit == "dof"

    def test_custom_dof_limit(self):
        provider = FealpyResourceQuotaProvider()
        spec = _spec(nx=100, ny=100, fe_degree=1)
        quota_default = provider.estimate_quota(spec)
        quota_custom = provider.estimate_quota(spec, dof_limit=5000)
        assert not quota_default.exhausted  # 101*101 = 10201 < 2M
        assert quota_custom.exhausted  # 10201 > 5000

    def test_memory_exhaustion(self):
        provider = FealpyResourceQuotaProvider()
        quota = provider.estimate_quota(_spec(nx=100, ny=100, fe_degree=1), memory_mb_limit=0.01)
        assert quota.exhausted
