from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import (
    CAP_DEEPMD_MODEL_FREEZE,
    CAP_DEEPMD_MODEL_TEST,
    CAP_DEEPMD_TRAIN_RUN,
)
from metaharness_ext.deepmd.contracts import (
    DeepMDDiagnosticSummary,
    DeepMDRunArtifact,
    DeepMDRunPlan,
)
from metaharness_ext.deepmd.slots import DEEPMD_EXECUTOR_SLOT


class DeepMDExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_EXECUTOR_SLOT)
        api.declare_input("plan", "DeepMDRunPlan")
        api.declare_output("run", "DeepMDRunArtifact", mode="sync")
        api.provide_capability(CAP_DEEPMD_TRAIN_RUN)
        api.provide_capability(CAP_DEEPMD_MODEL_FREEZE)
        api.provide_capability(CAP_DEEPMD_MODEL_TEST)

    def execute_plan(self, plan: DeepMDRunPlan) -> DeepMDRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        input_json_path = run_dir / "input.json"
        input_json_path.write_text(json.dumps(plan.input_json, indent=2, sort_keys=True) + "\n")

        resolved_binary = self._resolve_binary(plan)
        if resolved_binary is None:
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text="",
                stderr_text=f"DeepMD binary not found: {plan.executable.binary_name}",
            )
            return self._build_artifact(
                plan,
                run_dir=run_dir,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                return_code=None,
                status="unavailable",
                result_summary={"fallback_reason": "binary_not_found", "exit_code": None},
            )

        command = self._build_command(plan, resolved_binary)
        timeout_seconds = plan.executable.timeout_seconds
        try:
            result = self._run_command(command, cwd=run_dir, timeout_seconds=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n\n"
            stderr_text += f"DeepMD command timed out after {timeout_seconds} seconds."
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
            )
            return self._build_artifact(
                plan,
                run_dir=run_dir,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                return_code=None,
                status="failed",
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
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            return_code=result.returncode,
            status=status,
            result_summary={"fallback_reason": None, "exit_code": result.returncode},
        )

    def _resolve_run_dir(self, plan: DeepMDRunPlan) -> Path:
        runtime = getattr(self, "_runtime", None)
        if runtime is None or runtime.storage_path is None:
            raise RuntimeError("DeepMDExecutorComponent requires runtime.storage_path")
        self._validate_task_id(plan.task_id)
        run_dir = runtime.storage_path / "deepmd_runs" / plan.task_id / plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _validate_task_id(self, task_id: str) -> None:
        if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
            raise ValueError(f"Invalid task_id: {task_id!r}")

    def _resolve_binary(self, plan: DeepMDRunPlan) -> str | None:
        candidate = Path(plan.executable.binary_name)
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        return shutil.which(plan.executable.binary_name)

    def _build_command(self, plan: DeepMDRunPlan, resolved_binary: str) -> list[str]:
        command = [resolved_binary, plan.execution_mode]
        if plan.execution_mode == "train":
            command.append("input.json")
        elif plan.execution_mode == "freeze":
            command.extend(["-o", "frozen_model.pb"])
        elif plan.execution_mode == "test":
            command.extend(["-m", "frozen_model.pb", "-s", plan.dataset_paths[0], "-n", "10"])
        return command

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
        plan: DeepMDRunPlan,
        *,
        run_dir: Path,
        stdout_path: str,
        stderr_path: str,
        return_code: int | None,
        status: str,
        result_summary: dict[str, object],
    ) -> DeepMDRunArtifact:
        checkpoint_files = self._discover_files(run_dir, ["checkpoint", "model.ckpt*"])
        model_files = self._discover_files(run_dir, ["*.pb", "graph.pb", "frozen_model.pb"])
        diagnostic_files = self._discover_files(run_dir, ["lcurve.out", "test.*", "results.*"])
        summary = self._build_summary(run_dir, diagnostic_files, stdout_path)
        return DeepMDRunArtifact(
            task_id=plan.task_id,
            run_id=plan.run_id,
            execution_mode=plan.execution_mode,
            command=self._build_command(
                plan, self._resolve_binary(plan) or plan.executable.binary_name
            ),
            return_code=return_code,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            working_directory=str(run_dir),
            checkpoint_files=checkpoint_files,
            model_files=model_files,
            diagnostic_files=diagnostic_files,
            summary=summary,
            status=status,
            result_summary=result_summary,
        )

    def _discover_files(self, run_dir: Path, patterns: list[str]) -> list[str]:
        files: list[str] = []
        for pattern in patterns:
            files.extend(str(path) for path in sorted(run_dir.glob(pattern)) if path.is_file())
        return files

    def _build_summary(
        self,
        run_dir: Path,
        diagnostic_files: list[str],
        stdout_path: str,
    ) -> DeepMDDiagnosticSummary:
        summary = DeepMDDiagnosticSummary()
        lcurve_path = run_dir / "lcurve.out"
        if lcurve_path.exists():
            summary.learning_curve_path = str(lcurve_path)
            self._parse_lcurve(lcurve_path, summary)
        stdout_file = Path(stdout_path)
        if stdout_file.exists():
            self._parse_test_metrics(stdout_file.read_text(), summary)
        for diagnostic in diagnostic_files:
            if diagnostic not in summary.messages:
                summary.messages.append(f"Discovered diagnostic: {Path(diagnostic).name}")
        return summary

    def _parse_lcurve(self, path: Path, summary: DeepMDDiagnosticSummary) -> None:
        lines = [
            line.strip()
            for line in path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        if not lines:
            return
        last = lines[-1].split()
        if last:
            try:
                summary.last_step = int(float(last[0]))
            except ValueError:
                pass
        if len(last) >= 3:
            try:
                summary.rmse_e_trn = float(last[1])
                summary.rmse_f_trn = float(last[2])
            except ValueError:
                return

    def _parse_test_metrics(self, text: str, summary: DeepMDDiagnosticSummary) -> None:
        patterns = {
            "rmse_e": r"rmse[_ ]e(?:nergy)?\s*[=:]\s*([0-9.eE+-]+)",
            "rmse_f": r"rmse[_ ]f(?:orce)?\s*[=:]\s*([0-9.eE+-]+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary.test_metrics[key] = float(match.group(1))
