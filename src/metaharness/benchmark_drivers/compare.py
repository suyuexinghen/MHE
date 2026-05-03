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
    "approval_gate_status",
    "approval_ready",
    "approval_required_profiles",
    "approval_human_missing",
    "approval_scientific_missing",
    "approval_production_missing",
    "approval_real_repeat_missing",
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
    "repair_advantage",
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
    approval_config_root: Path | None = None,
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
    approval_gate = evaluate_approval_gate(
        config_root=approval_config_root or Path(".mhe"),
        suite=suite,
        rows=rows,
    )
    evidence_context["approval_gate"] = approval_gate
    enriched_row_payloads = _enrich_rows(row_payloads, evidence_context)
    write_csv(comp_dir / "summary_table.csv", enriched_row_payloads, FIELDNAMES)
    write_json(
        comp_dir / "result_bundle.json",
        {
            "suite": suite,
            "approval_status": approval_gate["status"],
            "approval_profiles": approval_gate.get("approved_profiles", []),
            "blocked_profiles": approval_gate.get("blocked_profiles", []),
            "excluded_claims": approval_gate.get("excluded_claims", []),
            "evidence_context": evidence_context,
            "rows": row_payloads,
        },
    )
    write_json(comp_dir / "approval_gate.json", approval_gate)
    write_json(comp_dir / "run_manifest.json", manifest)
    write_text(
        comp_dir / "comparison_report.md", _comparison_markdown(suite, rows, evidence_context)
    )
    write_text(
        report_dir / f"{suite}-analysis-report.md",
        _analysis_markdown(suite, rows, evidence_context),
    )
    write_text(report_dir / f"{suite}-backlog.md", _backlog_markdown(suite, rows, evidence_context))
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
    grouped = load_lane_summaries(runs_root, suite)
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
        "metric_rows": _metric_detail_rows(grouped),
        "preflight_rows": _preflight_rows(runs_root, suite),
        "capability_gate_rows": _capability_gate_rows(runs_root, suite),
        "repair_rows": _repair_rows(rows),
        "repeat_rows": [] if repeat_summary is None else repeat_summary.get("rows", []),
    }


def _preflight_rows(runs_root: Path, suite: BenchmarkSuite) -> list[dict[str, Any]]:
    preflight_root = suite_root(runs_root, suite) / "preflight"
    if not preflight_root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for summary_path in sorted(preflight_root.glob("*/tester_summary.json")):
        try:
            summary = read_json(summary_path)
        except (JSONDecodeError, OSError):
            rows.append(
                {
                    "case_id": summary_path.parent.name,
                    "status": "schema_failed",
                    "preflight_executed": False,
                    "tester_available": None,
                    "solver_available": None,
                    "tst_available": None,
                    "reference_metric_count": None,
                    "tester_return_code": None,
                    "alternative_validation": None,
                }
            )
            continue
        rows.append(
            {
                "case_id": summary.get("case_id", summary_path.parent.name),
                "status": summary.get("status"),
                "preflight_executed": summary.get("preflight_executed", False),
                "tester_available": summary.get("tester_available"),
                "solver_available": summary.get("solver_available"),
                "tst_available": summary.get("tst_available"),
                "reference_metric_count": summary.get("reference_metric_count"),
                "tester_return_code": summary.get("tester_return_code"),
                "alternative_validation": summary.get("alternative_validation"),
            }
        )
    return rows


def _capability_gate_rows(runs_root: Path, suite: BenchmarkSuite) -> list[dict[str, Any]]:
    root = suite_root(runs_root, suite)
    rows: list[dict[str, Any]] = []
    for lane in ["extension", "direct", "agent"]:
        lane_root = root / lane
        if not lane_root.exists():
            continue
        case_dirs = sorted(
            path
            for path in lane_root.iterdir()
            if path.is_dir()
            and ((path / "capability_status.json").exists() or (path / "source_refs.json").exists())
        )
        for case_path in case_dirs:
            status_path = case_path / "capability_status.json"
            source_refs_path = case_path / "source_refs.json"
            if not status_path.exists():
                rows.append(
                    {
                        "case_id": case_path.name,
                        "lane": lane,
                        "status": "missing",
                        "promotion_ready": False,
                        "missing_capabilities": ["capability_status_missing"],
                        "solver_binary": None,
                        "solver_family": None,
                        "plan_status": None,
                        "source_refs_path": str(source_refs_path),
                        "capability_status_path": str(status_path),
                    }
                )
                continue
            try:
                status = read_json(status_path)
            except (JSONDecodeError, OSError) as exc:
                rows.append(
                    {
                        "case_id": case_path.name,
                        "lane": lane,
                        "status": "schema_failed",
                        "promotion_ready": False,
                        "missing_capabilities": [f"capability_status_unreadable: {exc}"],
                        "solver_binary": None,
                        "solver_family": None,
                        "plan_status": None,
                        "source_refs_path": str(source_refs_path)
                        if source_refs_path.exists()
                        else None,
                        "capability_status_path": str(status_path),
                    }
                )
                continue
            rows.append(
                {
                    "case_id": status.get("case_id", case_path.name),
                    "lane": lane,
                    "status": status.get("status"),
                    "promotion_ready": status.get("promotion_ready", False),
                    "missing_capabilities": status.get("missing_capabilities", []),
                    "solver_binary": status.get("solver_binary"),
                    "solver_family": status.get("solver_family"),
                    "plan_status": status.get("plan_status"),
                    "source_refs_path": str(source_refs_path)
                    if source_refs_path.exists()
                    else None,
                    "capability_status_path": str(status_path),
                }
            )
    return rows


def _repair_rows(rows: list[ComparisonRow]) -> list[dict[str, Any]]:
    repair_rows: list[dict[str, Any]] = []
    for row in rows:
        if not any(
            [
                row.direct_proposal_contract_status,
                row.agent_proposal_contract_status,
                row.direct_repairs,
                row.agent_repairs,
                row.direct_repair_outcome,
                row.agent_repair_outcome,
            ]
        ):
            continue
        repair_rows.append(
            {
                "case_id": row.case_id,
                "direct_contract": row.direct_proposal_contract_status,
                "agent_contract": row.agent_proposal_contract_status,
                "direct_repairs": row.direct_repairs or 0,
                "agent_repairs": row.agent_repairs or 0,
                "direct_repair_outcome": row.direct_repair_outcome,
                "agent_repair_outcome": row.agent_repair_outcome,
                "repair_advantage": _repair_advantage(row),
            }
        )
    return repair_rows


def _repair_advantage(row: ComparisonRow) -> str:
    direct_repairs = row.direct_repairs or 0
    agent_repairs = row.agent_repairs or 0
    if (
        row.direct_status == "failed"
        and row.agent_status == "passed"
        and agent_repairs > direct_repairs
    ):
        return "agent_repaired_direct_failure"
    if agent_repairs > direct_repairs:
        return "agent_more_repair_evidence"
    if direct_repairs > agent_repairs:
        return "direct_more_repair_evidence"
    return "none"


def _metric_detail_rows(grouped: dict[str, dict[str, LaneSummary]]) -> list[dict[str, Any]]:
    metric_rows: list[dict[str, Any]] = []
    for case_id in sorted(grouped):
        for lane in ["extension", "direct", "agent"]:
            summary = grouped[case_id].get(lane)
            if summary is None:
                continue
            for metric_name, value in sorted(summary.metrics.items()):
                if metric_name == "elapsed_seconds":
                    continue
                if not isinstance(value, int | float | list):
                    continue
                metric_rows.append(
                    {
                        "case_id": case_id,
                        "lane": lane,
                        "metric": metric_name,
                        "value": value,
                        "reference_diff": summary.metric_diffs.get(metric_name),
                        "status": summary.status,
                        "passed": summary.passed,
                    }
                )
    return metric_rows


def evaluate_approval_gate(
    *,
    config_root: Path,
    suite: BenchmarkSuite,
    rows: list[ComparisonRow] | None = None,
    case_ids: list[str] | None = None,
) -> dict[str, Any]:
    config_path = config_root / "config.json"
    policy_path = config_root / "benchmarks" / "comparison-approval.json"
    if not config_path.exists() or not policy_path.exists():
        return {
            "status": "not_configured",
            "approval_ready": False,
            "missing_evidence_by_category": {"human_approval": ["approval_policy_missing"]},
            "profile_results": {},
            "claim_boundary": "No comparison promotion approval policy was found.",
        }
    try:
        config = read_json(config_path)
        policy = read_json(policy_path)
    except (JSONDecodeError, OSError) as exc:
        return {
            "status": "invalid",
            "approval_ready": False,
            "missing_evidence_by_category": {
                "human_approval": [f"approval_policy_unreadable: {exc}"]
            },
            "profile_results": {},
            "claim_boundary": "Comparison approval policy must be valid JSON before claims are allowed.",
        }
    profiles = config.get("approval", {}).get("profiles", {})
    required_profiles = list(policy.get("required_approval_profiles", []))
    for conditional in policy.get("conditional_approval_profiles", []):
        if _approval_condition_matches(
            conditional.get("when", {}), suite, rows or [], case_ids or []
        ):
            required_profiles.extend(conditional.get("requires", []))
    required_profiles = list(dict.fromkeys(required_profiles))
    profile_results = {
        profile_name: _approval_profile_result(
            config_root, profile_name, profiles.get(profile_name, {})
        )
        for profile_name in required_profiles
    }
    approved_profiles = [
        profile_name for profile_name, result in profile_results.items() if result["satisfied"]
    ]
    blocked_profiles = [
        profile_name for profile_name, result in profile_results.items() if not result["satisfied"]
    ]
    excluded_claims = list(
        dict.fromkeys(
            claim
            for result in profile_results.values()
            for claim in result.get("excluded_claims", [])
        )
    )
    missing_evidence_by_category: dict[str, list[str]] = {
        "human_approval": [],
        "scientific_validation": [],
        "production_converter": [],
        "real_repeat_evidence": [],
    }
    for result in profile_results.values():
        if result["satisfied"]:
            continue
        categorized = result.get(
            "missing_evidence_by_category"
        ) or _approval_missing_evidence_by_category(result["profile"], result["missing_evidence"])
        for category, blockers in categorized.items():
            missing_evidence_by_category.setdefault(category, []).extend(blockers)
    missing_evidence_by_category = {
        category: list(dict.fromkeys(blockers))
        for category, blockers in missing_evidence_by_category.items()
    }
    approval_ready = not any(missing_evidence_by_category.values())
    approval_decisions = {
        result.get("approval_decision")
        for result in profile_results.values()
        if result["satisfied"]
    }
    status = "blocked"
    if approval_ready:
        status = (
            "approved_with_limitations"
            if "approved_with_limitations" in approval_decisions
            else "approved"
        )
    return {
        "status": status,
        "approval_ready": approval_ready,
        "policy_id": policy.get("policy_id"),
        "required_profiles": required_profiles,
        "approved_profiles": approved_profiles,
        "blocked_profiles": blocked_profiles,
        "excluded_claims": excluded_claims,
        "profile_results": profile_results,
        "missing_evidence_by_category": missing_evidence_by_category,
        "claim_boundary": (
            "Administrator approval gates comparison promotion claims; it does not prove "
            "scientific or numerical superiority by itself."
        ),
    }


def _approval_condition_matches(
    condition: dict[str, Any],
    suite: BenchmarkSuite,
    rows: list[ComparisonRow],
    case_ids: list[str],
) -> bool:
    if condition.get("suite") not in {None, suite}:
        return False
    case_id = condition.get("case_id")
    observed_case_ids = list(dict.fromkeys([*(row.case_id for row in rows), *case_ids]))
    if case_id is not None and case_id not in observed_case_ids:
        return False
    return True


def _approval_profile_result(
    config_root: Path, profile_name: str, profile: dict[str, Any]
) -> dict[str, Any]:
    manifest_ref = profile.get("manifest")
    required_fields = list(profile.get("required_fields", []))
    if not manifest_ref:
        return {
            "profile": profile_name,
            "status": "missing",
            "satisfied": False,
            "manifest": None,
            "missing_evidence": [f"{profile_name}_manifest_ref_missing"],
        }
    manifest_path = (
        config_root.parent / manifest_ref
        if not Path(manifest_ref).is_absolute()
        else Path(manifest_ref)
    )
    if not manifest_path.exists():
        return {
            "profile": profile_name,
            "status": "missing",
            "satisfied": False,
            "manifest": str(manifest_path),
            "missing_evidence": [f"{profile_name}_manifest_missing"],
        }
    try:
        manifest = read_json(manifest_path)
    except (JSONDecodeError, OSError) as exc:
        return {
            "profile": profile_name,
            "status": "invalid",
            "satisfied": False,
            "manifest": str(manifest_path),
            "missing_evidence": [f"{profile_name}_manifest_unreadable: {exc}"],
        }
    missing_fields = [field for field in required_fields if not manifest.get(field)]
    status = str(manifest.get("status", "unknown"))
    decision = manifest.get("approval_decision")
    grantable_decisions = {"approved", "approved_with_limitations"}
    grantable_statuses = {"approved", "approved_with_limitations", "valid"}
    decision_satisfied = (
        "approval_decision" not in required_fields or decision in grantable_decisions
    )
    satisfied = not missing_fields and status in grantable_statuses and decision_satisfied
    missing_evidence = [] if satisfied else [f"{profile_name}_not_approved"]
    missing_evidence.extend(f"{profile_name}_{field}_missing" for field in missing_fields)
    return {
        "profile": profile_name,
        "status": status,
        "approval_decision": decision,
        "approved_by": manifest.get("approved_by"),
        "satisfied": satisfied,
        "manifest": str(manifest_path),
        "missing_fields": missing_fields,
        "missing_evidence": missing_evidence,
        "missing_evidence_by_category": _approval_missing_evidence_by_category(
            profile_name, missing_evidence
        ),
        "excluded_claims": manifest.get("approved_scope", {}).get("excluded_claims", []),
    }


def _approval_missing_evidence_by_category(
    profile_name: str, missing_evidence: list[str]
) -> dict[str, list[str]]:
    categorized: dict[str, list[str]] = {
        "human_approval": [],
        "scientific_validation": [],
        "production_converter": [],
        "real_repeat_evidence": [],
    }
    for item in missing_evidence:
        if item.endswith(
            (
                "fixture_refs_missing",
                "tolerance_table_ref_missing",
                "reference_observable_missing",
            )
        ):
            category = "scientific_validation"
        elif "converter" in item:
            category = "production_converter"
        elif "repeat" in item:
            category = "real_repeat_evidence"
        elif profile_name == "abacus_hs_scientific" and item.endswith("_not_approved"):
            category = "scientific_validation"
        else:
            category = "human_approval"
        categorized[category].append(item)
    return categorized


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
                "approval_gate_status": evidence_context["approval_gate"]["status"],
                "approval_ready": evidence_context["approval_gate"]["approval_ready"],
                "approval_required_profiles": ",".join(
                    evidence_context["approval_gate"].get("required_profiles", [])
                ),
                "approval_human_missing": ",".join(
                    evidence_context["approval_gate"]
                    .get("missing_evidence_by_category", {})
                    .get("human_approval", [])
                ),
                "approval_scientific_missing": ",".join(
                    evidence_context["approval_gate"]
                    .get("missing_evidence_by_category", {})
                    .get("scientific_validation", [])
                ),
                "approval_production_missing": ",".join(
                    evidence_context["approval_gate"]
                    .get("missing_evidence_by_category", {})
                    .get("production_converter", [])
                ),
                "approval_real_repeat_missing": ",".join(
                    evidence_context["approval_gate"]
                    .get("missing_evidence_by_category", {})
                    .get("real_repeat_evidence", [])
                ),
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
                "repair_advantage": _repair_advantage_from_payload(row),
            }
        )
    return enriched


def _repair_advantage_from_payload(row: dict[str, Any]) -> str:
    direct_repairs = row.get("direct_repairs") or 0
    agent_repairs = row.get("agent_repairs") or 0
    if (
        row.get("direct_status") == "failed"
        and row.get("agent_status") == "passed"
        and agent_repairs > direct_repairs
    ):
        return "agent_repaired_direct_failure"
    if agent_repairs > direct_repairs:
        return "agent_more_repair_evidence"
    if direct_repairs > agent_repairs:
        return "direct_more_repair_evidence"
    return "none"


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


def _approval_markdown_lines(evidence_context: dict[str, Any]) -> list[str]:
    approval_gate = evidence_context["approval_gate"]
    lines = [
        "",
        "## Approval gate",
        "",
        f"- Status: `{approval_gate['status']}`",
        f"- Approval ready: `{approval_gate['approval_ready']}`",
        f"- Claim boundary: {approval_gate['claim_boundary']}",
        "",
        "| Profile | Status | Decision | Approved by | Satisfied | Missing evidence |",
        "|---|---|---|---|---|---|",
    ]
    for profile_name, result in approval_gate.get("profile_results", {}).items():
        missing = ", ".join(result.get("missing_evidence", [])) or "none"
        lines.append(
            f"| {profile_name} | {result.get('status')} | {result.get('approval_decision') or 'none'} | {result.get('approved_by') or 'none'} | {result.get('satisfied')} | {missing} |"
        )
    if not approval_gate.get("profile_results"):
        lines.append("| none | none | none | none | False | approval_policy_missing |")
    return lines


def _repair_markdown_lines(evidence_context: dict[str, Any]) -> list[str]:
    repair_rows = evidence_context.get("repair_rows", [])
    if not repair_rows:
        return []
    lines = [
        "",
        "## Proposal contracts and repair",
        "",
        "| Case | Direct contract | Agent contract | Direct repairs | Agent repairs | Direct repair outcome | Agent repair outcome | Repair advantage |",
        "|---|---|---|---:|---:|---|---|---|",
    ]
    for repair_row in repair_rows:
        lines.append(
            f"| {repair_row['case_id']} | {repair_row.get('direct_contract') or 'none'} | {repair_row.get('agent_contract') or 'none'} | {repair_row['direct_repairs']} | {repair_row['agent_repairs']} | {repair_row.get('direct_repair_outcome') or 'none'} | {repair_row.get('agent_repair_outcome') or 'none'} | {repair_row['repair_advantage']} |"
        )
    return lines


def _metric_markdown_lines(evidence_context: dict[str, Any]) -> list[str]:
    metric_rows = evidence_context.get("metric_rows", [])
    if not metric_rows:
        return []
    lines = [
        "",
        "## Metric details",
        "",
        "| Case | Lane | Metric | Value | Reference diff | Status | Passed |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for metric_row in metric_rows:
        lines.append(
            f"| {metric_row['case_id']} | {metric_row['lane']} | {metric_row['metric']} | {metric_row['value']} | {metric_row.get('reference_diff')} | {metric_row['status']} | {metric_row['passed']} |"
        )
    return lines


def _capability_gate_markdown_lines(evidence_context: dict[str, Any]) -> list[str]:
    capability_gate_rows = evidence_context.get("capability_gate_rows", [])
    if not capability_gate_rows:
        return []
    lines = [
        "",
        "## Capability gates",
        "",
        "| Case | Lane | Status | Promotion ready | Missing capabilities | Solver | Family | Plan status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for gate_row in capability_gate_rows:
        missing = ", ".join(gate_row.get("missing_capabilities", [])) or "none"
        lines.append(
            f"| {gate_row['case_id']} | {gate_row['lane']} | {gate_row.get('status')} | {gate_row.get('promotion_ready')} | {missing} | {gate_row.get('solver_binary') or 'none'} | {gate_row.get('solver_family') or 'none'} | {gate_row.get('plan_status') or 'none'} |"
        )
    return lines


def _preflight_markdown_lines(evidence_context: dict[str, Any]) -> list[str]:
    preflight_rows = evidence_context.get("preflight_rows", [])
    if not preflight_rows:
        return []
    lines = [
        "",
        "## Preflight summaries",
        "",
        "| Case | Status | Executed | Tester | Solver | TST | Reference metrics | Tester return code | Alternative validation |",
        "|---|---|---|---|---|---|---:|---:|---|",
    ]
    for preflight_row in preflight_rows:
        lines.append(
            f"| {preflight_row['case_id']} | {preflight_row.get('status')} | {preflight_row.get('preflight_executed')} | {preflight_row.get('tester_available')} | {preflight_row.get('solver_available')} | {preflight_row.get('tst_available')} | {preflight_row.get('reference_metric_count')} | {preflight_row.get('tester_return_code')} | {preflight_row.get('alternative_validation') or 'none'} |"
        )
    return lines


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
        f"- Approval gate: `{evidence_context['approval_gate']['status']}`",
        "",
        "| Case | Extension | Direct | Agent | Direct proposal | Agent proposal | Direct preflight | Agent preflight | Agent repair | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        sources = evidence_context["proposal_sources"].get(row.case_id, {})
        lines.append(
            f"| {row.case_id} | {row.extension_status} | {row.direct_status} | {row.agent_status} | {sources.get('direct', 'none')} | {sources.get('agent', 'none')} | {row.direct_preflight_status or 'none'} | {row.agent_preflight_status or 'none'} | {row.agent_repair_outcome or 'none'} | {row.verdict} |"
        )
    lines.extend(_repair_markdown_lines(evidence_context))
    lines.extend(_metric_markdown_lines(evidence_context))
    lines.extend(_preflight_markdown_lines(evidence_context))
    lines.extend(_capability_gate_markdown_lines(evidence_context))
    lines.extend(_approval_markdown_lines(evidence_context))
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
    total_direct_repairs = sum(row.direct_repairs or 0 for row in rows)
    total_agent_repairs = sum(row.agent_repairs or 0 for row in rows)
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
        f"- Approval gate: `{evidence_context['approval_gate']['status']}`",
        f"- Direct Claude CLI calls: {total_direct_llm_calls}",
        f"- Agent Claude CLI calls: {total_agent_llm_calls}",
        f"- Direct repairs: {total_direct_repairs}",
        f"- Agent repairs: {total_agent_repairs}",
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
    lines.extend(_repair_markdown_lines(evidence_context))
    lines.extend(_metric_markdown_lines(evidence_context))
    lines.extend(_preflight_markdown_lines(evidence_context))
    lines.extend(_capability_gate_markdown_lines(evidence_context))
    lines.extend(_approval_markdown_lines(evidence_context))
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


def _backlog_markdown(
    suite: BenchmarkSuite, rows: list[ComparisonRow], evidence_context: dict[str, Any]
) -> str:
    lines = [f"# {suite} backlog", ""]
    case_backlog_items = [row for row in rows if row.verdict != "all_passed"]
    if case_backlog_items:
        for row in case_backlog_items:
            lines.append(f"- `{row.case_id}`: investigate `{row.verdict}`.")
    else:
        lines.append("- No case-level benchmark backlog items from current summaries.")
    approval_gate = evidence_context["approval_gate"]
    if not approval_gate.get("approval_ready", False):
        lines.extend(
            [
                "",
                "## Approval gate blockers",
                "",
                f"- Status: `{approval_gate['status']}`.",
                f"- Claim boundary: {approval_gate['claim_boundary']}",
            ]
        )
        for category, blockers in approval_gate.get("missing_evidence_by_category", {}).items():
            if blockers:
                rendered_blockers = ", ".join(f"`{blocker}`" for blocker in blockers)
                lines.append(f"- `{category}`: {rendered_blockers}.")
    lines.append("")
    return "\n".join(lines)
