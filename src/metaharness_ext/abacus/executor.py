from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.abacus.capabilities import (
    CAP_ABACUS_MD_RUN,
    CAP_ABACUS_NSCF_RUN,
    CAP_ABACUS_RELAX_RUN,
    CAP_ABACUS_SCF_RUN,
)
from metaharness_ext.abacus.contracts import AbacusRunArtifact, AbacusRunPlan
from metaharness_ext.abacus.slots import ABACUS_EXECUTOR_SLOT


class AbacusExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self, runtime: ComponentRuntime) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(ABACUS_EXECUTOR_SLOT)
        api.declare_input("plan", "AbacusRunPlan")
        api.declare_output("run", "AbacusRunArtifact", mode="sync")
        api.provide_capability(CAP_ABACUS_SCF_RUN)
        api.provide_capability(CAP_ABACUS_NSCF_RUN)
        api.provide_capability(CAP_ABACUS_RELAX_RUN)
        api.provide_capability(CAP_ABACUS_MD_RUN)

    def execute_plan(self, plan: AbacusRunPlan) -> AbacusRunArtifact:
        run_dir = self._resolve_run_dir(plan)
        run_dir.mkdir(parents=True, exist_ok=True)

        prepared_inputs = self._write_inputs(plan, run_dir)

        resolved_binary = self._resolve_binary(plan.executable.binary_name)
        if resolved_binary is None:
            stdout_path, stderr_path = self._write_logs(
                run_dir,
                stdout_text="",
                stderr_text=f"ABACUS binary not found: {plan.executable.binary_name}",
            )
            return self._build_artifact(
                plan,
                run_dir=run_dir,
                command=[plan.executable.binary_name],
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
        timeout_seconds = plan.executable.timeout_seconds
        try:
            result = self._run_command(command, cwd=run_dir, timeout_seconds=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n\n"
            stderr_text += f"ABACUS command timed out after {timeout_seconds} seconds."
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

        output_root = run_dir / (plan.output_root or f"OUT.{plan.suffix}")
        output_files = self._discover_outputs(run_dir, plan)
        diagnostic_files = self._discover_diagnostics(run_dir, plan)
        structure_files = self._discover_structure_files(run_dir, output_root)

        return self._build_artifact(
            plan,
            run_dir=run_dir,
            command=command,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            return_code=result.returncode,
            status=status,
            prepared_inputs=prepared_inputs,
            output_root=str(output_root) if output_root.exists() else None,
            output_files=output_files,
            diagnostic_files=diagnostic_files,
            structure_files=structure_files,
            result_summary={
                "fallback_reason": None,
                "exit_code": result.returncode,
                "esolver_type": plan.esolver_type,
                "pot_file": plan.pot_file,
                "environment_prerequisites": plan.environment_prerequisites,
            },
        )

    def _resolve_run_dir(self, plan: AbacusRunPlan) -> Path:
        runtime = getattr(self, "_runtime", None)
        if runtime is not None and runtime.storage_path is not None:
            run_dir = runtime.storage_path / "abacus_runs" / plan.task_id / plan.run_id
        else:
            run_dir = Path(plan.working_directory).expanduser()
        return run_dir

    def _write_inputs(self, plan: AbacusRunPlan, run_dir: Path) -> list[str]:
        prepared: list[str] = []
        input_path = run_dir / "INPUT"
        input_path.write_text(plan.input_content)
        prepared.append(str(input_path))

        stru_path = run_dir / "STRU"
        stru_path.write_text(plan.structure_content)
        prepared.append(str(stru_path))

        if plan.kpoints_content:
            kpt_path = run_dir / "KPT"
            kpt_path.write_text(plan.kpoints_content)
            prepared.append(str(kpt_path))

        return prepared

    def _resolve_binary(self, binary_name: str) -> str | None:
        candidate = Path(binary_name).expanduser()
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        if candidate.exists():
            return str(candidate.resolve())
        return shutil.which(binary_name)

    def _build_command(
        self,
        plan: AbacusRunPlan,
        resolved_binary: str,
        resolved_launcher: str | None,
    ) -> list[str]:
        base_command = [resolved_binary]
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
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )

    def _write_logs(
        self,
        run_dir: Path,
        *,
        stdout_text: str,
        stderr_text: str,
    ) -> tuple[str, str]:
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

    def _discover_outputs(self, run_dir: Path, plan: AbacusRunPlan) -> list[str]:
        outputs: list[str] = []
        out_dir = run_dir / (plan.output_root or f"OUT.{plan.suffix}")
        if out_dir.exists():
            outputs.append(str(out_dir))
            for path in out_dir.rglob("*"):
                if path.is_file():
                    outputs.append(str(path))
        return outputs

    def _discover_diagnostics(self, run_dir: Path, plan: AbacusRunPlan) -> list[str]:
        diagnostics: list[str] = []
        for pattern in plan.expected_logs:
            for path in run_dir.rglob(pattern):
                if path.is_file():
                    diagnostics.append(str(path))
        return diagnostics

    def _discover_structure_files(self, run_dir: Path, output_root: Path) -> list[str]:
        structure_files: list[str] = []
        for root in (run_dir, output_root):
            if not root.exists():
                continue
            for pattern in ("STRU*", "*.cif"):
                for path in root.rglob(pattern):
                    if path.is_file() and str(path) not in structure_files:
                        structure_files.append(str(path))
        return structure_files

    def _build_artifact(
        self,
        plan: AbacusRunPlan,
        *,
        run_dir: Path,
        command: list[str],
        stdout_path: str | None,
        stderr_path: str | None,
        return_code: int | None,
        status: str,
        prepared_inputs: list[str],
        output_root: str | None = None,
        output_files: list[str] | None = None,
        diagnostic_files: list[str] | None = None,
        structure_files: list[str] | None = None,
        result_summary: dict[str, object],
    ) -> AbacusRunArtifact:
        return AbacusRunArtifact(
            task_id=plan.task_id,
            run_id=plan.run_id,
            application_family=plan.application_family,
            command=command,
            return_code=return_code,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            prepared_inputs=prepared_inputs,
            output_root=output_root,
            output_files=output_files or [],
            diagnostic_files=diagnostic_files or [],
            structure_files=structure_files or [],
            working_directory=str(run_dir),
            status=status,  # type: ignore[arg-type]
            result_summary=result_summary,
        )
