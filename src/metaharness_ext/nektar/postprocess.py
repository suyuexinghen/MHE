from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from metaharness.sdk.api import HarnessAPI
from metaharness.sdk.base import HarnessComponent
from metaharness.sdk.runtime import ComponentRuntime
from metaharness_ext.nektar.capabilities import CAP_NEKTAR_POSTPROCESS
from metaharness_ext.nektar.contracts import NektarRunArtifact
from metaharness_ext.nektar.slots import POSTPROCESS_SLOT
from metaharness_ext.nektar.types import NektarSolverFamily


class PostprocessComponent(HarnessComponent):
    async def activate(self, runtime: ComponentRuntime) -> None:
        self._runtime = runtime

    async def deactivate(self) -> None:
        self._runtime = None

    def declare_interface(self, api: HarnessAPI) -> None:
        api.bind_slot(POSTPROCESS_SLOT)
        api.declare_input("run", "NektarRunArtifact")
        api.declare_output("postprocessed_run", "NektarRunArtifact", mode="sync")
        api.provide_capability(CAP_NEKTAR_POSTPROCESS)

    def run_postprocess(self, artifact: NektarRunArtifact) -> NektarRunArtifact:
        updated = artifact.model_copy(deep=True)
        updated.filter_output.metrics.update(self._extract_solver_convergence_metrics(updated))
        steps = updated.postprocess_plan or []
        if not steps:
            updated.result_summary["postprocess"] = {
                "status": "skipped",
                "ran_fieldconvert": False,
                "fallback_reason": "no_postprocess_plan",
                "steps": [],
            }
            return updated

        run_dir = self._resolve_run_dir(updated)
        overall_status: str = "completed"
        step_results: list[dict[str, object]] = []
        for step in steps:
            step_result = self._execute_step(step, updated, run_dir)
            step_results.append(step_result)
            step_status = step_result["status"]
            if step_status in ("failed", "unavailable"):
                overall_status = step_status if overall_status != "failed" else "failed"

        updated.result_summary["postprocess"] = {
            "status": overall_status,
            "ran_fieldconvert": any(sr.get("ran_fieldconvert") for sr in step_results),
            "fallback_reason": next(
                (sr.get("fallback_reason") for sr in step_results if sr.get("fallback_reason")),
                None,
            ),
            "steps": step_results,
        }
        return updated

    def _execute_step(
        self, step: dict[str, object], artifact: NektarRunArtifact, run_dir: Path
    ) -> dict[str, object]:
        step_type = step.get("type")
        if step_type != "fieldconvert":
            return {
                "type": step_type,
                "status": "skipped",
                "fallback_reason": "unsupported_postprocess_type",
                "ran_fieldconvert": False,
            }

        output_name = step.get("output")
        if not output_name:
            return {
                "type": step_type,
                "status": "skipped",
                "fallback_reason": "invalid_postprocess_step",
                "ran_fieldconvert": False,
            }

        input_file = self._select_input_file(artifact, step)
        if input_file is None:
            return {
                "type": step_type,
                "status": "skipped",
                "fallback_reason": "postprocess_input_not_found",
                "ran_fieldconvert": False,
                "output_file": output_name,
            }

        resolved_binary = self._resolve_fieldconvert_binary()
        if resolved_binary is None:
            self._write_fieldconvert_logs(
                run_dir, stdout_text="", stderr_text="FieldConvert binary not found."
            )
            return {
                "type": step_type,
                "status": "unavailable",
                "fallback_reason": "fieldconvert_binary_not_found",
                "ran_fieldconvert": False,
                "resolved_binary": None,
                "output_file": output_name,
            }

        evaluate_error = self._is_error_evaluation_step(step)
        session_file = artifact.session_files[0] if artifact.session_files else None
        if evaluate_error and session_file is None:
            return {
                "type": step_type,
                "status": "skipped",
                "fallback_reason": "fieldconvert_session_not_found",
                "ran_fieldconvert": False,
                "output_file": output_name,
            }

        command = self._build_fieldconvert_command(
            step=step,
            input_file=input_file,
            output_name=str(output_name),
            resolved_binary=resolved_binary,
            run_dir=run_dir,
            session_file=session_file,
        )
        timeout_seconds = self._resolve_fieldconvert_timeout(artifact)
        try:
            result = self._run_fieldconvert(command, cwd=run_dir, timeout_seconds=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            stdout_text = self._coerce_process_output(error.stdout)
            stderr_text = self._coerce_process_output(error.stderr)
            if stderr_text:
                stderr_text += "\n\n"
            stderr_text += f"FieldConvert timed out after {timeout_seconds} seconds."
            self._write_fieldconvert_logs(run_dir, stdout_text=stdout_text, stderr_text=stderr_text)
            return {
                "type": step_type,
                "status": "failed",
                "fallback_reason": "fieldconvert_timeout",
                "ran_fieldconvert": True,
                "resolved_binary": resolved_binary,
                "command": command,
                "timeout_seconds": timeout_seconds,
                "exit_code": None,
                "output_file": output_name,
            }

        self._write_fieldconvert_logs(run_dir, stdout_text=result.stdout, stderr_text=result.stderr)
        output_path = None if evaluate_error else run_dir / str(output_name)
        produced_files = self._discover_derived_outputs(run_dir, output_path)
        self._update_artifact_outputs(artifact, produced_files)
        error_norms = self._extract_error_norms(result.stdout, result.stderr)
        if error_norms:
            artifact.filter_output.error_norms.update(error_norms)

        step_status = "completed" if result.returncode == 0 else "failed"
        return {
            "type": step_type,
            "status": step_status,
            "ran_fieldconvert": True,
            "resolved_binary": resolved_binary,
            "command": command,
            "timeout_seconds": timeout_seconds,
            "exit_code": result.returncode,
            "output_file": str(output_path) if output_path is not None else None,
            "produced_files": produced_files,
        }

    def _resolve_run_dir(self, artifact: NektarRunArtifact) -> Path:
        if artifact.session_files:
            return Path(artifact.session_files[0]).parent
        if artifact.field_files:
            return Path(artifact.field_files[0]).parent
        if artifact.filter_output.checkpoint_files:
            return Path(artifact.filter_output.checkpoint_files[-1]).parent
        raise ValueError("Cannot resolve postprocess run directory from artifact")

    def _select_input_file(
        self, artifact: NektarRunArtifact, step: dict[str, object]
    ) -> str | None:
        explicit = step.get("input")
        if explicit:
            return str(explicit)
        if artifact.field_files:
            return artifact.field_files[0]
        if artifact.filter_output.checkpoint_files:
            return sorted(artifact.filter_output.checkpoint_files)[-1]
        return None

    def _resolve_fieldconvert_binary(self) -> str | None:
        return shutil.which("FieldConvert")

    def _resolve_fieldconvert_timeout(self, artifact: NektarRunArtifact) -> float:
        solver_timeout = artifact.result_summary.get("timeout_seconds", 600)
        return float(solver_timeout)

    def _build_fieldconvert_command(
        self,
        *,
        step: dict[str, object],
        input_file: str,
        output_name: str,
        resolved_binary: str,
        run_dir: Path,
        session_file: str | None,
    ) -> list[str]:
        command = [resolved_binary]
        module = step.get("module")
        if module:
            command.extend(["-m", str(module)])
        args = step.get("args")
        if isinstance(args, list):
            command.extend(str(a) for a in args)
        if session_file is not None:
            command.append(session_file)
        command.append(input_file)
        command.append(str(run_dir / output_name))
        return command

    def _run_fieldconvert(
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

    def _write_fieldconvert_logs(
        self, run_dir: Path, *, stdout_text: str, stderr_text: str
    ) -> list[str]:
        stdout_path = run_dir / "fieldconvert.stdout.log"
        stderr_path = run_dir / "fieldconvert.stderr.log"
        combined_path = run_dir / "fieldconvert.log"
        stdout_path.write_text(stdout_text)
        stderr_path.write_text(stderr_text)
        combined_text = stdout_text
        if stdout_text and stderr_text:
            combined_text += "\n\n"
        combined_text += stderr_text
        combined_path.write_text(combined_text)
        return [str(combined_path), str(stdout_path), str(stderr_path)]

    def _discover_derived_outputs(self, run_dir: Path, declared_output: Path | None) -> list[str]:
        found: list[str] = []
        if declared_output is not None and declared_output.exists():
            found.append(str(declared_output))
        for pattern in ("*.vtu", "*.pvtu", "*.dat"):
            for path in sorted(run_dir.glob(pattern)):
                p = str(path)
                if p not in found:
                    found.append(p)
        return found

    def _update_artifact_outputs(
        self, artifact: NektarRunArtifact, produced_files: list[str]
    ) -> None:
        for path in produced_files:
            if path not in artifact.derived_files:
                artifact.derived_files.append(path)
            if path not in artifact.filter_output.files:
                artifact.filter_output.files.append(path)
            if path not in artifact.filter_output.fieldconvert_intermediates:
                artifact.filter_output.fieldconvert_intermediates.append(path)

    _COORDINATE_VARIABLES = frozenset({"x", "y", "z"})
    _FLOAT_PATTERN = r"[0-9]*\.?[0-9]+(?:[eE][+-]?[0-9]+)?"

    def _is_error_evaluation_step(self, step: dict[str, object]) -> bool:
        args = step.get("args")
        return isinstance(args, list) and any(str(arg) == "-e" for arg in args)

    def _extract_error_norms(self, stdout_text: str, stderr_text: str) -> dict[str, float]:
        norms: dict[str, float] = {}
        combined = f"{stdout_text}\n{stderr_text}"
        for match in re.finditer(
            rf"L\s*(2|inf)\s+error\s+\(variable\s+(\w+)\)\s*:\s*({self._FLOAT_PATTERN})",
            combined,
        ):
            norm_type = "l2" if match.group(1) == "2" else "linf"
            var = match.group(2).lower()
            if var in self._COORDINATE_VARIABLES:
                continue
            key = f"{norm_type}_error_{var}"
            norms[key] = float(match.group(3))
        return norms

    def _extract_solver_convergence_metrics(self, artifact: NektarRunArtifact) -> dict[str, float]:
        if artifact.solver_family != NektarSolverFamily.INCNS:
            return {}
        combined = self._read_solver_log_text(artifact.log_files)
        if not combined:
            return {}

        metrics: dict[str, float] = {}

        pressure_match = None
        for match in re.finditer(
            rf"Pressure system \(mapping\) converged in (\d+) iterations with error = ({self._FLOAT_PATTERN})",
            combined,
        ):
            pressure_match = match
        if pressure_match is not None:
            metrics["incns_pressure_iterations"] = float(pressure_match.group(1))
            metrics["incns_pressure_error"] = float(pressure_match.group(2))

        velocity_match = None
        for match in re.finditer(
            rf"Velocity system \(mapping\) converged in (\d+) iterations with error = ({self._FLOAT_PATTERN})",
            combined,
        ):
            velocity_match = match
        if velocity_match is not None:
            metrics["incns_velocity_iterations"] = float(velocity_match.group(1))
            metrics["incns_velocity_error"] = float(velocity_match.group(2))

        newton_match = None
        for match in re.finditer(r"We have done (\d+) iteration\(s\)", combined):
            newton_match = match
        if newton_match is not None:
            metrics["incns_newton_iterations"] = float(newton_match.group(1))

        for match in re.finditer(rf"L2Norm\[(\d+)\]\s*=\s*({self._FLOAT_PATTERN})", combined):
            metrics[f"incns_l2norm_{match.group(1)}"] = float(match.group(2))

        for match in re.finditer(rf"InfNorm\[(\d+)\]\s*=\s*({self._FLOAT_PATTERN})", combined):
            metrics[f"incns_infnorm_{match.group(1)}"] = float(match.group(2))

        for line in combined.splitlines():
            iteration_match = re.search(
                rf"Iteration:\s*(\d+).*?Velocity\s+L2:\s*({self._FLOAT_PATTERN}).*?Pressure\s+L2:\s*({self._FLOAT_PATTERN})",
                line,
            )
            if iteration_match is None:
                continue
            metrics["incns_iteration"] = float(iteration_match.group(1))
            metrics["incns_velocity_l2"] = float(iteration_match.group(2))
            metrics["incns_pressure_l2"] = float(iteration_match.group(3))

        return metrics

    def _read_solver_log_text(self, log_files: list[str]) -> str:
        combined_path = None
        fallback_paths: list[Path] = []
        for log_file in log_files:
            path = Path(log_file)
            if not path.exists() or not path.name.startswith("solver"):
                continue
            if path.name == "solver.log":
                combined_path = path
                break
            fallback_paths.append(path)

        if combined_path is not None:
            return combined_path.read_text()

        return "\n".join(path.read_text() for path in fallback_paths)
