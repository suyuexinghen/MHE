from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.octave.capabilities import CAP_OCTAVE_EXECUTE_RUN
from metaharness_ext.octave.contracts import (
    OctaveEnvironmentReport,
    OctaveRunArtifact,
    OctaveRunPlan,
    OctaveWarning,
)
from metaharness_ext.octave.slots import OCTAVE_EXECUTOR_SLOT
from metaharness_ext.octave.workspace import OctaveWorkspaceManager


class OctaveExecutorComponent(HarnessComponent):
    def __init__(self) -> None:
        self._workspace_manager = OctaveWorkspaceManager()

    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(OCTAVE_EXECUTOR_SLOT)
        api.declare_input("plan", "OctaveRunPlan")
        api.declare_input("environment", "OctaveEnvironmentReport", required=False)
        api.declare_output("run", "OctaveRunArtifact", mode="sync")
        api.provide_capability(CAP_OCTAVE_EXECUTE_RUN)

    def execute_plan(
        self,
        plan: OctaveRunPlan,
        environment_report: OctaveEnvironmentReport | None = None,
    ) -> OctaveRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        if environment_report is not None and not environment_report.available:
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                status="unavailable",
                terminal_error_type="environment_unavailable",
                error_message=f"Octave environment unavailable: {environment_report.status}",
            )

        wrapper_path, input_files = self._workspace_manager.materialize_plan(plan, run_dir)
        resolved_binary = self._resolve_binary(plan.executable.binary_name)
        if resolved_binary is None:
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                status="unavailable",
                terminal_error_type="binary_missing",
                error_message=f"Octave binary not found: {plan.executable.binary_name}",
                wrapper_files=[wrapper_path],
                input_files=input_files,
            )

        command = [resolved_binary, "--no-gui", "--quiet", "--no-init-file", plan.wrapper_name]
        try:
            result = self._run_command(command, plan=plan, cwd=run_dir)
            stdout_text = result.stdout
            stderr_text = result.stderr
            return_code = result.returncode
            status = "completed" if return_code == 0 else "failed"
            terminal_error_type = None if return_code == 0 else "nonzero_return"
            error_message = None if return_code == 0 else f"Octave exited with status {return_code}"
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n"
            stderr_text += (
                f"Octave command timed out after {plan.executable.timeout_seconds} seconds."
            )
            return_code = None
            status = "timeout"
            terminal_error_type = "timeout"
            error_message = stderr_text

        stdout_path, stderr_path = self._write_logs(run_dir, stdout_text, stderr_text)
        output_files, figure_files, discovered_logs = self._workspace_manager.discover_outputs(
            run_dir,
            plan,
        )
        status_path = run_dir / "mhe_status.txt"
        log_files = [stdout_path, stderr_path, *discovered_logs]
        evidence_refs = self._build_evidence_refs(
            plan, run_dir, [wrapper_path], input_files, output_files
        )
        return OctaveRunArtifact(
            artifact_id=f"{plan.plan_id}-artifact-{uuid.uuid4().hex[:8]}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=status,
            return_code=return_code,
            terminal_error_type=terminal_error_type,
            command=command,
            working_directory=str(run_dir),
            wrapper_files=[wrapper_path],
            input_files=input_files,
            output_files=output_files,
            figure_files=figure_files,
            log_files=sorted(set(log_files)),
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            status_path=str(status_path) if status_path.exists() else None,
            summary_metrics={"output_count": len(output_files), "figure_count": len(figure_files)},
            warnings=self._classify_warnings(stderr_text),
            evidence_refs=evidence_refs,
            error_message=error_message,
        )

    def _resolve_run_dir(self, plan: OctaveRunPlan) -> Path:
        self._validate_id(plan.task_id)
        self._validate_id(plan.run_id)
        runtime = getattr(self, "_runtime", None)
        if runtime is not None and runtime.storage_path is not None:
            return runtime.storage_path / ".runs" / "octave" / plan.task_id / plan.run_id
        return Path(plan.workspace_dir).expanduser()

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _run_command(
        self,
        command: list[str],
        *,
        plan: OctaveRunPlan,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(plan.execution_params.environment)
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=plan.executable.timeout_seconds,
        )

    def _write_logs(self, run_dir: Path, stdout_text: str, stderr_text: str) -> tuple[str, str]:
        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        stdout_path.write_text(stdout_text)
        stderr_path.write_text(stderr_text)
        return str(stdout_path), str(stderr_path)

    def _coerce_process_output(self, output: bytes | str | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="replace")
        return output

    def _classify_warnings(self, stderr_text: str) -> list[OctaveWarning]:
        warnings: list[OctaveWarning] = []
        for line in stderr_text.splitlines():
            lower = line.lower()
            if "error:" in lower or "not installed" in lower:
                warnings.append(OctaveWarning(message=line, severity="blocking"))
            elif "warning:" in lower:
                severity = "benign" if "division by zero" in lower else "suspicious"
                warnings.append(OctaveWarning(message=line, severity=severity))
        return warnings

    def _build_evidence_refs(
        self,
        plan: OctaveRunPlan,
        run_dir: Path,
        wrapper_files: list[str],
        input_files: list[str],
        output_files: list[str],
    ) -> list[str]:
        refs = [f"octave://run/{plan.task_id}/{plan.run_id}"]
        refs.extend(f"file://{path}" for path in [*wrapper_files, *input_files, *output_files])
        refs.append(f"file://{run_dir / 'stdout.log'}")
        refs.append(f"file://{run_dir / 'stderr.log'}")
        return refs

    def _failed_artifact(
        self,
        plan: OctaveRunPlan,
        *,
        run_dir: Path,
        status: str,
        terminal_error_type: str,
        error_message: str,
        wrapper_files: list[str] | None = None,
        input_files: list[str] | None = None,
    ) -> OctaveRunArtifact:
        run_dir.mkdir(parents=True, exist_ok=True)
        stdout_path, stderr_path = self._write_logs(run_dir, "", error_message)
        return OctaveRunArtifact(
            artifact_id=f"{plan.plan_id}-artifact-{uuid.uuid4().hex[:8]}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=status,
            terminal_error_type=terminal_error_type,
            working_directory=str(run_dir),
            wrapper_files=wrapper_files or [],
            input_files=input_files or [],
            log_files=[stdout_path, stderr_path],
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            warnings=[OctaveWarning(message=error_message, severity="blocking")],
            evidence_refs=[f"octave://run/{plan.task_id}/{plan.run_id}"],
            error_message=error_message,
        )

    def _validate_id(self, value: str) -> None:
        if not value or any(part in value for part in ("/", "\\", "..")):
            raise ValueError(f"Invalid Octave run identifier: {value!r}")
