from __future__ import annotations

import pytest
from pydantic import ValidationError

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec
from metaharness_ext.fealpy.benchmark_cases import fealpy_case_catalog, get_fealpy_cases


class TestFealpyCaseCatalog:
    def test_catalog_returns_dict(self):
        catalog = fealpy_case_catalog()
        assert isinstance(catalog, dict)
        assert len(catalog) >= 8

    def test_all_values_are_benchmark_case_specs(self):
        catalog = fealpy_case_catalog()
        for case_id, case in catalog.items():
            assert isinstance(case, BenchmarkCaseSpec), f"{case_id} is not BenchmarkCaseSpec"

    def test_case_ids_match_keys(self):
        catalog = fealpy_case_catalog()
        for case_id, case in catalog.items():
            assert case.case_id == case_id

    def test_all_suites_are_fealpy_pde(self):
        catalog = fealpy_case_catalog()
        for case in catalog.values():
            assert case.suite == "fealpy-pde"

    def test_all_have_task_family_fealpy_pde(self):
        catalog = fealpy_case_catalog()
        for case in catalog.values():
            assert case.task_family == "fealpy_pde"

    def test_all_have_expected_metrics(self):
        catalog = fealpy_case_catalog()
        for case in catalog.values():
            assert len(case.expected_metrics) >= 1

    @pytest.mark.parametrize(
        "case_id",
        [
            "poisson-2d-numpy",
            "poisson-2d-pytorch",
            "poisson-2d-jax",
            "poisson-3d-numpy",
            "stokes-2d-numpy",
            "darcy-2d-numpy",
            "linear_elasticity-2d-numpy",
            "curlcurl-2d-numpy",
        ],
    )
    def test_known_case_exists(self, case_id):
        catalog = fealpy_case_catalog()
        assert case_id in catalog

    @pytest.mark.parametrize(
        "case_id,expected_backend",
        [
            ("poisson-2d-numpy", "numpy"),
            ("poisson-2d-pytorch", "pytorch"),
            ("poisson-2d-jax", "jax"),
            ("poisson-3d-numpy", "numpy"),
        ],
    )
    def test_poisson_cases_have_correct_backend(self, case_id, expected_backend):
        catalog = fealpy_case_catalog()
        case = catalog[case_id]
        assert case.problem_definition["backend"] == expected_backend

    def test_poisson_3d_has_nz_field(self):
        catalog = fealpy_case_catalog()
        case = catalog["poisson-3d-numpy"]
        assert case.problem_definition.get("nz") == 8

    def test_capability_gated_cases_marked(self):
        catalog = fealpy_case_catalog()
        gated = [
            "poisson-2d-pytorch",
            "poisson-2d-jax",
            "poisson-3d-numpy",
            "stokes-2d-numpy",
            "darcy-2d-numpy",
            "linear_elasticity-2d-numpy",
            "curlcurl-2d-numpy",
        ]
        for case_id in gated:
            assert catalog[case_id].capability_gated is True, f"{case_id} should be gated"

    def test_numpy_cases_not_capability_gated(self):
        catalog = fealpy_case_catalog()
        # Only poisson-2d-numpy is ungated — other PDE families are blocked by
        # compiler-template vs installed-fealpy API mismatches.
        for case_id in [
            "poisson-2d-numpy",
        ]:
            assert not catalog[case_id].capability_gated, f"{case_id} should not be gated"

    def test_blocked_pde_families_are_capability_gated(self):
        catalog = fealpy_case_catalog()
        for case_id in [
            "stokes-2d-numpy",
            "darcy-2d-numpy",
            "linear_elasticity-2d-numpy",
            "curlcurl-2d-numpy",
        ]:
            assert catalog[case_id].capability_gated, f"{case_id} should be gated"

    def test_stokes_case_uses_fe_degree_2(self):
        catalog = fealpy_case_catalog()
        assert catalog["stokes-2d-numpy"].problem_definition["fe_degree"] == 2

    def test_darcy_case_uses_fe_degree_0(self):
        catalog = fealpy_case_catalog()
        assert catalog["darcy-2d-numpy"].problem_definition["fe_degree"] == 0

    def test_case_id_rejects_slashes(self):
        with pytest.raises(ValidationError):
            BenchmarkCaseSpec(
                case_id="bad/case",
                suite="fealpy-pde",
                task_family="fealpy_pde",
                description="test",
                source_reference={},
            )

    def test_case_id_rejects_empty(self):
        with pytest.raises(ValidationError):
            BenchmarkCaseSpec(
                case_id="  ",
                suite="fealpy-pde",
                task_family="fealpy_pde",
                description="test",
                source_reference={},
            )


class TestGetFealpyCases:
    def test_no_filter_returns_all(self):
        cases = get_fealpy_cases()
        assert len(cases) >= 8

    def test_filter_returns_subset(self):
        cases = get_fealpy_cases(["poisson-2d-numpy"])
        assert len(cases) == 1
        assert cases[0].case_id == "poisson-2d-numpy"

    def test_filter_returns_ordered(self):
        case_ids = ["poisson-2d-pytorch", "poisson-2d-numpy"]
        cases = get_fealpy_cases(case_ids)
        assert [c.case_id for c in cases] == case_ids

    def test_unknown_case_raises_key_error(self):
        with pytest.raises(KeyError):
            get_fealpy_cases(["nonexistent-case"])
