from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.jedi.capabilities import (
    CAP_JEDI_REAL_RUN,
    CAP_JEDI_SCHEMA,
    CAP_JEDI_VALIDATE_ONLY,
)
from metaharness_ext.jedi.contracts import JediRunArtifact, JediRunPlan
from metaharness_ext.jedi.preprocessor import JediRunPreprocessor
from metaharness_ext.jedi.slots import JEDI_EXECUTOR_SLOT


class JediExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(JEDI_EXECUTOR_SLOT)
        api.declare_input("plan", "JediRunPlan")
        api.declare_output("run", "JediRunArtifact", mode="sync")
        api.provide_capability(CAP_JEDI_SCHEMA)
        api.provide_capability(CAP_JEDI_VALIDATE_ONLY)
        api.provide_capability(CAP_JEDI_REAL_RUN)

    def execute_plan(self, plan: JediRunPlan) -> JediRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        try:
            prepared_inputs = JediRunPreprocessor().prepare(plan, run_dir)
        except ValueError as error:
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text="",
                stderr_text=str(error),
            )
            return self._build_artifact(
                plan,
                run_dir=run_dir,
                command=[plan.executable.binary_name, plan.execution_mode],
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                return_code=None,
                status="unavailable",
                prepared_inputs=[],
                result_summary={"fallback_reason": "missing_required_runtime_path", "exit_code": None},
            )

        resolved_binary = self._resolve_binary(plan.executable.binary_name)
        if resolved_binary is None:
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text="",
                stderr_text=f"JEDI binary not found: {plan.executable.binary_name}",
            )
            return self._build_artifact(
                plan,
                run_dir=run_dir,
                command=[plan.executable.binary_name, plan.execution_mode],
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                return_code=None,
                status="unavailable",
                prepared_inputs=prepared_inputs,
                result_summary={"fallback_reason": "binary_not_found", "exit_code": None},
            )

        resolved_launcher: str | None = None
        if plan.executable.launcher != "direct":
            resolved_launcher = self._resolve_binary(plan.executable.launcher)
            if resolved_launcher is None:
                stdout_path, stderr_path = self._write_logs(
                    run_dir,
                    stdout_text="",
                    stderr_text=f"Launcher not found: {plan.executable.launcher}",
                )
                return self._build_artifact(
                    plan,
                    run_dir=run_dir,
                    command=self._build_command(plan, resolved_binary, plan.executable.launcher),
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    return_code=None,
                    status="unavailable",
                    prepared_inputs=prepared_inputs,
                    result_summary={"fallback_reason": "launcher_not_found", "exit_code": None},
                )

        command = self._build_command(plan, resolved_binary, resolved_launcher)
        try:
            result = self._run_command(
                command,
                cwd=run_dir,
                timeout_seconds=plan.executable.timeout_seconds,
            )
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n\n"
            stderr_text += (
                f"JEDI command timed out after {plan.executable.timeout_seconds} seconds."
            )
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
            )
            return self._build_artifact(
                plan,
                run_dir=run_dir,
                command=command,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                return_code=None,
                status="failed",
                prepared_inputs=prepared_inputs,
                result_summary={"fallback_reason": "command_timeout", "exit_code": None},
            )

        stdout_path, stderr_path = self._write_logs(
            run_dir,
            stdout_text=result.stdout,
            stderr_text=result.stderr,
        )
        status = "completed" if result.returncode == 0 else "failed"
        return self._build_artifact(
            plan,
            run_dir=run_dir,
            command=command,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            return_code=result.returncode,
            status=status,
            prepared_inputs=prepared_inputs,
            result_summary={"fallback_reason": None, "exit_code": result.returncode},
        )

    def _resolve_run_dir(self, plan: JediRunPlan) -> Path:
        runtime = getattr(self, "_runtime", None)
        if runtime is None or runtime.storage_path is None:
            raise RuntimeError("JediExecutorComponent requires runtime.storage_path")
        self._validate_task_id(plan.task_id)
        run_dir = runtime.storage_path / "jedi_runs" / plan.task_id / plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _validate_task_id(self, task_id: str) -> None:
        if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
            raise ValueError(f"Invalid task_id: {task_id!r}")

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _build_command(
        self,
        plan: JediRunPlan,
        resolved_binary: str,
        resolved_launcher: str | None,
    ) -> list[str]:
        base_command: list[str]
        if plan.execution_mode == "schema":
            schema_name = Path(plan.schema_path or "schema.json").name
            base_command = [resolved_binary, f"--output-json-schema={schema_name}"]
        elif plan.execution_mode == "validate_only":
            base_command = [resolved_binary, "--validate-only", Path(plan.config_path).name]
        else:
            base_command = [resolved_binary, Path(plan.config_path).name]

        if resolved_launcher is None:
            return base_command

        launcher_command = [resolved_launcher, *plan.executable.launcher_args]
        if plan.executable.process_count is not None:
            launcher_command.extend(["-n", str(plan.executable.process_count)])
        return [*launcher_command, *base_command]

    def _run_command(
        self,
        command: list[str],
        *,
        cwd: Path,
        timeout_seconds: int | None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )

    def _coerce_process_output(self, value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode()
        return value

    def _write_logs(self, run_dir: Path, *, stdout_text: str, stderr_text: str) -> tuple[str, str]:
        stdout_path = run_dir / "stdout.log"
        stderr_path = run_dir / "stderr.log"
        stdout_path.write_text(stdout_text)
        stderr_path.write_text(stderr_text)
        return str(stdout_path), str(stderr_path)

    def _build_artifact(
        self,
        plan: JediRunPlan,
        *,
        run_dir: Path,
        command: list[str],
        stdout_path: str,
        stderr_path: str,
        return_code: int | None,
        status: str,
        prepared_inputs: list[str],
        result_summary: dict[str, object],
    ) -> JediRunArtifact:
        schema_path = run_dir / "schema.json"
        output_files = self._discover_files(run_dir, plan.expected_outputs)
        diagnostic_files = [
            path
            for path in self._discover_files(run_dir, ["*.log", "*.out", "*.nc", "*.ioda"])
            if Path(path).name not in {"stdout.log", "stderr.log"}
        ]
        return JediRunArtifact(
            task_id=plan.task_id,
            run_id=plan.run_id,
            application_family=plan.application_family,
            execution_mode=plan.execution_mode,
            command=command,
            return_code=return_code,
            config_path=str(run_dir / "config.yaml"),
            schema_path=str(schema_path) if schema_path.exists() else None,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            prepared_inputs=prepared_inputs,
            output_files=output_files,
            diagnostic_files=diagnostic_files,
            working_directory=str(run_dir),
            status=status,
            result_summary=result_summary,
        )

    def _discover_files(self, run_dir: Path, patterns: list[str]) -> list[str]:
        files: list[str] = []
        seen: set[str] = set()
        for pattern in patterns:
            for path in sorted(run_dir.glob(pattern)):
                if not path.is_file():
                    continue
                path_str = str(path)
                if path_str in seen:
                    continue
                seen.add(path_str)
                files.append(path_str)
        return files
