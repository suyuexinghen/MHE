from __future__ import annotations

from metaharness_ext.pycfd.benchmark_cases import get_pycfd_cases, pycfd_case_catalog


class TestPyCFDBenchmarkCases:
    def test_catalog_has_five_cases(self):
        catalog = pycfd_case_catalog()
        assert len(catalog) == 5

    def test_all_known_case_ids(self):
        catalog = pycfd_case_catalog()
        expected = {
            "vortex-2d",
            "airfoil-2d",
            "cylinder-2d",
            "mms-2d",
            "shock-diffraction-2d",
        }
        assert set(catalog.keys()) == expected

    def test_vortex_case_spec(self):
        spec = pycfd_case_catalog()["vortex-2d"]
        assert spec.case_type == "vortex"
        assert spec.mesh.nx == 64
        assert spec.mesh.ny == 64
        assert spec.mesh.mesh_type == "tri"
        assert spec.flow.M_inf == 0.3

    def test_airfoil_case_spec(self):
        spec = pycfd_case_catalog()["airfoil-2d"]
        assert spec.case_type == "airfoil"
        assert spec.flow.M_inf == 0.80
        assert spec.flow.aoa == 1.25
        assert spec.solver.use_limiter is True

    def test_shock_case_spec(self):
        spec = pycfd_case_catalog()["shock-diffraction-2d"]
        assert spec.case_type == "shock_diffraction"
        assert spec.flow.M_inf == 5.09
        assert spec.solver.CFL == 0.5

    def test_filter_by_case_type(self):
        cases = get_pycfd_cases(case_types=["vortex", "mms"])
        assert len(cases) == 2
        assert all(v.case_type in ("vortex", "mms") for v in cases.values())

    def test_filter_empty_returns_all(self):
        cases = get_pycfd_cases()
        assert len(cases) == 5
