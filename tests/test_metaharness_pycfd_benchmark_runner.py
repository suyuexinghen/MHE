from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, BenchmarkLane
from metaharness_ext.pycfd.benchmark_runner import PyCFDBenchmarkRunner


def _make_vortex_case() -> BenchmarkCaseSpec:
    return BenchmarkCaseSpec(
        case_id="vortex-2d",
        suite="pycfd-pde",
        task_family="pycfd-euler",
        description="Isentropic vortex convection",
        source_reference="PyCFD/vortex",
        expected_metrics=["residual_l1", "residual_l2"],
        tolerance={"residual_l1": 1e-3, "residual_l2": 1e-3},
        problem_definition={
            "case_type": "vortex",
            "task_id": "bench-vortex",
            "nx": 42,
            "ny": 21,
            "t_final": 1.0,
            "dt": 0.01,
        },
    )


class TestPyCFDBenchmarkRunner:
    def test_dry_run_extension_lane(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["extension"])
        assert len(summaries) == 1
        s = summaries[0]
        assert s.lane == "extension"
        assert s.case_id == "vortex-2d"
        assert s.status == "passed"

    def test_dry_run_direct_lane(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["direct"])
        assert len(summaries) == 1
        s = summaries[0]
        assert s.lane == "direct"
        assert s.status == "passed"

    def test_dry_run_agent_lane(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["agent"])
        assert len(summaries) == 1
        s = summaries[0]
        assert s.lane == "agent"
        assert s.status == "passed"

    def test_unknown_lane_ignored(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path)
        case = _make_vortex_case()
        summaries = runner.run_case(case, ["bogus"])  # type: ignore[list-item]
        assert len(summaries) == 0

    def test_run_all_three_lanes(self, tmp_path: Path):
        runner = PyCFDBenchmarkRunner(runs_root=tmp_path, allow_real_tools=False)
        case = _make_vortex_case()
        lanes: list[BenchmarkLane] = ["extension", "direct", "agent"]
        summaries = runner.run_case(case, lanes)
        assert len(summaries) == 3
        lane_names = {s.lane for s in summaries}
        assert lane_names == {"extension", "direct", "agent"}
        for s in summaries:
            assert s.status == "passed"
