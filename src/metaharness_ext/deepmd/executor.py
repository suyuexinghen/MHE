from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.deepmd.capabilities import (
    CAP_DEEPMD_MODEL_COMPRESS,
    CAP_DEEPMD_MODEL_DEVI,
    CAP_DEEPMD_MODEL_FREEZE,
    CAP_DEEPMD_MODEL_TEST,
    CAP_DEEPMD_NEIGHBOR_STAT,
    CAP_DEEPMD_TRAIN_RUN,
    CAP_DPGEN_AUTOTEST,
    CAP_DPGEN_RUN,
    CAP_DPGEN_SIMPLIFY,
)
from metaharness_ext.deepmd.collector import DPGenIterationCollector
from metaharness_ext.deepmd.contracts import DeepMDRunArtifact, DeepMDRunPlan
from metaharness_ext.deepmd.diagnostics import build_diagnostic_summary
from metaharness_ext.deepmd.slots import DEEPMD_EXECUTOR_SLOT
from metaharness_ext.deepmd.workspace import DeepMDWorkspacePreparer, WorkspacePreparationError


class DeepMDExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime
        self._workspace_preparer = DeepMDWorkspacePreparer()
        self._dpgen_collector = DPGenIterationCollector()

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(DEEPMD_EXECUTOR_SLOT)
        api.declare_input("plan", "DeepMDRunPlan")
        api.declare_output("run", "DeepMDRunArtifact", mode="sync")
        api.provide_capability(CAP_DEEPMD_TRAIN_RUN)
        api.provide_capability(CAP_DEEPMD_MODEL_FREEZE)
        api.provide_capability(CAP_DEEPMD_MODEL_TEST)
        api.provide_capability(CAP_DEEPMD_MODEL_COMPRESS)
        api.provide_capability(CAP_DEEPMD_MODEL_DEVI)
        api.provide_capability(CAP_DEEPMD_NEIGHBOR_STAT)
        api.provide_capability(CAP_DPGEN_RUN)
        api.provide_capability(CAP_DPGEN_SIMPLIFY)
        api.provide_capability(CAP_DPGEN_AUTOTEST)

    def execute_plan(self, plan: DeepMDRunPlan) -> DeepMDRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        try:
            workspace_files = self._prepare_workspace(plan, run_dir)
        except WorkspacePreparationError as error:
            stdout_path, stderr_path = self._write_logs(
                run_dir, stdout_text="", stderr_text=str(error)
            )
            return self._build_artifact(
                plan,
                command=[plan.executable.binary_name, plan.execution_mode],
                run_dir=run_dir,
                workspace_files=[],
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                return_code=None,
                status="failed",
                result_summary={"fallback_reason": "workspace_prepare_failed", "exit_code": None},
            )

        self._materialize_plan_files(plan, run_dir)

        resolved_binary = self._resolve_binary(plan)
        if resolved_binary is None:
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text="",
                stderr_text=f"DeepMD binary not found: {plan.executable.binary_name}",
            )
            return self._build_artifact(
                plan,
                command=[plan.executable.binary_name, plan.execution_mode],
                run_dir=run_dir,
                workspace_files=workspace_files,
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
                command=command,
                run_dir=run_dir,
                workspace_files=workspace_files,
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
            command=command,
            run_dir=run_dir,
            workspace_files=workspace_files,
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
        run_dir = runtime.storage_path / ".runs" / "deepmd" / plan.task_id / plan.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _prepare_workspace(self, plan: DeepMDRunPlan, run_dir: Path) -> list[str]:
        return self._workspace_preparer.prepare(plan, run_dir)

    def _validate_task_id(self, task_id: str) -> None:
        if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
            raise ValueError(f"Invalid task_id: {task_id!r}")

    def _materialize_plan_files(self, plan: DeepMDRunPlan, run_dir: Path) -> list[str]:
        if plan.input_json_path is not None:
            (run_dir / "input.json").write_text(
                json.dumps(plan.input_json, indent=2, sort_keys=True) + "\n"
            )
        if plan.param_json_path is not None:
            (run_dir / "param.json").write_text(
                json.dumps(plan.param_json, indent=2, sort_keys=True) + "\n"
            )
        if plan.machine_json_path is not None:
            (run_dir / "machine.json").write_text(
                json.dumps(plan.machine_json, indent=2, sort_keys=True) + "\n"
            )
        return self._discover_files(run_dir, ["input.json", "param.json", "machine.json"])

    def _resolve_binary(self, plan: DeepMDRunPlan) -> str | None:
        candidate = Path(plan.executable.binary_name)
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        return shutil.which(plan.executable.binary_name)

    def _build_command(self, plan: DeepMDRunPlan, resolved_binary: str) -> list[str]:
        if plan.execution_mode == "dpgen_run":
            return [resolved_binary, "run", "param.json", "machine.json"]
        if plan.execution_mode == "dpgen_simplify":
            return [resolved_binary, "simplify", "param.json", "machine.json"]
        if plan.execution_mode == "dpgen_autotest":
            return [resolved_binary, "autotest", "param.json", "machine.json"]

        command = [resolved_binary, plan.execution_mode]
        if plan.execution_mode == "train":
            command.append("input.json")
        elif plan.execution_mode == "freeze":
            command.extend(["-o", "frozen_model.pb"])
        elif plan.execution_mode == "test":
            if not plan.dataset_paths:
                raise ValueError("test mode requires at least one dataset path")
            command.extend(
                [
                    "-m",
                    plan.mode_inputs.model_path or "frozen_model.pb",
                    "-s",
                    plan.dataset_paths[0],
                    "-n",
                    str(plan.mode_inputs.sample_count or 10),
                ]
            )
        elif plan.execution_mode == "compress":
            command.extend(
                [
                    "-i",
                    plan.mode_inputs.model_path or "frozen_model.pb",
                    "-o",
                    plan.mode_inputs.output_model_path or "compressed_model.pb",
                ]
            )
        elif plan.execution_mode == "model_devi":
            if not plan.dataset_paths:
                raise ValueError("model_devi mode requires at least one dataset path")
            command.extend(
                [
                    "-m",
                    plan.mode_inputs.model_path or "frozen_model.pb",
                    "-s",
                    plan.dataset_paths[0],
                ]
            )
        elif plan.execution_mode == "neighbor_stat":
            if not plan.dataset_paths:
                raise ValueError("neighbor_stat mode requires at least one dataset path")
            command.extend(["-s", plan.dataset_paths[0]])
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
        command: list[str],
        run_dir: Path,
        workspace_files: list[str],
        stdout_path: str,
        stderr_path: str,
        return_code: int | None,
        status: str,
        result_summary: dict[str, object],
    ) -> DeepMDRunArtifact:
        checkpoint_files = self._discover_files(run_dir, ["checkpoint", "model.ckpt*"])
        model_files = self._discover_files(
            run_dir, ["*.pb", "graph.pb", "frozen_model.pb", "compressed_model.pb"]
        )
        diagnostic_files = self._discover_files(
            run_dir,
            [
                "lcurve.out",
                "train.log",
                "test.*",
                "result.*",
                "results.*",
                "*.out",
                "model_devi*",
                "neighbor_stat*",
                "record.dpgen",
            ],
        )
        summary = build_diagnostic_summary(
            run_dir, diagnostic_files, stdout_path, properties=plan.properties
        )
        if plan.execution_mode in {"dpgen_run", "dpgen_simplify"}:
            summary.dpgen_collection = self._dpgen_collector.collect(run_dir)
            for message in summary.dpgen_collection.messages:
                if message not in summary.messages:
                    summary.messages.append(message)
        return DeepMDRunArtifact(
            task_id=plan.task_id,
            run_id=plan.run_id,
            application_family=plan.application_family,
            execution_mode=plan.execution_mode,
            command=command,
            return_code=return_code,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            working_directory=str(run_dir),
            workspace_files=workspace_files,
            checkpoint_files=checkpoint_files,
            model_files=model_files,
            diagnostic_files=diagnostic_files,
            summary=summary,
            status=status,
            result_summary=result_summary,
        )

    def _discover_files(self, run_dir: Path, patterns: list[str]) -> list[str]:
        files: list[str] = []
        seen: set[str] = set()
        for pattern in patterns:
            for path in sorted(run_dir.rglob(pattern)):
                if not path.is_file():
                    continue
                path_str = str(path)
                if path_str in seen:
                    continue
                seen.add(path_str)
                files.append(path_str)
        return files
