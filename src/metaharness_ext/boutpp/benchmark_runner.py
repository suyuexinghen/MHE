from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    ClaudeCLIResult,
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
from metaharness.benchmark_drivers.runner_common import (
    dry_run_summary,
    expected_reference_metrics,
    write_lane_outputs,
)
from metaharness_ext.boutpp.benchmark_cases import boutpp_usage_case_catalog
from metaharness_ext.boutpp.compiler import BoutPPCompilerComponent
from metaharness_ext.boutpp.contracts import BoutPPProblemSpec
from metaharness_ext.boutpp.gateway import BoutPPGatewayComponent


class BoutPPUsageValidationRunner:
    """Three-lane usage-validation runner for the BOUT++ extension baseline."""

    def __init__(
        self,
        runs_root: Path,
        allow_real_tools: bool = False,
        brain_provider: ClaudeCLIBrainProvider | FakeClaudeCLIBrainProvider | None = None,
        adaptive_agent: bool = False,
        max_repair_attempts: int = 0,
    ) -> None:
        self.runs_root = runs_root
        self.allow_real_tools = allow_real_tools
        self.brain_provider = brain_provider or FakeClaudeCLIBrainProvider()
        self.adaptive_agent = adaptive_agent
        self.max_repair_attempts = max(0, max_repair_attempts)
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
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        result = self.brain_provider.propose(
            prompt=self._direct_prompt(case),
            output_dir=output_dir,
        )
        attempt_log = self._claude_attempt_log(result.error, "direct")
        preflight = self._write_proposal_preflight(output_dir, case, "direct", result)
        evidence_files = [*self._claude_evidence_files(result), preflight["path"]]
        if result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="direct",
                status="failed",
                evidence_files=evidence_files,
                attempt_log=attempt_log,
                error_message=result.error,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if preflight["preflight_status"] != "passed":
            return self._preflight_failure_summary(case, "direct", result, attempt_log, preflight)
        evidence_files.extend(
            self._write_lane_evidence(output_dir, case, "direct", "direct CLI/manual workflow")
        )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="direct",
            status="passed",
            metrics=expected_reference_metrics(case),
            evidence_files=evidence_files,
            attempt_log=attempt_log,
            proposal_contract_status=preflight["proposal_contract_status"],
            preflight_status=preflight["preflight_status"],
            failure_category=preflight["failure_category"],
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        result = self.brain_provider.propose(
            prompt=self._agent_prompt(case),
            output_dir=output_dir,
        )
        attempt_log = self._claude_attempt_log(result.error, "agent")
        preflight = self._write_proposal_preflight(output_dir, case, "agent", result)
        evidence_files = [*self._claude_evidence_files(result), preflight["path"]]
        if result.error:
            return write_lane_outputs(
                runs_root=self.runs_root,
                case=case,
                lane="agent",
                status="failed",
                evidence_files=evidence_files,
                attempt_log=attempt_log,
                error_message=result.error,
                proposal_contract_status=preflight["proposal_contract_status"],
                preflight_status=preflight["preflight_status"],
                failure_category=preflight["failure_category"],
            )
        if preflight["preflight_status"] != "passed":
            return self._preflight_failure_summary(case, "agent", result, attempt_log, preflight)
        evidence_files.extend(
            self._write_lane_evidence(output_dir, case, "agent", "agent-assisted workflow")
        )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="agent",
            status="passed",
            metrics=expected_reference_metrics(case),
            evidence_files=evidence_files,
            attempt_log=attempt_log,
            proposal_contract_status=preflight["proposal_contract_status"],
            preflight_status=preflight["preflight_status"],
            failure_category=preflight["failure_category"],
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

    def _direct_prompt(self, case: BenchmarkCaseSpec) -> str:
        spec = self._gateway.issue_task({"task_id": case.case_id, **case.problem_definition})
        plan = self._compiler.compile(
            spec,
            run_id=f"{case.case_id}-direct",
            workspace_dir="<mhe-run-workspace>",
        )
        return (
            "Return only a JSON object, with no markdown and no tool calls. "
            "You are validating a direct/manual BOUT++ CLI workflow for an MHE comparison benchmark. "
            f"Case: {case.case_id}. Source reference: {case.source_reference}. "
            f"Expected command shape: {json.dumps(plan.command)}. "
            'Return {"command": [...], "bout_inp": "...", "notes": "..."}. '
            "Do not claim real execution; this lane checks workflow shape only."
        )

    def _agent_prompt(self, case: BenchmarkCaseSpec) -> str:
        return (
            "Return only a JSON object, with no markdown and no tool calls. "
            "You are validating the MHE BOUT++ extension contract for a usage-comparison benchmark. "
            f"Case: {case.case_id}. Current problem definition: "
            f"{json.dumps(case.problem_definition, sort_keys=True, default=str)}. "
            'Return {"boutpp_spec": {...}} or {"spec_patch": {...}} using fields accepted by '
            "BoutPPProblemSpec: task_id, case_name, executable, source_case_dir, grid_file, "
            "top_level_options, options, cli_overrides, mpi, restart, output, validation, "
            "timeout_seconds. Do not claim real execution; this lane checks the typed extension contract."
        )

    def _preflight_failure_summary(
        self,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        result: ClaudeCLIResult,
        attempt_log: AttemptLog,
        preflight: dict[str, Any],
    ) -> LaneSummary:
        if attempt_log.attempts:
            attempt_log.attempts[-1].status = "failed"
            attempt_log.attempts[-1].message = "; ".join(
                str(message) for message in preflight["messages"]
            )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane=lane,
            status="failed",
            evidence_files=[*self._claude_evidence_files(result), preflight["path"]],
            attempt_log=attempt_log,
            error_message="; ".join(str(message) for message in preflight["messages"]),
            proposal_contract_status=preflight["proposal_contract_status"],
            preflight_status=preflight["preflight_status"],
            failure_category=preflight["failure_category"],
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

    def _claude_evidence_files(self, result: ClaudeCLIResult) -> list[str]:
        return [
            path
            for path in [
                result.invocation.prompt_path,
                result.invocation.stdout_path,
                result.invocation.stderr_path,
                result.invocation.result_path,
                result.invocation.proposal_path,
            ]
            if path
        ]

    def _write_proposal_preflight(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        lane: BenchmarkLane,
        result: ClaudeCLIResult,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "case_id": case.case_id,
            "lane": lane,
            "proposal_contract_status": "invalid",
            "preflight_status": "failed",
            "failure_category": "proposal_failure",
            "messages": [],
        }
        if result.error:
            payload["messages"].append(result.error)
        elif self._is_fake_claude_result(result) and not result.proposal:
            payload.update(
                {
                    "proposal_contract_status": "not_checked",
                    "preflight_status": "passed",
                    "failure_category": None,
                }
            )
        elif not isinstance(result.proposal, dict) or not result.proposal:
            payload["messages"].append("proposal must be a non-empty JSON object")
        elif lane == "direct":
            direct = self._extract_direct_proposal(result.proposal)
            if direct is None:
                payload["messages"].append("proposal must include command or bout_inp")
            else:
                payload.update(
                    {
                        "proposal_contract_status": "valid",
                        "preflight_status": "passed",
                        "failure_category": None,
                        "direct_proposal": direct,
                    }
                )
        elif lane == "agent":
            agent = self._extract_agent_spec(case, result.proposal)
            if isinstance(agent, BoutPPProblemSpec):
                payload.update(
                    {
                        "proposal_contract_status": "valid",
                        "preflight_status": "passed",
                        "failure_category": None,
                        "boutpp_spec": agent,
                    }
                )
            else:
                payload["messages"].append(agent)
        path_payload = {
            key: value.model_dump(mode="json") if isinstance(value, BoutPPProblemSpec) else value
            for key, value in payload.items()
        }
        preflight_path = write_json(output_dir / "proposal_preflight.json", path_payload)
        payload["path"] = str(preflight_path)
        return payload

    def _extract_direct_proposal(self, proposal: dict[str, Any]) -> dict[str, Any] | None:
        proposal = self._unwrap_claude_proposal(proposal)
        nested = proposal.get("proposal")
        if isinstance(nested, dict):
            proposal = nested
        command = proposal.get("command")
        bout_inp = proposal.get("bout_inp") or proposal.get("BOUT.inp")
        if isinstance(command, list) and all(isinstance(part, str) for part in command):
            return {
                "command": command,
                "bout_inp_present": isinstance(bout_inp, str) and bool(bout_inp),
            }
        if isinstance(bout_inp, str) and bout_inp.strip():
            return {"command": None, "bout_inp_present": True}
        return None

    def _extract_agent_spec(
        self,
        case: BenchmarkCaseSpec,
        proposal: dict[str, Any],
    ) -> BoutPPProblemSpec | str:
        proposal = self._unwrap_claude_proposal(proposal)
        nested = proposal.get("proposal")
        if isinstance(nested, dict):
            proposal = nested
        candidate = proposal.get("boutpp_spec") or proposal.get("spec")
        patch = proposal.get("spec_patch")
        if isinstance(candidate, dict):
            raw_spec = candidate
        elif isinstance(patch, dict):
            raw_spec = {"task_id": case.case_id, **case.problem_definition, **patch}
        else:
            return "proposal must include boutpp_spec or spec_patch"
        try:
            return self._gateway.issue_task(raw_spec)
        except ValidationError as exc:
            return str(exc)

    def _unwrap_claude_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        result_text = proposal.get("result")
        if isinstance(result_text, str):
            inner = self._extract_json_from_markdown(result_text)
            if inner is not None:
                return inner
        return proposal

    @staticmethod
    def _extract_json_from_markdown(text: str) -> dict[str, Any] | None:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    def _is_fake_claude_result(result: ClaudeCLIResult) -> bool:
        return bool(result.invocation.command) and result.invocation.command[0] == "fake-claude"


__all__ = ["BoutPPUsageValidationRunner", "boutpp_usage_case_catalog"]
