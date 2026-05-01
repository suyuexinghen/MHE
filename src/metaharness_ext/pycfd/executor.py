from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

from metaharness_ext.pycfd.contracts import PyCFDRunArtifact, PyCFDRunPlan


class PyCFDExecutorComponent:
    """Executes a PyCFD run plan via subprocess."""

    def __init__(self, workspace_root: str | None = None):
        self._workspace_root = Path(workspace_root) if workspace_root else Path(".runs/pycfd")

    def execute(self, plan: PyCFDRunPlan) -> PyCFDRunArtifact:
        artifact_id = f"pycfd-artifact-{uuid.uuid4().hex[:12]}"
        workspace = self._workspace_root / plan.run_id
        workspace.mkdir(parents=True, exist_ok=True)

        script_path = workspace / "solve.py"
        script_path.write_text(plan.script_source)

        artifact = PyCFDRunArtifact(
            artifact_id=artifact_id,
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status="unavailable",
        )

        timeout = plan.spec.timeout_seconds
        try:
            result = subprocess.run(
                [sys.executable, str(script_path.resolve())],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(workspace),
            )
        except subprocess.TimeoutExpired:
            artifact.status = "timeout"
            artifact.return_code = -1
            artifact.error_message = f"Execution timed out after {timeout}s"
            return artifact
        except OSError as e:
            artifact.status = "failed"
            artifact.return_code = -2
            artifact.error_message = f"OS error: {e}"
            return artifact

        artifact.return_code = result.returncode

        # Parse JSON from last stdout line
        if result.returncode != 0:
            artifact.status = "failed"
            artifact.error_message = (
                result.stderr[:2000] if result.stderr else f"Exit code {result.returncode}"
            )
            return artifact

        stdout = result.stdout.strip()
        if not stdout:
            artifact.status = "failed"
            artifact.error_message = "No output from solver"
            return artifact

        # Find the last JSON line
        try:
            lines = stdout.splitlines()
            metrics = None
            for line in reversed(lines):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        metrics = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue

            if metrics is None:
                artifact.status = "failed"
                artifact.error_message = "No JSON metrics found in solver output"
                return artifact

            artifact.status = metrics.get("status", "completed")
            artifact.residual_l1 = metrics.get("residual_l1")
            artifact.residual_l2 = metrics.get("residual_l2")
            artifact.wall_time_seconds = metrics.get("wall_time_seconds")
            artifact.iterations = metrics.get("iterations")
            artifact.ncells = metrics.get("ncells")
            artifact.nnodes = metrics.get("nnodes")
            artifact.nfaces = metrics.get("nfaces")
            artifact.summary_metrics = metrics
        except (json.JSONDecodeError, KeyError) as e:
            artifact.status = "failed"
            artifact.error_message = f"Failed to parse output: {e}"
            return artifact

        return artifact
