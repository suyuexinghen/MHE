from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.lean.backends import MockLeanBackend
from metaharness_ext.lean.capabilities import CAP_LEAN_EXECUTE_PROOF
from metaharness_ext.lean.contracts import (
    LeanDiagnostic,
    LeanEnvironmentReport,
    LeanExecutionPolicy,
    LeanRunArtifact,
    LeanRunPlan,
)
from metaharness_ext.lean.slots import LEAN_EXECUTOR_SLOT
from metaharness_ext.lean.types import LeanDiagnosticSeverity

_DIAGNOSTIC_RE = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+):(?P<column>\d+):\s*"
    r"(?P<severity>error|warning|information):\s*(?P<message>.*)$"
)


class LeanExecutorComponent(HarnessComponent):
    def __init__(self, backend: MockLeanBackend | None = None) -> None:
        self._backend = backend or MockLeanBackend()

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(LEAN_EXECUTOR_SLOT)
        api.declare_input("plan", "LeanRunPlan")
        api.declare_output("run", "LeanRunArtifact", mode="sync")
        api.provide_capability(CAP_LEAN_EXECUTE_PROOF)

    def execute_plan(
        self,
        plan: LeanRunPlan,
        environment_report: LeanEnvironmentReport | None = None,
        policy: LeanExecutionPolicy | None = None,
    ) -> LeanRunArtifact:
        execution_policy = policy or LeanExecutionPolicy()
        if execution_policy.mode == "dry_run" or os.environ.get("MHE_RUN_REAL_LEAN") != "1":
            return self._execute_mock(plan)
        return self._execute_real(plan, environment_report, execution_policy)

    def _execute_mock(self, plan: LeanRunPlan) -> LeanRunArtifact:
        start = time.monotonic()
        result = self._backend.run(plan.target_file)
        sorry_locations = [
            diagnostic
            for diagnostic in result.diagnostics
            if diagnostic.code == "sorry" or "sorry" in diagnostic.message.lower()
        ]
        return LeanRunArtifact(
            artifact_id=f"artifact:{plan.plan_id}",
            plan_ref=plan.plan_id,
            exit_code=result.exit_code,
            stdout=result.stdout,
            stderr=result.stderr,
            diagnostics=result.diagnostics,
            sorry_locations=sorry_locations,
            duration_seconds=time.monotonic() - start,
            backend="mock",
            execution_mode="dry_run",
        )

    def _execute_real(
        self,
        plan: LeanRunPlan,
        environment_report: LeanEnvironmentReport | None,
        policy: LeanExecutionPolicy,
    ) -> LeanRunArtifact:
        start = time.monotonic()
        cwd = plan.execution_params.get("project_root")
        if cwd is None and environment_report is not None and environment_report.lakefile_path:
            cwd = str(Path(environment_report.lakefile_path).parent)
        cwd = cwd or str(Path(plan.target_file).resolve().parent)
        command = ["lake", "env", "lean", plan.target_file]
        build_result = None
        if Path(cwd, "lakefile.lean").exists():
            build_result = subprocess.run(
                ["lake", "build"],
                capture_output=True,
                text=True,
                timeout=policy.timeout_seconds,
                cwd=cwd,
                check=False,
            )
            if build_result.returncode != 0:
                return self._real_artifact_from_result(
                    plan=plan,
                    result=build_result,
                    start=start,
                )
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=policy.timeout_seconds,
                cwd=cwd,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            diagnostic = LeanDiagnostic(
                file=plan.target_file,
                severity=LeanDiagnosticSeverity.ERROR,
                message=f"Lean execution timed out after {policy.timeout_seconds}s",
                code="timeout",
            )
            return LeanRunArtifact(
                artifact_id=f"artifact:{plan.plan_id}",
                plan_ref=plan.plan_id,
                exit_code=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                diagnostics=[diagnostic],
                duration_seconds=time.monotonic() - start,
                backend="lake",
                execution_mode="real_lean",
            )

        if build_result is not None:
            result.stdout = build_result.stdout + result.stdout
            result.stderr = build_result.stderr + result.stderr
        return self._real_artifact_from_result(
            plan=plan,
            result=result,
            start=start,
        )

    def _real_artifact_from_result(
        self,
        *,
        plan: LeanRunPlan,
        result: subprocess.CompletedProcess[str],
        start: float,
    ) -> LeanRunArtifact:
        diagnostics = parse_lean_diagnostics(
            result.stdout, plan.target_file
        ) + parse_lean_diagnostics(result.stderr, plan.target_file)
        sorry_locations = [
            diagnostic
            for diagnostic in diagnostics
            if diagnostic.code == "sorry" or "sorry" in diagnostic.message.lower()
        ]
        return LeanRunArtifact(
            artifact_id=f"artifact:{plan.plan_id}",
            plan_ref=plan.plan_id,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            diagnostics=diagnostics,
            sorry_locations=sorry_locations,
            duration_seconds=time.monotonic() - start,
            backend="lake",
            execution_mode="real_lean",
        )


def parse_lean_diagnostics(output: str, fallback_file: str) -> list[LeanDiagnostic]:
    diagnostics: list[LeanDiagnostic] = []
    for line in output.splitlines():
        match = _DIAGNOSTIC_RE.match(line.strip())
        if match is None:
            continue
        message = match.group("message")
        code = "sorry" if "sorry" in message.lower() else None
        diagnostics.append(
            LeanDiagnostic(
                file=match.group("file") or fallback_file,
                line=int(match.group("line")),
                column=int(match.group("column")),
                severity=_parse_severity(match.group("severity")),
                message=message,
                code=code,
            )
        )
    return diagnostics


def _parse_severity(value: str) -> LeanDiagnosticSeverity:
    if value == "information":
        return LeanDiagnosticSeverity.INFO
    return LeanDiagnosticSeverity(value)
