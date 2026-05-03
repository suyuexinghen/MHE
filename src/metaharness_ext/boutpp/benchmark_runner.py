from __future__ import annotations

from pathlib import Path

from metaharness.benchmark_drivers.io import write_json, write_text
from metaharness.benchmark_drivers.models import BenchmarkCaseSpec, BenchmarkLane, LaneSummary
from metaharness.benchmark_drivers.runner_common import dry_run_summary
from metaharness_ext.boutpp.benchmark_cases import boutpp_usage_case_catalog
from metaharness_ext.boutpp.compiler import BoutPPCompilerComponent
from metaharness_ext.boutpp.gateway import BoutPPGatewayComponent


class BoutPPUsageValidationRunner:
    """Three-lane usage-validation runner for the BOUT++ extension baseline."""

    def __init__(self, runs_root: Path, allow_real_tools: bool = False) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self._gateway = BoutPPGatewayComponent()
        self._compiler = BoutPPCompilerComponent()

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
        return dry_run_summary(
            runs_root=self.runs_root,
            case=case,
            lane="extension",
            evidence_factory=lambda path: self._write_lane_evidence(
                path, case, "extension", "extension baseline"
            ),
        )

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        return dry_run_summary(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            evidence_factory=lambda path: self._write_lane_evidence(
                path, case, "direct", "direct CLI/manual workflow"
            ),
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        return dry_run_summary(
            runs_root=self.runs_root,
            case=case,
            lane="agent",
            evidence_factory=lambda path: self._write_lane_evidence(
                path, case, "agent", "agent-assisted workflow"
            ),
        )

    def _write_lane_evidence(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        lane: str,
        workflow_label: str,
    ) -> list[str]:
        spec = self._gateway.issue_task({"task_id": case.case_id, **case.problem_definition})
        plan = self._compiler.compile(
            spec,
            run_id=f"{case.case_id}-{lane}",
            workspace_dir=str(output_dir),
        )
        files = [
            write_json(output_dir / "boutpp_problem_spec.json", spec),
            write_json(output_dir / "boutpp_run_plan.json", plan),
            write_text(output_dir / "BOUT.inp", plan.bout_inp_content),
            write_text(
                output_dir / "usage_validation.md",
                self._usage_note(case, lane, workflow_label, plan.command),
            ),
            write_json(
                output_dir / "usage_validation_summary.json",
                {
                    "case_id": case.case_id,
                    "suite": case.suite,
                    "lane": lane,
                    "workflow_label": workflow_label,
                    "command": plan.command,
                    "data_dir": plan.data_dir,
                    "claim_boundary": "Usage validation only; no real BOUT++ execution was required.",
                    "real_tools_requested": self.allow_real_tools,
                },
            ),
        ]
        if lane == "agent":
            files.append(
                write_text(
                    output_dir / "agent_prompt.txt",
                    "Validate the BOUT++ usage baseline against the direct/manual workflow.",
                )
            )
        elif lane == "direct":
            files.append(
                write_text(
                    output_dir / "manual_cli_workflow.txt",
                    "Direct CLI/manual workflow comparison uses the same compiled command and BOUT.inp.",
                )
            )
        return [str(path) for path in files]

    def _usage_note(
        self,
        case: BenchmarkCaseSpec,
        lane: str,
        workflow_label: str,
        command: list[str],
    ) -> str:
        return "\n".join(
            [
                f"# BOUT++ usage validation: {case.case_id}",
                f"- lane: {lane}",
                f"- workflow: {workflow_label}",
                f"- command: {' '.join(command)}",
                "- boundary: accepted baseline only; no claim of real solver execution",
            ]
        )


__all__ = ["BoutPPUsageValidationRunner", "boutpp_usage_case_catalog"]
