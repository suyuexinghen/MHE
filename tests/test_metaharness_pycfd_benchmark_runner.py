from __future__ import annotations

from metaharness_ext.pycfd.benchmark_runner import PyCFDBenchmarkRunner
from metaharness_ext.pycfd.contracts import PyCFDProblemSpec


class TestPyCFDBenchmarkRunner:
    def test_dry_run_extension_lane(self):
        runner = PyCFDBenchmarkRunner(allow_real_tools=False)
        spec = PyCFDProblemSpec(task_id="t1", case_type="vortex")
        result = runner.run_case("vortex-2d", spec, "extension")
        assert result["lane"] == "extension"
        assert result["status"] == "dry_run"

    def test_dry_run_direct_lane(self):
        runner = PyCFDBenchmarkRunner(allow_real_tools=False)
        spec = PyCFDProblemSpec(task_id="t1", case_type="vortex")
        result = runner.run_case("vortex-2d", spec, "direct")
        assert result["lane"] == "direct"
        assert result["status"] == "not_implemented"

    def test_dry_run_agent_lane(self):
        runner = PyCFDBenchmarkRunner(allow_real_tools=False)
        spec = PyCFDProblemSpec(task_id="t1", case_type="vortex")
        result = runner.run_case("vortex-2d", spec, "agent")
        assert result["lane"] == "agent"
        assert result["status"] == "not_implemented"

    def test_unknown_lane(self):
        runner = PyCFDBenchmarkRunner()
        spec = PyCFDProblemSpec(task_id="t1")
        result = runner.run_case("t1", spec, "bogus")
        assert result["status"] == "unknown_lane"

    def test_run_all_cases_dry_run(self):
        runner = PyCFDBenchmarkRunner(allow_real_tools=False)
        results = runner.run_all_cases(case_ids=["vortex-2d"], lanes=["extension"])
        assert len(results) == 1
        assert results[0]["status"] == "dry_run"
