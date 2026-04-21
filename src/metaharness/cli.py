"""Small command-line interface for Meta-Harness."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from metaharness import __version__
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

    ai4pde_case = subparsers.add_parser("ai4pde-case", help="Run an AI4PDECase XML through the AI4PDE demo flow")
    ai4pde_case.add_argument("case", help="path to AI4PDECase XML")
    ai4pde_case.set_defaults(func=_cmd_ai4pde_case)

    validate_case = subparsers.add_parser("validate-case", help="Validate an AI4PDECase XML via the case parser")
    validate_case.add_argument("case", help="path to AI4PDECase XML")
    validate_case.set_defaults(func=_cmd_validate_case)

    version = subparsers.add_parser("version", help="Print the package version")
    version.set_defaults(func=_cmd_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
