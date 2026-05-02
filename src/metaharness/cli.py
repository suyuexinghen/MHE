"""Small command-line interface for Meta-Harness."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from metaharness import __version__
from metaharness.benchmark_drivers.acp_provider import ACPBrainConfig, ACPBrainProvider
from metaharness.benchmark_drivers.claude_cli import ClaudeCLIBrainProvider, ClaudeCLIConfig
from metaharness.benchmark_drivers.compare import evaluate_approval_gate, write_comparison_outputs
from metaharness.benchmark_drivers.io import (
    case_dir,
    comparison_dir,
    read_json,
    specs_dir,
    write_json,
)
from metaharness.benchmark_drivers.models import BenchmarkLane, BenchmarkSuite
from metaharness.benchmark_drivers.nektar_cases import get_nektar_cases
from metaharness.benchmark_drivers.nektar_runner import NektarBenchmarkRunner
from metaharness.benchmark_drivers.octave_cases import get_octave_cases
from metaharness.benchmark_drivers.octave_runner import OctaveBenchmarkRunner
from metaharness.benchmark_drivers.qcompute_abacus_cases import get_qcompute_abacus_cases
from metaharness.benchmark_drivers.qcompute_abacus_runner import QComputeAbacusBenchmarkRunner
from metaharness.config.xml_parser import parse_graph_xml
from metaharness.config.xsd_validator import XmlStructuralError, validate_harness_xml
from metaharness.core.connection_engine import ConnectionEngine
from metaharness.core.graph_versions import GraphVersionStore
from metaharness.core.models import PendingConnectionSet
from metaharness.core.research import ResearchOrchestrator
from metaharness.demo import DemoHarness
from metaharness.research.domains.fealpy import FEALPyRuleBasedExperimentDesigner
from metaharness.research.dossier import build_research_dossier
from metaharness.research.reviewers import MetricThresholdReviewer
from metaharness.research.store import ResearchStore
from metaharness.sdk.discovery import discover_manifest_paths
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness.sdk.research import ExperimentPlan, Hypothesis, ResearchBudget, ResearchQuestion
from metaharness_ext.ai4pde.case_parser import Ai4PdeCaseXmlError, parse_ai4pde_case_xml
from metaharness_ext.ai4pde.demo import AI4PDECaseDemoHarness
from metaharness_ext.fealpy.benchmark_cases import get_fealpy_cases
from metaharness_ext.fealpy.benchmark_runner import FealpyBenchmarkRunner
from metaharness_ext.pycfd.benchmark_cases import pycfd_case_catalog
from metaharness_ext.pycfd.benchmark_runner import PyCFDBenchmarkRunner


def _cmd_demo(args: argparse.Namespace) -> int:
    harness = DemoHarness(topology=args.topology)
    if args.async_mode:
        result = asyncio.run(harness.run_async(task=args.task, trace_id=args.trace_id))
    else:
        result = harness.run(task=args.task, trace_id=args.trace_id)
    payload = {
        "topology": args.topology,
        "graph_version": result.graph_version,
        "trace_id": result.trace_id,
        "gateway_payload": result.gateway_payload,
        "runtime_payload": result.runtime_payload,
        "executor_payload": result.executor_payload,
        "evaluation_payload": result.evaluation_payload,
        "plan_payload": result.plan_payload,
        "memory_record": result.memory_record,
        "policy_record": result.policy_record,
        "audit_event": result.audit_event,
        "lifecycle": result.lifecycle,
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.graph)
    try:
        validate_harness_xml(path.read_text())
    except XmlStructuralError as exc:
        print("structural validation failed:", file=sys.stderr)
        for issue in exc.issues:
            print(f"  - {issue}", file=sys.stderr)
        return 2

    if not args.manifests:
        print("structural validation ok")
        return 0

    registry = ComponentRegistry()
    for manifest_dir in args.manifests:
        for manifest_path in discover_manifest_paths(Path(manifest_dir)):
            manifest = load_manifest(manifest_path)
            _, api = declare_component(f"{manifest.name}.primary", manifest)
            registry.register(f"{manifest.name}.primary", manifest, api.snapshot())

    engine = ConnectionEngine(registry, GraphVersionStore())
    snapshot = parse_graph_xml(path)
    _, report = engine.stage(PendingConnectionSet(nodes=snapshot.nodes, edges=snapshot.edges))
    if report.valid:
        print("semantic validation ok")
        return 0
    print("semantic validation failed:", file=sys.stderr)
    for issue in report.issues:
        print(f"  [{issue.code}] {issue.subject}: {issue.message}", file=sys.stderr)
    return 3


def _cmd_ai4pde_case(args: argparse.Namespace) -> int:
    result = AI4PDECaseDemoHarness().run_case(args.case)
    json.dump(result.to_json_dict(), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _cmd_validate_case(args: argparse.Namespace) -> int:
    try:
        task, plan = parse_ai4pde_case_xml(args.case)
    except Exception as exc:
        print("case validation failed:", file=sys.stderr)
        issues = exc.issues if isinstance(exc, Ai4PdeCaseXmlError) else [str(exc)]
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        return 2
    payload = {
        "status": "ok",
        "case": str(Path(args.case).resolve()),
        "task_id": task.task_id,
        "plan_id": plan.plan_id,
        "selected_method": plan.selected_method.value,
        "graph_family": plan.graph_family,
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _parse_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _repeat_runs_root(runs_root: Path, repeat_index: int) -> Path:
    return runs_root if repeat_index == 1 else runs_root / f"repeat-{repeat_index:02d}"


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _timing_stats(values: list[float]) -> dict[str, float | None]:
    q1 = _percentile(values, 0.25)
    q3 = _percentile(values, 0.75)
    return {
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "median": statistics.median(values) if values else None,
        "iqr": q3 - q1 if q1 is not None and q3 is not None else None,
    }


def _real_claude_permission_mode(*, allow_real_claude: bool, requested_mode: str | None) -> str:
    if requested_mode:
        return requested_mode
    return "bypassPermissions" if allow_real_claude else "auto"


def _parse_env_pairs(values: list[str]) -> dict[str, str]:
    env: dict[str, str] = {}
    for value in values:
        key, separator, raw = value.partition("=")
        if separator and key:
            env[key] = raw
    return env


def _benchmark_brain_provider(args: argparse.Namespace, *, use_real_claude: bool) -> Any | None:
    if not use_real_claude:
        return None
    if args.brain_provider == "acp":
        return ACPBrainProvider(
            ACPBrainConfig(
                command=args.acp_command,
                cwd=args.acp_cwd,
                env=_parse_env_pairs(args.acp_env),
                session_key=args.acp_session_key,
                timeout_seconds=args.acp_timeout_seconds,
                sdk_root=Path(args.acp_sdk_root) if args.acp_sdk_root else None,
            )
        )
    claude_permission_mode = _real_claude_permission_mode(
        allow_real_claude=use_real_claude,
        requested_mode=args.claude_permission_mode,
    )
    return ClaudeCLIBrainProvider(
        ClaudeCLIConfig(
            binary=args.claude_binary,
            model=args.claude_model,
            max_turns=args.claude_max_turns,
            permission_mode=claude_permission_mode,
            extra_args=args.claude_extra_arg,
        )
    )


def _aggregate_repeated_summaries(summaries: list[Any]) -> dict[str, object]:
    groups: dict[tuple[str, str], list[Any]] = {}
    for summary in summaries:
        groups.setdefault((summary.case_id, summary.lane), []).append(summary)
    rows = []
    for (case_id, lane), lane_summaries in sorted(groups.items()):
        driver_times = [
            float(summary.driver_time_seconds)
            for summary in lane_summaries
            if summary.driver_time_seconds is not None
        ]
        solver_times = [
            float(summary.elapsed_seconds)
            for summary in lane_summaries
            if summary.elapsed_seconds is not None
        ]
        statuses = [summary.status for summary in lane_summaries]
        flags = []
        if len(set(statuses)) > 1:
            flags.append("flaky_status")
        elapsed_stats = _timing_stats(solver_times)
        median_elapsed = elapsed_stats["median"]
        if (
            median_elapsed is not None
            and elapsed_stats["iqr"] is not None
            and median_elapsed > 0
            and elapsed_stats["iqr"] / median_elapsed > 0.5
        ):
            flags.append("flaky_timing")
        rows.append(
            {
                "case_id": case_id,
                "lane": lane,
                "run_count": len(lane_summaries),
                "passed_count": sum(1 for summary in lane_summaries if summary.passed),
                "failed_count": sum(1 for summary in lane_summaries if summary.status == "failed"),
                "skipped_count": sum(
                    1 for summary in lane_summaries if summary.status == "skipped"
                ),
                "median_driver_time_seconds": _timing_stats(driver_times)["median"],
                "min_driver_time_seconds": _timing_stats(driver_times)["min"],
                "max_driver_time_seconds": _timing_stats(driver_times)["max"],
                "iqr_driver_time_seconds": _timing_stats(driver_times)["iqr"],
                "median_elapsed_seconds": median_elapsed,
                "min_elapsed_seconds": elapsed_stats["min"],
                "max_elapsed_seconds": elapsed_stats["max"],
                "iqr_elapsed_seconds": elapsed_stats["iqr"],
                "total_llm_calls": sum(summary.llm_calls for summary in lane_summaries),
                "total_repairs": sum(summary.repair_count for summary in lane_summaries),
                "flags": flags,
            }
        )
    return {"rows": rows}


def _cmd_benchmark_run(args: argparse.Namespace) -> int:
    suite: BenchmarkSuite = args.suite
    raw_lanes = _parse_csv(args.lanes)
    if not raw_lanes:
        print("at least one benchmark lane is required", file=sys.stderr)
        return 2
    allowed_lanes = {"extension", "direct", "agent"}
    invalid_lanes = sorted(set(raw_lanes) - allowed_lanes)
    if invalid_lanes:
        print(f"invalid benchmark lanes: {', '.join(invalid_lanes)}", file=sys.stderr)
        return 2
    lanes: list[BenchmarkLane] = raw_lanes  # type: ignore[assignment]
    case_ids = _parse_csv(args.cases) if args.cases else None
    runs_root = Path(args.runs_root)
    repeat_count = max(1, int(args.repeat))
    use_real_claude = bool(args.allow_real_claude)
    brain_provider = _benchmark_brain_provider(args, use_real_claude=use_real_claude)
    try:
        if suite == "octave-native":
            cases = get_octave_cases(case_ids)
            runner = OctaveBenchmarkRunner(
                runs_root=runs_root,
                allow_real_tools=args.allow_real_tools,
                brain_provider=brain_provider,
                adaptive_agent=args.adaptive_agent,
                max_repair_attempts=args.max_repair_attempts,
            )
        elif suite == "nektar-pde":
            cases = get_nektar_cases(case_ids)
            runner = NektarBenchmarkRunner(
                runs_root=runs_root,
                allow_real_tools=args.allow_real_tools,
                brain_provider=brain_provider,
                adaptive_agent=args.adaptive_agent,
                max_repair_attempts=args.max_repair_attempts,
            )
        elif suite == "fealpy-pde":
            cases = get_fealpy_cases(case_ids)
            runner = FealpyBenchmarkRunner(
                runs_root=runs_root,
                allow_real_tools=args.allow_real_tools,
                brain_provider=brain_provider,
                adaptive_agent=args.adaptive_agent,
                max_repair_attempts=args.max_repair_attempts,
            )
        elif suite == "pycfd-pde":
            cases = list(pycfd_case_catalog(case_ids).values())
            runner = PyCFDBenchmarkRunner(
                runs_root=runs_root,
                allow_real_tools=args.allow_real_tools,
                pycfd_src_path=args.pycfd_src_path,
                brain_provider=brain_provider,
                adaptive_agent=args.adaptive_agent,
                max_repair_attempts=args.max_repair_attempts,
            )
        else:
            cases = get_qcompute_abacus_cases(case_ids)
            runner = QComputeAbacusBenchmarkRunner(
                runs_root=runs_root,
                allow_real_tools=args.allow_real_tools,
                brain_provider=brain_provider,
            )
    except KeyError as exc:
        print(f"unknown benchmark case: {exc.args[0]}", file=sys.stderr)
        return 2

    summaries = []
    summary_paths = []
    for repeat_index in range(1, repeat_count + 1):
        repeat_root = _repeat_runs_root(runs_root, repeat_index)
        if repeat_root != runner.runs_root:
            runner.runs_root = repeat_root
        for case in cases:
            write_json(specs_dir(repeat_root, suite) / f"{case.case_id}.json", case)
            case_summaries = runner.run_case(case, lanes)
            summaries.extend(case_summaries)
            summary_paths.extend(
                str(case_dir(repeat_root, suite, summary.lane, summary.case_id) / "summary.json")
                for summary in case_summaries
            )
    if repeat_count > 1:
        write_json(
            runs_root / f"{suite}-benchmark" / "comparison" / "repeat_summary.json",
            _aggregate_repeated_summaries(summaries),
        )
    payload = {
        "suite": suite,
        "lanes": lanes,
        "cases": [case.case_id for case in cases],
        "repeat_count": repeat_count,
        "real_claude": use_real_claude,
        "real_tools": bool(args.allow_real_tools),
        "summary_paths": summary_paths,
        "summaries": [summary.model_dump(mode="json") for summary in summaries],
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _cmd_benchmark_compare(args: argparse.Namespace) -> int:
    rows = write_comparison_outputs(
        runs_root=Path(args.runs_root),
        suite=args.suite,
        brain_provider=args.brain_provider,
        claude_binary=args.claude_binary,
        claude_model=args.claude_model,
        claude_max_turns=args.claude_max_turns,
        claude_permission_mode=_real_claude_permission_mode(
            allow_real_claude=args.allow_real_claude,
            requested_mode=args.claude_permission_mode,
        ),
        claude_extra_args=args.claude_extra_arg,
        real_claude=args.allow_real_claude,
        real_tools=args.allow_real_tools,
        repeat_count=args.repeat,
    )
    json.dump([row.model_dump(mode="json") for row in rows], sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


def _cmd_benchmark_approval_check(args: argparse.Namespace) -> int:
    case_ids = [case_id for case_id in args.cases.split(",") if case_id]
    gate = evaluate_approval_gate(
        config_root=Path(args.config_root),
        suite=args.suite,
        case_ids=case_ids,
    )
    json.dump(gate, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    if args.strict:
        return 0 if gate["approval_ready"] else 1
    malformed_statuses = {"not_configured", "invalid"}
    if gate["status"] in malformed_statuses:
        return 1
    for result in gate.get("profile_results", {}).values():
        if result.get("status") in {"missing"} or result.get("manifest") is None:
            return 1
    return 0


def _cmd_research_run(args: argparse.Namespace) -> int:
    try:
        question = ResearchQuestion.model_validate(read_json(Path(args.question)))
        summary_records = _research_summary_records(args)
        hypotheses, plans, summaries, artifact_refs = _research_plan_inputs(
            question, summary_records
        )
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        print(f"research-run input error: {exc}", file=sys.stderr)
        return 2

    runs_root = Path(args.runs_root)
    store = ResearchStore(runs_root)
    orchestrator = ResearchOrchestrator(store, budget=ResearchBudget(max_experiments=len(plans)))
    run = orchestrator.pursue(
        question,
        hypotheses=hypotheses,
        plans=plans,
        summaries=summaries,
        artifact_refs=artifact_refs,
    )
    reviews = [
        MetricThresholdReviewer().review(hypothesis, evidence)
        for hypothesis, evidence in zip(run.hypotheses, run.evidence, strict=True)
    ]
    dossier = build_research_dossier(run.question, run.evidence, run.conclusion)
    for review in reviews:
        store.record_review(review)
    store.record_dossier(dossier)
    artifacts = _write_research_run_artifacts(
        runs_root=runs_root,
        run=run,
        plans=plans,
        reviews=reviews,
        dossier=dossier,
        summary_records=summary_records,
        trace_path=store.trace_path,
    )
    manifest = _research_run_manifest(
        question_path=Path(args.question),
        summary_records=summary_records,
        run=run,
        review_ids=[review.review_id for review in reviews],
        dossier_id=dossier.dossier_id,
        artifacts={name: str(path) for name, path in artifacts.items()},
    )
    artifacts["artifact_manifest"] = write_json(runs_root / "artifact_manifest.json", manifest)
    payload = {
        "question_id": run.question.question_id,
        "decision": run.decisions[0].decision.value,
        "decisions": [decision.decision.value for decision in run.decisions],
        "runs_root": str(runs_root),
        "artifacts": {name: str(path) for name, path in artifacts.items()},
        "scope": manifest["scope"],
        "non_claims": manifest["non_claims"],
    }
    if args.print_trace:
        payload["trace"] = store.trace_path.read_text().splitlines()
    if args.output_format == "text":
        print(
            f"{run.question.question_id}: {payload['decision']} "
            f"({len(run.evidence)} evidence bundles) -> {runs_root}"
        )
    else:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    return 0


def _research_summary_records(args: argparse.Namespace) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for summary in args.summary:
        summary_path = Path(summary)
        records.append(
            {"path": summary_path, "summary": read_json(summary_path), "source": "summary"}
        )
    if args.benchmark_runs_root:
        if not args.suite:
            raise ValueError("--suite is required with --benchmark-runs-root")
        cases = _parse_csv(args.cases)
        lanes = _parse_csv(args.lanes or "extension")
        if not cases:
            raise ValueError("--cases is required with --benchmark-runs-root")
        for case_id in cases:
            for lane in lanes:
                summary_path = (
                    case_dir(Path(args.benchmark_runs_root), args.suite, lane, case_id)
                    / "summary.json"
                )
                records.append(
                    {
                        "path": summary_path,
                        "summary": read_json(summary_path),
                        "source": "benchmark-run",
                        "benchmark_runs_root": args.benchmark_runs_root,
                        "suite": args.suite,
                        "case_id": case_id,
                        "lane": lane,
                    }
                )
    if not records:
        raise ValueError("provide --summary or --benchmark-runs-root with --suite/--cases")
    return records


def _research_plan_inputs(
    question: ResearchQuestion, summary_records: list[dict[str, Any]]
) -> tuple[list[Hypothesis], list[ExperimentPlan], dict[str, dict[str, Any]], dict[str, str]]:
    hypotheses: list[Hypothesis] = []
    plans: list[ExperimentPlan] = []
    summaries: dict[str, dict[str, Any]] = {}
    artifact_refs: dict[str, str] = {}
    for index, record in enumerate(summary_records):
        summary = record["summary"]
        suffix = _research_summary_suffix(summary, index, len(summary_records))
        hypothesis = _hypothesis_from_question(question, suffix=suffix)
        plan = _experiment_plan_from_summary(hypothesis, summary, suffix=suffix)
        hypotheses.append(hypothesis)
        plans.append(plan)
        summaries[plan.plan_id] = summary
        artifact_refs[plan.plan_id] = str(record["path"])
    return hypotheses, plans, summaries, artifact_refs


def _experiment_plan_from_summary(
    hypothesis: Hypothesis, summary: dict[str, Any], *, suffix: str
) -> ExperimentPlan:
    if (
        not suffix
        and summary.get("suite") == "fealpy-pde"
        and summary.get("case_id") == "poisson-2d-numpy"
    ):
        return FEALPyRuleBasedExperimentDesigner(lane=str(summary.get("lane", "extension"))).design(
            ResearchQuestion(
                question_id=hypothesis.question_id,
                statement=hypothesis.statement,
                formal_spec=_formal_spec_from_prediction(hypothesis),
            ),
            hypothesis,
        )
    suite = str(summary.get("suite", "benchmark"))
    case_id = str(summary.get("case_id", "case"))
    lane = str(summary.get("lane", "extension"))
    plan_suffix = suffix or f"{suite}-{case_id}-{lane}"
    return ExperimentPlan(
        plan_id=f"plan-{plan_suffix}",
        hypothesis_id=hypothesis.hypothesis_id,
        suite=suite,
        case_id=case_id,
        lane=lane,
        expected_outcome=_formal_spec_from_prediction(hypothesis),
    )


def _formal_spec_from_prediction(hypothesis: Hypothesis) -> dict[str, Any]:
    if not hypothesis.prediction:
        return {}
    metric, expectation = next(iter(hypothesis.prediction.items()))
    return {
        "primary_metric": metric,
        "relation": expectation.get("relation"),
        "target": expectation.get("value"),
    }


def _research_summary_suffix(summary: dict[str, Any], index: int, record_count: int) -> str:
    if record_count == 1:
        return ""
    return "-".join(
        str(part)
        for part in (
            index + 1,
            summary.get("suite", "benchmark"),
            summary.get("case_id", f"case-{index}"),
            summary.get("lane", "extension"),
        )
    )


def _write_research_run_artifacts(
    *,
    runs_root: Path,
    run: Any,
    plans: list[ExperimentPlan],
    reviews: list[Any],
    dossier: Any,
    summary_records: list[dict[str, Any]],
    trace_path: Path,
) -> dict[str, Path]:
    artifacts = {
        "question": write_json(runs_root / "research_question.json", run.question),
        "hypotheses": write_json(runs_root / "hypotheses.json", run.hypotheses),
        "experiment_plans": write_json(runs_root / "experiment_plans.json", plans),
        "evidence_bundles": write_json(runs_root / "evidence_bundles.json", run.evidence),
        "decisions": write_json(runs_root / "decisions.json", run.decisions),
        "reviews": write_json(runs_root / "reviews.json", reviews),
        "dossier": write_json(runs_root / "research_dossier.json", dossier),
        "conclusion": write_json(runs_root / "conclusion.json", run.conclusion),
        "metric_schema": write_json(
            runs_root / "metric_schema.json", _metric_schema_sidecar(run.question)
        ),
        "sota_baselines": write_json(
            runs_root / "sota_baselines.json", _sota_baseline_sidecar(summary_records)
        ),
        "reproducibility_summary": write_json(
            runs_root / "reproducibility_summary.json",
            _reproducibility_summary(summary_records),
        ),
        "trace": trace_path,
    }
    if len(run.hypotheses) == 1:
        artifacts.update(
            {
                "hypothesis": write_json(runs_root / "hypothesis.json", run.hypotheses[0]),
                "experiment_plan": write_json(runs_root / "experiment_plan.json", plans[0]),
                "evidence_bundle": write_json(runs_root / "evidence_bundle.json", run.evidence[0]),
                "decision": write_json(runs_root / "decision.json", run.decisions[0]),
                "review": write_json(runs_root / "review.json", reviews[0]),
            }
        )
    return artifacts


def _metric_schema_sidecar(question: ResearchQuestion) -> dict[str, Any]:
    return {
        "schema": "metaharness.metric_schema_sidecar.v1",
        "question_id": question.question_id,
        "metrics": [
            {
                "name": question.formal_spec.get("primary_metric"),
                "relation": question.formal_spec.get("relation"),
                "target": question.formal_spec.get("target", question.formal_spec.get("value")),
                "unit": question.formal_spec.get("unit", ""),
                "is_primary": True,
            }
        ],
    }


def _sota_baseline_sidecar(summary_records: list[dict[str, Any]]) -> dict[str, Any]:
    baselines = []
    for record in summary_records:
        summary = record["summary"]
        baselines.append(
            {
                "baseline_id": "benchmark:"
                f"{summary.get('suite')}:{summary.get('case_id')}:{summary.get('lane')}",
                "source": str(record["path"]),
                "suite": summary.get("suite"),
                "case_id": summary.get("case_id"),
                "lane": summary.get("lane"),
                "status": summary.get("status"),
                "metric_values": summary.get("metrics", {}),
            }
        )
    return {"schema": "metaharness.sota_baseline_sidecar.v1", "baselines": baselines}


def _reproducibility_summary(summary_records: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[Any, Any, Any], list[dict[str, Any]]] = {}
    repeat_summary_refs = sorted(
        {
            str(
                comparison_dir(Path(record["benchmark_runs_root"]), record["suite"])
                / "repeat_summary.json"
            )
            for record in summary_records
            if record.get("benchmark_runs_root")
            and (
                comparison_dir(Path(record["benchmark_runs_root"]), record["suite"])
                / "repeat_summary.json"
            ).exists()
        }
    )
    for record in summary_records:
        summary = record["summary"]
        key = (summary.get("suite"), summary.get("case_id"), summary.get("lane"))
        groups.setdefault(key, []).append(summary)
    rows = []
    for (suite, case_id, lane), summaries in groups.items():
        rows.append(
            {
                "suite": suite,
                "case_id": case_id,
                "lane": lane,
                "run_count": len(summaries),
                "passed_count": sum(
                    1 for summary in summaries if summary.get("status") == "passed"
                ),
                "failed_count": sum(
                    1 for summary in summaries if summary.get("status") == "failed"
                ),
                "skipped_count": sum(
                    1 for summary in summaries if summary.get("status") == "skipped"
                ),
                "reproducibility_tier": "single_run" if len(summaries) == 1 else "repeated_run",
            }
        )
    return {
        "schema": "metaharness.reproducibility_summary.v1",
        "repeat_summary_refs": repeat_summary_refs,
        "rows": rows,
    }


def _research_run_manifest(
    *,
    question_path: Path,
    summary_records: list[dict[str, Any]],
    run: Any,
    review_ids: list[str],
    dossier_id: str,
    artifacts: dict[str, str],
) -> dict[str, Any]:
    benchmark_sources = [
        record for record in summary_records if record.get("source") == "benchmark-run"
    ]
    return {
        "schema": "metaharness.research_run_manifest.v2",
        "question_id": run.question.question_id,
        "decision": run.decisions[0].decision.value,
        "decisions": [decision.decision.value for decision in run.decisions],
        "source_inputs": {
            "question": str(question_path),
            "benchmark_summary": str(summary_records[0]["path"]),
            "benchmark_summaries": [str(record["path"]) for record in summary_records],
            "benchmark_handoff": bool(benchmark_sources),
            "benchmark_runs_roots": sorted(
                {str(record["benchmark_runs_root"]) for record in benchmark_sources}
            ),
        },
        "derived_records": {
            "hypothesis_id": run.hypotheses[0].hypothesis_id,
            "hypothesis_ids": [hypothesis.hypothesis_id for hypothesis in run.hypotheses],
            "evidence_bundle_id": run.evidence[0].bundle_id,
            "evidence_bundle_ids": [evidence.bundle_id for evidence in run.evidence],
            "decision_id": run.decisions[0].decision_id,
            "decision_ids": [decision.decision_id for decision in run.decisions],
            "review_id": review_ids[0],
            "review_ids": review_ids,
            "dossier_id": dossier_id,
        },
        "artifacts": artifacts,
        "scope": "deterministic benchmark-backed MVP research loop",
        "non_claims": [
            "open-ended discovery loop",
            "solver superiority",
            "generalized benchmark approval",
        ],
    }


def _hypothesis_from_question(question: ResearchQuestion, *, suffix: str = "") -> Hypothesis:
    metric = question.formal_spec.get("primary_metric")
    relation = question.formal_spec.get("relation")
    value = question.formal_spec.get("target", question.formal_spec.get("value"))
    if not metric or not relation or value is None:
        raise ValueError("question formal_spec must include primary_metric, relation, and target")
    hypothesis_suffix = f"-{suffix}" if suffix else ""
    return Hypothesis(
        hypothesis_id=f"h-{question.question_id}{hypothesis_suffix}",
        question_id=question.question_id,
        statement=f"{question.statement} ({metric} {relation} {value})",
        prediction={str(metric): {"relation": relation, "value": value}},
    )


def _cmd_version(_: argparse.Namespace) -> int:
    print(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="metaharness", description="Meta-Harness CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the bundled demo harness")
    demo.add_argument("--topology", choices=["minimal", "expanded"], default="minimal")
    demo.add_argument("--task", default="demo task")
    demo.add_argument("--trace-id", default="trace-demo-1")
    demo.add_argument("--async-mode", action="store_true")
    demo.set_defaults(func=_cmd_demo)

    validate = subparsers.add_parser(
        "validate", help="Structurally (and optionally semantically) validate a graph XML"
    )
    validate.add_argument("graph", help="path to graph XML")
    validate.add_argument(
        "--manifests",
        action="append",
        default=[],
        help="manifest directory to include for semantic validation (repeatable)",
    )
    validate.set_defaults(func=_cmd_validate)

    ai4pde_case = subparsers.add_parser(
        "ai4pde-case", help="Run an AI4PDECase XML through the AI4PDE demo flow"
    )
    ai4pde_case.add_argument("case", help="path to AI4PDECase XML")
    ai4pde_case.set_defaults(func=_cmd_ai4pde_case)

    validate_case = subparsers.add_parser(
        "validate-case", help="Validate an AI4PDECase XML via the case parser"
    )
    validate_case.add_argument("case", help="path to AI4PDECase XML")
    validate_case.set_defaults(func=_cmd_validate_case)

    benchmark_run = subparsers.add_parser(
        "benchmark-run", help="Run scientific workflow benchmark lanes"
    )
    benchmark_run.add_argument(
        "--suite",
        choices=["octave-native", "nektar-pde", "qcompute-abacus", "fealpy-pde", "pycfd-pde"],
        required=True,
    )
    benchmark_run.add_argument("--lanes", default="extension,direct,agent")
    benchmark_run.add_argument("--cases", default="")
    benchmark_run.add_argument("--runs-root", default=".runs")
    benchmark_run.add_argument(
        "--brain-provider", choices=["claude-cli", "acp"], default="claude-cli"
    )
    benchmark_run.add_argument("--claude-binary", default="claude")
    benchmark_run.add_argument("--claude-model", default=None)
    benchmark_run.add_argument("--claude-max-turns", type=int, default=5)
    benchmark_run.add_argument("--claude-permission-mode", default=None)
    benchmark_run.add_argument("--claude-extra-arg", action="append", default=[])
    benchmark_run.add_argument(
        "--acp-command",
        nargs="+",
        default=["npx", "@agentclientprotocol/claude-agent-acp"],
    )
    benchmark_run.add_argument("--acp-cwd", default=".")
    benchmark_run.add_argument(
        "--acp-env", action="append", default=["ACP_PERMISSION_MODE=acceptEdits"]
    )
    benchmark_run.add_argument("--acp-session-key", default="mhe-benchmark")
    benchmark_run.add_argument("--acp-timeout-seconds", type=float, default=300.0)
    benchmark_run.add_argument("--acp-sdk-root", default=None)
    benchmark_run.add_argument("--allow-real-tools", action="store_true")
    benchmark_run.add_argument("--allow-real-claude", action="store_true")
    benchmark_run.add_argument("--pycfd-src-path", default=None)
    benchmark_run.add_argument("--repeat", type=int, default=1)
    benchmark_run.add_argument("--adaptive-agent", action="store_true")
    benchmark_run.add_argument("--max-repair-attempts", type=int, default=1)
    benchmark_run.set_defaults(func=_cmd_benchmark_run)

    benchmark_compare = subparsers.add_parser(
        "benchmark-compare", help="Compare saved scientific workflow benchmark summaries"
    )
    benchmark_compare.add_argument(
        "--suite",
        choices=["octave-native", "nektar-pde", "qcompute-abacus", "fealpy-pde", "pycfd-pde"],
        required=True,
    )
    benchmark_compare.add_argument("--runs-root", default=".runs")
    benchmark_compare.add_argument(
        "--brain-provider", choices=["claude-cli", "acp"], default="claude-cli"
    )
    benchmark_compare.add_argument("--claude-binary", default="claude")
    benchmark_compare.add_argument("--claude-model", default=None)
    benchmark_compare.add_argument("--claude-max-turns", type=int, default=5)
    benchmark_compare.add_argument("--claude-permission-mode", default=None)
    benchmark_compare.add_argument("--claude-extra-arg", action="append", default=[])
    benchmark_compare.add_argument("--allow-real-tools", action="store_true")
    benchmark_compare.add_argument("--allow-real-claude", action="store_true")
    benchmark_compare.add_argument("--repeat", type=int, default=1)
    benchmark_compare.set_defaults(func=_cmd_benchmark_compare)

    approval_check = subparsers.add_parser(
        "benchmark-approval-check", help="Validate benchmark comparison approval gates"
    )
    approval_check.add_argument(
        "--suite",
        choices=["octave-native", "nektar-pde", "qcompute-abacus", "fealpy-pde", "pycfd-pde"],
        required=True,
    )
    approval_check.add_argument("--cases", default="")
    approval_check.add_argument("--config-root", default=".mhe")
    approval_check.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when required approval profiles are intentionally blocked",
    )
    approval_check.set_defaults(func=_cmd_benchmark_approval_check)

    research_run = subparsers.add_parser(
        "research-run", help="Run a benchmark-backed MVP research loop from JSON artifacts"
    )
    research_run.add_argument("--question", required=True, help="path to ResearchQuestion JSON")
    research_run.add_argument(
        "--summary", action="append", default=[], help="path to benchmark summary JSON (repeatable)"
    )
    research_run.add_argument(
        "--benchmark-runs-root",
        default=None,
        help="benchmark runs root to resolve summary paths from --suite/--cases/--lanes",
    )
    research_run.add_argument(
        "--suite",
        choices=["octave-native", "nektar-pde", "qcompute-abacus", "fealpy-pde", "pycfd-pde"],
        default=None,
    )
    research_run.add_argument("--cases", default="", help="comma-separated benchmark case ids")
    research_run.add_argument(
        "--lanes", default="extension", help="comma-separated benchmark lanes"
    )
    research_run.add_argument(
        "--runs-root", required=True, help="directory for research trace/artifacts"
    )
    research_run.add_argument("--output-format", choices=["json", "text"], default="json")
    research_run.add_argument("--print-trace", action="store_true")
    research_run.set_defaults(func=_cmd_research_run)

    version = subparsers.add_parser("version", help="Print the package version")
    version.set_defaults(func=_cmd_version)

    return parser


def _normalize_claude_extra_args(argv: list[str] | None) -> list[str] | None:
    if argv is None:
        return None
    normalized: list[str] = []
    index = 0
    while index < len(argv):
        value = argv[index]
        if value == "--claude-extra-arg" and index + 1 < len(argv):
            normalized.append(f"--claude-extra-arg={argv[index + 1]}")
            index += 2
            continue
        normalized.append(value)
        index += 1
    return normalized


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(_normalize_claude_extra_args(argv))
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
