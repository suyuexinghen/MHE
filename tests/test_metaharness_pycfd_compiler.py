from __future__ import annotations

from metaharness_ext.pycfd.compiler import PyCFDCompilerComponent
from metaharness_ext.pycfd.contracts import PyCFDProblemSpec


class TestPyCFDCompiler:
    def test_plan_id_deterministic(self):
        compiler = PyCFDCompilerComponent(pycfd_src_path="/tmp/pycfd")
        spec = PyCFDProblemSpec(task_id="test", case_type="vortex")
        id1 = compiler._build_plan_id(spec)
        id2 = compiler._build_plan_id(spec)
        assert id1 == id2

    def test_plan_id_differs_per_case(self):
        compiler = PyCFDCompilerComponent(pycfd_src_path="/tmp/pycfd")
        id1 = compiler._build_plan_id(PyCFDProblemSpec(task_id="a", case_type="vortex"))
        id2 = compiler._build_plan_id(PyCFDProblemSpec(task_id="a", case_type="shock_diffraction"))
        assert id1 != id2

    def test_compile_returns_plan(self):
        compiler = PyCFDCompilerComponent(pycfd_src_path="/tmp/pycfd")
        spec = PyCFDProblemSpec(task_id="compile-test", case_type="vortex")
        plan = compiler.compile(spec, run_id="run-1", workspace_dir="/tmp/ws")
        assert plan.plan_id
        assert plan.task_id == "compile-test"
        assert plan.script_source
        assert "run_pycfd_case" in plan.script_source
        assert plan.experiment_ref == "compile-test"

    def test_vortex_script_contains_expected_config(self):
        compiler = PyCFDCompilerComponent(pycfd_src_path="/tmp/pycfd")
        spec = PyCFDProblemSpec(task_id="vtx", case_type="vortex")
        plan = compiler.compile(spec, run_id="r1", workspace_dir="/tmp/ws")
        assert "'case_type': 'vortex'" in plan.script_source
        assert "'flowtype': 'vortex'" in plan.script_source
        assert "'solver_type': 'explicit_unsteady_solver'" in plan.script_source

    def test_shock_script_contains_expected_config(self):
        compiler = PyCFDCompilerComponent(pycfd_src_path="/tmp/pycfd")
        spec = PyCFDProblemSpec(task_id="shk", case_type="shock_diffraction")
        plan = compiler.compile(spec, run_id="r1", workspace_dir="/tmp/ws")
        assert "'case_type': 'shock_diffraction'" in plan.script_source
        assert "'flowtype': 'shock-diffraction'" in plan.script_source

    def test_mms_script_adds_compute_te_mms(self):
        compiler = PyCFDCompilerComponent(pycfd_src_path="/tmp/pycfd")
        spec = PyCFDProblemSpec(task_id="m", case_type="mms")
        plan = compiler.compile(spec, run_id="r1", workspace_dir="/tmp/ws")
        assert "'compute_te_mms': True" in plan.script_source
