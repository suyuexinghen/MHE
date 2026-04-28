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
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.brain_provider = brain_provider or FakeClaudeCLIBrainProvider()

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
        started_at = time.perf_counter()
        try:
            spec = self._build_extension_spec(case, output_dir)
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
                lane="extension",
                status="passed" if validation.passed else "failed",
                metrics=metrics,
                evidence_files=evidence.evidence_files,
                started_at=started_at,
            )
        except Exception as exc:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                status="failed",
                error_message=str(exc),
                started_at=started_at,
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
        started_at = time.perf_counter()
        script_path = output_dir / "solve.m"
        self._write_direct_script(script_path, case)
        stdout_path = output_dir / "stdout.txt"
        stderr_path = output_dir / "stderr.txt"
        result = subprocess.run(
            ["octave-cli", "--no-gui", "--quiet", "--no-init-file", str(script_path)],
            cwd=output_dir,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        write_text(stdout_path, result.stdout)
        write_text(stderr_path, result.stderr)
        metrics = self._read_metrics(output_dir)
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status="passed" if result.returncode == 0 else "failed",
            metrics=metrics,
            evidence_files=[
                claude_result.invocation.prompt_path,
                claude_result.invocation.stdout_path,
                claude_result.invocation.stderr_path,
                claude_result.invocation.result_path or "",
                claude_result.invocation.proposal_path or "",
                str(script_path),
                str(stdout_path),
                str(stderr_path),
            ],
            attempt_log=attempt_log,
            started_at=started_at,
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
        return self.run_extension(case).model_copy(update={"lane": "agent", "llm_calls": 1})

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
        self, case: BenchmarkCaseSpec, output_dir: Path
    ) -> OctaveExperimentSpec:
        return OctaveExperimentSpec(
            task_id=case.case_id,
            script=OctaveScriptSpec(
                mode="inline",
                inline_source=build_octave_case_script(case),
            ),
            workspace=OctaveWorkspaceSpec(working_directory=str(output_dir / "workspace")),
            expected_outputs=[
                OctaveOutputSpec(
                    name=metric,
                    variable_name=metric,
                    tolerance=OctaveToleranceSpec(
                        expected_value=float(reference.value)
                        if (reference := case.metric_references.get(metric)) is not None
                        and isinstance(reference.value, int | float)
                        else 0.0,
                        atol=reference.tolerance
                        if reference is not None
                        else case.tolerance.get(metric, 1e-8),
                        rtol=0.0,
                    ),
                )
                for metric in case.expected_metrics
            ],
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

    def _write_direct_script(self, script_path: Path, case: BenchmarkCaseSpec) -> None:
        metric_fields = ", ".join(f"'{metric}', {metric}" for metric in case.expected_metrics)
        content = (
            "more off;\n"
            "warning('on', 'all');\n"
            + build_octave_case_script(case)
            + "\nmetrics = struct("
            + metric_fields
            + ");\nfid = fopen('metrics.json', 'w');\nfputs(fid, jsonencode(metrics));\nfclose(fid);\n"
        )
        write_text(script_path, content)

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
