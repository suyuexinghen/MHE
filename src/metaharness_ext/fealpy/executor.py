from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.fealpy.capabilities import CAP_FEALPY_EXECUTE_RUN
from metaharness_ext.fealpy.contracts import (
    FealpyEnvironmentReport,
    FealpyRunArtifact,
    FealpyRunPlan,
)
from metaharness_ext.fealpy.slots import FEALPY_EXECUTOR_SLOT


class FealpyExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(FEALPY_EXECUTOR_SLOT)
        api.declare_input("plan", "FealpyRunPlan")
        api.declare_input("environment", "FealpyEnvironmentReport", required=False)
        api.declare_output("artifact", "FealpyRunArtifact", mode="sync")
        api.provide_capability(CAP_FEALPY_EXECUTE_RUN)

    def execute_plan(
        self,
        plan: FealpyRunPlan,
        environment: FealpyEnvironmentReport | None = None,
    ) -> FealpyRunArtifact:
        runtime = getattr(self, "_runtime", None)
        if runtime is not None:
            quota = runtime.resolved_resource_quota()
            if quota is not None and quota.exhausted:
                return FealpyRunArtifact(
                    artifact_id=f"artifact-{plan.run_id}",
                    run_id=plan.run_id,
                    task_id=plan.task_id,
                    plan_ref=plan.plan_id,
                    status="failed",
                    error_message=f"Resource quota exhausted: {quota.metadata}",
                    evidence_refs=plan.evidence_refs,
                )

        if environment is not None and not environment.available:
            return FealpyRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="unavailable",
                error_message="Environment is not available",
                evidence_refs=[],
            )

        workspace = Path(plan.workspace_dir).resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        script_path = workspace / "solve.py"
        script_path.write_text(plan.script_source)

        timeout = plan.spec.timeout_seconds
        warnings: list[str] = []

        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(workspace),
                env={**os.environ, "PYTHONPATH": os.environ.get("PYTHONPATH", "")},
            )
        except subprocess.TimeoutExpired:
            return FealpyRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="timeout",
                error_message=f"Execution timed out after {timeout}s",
                evidence_refs=plan.evidence_refs,
            )
        except OSError as exc:
            return FealpyRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="failed",
                return_code=-1,
                error_message=f"OS error: {exc}",
                evidence_refs=plan.evidence_refs,
            )

        if result.returncode != 0:
            stderr_tail = result.stderr.strip().split("\n")[-5:] if result.stderr else []
            return FealpyRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="failed",
                return_code=result.returncode,
                error_message="\n".join(stderr_tail) if stderr_tail else "Non-zero exit",
                evidence_refs=plan.evidence_refs,
                warnings=warnings,
            )

        return self._parse_output(plan, result.stdout, warnings)

    def _parse_output(
        self,
        plan: FealpyRunPlan,
        stdout: str,
        warnings: list[str],
    ) -> FealpyRunArtifact:
        last_line = stdout.strip().split("\n")[-1]
        try:
            data = json.loads(last_line)
        except json.JSONDecodeError:
            return FealpyRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="failed",
                error_message="Failed to parse JSON output",
                evidence_refs=plan.evidence_refs,
                warnings=warnings,
            )

        status = data.get("status", "failed")
        if status == "failed":
            return FealpyRunArtifact(
                artifact_id=f"artifact-{plan.run_id}",
                run_id=plan.run_id,
                task_id=plan.task_id,
                plan_ref=plan.plan_id,
                status="failed",
                error_message=data.get("error", "Unknown error"),
                evidence_refs=plan.evidence_refs,
                warnings=warnings,
            )

        return FealpyRunArtifact(
            artifact_id=f"artifact-{plan.run_id}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status="completed",
            l2_error=data.get("l2_error"),
            h1_error=data.get("h1_error"),
            dof_count=data.get("dof"),
            wall_time_seconds=data.get("wall_time"),
            mesh_info={
                "nc": data.get("nc"),
                "nn": data.get("nn"),
            },
            summary_metrics={
                "l2_error": data.get("l2_error"),
                "h1_error": data.get("h1_error"),
                "dof": data.get("dof"),
                "wall_time": data.get("wall_time"),
            },
            evidence_refs=plan.evidence_refs,
            warnings=warnings,
        )
