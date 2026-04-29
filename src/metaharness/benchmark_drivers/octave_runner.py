from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    FakeClaudeCLIBrainProvider,
)
from metaharness.benchmark_drivers.io import case_dir, write_json, write_text
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    BenchmarkLane,
    LaneSummary,
)
from metaharness.benchmark_drivers.octave_scripts import build_octave_case_script
from metaharness.benchmark_drivers.runner_common import dry_run_summary, write_lane_outputs
from metaharness_ext.octave.contracts import (
    OctaveExperimentSpec,
    OctaveOutputSpec,
    OctaveScriptSpec,
    OctaveToleranceSpec,
    OctaveWorkspaceSpec,
)
from metaharness_ext.octave.evidence import build_evidence_bundle
from metaharness_ext.octave.executor import OctaveExecutorComponent
from metaharness_ext.octave.script_compiler import OctaveScriptCompilerComponent
from metaharness_ext.octave.validator import OctaveValidatorComponent


class OctaveBenchmarkRunner:
    def __init__(
        self,
        *,
        runs_root: Path,
        allow_real_tools: bool = False,
        brain_provider: ClaudeCLIBrainProvider | FakeClaudeCLIBrainProvider | None = None,
        adaptive_agent: bool = False,
        max_repair_attempts: int = 1,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.brain_provider = brain_provider or FakeClaudeCLIBrainProvider()
        self.adaptive_agent = adaptive_agent
        self.max_repair_attempts = max(0, max_repair_attempts)

    def run_case(self, case: BenchmarkCaseSpec, lanes: list[BenchmarkLane]) -> list[LaneSummary]:
        summaries: list[LaneSummary] = []
        for lane in lanes:
            if lane == "extension":
                summaries.append(self.run_extension(case))
            elif lane == "direct":
                summaries.append(self.run_direct(case))
            elif lane == "agent":
                summaries.append(self.run_agent(case))
        return summaries

    def run_extension(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "extension", case.case_id)
        if not self.allow_real_tools:
            return dry_run_summary(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                evidence_factory=lambda path: self._write_extension_evidence(path, case),
            )
        if shutil.which("octave-cli") is None:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="skipped",
                skip_reason="octave-cli not found",
            )
        return self._run_extension_pipeline_lane(
            case=case,
            lane="extension",
            output_dir=output_dir,
        )

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        prompt = f"Generate a standalone Octave solve.m for benchmark case {case.case_id}."
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        attempt_log = self._claude_attempt_log(claude_result.error, "direct")
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                attempt_log=attempt_log,
                error_message=claude_result.error,
            )
        if not self.allow_real_tools:
            metrics = {
                metric: float(reference.value)
                if (reference := case.metric_references.get(metric)) is not None
                and isinstance(reference.value, int | float)
                else 0.0
                for metric in case.expected_metrics
            }
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="passed",
                metrics=metrics,
                evidence_files=[
                    claude_result.invocation.prompt_path,
                    claude_result.invocation.stdout_path,
                    claude_result.invocation.stderr_path,
                    claude_result.invocation.result_path or "",
                    claude_result.invocation.proposal_path or "",
                    *self._write_direct_evidence(output_dir, case),
                ],
                attempt_log=attempt_log,
            )
        if shutil.which("octave-cli") is None:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=[
                    claude_result.invocation.prompt_path,
                    claude_result.invocation.stdout_path,
                    claude_result.invocation.stderr_path,
                    claude_result.invocation.result_path or "",
                    claude_result.invocation.proposal_path or "",
                ],
                skip_reason="octave-cli not found",
            )
        return self._run_direct_script_lane(
            case=case,
            lane="direct",
            output_dir=output_dir,
            claude_result=claude_result,
            attempt_log=attempt_log,
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        prompt = f"Generate an Octave benchmark proposal for case {case.case_id}."
        claude_result = self.brain_provider.propose(prompt=prompt, output_dir=output_dir)
        attempt_log = self._claude_attempt_log(claude_result.error, "agent")
        if claude_result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                attempt_log=attempt_log,
                error_message=claude_result.error,
            )
        if not self.allow_real_tools:
            metrics = {
                metric: float(reference.value)
                if (reference := case.metric_references.get(metric)) is not None
                and isinstance(reference.value, int | float)
                else 0.0
                for metric in case.expected_metrics
            }
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="passed",
                metrics=metrics,
                evidence_files=[
                    claude_result.invocation.prompt_path,
                    claude_result.invocation.stdout_path,
                    claude_result.invocation.stderr_path,
                    claude_result.invocation.result_path or "",
                    claude_result.invocation.proposal_path or "",
                ],
                attempt_log=attempt_log,
            )
        if shutil.which("octave-cli") is None:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="skipped",
                attempt_log=attempt_log,
                evidence_files=[
                    claude_result.invocation.prompt_path,
                    claude_result.invocation.stdout_path,
                    claude_result.invocation.stderr_path,
                    claude_result.invocation.result_path or "",
                    claude_result.invocation.proposal_path or "",
                ],
                skip_reason="octave-cli not found",
            )
        evidence_files = [
            claude_result.invocation.prompt_path,
            claude_result.invocation.stdout_path,
            claude_result.invocation.stderr_path,
            claude_result.invocation.result_path or "",
            claude_result.invocation.proposal_path or "",
        ]
        if self.adaptive_agent:
            return self._run_adaptive_agent_lane(
                case=case,
                output_dir=output_dir,
                initial_proposal=claude_result.proposal,
                attempt_log=attempt_log,
                evidence_files=evidence_files,
            )
        return self._run_extension_pipeline_lane(
            case=case,
            lane="agent",
            output_dir=output_dir,
            attempt_log=attempt_log,
            evidence_files=evidence_files,
        )

    def _run_extension_pipeline_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        output_dir: Path,
        attempt_log: AttemptLog | None = None,
        evidence_files: list[str] | None = None,
        proposal: dict[str, Any] | None = None,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        try:
            spec = self._build_extension_spec(case, output_dir, proposal=proposal)
            plan = OctaveScriptCompilerComponent().build_plan(spec)
            artifact = OctaveExecutorComponent().execute_plan(plan)
            artifact = artifact.model_copy(
                update={
                    "parsed_outputs": self._read_metric_output_files(
                        Path(artifact.working_directory)
                    )
                }
            )
            validation = OctaveValidatorComponent().validate_run(artifact, plan)
            evidence = build_evidence_bundle(artifact, validation, plan=plan)
            metrics = {
                **artifact.summary_metrics,
                **artifact.parsed_outputs,
                **validation.numeric_metrics,
            }
            write_json(output_dir / "validation.json", validation)
            write_json(output_dir / "evidence.json", evidence)
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="passed" if validation.passed else "failed",
                metrics=metrics,
                evidence_files=[*(evidence_files or []), *evidence.evidence_files],
                attempt_log=attempt_log,
                started_at=started_at,
            )
        except Exception as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                attempt_log=attempt_log,
                evidence_files=evidence_files,
                error_message=str(exc),
                started_at=started_at,
            )

    def _run_adaptive_agent_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        initial_proposal: dict[str, Any],
        attempt_log: AttemptLog,
        evidence_files: list[str],
    ) -> LaneSummary:
        current_proposal = initial_proposal
        diagnostics_files: list[str] = []
        for repair_index in range(self.max_repair_attempts + 1):
            attempt_output_dir = (
                output_dir if repair_index == 0 else output_dir / f"repair-{repair_index}"
            )
            summary = self._run_extension_pipeline_lane(
                case=case,
                lane="agent",
                output_dir=attempt_output_dir,
                attempt_log=attempt_log,
                evidence_files=[*evidence_files, *diagnostics_files],
                proposal=current_proposal,
            )
            if summary.passed or repair_index >= self.max_repair_attempts:
                if attempt_output_dir != output_dir:
                    write_json(output_dir / "adaptive_final_summary.json", summary)
                    return write_lane_outputs(
                        runs_root=self.runs_root,
                        case=case,
                        lane="agent",
                        status=summary.status,
                        metrics=summary.metrics,
                        evidence_files=[
                            *summary.evidence_files,
                            str(output_dir / "adaptive_final_summary.json"),
                        ],
                        attempt_log=attempt_log,
                        error_message=summary.error_message,
                        skip_reason=summary.skip_reason,
                    )
                return summary
            diagnostics_path = self._write_adaptive_diagnostics(
                output_dir,
                case,
                summary,
                current_proposal,
                repair_index + 1,
            )
            diagnostics_files.append(str(diagnostics_path))
            repair_result = self.brain_provider.propose(
                prompt=self._repair_prompt(case, summary, diagnostics_path),
                output_dir=output_dir / f"repair-{repair_index + 1}-claude",
            )
            attempt_log.add(
                AttemptRecord(
                    attempt_id=attempt_log.attempt_count + 1,
                    lane="agent",
                    status="failed" if repair_result.error else "passed",
                    repair=True,
                    llm_call=True,
                    message=repair_result.error,
                    evidence_files=[
                        repair_result.invocation.prompt_path,
                        repair_result.invocation.stdout_path,
                        repair_result.invocation.stderr_path,
                        repair_result.invocation.result_path or "",
                        repair_result.invocation.proposal_path or "",
                    ],
                )
            )
            evidence_files.extend(
                [
                    repair_result.invocation.prompt_path,
                    repair_result.invocation.stdout_path,
                    repair_result.invocation.stderr_path,
                    repair_result.invocation.result_path or "",
                    repair_result.invocation.proposal_path or "",
                ]
            )
            if repair_result.error:
                current_proposal = {}
            else:
                current_proposal = repair_result.proposal
        return summary

    def _run_direct_script_lane(
        self,
        *,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        output_dir: Path,
        claude_result,
        attempt_log: AttemptLog,
    ) -> LaneSummary:
        started_at = time.perf_counter()
        script_path = output_dir / "solve.m"
        self._write_direct_script(script_path, case, claude_result.proposal)
        stdout_path = output_dir / "stdout.txt"
        stderr_path = output_dir / "stderr.txt"
        evidence_files = [
            claude_result.invocation.prompt_path,
            claude_result.invocation.stdout_path,
            claude_result.invocation.stderr_path,
            claude_result.invocation.result_path or "",
            claude_result.invocation.proposal_path or "",
            str(script_path),
            str(stdout_path),
            str(stderr_path),
        ]
        try:
            result = subprocess.run(
                ["octave-cli", "--no-gui", "--quiet", "--no-init-file", script_path.name],
                cwd=output_dir,
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            write_text(stdout_path, self._process_output_text(exc.stdout))
            write_text(stderr_path, self._process_output_text(exc.stderr))
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                evidence_files=evidence_files,
                attempt_log=attempt_log,
                error_message=f"octave-cli timed out after {exc.timeout} seconds",
                started_at=started_at,
            )
        except OSError as exc:
            write_text(stdout_path, "")
            write_text(stderr_path, str(exc))
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                evidence_files=evidence_files,
                attempt_log=attempt_log,
                error_message=str(exc),
                started_at=started_at,
            )
        write_text(stdout_path, result.stdout)
        write_text(stderr_path, result.stderr)
        try:
            metrics = self._read_metrics(output_dir)
        except json.JSONDecodeError as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane=lane,
                status="failed",
                evidence_files=evidence_files,
                attempt_log=attempt_log,
                error_message=f"invalid metrics.json: {exc}",
                started_at=started_at,
            )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status="passed" if result.returncode == 0 else "failed",
            metrics=metrics,
            evidence_files=evidence_files,
            attempt_log=attempt_log,
            started_at=started_at,
        )

    def _claude_attempt_log(self, error: str | None, lane: BenchmarkLane) -> AttemptLog:
        return AttemptLog(
            attempts=[
                AttemptRecord(
                    attempt_id=1,
                    lane=lane,
                    status="failed" if error else "passed",
                    llm_call=True,
                    message=error,
                )
            ]
        )

    def _build_extension_spec(
        self,
        case: BenchmarkCaseSpec,
        output_dir: Path,
        proposal: dict[str, Any] | None = None,
    ) -> OctaveExperimentSpec:
        return OctaveExperimentSpec(
            task_id=case.case_id,
            script=OctaveScriptSpec(
                mode="inline",
                inline_source=self._extension_inline_source(case, proposal or {}),
            ),
            workspace=OctaveWorkspaceSpec(working_directory=str(output_dir / "workspace")),
            expected_outputs=[
                OctaveOutputSpec(
                    name=metric,
                    variable_name=metric,
                    tolerance=OctaveToleranceSpec(
                        expected_value=float(reference.value),
                        atol=reference.tolerance,
                        rtol=0.0,
                    )
                    if (reference := case.metric_references.get(metric)) is not None
                    and isinstance(reference.value, int | float)
                    else None,
                )
                for metric in case.expected_metrics
            ],
        )

    def _extension_inline_source(self, case: BenchmarkCaseSpec, proposal: dict[str, Any]) -> str:
        return self._proposal_script(proposal) or build_octave_case_script(case)

    def _write_adaptive_diagnostics(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        summary: LaneSummary,
        proposal: dict[str, Any],
        repair_attempt: int,
    ) -> Path:
        return write_json(
            output_dir / f"adaptive_diagnostics_{repair_attempt}.json",
            {
                "case_id": case.case_id,
                "repair_attempt": repair_attempt,
                "status": summary.status,
                "missing_metrics": summary.missing_metrics,
                "error_message": summary.error_message,
                "proposal": proposal,
                "evidence_files": summary.evidence_files,
            },
        )

    def _repair_prompt(
        self, case: BenchmarkCaseSpec, summary: LaneSummary, diagnostics_path: Path
    ) -> str:
        return (
            "Repair the Octave benchmark agent proposal as JSON. "
            "Return a proposal with one of solve_m, script, or octave_script containing a complete "
            f"Octave script for case {case.case_id}. "
            f"Missing metrics: {summary.missing_metrics}. "
            f"Previous error: {summary.error_message}. "
            f"Diagnostics path: {diagnostics_path}."
        )

    def _write_extension_evidence(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        validation_path = write_json(
            output_dir / "validation.json", {"passed": True, "dry_run": True}
        )
        evidence_path = write_json(
            output_dir / "evidence.json", {"case_id": case.case_id, "dry_run": True}
        )
        wrapper_path = write_text(output_dir / "mhe_wrapper.m", "% dry-run wrapper\n")
        solver_path = write_text(output_dir / "generated_solver.m", "% dry-run solver\n")
        return [str(validation_path), str(evidence_path), str(wrapper_path), str(solver_path)]

    def _write_direct_evidence(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        script_path = write_text(output_dir / "solve.m", "% dry-run direct solve\n")
        stdout_path = write_text(output_dir / "stdout.txt", "")
        stderr_path = write_text(output_dir / "stderr.txt", "")
        return [str(script_path), str(stdout_path), str(stderr_path)]

    def _write_direct_script(
        self,
        script_path: Path,
        case: BenchmarkCaseSpec,
        proposal: dict[str, Any] | None = None,
    ) -> None:
        proposal_script = self._proposal_script(proposal or {})
        content = (
            proposal_script if proposal_script is not None else self._default_direct_script(case)
        )
        write_text(script_path, content)

    def _default_direct_script(self, case: BenchmarkCaseSpec) -> str:
        metric_writes = []
        for index, metric in enumerate(case.expected_metrics):
            separator = "" if index == 0 else ", "
            metric_writes.append(f"fprintf(fid, '{separator}\\\"{metric}\\\": %.17g', {metric});")
        return (
            "more off;\n"
            "warning('on', 'all');\n"
            + build_octave_case_script(case)
            + "\nfid = fopen('metrics.json', 'w');\nfprintf(fid, '{');\n"
            + "\n".join(metric_writes)
            + "\nfprintf(fid, '}');\nfclose(fid);\n"
        )

    def _proposal_script(self, proposal: dict[str, Any]) -> str | None:
        for key in ["solve_m", "script", "octave_script"]:
            value = proposal.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    def _process_output_text(self, value: bytes | str | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    def _read_metric_output_files(self, output_dir: Path) -> dict[str, float]:
        metrics: dict[str, float] = {}
        for path in sorted((output_dir / "outputs").glob("*.txt")):
            try:
                metrics[path.stem] = float(path.read_text().split()[-1])
            except (IndexError, ValueError, OSError):
                continue
        return metrics

    def _read_metrics(self, output_dir: Path) -> dict[str, Any]:
        metrics_path = output_dir / "metrics.json"
        if not metrics_path.exists():
            return {}
        return json.loads(metrics_path.read_text())
