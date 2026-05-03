from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.moose.capabilities import CAP_MOOSE_EXECUTE_RUN
from metaharness_ext.moose.contracts import (
    MooseEnvironmentReport,
    MooseRunArtifact,
    MooseRunPlan,
    MooseWarning,
)
from metaharness_ext.moose.slots import MOOSE_EXECUTOR_SLOT


class MooseExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(MOOSE_EXECUTOR_SLOT)
        api.declare_input("plan", "MooseRunPlan")
        api.declare_input("environment", "MooseEnvironmentReport", required=False)
        api.declare_output("run", "MooseRunArtifact", mode="sync")
        api.provide_capability(CAP_MOOSE_EXECUTE_RUN)

    def execute_plan(
        self,
        plan: MooseRunPlan,
        environment_report: MooseEnvironmentReport | None = None,
    ) -> MooseRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        if environment_report is not None and not environment_report.available:
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                status="unavailable",
                terminal_error_type="environment_unavailable",
                error_message=f"MOOSE environment unavailable: {environment_report.status}",
            )

        run_dir.mkdir(parents=True, exist_ok=True)
        input_path = run_dir / plan.input_filename
        input_path.write_text(plan.input_source)
        resolved_binary = self._resolve_binary(plan.spec.executable.binary_name)
        if resolved_binary is None:
            return self._failed_artifact(
                plan,
                run_dir=run_dir,
                status="unavailable",
                terminal_error_type="binary_missing",
                error_message=f"MOOSE binary not found: {plan.spec.executable.binary_name}",
                input_files=[str(input_path)],
            )

        command = [resolved_binary, "-i", plan.input_filename, *plan.spec.input.extra_args]
        if plan.spec.input.mesh_only:
            command.append("--mesh-only")
            if plan.spec.input.mesh_output_path:
                command.append(plan.spec.input.mesh_output_path)

        try:
            result = self._run_command(command, plan=plan, cwd=run_dir)
            stdout_text = result.stdout
            stderr_text = result.stderr
            return_code = result.returncode
            status = "completed" if return_code == 0 else "failed"
            terminal_error_type = None if return_code == 0 else "nonzero_return"
            error_message = None if return_code == 0 else f"MOOSE exited with status {return_code}"
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n"
            stderr_text += (
                f"MOOSE command timed out after {plan.spec.executable.timeout_seconds} seconds."
            )
            return_code = None
            status = "timeout"
            terminal_error_type = "timeout"
            error_message = stderr_text

        stdout_path, stderr_path = self._write_logs(run_dir, stdout_text, stderr_text)
        output_files = self._discover_outputs(run_dir, plan)
        evidence_refs = self._build_evidence_refs(plan, run_dir, input_path, output_files)
        log_files = [stdout_path, stderr_path]
        if plan.spec.workspace is not None and plan.spec.workspace.output_directory:
            log_files.append(str(run_dir / plan.spec.workspace.output_directory))

        return MooseRunArtifact(
            artifact_id=f"{plan.plan_id}-artifact-{uuid.uuid4().hex[:8]}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=status,
            return_code=return_code,
            terminal_error_type=terminal_error_type,
            error_message=error_message,
            command=command,
            working_directory=str(run_dir),
            input_files=[str(input_path)],
            output_files=output_files,
            log_files=log_files,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            summary_metrics={"output_count": len(output_files)},
            evidence_refs=evidence_refs,
            warnings=self._classify_warnings(stderr_text),
        )

    def _validate_id(self, value: str) -> None:
        if not value or any(part in value for part in ("/", "\\", "..")):
            raise ValueError(f"Unsafe MOOSE run identifier: {value}")

    def _resolve_run_dir(self, plan: MooseRunPlan) -> Path:
        self._validate_id(plan.task_id)
        self._validate_id(plan.run_id)
        runtime = getattr(self, "_runtime", None)
        if runtime is not None and runtime.storage_path is not None:
            return runtime.storage_path / ".runs" / "moose" / plan.task_id / plan.run_id
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
        plan: MooseRunPlan,
        cwd: Path,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(plan.spec.executable.env)
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=plan.spec.executable.timeout_seconds,
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

    def _discover_outputs(self, run_dir: Path, plan: MooseRunPlan) -> list[str]:
        discovered: list[str] = []
        candidates = [run_dir]
        if plan.spec.workspace is not None and plan.spec.workspace.output_directory:
            candidates.append(run_dir / plan.spec.workspace.output_directory)
        if run_dir / "outputs" not in candidates:
            candidates.append(run_dir / "outputs")
        for output in plan.expected_outputs:
            file_name = output.resolved_file_name
            for base_dir in candidates:
                candidate = base_dir / file_name
                if candidate.exists():
                    discovered.append(str(candidate))
                    break
        return discovered

    def _classify_warnings(self, stderr_text: str) -> list[MooseWarning]:
        warnings: list[MooseWarning] = []
        for line in stderr_text.splitlines():
            lower = line.lower()
            if "error:" in lower:
                warnings.append(MooseWarning(message=line, severity="blocking"))
            elif "warning:" in lower:
                warnings.append(MooseWarning(message=line, severity="suspicious"))
        return warnings

    def _build_evidence_refs(
        self,
        plan: MooseRunPlan,
        run_dir: Path,
        input_path: Path,
        output_files: list[str],
    ) -> list[str]:
        refs = [f"moose://run/{plan.task_id}/{plan.run_id}"]
        refs.append(f"file://{input_path}")
        refs.extend(f"file://{path}" for path in output_files)
        refs.append(f"file://{run_dir / 'stdout.log'}")
        refs.append(f"file://{run_dir / 'stderr.log'}")
        return refs

    def _failed_artifact(
        self,
        plan: MooseRunPlan,
        *,
        run_dir: Path,
        status: str,
        terminal_error_type: str,
        error_message: str,
        input_files: list[str] | None = None,
    ) -> MooseRunArtifact:
        run_dir.mkdir(parents=True, exist_ok=True)
        stdout_path, stderr_path = self._write_logs(run_dir, "", error_message)
        return MooseRunArtifact(
            artifact_id=f"{plan.plan_id}-artifact-{uuid.uuid4().hex[:8]}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            status=status,
            terminal_error_type=terminal_error_type,
            error_message=error_message,
            command=list(plan.command),
            working_directory=str(run_dir),
            input_files=input_files or [],
            output_files=[],
            log_files=[stdout_path, stderr_path],
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            summary_metrics={"output_count": 0},
            evidence_refs=[f"moose://run/{plan.task_id}/{plan.run_id}"],
            warnings=[MooseWarning(message=error_message, severity="blocking")],
        )
