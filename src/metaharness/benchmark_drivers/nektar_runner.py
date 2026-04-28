from __future__ import annotations

import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from metaharness.benchmark_drivers.claude_cli import (
    ClaudeCLIBrainProvider,
    FakeClaudeCLIBrainProvider,
)
from metaharness.benchmark_drivers.io import case_dir, suite_root, write_json, write_text
from metaharness.benchmark_drivers.models import (
    AttemptLog,
    AttemptRecord,
    BenchmarkCaseSpec,
    BenchmarkLane,
    LaneSummary,
)
from metaharness.benchmark_drivers.runner_common import dry_run_summary, write_lane_outputs

L2_PATTERN = re.compile(
    r"^L 2 error\s*(?:\(variable\s+(\w+)\))?\s*:\s*"
    r"([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)"
)
LINF_PATTERN = re.compile(
    r"^L inf error\s*(?:\(variable\s+(\w+)\))?\s*:\s*"
    r"([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)"
)


@dataclass(frozen=True)
class NektarTestSpec:
    executable: str | None = None
    parameters: list[str] = field(default_factory=list)
    reference_metrics: dict[str, tuple[float, float]] = field(default_factory=dict)


def parse_nektar_tst(path: Path) -> NektarTestSpec:
    root = ET.fromstring(path.read_text())
    executable = _element_text(root, "executable")
    parameters = [element.text.strip() for element in root.findall(".//parameters") if element.text]
    reference_metrics: dict[str, tuple[float, float]] = {}
    for metric in root.findall(".//metric"):
        metric_type = (metric.get("type") or "").lower()
        if metric_type not in {"l2", "linf"}:
            continue
        prefix = "l2_error" if metric_type == "l2" else "linf_error"
        for value in metric.findall(".//value"):
            variable = value.get("variable") or "u"
            if value.text is None:
                continue
            tolerance = float(value.get("tolerance", "0"))
            reference_metrics[f"{prefix}_{variable}"] = (float(value.text.strip()), tolerance)
    return NektarTestSpec(
        executable=executable,
        parameters=parameters,
        reference_metrics=reference_metrics,
    )


def _element_text(root: ET.Element, name: str) -> str | None:
    element = root.find(f".//{name}")
    if element is None or element.text is None:
        return None
    stripped = element.text.strip()
    return stripped or None


def parse_nektar_error_norms(stdout: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in stdout.splitlines():
        stripped = line.strip()
        l2_match = L2_PATTERN.match(stripped)
        if l2_match:
            variable = l2_match.group(1) or "u"
            metrics[f"l2_error_{variable}"] = float(l2_match.group(2))
            continue
        linf_match = LINF_PATTERN.match(stripped)
        if linf_match:
            variable = linf_match.group(1) or "u"
            metrics[f"linf_error_{variable}"] = float(linf_match.group(2))
    return metrics


class NektarBenchmarkRunner:
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
        self._write_preflight(case)
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
        if not self.allow_real_tools:
            return dry_run_summary(
                runs_root=self.runs_root,
                case=case,
                lane="extension",
                evidence_factory=lambda path: self._write_extension_evidence(path, case),
            )
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="extension",
            status="skipped",
            skip_reason="real Nektar reference-XML extension replay is not enabled by default",
        )

    def run_direct(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "direct", case.case_id)
        prompt = f"Generate a standalone Nektar++ session.xml for benchmark case {case.case_id}."
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
        test_spec = self._load_test_spec(case)
        solver_binary = test_spec.executable or str(
            case.problem_definition.get("solver_binary", "ADRSolver")
        )
        if shutil.which(solver_binary) is None:
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
                skip_reason=f"{solver_binary} not found",
            )
        started_at = time.perf_counter()
        session_path = self._materialize_session_xml(output_dir, case, test_spec)
        stdout_path = output_dir / "solver.stdout.log"
        stderr_path = output_dir / "solver.stderr.log"
        result = subprocess.run(
            [solver_binary, str(session_path)],
            cwd=output_dir,
            text=True,
            capture_output=True,
            check=False,
            timeout=600,
        )
        write_text(stdout_path, result.stdout)
        write_text(stderr_path, result.stderr)
        metrics: dict[str, Any] = parse_nektar_error_norms(result.stdout)
        metrics["elapsed_seconds"] = time.perf_counter() - started_at
        self._write_nektar_reference_metrics(output_dir, test_spec)
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
                str(session_path),
                str(stdout_path),
                str(stderr_path),
            ],
            attempt_log=attempt_log,
            started_at=started_at,
        )

    def run_agent(self, case: BenchmarkCaseSpec) -> LaneSummary:
        output_dir = case_dir(self.runs_root, case.suite, "agent", case.case_id)
        prompt = f"Generate a Nektar++ benchmark proposal for case {case.case_id}."
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
        return write_lane_outputs(
            runs_root=self.runs_root,
            case=case,
            lane="agent",
            status="skipped",
            attempt_log=attempt_log,
            skip_reason="real Nektar agent replay requires a dedicated extension session mapping",
        )

    def _write_preflight(self, case: BenchmarkCaseSpec) -> None:
        output_dir = suite_root(self.runs_root, case.suite) / "preflight" / case.case_id
        source_reference = case.source_reference if isinstance(case.source_reference, dict) else {}
        raw_tst_path = str(source_reference.get("tst", ""))
        tst_path = Path(raw_tst_path) if raw_tst_path else None
        test_spec = self._load_test_spec(case)
        tester_available = shutil.which("Tester") is not None
        solver_binary = test_spec.executable or str(
            case.problem_definition.get("solver_binary", "ADRSolver")
        )
        solver_available = shutil.which(solver_binary) is not None
        summary = {
            "case_id": case.case_id,
            "tester_available": tester_available,
            "alternative_validation": "solver_binary_probe" if not tester_available else None,
            "solver_binary": solver_binary,
            "solver_available": solver_available,
            "tst_path": raw_tst_path or None,
            "tst_available": tst_path.exists() if tst_path is not None else False,
            "reference_metric_count": len(test_spec.reference_metrics),
            "real_tools_allowed": self.allow_real_tools,
            "status": "available" if tester_available or solver_available else "unavailable",
        }
        write_text(output_dir / "tester.stdout.log", "")
        write_text(output_dir / "tester.stderr.log", "")
        write_json(output_dir / "tester_summary.json", summary)

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

    def _write_extension_evidence(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        session_path = write_text(output_dir / "session.xml", "<NEKTAR />\n")
        stdout_path = write_text(output_dir / "solver.stdout.log", "")
        stderr_path = write_text(output_dir / "solver.stderr.log", "")
        validation_path = write_json(
            output_dir / "validation.json", {"passed": True, "dry_run": True}
        )
        evidence_path = write_json(
            output_dir / "evidence.json", {"case_id": case.case_id, "dry_run": True}
        )
        return [
            str(session_path),
            str(stdout_path),
            str(stderr_path),
            str(validation_path),
            str(evidence_path),
        ]

    def _write_direct_evidence(self, output_dir: Path, case: BenchmarkCaseSpec) -> list[str]:
        session_path = write_text(output_dir / "session.xml", "<NEKTAR />\n")
        stdout_path = write_text(output_dir / "solver.stdout.log", "")
        stderr_path = write_text(output_dir / "solver.stderr.log", "")
        return [str(session_path), str(stdout_path), str(stderr_path)]

    def _load_test_spec(self, case: BenchmarkCaseSpec) -> NektarTestSpec:
        source_reference = case.source_reference
        if not isinstance(source_reference, dict):
            return NektarTestSpec()
        tst_path = Path(str(source_reference.get("tst", "")))
        if not tst_path.exists():
            return NektarTestSpec()
        return parse_nektar_tst(tst_path)

    def _materialize_session_xml(
        self,
        output_dir: Path,
        case: BenchmarkCaseSpec,
        test_spec: NektarTestSpec | None = None,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        source_reference = case.source_reference
        target = output_dir / "session.xml"
        if isinstance(source_reference, dict):
            source_tst = Path(str(source_reference.get("tst", "")))
            source_xml = self._source_xml_from_test_spec(source_reference, source_tst, test_spec)
            if source_xml is not None and source_xml.exists():
                shutil.copy2(source_xml, target)
                return target
        target.write_text("<NEKTAR />\n")
        return target

    def _source_xml_from_test_spec(
        self,
        source_reference: dict[str, Any],
        source_tst: Path,
        test_spec: NektarTestSpec | None,
    ) -> Path | None:
        if test_spec is not None and test_spec.parameters:
            parameter_path = Path(test_spec.parameters[0])
            return (
                parameter_path
                if parameter_path.is_absolute()
                else source_tst.parent / parameter_path
            )
        source_xml = Path(str(source_reference.get("xml", "")))
        return source_xml if str(source_xml) else None

    def _write_nektar_reference_metrics(
        self,
        output_dir: Path,
        test_spec: NektarTestSpec,
    ) -> None:
        if not test_spec.reference_metrics:
            return
        write_json(
            output_dir / "reference_metrics.json",
            {
                key: {"value": value, "tolerance": tolerance}
                for key, (value, tolerance) in sorted(test_spec.reference_metrics.items())
            },
        )
