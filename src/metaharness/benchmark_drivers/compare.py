from __future__ import annotations

from json import JSONDecodeError
from pathlib import Path

from pydantic import ValidationError

from metaharness.benchmark_drivers.io import (
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
    claude_binary: str = "claude",
) -> list[ComparisonRow]:
    rows = compare_suite(runs_root, suite)
    manifest_lanes = lanes or _observed_lanes(runs_root, suite)
    comp_dir = comparison_dir(runs_root, suite)
    report_dir = reports_dir(runs_root, suite)
    row_payloads = [row.model_dump(mode="json") for row in rows]
    write_csv(comp_dir / "summary_table.csv", row_payloads, FIELDNAMES)
    write_json(comp_dir / "result_bundle.json", {"suite": suite, "rows": row_payloads})
    write_json(
        comp_dir / "run_manifest.json",
        build_run_manifest(
            suite=suite,
            lanes=manifest_lanes,
            cases=cases or [row.case_id for row in rows],
            runs_root=runs_root,
            claude_binary=claude_binary,
        ),
    )
    write_text(comp_dir / "comparison_report.md", _comparison_markdown(suite, rows))
    write_text(report_dir / f"{suite}-analysis-report.md", _analysis_markdown(suite, rows))
    write_text(report_dir / f"{suite}-backlog.md", _backlog_markdown(suite, rows))
    return rows


def _observed_lanes(runs_root: Path, suite: BenchmarkSuite) -> list[BenchmarkLane]:
    root = suite_root(runs_root, suite)
    known_lanes: list[BenchmarkLane] = ["extension", "direct", "agent"]
    return [lane for lane in known_lanes if (root / lane).exists()]


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
    if extension.passed and not direct.passed and agent.passed:
        return "agent_pipeline_advantage"
    if not extension.passed:
        return "extension_baseline_failed"
    return "workflow_gap"


def _comparison_markdown(suite: BenchmarkSuite, rows: list[ComparisonRow]) -> str:
    lines = [
        f"# {suite} comparison report",
        "",
        "| Case | Extension | Direct | Agent | Verdict |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.case_id} | {row.extension_status} | {row.direct_status} | {row.agent_status} | {row.verdict} |"
        )
    lines.append("")
    return "\n".join(lines)


def _analysis_markdown(suite: BenchmarkSuite, rows: list[ComparisonRow]) -> str:
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
        f"- Direct Claude CLI calls: {total_direct_llm_calls}",
        f"- Agent Claude CLI calls: {total_agent_llm_calls}",
        "- Evidence counts measure reproducibility support, not numerical superiority.",
        "- Driver time and solver elapsed time should be interpreted separately.",
        "",
        "## Case verdicts",
        "",
        "| Case | Extension | Direct | Agent | Verdict |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.case_id} | {row.extension_status} | {row.direct_status} | {row.agent_status} | {row.verdict} |"
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
