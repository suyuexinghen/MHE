from __future__ import annotations

import glob
import shutil
import subprocess
import uuid
from pathlib import Path

from metaharness_ext.boutpp.contracts import BoutPPRunArtifact, BoutPPRunPlan


class BoutPPExecutorComponent:
    def __init__(self, workspace_root: str | None = None):
        self._workspace_root = Path(workspace_root) if workspace_root else Path(".runs/boutpp")

    def execute(self, plan: BoutPPRunPlan) -> BoutPPRunArtifact:
        workspace = self._workspace_root / plan.run_id
        data_dir = workspace / plan.spec.output.data_dir
        artifact = BoutPPRunArtifact(
            artifact_id=f"boutpp-artifact-{uuid.uuid4().hex[:12]}",
            run_id=plan.run_id,
            task_id=plan.task_id,
            plan_ref=plan.plan_id,
            workspace_dir=str(workspace),
            data_dir=str(data_dir),
        )
        unavailable = self._unavailable_reason(plan)
        if unavailable:
            artifact.status = "unavailable"
            artifact.error_message = unavailable
            artifact.missing_artifacts.append("executable")
            return artifact
        workspace.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        self._copy_source_data(plan, data_dir)
        (data_dir / "BOUT.inp").write_text(plan.bout_inp_content)
        command = self._runtime_command(plan, workspace)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=plan.spec.timeout_seconds,
                cwd=str(workspace),
            )
        except subprocess.TimeoutExpired as error:
            artifact.status = "timeout"
            artifact.return_code = -1
            artifact.error_message = f"Execution timed out after {plan.spec.timeout_seconds}s"
            artifact.stdout_excerpt = self._excerpt(error.stdout)
            artifact.stderr_excerpt = self._excerpt(error.stderr)
            self._discover_artifacts(plan, artifact)
            return artifact
        except OSError as error:
            artifact.status = "failed"
            artifact.return_code = -2
            artifact.error_message = f"OS error: {error}"
            self._discover_artifacts(plan, artifact)
            return artifact
        artifact.return_code = result.returncode
        artifact.stdout_excerpt = self._excerpt(result.stdout)
        artifact.stderr_excerpt = self._excerpt(result.stderr)
        artifact.status = "completed" if result.returncode == 0 else "failed"
        if result.returncode != 0:
            artifact.error_message = result.stderr[:2000] if result.stderr else f"Exit code {result.returncode}"
        self._discover_artifacts(plan, artifact)
        return artifact

    def _copy_source_data(self, plan: BoutPPRunPlan, data_dir: Path) -> None:
        source_case_dir = plan.spec.source_case_dir
        if not source_case_dir:
            return
        source_data = Path(source_case_dir) / plan.spec.output.data_dir
        if source_data.is_dir():
            shutil.copytree(source_data, data_dir, dirs_exist_ok=True)

    def _runtime_command(self, plan: BoutPPRunPlan, workspace: Path) -> list[str]:
        command = list(plan.command)
        executable_index = 3 + len(plan.spec.mpi.extra_args) if plan.spec.mpi.launcher_mode == "mpi" else 0
        executable = Path(command[executable_index])
        if executable.is_absolute():
            return command
        source_case_dir = plan.spec.source_case_dir
        candidates = [workspace / executable]
        if source_case_dir:
            candidates.append(Path(source_case_dir) / executable)
        for candidate in candidates:
            if candidate.exists():
                command[executable_index] = str(candidate.resolve())
                return command
        resolved = shutil.which(str(executable))
        if resolved:
            command[executable_index] = resolved
        return command

    def _unavailable_reason(self, plan: BoutPPRunPlan) -> str | None:
        command = plan.command
        if plan.spec.mpi.launcher_mode == "mpi" and not shutil.which(command[0]):
            return f"MPI launcher not found: {command[0]}"
        executable_index = 3 + len(plan.spec.mpi.extra_args) if plan.spec.mpi.launcher_mode == "mpi" else 0
        executable = Path(command[executable_index])
        if executable.is_absolute() and executable.exists():
            return None
        if shutil.which(str(executable)):
            return None
        source_case_dir = plan.spec.source_case_dir
        if source_case_dir and (Path(source_case_dir) / executable).exists():
            return None
        return f"Executable not found: {executable}"

    def _discover_artifacts(self, plan: BoutPPRunPlan, artifact: BoutPPRunArtifact) -> None:
        settings = Path(artifact.data_dir or "") / plan.spec.output.settings_file
        if settings.exists():
            artifact.settings_file = str(settings)
        artifact.log_files = sorted(glob.glob(str(Path(artifact.data_dir or "") / plan.spec.output.log_glob)))
        artifact.dump_files = sorted(glob.glob(str(Path(artifact.data_dir or "") / plan.spec.output.dump_glob)))
        artifact.restart_files = sorted(glob.glob(str(Path(artifact.data_dir or "") / plan.spec.output.restart_glob)))
        missing = []
        if plan.spec.output.require_settings and not artifact.settings_file:
            missing.append("settings")
        if plan.spec.output.require_logs and not artifact.log_files:
            missing.append("logs")
        if plan.spec.output.require_dumps and not artifact.dump_files:
            missing.append("dumps")
        if plan.spec.output.require_restarts and not artifact.restart_files:
            missing.append("restarts")
        artifact.missing_artifacts = missing
        refs = [artifact.settings_file, *artifact.log_files, *artifact.dump_files, *artifact.restart_files]
        artifact.evidence_refs = [ref for ref in refs if ref]

    @staticmethod
    def _excerpt(value: str | bytes | None, limit: int = 2000) -> str | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode(errors="replace")
        return value[:limit]
