from __future__ import annotations

import pytest

from metaharness_ext.pycfd.contracts import (
    PyCFDFlowSpec,
    PyCFDMeshSpec,
    PyCFDProblemSpec,
    PyCFDSolverSpec,
)


class TestPyCFDMeshSpec:
    def test_defaults(self):
        m = PyCFDMeshSpec()
        assert m.mesh_type == "quad"
        assert m.nx == 42
        assert m.ny == 21

    def test_validation_nx_minimum(self):
        with pytest.raises(ValueError, match=">= 2"):
            PyCFDMeshSpec(nx=1)

    def test_validation_ny_minimum(self):
        with pytest.raises(ValueError, match=">= 2"):
            PyCFDMeshSpec(ny=1)


class TestPyCFDFlowSpec:
    def test_defaults(self):
        f = PyCFDFlowSpec()
        assert f.M_inf == 0.3
        assert f.gamma == 1.4

    def test_validation_mach_positive(self):
        with pytest.raises(ValueError, match="positive"):
            PyCFDFlowSpec(M_inf=0)

    def test_validation_gamma(self):
        with pytest.raises(ValueError, match="> 1.0"):
            PyCFDFlowSpec(gamma=1.0)


class TestPyCFDSolverSpec:
    def test_defaults(self):
        s = PyCFDSolverSpec()
        assert s.CFL == 0.9
        assert s.second_order is True

    def test_cfl_range(self):
        with pytest.raises(ValueError, match=r"\(0, 2.0\]"):
            PyCFDSolverSpec(CFL=2.5)


class TestPyCFDProblemSpec:
    def test_minimal(self):
        s = PyCFDProblemSpec(task_id="test-case")
        assert s.task_id == "test-case"
        assert s.case_type == "vortex"
        assert s.flowtype == "vortex"
        assert s.solver_type == "explicit_unsteady_solver"

    def test_task_id_sanitization(self):
        with pytest.raises(ValueError, match="simple identifier"):
            PyCFDProblemSpec(task_id="bad/path")

        with pytest.raises(ValueError, match="simple identifier"):
            PyCFDProblemSpec(task_id="  ")

    def test_case_to_flowtype_mapping(self):
        assert PyCFDProblemSpec(task_id="t", case_type="airfoil").flowtype == "freestream"
        assert PyCFDProblemSpec(task_id="t", case_type="cylinder").flowtype == "freestream"
        assert PyCFDProblemSpec(task_id="t", case_type="mms").flowtype == "mms"
        assert (
            PyCFDProblemSpec(task_id="t", case_type="shock_diffraction").flowtype
            == "shock-diffraction"
        )

    def test_case_to_solver_type_mapping(self):
        assert (
            PyCFDProblemSpec(task_id="t", case_type="airfoil").solver_type
            == "explicit_steady_solver"
        )
        assert (
            PyCFDProblemSpec(task_id="t", case_type="cylinder").solver_type
            == "explicit_steady_solver"
        )
        assert PyCFDProblemSpec(task_id="t", case_type="mms").solver_type == "mms_solver"
        assert (
            PyCFDProblemSpec(task_id="t", case_type="shock_diffraction").solver_type
            == "explicit_unsteady_solver_efficient_shockdiffraction"
        )

    def test_validation_timeout_positive(self):
        with pytest.raises(ValueError, match="positive"):
            PyCFDProblemSpec(task_id="t", timeout_seconds=0)

    def test_validation_tfinal_positive(self):
        with pytest.raises(ValueError, match="positive"):
            PyCFDProblemSpec(task_id="t", t_final=0)

    def test_validation_dt_positive(self):
        with pytest.raises(ValueError, match="positive"):
            PyCFDProblemSpec(task_id="t", dt=0)
