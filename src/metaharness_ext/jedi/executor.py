from __future__ import annotations

import json
import re
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
from metaharness_ext.jedi.contracts import JediEnvironmentReport, JediRunArtifact, JediRunPlan
from metaharness_ext.jedi.preprocessor import JediRunPreprocessor
from metaharness_ext.jedi.slots import JEDI_EXECUTOR_SLOT

_LAUNCHER_PROCESS_COUNT_FLAGS: dict[str, str | None] = {
    "direct": None,
    "mpiexec": "-n",
    "mpirun": "-n",
    "srun": "-n",
    "jsrun": "-n",
}

_PROCESS_COUNT_FLAG_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "mpiexec": (
        re.compile(r"^-n(?:=\d+|\d+)?$"),
        re.compile(r"^-np(?:=\d+|\d+)?$"),
    ),
    "mpirun": (
        re.compile(r"^-n(?:=\d+|\d+)?$"),
        re.compile(r"^-np(?:=\d+|\d+)?$"),
    ),
    "srun": (re.compile(r"^-n(?:=\d+|\d+)?$"), re.compile(r"^--ntasks(?:=.*)?$")),
    "jsrun": (
        re.compile(r"^-n(?:=\d+|\d+)?$"),
        re.compile(r"^-np(?:=\d+|\d+)?$"),
        re.compile(r"^-r(?:=\d+|\d+)?$"),
    ),
}


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

    def execute_plan(
        self,
        plan: JediRunPlan,
        environment_report: JediEnvironmentReport | None = None,
    ) -> JediRunArtifact:
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
                result_summary=self._base_result_summary(
                    fallback_reason="missing_required_runtime_path",
                    exit_code=None,
                    environment_report=environment_report,
                ),
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
                result_summary=self._base_result_summary(
                    fallback_reason="binary_not_found",
                    exit_code=None,
                    environment_report=environment_report,
                ),
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
                    result_summary=self._base_result_summary(
                        fallback_reason="launcher_not_found",
                        exit_code=None,
                        environment_report=environment_report,
                    ),
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
                result_summary=self._base_result_summary(
                    fallback_reason="command_timeout",
                    exit_code=None,
                    environment_report=environment_report,
                ),
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
            result_summary=self._base_result_summary(
                fallback_reason=None,
                exit_code=result.returncode,
                environment_report=environment_report,
            ),
        )

    def _base_result_summary(
        self,
        *,
        fallback_reason: str | None,
        exit_code: int | None,
        environment_report: JediEnvironmentReport | None,
    ) -> dict[str, object]:
        summary: dict[str, object] = {
            "fallback_reason": fallback_reason,
            "exit_code": exit_code,
        }
        if environment_report is None:
            return summary
        summary["prerequisite_evidence"] = {
            prerequisite: list(paths)
            for prerequisite, paths in environment_report.prerequisite_evidence.items()
        }
        if environment_report.ready_prerequisites:
            summary["checkpoint_refs"] = [
                f"checkpoint://jedi/prerequisite/{self._checkpoint_slug(prerequisite)}"
                for prerequisite in environment_report.ready_prerequisites
            ]
        return summary

    def _checkpoint_slug(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")

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

        return [*self._build_launcher_command(plan, resolved_launcher), *base_command]

    def _build_launcher_command(self, plan: JediRunPlan, resolved_launcher: str) -> list[str]:
        launcher = plan.executable.launcher
        launcher_command = [resolved_launcher]
        self._reject_duplicate_process_count_args(launcher, plan.executable.launcher_args)
        process_count_flag = self._process_count_flag(launcher)
        if plan.executable.process_count is not None and process_count_flag is not None:
            launcher_command.extend([process_count_flag, str(plan.executable.process_count)])
        launcher_command.extend(plan.executable.launcher_args)
        return launcher_command

    def _process_count_flag(self, launcher: str) -> str | None:
        if launcher in _LAUNCHER_PROCESS_COUNT_FLAGS:
            return _LAUNCHER_PROCESS_COUNT_FLAGS[launcher]
        raise NotImplementedError(f"Unsupported JEDI launcher: {launcher}")

    def _reject_duplicate_process_count_args(self, launcher: str, launcher_args: list[str]) -> None:
        if launcher == "direct":
            return
        for arg in launcher_args:
            if self._is_process_count_arg(launcher, arg):
                raise ValueError(
                    "launcher_args must not include process-count flags; use executable.process_count"
                )

    def _is_process_count_arg(self, launcher: str, arg: str) -> bool:
        patterns = _PROCESS_COUNT_FLAG_PATTERNS.get(launcher, ())
        return any(pattern.match(arg) for pattern in patterns)

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
        diagnostic_files = self._discover_files(run_dir, plan.expected_diagnostics)
        reference_files = self._discover_files(run_dir, plan.expected_references)
        parsed_summary = self._augment_result_summary(
            result_summary,
            scientific_check=plan.scientific_check,
            diagnostic_files=diagnostic_files,
            candidate_id=plan.candidate_id,
            graph_version_id=plan.graph_version_id,
            session_id=plan.session_id,
            audit_refs=plan.audit_refs,
        )
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
            reference_files=reference_files,
            working_directory=str(run_dir),
            status=status,
            result_summary=parsed_summary,
        )

    def _augment_result_summary(
        self,
        result_summary: dict[str, object],
        *,
        scientific_check: str,
        diagnostic_files: list[str],
        candidate_id: str | None,
        graph_version_id: int | None,
        session_id: str | None,
        audit_refs: list[str],
    ) -> dict[str, object]:
        summary = {
            **result_summary,
            "scientific_check": scientific_check,
            "candidate_id": candidate_id,
            "graph_version_id": graph_version_id,
            "session_id": session_id,
            "audit_refs": list(audit_refs),
        }
        if scientific_check != "rms_improves":
            return summary

        for diagnostic_path in diagnostic_files:
            path = Path(diagnostic_path)
            if path.name != "departures.json":
                continue
            try:
                departures = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            observation_minus_analysis = departures.get("rms_observation_minus_analysis")
            observation_minus_background = departures.get("rms_observation_minus_background")
            if isinstance(observation_minus_analysis, int | float):
                summary["rms_observation_minus_analysis"] = float(observation_minus_analysis)
            if isinstance(observation_minus_background, int | float):
                summary["rms_observation_minus_background"] = float(observation_minus_background)
            break
        return summary

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
