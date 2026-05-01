from __future__ import annotations

from metaharness_ext.pycfd.benchmark_cases import pycfd_case_catalog


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
        assert spec.case_id == "vortex-2d"
        assert spec.problem_definition["case_type"] == "vortex"
        assert spec.problem_definition["mesh"]["nx"] == 64
        assert spec.problem_definition["mesh"]["ny"] == 64
        assert spec.problem_definition["mesh"]["mesh_type"] == "tri"
        assert spec.problem_definition["flow"]["M_inf"] == 0.3

    def test_airfoil_case_spec(self):
        spec = pycfd_case_catalog()["airfoil-2d"]
        assert spec.case_id == "airfoil-2d"
        assert spec.problem_definition["case_type"] == "airfoil"
        assert spec.problem_definition["flow"]["M_inf"] == 0.80
        assert spec.problem_definition["flow"]["aoa"] == 1.25
        assert spec.problem_definition["solver"]["use_limiter"] is True

    def test_shock_case_spec(self):
        spec = pycfd_case_catalog()["shock-diffraction-2d"]
        assert spec.case_id == "shock-diffraction-2d"
        assert spec.problem_definition["case_type"] == "shock_diffraction"
        assert spec.problem_definition["flow"]["M_inf"] == 5.09
        assert spec.problem_definition["solver"]["CFL"] == 0.5

    def test_filter_by_case_id(self):
        cases = pycfd_case_catalog(case_ids=["vortex-2d", "mms-2d"])
        assert len(cases) == 2
        assert set(cases.keys()) == {"vortex-2d", "mms-2d"}

    def test_filter_empty_returns_all(self):
        cases = pycfd_case_catalog()
        assert len(cases) == 5
