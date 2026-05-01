from __future__ import annotations

import os
import tempfile

from metaharness_ext.pycfd.contracts import PyCFDProblemSpec, PyCFDRunPlan
from metaharness_ext.pycfd.executor import PyCFDExecutorComponent


class TestPyCFDExecutor:
    def _make_plan(self, script_source: str, timeout: int = 30) -> PyCFDRunPlan:
        spec = PyCFDProblemSpec(task_id="test-exec", timeout_seconds=timeout)
        return PyCFDRunPlan(
            plan_id="plan-1",
            task_id="test-exec",
            run_id="run-1",
            spec=spec,
            workspace_dir="/tmp/ws",
            script_source=script_source,
        )

    def test_successful_execution(self):
        script = """import json
print(json.dumps({"status": "completed", "residual_l1": 1e-6, "residual_l2": 1e-7,
    "wall_time_seconds": 0.5, "iterations": 100, "ncells": 800, "nnodes": 441, "nfaces": 1240}))
"""
        plan = self._make_plan(script)
        executor = PyCFDExecutorComponent()
        artifact = executor.execute(plan)
        assert artifact.status == "completed"
        assert artifact.residual_l1 == 1e-6
        assert artifact.residual_l2 == 1e-7
        assert artifact.ncells == 800

    def test_timeout(self):
        script = "import time; time.sleep(10)"
        plan = self._make_plan(script, timeout=1)
        executor = PyCFDExecutorComponent()
        artifact = executor.execute(plan)
        assert artifact.status == "timeout"

    def test_nonzero_exit(self):
        script = "import sys; sys.exit(1)"
        plan = self._make_plan(script)
        executor = PyCFDExecutorComponent()
        artifact = executor.execute(plan)
        assert artifact.status == "failed"
        assert artifact.return_code == 1

    def test_no_json_output(self):
        script = "print('no json here')"
        plan = self._make_plan(script)
        executor = PyCFDExecutorComponent()
        artifact = executor.execute(plan)
        assert artifact.status == "failed"
        assert "No JSON" in (artifact.error_message or "")

    def test_malformed_json(self):
        script = 'print("{bad json")'
        plan = self._make_plan(script)
        executor = PyCFDExecutorComponent()
        artifact = executor.execute(plan)
        assert artifact.status == "failed"

    def test_workspace_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script = 'import json; print(json.dumps({"status": "completed"}))'
            spec = PyCFDProblemSpec(task_id="t", timeout_seconds=30)
            plan = PyCFDRunPlan(
                plan_id="p1",
                task_id="t",
                run_id="r1",
                spec=spec,
                workspace_dir=tmpdir,
                script_source=script,
            )
            executor = PyCFDExecutorComponent(workspace_root=tmpdir)
            artifact = executor.execute(plan)
            assert artifact.status == "completed"
            assert os.path.isfile(os.path.join(tmpdir, "r1", "solve.py"))
