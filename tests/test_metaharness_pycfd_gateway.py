from __future__ import annotations

import pytest

from metaharness_ext.pycfd.gateway import PyCFDGatewayComponent


class TestPyCFDGateway:
    def test_issue_task_defaults(self):
        gw = PyCFDGatewayComponent()
        spec = gw.issue_task("my-task")
        assert spec.task_id == "my-task"
        assert spec.case_type == "vortex"

    def test_issue_task_specific_case(self):
        gw = PyCFDGatewayComponent()
        spec = gw.issue_task("airfoil-task", case_type="airfoil")
        assert spec.case_type == "airfoil"

    def test_rejects_unknown_case_type(self):
        gw = PyCFDGatewayComponent()
        with pytest.raises(ValueError, match="Unknown case_type"):
            gw.issue_task("bad", case_type="nonexistent")

    def test_issue_task_with_overrides(self):
        gw = PyCFDGatewayComponent()
        spec = gw.issue_task("t1", case_type="vortex", overrides={"t_final": 5.0, "dt": 0.001})
        assert spec.t_final == 5.0
        assert spec.dt == 0.001

    def test_issue_task_with_nested_overrides(self):
        gw = PyCFDGatewayComponent()
        spec = gw.issue_task(
            "t1", case_type="vortex", overrides={"flow.M_inf": 1.5, "solver.CFL": 0.5}
        )
        assert spec.flow.M_inf == 1.5
        assert spec.solver.CFL == 0.5
