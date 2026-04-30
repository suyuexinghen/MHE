from __future__ import annotations

from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from metaharness.benchmark_drivers.io import (
    case_dir,
    comparison_dir,
    read_json,
    reports_dir,
    suite_root,
    write_csv,
    write_json,
    write_text,
)
from metaharness.benchmark_drivers.manifests import build_run_manifest
from metaharness.benchmark_drivers.models import (
    BenchmarkLane,
    BenchmarkSuite,
    ComparisonRow,
    LaneSummary,
)

FIELDNAMES = [
    "case_id",
    "suite",
    "extension_status",
    "direct_status",
    "agent_status",
    "extension_passed",
    "direct_passed",
    "agent_passed",
    "direct_attempts",
    "agent_attempts",
    "direct_repairs",
    "agent_repairs",
    "direct_llm_calls",
    "agent_llm_calls",
    "extension_evidence_count",
    "direct_evidence_count",
    "agent_evidence_count",
    "real_tools",
    "real_claude",
    "repeat_count",
    "direct_proposal_source",
    "agent_proposal_source",
    "direct_proposal_contract_status",
    "agent_proposal_contract_status",
    "direct_preflight_status",
    "agent_preflight_status",
    "direct_failure_category",
    "agent_failure_category",
    "direct_repair_outcome",
    "agent_repair_outcome",
    "agent_diagnostics_count",
    "verdict",
]


def load_lane_summaries(
    runs_root: Path, suite: BenchmarkSuite
) -> dict[str, dict[str, LaneSummary]]:
    root = suite_root(runs_root, suite)
    grouped: dict[str, dict[str, LaneSummary]] = {}
    for lane in ["extension", "direct", "agent"]:
        lane_root = root / lane
        if not lane_root.exists():
            continue
        for summary_path in lane_root.glob("*/summary.json"):
            summary = _load_summary_or_schema_failure(summary_path, suite, lane)
            grouped.setdefault(summary.case_id, {})[lane] = summary
    return grouped


def _load_summary_or_schema_failure(
    summary_path: Path, suite: BenchmarkSuite, lane: str
) -> LaneSummary:
    try:
        return LaneSummary.model_validate(read_json(summary_path))
    except (JSONDecodeError, ValidationError, OSError) as exc:
        schema_report = {
            "path": str(summary_path),
            "valid": False,
            "error": str(exc),
        }
        write_json(summary_path.parent / "schema_validation.json", schema_report)
        return LaneSummary(
            case_id=summary_path.parent.name,
            suite=suite,
            lane=lane,  # type: ignore[arg-type]
            status="schema_failed",
            passed=False,
            error_message=str(exc),
            evidence_files=[str(summary_path), str(summary_path.parent / "schema_validation.json")],
            flags=["schema_failed"],
        )


def compare_suite(runs_root: Path, suite: BenchmarkSuite) -> list[ComparisonRow]:
    grouped = load_lane_summaries(runs_root, suite)
    rows: list[ComparisonRow] = []
    for case_id in sorted(grouped):
        lanes = grouped[case_id]
        extension = lanes.get("extension")
        direct = lanes.get("direct")
        agent = lanes.get("agent")
        rows.append(
            ComparisonRow(
                case_id=case_id,
                suite=suite,
                extension_status=None if extension is None else extension.status,
                direct_status=None if direct is None else direct.status,
                agent_status=None if agent is None else agent.status,
                extension_passed=None if extension is None else extension.passed,
                direct_passed=None if direct is None else direct.passed,
                agent_passed=None if agent is None else agent.passed,
                direct_attempts=None if direct is None else direct.attempt_count,
                agent_attempts=None if agent is None else agent.attempt_count,
                direct_repairs=None if direct is None else direct.repair_count,
                agent_repairs=None if agent is None else agent.repair_count,
                direct_llm_calls=None if direct is None else direct.llm_calls,
                agent_llm_calls=None if agent is None else agent.llm_calls,
                extension_evidence_count=None if extension is None else extension.evidence_count,
                direct_evidence_count=None if direct is None else direct.evidence_count,
                agent_evidence_count=None if agent is None else agent.evidence_count,
                direct_proposal_contract_status=None
                if direct is None
                else direct.proposal_contract_status,
                agent_proposal_contract_status=None
                if agent is None
                else agent.proposal_contract_status,
                direct_preflight_status=None if direct is None else direct.preflight_status,
                agent_preflight_status=None if agent is None else agent.preflight_status,
                direct_failure_category=None if direct is None else direct.failure_category,
                agent_failure_category=None if agent is None else agent.failure_category,
                direct_repair_outcome=None if direct is None else direct.repair_outcome,
                agent_repair_outcome=None if agent is None else agent.repair_outcome,
                agent_diagnostics_count=None if agent is None else len(agent.diagnostics_files),
                verdict=_verdict(extension, direct, agent),
            )
        )
    return rows


def write_comparison_outputs(
    *,
    runs_root: Path,
    suite: BenchmarkSuite,
    cases: list[str] | None = None,
    lanes: list[BenchmarkLane] | None = None,
    brain_provider: str = "claude-cli",
    claude_binary: str = "claude",
    claude_model: str | None = None,
    claude_max_turns: int = 5,
    claude_permission_mode: str = "auto",
    claude_extra_args: list[str] | None = None,
    real_claude: bool = False,
    real_tools: bool = False,
    repeat_count: int = 1,
) -> list[ComparisonRow]:
    rows = compare_suite(runs_root, suite)
    manifest_lanes = lanes or _observed_lanes(runs_root, suite)
    comp_dir = comparison_dir(runs_root, suite)
    report_dir = reports_dir(runs_root, suite)
    row_payloads = [row.model_dump(mode="json") for row in rows]
    manifest = build_run_manifest(
        suite=suite,
        lanes=manifest_lanes,
        cases=cases or [row.case_id for row in rows],
        runs_root=runs_root,
        brain_provider=brain_provider,
        claude_binary=claude_binary,
        claude_model=claude_model,
        claude_max_turns=claude_max_turns,
        claude_permission_mode=claude_permission_mode,
        claude_extra_args=claude_extra_args,
        real_claude=real_claude,
        real_tools=real_tools,
        repeat_count=repeat_count,
    )
    repeat_summary = _read_repeat_summary(comp_dir)
    evidence_context = _evidence_context(
        runs_root=runs_root,
        suite=suite,
        rows=rows,
        manifest=manifest.model_dump(mode="json"),
        repeat_summary=repeat_summary,
    )
    enriched_row_payloads = _enrich_rows(row_payloads, evidence_context)
    write_csv(comp_dir / "summary_table.csv", enriched_row_payloads, FIELDNAMES)
    write_json(
        comp_dir / "result_bundle.json",
        {"suite": suite, "evidence_context": evidence_context, "rows": row_payloads},
    )
    write_json(comp_dir / "run_manifest.json", manifest)
    write_text(
        comp_dir / "comparison_report.md", _comparison_markdown(suite, rows, evidence_context)
    )
    write_text(
        report_dir / f"{suite}-analysis-report.md",
        _analysis_markdown(suite, rows, evidence_context),
    )
    write_text(report_dir / f"{suite}-backlog.md", _backlog_markdown(suite, rows))
    return rows


def _observed_lanes(runs_root: Path, suite: BenchmarkSuite) -> list[BenchmarkLane]:
    root = suite_root(runs_root, suite)
    known_lanes: list[BenchmarkLane] = ["extension", "direct", "agent"]
    return [lane for lane in known_lanes if (root / lane).exists()]


def _read_repeat_summary(comp_dir: Path) -> dict[str, Any] | None:
    repeat_path = comp_dir / "repeat_summary.json"
    if not repeat_path.exists():
        return None
    try:
        return read_json(repeat_path)
    except (JSONDecodeError, OSError):
        return None


def _proposal_source(
    runs_root: Path, suite: BenchmarkSuite, lane: BenchmarkLane, case_id: str
) -> str:
    command_path = case_dir(runs_root, suite, lane, case_id) / "claude_command.json"
    if not command_path.exists():
        return "none"
    try:
        command = read_json(command_path).get("command", [])
    except (JSONDecodeError, OSError):
        return "unknown"
    if not command:
        return "unknown"
    return "fake" if command[0] == "fake-claude" else "real"


def _evidence_context(
    *,
    runs_root: Path,
    suite: BenchmarkSuite,
    rows: list[ComparisonRow],
    manifest: dict[str, Any],
    repeat_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    claude_cli = manifest.get("claude_cli", {})
    proposal_sources = {
        row.case_id: {
            "direct": _proposal_source(runs_root, suite, "direct", row.case_id),
            "agent": _proposal_source(runs_root, suite, "agent", row.case_id),
        }
        for row in rows
    }
    return {
        "real_tools": bool(claude_cli.get("real_tools", False)),
        "real_claude": bool(claude_cli.get("real_claude", False)),
        "repeat_count": claude_cli.get("repeat_count", 1),
        "proposal_sources": proposal_sources,
        "repeat_rows": [] if repeat_summary is None else repeat_summary.get("rows", []),
    }


def _enrich_rows(
    row_payloads: list[dict[str, Any]], evidence_context: dict[str, Any]
) -> list[dict[str, Any]]:
    enriched = []
    for row in row_payloads:
        sources = evidence_context["proposal_sources"].get(row["case_id"], {})
        enriched.append(
            {
                **row,
                "real_tools": evidence_context["real_tools"],
                "real_claude": evidence_context["real_claude"],
                "repeat_count": evidence_context["repeat_count"],
                "direct_proposal_source": sources.get("direct", "none"),
                "agent_proposal_source": sources.get("agent", "none"),
                "direct_proposal_contract_status": row.get("direct_proposal_contract_status"),
                "agent_proposal_contract_status": row.get("agent_proposal_contract_status"),
                "direct_preflight_status": row.get("direct_preflight_status"),
                "agent_preflight_status": row.get("agent_preflight_status"),
                "direct_failure_category": row.get("direct_failure_category"),
                "agent_failure_category": row.get("agent_failure_category"),
                "direct_repair_outcome": row.get("direct_repair_outcome"),
                "agent_repair_outcome": row.get("agent_repair_outcome"),
                "agent_diagnostics_count": row.get("agent_diagnostics_count"),
            }
        )
    return enriched


def _verdict(
    extension: LaneSummary | None,
    direct: LaneSummary | None,
    agent: LaneSummary | None,
) -> str:
    if extension is None or direct is None or agent is None:
        return "incomplete"
    if any(summary.status == "schema_failed" for summary in [extension, direct, agent]):
        return "schema_failed"
    if any(summary.status == "skipped" for summary in [extension, direct, agent]):
        return "capability_skip"
    if extension.passed and direct.passed and agent.passed:
        return "all_passed"
    if extension.passed and not direct.passed and agent.repair_outcome == "repaired_success":
        return "agent_repaired_success"
    if extension.passed and not direct.passed and agent.passed:
        return "agent_pipeline_advantage"
    if agent.repair_outcome == "unrepaired_failure":
        return "unrepaired_failure"
    if not extension.passed:
        return "extension_baseline_failed"
    return "workflow_gap"


def _comparison_markdown(
    suite: BenchmarkSuite, rows: list[ComparisonRow], evidence_context: dict[str, Any]
) -> str:
    lines = [
        f"# {suite} comparison report",
        "",
        "## Evidence context",
        "",
        f"- Real tools: `{evidence_context['real_tools']}`",
        f"- Real Claude: `{evidence_context['real_claude']}`",
        f"- Repeat count: `{evidence_context['repeat_count']}`",
        "",
        "| Case | Extension | Direct | Agent | Direct proposal | Agent proposal | Direct preflight | Agent preflight | Agent repair | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        sources = evidence_context["proposal_sources"].get(row.case_id, {})
        lines.append(
            f"| {row.case_id} | {row.extension_status} | {row.direct_status} | {row.agent_status} | {sources.get('direct', 'none')} | {sources.get('agent', 'none')} | {row.direct_preflight_status or 'none'} | {row.agent_preflight_status or 'none'} | {row.agent_repair_outcome or 'none'} | {row.verdict} |"
        )
    if evidence_context["repeat_rows"]:
        lines.extend(
            [
                "",
                "## Repeat statistics",
                "",
                "| Case | Lane | Runs | Passed | Failed | Skipped | Median elapsed | IQR elapsed | Flags |",
                "|---|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for repeat_row in evidence_context["repeat_rows"]:
            lines.append(
                f"| {repeat_row['case_id']} | {repeat_row['lane']} | {repeat_row['run_count']} | {repeat_row['passed_count']} | {repeat_row['failed_count']} | {repeat_row['skipped_count']} | {repeat_row.get('median_elapsed_seconds')} | {repeat_row.get('iqr_elapsed_seconds')} | {', '.join(repeat_row.get('flags', [])) or 'none'} |"
            )
    lines.append("")
    return "\n".join(lines)


def _analysis_markdown(
    suite: BenchmarkSuite, rows: list[ComparisonRow], evidence_context: dict[str, Any]
) -> str:
    passed = sum(1 for row in rows if row.verdict == "all_passed")
    capability_skips = sum(1 for row in rows if row.verdict == "capability_skip")
    schema_failures = sum(1 for row in rows if row.verdict == "schema_failed")
    total_direct_llm_calls = sum(row.direct_llm_calls or 0 for row in rows)
    total_agent_llm_calls = sum(row.agent_llm_calls or 0 for row in rows)
    lines = [
        f"# {suite} analysis report",
        "",
        "## Scope",
        "",
        f"- Cases compared: {len(rows)}",
        f"- Fully passed cases: {passed}",
        f"- Capability skips: {capability_skips}",
        f"- Schema failures: {schema_failures}",
        "",
        "## Workflow quality",
        "",
        f"- Real tools: `{evidence_context['real_tools']}`",
        f"- Real Claude: `{evidence_context['real_claude']}`",
        f"- Repeat count: `{evidence_context['repeat_count']}`",
        f"- Direct Claude CLI calls: {total_direct_llm_calls}",
        f"- Agent Claude CLI calls: {total_agent_llm_calls}",
        "- Evidence counts measure reproducibility support, not numerical superiority.",
        "- Driver time and solver elapsed time should be interpreted separately.",
        "",
        "## Case verdicts",
        "",
        "| Case | Extension | Direct | Agent | Direct proposal | Agent proposal | Direct preflight | Agent preflight | Agent repair | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        sources = evidence_context["proposal_sources"].get(row.case_id, {})
        lines.append(
            f"| {row.case_id} | {row.extension_status} | {row.direct_status} | {row.agent_status} | {sources.get('direct', 'none')} | {sources.get('agent', 'none')} | {row.direct_preflight_status or 'none'} | {row.agent_preflight_status or 'none'} | {row.agent_repair_outcome or 'none'} | {row.verdict} |"
        )
    if evidence_context["repeat_rows"]:
        lines.extend(
            [
                "",
                "## Repeat statistics",
                "",
                "| Case | Lane | Runs | Passed | Failed | Skipped | Median elapsed | IQR elapsed | Flags |",
                "|---|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for repeat_row in evidence_context["repeat_rows"]:
            lines.append(
                f"| {repeat_row['case_id']} | {repeat_row['lane']} | {repeat_row['run_count']} | {repeat_row['passed_count']} | {repeat_row['failed_count']} | {repeat_row['skipped_count']} | {repeat_row.get('median_elapsed_seconds')} | {repeat_row.get('iqr_elapsed_seconds')} | {', '.join(repeat_row.get('flags', [])) or 'none'} |"
            )
    lines.extend(["", "## Limitations", ""])
    if suite == "nektar-pde":
        lines.extend(
            [
                "- Dry-run summaries do not prove local Nektar++ solver availability.",
                "- Agent workflow quality is measured through lane evidence, not improved PDE accuracy.",
            ]
        )
    elif suite == "qcompute-abacus":
        lines.extend(
            [
                "- Dry-run summaries validate Hamiltonian proxy workflow layout, not real QPU or ABACUS execution.",
                "- The ABACUS H/S bridge sentinel must remain skipped until a converter is implemented.",
            ]
        )
    elif suite == "fealpy-pde":
        lines.extend(
            [
                "- Dry-run summaries validate harness layout and comparison logic, not fealpy numerical runtime.",
                "- Multi-backend comparison requires numpy/pytorch/jax to be installed for real runs.",
                "- Transient PDE cases (Allen-Cahn, Navier-Stokes) require time-stepping infrastructure in the solver.",
            ]
        )
    else:
        lines.extend(
            [
                "- Dry-run summaries validate harness layout and comparison logic, not Octave numerical runtime.",
                "- Direct and agent lanes should use the same Claude CLI binary, model, and turn budget in real runs.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _backlog_markdown(suite: BenchmarkSuite, rows: list[ComparisonRow]) -> str:
    lines = [f"# {suite} backlog", ""]
    for row in rows:
        if row.verdict != "all_passed":
            lines.append(f"- `{row.case_id}`: investigate `{row.verdict}`.")
    if len(lines) == 2:
        lines.append("- No benchmark backlog items from current summaries.")
    lines.append("")
    return "\n".join(lines)
