from __future__ import annotations

from metaharness_ext.boutpp.compiler import BoutPPCompilerComponent
from metaharness_ext.boutpp.contracts import BoutPPProblemSpec


def test_render_bout_inp_and_command():
    spec = BoutPPProblemSpec(
        task_id="boutpp-test",
        executable="conduction",
        options={
            "solver": {"type": "rk4", "atol": 1e-10, "adaptive": True},
            "mesh": {"nx": 16, "ny": 8},
        },
        cli_overrides=["solver:type=rk4"],
    )
    compiler = BoutPPCompilerComponent()
    plan = compiler.compile(spec, run_id="run-1", workspace_dir="/tmp/ws")
    assert plan.plan_id
    assert plan.data_dir == "/tmp/ws/data"
    assert plan.command == ["mpiexec", "-np", "1", "conduction", "-d", "/tmp/ws/data", "solver:type=rk4"]
    assert "[mesh]" in plan.bout_inp_content
    assert "adaptive = true" in plan.bout_inp_content
    assert "atol = 1e-10" in plan.bout_inp_content


def test_direct_launcher_omits_mpi_prefix():
    spec = BoutPPProblemSpec(
        task_id="boutpp-direct",
        executable="/bin/true",
        mpi={"launcher_mode": "direct"},
    )
    compiler = BoutPPCompilerComponent()
    plan = compiler.compile(spec, run_id="run-2", workspace_dir="/tmp/ws")
    assert plan.command == ["/bin/true", "-d", "/tmp/ws/data"]
