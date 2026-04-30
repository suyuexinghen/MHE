"""Small command-line interface for Meta-Harness."""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
from pathlib import Path
from typing import Any

from metaharness import __version__
from metaharness.benchmark_drivers.acp_provider import ACPBrainConfig, ACPBrainProvider
from metaharness.benchmark_drivers.claude_cli import ClaudeCLIBrainProvider, ClaudeCLIConfig
from metaharness.benchmark_drivers.compare import write_comparison_outputs
from metaharness.benchmark_drivers.io import specs_dir, write_json
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
from metaharness.demo import DemoHarness
from metaharness.sdk.discovery import discover_manifest_paths
from metaharness.sdk.loader import declare_component, load_manifest
from metaharness.sdk.registry import ComponentRegistry
from metaharness_ext.ai4pde.case_parser import Ai4PdeCaseXmlError, parse_ai4pde_case_xml
from metaharness_ext.ai4pde.demo import AI4PDECaseDemoHarness


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
    for repeat_index in range(1, repeat_count + 1):
        repeat_root = _repeat_runs_root(runs_root, repeat_index)
        if repeat_root != runner.runs_root:
            runner.runs_root = repeat_root
        for case in cases:
            write_json(specs_dir(repeat_root, suite) / f"{case.case_id}.json", case)
            summaries.extend(runner.run_case(case, lanes))
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
        "--suite", choices=["octave-native", "nektar-pde", "qcompute-abacus"], required=True
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
    benchmark_run.add_argument("--repeat", type=int, default=1)
    benchmark_run.add_argument("--adaptive-agent", action="store_true")
    benchmark_run.add_argument("--max-repair-attempts", type=int, default=1)
    benchmark_run.set_defaults(func=_cmd_benchmark_run)

    benchmark_compare = subparsers.add_parser(
        "benchmark-compare", help="Compare saved scientific workflow benchmark summaries"
    )
    benchmark_compare.add_argument(
        "--suite", choices=["octave-native", "nektar-pde", "qcompute-abacus"], required=True
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
