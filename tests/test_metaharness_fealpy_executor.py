from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyMeshSpec,
    FealpyProblemSpec,
    FealpyRunPlan,
)
from metaharness_ext.fealpy.executor import FealpyExecutorComponent


def _spec() -> FealpyProblemSpec:
    return FealpyProblemSpec(
        task_id="exec-test",
        pde_family="poisson",
        example_key=1,
        backend="numpy",
        mesh=FealpyMeshSpec(meshtype="tri", nx=4, ny=4),
        fe_degree=1,
        timeout_seconds=30,
    )


def _plan(spec: FealpyProblemSpec | None = None) -> FealpyRunPlan:
    spec = spec or _spec()
    return FealpyRunPlan(
        plan_id="fealpy-exec-test-abc123",
        task_id=spec.task_id,
        run_id="run-exec-test-1",
        spec=spec,
        workspace_dir=str(Path("/tmp/.runs/fealpy/exec-test/run-exec-test-1")),
        script_source="print('hello')",
    )


def _mock_subprocess_result(stdout: str = "", stderr: str = "", returncode: int = 0):
    result = Mock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


def test_executor_success() -> None:
    valid_output = json.dumps(
        {
            "status": "completed",
            "l2_error": 1.23e-8,
            "h1_error": 4.56e-6,
            "dof": 289,
            "wall_time": 0.15,
            "nc": 128,
            "nn": 81,
        }
    )
    plan = _plan()
    executor = FealpyExecutorComponent()

    with patch("subprocess.run", return_value=_mock_subprocess_result(stdout=valid_output)):
        artifact = executor.execute_plan(plan)

    assert artifact.status == "completed"
    assert artifact.l2_error == 1.23e-8
    assert artifact.h1_error == 4.56e-6
    assert artifact.dof_count == 289
    assert artifact.wall_time_seconds == 0.15
    assert artifact.mesh_info == {"nc": 128, "nn": 81}
    assert artifact.summary_metrics["l2_error"] == 1.23e-8
    assert artifact.return_code is None


def test_executor_environment_unavailable() -> None:
    env = FealpyEnvironmentReport(
        task_id="exec-test", available=False, status="prerequisite_missing"
    )
    executor = FealpyExecutorComponent()
    artifact = executor.execute_plan(_plan(), environment=env)

    assert artifact.status == "unavailable"
    assert artifact.error_message == "Environment is not available"


def test_executor_timeout() -> None:
    executor = FealpyExecutorComponent()

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="python", timeout=30)):
        artifact = executor.execute_plan(_plan())

    assert artifact.status == "timeout"
    assert "timed out" in (artifact.error_message or "")


def test_executor_non_zero_exit() -> None:
    executor = FealpyExecutorComponent()

    with patch(
        "subprocess.run",
        return_value=_mock_subprocess_result(
            stdout="", stderr="Traceback: NameError\n", returncode=1
        ),
    ):
        artifact = executor.execute_plan(_plan())

    assert artifact.status == "failed"
    assert artifact.return_code == 1
    assert artifact.error_message is not None


def test_executor_json_parse_failure() -> None:
    executor = FealpyExecutorComponent()

    with patch(
        "subprocess.run",
        return_value=_mock_subprocess_result(stdout="not valid json", returncode=0),
    ):
        artifact = executor.execute_plan(_plan())

    assert artifact.status == "failed"
    assert "parse" in (artifact.error_message or "").lower()


def test_executor_os_error() -> None:
    executor = FealpyExecutorComponent()

    with patch("subprocess.run", side_effect=OSError("No such file")):
        artifact = executor.execute_plan(_plan())

    assert artifact.status == "failed"
    assert artifact.return_code == -1
    assert "OS error" in (artifact.error_message or "")


def test_executor_failed_status_from_script() -> None:
    failed_output = json.dumps({"status": "failed", "error": "Solver did not converge"})
    executor = FealpyExecutorComponent()

    with patch("subprocess.run", return_value=_mock_subprocess_result(stdout=failed_output)):
        artifact = executor.execute_plan(_plan())

    assert artifact.status == "failed"
    assert "Solver did not converge" in (artifact.error_message or "")


def test_executor_writes_script_to_workspace() -> None:
    plan = _plan()
    executor = FealpyExecutorComponent()

    with patch("pathlib.Path.mkdir") as mock_mkdir:
        with patch("pathlib.Path.write_text") as mock_write:
            with patch(
                "subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="python", timeout=30)
            ):
                executor.execute_plan(plan)

    mock_mkdir.assert_called_once()
    mock_write.assert_called_once_with(plan.script_source)


def test_executor_rejects_exhausted_quota() -> None:
    """Executor returns failed artifact when runtime quota is exhausted."""
    from metaharness.sdk.execution import ResourceQuota
    from metaharness.sdk.runtime import ComponentRuntime

    quota = ResourceQuota(
        quota_id="test-quota",
        resource_type="fealpy_mesh",
        limit=100,
        used=100,
        remaining=0,
        exhausted=True,
    )
    runtime = ComponentRuntime()
    runtime.resource_quota = quota

    executor = FealpyExecutorComponent()
    executor._runtime = runtime
    plan = _plan()
    artifact = executor.execute_plan(plan)
    assert artifact.status == "failed"
    assert "Resource quota exhausted" in (artifact.error_message or "")
