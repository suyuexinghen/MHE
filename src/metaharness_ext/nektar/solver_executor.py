from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.capabilities import CAP_NEKTAR_SOLVE_ADR, CAP_NEKTAR_SOLVE_INCNS
from metaharness_ext.nektar.contracts import (
    FilterOutputSummary,
    NektarRunArtifact,
    NektarRunStatus,
    NektarSessionPlan,
)
from metaharness_ext.nektar.slots import SOLVER_EXECUTOR_SLOT
from metaharness_ext.nektar.types import NektarAdrEqType, NektarIncnsEqType, NektarSolverFamily
from metaharness_ext.nektar.xml_renderer import write_session_xml


class SolverExecutorComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(SOLVER_EXECUTOR_SLOT)
        api.declare_input("plan", "NektarSessionPlan")
        api.declare_output("run", "NektarRunArtifact", mode="sync")
        api.provide_capability(CAP_NEKTAR_SOLVE_ADR)
        api.provide_capability(CAP_NEKTAR_SOLVE_INCNS)

    def execute_plan(self, plan: NektarSessionPlan) -> NektarRunArtifact:
        self._validate_equation_type(plan)
        run_dir = self._resolve_run_dir(plan)
        mesh_path = self._resolve_mesh_path(plan)
        if not plan.render_geometry_inline and mesh_path is None:
            session_path = run_dir / plan.session_file_name
            log_files = self._write_solver_logs(
                run_dir,
                stdout_text="",
                stderr_text="External mesh overlay mode requires an existing mesh.source_path.",
            )
            return self._build_run_artifact(
                plan,
                session_path=session_path,
                mesh_path=None,
                field_files=[],
                checkpoint_files=[],
                log_files=log_files,
                status="unavailable",
                result_summary={
                    "mode": "solver_unavailable",
                    "equation_type": plan.equation_type.value,
                    "solver_binary": plan.solver_binary,
                    "resolved_binary": None,
                    "command": [],
                    "cwd": str(run_dir),
                    "ran_solver": False,
                    "runtime_process_mode": "stdlib_subprocess_phase1",
                    "exit_code": None,
                    "fallback_reason": "mesh_source_not_found",
                    "session_file": str(session_path),
                },
            )

        session_path = write_session_xml(plan, run_dir / plan.session_file_name)
        resolved_binary = self._resolve_solver_binary(plan)
        if resolved_binary is None:
            log_files = self._write_solver_logs(
                run_dir,
                stdout_text="",
                stderr_text=f"Solver binary not found: {plan.solver_binary}",
            )
            return self._build_run_artifact(
                plan,
                session_path=session_path,
                mesh_path=mesh_path,
                field_files=[],
                checkpoint_files=[],
                log_files=log_files,
                status="unavailable",
                result_summary={
                    "mode": "solver_unavailable",
                    "equation_type": plan.equation_type.value,
                    "solver_binary": plan.solver_binary,
                    "resolved_binary": None,
                    "command": [],
                    "cwd": str(run_dir),
                    "ran_solver": False,
                    "runtime_process_mode": "stdlib_subprocess_phase1",
                    "exit_code": None,
                    "fallback_reason": "solver_binary_not_found",
                    "session_file": str(session_path),
                },
            )

        command = self._build_solver_command(
            plan,
            session_path=session_path,
            resolved_binary=resolved_binary,
            mesh_path=mesh_path,
        )
        timeout_seconds = self._resolve_solver_timeout(plan)
        try:
            result = self._run_solver(command, cwd=run_dir, timeout_seconds=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n\n"
            stderr_text += f"Solver timed out after {timeout_seconds} seconds."
            log_files = self._write_solver_logs(
                run_dir,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
            )
            field_files, checkpoint_files = self._discover_outputs(run_dir)
            error_norms = self._extract_error_norms(stdout_text, stderr_text)
            step_metrics = self._extract_step_metrics(stdout_text, stderr_text)
            artifact = self._build_run_artifact(
                plan,
                session_path=session_path,
                mesh_path=mesh_path,
                field_files=field_files,
                checkpoint_files=checkpoint_files,
                log_files=log_files,
                status="failed",
                error_norms=error_norms,
                result_summary={
                    "mode": "solver_executed",
                    "equation_type": plan.equation_type.value,
                    "solver_binary": plan.solver_binary,
                    "resolved_binary": resolved_binary,
                    "command": command,
                    "cwd": str(run_dir),
                    "ran_solver": True,
                    "runtime_process_mode": "stdlib_subprocess_phase1",
                    "exit_code": None,
                    "timeout_seconds": timeout_seconds,
                    "fallback_reason": "solver_timeout",
                    "session_file": str(session_path),
                },
            )
            artifact.filter_output.metrics.update(step_metrics)
            return artifact

        log_files = self._write_solver_logs(
            run_dir,
            stdout_text=result.stdout,
            stderr_text=result.stderr,
        )
        field_files, checkpoint_files = self._discover_outputs(run_dir)
        error_norms = self._extract_error_norms(result.stdout, result.stderr)
        step_metrics = self._extract_step_metrics(result.stdout, result.stderr)
        status: NektarRunStatus = "completed" if result.returncode == 0 else "failed"
        artifact = self._build_run_artifact(
            plan,
            session_path=session_path,
            mesh_path=mesh_path,
            field_files=field_files,
            checkpoint_files=checkpoint_files,
            log_files=log_files,
            status=status,
            error_norms=error_norms,
            result_summary={
                "mode": "solver_executed",
                "equation_type": plan.equation_type.value,
                "solver_binary": plan.solver_binary,
                "resolved_binary": resolved_binary,
                "command": command,
                "cwd": str(run_dir),
                "ran_solver": True,
                "runtime_process_mode": "stdlib_subprocess_phase1",
                "exit_code": result.returncode,
                "timeout_seconds": timeout_seconds,
                "fallback_reason": None,
                "session_file": str(session_path),
            },
        )
        artifact.filter_output.metrics.update(step_metrics)
        return artifact

    def _validate_equation_type(self, plan: NektarSessionPlan) -> None:
        if plan.solver_family == NektarSolverFamily.ADR and not isinstance(
            plan.equation_type, NektarAdrEqType
        ):
            raise ValueError("ADR family requires NektarAdrEqType")
        if plan.solver_family == NektarSolverFamily.INCNS and not isinstance(
            plan.equation_type, NektarIncnsEqType
        ):
            raise ValueError("IncNS family requires NektarIncnsEqType")

    def _resolve_run_dir(self, plan: NektarSessionPlan) -> Path:
        runtime = getattr(self, "_runtime", None)
        if runtime is None or runtime.storage_path is None:
            raise RuntimeError("SolverExecutorComponent requires runtime.storage_path")
        self._validate_task_id(plan.task_id)
        run_dir = runtime.storage_path / "nektar_runs" / plan.task_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _validate_task_id(self, task_id: str) -> None:
        if not task_id or ".." in task_id or "/" in task_id or "\\" in task_id:
            raise ValueError(f"Invalid task_id: {task_id!r}")

    def _resolve_mesh_path(self, plan: NektarSessionPlan) -> Path | None:
        if plan.mesh.source_path is None:
            return None
        mesh_path = Path(plan.mesh.source_path).expanduser()
        if not mesh_path.is_absolute():
            mesh_path = mesh_path.resolve()
        if not mesh_path.exists():
            return None
        return mesh_path

    def _resolve_solver_binary(self, plan: NektarSessionPlan) -> str | None:
        candidate = Path(plan.solver_binary)
        if candidate.is_absolute() and candidate.exists():
            return str(candidate)
        return shutil.which(plan.solver_binary)

    def _resolve_solver_timeout(self, plan: NektarSessionPlan) -> float:
        timeout_value = plan.parameters.get("SolverTimeout", 600)
        return float(timeout_value)

    def _build_solver_command(
        self,
        plan: NektarSessionPlan,
        *,
        session_path: Path,
        resolved_binary: str,
        mesh_path: Path | None,
    ) -> list[str]:
        command = [resolved_binary]
        if not plan.render_geometry_inline:
            if mesh_path is None:
                raise ValueError("External mesh overlay mode requires a resolved mesh path")
            command.append(str(mesh_path))
        command.append(str(session_path))
        return command

    def _run_solver(
        self,
        command: list[str],
        *,
        cwd: Path,
        timeout_seconds: float,
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

    def _write_solver_logs(self, run_dir: Path, *, stdout_text: str, stderr_text: str) -> list[str]:
        stdout_path = run_dir / "solver.stdout.log"
        stderr_path = run_dir / "solver.stderr.log"
        combined_path = run_dir / "solver.log"
        stdout_path.write_text(stdout_text)
        stderr_path.write_text(stderr_text)
        combined_text = stdout_text
        if stdout_text and stderr_text:
            combined_text += "\n\n"
        combined_text += stderr_text
        combined_path.write_text(combined_text)
        return [str(combined_path), str(stdout_path), str(stderr_path)]

    def _discover_outputs(self, run_dir: Path) -> tuple[list[str], list[str]]:
        field_files = sorted(str(path) for path in run_dir.glob("*.fld") if path.is_file())
        checkpoint_files = sorted(str(path) for path in run_dir.glob("*.chk") if path.is_file())
        return field_files, checkpoint_files

    def _build_run_artifact(
        self,
        plan: NektarSessionPlan,
        *,
        session_path: Path,
        mesh_path: Path | None,
        field_files: list[str],
        checkpoint_files: list[str],
        log_files: list[str],
        status: NektarRunStatus,
        error_norms: dict[str, float] | None = None,
        result_summary: dict[str, object],
    ) -> NektarRunArtifact:
        return NektarRunArtifact(
            run_id=f"run::{plan.task_id}",
            task_id=plan.task_id,
            solver_family=plan.solver_family,
            solver_binary=plan.solver_binary,
            session_files=[str(session_path)],
            mesh_files=[str(mesh_path)] if mesh_path is not None else [],
            field_files=field_files,
            log_files=log_files,
            filter_output=FilterOutputSummary(
                checkpoint_files=checkpoint_files,
                error_norms=error_norms or {},
            ),
            result_summary=result_summary,
            postprocess_plan=list(plan.postprocess_plan),
            status=status,
        )

    _COORDINATE_VARIABLES = frozenset({"x", "y", "z"})

    def _extract_error_norms(self, stdout_text: str, stderr_text: str) -> dict[str, float]:
        norms: dict[str, float] = {}
        combined = f"{stdout_text}\n{stderr_text}"
        for match in re.finditer(
            r"L\s*(2|inf)\s+error\s+\(variable\s+(\w+)\)\s*:\s*([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)",
            combined,
        ):
            norm_type = "l2" if match.group(1) == "2" else "linf"
            var = match.group(2).lower()
            if var in self._COORDINATE_VARIABLES:
                continue
            key = f"{norm_type}_error_{var}"
            norms[key] = float(match.group(3))
        return norms

    def _extract_step_metrics(self, stdout_text: str, stderr_text: str) -> dict[str, float | str]:
        metrics: dict[str, float | str] = {}
        combined = f"{stdout_text}\n{stderr_text}"
        step_matches = list(
            re.finditer(
                r"Steps:\s+(\d+)\s+Time:\s+([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)\s+CPU Time:\s+([0-9]*\.?[0-9]+)s",
                combined,
            )
        )
        if step_matches:
            last = step_matches[-1]
            metrics["total_steps"] = int(last.group(1))
            metrics["final_time"] = float(last.group(2))
            metrics["cpu_time"] = float(last.group(3))
        wall_match = re.search(
            r"Total Computation Time\s*=\s*([0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?)s",
            combined,
        )
        if wall_match:
            metrics["wall_time"] = float(wall_match.group(1))
        return metrics
